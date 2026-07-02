from __future__ import annotations

import csv
import hashlib
import json
import math
from bisect import bisect_left, bisect_right
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean, stdev


def run_stress_analysis(specification: Path, output: Path) -> dict:
    spec = json.loads(specification.read_text(encoding="utf-8"))
    root = specification.resolve().parents[4]
    rows = []
    for session_number, relative in enumerate(spec["input_datasets"], 1):
        with (root / relative).open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                row["session_number"] = session_number
                rows.append(row)
    rows.sort(key=lambda row: row["entry_timestamp"])
    enrichment = _enrich_execution_fields(rows, root)
    output.mkdir(parents=True, exist_ok=True)
    result_rows = []
    scenario_summaries = []
    for scenario in spec["scenarios"]:
        stressed = [_stress_row(row, scenario) for row in rows]
        result_rows.extend(stressed)
        scenario_summaries.append(_summary(scenario["name"], stressed))
    _write_csv(output / "stress_results.csv", result_rows)
    segments = _segments(result_rows)
    _write_csv(output / "segment_stability.csv", segments)
    quote_rows = []
    quote_summaries = []
    for scenario in spec["actual_quote_replay_scenarios"]:
        replayed = [_quote_replay_row(row, scenario) for row in rows]
        quote_rows.extend(replayed)
        quote_summaries.append(_summary(scenario["name"], replayed))
    _write_csv(output / "quote_replay_results.csv", quote_rows)
    quote_segments = _segments(quote_rows)
    _write_csv(output / "quote_segment_stability.csv", quote_segments)
    report = {
        "frozen_specification": spec,
        "holdout_status": "sealed_holdout_not_inspected_no_holdout_evaluation_run",
        "rows": len(rows),
        "execution_field_enrichment": enrichment,
        "scenarios": scenario_summaries,
        "actual_quote_replay_scenarios": quote_summaries,
        "actual_quote_replay_segments": quote_segments,
        "segments": segments,
    }
    (output / "stress_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def _stress_row(row: dict[str, str], scenario: dict) -> dict:
    side_sign = 1.0 if row["side"] == "YES" else -1.0
    delay = float(scenario["delay_seconds"])
    velocity = _number(row["repricing_velocity"])
    acceleration = _number(row["repricing_acceleration"])
    delay_cost = max(0.0, side_sign * (velocity * delay + 0.5 * acceleration * delay * delay))
    quote_age_cost = (
        abs(velocity)
        * min(_number(row["quote_age_seconds"]), 10.0)
        * float(scenario["quote_age_multiplier"])
    )
    spread_cost = _number(row["bid_ask_spread"]) * float(scenario["spread_multiplier"])
    transaction_cost = float(scenario["transaction_cost"])
    identity = "|".join((row["source_session"], row["market_id"], row["entry_timestamp"]))
    score = int(hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16], 16) / 2**64
    missed = score < float(scenario["miss_rate"])
    size = _number(row["yes_ask_size"] if row["side"] == "YES" else row["yes_bid_size"])
    order_size = float(scenario["order_size_shares"])
    liquidity_ratio = 1.0 if order_size <= 0 else min(1.0, size / order_size)
    fill_ratio = 0.0 if missed else min(float(scenario["max_fill_fraction"]), liquidity_ratio)
    base_pnl = _number(row["simulated_pnl_after_slippage"])
    unit_pnl = base_pnl - spread_cost - delay_cost - quote_age_cost - transaction_cost
    return {
        "scenario": scenario["name"],
        "session_number": row["session_number"],
        "entry_timestamp": row["entry_timestamp"],
        "market_id": row["market_id"],
        "asset": row["asset"],
        "side": row["side"],
        "external_move_regime": _bucket_abs(_number(row["external_price_move"]), 0.001, 0.002),
        "spread_regime": _bucket(_number(row["bid_ask_spread"]), 0.01, 0.03),
        "quote_age_regime": _bucket(_number(row["quote_age_seconds"]), 2.0, 5.0),
        "base_pnl": base_pnl,
        "spread_cost": spread_cost,
        "delay_cost": delay_cost,
        "quote_age_cost": quote_age_cost,
        "transaction_cost": transaction_cost,
        "missed_fill": missed,
        "fill_ratio": fill_ratio,
        "stressed_pnl": fill_ratio * unit_pnl,
    }


def _enrich_execution_fields(rows: list[dict], root: Path) -> dict:
    required = ("bid_ask_spread", "yes_ask_size", "yes_bid_size")
    by_source = defaultdict(list)
    for row in rows:
        by_source[row["source_session"]].append(row)
    populated = 0
    for source, source_rows in by_source.items():
        path = Path(source)
        if not path.is_file():
            path = root / source
        relevant = {row["market_id"] for row in source_rows}
        snapshots = defaultdict(list)
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                event = json.loads(line)
                if event.get("event") != "microstructure_snapshot":
                    continue
                payload = event.get("payload", {})
                market_id = payload.get("market_id")
                if market_id in relevant:
                    snapshots[market_id].append((event["timestamp"], payload))
        for row in source_rows:
            history = snapshots.get(row["market_id"], [])
            index = bisect_right([item[0] for item in history], row["entry_timestamp"]) - 1
            if index < 0:
                continue
            payload = history[index][1]
            row["_execution_snapshots"] = history
            for field in required:
                row[field] = payload.get(field, "")
            if all(row.get(field, "") != "" for field in required):
                populated += 1
    return {
        "required_fields": list(required),
        "populated_rows": populated,
        "total_rows": len(rows),
        "coverage_percentage": 100.0 * populated / len(rows) if rows else 0.0,
    }


def _quote_replay_row(row: dict, scenario: dict) -> dict:
    history = row.get("_execution_snapshots", [])
    signal_time = datetime.fromisoformat(row["entry_timestamp"])
    entry_time = signal_time + timedelta(seconds=float(scenario["delay_seconds"]))
    timestamps = [datetime.fromisoformat(item[0]) for item in history]
    entry_index = bisect_left(timestamps, entry_time)
    missed = entry_index >= len(history)
    fill_ratio = 0.0
    pnl = 0.0
    if not missed:
        entry_payload = history[entry_index][1]
        entry_price, entry_size = _executable_price(entry_payload, row["side"], entering=True)
        order_size = float(scenario["order_size_shares"])
        fill_ratio = min(1.0, entry_size / order_size) if order_size > 0 else 1.0
        deadline = entry_time + timedelta(seconds=180)
        exit_price = entry_price
        exit_size = entry_size
        for timestamp_text, payload in history[entry_index + 1:]:
            timestamp = datetime.fromisoformat(timestamp_text)
            if timestamp > deadline:
                break
            candidate, candidate_size = _executable_price(payload, row["side"], entering=False)
            exit_price, exit_size = candidate, candidate_size
            move = exit_price - entry_price
            if move >= 0.03 or move <= -0.03:
                break
        fill_ratio = min(fill_ratio, exit_size / order_size) if order_size > 0 else fill_ratio
        pnl = fill_ratio * (exit_price - entry_price - float(scenario["transaction_cost"]))
    return {
        "scenario": scenario["name"],
        "session_number": row["session_number"],
        "entry_timestamp": row["entry_timestamp"],
        "market_id": row["market_id"],
        "asset": row["asset"],
        "side": row["side"],
        "external_move_regime": _bucket_abs(_number(row["external_price_move"]), 0.001, 0.002),
        "spread_regime": _bucket(_number(row["bid_ask_spread"]), 0.01, 0.03),
        "quote_age_regime": _bucket(_number(row["quote_age_seconds"]), 2.0, 5.0),
        "base_pnl": _number(row["simulated_pnl_after_slippage"]),
        "spread_cost": 0.0,
        "delay_cost": 0.0,
        "quote_age_cost": 0.0,
        "transaction_cost": float(scenario["transaction_cost"]),
        "missed_fill": missed,
        "fill_ratio": fill_ratio,
        "stressed_pnl": pnl,
    }


def _executable_price(payload: dict, side: str, *, entering: bool) -> tuple[float, float]:
    if side == "YES":
        return (
            _number(payload["yes_ask"] if entering else payload["yes_bid"]),
            _number(payload["yes_ask_size"] if entering else payload["yes_bid_size"]),
        )
    return (
        1.0 - _number(payload["yes_bid"] if entering else payload["yes_ask"]),
        _number(payload["yes_bid_size"] if entering else payload["yes_ask_size"]),
    )


def _summary(name: str, rows: list[dict]) -> dict:
    pnl = [float(row["stressed_pnl"]) for row in rows]
    executed = [row for row in rows if float(row["fill_ratio"]) > 0]
    positive = sum(float(row["stressed_pnl"]) > 0 for row in executed)
    total = sum(pnl)
    expectation = mean(pnl)
    standard_error = stdev(pnl) / math.sqrt(len(pnl))
    by_session = _group_expectancy(rows, "session_number")
    by_asset = _group_expectancy(rows, "asset")
    by_side = _group_expectancy(rows, "side")
    return {
        "scenario": name,
        "attempted_signals": len(rows),
        "executed_signals": len(executed),
        "missed_signals": len(rows) - len(executed),
        "average_fill_ratio": mean(float(row["fill_ratio"]) for row in rows),
        "win_rate_executed": positive / len(executed) if executed else 0.0,
        "expectancy_per_attempt": expectation,
        "expectancy_nominal_95_interval": [expectation - 1.96 * standard_error, expectation + 1.96 * standard_error],
        "pnl_after_stress": total,
        "max_drawdown": _max_drawdown(pnl),
        "positive_sessions": sum(value["expectancy"] > 0 for value in by_session.values()),
        "by_session": by_session,
        "by_asset": by_asset,
        "by_side": by_side,
        "top_10_signal_pnl_share": _top_share(pnl, 10, total),
        "largest_session_pnl_share": _largest_positive_share(by_session, total),
        "largest_asset_pnl_share": _largest_positive_share(by_asset, total),
    }


def _segments(rows: list[dict]) -> list[dict]:
    output = []
    for scenario in sorted({row["scenario"] for row in rows}):
        selected = [row for row in rows if row["scenario"] == scenario]
        for dimension in (
            "session_number", "asset", "side", "external_move_regime",
            "spread_regime", "quote_age_regime",
        ):
            for value, metrics in _group_expectancy(selected, dimension).items():
                output.append({"scenario": scenario, "dimension": dimension, "segment": value, **metrics})
    return output


def _group_expectancy(rows: list[dict], key: str) -> dict:
    grouped = defaultdict(list)
    for row in rows:
        grouped[str(row[key])].append(float(row["stressed_pnl"]))
    return {key: {"signals": len(values), "pnl": sum(values), "expectancy": mean(values), "max_drawdown": _max_drawdown(values)} for key, values in sorted(grouped.items())}


def _max_drawdown(values: list[float]) -> float:
    cumulative = peak = drawdown = 0.0
    for value in values:
        cumulative += value
        peak = max(peak, cumulative)
        drawdown = max(drawdown, peak - cumulative)
    return drawdown


def _top_share(values: list[float], count: int, total: float) -> float | None:
    return sum(sorted((value for value in values if value > 0), reverse=True)[:count]) / total if total > 0 else None


def _largest_positive_share(groups: dict, total: float) -> float | None:
    return max((value["pnl"] for value in groups.values()), default=0.0) / total if total > 0 else None


def _number(value: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0
    return result if math.isfinite(result) else 0.0


def _bucket(value: float, low: float, high: float) -> str:
    return "low" if value <= low else "medium" if value <= high else "high"


def _bucket_abs(value: float, low: float, high: float) -> str:
    return _bucket(abs(value), low, high)


def _write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
