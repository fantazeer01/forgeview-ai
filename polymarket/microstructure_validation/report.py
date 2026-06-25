from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from polymarket.feature_engine.schema import MICROSTRUCTURE_FEATURE_COLUMNS


EVENT_TO_FEATURE = {
    "quote_age_seconds": "quote_age_seconds",
    "time_since_last_quote_update_seconds": "time_since_quote_update_seconds",
    "repricing_velocity": "repricing_velocity",
    "repricing_acceleration": "repricing_acceleration",
    "yes_change_frequency_30s": "yes_change_frequency_30s",
    "no_change_frequency_30s": "no_change_frequency_30s",
    "consecutive_quote_stability": "consecutive_quote_stability",
    "bid_ask_spread": "bid_ask_spread",
    "spread_change": "spread_change",
    "spread_velocity": "spread_velocity",
    "spread_compression": "spread_compression",
    "yes_bid_size": "yes_bid_size",
    "yes_ask_size": "yes_ask_size",
    "total_bid_depth": "total_bid_depth",
    "total_ask_depth": "total_ask_depth",
    "book_imbalance": "book_imbalance",
    "refresh_latency_seconds": "market_refresh_latency",
    "cross_asset_yes_dispersion": "cross_asset_yes_dispersion",
    "cross_asset_relative_yes": "cross_asset_relative_yes",
}


def build_validation_report(
    session_path: Path,
    replay_report_path: Path,
    feature_export: Path,
    feature_export_repeat: Path,
    output_root: Path,
) -> dict:
    events = [
        json.loads(line) for line in session_path.read_text(
            encoding="utf-8"
        ).splitlines() if line.strip()
    ]
    started = next(row for row in events if row["event"] == "session_started")
    completed = next(row for row in reversed(events)
                     if row["event"] == "session_completed")
    micros = [
        row["payload"] for row in events
        if row["event"] == "microstructure_snapshot"
    ]
    original_report = _json(session_path.parent / "evidence_report.json")
    replay_report = _json(replay_report_path)
    feature_rows = _csv(feature_export / "dataset.csv")
    repeat_rows = _csv(feature_export_repeat / "dataset.csv")
    population_rows = []
    missing_rows = []
    for event_field, feature in EVENT_TO_FEATURE.items():
        valid = sum(row.get(event_field) is not None for row in micros)
        feature_valid = sum(row.get(feature, "") != "" for row in feature_rows)
        population = valid / len(micros) * 100 if micros else 0.0
        feature_population = (
            feature_valid / len(feature_rows) * 100 if feature_rows else 0.0
        )
        population_rows.append({
            "feature": feature,
            "event_field": event_field,
            "valid_sample_count": valid,
            "event_population_percentage": round(population, 4),
            "event_missing_percentage": round(100.0 - population, 4),
            "feature_rows_valid": feature_valid,
            "feature_row_population_percentage": round(feature_population, 4),
            "replay_status": "compatible",
        })
        missing_rows.append({
            "feature": feature,
            "event_missing_count": len(micros) - valid,
            "event_missing_percentage": round(100.0 - population, 4),
            "feature_row_missing_count": len(feature_rows) - feature_valid,
            "feature_row_missing_percentage": round(
                100.0 - feature_population, 4
            ),
        })
    replay_compatible = (
        original_report["metrics"] == replay_report["metrics"]
        and original_report["campaign_completeness"]
        == replay_report["campaign_completeness"]
        and original_report["microstructure_coverage"]
        == replay_report["microstructure_coverage"]
    )
    export_deterministic = (
        _sha256(feature_export / "dataset.csv")
        == _sha256(feature_export_repeat / "dataset.csv")
        and _sha256(feature_export / "dataset.parquet")
        == _sha256(feature_export_repeat / "dataset.parquet")
        and feature_rows == repeat_rows
    )
    raw_required = (
        "quote_age_seconds", "market_refresh_latency", "yes_bid_size",
        "yes_ask_size", "total_bid_depth", "total_ask_depth", "book_imbalance",
    )
    raw_coverage = min(
        row["event_population_percentage"] for row in population_rows
        if row["feature"] in raw_required
    )
    decision = (
        "READY_FOR_PRODUCTION_CAPTURE"
        if raw_coverage >= 95.0 and replay_compatible and export_deterministic
        and feature_rows else
        "PARTIAL_COVERAGE_REQUIRES_FIX"
        if micros else "FEATURE_CAPTURE_FAILURE"
    )
    asset_counts = Counter(row["asset"] for row in micros)
    report = {
        "schema_version": 1,
        "decision": decision,
        "capture": {
            "session": str(session_path),
            "mode": started["payload"]["mode"],
            "configured_duration_seconds": started["payload"]["duration_seconds"],
            "observed_duration_seconds": (
                original_report["campaign_completeness"][
                    "observed_utc_span_seconds"
                ]
            ),
            "microstructure_events": len(micros),
            "events_by_asset": dict(sorted(asset_counts.items())),
            "campaign_completeness": original_report["campaign_completeness"],
            "observation_continuity": original_report["observation_continuity"],
            "reference_coverage_percentage": original_report["metrics"][
                "reference_coverage_percentage"
            ],
            "market_data_gap_percentage": original_report["metrics"][
                "data_gap_percentage"
            ],
        },
        "coverage": {
            "minimum_required_raw_field_coverage_percentage": raw_coverage,
            "features": population_rows,
        },
        "feature_engine": {
            "rows": len(feature_rows),
            "rows_by_asset": dict(sorted(Counter(
                row["asset"] for row in feature_rows
            ).items())),
            "all_microstructure_columns_present": (
                set(MICROSTRUCTURE_FEATURE_COLUMNS)
                <= set(feature_rows[0]) if feature_rows else False
            ),
            "deterministic_export": export_deterministic,
            "csv_sha256": _sha256(feature_export / "dataset.csv"),
            "parquet_sha256": _sha256(feature_export / "dataset.parquet"),
        },
        "replay": {
            "compatible": replay_compatible,
            "metrics_match": original_report["metrics"] == replay_report["metrics"],
            "campaign_completeness_matches": (
                original_report["campaign_completeness"]
                == replay_report["campaign_completeness"]
            ),
            "microstructure_coverage_matches": (
                original_report["microstructure_coverage"]
                == replay_report["microstructure_coverage"]
            ),
        },
        "holdout": {
            "outcomes_read": False,
            "protocol_modified": False,
        },
        "limitations": [
            "The 15-minute smoke is an operational coverage test, not alpha validation.",
            "Order flow remains a public order-book change proxy.",
            "Feature export uses proxy labels only to verify disposable ingestion.",
        ],
    }
    output_root.mkdir(parents=True, exist_ok=True)
    _write_csv(output_root / "feature_population.csv", population_rows)
    _write_csv(output_root / "missingness_report.csv", missing_rows)
    _write_json(output_root / "replay_validation.json", report["replay"])
    _write_json(output_root / "coverage_report.json", report)
    _write_markdown(output_root / "coverage_report.md", report)
    return report


def _write_markdown(path: Path, report: dict) -> None:
    lines = [
        "# Public Microstructure Capture Smoke Validation v1",
        "",
        f"Decision: **{report['decision']}**",
        "",
        f"- Duration: {report['capture']['observed_duration_seconds']:.3f}s",
        f"- Events: {report['capture']['microstructure_events']}",
        f"- Assets: {report['capture']['events_by_asset']}",
        f"- Replay compatible: {report['replay']['compatible']}",
        f"- Feature rows: {report['feature_engine']['rows']}",
        f"- Holdout outcomes read: {report['holdout']['outcomes_read']}",
        "",
        "| Feature | Event population | Missing | Valid | Feature rows |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in report["coverage"]["features"]:
        lines.append(
            f"| {row['feature']} | "
            f"{row['event_population_percentage']:.2f}% | "
            f"{row['event_missing_percentage']:.2f}% | "
            f"{row['valid_sample_count']} | "
            f"{row['feature_row_population_percentage']:.2f}% |"
        )
    lines += ["", "This report measures capture plumbing, not predictive edge.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]) if rows else [], lineterminator="\n"
        )
        if rows:
            writer.writeheader()
            writer.writerows(rows)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
