from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .config import FeatureConfig
from .export import write_csv, write_json, write_parquet
from .features import (
    change,
    momentum,
    nearest_at_or_after,
    realized_volatility,
    simple_return,
)
from .labels import resolve_from_reference
from .schema import (
    COLUMNS, CORE_FEATURE_COLUMNS, FEATURE_COLUMNS,
    MICROSTRUCTURE_FEATURE_COLUMNS, NUMERIC_COLUMNS, TrainingRow,
)
from polymarket.resolution_engine.storage import read_resolutions


@dataclass(frozen=True)
class BuildResult:
    rows: list[TrainingRow]
    summary: dict[str, Any]
    csv_path: Path
    parquet_path: Path
    summary_path: Path


@dataclass
class _MarketEvidence:
    market: dict[str, Any]
    snapshots: list[tuple[datetime, dict[str, Any]]]
    lag: list[tuple[datetime, dict[str, Any]]]
    microstructure: list[tuple[datetime, dict[str, Any]]]
    detection_delay: float | None = None
    detection_source: str = ""


class DatasetBuilder:
    def __init__(self, config: FeatureConfig | None = None) -> None:
        self.config = config or FeatureConfig()
        self._derived_detection_markets: set[str] = set()
        self._explicit_detection_markets: set[str] = set()

    def build(self) -> BuildResult:
        self._derived_detection_markets = set()
        self._explicit_detection_markets = set()
        resolutions = read_resolutions(self.config.resolutions_path)
        candidates: dict[str, list[tuple[TrainingRow, int]]] = {}
        sessions_read = 0
        skipped: dict[str, int] = {}
        for session in self._session_paths():
            sessions_read += 1
            rows, session_skips = self._read_session(session, resolutions)
            for reason, count in session_skips.items():
                skipped[reason] = skipped.get(reason, 0) + count
            for row, quality in rows:
                candidates.setdefault(row.market_id, []).append((row, quality))

        rows = [
            max(versions, key=lambda candidate: (
                candidate[1],
                candidate[0].source_session,
            ))[0]
            for versions in candidates.values()
        ]
        rows.sort(key=lambda row: (row.window_start, row.asset, row.market_id))
        pre_filter_rows = list(rows)
        excluded_rows = []
        rows = []
        for row in pre_filter_rows:
            missing_features = [
                name for name in CORE_FEATURE_COLUMNS
                if getattr(row, name) is None
            ]
            if len(missing_features) > self.config.max_missing_features_per_row:
                excluded_rows.append({
                    "market_id": row.market_id,
                    "asset": row.asset,
                    "source_session": row.source_session,
                    "missing_feature_count": len(missing_features),
                    "missing_features": missing_features,
                    "reason": "feature_completeness_policy",
                })
            else:
                rows.append(row)
        summary = summarize(rows)
        summary["dataset_paths"] = {
            "csv": str(self.config.output_root / "dataset.csv"),
            "parquet": str(self.config.output_root / "dataset.parquet"),
        }
        summary["sessions_read"] = sessions_read
        summary["skipped_windows"] = skipped
        summary["label_policy"] = {
            "preferred_source": "polymarket_gamma_resolved",
            "proxy_source": "reference_window_return",
            "proxy_allowed": self.config.allow_proxy_labels,
            "proxy_up_rule": "closing_reference_price >= opening_reference_price",
            "boundary_tolerance_seconds": self.config.boundary_tolerance_seconds,
        }
        summary["authoritative_labels"] = sum(
            row.label_source == "polymarket_gamma_resolved" for row in rows
        )
        summary["proxy_labels"] = sum(
            row.label_source == "reference_window_return" for row in rows
        )
        summary["feature_anchor_seconds"] = self.config.feature_anchor_seconds
        summary["asof_max_age_seconds"] = self.config.asof_max_age_seconds
        summary["max_missing_features_per_row"] = (
            self.config.max_missing_features_per_row
        )
        summary["rows_before_completeness_filter"] = len(pre_filter_rows)
        summary["rows_excluded_by_completeness_policy"] = len(excluded_rows)
        summary["microstructure"] = {
            "schema_version": 1,
            "feature_columns": list(MICROSTRUCTURE_FEATURE_COLUMNS),
            "rows_with_any_microstructure": sum(
                any(getattr(row, name) is not None
                    for name in MICROSTRUCTURE_FEATURE_COLUMNS)
                for row in rows
            ),
            "rows_with_complete_microstructure": sum(
                all(getattr(row, name) is not None
                    for name in MICROSTRUCTURE_FEATURE_COLUMNS)
                for row in rows
            ),
            "legacy_rows_remain_eligible": True,
            "provenance": {
                "event": "microstructure_snapshot",
                "selection": "latest event at or before feature_timestamp",
                "maximum_age_seconds": self.config.asof_max_age_seconds,
                "future_events_allowed": False,
                "missing_value_policy": "explicit null; no imputation",
            },
        }

        output = self.config.output_root
        output.mkdir(parents=True, exist_ok=True)
        csv_path = output / "dataset.csv"
        parquet_path = output / "dataset.parquet"
        summary_path = output / "feature_summary.json"
        write_csv(csv_path, rows)
        write_parquet(parquet_path, rows)
        write_json(summary_path, summary)
        write_json(output / "missingness_diagnostics.json", {
            "configuration": {
                "asof_max_age_seconds": self.config.asof_max_age_seconds,
                "max_missing_features_per_row": (
                    self.config.max_missing_features_per_row
                ),
            },
            "before_filter": _missingness(pre_filter_rows),
            "after_filter": _missingness(rows),
            "excluded_rows": excluded_rows,
            "recovery": {
                "detection_delay_derived_from_first_seen": len(
                    self._derived_detection_markets
                    & {row.market_id for row in pre_filter_rows}
                ),
            },
        })
        return BuildResult(rows, summary, csv_path, parquet_path, summary_path)

    def inspect(self) -> dict[str, Any]:
        summary_path = self.config.output_root / "feature_summary.json"
        if not summary_path.exists():
            raise FileNotFoundError(
                f"Dataset not found at {self.config.output_root}; run build first"
            )
        return json.loads(summary_path.read_text(encoding="utf-8"))

    def _session_paths(self) -> list[Path]:
        if not self.config.runs_root.exists():
            return []
        return sorted(
            path for path in self.config.runs_root.glob("*/session.jsonl")
            if path.parent.name != "latest"
        )

    def _read_session(
        self, path: Path, resolutions: dict
    ) -> tuple[list[tuple[TrainingRow, int]], dict[str, int]]:
        markets: dict[str, _MarketEvidence] = {}
        references: dict[str, list[tuple[datetime, float]]] = {}
        last_timestamp: datetime | None = None
        malformed = 0
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    envelope = json.loads(line)
                    timestamp = _dt(envelope["timestamp"])
                    event = envelope["event"]
                    payload = envelope.get("payload", {})
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    malformed += 1
                    continue
                last_timestamp = max(last_timestamp, timestamp) if last_timestamp else timestamp
                if event == "market_lifecycle":
                    market = payload.get("market", {})
                    market_id = market.get("market_id")
                    if market_id:
                        evidence = markets.setdefault(
                            market_id, _MarketEvidence(market, [], [], [])
                        )
                        evidence.market = market
                        if evidence.detection_delay is None:
                            window_start = _dt(market["window_start"])
                            evidence.detection_delay = max(
                                0.0, (timestamp - window_start).total_seconds()
                            )
                            evidence.detection_source = "market_lifecycle_first_seen"
                            if str(market_id) not in self._explicit_detection_markets:
                                self._derived_detection_markets.add(str(market_id))
                elif event == "reference_price":
                    asset = payload.get("asset")
                    if asset and payload.get("price") is not None:
                        references.setdefault(asset, []).append(
                            (_dt(payload.get("timestamp", envelope["timestamp"])),
                             float(payload["price"]))
                        )
                elif event == "polymarket_snapshot":
                    market_id = payload.get("market_id")
                    if market_id:
                        evidence = markets.setdefault(
                            market_id, _MarketEvidence({}, [], [], [])
                        )
                        evidence.snapshots.append((timestamp, payload))
                elif event == "microstructure_snapshot":
                    market_id = payload.get("market_id")
                    if market_id:
                        evidence = markets.setdefault(
                            market_id, _MarketEvidence({}, [], [], [])
                        )
                        evidence.microstructure.append((timestamp, payload))
                elif event == "lag_measurement":
                    market_id = payload.get("market_id")
                    if market_id:
                        evidence = markets.setdefault(
                            market_id, _MarketEvidence({}, [], [], [])
                        )
                        evidence.lag.append((timestamp, payload.get("measurement", {})))
                elif event == "lifecycle_tracking" and payload.get("event") == "detected":
                    market_id = payload.get("market_id")
                    if market_id:
                        evidence = markets.setdefault(
                            market_id, _MarketEvidence({}, [], [], [])
                        )
                        evidence.detection_delay = float(
                            payload.get("seconds_after_open_when_detected", 0.0)
                        )
                        evidence.detection_source = "lifecycle_tracking"
                        self._explicit_detection_markets.add(str(market_id))
                        self._derived_detection_markets.discard(str(market_id))

        for series in references.values():
            series.sort()
        rows: list[tuple[TrainingRow, int]] = []
        skipped: dict[str, int] = {}
        if malformed:
            skipped["malformed_events"] = malformed
        for market_id, evidence in markets.items():
            reason, candidate = self._build_row(
                market_id, evidence, references, last_timestamp, path, resolutions
            )
            if candidate:
                rows.append(candidate)
            else:
                skipped[reason] = skipped.get(reason, 0) + 1
        return rows, skipped

    def _build_row(
        self,
        market_id: str,
        evidence: _MarketEvidence,
        references: dict[str, list[tuple[datetime, float]]],
        last_timestamp: datetime | None,
        session_path: Path,
        resolutions: dict,
    ) -> tuple[str, tuple[TrainingRow, int] | None]:
        market = evidence.market
        required = {"asset", "window_start", "window_end"}
        if not required <= market.keys():
            return "missing_market_metadata", None
        asset = str(market["asset"])
        window_start = _dt(market["window_start"])
        window_end = _dt(market["window_end"])
        if last_timestamp is None or window_end > last_timestamp:
            return "incomplete_window", None
        reference = references.get(asset, [])
        proxy_label = resolve_from_reference(
            window_start,
            window_end,
            reference,
            self.config.boundary_tolerance_seconds,
        )
        authoritative = resolutions.get(market_id)
        if authoritative and authoritative.resolved:
            label_outcome = authoritative.outcome
            label_timestamp = authoritative.resolution_timestamp or window_end
            label_source = "polymarket_gamma_resolved"
        elif self.config.allow_proxy_labels:
            if proxy_label is None:
                return "missing_label_boundaries", None
            label_outcome = proxy_label.outcome
            label_timestamp = proxy_label.resolution_timestamp
            label_source = proxy_label.source
        else:
            return "missing_authoritative_label", None

        evidence.snapshots.sort()
        anchor_target = window_start + timedelta(
            seconds=self.config.feature_anchor_seconds
        )
        selected = nearest_at_or_after(evidence.snapshots, anchor_target, window_end)
        if selected is None:
            return "missing_anchor_snapshot", None
        feature_timestamp, snapshot_obj = selected
        snapshot = dict(snapshot_obj)
        reference_to_anchor = [
            point for point in reference if point[0] <= feature_timestamp
        ]
        if not reference_to_anchor:
            return "missing_anchor_reference", None
        probability = [
            (timestamp, float(payload["yes_price"]))
            for timestamp, payload in evidence.snapshots
            if timestamp <= feature_timestamp and payload.get("yes_price") is not None
        ]
        lag = _latest_before(evidence.lag, feature_timestamp)
        micro = _latest_before_fresh(
            evidence.microstructure,
            feature_timestamp,
            self.config.asof_max_age_seconds,
        )
        returns = {
            seconds: simple_return(
                reference_to_anchor,
                feature_timestamp,
                seconds,
                self.config.asof_max_age_seconds,
            )
            for seconds in (5, 15, 30, 60)
        }
        detection = evidence.detection_delay
        yes_price = float(snapshot["yes_price"])
        no_price = float(snapshot.get("no_price", 1.0 - yes_price))
        row = TrainingRow(
            market_id=market_id,
            asset=asset,
            market_source="mock" if market_id.startswith("mock-") else "public",
            window_start=window_start.isoformat(),
            window_end=window_end.isoformat(),
            feature_timestamp=feature_timestamp.isoformat(),
            market_age_seconds=(feature_timestamp - window_start).total_seconds(),
            seconds_to_expiry=(window_end - feature_timestamp).total_seconds(),
            return_5s=returns[5],
            return_15s=returns[15],
            return_30s=returns[30],
            return_60s=returns[60],
            momentum_short=momentum(returns[5], returns[15]),
            momentum_medium=momentum(returns[15], returns[60]),
            volatility_30s=realized_volatility(
                reference_to_anchor, feature_timestamp, 30
            ),
            volatility_60s=realized_volatility(
                reference_to_anchor, feature_timestamp, 60
            ),
            yes_price=yes_price,
            no_price=no_price,
            yes_no_spread=yes_price - no_price,
            probability_change_15s=change(
                probability,
                feature_timestamp,
                15,
                self.config.asof_max_age_seconds,
            ),
            probability_change_30s=change(
                probability,
                feature_timestamp,
                30,
                self.config.asof_max_age_seconds,
            ),
            lag_score=float(lag.get("lag_score")) if lag and lag.get("lag_score") is not None else None,
            confidence_score=float(lag.get("confidence")) if lag and lag.get("confidence") is not None else None,
            detection_delay=detection,
            early_window_flag=int(
                detection is not None
                and detection <= self.config.early_window_seconds
            ),
            late_window_flag=int(
                detection is not None
                and detection > self.config.late_window_seconds
            ),
            outcome=int(label_outcome),
            resolution_timestamp=label_timestamp.isoformat(),
            label_source=label_source,
            source_session=str(session_path.relative_to(self.config.runs_root)),
            quote_age_seconds=_micro_float(micro, "quote_age_seconds"),
            time_since_quote_update_seconds=_micro_float(
                micro, "time_since_last_quote_update_seconds"
            ),
            repricing_velocity=_micro_float(micro, "repricing_velocity"),
            repricing_acceleration=_micro_float(micro, "repricing_acceleration"),
            yes_change_frequency_30s=_micro_float(
                micro, "yes_change_frequency_30s"
            ),
            no_change_frequency_30s=_micro_float(
                micro, "no_change_frequency_30s"
            ),
            consecutive_quote_stability=_micro_float(
                micro, "consecutive_quote_stability"
            ),
            bid_ask_spread=_micro_float(micro, "bid_ask_spread"),
            spread_change=_micro_float(micro, "spread_change"),
            spread_velocity=_micro_float(micro, "spread_velocity"),
            spread_compression=_micro_float(micro, "spread_compression"),
            yes_bid_size=_micro_float(micro, "yes_bid_size"),
            yes_ask_size=_micro_float(micro, "yes_ask_size"),
            total_bid_depth=_micro_float(micro, "total_bid_depth"),
            total_ask_depth=_micro_float(micro, "total_ask_depth"),
            book_imbalance=_micro_float(micro, "book_imbalance"),
            market_refresh_latency=_micro_float(
                micro, "refresh_latency_seconds"
            ),
            cross_asset_yes_dispersion=_micro_float(
                micro, "cross_asset_yes_dispersion"
            ),
            cross_asset_relative_yes=_micro_float(
                micro, "cross_asset_relative_yes"
            ),
        )
        quality = len(evidence.snapshots) + len(reference_to_anchor)
        return "", (row, quality)


def summarize(rows: list[TrainingRow]) -> dict[str, Any]:
    values = [asdict(row) for row in rows]
    missing = {
        column: sum(row[column] is None for row in values)
        for column in COLUMNS
    }
    assets: dict[str, int] = {}
    for row in rows:
        assets[row.asset] = assets.get(row.asset, 0) + 1
    numeric = [column for column in NUMERIC_COLUMNS]
    return {
        "total_samples": len(rows),
        "assets": dict(sorted(assets.items())),
        "class_balance": {
            "UP": sum(row.outcome == 1 for row in rows),
            "DOWN": sum(row.outcome == 0 for row in rows),
        },
        "feature_count": len(FEATURE_COLUMNS),
        "feature_columns": list(FEATURE_COLUMNS),
        "missing_values": missing,
        "total_missing_values": sum(missing.values()),
        "correlation_matrix": _correlations(values, numeric),
        "dataset_paths": {
            "csv": "polymarket/data/training/dataset.csv",
            "parquet": "polymarket/data/training/dataset.parquet",
        },
    }


def _missingness(rows: list[TrainingRow]) -> dict[str, Any]:
    by_feature = {
        name: sum(getattr(row, name) is None for row in rows)
        for name in CORE_FEATURE_COLUMNS
    }
    microstructure_by_feature = {
        name: sum(getattr(row, name) is None for row in rows)
        for name in MICROSTRUCTURE_FEATURE_COLUMNS
    }
    by_session: dict[str, dict[str, int]] = {}
    for row in rows:
        missing = [
            name for name in CORE_FEATURE_COLUMNS
            if getattr(row, name) is None
        ]
        session = by_session.setdefault(
            row.source_session, {"rows": 0, "missing_feature_cells": 0}
        )
        session["rows"] += 1
        session["missing_feature_cells"] += len(missing)
    cells = len(rows) * len(CORE_FEATURE_COLUMNS)
    missing_cells = sum(by_feature.values())
    return {
        "rows": len(rows),
        "feature_cells": cells,
        "missing_feature_cells": missing_cells,
        "feature_completeness_percentage": round(
            (cells - missing_cells) / cells * 100, 4
        ) if cells else 0.0,
        "missing_by_feature": by_feature,
        "microstructure_missing_by_feature": microstructure_by_feature,
        "microstructure_feature_cells": (
            len(rows) * len(MICROSTRUCTURE_FEATURE_COLUMNS)
        ),
        "microstructure_available_cells": sum(
            len(rows) - count
            for count in microstructure_by_feature.values()
        ),
        "missing_by_session": dict(sorted(by_session.items())),
    }


def _correlations(
    rows: list[dict[str, Any]], columns: list[str]
) -> dict[str, dict[str, float | None]]:
    matrix: dict[str, dict[str, float | None]] = {}
    for left in columns:
        matrix[left] = {}
        for right in columns:
            pairs = [
                (float(row[left]), float(row[right]))
                for row in rows
                if row[left] is not None and row[right] is not None
            ]
            matrix[left][right] = _pearson(pairs)
    return matrix


def _pearson(pairs: list[tuple[float, float]]) -> float | None:
    if len(pairs) < 2:
        return None
    xs, ys = zip(*pairs)
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
    denominator = (
        sum((x - mean_x) ** 2 for x in xs)
        * sum((y - mean_y) ** 2 for y in ys)
    ) ** 0.5
    return round(numerator / denominator, 8) if denominator else None


def _latest_before(
    series: list[tuple[datetime, dict[str, Any]]], timestamp: datetime
) -> dict[str, Any] | None:
    candidates = [payload for point, payload in series if point <= timestamp]
    return candidates[-1] if candidates else None


def _latest_before_fresh(
    series: list[tuple[datetime, dict[str, Any]]],
    timestamp: datetime,
    max_age_seconds: float,
) -> dict[str, Any] | None:
    candidates = [
        (point, payload) for point, payload in series if point <= timestamp
    ]
    if not candidates:
        return None
    point, payload = candidates[-1]
    if (timestamp - point).total_seconds() > max_age_seconds:
        return None
    return payload


def _micro_float(payload: dict[str, Any] | None, name: str) -> float | None:
    if not payload or payload.get(name) is None:
        return None
    return float(payload[name])


def _dt(value: str | datetime) -> datetime:
    return value if isinstance(value, datetime) else datetime.fromisoformat(value)
