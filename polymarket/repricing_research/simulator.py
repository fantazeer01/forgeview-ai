from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from .schema import (
    REPRICING_COLUMNS,
    RepricingLabelRow,
    RepricingSimulationSummary,
)


SIGNAL_REASONS = {
    "qualified_external_move_not_repriced",
    "confidence_below_threshold",
}


@dataclass(frozen=True)
class RepricingConfig:
    horizons_seconds: tuple[int, ...] = (30, 60, 120, 180)
    max_holding_seconds: float = 180.0
    repricing_target: float = 0.03
    stop_loss: float = 0.03
    conservative_slippage: float = 0.02
    min_seconds_to_expiry: float = 35.0
    signal_reasons: tuple[str, ...] = tuple(sorted(SIGNAL_REASONS))


@dataclass(frozen=True)
class _Snapshot:
    timestamp: datetime
    market_id: str
    asset: str
    yes_price: float
    no_price: float
    seconds_to_expiry: float

    @property
    def window_end(self) -> datetime:
        return self.timestamp + timedelta(seconds=self.seconds_to_expiry)


def build_repricing_dataset(
    session_paths: Iterable[str | Path],
    config: RepricingConfig | None = None,
) -> list[RepricingLabelRow]:
    cfg = config or RepricingConfig()
    rows: list[RepricingLabelRow] = []
    seen_entries: set[tuple[str, str, str]] = set()
    open_until: dict[tuple[str, str], datetime] = {}
    for session_path in session_paths:
        rows.extend(_rows_from_session(
            Path(session_path), cfg, seen_entries, open_until
        ))
    rows.sort(key=lambda row: (row.entry_timestamp, row.asset, row.market_id))
    return rows


def simulate_repricing_strategy(
    rows: list[RepricingLabelRow],
) -> RepricingSimulationSummary:
    wins = sum(row.repriced_favorably for row in rows)
    pnl_before = sum(row.simulated_pnl_before_slippage for row in rows)
    pnl_after = sum(row.simulated_pnl_after_slippage for row in rows)
    favorable = _mean([row.max_favorable_excursion for row in rows])
    adverse = _mean([row.max_adverse_excursion for row in rows])
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for row in rows:
        equity += row.simulated_pnl_after_slippage
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
    first = rows[0].entry_timestamp if rows else None
    last = rows[-1].entry_timestamp if rows else None
    hours = None
    if first and last and first != last:
        elapsed = (
            datetime.fromisoformat(last) - datetime.fromisoformat(first)
        ).total_seconds()
        hours = max(elapsed / 3600.0, 1e-9)
    return RepricingSimulationSummary(
        rows=len(rows),
        signals=len(rows),
        wins=wins,
        win_rate=wins / len(rows) if rows else None,
        average_favorable_repricing=favorable,
        average_adverse_move=adverse,
        simulated_pnl_before_fees_slippage=round(pnl_before, 8),
        simulated_pnl_after_conservative_slippage=round(pnl_after, 8),
        max_drawdown=round(max_drawdown, 8),
        expectancy_per_signal=(pnl_after / len(rows) if rows else None),
        signals_per_hour=(len(rows) / hours if hours else None),
        first_entry_timestamp=first,
        last_entry_timestamp=last,
    )


def write_outputs(
    output_dir: str | Path,
    rows: list[RepricingLabelRow],
    summary: RepricingSimulationSummary,
) -> dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    dataset_path = output / "repricing_labels.csv"
    summary_path = output / "simulation_summary.json"
    with dataset_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPRICING_COLUMNS)
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
    summary_path.write_text(
        json.dumps(asdict(summary), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return {"dataset": str(dataset_path), "summary": str(summary_path)}


def _rows_from_session(
    session_path: Path,
    config: RepricingConfig,
    seen_entries: set[tuple[str, str, str]],
    open_until: dict[tuple[str, str], datetime],
) -> list[RepricingLabelRow]:
    events = _read_events(session_path)
    references: dict[str, list[tuple[datetime, float]]] = {}
    snapshots: dict[str, list[_Snapshot]] = {}
    microstructure: dict[tuple[str, datetime], dict[str, Any]] = {}
    lag_measurements: list[tuple[datetime, str, dict[str, Any]]] = []

    for event in events:
        timestamp = datetime.fromisoformat(event["timestamp"])
        payload = event["payload"]
        kind = event["event"]
        if kind == "reference_price":
            references.setdefault(payload["asset"], []).append(
                (timestamp, float(payload["price"]))
            )
        elif kind == "polymarket_snapshot":
            snapshot = _Snapshot(
                timestamp=timestamp,
                market_id=payload["market_id"],
                asset=payload["asset"],
                yes_price=float(payload["yes_price"]),
                no_price=float(payload["no_price"]),
                seconds_to_expiry=float(payload["seconds_to_expiry"]),
            )
            snapshots.setdefault(snapshot.market_id, []).append(snapshot)
        elif kind == "microstructure_snapshot":
            microstructure[(payload["market_id"], timestamp)] = payload
        elif kind == "lag_measurement":
            lag_measurements.append(
                (timestamp, payload["market_id"], payload["measurement"])
            )

    for values in references.values():
        values.sort(key=lambda item: item[0])
    for values in snapshots.values():
        values.sort(key=lambda item: item.timestamp)

    rows: list[RepricingLabelRow] = []
    accepted_reasons = set(config.signal_reasons)
    for timestamp, market_id, measurement in lag_measurements:
        if measurement.get("reason") not in accepted_reasons:
            continue
        direction = measurement.get("direction")
        if direction not in {"UP", "DOWN"}:
            continue
        entry = _snapshot_at_or_before(snapshots.get(market_id, []), timestamp)
        if entry is None or entry.seconds_to_expiry < config.min_seconds_to_expiry:
            continue
        key = (market_id, direction, timestamp.isoformat())
        if key in seen_entries:
            continue
        seen_entries.add(key)
        future = [
            row for row in snapshots.get(market_id, [])
            if row.timestamp >= entry.timestamp
            and row.timestamp <= min(
                entry.timestamp + timedelta(seconds=config.max_holding_seconds),
                entry.window_end - timedelta(seconds=1),
            )
        ]
        if len(future) < 2:
            continue
        side = "YES" if direction == "UP" else "NO"
        position_key = (market_id, side)
        if open_until.get(position_key, datetime.min.replace(tzinfo=timestamp.tzinfo)) > timestamp:
            continue
        entry_side_price = _side_price(entry, side)
        moves = [
            (row.timestamp, _side_price(row, side) - entry_side_price)
            for row in future
        ]
        max_favorable = max(move for _, move in moves)
        max_adverse = min(move for _, move in moves)
        repricing_hit = next(
            ((ts, move) for ts, move in moves if move >= config.repricing_target),
            None,
        )
        stop_hit = next(
            ((ts, move) for ts, move in moves if move <= -config.stop_loss),
            None,
        )
        exit_ts, exit_move, exit_reason = _choose_exit(
            moves, repricing_hit, stop_hit
        )
        repriced_favorably = exit_reason == "repricing_target"
        exit_price = entry_side_price + exit_move
        micro = microstructure.get((market_id, entry.timestamp), {})
        returns = {
            seconds: _reference_return(
                references.get(entry.asset, []), entry.timestamp, seconds
            )
            for seconds in (5, 15, 30, 60)
        }
        horizon_moves = {
            seconds: _side_move_at_horizon(future, side, entry_side_price, seconds)
            for seconds in config.horizons_seconds
        }
        row = RepricingLabelRow(
            entry_timestamp=entry.timestamp.isoformat(),
            asset=entry.asset,
            market_id=market_id,
            side=side,
            yes_price_at_entry=entry.yes_price,
            no_price_at_entry=entry.no_price,
            side_price_at_entry=entry_side_price,
            external_price_move=float(measurement.get("external_price_change", 0.0)),
            external_return_5s=returns[5],
            external_return_15s=returns[15],
            external_return_30s=returns[30],
            external_return_60s=returns[60],
            momentum=_momentum(returns),
            quote_age_seconds=_float_or_none(micro.get("quote_age_seconds")),
            repricing_velocity=_float_or_none(micro.get("repricing_velocity")),
            repricing_acceleration=_float_or_none(
                micro.get("repricing_acceleration")
            ),
            spread_compression=_float_or_none(micro.get("spread_compression")),
            book_imbalance=_float_or_none(micro.get("book_imbalance")),
            cross_asset_movement=_float_or_none(
                micro.get("cross_asset_yes_dispersion")
            ),
            time_to_expiry_seconds=entry.seconds_to_expiry,
            lag_score=_float_or_none(measurement.get("lag_score")),
            polymarket_price_move_after_30s=horizon_moves.get(30),
            polymarket_price_move_after_60s=horizon_moves.get(60),
            polymarket_price_move_after_120s=horizon_moves.get(120),
            polymarket_price_move_after_180s=horizon_moves.get(180),
            max_favorable_excursion=max_favorable,
            max_adverse_excursion=max_adverse,
            time_to_repricing_seconds=(
                (repricing_hit[0] - entry.timestamp).total_seconds()
                if repriced_favorably and repricing_hit else None
            ),
            simulated_exit_timestamp=exit_ts.isoformat(),
            simulated_exit_seconds=(exit_ts - entry.timestamp).total_seconds(),
            simulated_exit_price=exit_price,
            simulated_exit_reason=exit_reason,
            simulated_pnl_before_slippage=exit_move,
            simulated_pnl_after_slippage=exit_move - config.conservative_slippage,
            repriced_favorably=repriced_favorably,
            source_session=str(session_path),
        )
        rows.append(row)
        open_until[position_key] = exit_ts
    return rows


def _read_events(session_path: Path) -> list[dict[str, Any]]:
    with session_path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _snapshot_at_or_before(
    snapshots: list[_Snapshot],
    timestamp: datetime,
) -> _Snapshot | None:
    candidate = None
    for snapshot in snapshots:
        if snapshot.timestamp > timestamp:
            break
        candidate = snapshot
    return candidate


def _side_price(snapshot: _Snapshot, side: str) -> float:
    return snapshot.yes_price if side == "YES" else snapshot.no_price


def _choose_exit(
    moves: list[tuple[datetime, float]],
    repricing_hit: tuple[datetime, float] | None,
    stop_hit: tuple[datetime, float] | None,
) -> tuple[datetime, float, str]:
    if repricing_hit and stop_hit:
        if repricing_hit[0] <= stop_hit[0]:
            return repricing_hit[0], repricing_hit[1], "repricing_target"
        return stop_hit[0], stop_hit[1], "stop_loss"
    if repricing_hit:
        return repricing_hit[0], repricing_hit[1], "repricing_target"
    if stop_hit:
        return stop_hit[0], stop_hit[1], "stop_loss"
    return moves[-1][0], moves[-1][1], "timeout"


def _side_move_at_horizon(
    future: list[_Snapshot],
    side: str,
    entry_side_price: float,
    horizon_seconds: int,
) -> float | None:
    target = future[0].timestamp + timedelta(seconds=horizon_seconds)
    candidates = [row for row in future if row.timestamp >= target]
    if not candidates:
        return None
    return _side_price(candidates[0], side) - entry_side_price


def _reference_return(
    references: list[tuple[datetime, float]],
    timestamp: datetime,
    lookback_seconds: int,
) -> float | None:
    current = _reference_at_or_before(references, timestamp)
    previous = _reference_at_or_before(
        references, timestamp - timedelta(seconds=lookback_seconds)
    )
    if current is None or previous is None or previous <= 0:
        return None
    return current / previous - 1.0


def _reference_at_or_before(
    references: list[tuple[datetime, float]],
    timestamp: datetime,
) -> float | None:
    candidate = None
    for ref_ts, price in references:
        if ref_ts > timestamp:
            break
        candidate = price
    return candidate


def _momentum(returns: dict[int, float | None]) -> float | None:
    short = returns.get(15)
    long = returns.get(60)
    if short is None or long is None:
        return None
    return short - long


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None
