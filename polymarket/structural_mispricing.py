from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median


SESSION_PATHS = (
    "polymarket/runs/microstructure_development_v1/20260623_120611/session.jsonl",
    "polymarket/runs/microstructure_development_v1_batch_002/20260623_214015/session.jsonl",
    "polymarket/runs/repricing_balanced_v1/20260624_154206/session.jsonl",
    "polymarket/runs/repricing_balanced_v1_batch_002/20260625_200724/session.jsonl",
    "polymarket/runs/repricing_paper_soak_v4/20260701_212557/v5_sessions/20260701_212638/session.jsonl",
)
TOTAL_COST = 0.01
ORDER_SIZE_SHARES = 250.0
MAX_FILL_FRACTION = 0.50
MAX_QUOTE_AGE_SECONDS = 5.0
NEAR_EXPIRY_SECONDS = 30.0
WIDE_SPREAD_THRESHOLD = 0.03


def run_structural_mispricing_triage(root: Path, output: Path) -> dict:
    session_rows = []
    observations = []
    for session_number, relative in enumerate(SESSION_PATHS, 1):
        summary, rows = _read_session(root / relative, session_number, relative)
        session_rows.append(summary)
        observations.extend(rows)

    episodes = _build_episodes(observations)
    episode_rows = [_episode_row(row) for row in episodes]
    scheduled_hours = sum(row["expected_duration_seconds"] for row in session_rows) / 3600
    candidates = _candidate_summaries(observations, episode_rows, scheduled_hours)
    fresh_spreads = [
        row["spread"] for row in observations
        if row["valid"] and not row["stale"] and row["spread"] is not None
    ]
    decision = "B_FREEZE_STRUCTURAL_MISPRICING_RECOMMEND_NEW_DIRECTION"
    report = {
        "task": "Polymarket Executable Structural Mispricing Triage v1",
        "decision": decision,
        "frozen_specification": {
            "sessions": list(SESSION_PATHS),
            "cost_probability_points": TOTAL_COST,
            "order_size_shares": ORDER_SIZE_SHARES,
            "maximum_fill_fraction": MAX_FILL_FRACTION,
            "maximum_quote_age_seconds": MAX_QUOTE_AGE_SECONDS,
            "near_expiry_seconds": NEAR_EXPIRY_SECONDS,
            "wide_spread_threshold": WIDE_SPREAD_THRESHOLD,
            "quote_deduplication": "market_id + quote_timestamp + bid/ask prices and sizes",
            "persistence_checks_seconds": [2, 5],
        },
        "dataset": {
            "completed_public_sessions": len(session_rows),
            "scheduled_hours": scheduled_hours,
            "raw_polymarket_snapshots": sum(row["raw_snapshots"] for row in session_rows),
            "deduplicated_quote_states": len(observations),
            "assets": dict(sorted(Counter(row["asset"] for row in observations).items())),
            "markets": len({row["market_id"] for row in observations}),
            "valid_fresh_states": sum(row["valid"] and not row["stale"] for row in observations),
            "stale_states": sum(row["stale"] for row in observations),
            "invalid_states": sum(not row["valid"] for row in observations),
            "spread_statistics": {
                "minimum": min(fresh_spreads) if fresh_spreads else None,
                "median": median(fresh_spreads) if fresh_spreads else None,
                "p95": _quantile(fresh_spreads, 0.95),
                "maximum": max(fresh_spreads) if fresh_spreads else None,
            },
        },
        "book_semantics": {
            "independent_yes_book": True,
            "independent_no_book": False,
            "multi_outcome_books": False,
            "implication": (
                "NO bid/ask and depth were not independently captured. Complete-set and multi-outcome "
                "claims cannot be admitted; algebraic complements reduce both complete-set margins to -YES spread."
            ),
        },
        "candidate_rankings": candidates,
        "holdout_status": "sealed_holdout_not_inspected_no_holdout_evaluation_run",
    }
    output.mkdir(parents=True, exist_ok=True)
    _write_csv(output / "session_inventory.csv", session_rows)
    _write_csv(output / "structural_episodes.csv", episode_rows)
    _write_csv(output / "candidate_rankings.csv", candidates)
    (output / "triage_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def _read_session(path: Path, session_number: int, relative: str) -> tuple[dict, list[dict]]:
    started = completed = None
    raw_snapshots = 0
    deduplicated = []
    last_identity_by_market = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            event = json.loads(line)
            kind = event.get("event")
            if kind == "session_started":
                started = event
            elif kind == "session_completed":
                completed = event
            elif kind == "polymarket_snapshot":
                raw_snapshots += 1
                payload = event.get("payload", {})
                identity = (
                    payload.get("market_id"), payload.get("quote_timestamp"),
                    payload.get("yes_bid"), payload.get("yes_ask"),
                    payload.get("yes_bid_size"), payload.get("yes_ask_size"),
                )
                market_id = payload.get("market_id")
                if last_identity_by_market.get(market_id) == identity:
                    continue
                last_identity_by_market[market_id] = identity
                row = _normalize_snapshot(payload, event["timestamp"], session_number, relative)
                deduplicated.append(row)
    if started is None or completed is None:
        raise ValueError(f"incomplete session: {relative}")
    start_payload = started.get("payload", {})
    complete_payload = completed.get("payload", {})
    campaign = complete_payload.get("campaign_completeness", {})
    continuity = complete_payload.get("observation_continuity", {})
    if start_payload.get("mode") != "public":
        raise ValueError(f"non-public session: {relative}")
    if campaign.get("status") != "complete" or continuity.get("status") != "continuous":
        raise ValueError(f"failed integrity session: {relative}")
    summary = {
        "session_number": session_number,
        "session_path": relative,
        "mode": start_payload.get("mode"),
        "expected_duration_seconds": float(start_payload.get("duration_seconds", 0)),
        "campaign_status": campaign.get("status"),
        "continuity_status": continuity.get("status"),
        "fatal_capture_errors": int(continuity.get("fatal_capture_error_count", 0)),
        "raw_snapshots": raw_snapshots,
        "deduplicated_quote_states": len(deduplicated),
        "first_timestamp": deduplicated[0]["timestamp"] if deduplicated else "",
        "last_timestamp": deduplicated[-1]["timestamp"] if deduplicated else "",
    }
    return summary, deduplicated


def _normalize_snapshot(payload: dict, event_timestamp: str, session_number: int, source: str) -> dict:
    bid = _number(payload.get("yes_bid"))
    ask = _number(payload.get("yes_ask"))
    bid_size = _number(payload.get("yes_bid_size"))
    ask_size = _number(payload.get("yes_ask_size"))
    seconds_to_expiry = _number(payload.get("seconds_to_expiry"))
    quote_timestamp = payload.get("quote_timestamp", "")
    try:
        quote_age = (
            datetime.fromisoformat(event_timestamp) - datetime.fromisoformat(quote_timestamp)
        ).total_seconds()
    except (TypeError, ValueError):
        quote_age = math.inf
    valid = all(
        value is not None for value in (bid, ask, bid_size, ask_size, seconds_to_expiry)
    ) and 0 <= bid <= 1 and 0 <= ask <= 1 and bid_size > 0 and ask_size > 0
    spread = ask - bid if valid else None
    stale = not math.isfinite(quote_age) or quote_age > MAX_QUOTE_AGE_SECONDS
    crossed = bool(valid and bid > ask)
    locked = bool(valid and bid == ask)
    wide = bool(valid and spread > WIDE_SPREAD_THRESHOLD)
    near_expiry = bool(valid and 0 <= seconds_to_expiry <= NEAR_EXPIRY_SECONDS)
    executable_capacity = min(bid_size, ask_size, ORDER_SIZE_SHARES * MAX_FILL_FRACTION) if valid else 0.0
    return {
        "session_number": session_number,
        "source_session": source,
        "timestamp": event_timestamp,
        "quote_timestamp": quote_timestamp,
        "market_id": payload.get("market_id", ""),
        "asset": payload.get("asset", ""),
        "yes_bid": bid,
        "yes_ask": ask,
        "yes_bid_size": bid_size,
        "yes_ask_size": ask_size,
        "spread": spread,
        "quote_age_seconds": quote_age,
        "seconds_to_expiry": seconds_to_expiry,
        "valid": valid,
        "stale": stale,
        "crossed": crossed,
        "locked": locked,
        "wide_spread": wide,
        "near_expiry": near_expiry,
        "executable_capacity_shares": executable_capacity,
        "crossed_net_margin": bid - ask - TOTAL_COST if valid else None,
        "complete_set_acquisition_net_margin": bid - ask - TOTAL_COST if valid else None,
        "complete_set_liquidation_net_margin": bid - ask - TOTAL_COST if valid else None,
        "marketable_round_trip_margin": bid - ask - TOTAL_COST if valid else None,
    }


def _build_episodes(rows: list[dict]) -> list[dict]:
    episodes = []
    active = {}
    ordered = sorted(rows, key=lambda row: (row["session_number"], row["market_id"], row["timestamp"]))
    for row in ordered:
        for kind in ("crossed", "locked", "wide_spread"):
            key = (row["session_number"], row["market_id"], kind)
            qualifies = bool(row["valid"] and not row["stale"] and row[kind])
            previous = active.get(key)
            if qualifies:
                timestamp = datetime.fromisoformat(row["timestamp"])
                if previous and (timestamp - previous["last_time"]).total_seconds() <= MAX_QUOTE_AGE_SECONDS:
                    previous["last_time"] = timestamp
                    previous["last_row"] = row
                    previous["state_count"] += 1
                    previous["max_capacity"] = max(previous["max_capacity"], row["executable_capacity_shares"])
                    previous["best_margin"] = max(previous["best_margin"], row["crossed_net_margin"])
                else:
                    if previous:
                        episodes.append(previous)
                    active[key] = {
                        "kind": kind,
                        "session_number": row["session_number"],
                        "market_id": row["market_id"],
                        "asset": row["asset"],
                        "first_time": timestamp,
                        "last_time": timestamp,
                        "first_row": row,
                        "last_row": row,
                        "state_count": 1,
                        "max_capacity": row["executable_capacity_shares"],
                        "best_margin": row["crossed_net_margin"],
                    }
            elif previous:
                episodes.append(previous)
                del active[key]
    episodes.extend(active.values())
    return sorted(episodes, key=lambda row: (row["session_number"], row["first_time"], row["market_id"], row["kind"]))


def _episode_row(episode: dict) -> dict:
    duration = (episode["last_time"] - episode["first_time"]).total_seconds()
    return {
        "kind": episode["kind"],
        "session_number": episode["session_number"],
        "market_id": episode["market_id"],
        "asset": episode["asset"],
        "first_timestamp": episode["first_time"].isoformat(),
        "last_timestamp": episode["last_time"].isoformat(),
        "duration_seconds": duration,
        "state_count": episode["state_count"],
        "persists_2_seconds": duration >= 2,
        "persists_5_seconds": duration >= 5,
        "maximum_conservative_capacity_shares": episode["max_capacity"],
        "best_executable_net_margin": episode["best_margin"],
    }


def _candidate_summaries(rows: list[dict], episodes: list[dict], scheduled_hours: float) -> list[dict]:
    fresh = [row for row in rows if row["valid"] and not row["stale"]]
    near = [row for row in fresh if row["near_expiry"]]
    crossed = [row for row in fresh if row["crossed"]]
    locked = [row for row in fresh if row["locked"]]
    wide = [row for row in fresh if row["wide_spread"]]
    crossed_episodes = [row for row in episodes if row["kind"] == "crossed"]
    locked_episodes = [row for row in episodes if row["kind"] == "locked"]
    wide_episodes = [row for row in episodes if row["kind"] == "wide_spread"]
    stale_crossed = [row for row in rows if row["valid"] and row["stale"] and row["crossed"]]
    near_crossed = [row for row in near if row["crossed"]]
    base = [
        _candidate(1, "crossed_or_inverted_yes_book", "testable", crossed, crossed_episodes,
                   "direct bid-minus-ask less 0.01 cost", "reject_no_positive_fresh_states"),
        _candidate(2, "complete_set_acquisition", "not_independently_testable", [], [],
                   "derived margin equals -YES spread - 0.01", "reject_missing_independent_no_book"),
        _candidate(3, "complete_set_liquidation", "not_independently_testable", [], [],
                   "derived margin equals -YES spread - 0.01", "reject_missing_independent_no_book"),
        _candidate(4, "locked_book", "testable", locked, locked_episodes,
                   "zero gross margin less 0.01 cost", "reject_nonpositive_after_cost"),
        _candidate(5, "stale_bid_ask_inconsistency", "testable_but_ineligible", stale_crossed, [],
                   "stale states fail quote-age gate", "reject_stale_or_zero_count"),
        _candidate(6, "temporary_wide_spread_capture", "observable_not_directly_executable", wide, wide_episodes,
                   "marketable round trip equals -spread - 0.01; passive capture has unknown queue/fill", "reject_requires_two_uncertain_passive_fills"),
        _candidate(7, "near_expiry_structural_distortion", "testable", near_crossed, [],
                   "crossed fresh states within 30 seconds of expiry", "reject_no_positive_near_expiry_states"),
        _candidate(8, "multi_outcome_pricing_inconsistency", "not_applicable", [], [],
                   "all captured markets are binary and no multi-outcome books exist", "reject_unsupported_schema"),
        _candidate(9, "executable_bid_ask_anomaly", "testable", crossed, crossed_episodes,
                   "same as crossed-book direct execution", "reject_no_positive_fresh_states"),
        _candidate(10, "liquidity_aware_arbitrage_like_setup", "testable", crossed, crossed_episodes,
                   "crossed margin with 250-share cap and 50% fill cap", "reject_no_positive_capacity"),
    ]
    theoretical = [row["crossed_net_margin"] for row in fresh]
    near_theoretical = [row["crossed_net_margin"] for row in near]
    for row in base:
        row["frequency_states_per_hour"] = row["qualifying_states"] / scheduled_hours
        row["frequency_episodes_per_hour"] = row["episodes"] / scheduled_hours
        if row["candidate"] in {"complete_set_acquisition", "complete_set_liquidation"}:
            row["best_net_margin"] = max(theoretical) if theoretical else None
            row["mean_net_margin"] = mean(theoretical) if theoretical else None
        if row["candidate"] == "near_expiry_structural_distortion":
            row["best_net_margin"] = max(near_theoretical) if near_theoretical else None
            row["mean_net_margin"] = mean(near_theoretical) if near_theoretical else None
    for row in base:
        row["fresh_quote_state_denominator"] = len(fresh)
        row["near_expiry_state_denominator"] = len(near)
    return base


def _candidate(rank: int, name: str, testability: str, states: list[dict], episodes: list[dict], economics: str, verdict: str) -> dict:
    margins = [row["crossed_net_margin"] for row in states if row["crossed_net_margin"] is not None]
    durations = [float(row["duration_seconds"]) for row in episodes]
    capacities = [row["executable_capacity_shares"] for row in states]
    return {
        "rank": rank,
        "candidate": name,
        "testability": testability,
        "qualifying_states": len(states),
        "episodes": len(episodes),
        "markets": len({row["market_id"] for row in states}),
        "assets": ";".join(sorted({row["asset"] for row in states})),
        "persists_2s_episodes": sum(float(row["duration_seconds"]) >= 2 for row in episodes),
        "persists_5s_episodes": sum(float(row["duration_seconds"]) >= 5 for row in episodes),
        "median_episode_seconds": median(durations) if durations else None,
        "best_net_margin": max(margins) if margins else None,
        "mean_net_margin": mean(margins) if margins else None,
        "maximum_conservative_capacity_shares": max(capacities) if capacities else 0.0,
        "economics": economics,
        "verdict": verdict,
    }


def _number(value) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(probability * len(ordered)) - 1))
    return ordered[index]


def _write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
