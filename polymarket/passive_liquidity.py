from __future__ import annotations

import csv
import json
import random
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean

from polymarket.structural_mispricing import (
    MAX_QUOTE_AGE_SECONDS,
    _build_episodes,
    _read_session,
)


QUEUE_FILL_RATIO = 0.375
ORDER_SIZE_SHARES = 250.0
MAX_FILLED_SHARES = 125.0
PER_FILLED_LEG_COST = 0.005
CANCELLATION_LATENCY_SECONDS = 2.0
PRIMARY_QUOTE_AGE_SECONDS = 2.0
POLICIES = (
    ("all_assets_2s", 2, "ALL", "standard"),
    ("all_assets_5s", 5, "ALL", "standard"),
    ("all_assets_15s", 15, "ALL", "standard"),
    ("all_assets_30s", 30, "ALL", "standard"),
    ("btc_15s", 15, "BTC", "standard"),
    ("eth_15s", 15, "ETH", "standard"),
    ("sol_15s", 15, "SOL", "standard"),
    ("near_expiry_5s", 5, "ALL", "near_expiry"),
)


def run_passive_liquidity_triage(root: Path, output: Path) -> dict:
    observations = []
    sessions = []
    from polymarket.structural_mispricing import SESSION_PATHS

    for number, relative in enumerate(SESSION_PATHS, 1):
        summary, rows = _read_session(root / relative, number, relative)
        sessions.append(summary)
        observations.extend(rows)
    histories = _histories(observations)
    wide_episodes = [episode for episode in _build_episodes(observations) if episode["kind"] == "wide_spread"]
    opportunity_rows = [episode["first_row"] for episode in wide_episodes]
    results = []
    summaries = []
    for name, lifetime, asset, regime in POLICIES:
        attempts = []
        for row in opportunity_rows:
            if asset != "ALL" and row["asset"] != asset:
                continue
            if row["quote_age_seconds"] > PRIMARY_QUOTE_AGE_SECONDS:
                continue
            if regime == "near_expiry":
                if not (lifetime + CANCELLATION_LATENCY_SECONDS < row["seconds_to_expiry"] <= 30):
                    continue
            elif row["seconds_to_expiry"] <= lifetime + CANCELLATION_LATENCY_SECONDS + 30:
                continue
            result = _evaluate_attempt(row, histories[(row["session_number"], row["market_id"])], lifetime)
            if result is not None:
                result["policy"] = name
                attempts.append(result)
                results.append(result)
        summaries.append(_summarize(name, lifetime, asset, regime, attempts, sessions))
    decision = "B_FREEZE_PASSIVE_LIQUIDITY_PROVISION_RECOMMEND_NEW_DIRECTION"
    report = {
        "task": "Polymarket Passive Liquidity Provision Existing-Data Feasibility Triage v1",
        "decision": decision,
        "frozen_specification": {
            "policies": [list(item) for item in POLICIES],
            "queue_fill_ratio": QUEUE_FILL_RATIO,
            "queue_basis": "existing severe 50% fill cap multiplied by 75% non-miss rate",
            "fill_proxy_bid": "subsequent fresh best bid moves below posted bid",
            "fill_proxy_ask": "subsequent fresh best ask moves above posted ask",
            "per_filled_leg_cost": PER_FILLED_LEG_COST,
            "cancellation_latency_seconds": CANCELLATION_LATENCY_SECONDS,
            "primary_quote_age_seconds": PRIMARY_QUOTE_AGE_SECONDS,
            "maximum_filled_shares_per_side": MAX_FILLED_SHARES,
            "inventory_exit": "first fresh executable bid/ask at quote lifetime plus cancellation latency",
            "near_expiry_buffer_seconds": 30,
        },
        "dataset": {
            "sessions": len(sessions),
            "scheduled_hours": sum(row["expected_duration_seconds"] for row in sessions) / 3600,
            "wide_spread_episodes": len(wide_episodes),
            "candidate_episode_starts": len(opportunity_rows),
        },
        "policy_summaries": summaries,
        "comparison_to_frozen_branches": {
            "wallet": "frozen; conservative expectancy -0.038117 on 124 signals",
            "repricing": "frozen; actual 2s entry plus cost expectancy -0.009810",
            "structural_mispricing": "frozen; best marketable margin -0.040000",
            "passive_liquidity": "evaluated here with inferred fills; no production or fill claim",
        },
        "holdout_status": "sealed_holdout_not_inspected_no_holdout_evaluation_run",
    }
    output.mkdir(parents=True, exist_ok=True)
    _write_csv(output / "passive_lp_attempts.csv", results)
    _write_csv(output / "passive_lp_policy_summary.csv", summaries)
    (output / "passive_lp_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def _histories(rows: list[dict]) -> dict:
    output = defaultdict(list)
    for row in rows:
        if row["valid"] and not row["stale"]:
            output[(row["session_number"], row["market_id"])].append(row)
    for values in output.values():
        values.sort(key=lambda row: row["timestamp"])
    return output


def _evaluate_attempt(row: dict, history: list[dict], lifetime: int) -> dict | None:
    start = datetime.fromisoformat(row["timestamp"])
    deadline = start + timedelta(seconds=lifetime + CANCELLATION_LATENCY_SECONDS)
    timestamps = [datetime.fromisoformat(item["timestamp"]) for item in history]
    start_index = bisect_left(timestamps, start)
    exit_index = bisect_left(timestamps, deadline)
    if exit_index >= len(history):
        return None
    exit_row = history[exit_index]
    if (timestamps[exit_index] - deadline).total_seconds() > MAX_QUOTE_AGE_SECONDS:
        return None
    bid_trigger = ask_trigger = None
    for candidate in history[start_index + 1:exit_index + 1]:
        if bid_trigger is None and candidate["yes_bid"] < row["yes_bid"]:
            bid_trigger = candidate
        if ask_trigger is None and candidate["yes_ask"] > row["yes_ask"]:
            ask_trigger = candidate
        if bid_trigger is not None and ask_trigger is not None:
            break
    bid_quantity = (
        min(row["yes_bid_size"], MAX_FILLED_SHARES) * QUEUE_FILL_RATIO
        if bid_trigger is not None else 0.0
    )
    ask_quantity = (
        min(row["yes_ask_size"], MAX_FILLED_SHARES) * QUEUE_FILL_RATIO
        if ask_trigger is not None else 0.0
    )
    matched = min(bid_quantity, ask_quantity)
    long_inventory = bid_quantity - matched
    short_inventory = ask_quantity - matched
    spread_pnl = matched * (row["yes_ask"] - row["yes_bid"] - 2 * PER_FILLED_LEG_COST)
    long_pnl = long_inventory * (
        exit_row["yes_bid"] - row["yes_bid"] - PER_FILLED_LEG_COST
    )
    short_pnl = short_inventory * (
        row["yes_ask"] - exit_row["yes_ask"] - PER_FILLED_LEG_COST
    )
    pnl = spread_pnl + long_pnl + short_pnl
    filled_quantity = bid_quantity + ask_quantity
    return {
        "session_number": row["session_number"],
        "market_id": row["market_id"],
        "asset": row["asset"],
        "timestamp": row["timestamp"],
        "seconds_to_expiry": row["seconds_to_expiry"],
        "quote_age_seconds": row["quote_age_seconds"],
        "lifetime_seconds": lifetime,
        "cancellation_latency_seconds": CANCELLATION_LATENCY_SECONDS,
        "spread": row["spread"],
        "posted_bid": row["yes_bid"],
        "posted_ask": row["yes_ask"],
        "bid_fill_proxy": bid_trigger is not None,
        "ask_fill_proxy": ask_trigger is not None,
        "two_sided_fill_proxy": bid_trigger is not None and ask_trigger is not None,
        "bid_expected_filled_shares": bid_quantity,
        "ask_expected_filled_shares": ask_quantity,
        "matched_shares": matched,
        "unmatched_long_shares": long_inventory,
        "unmatched_short_shares": short_inventory,
        "exit_bid": exit_row["yes_bid"],
        "exit_ask": exit_row["yes_ask"],
        "spread_capture_pnl": spread_pnl,
        "long_inventory_pnl": long_pnl,
        "short_inventory_pnl": short_pnl,
        "pnl": pnl,
        "filled_shares": filled_quantity,
        "pnl_per_filled_share": pnl / filled_quantity if filled_quantity else 0.0,
    }


def _summarize(name: str, lifetime: int, asset: str, regime: str, rows: list[dict], sessions: list[dict]) -> dict:
    attempts = len(rows)
    pnl = [float(row["pnl"]) for row in rows]
    any_fills = [row for row in rows if row["bid_fill_proxy"] or row["ask_fill_proxy"]]
    two_sided = [row for row in rows if row["two_sided_fill_proxy"]]
    one_sided = [row for row in rows if (row["bid_fill_proxy"] != row["ask_fill_proxy"])]
    filled = sum(float(row["filled_shares"]) for row in rows)
    capacity = sum(min(float(row["filled_shares"]), ORDER_SIZE_SHARES) for row in rows)
    by_asset = _group(rows, "asset")
    by_session = _group(rows, "session_number")
    ci = _cluster_ci(rows, seed=20260704 + lifetime + sum(ord(c) for c in name))
    hours = sum(row["expected_duration_seconds"] for row in sessions) / 3600
    total = sum(pnl)
    summary = {
        "policy": name,
        "lifetime_seconds": lifetime,
        "asset_filter": asset,
        "regime": regime,
        "attempts": attempts,
        "attempts_per_hour": attempts / hours,
        "any_fill_proxy_count": len(any_fills),
        "raw_cross_depletion_rate": len(any_fills) / attempts if attempts else 0.0,
        "queue_adjusted_any_fill_probability": (len(any_fills) / attempts * QUEUE_FILL_RATIO) if attempts else 0.0,
        "two_sided_fill_proxy_count": len(two_sided),
        "queue_adjusted_two_sided_probability": (len(two_sided) / attempts * QUEUE_FILL_RATIO) if attempts else 0.0,
        "one_sided_fill_proxy_count": len(one_sided),
        "one_sided_share_of_triggered": len(one_sided) / len(any_fills) if any_fills else 0.0,
        "expected_filled_shares": filled,
        "expected_capacity_shares_per_hour": capacity / hours,
        "pnl": total,
        "expectancy_dollars_per_attempt": mean(pnl) if pnl else 0.0,
        "expectancy_probability_points_per_filled_share": total / filled if filled else 0.0,
        "win_rate_attempts": sum(value > 0 for value in pnl) / attempts if attempts else 0.0,
        "max_drawdown_dollars": _max_drawdown(pnl),
        "market_cluster_95_low_dollars_per_attempt": ci[0],
        "market_cluster_95_high_dollars_per_attempt": ci[1],
        "positive_assets": sum(value["expectancy"] > 0 for value in by_asset.values()),
        "asset_count": len(by_asset),
        "positive_sessions": sum(value["expectancy"] > 0 for value in by_session.values()),
        "session_count": len(by_session),
        "largest_asset_positive_pnl_share": _largest_share(by_asset, total),
        "largest_session_positive_pnl_share": _largest_share(by_session, total),
        "by_asset": json.dumps(by_asset, sort_keys=True, separators=(",", ":")),
        "by_session": json.dumps(by_session, sort_keys=True, separators=(",", ":")),
        "passes_prospective_shadow_gate": False,
    }
    summary["passes_prospective_shadow_gate"] = bool(
        summary["expectancy_dollars_per_attempt"] > 0
        and ci[0] is not None and ci[0] > 0
        and summary["one_sided_share_of_triggered"] <= 0.50
        and summary["positive_assets"] == summary["asset_count"]
        and summary["positive_sessions"] == summary["session_count"]
        and (summary["largest_asset_positive_pnl_share"] or 1) <= 0.40
        and (summary["largest_session_positive_pnl_share"] or 1) <= 0.40
    )
    return summary


def _group(rows: list[dict], key: str) -> dict:
    grouped = defaultdict(list)
    for row in rows:
        grouped[str(row[key])].append(float(row["pnl"]))
    return {
        name: {"attempts": len(values), "pnl": sum(values), "expectancy": mean(values), "max_drawdown": _max_drawdown(values)}
        for name, values in sorted(grouped.items())
    }


def _cluster_ci(rows: list[dict], seed: int) -> tuple[float | None, float | None]:
    if not rows:
        return None, None
    clusters = defaultdict(list)
    for row in rows:
        clusters[(row["session_number"], row["market_id"])].append(float(row["pnl"]))
    keys = sorted(clusters)
    rng = random.Random(seed)
    values = []
    for _ in range(3000):
        sample = [clusters[rng.choice(keys)] for _ in keys]
        flattened = [value for cluster in sample for value in cluster]
        values.append(mean(flattened))
    values.sort()
    return values[int(0.025 * len(values))], values[int(0.975 * len(values)) - 1]


def _max_drawdown(values: list[float]) -> float:
    total = peak = drawdown = 0.0
    for value in values:
        total += value
        peak = max(peak, total)
        drawdown = max(drawdown, peak - total)
    return drawdown


def _largest_share(groups: dict, total: float) -> float | None:
    if total <= 0 or not groups:
        return None
    return max(value["pnl"] for value in groups.values()) / total


def _write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
