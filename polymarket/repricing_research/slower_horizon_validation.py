from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean


HORIZONS = (30, 60, 120, 180)
DIRECTIONS = ("continuation", "mean_reversion")
ENTRY_DELAY_SECONDS = 2.0
TRANSACTION_COST = 0.005
MAX_SNAPSHOT_LAG_SECONDS = 5.0
RANDOM_TRIALS = 1000


def run_slower_horizon_validation(root: Path, output: Path) -> dict:
    inputs = (
        "polymarket/data/repricing_research_balanced_batch_001/repricing_labels.csv",
        "polymarket/data/repricing_research_balanced_batch_002/repricing_labels.csv",
        "polymarket/runs/repricing_paper_soak_v4/20260701_212557/postprocess/repricing_dataset/repricing_labels.csv",
    )
    rows = _load_rows(root, inputs)
    histories = _load_histories(root, rows)
    results: list[dict] = []
    for row in rows:
        history = histories[(row["source_session"], row["market_id"])]
        for horizon in HORIZONS:
            for direction in DIRECTIONS:
                result = _evaluate(row, history, horizon, direction)
                if result is not None:
                    results.append(result)

    summaries = []
    for horizon in HORIZONS:
        for direction in DIRECTIONS:
            selected = [
                row for row in results
                if row["horizon_seconds"] == horizon and row["direction"] == direction
            ]
            summaries.append(_summarize(selected, horizon, direction, histories))
    _holm_adjust(summaries)

    decision = (
        "GO_ADVANCE_PREREGISTERED_SLOWER_HORIZON_TO_PROSPECTIVE_SHADOW"
        if any(row["passes_all_gates"] for row in summaries)
        else "NO_GO_FREEZE_REPRICING_PERMANENTLY"
    )
    report = {
        "task": "Repricing Slower-Horizon Derivative Validation v1",
        "frozen_specification": {
            "input_datasets": list(inputs),
            "signal_anchors": len(rows),
            "horizons_seconds": list(HORIZONS),
            "directions": list(DIRECTIONS),
            "entry_delay_seconds": ENTRY_DELAY_SECONDS,
            "entry_price": "first executable ask at or after signal + 2 seconds",
            "exit_price": "first executable bid at or after signal + fixed horizon",
            "transaction_cost_probability_points": TRANSACTION_COST,
            "spread_and_slippage": "realized by executable ask-to-bid quote replay",
            "maximum_snapshot_lag_seconds": MAX_SNAPSHOT_LAG_SECONDS,
            "expiry_rule": "exclude when fixed horizon exceeds signal time-to-expiry",
            "random_timing_trials": RANDOM_TRIALS,
        },
        "holdout_status": "sealed_holdout_not_inspected_no_holdout_evaluation_run",
        "rows": len(results),
        "summaries": summaries,
        "decision": decision,
        "decision_rule": (
            "Advance only if one preregistered horizon/direction has positive expectancy, "
            "a Holm-adjusted 95% confidence interval above zero, random-timing p<=0.05, "
            "positive expectancy in every session, and no session or asset above 40% of positive P&L."
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    _write_csv(output / "slower_horizon_results.csv", results)
    _write_csv(output / "horizon_comparison.csv", summaries)
    (output / "validation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def _load_rows(root: Path, inputs: tuple[str, ...]) -> list[dict]:
    rows = []
    for session_number, relative in enumerate(inputs, 1):
        with (root / relative).open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                row["session_number"] = session_number
                source = Path(row["source_session"])
                if not source.is_absolute():
                    source = root / source
                source = source.resolve()
                try:
                    row["source_session"] = source.relative_to(root.resolve()).as_posix()
                except ValueError:
                    row["source_session"] = str(source)
                rows.append(row)
    rows.sort(key=lambda row: (row["entry_timestamp"], row["market_id"]))
    return rows


def _load_histories(root: Path, rows: list[dict]) -> dict:
    wanted: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        wanted[row["source_session"]].add(row["market_id"])
    histories = {}
    for source, market_ids in wanted.items():
        by_market: dict[str, list] = defaultdict(list)
        source_path = Path(source)
        if not source_path.is_absolute():
            source_path = root / source_path
        with source_path.open(encoding="utf-8") as handle:
            for line in handle:
                event = json.loads(line)
                if event.get("event") != "microstructure_snapshot":
                    continue
                payload = event.get("payload", {})
                market_id = payload.get("market_id")
                if market_id in market_ids:
                    by_market[market_id].append((datetime.fromisoformat(event["timestamp"]), payload))
        for market_id in market_ids:
            history = sorted(by_market.get(market_id, []), key=lambda item: item[0])
            histories[(source, market_id)] = history
    return histories


def _evaluate(row: dict, history: list, horizon: int, direction: str) -> dict | None:
    if not history:
        return None
    try:
        time_to_expiry = float(row["time_to_expiry_seconds"])
    except (KeyError, TypeError, ValueError):
        return None
    if not math.isfinite(time_to_expiry) or time_to_expiry < horizon:
        return None
    signal_time = datetime.fromisoformat(row["entry_timestamp"])
    entry_target = signal_time + timedelta(seconds=ENTRY_DELAY_SECONDS)
    exit_target = signal_time + timedelta(seconds=horizon)
    timestamps = [item[0] for item in history]
    entry_index = bisect_left(timestamps, entry_target)
    exit_index = bisect_left(timestamps, exit_target)
    if entry_index >= len(history) or exit_index >= len(history) or exit_index <= entry_index:
        return None
    entry_time, entry_payload = history[entry_index]
    exit_time, exit_payload = history[exit_index]
    if (entry_time - entry_target).total_seconds() > MAX_SNAPSHOT_LAG_SECONDS:
        return None
    if (exit_time - exit_target).total_seconds() > MAX_SNAPSHOT_LAG_SECONDS:
        return None
    side = row["side"]
    if direction == "mean_reversion":
        side = "NO" if side == "YES" else "YES"
    entry_price = _executable_price(entry_payload, side, entering=True)
    exit_price = _executable_price(exit_payload, side, entering=False)
    if entry_price is None or exit_price is None:
        return None
    pnl = exit_price - entry_price - TRANSACTION_COST
    return {
        "entry_timestamp": row["entry_timestamp"],
        "session_number": int(row["session_number"]),
        "market_id": row["market_id"],
        "asset": row["asset"],
        "detector_side": row["side"],
        "traded_side": side,
        "direction": direction,
        "horizon_seconds": horizon,
        "entry_quote_timestamp": entry_time.isoformat(),
        "exit_quote_timestamp": exit_time.isoformat(),
        "entry_price": entry_price,
        "exit_price": exit_price,
        "transaction_cost": TRANSACTION_COST,
        "pnl": pnl,
        "win": pnl > 0,
        "source_session": row["source_session"],
    }


def _executable_price(payload: dict, side: str, *, entering: bool) -> float | None:
    try:
        if side == "YES":
            value = payload["yes_ask" if entering else "yes_bid"]
        else:
            yes_value = payload["yes_bid" if entering else "yes_ask"]
            value = 1.0 - float(yes_value)
        value = float(value)
    except (KeyError, TypeError, ValueError):
        return None
    return value if math.isfinite(value) and 0 <= value <= 1 else None


def _summarize(rows: list[dict], horizon: int, direction: str, histories: dict) -> dict:
    values = [float(row["pnl"]) for row in rows]
    by_session = _group(rows, "session_number")
    by_asset = _group(rows, "asset")
    ci = _cluster_bootstrap_ci(rows, 0.05, seed=20260704 + horizon + (1 if direction == "mean_reversion" else 0))
    adjusted_ci = _cluster_bootstrap_ci(
        rows, 0.05 / (len(HORIZONS) * len(DIRECTIONS)),
        seed=20261704 + horizon + (1 if direction == "mean_reversion" else 0),
    )
    random_expectancies = _random_timing_expectancies(rows, histories, horizon, direction)
    expectancy = mean(values) if values else None
    random_p = (
        (1 + sum(value >= expectancy for value in random_expectancies)) / (1 + len(random_expectancies))
        if values and random_expectancies else None
    )
    total = sum(values) if values else 0.0
    return {
        "horizon_seconds": horizon,
        "direction": direction,
        "signal_count": len(rows),
        "win_rate": sum(value > 0 for value in values) / len(values) if values else None,
        "expectancy": expectancy,
        "pnl": total,
        "max_drawdown": _max_drawdown(values),
        "cluster_bootstrap_95_low": ci[0],
        "cluster_bootstrap_95_high": ci[1],
        "bonferroni_8way_95_low": adjusted_ci[0],
        "bonferroni_8way_95_high": adjusted_ci[1],
        "positive_sessions": sum(item["expectancy"] > 0 for item in by_session.values()),
        "session_count": len(by_session),
        "by_session": json.dumps(by_session, sort_keys=True, separators=(",", ":")),
        "by_asset": json.dumps(by_asset, sort_keys=True, separators=(",", ":")),
        "largest_session_positive_pnl_share": _largest_share(by_session, total),
        "largest_asset_positive_pnl_share": _largest_share(by_asset, total),
        "matched_random_timing_trials": len(random_expectancies),
        "matched_random_expectancy_mean": mean(random_expectancies) if random_expectancies else None,
        "matched_random_timing_p_value": random_p,
        "holm_adjusted_random_p_value": None,
        "passes_all_gates": False,
    }


def _group(rows: list[dict], key: str) -> dict:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        grouped[str(row[key])].append(float(row["pnl"]))
    return {
        name: {
            "signals": len(values),
            "expectancy": mean(values),
            "pnl": sum(values),
            "max_drawdown": _max_drawdown(values),
        }
        for name, values in sorted(grouped.items())
    }


def _cluster_bootstrap_ci(rows: list[dict], alpha: float, seed: int) -> tuple[float | None, float | None]:
    if not rows:
        return None, None
    clusters: dict[tuple, list[float]] = defaultdict(list)
    for row in rows:
        clusters[(row["session_number"], row["market_id"])].append(float(row["pnl"]))
    keys = sorted(clusters)
    rng = random.Random(seed)
    means = []
    for _ in range(5000):
        sample = [clusters[rng.choice(keys)] for _ in keys]
        flattened = [value for cluster in sample for value in cluster]
        means.append(mean(flattened))
    means.sort()
    low = means[max(0, int((alpha / 2) * len(means)))]
    high = means[min(len(means) - 1, int((1 - alpha / 2) * len(means)) - 1)]
    return low, high


def _random_timing_expectancies(rows: list[dict], histories: dict, horizon: int, direction: str) -> list[float]:
    if not rows:
        return []
    prepared = []
    for row in rows:
        history = histories[(row["source_session"], row["market_id"])]
        times = [item[0] for item in history]
        candidates = []
        for index, (timestamp, payload) in enumerate(history):
            exit_index = bisect_left(times, timestamp + timedelta(seconds=horizon - ENTRY_DELAY_SECONDS))
            if exit_index >= len(history):
                continue
            if (times[exit_index] - (timestamp + timedelta(seconds=horizon - ENTRY_DELAY_SECONDS))).total_seconds() > MAX_SNAPSHOT_LAG_SECONDS:
                continue
            side = row["detector_side"]
            if direction == "mean_reversion":
                side = "NO" if side == "YES" else "YES"
            entry = _executable_price(payload, side, entering=True)
            exit_price = _executable_price(history[exit_index][1], side, entering=False)
            if entry is not None and exit_price is not None:
                candidates.append(exit_price - entry - TRANSACTION_COST)
        if candidates:
            prepared.append((row, candidates))
    if len(prepared) != len(rows):
        return []
    output = []
    for trial in range(RANDOM_TRIALS):
        values = []
        for row, candidates in prepared:
            identity = f"{trial}|{row['entry_timestamp']}|{row['market_id']}|{direction}|{horizon}"
            index = int(hashlib.sha256(identity.encode()).hexdigest()[:16], 16) % len(candidates)
            values.append(candidates[index])
        output.append(mean(values))
    return output


def _holm_adjust(summaries: list[dict]) -> None:
    valid = [row for row in summaries if row["matched_random_timing_p_value"] is not None]
    ordered = sorted(valid, key=lambda row: row["matched_random_timing_p_value"])
    running = 0.0
    count = len(ordered)
    for index, row in enumerate(ordered):
        adjusted = min(1.0, (count - index) * row["matched_random_timing_p_value"])
        running = max(running, adjusted)
        row["holm_adjusted_random_p_value"] = running
    for row in summaries:
        row["passes_all_gates"] = bool(
            row["signal_count"]
            and row["expectancy"] > 0
            and row["bonferroni_8way_95_low"] is not None
            and row["bonferroni_8way_95_low"] > 0
            and row["holm_adjusted_random_p_value"] is not None
            and row["holm_adjusted_random_p_value"] <= 0.05
            and row["positive_sessions"] == row["session_count"]
            and (row["largest_session_positive_pnl_share"] or 1) <= 0.40
            and (row["largest_asset_positive_pnl_share"] or 1) <= 0.40
        )


def _max_drawdown(values: list[float]) -> float:
    cumulative = peak = drawdown = 0.0
    for value in values:
        cumulative += value
        peak = max(peak, cumulative)
        drawdown = max(drawdown, peak - cumulative)
    return drawdown


def _largest_share(groups: dict, total: float) -> float | None:
    if total <= 0 or not groups:
        return None
    return max((value["pnl"] for value in groups.values()), default=0.0) / total


def _write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
