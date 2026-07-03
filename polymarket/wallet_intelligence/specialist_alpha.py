"""Deterministic chronological validation for frozen wallet specialists."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable


DEFAULT_TRADE_INPUT = Path(
    "polymarket/data/wallet_intelligence/trade_history_broader_v1/trade_history_normalized.csv"
)
DEFAULT_OUTCOME_INPUT = Path(
    "polymarket/models/wallet_intelligence_v1/market_outcome_resolution_v1/market_outcome_join.csv"
)
DEFAULT_SKILL_INPUT = Path(
    "polymarket/models/wallet_intelligence_v1/outcome_skill_baseline_v1/wallet_skill_baseline.csv"
)
DEFAULT_OUTPUT = Path(
    "polymarket/models/wallet_intelligence_v1/specialist_alpha_chronological_v1"
)

FROZEN_SPECIALISTS = {
    "0x088df3b7e5c1b5c2d4b7dc760863153480cf025e": ("BTC", "ETH", "SOL"),
    "0x1cc53dd33c49d0a222c61ebfd2f24ba48802b199": ("BTC",),
    "0x29a55c2bf8efd1029c001477b34be47d3ca37752": ("ETH",),
    "0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a": ("BTC",),
}
OBSERVATION_DELAY_SECONDS = 30.0
MINIMUM_DECISION_WINDOW_SECONDS = 60.0
CONSERVATIVE_COST = 0.05
SEVERE_DELAY_SECONDS = 60.0
SEVERE_COST = 0.10
FOLD_COUNT = 3

SIGNAL_FIELDS = [
    "fold",
    "wallet_id",
    "condition_id",
    "market_slug",
    "asset_class",
    "signal_outcome",
    "winning_outcome",
    "trade_timestamp",
    "trade_datetime_utc",
    "expiry_timestamp",
    "raw_time_to_expiry_seconds",
    "modeled_decision_window_seconds",
    "reported_price",
    "modeled_entry_price",
    "matched_outcome",
    "reported_price_value",
    "conservative_value",
    "transaction_hash",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _format(value: float) -> str:
    return f"{value:.6f}"


def _wilson(successes: int, trials: int) -> tuple[float, float]:
    if not trials:
        return 0.0, 1.0
    z = 1.959963984540054
    point = successes / trials
    denominator = 1 + z * z / trials
    center = (point + z * z / (2 * trials)) / denominator
    half = z * math.sqrt(point * (1 - point) / trials + z * z / (4 * trials * trials)) / denominator
    return center - half, center + half


def _mean_ci(values: list[float]) -> tuple[float, float]:
    if len(values) < 2:
        return (values[0], values[0]) if values else (0.0, 0.0)
    mean = statistics.mean(values)
    half = 1.959963984540054 * statistics.stdev(values) / math.sqrt(len(values))
    return mean - half, mean + half


def _max_drawdown(values: Iterable[float]) -> float:
    equity = peak = drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return drawdown


def _render_csv(rows: list[dict[str, Any]], fields: list[str]) -> str:
    from io import StringIO

    handle = StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return handle.getvalue()


def build_specialist_signals(
    trades: list[dict[str, str]], outcomes: list[dict[str, str]],
    wallet_specialties: dict[str, tuple[str, ...]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    specialties = wallet_specialties or FROZEN_SPECIALISTS
    metadata: dict[str, dict[str, str]] = {}
    conflicts: set[str] = set()
    for row in outcomes:
        if row.get("resolved_status") != "resolved" or not row.get("winning_outcome"):
            continue
        condition = row["condition_id"].lower()
        candidate = {
            "winning_outcome": row["winning_outcome"],
            "expiry_timestamp": row["expiry_timestamp"],
            "market_slug": row["market_slug"],
            "asset_class": row["asset_class"],
        }
        if condition in metadata and metadata[condition] != candidate:
            conflicts.add(condition)
        metadata[condition] = candidate

    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    exclusions = Counter()
    for row in trades:
        wallet = row.get("wallet_id", "").lower()
        condition = row.get("condition_id", "").lower()
        if wallet not in specialties:
            continue
        if row.get("side") != "BUY":
            exclusions["non_buy"] += 1
            continue
        if row.get("up_down_market") != "true" or row.get("asset_class") not in specialties[wallet]:
            exclusions["outside_frozen_specialty"] += 1
            continue
        if condition not in metadata or condition in conflicts:
            exclusions["missing_or_conflicting_resolution"] += 1
            continue
        if "-updown-5m-" not in metadata[condition]["market_slug"]:
            exclusions["non_five_minute_market"] += 1
            continue
        grouped[(wallet, condition)].append(row)

    signals: list[dict[str, Any]] = []
    for (wallet, condition), rows in grouped.items():
        rows.sort(
            key=lambda row: (
                int(row["activity_timestamp"]),
                -float(row.get("notional_value") or 0),
                row.get("outcome", ""),
                row.get("dedupe_key", ""),
            )
        )
        earliest = int(rows[0]["activity_timestamp"])
        simultaneous = [row for row in rows if int(row["activity_timestamp"]) == earliest]
        chosen = max(
            simultaneous,
            key=lambda row: (float(row.get("notional_value") or 0), row.get("outcome", "")),
        )
        meta = metadata[condition]
        expiry = _parse_time(meta["expiry_timestamp"])
        trade_time = datetime.fromtimestamp(earliest, UTC)
        raw_window = (expiry - trade_time).total_seconds()
        modeled_window = raw_window - OBSERVATION_DELAY_SECONDS
        if modeled_window < MINIMUM_DECISION_WINDOW_SECONDS:
            exclusions["insufficient_modeled_decision_window"] += 1
            continue
        price = float(chosen["price"])
        modeled_entry = min(0.99, price + CONSERVATIVE_COST)
        matched = chosen["outcome"].casefold() == meta["winning_outcome"].casefold()
        payoff = 1.0 if matched else 0.0
        signals.append(
            {
                "wallet_id": wallet,
                "condition_id": condition,
                "market_slug": meta["market_slug"],
                "asset_class": chosen["asset_class"],
                "signal_outcome": chosen["outcome"],
                "winning_outcome": meta["winning_outcome"],
                "trade_timestamp": earliest,
                "trade_datetime_utc": trade_time.isoformat(timespec="seconds"),
                "expiry_timestamp": expiry.isoformat(timespec="seconds"),
                "raw_time_to_expiry_seconds": raw_window,
                "modeled_decision_window_seconds": modeled_window,
                "reported_price": price,
                "modeled_entry_price": modeled_entry,
                "matched_outcome": matched,
                "reported_price_value": payoff - price,
                "conservative_value": payoff - modeled_entry,
                "transaction_hash": chosen.get("transaction_hash", ""),
            }
        )

    signals.sort(key=lambda row: (row["trade_timestamp"], row["condition_id"], row["wallet_id"]))
    conditions = sorted(
        {row["condition_id"] for row in signals},
        key=lambda condition: (
            min(row["trade_timestamp"] for row in signals if row["condition_id"] == condition),
            condition,
        ),
    )
    fold_by_condition = {
        condition: min(FOLD_COUNT, index * FOLD_COUNT // max(1, len(conditions)) + 1)
        for index, condition in enumerate(conditions)
    }
    for row in signals:
        row["fold"] = fold_by_condition[row["condition_id"]]
    return signals, dict(sorted(exclusions.items()))


def _metrics(rows: list[dict[str, Any]], value_field: str = "conservative_value") -> dict[str, Any]:
    wins = sum(bool(row["matched_outcome"]) for row in rows)
    values = [float(row[value_field]) for row in rows]
    low, high = _wilson(wins, len(rows))
    value_low, value_high = _mean_ci(values)
    return {
        "sample_size": len(rows),
        "wins": wins,
        "losses": len(rows) - wins,
        "win_rate": wins / len(rows) if rows else 0.0,
        "win_rate_wilson_95_low": low,
        "win_rate_wilson_95_high": high,
        "expectancy": statistics.mean(values) if values else 0.0,
        "expectancy_95_low": value_low,
        "expectancy_95_high": value_high,
        "max_drawdown": _max_drawdown(values),
    }


def summarize_wallets(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for wallet in FROZEN_SPECIALISTS:
        wallet_rows = [row for row in signals if row["wallet_id"] == wallet]
        base = _metrics(wallet_rows)
        folds = [_metrics([row for row in wallet_rows if row["fold"] == fold]) for fold in range(1, 4)]
        positive_folds = sum(fold["sample_size"] > 0 and fold["expectancy"] > 0 for fold in folds)
        date_counts = Counter(row["trade_datetime_utc"][:10] for row in wallet_rows)
        asset_counts = Counter(row["asset_class"] for row in wallet_rows)
        rows.append(
            {
                "wallet_id": wallet,
                "frozen_specialty": ";".join(FROZEN_SPECIALISTS[wallet]),
                **base,
                "positive_fold_count": positive_folds,
                "nonempty_fold_count": sum(fold["sample_size"] > 0 for fold in folds),
                "stability": positive_folds / max(1, sum(fold["sample_size"] > 0 for fold in folds)),
                "asset_counts": json.dumps(dict(sorted(asset_counts.items())), sort_keys=True),
                "date_counts": json.dumps(dict(sorted(date_counts.items())), sort_keys=True),
                "largest_date_share": max(date_counts.values()) / len(wallet_rows) if wallet_rows else 0.0,
                "robustness": "positive_after_conservative_cost" if base["expectancy"] > 0 else "fails_conservative_cost",
            }
        )
    return rows


def summarize_folds(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for fold in range(1, FOLD_COUNT + 1):
        rows = [row for row in signals if row["fold"] == fold]
        metrics = _metrics(rows)
        output.append(
            {
                "fold": fold,
                **metrics,
                "first_trade_utc": min((row["trade_datetime_utc"] for row in rows), default=""),
                "last_trade_utc": max((row["trade_datetime_utc"] for row in rows), default=""),
                "unique_markets": len({row["condition_id"] for row in rows}),
            }
        )
    return output


def summarize_consensus(signals: list[dict[str, Any]], frozen_weights: dict[str, float]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in signals:
        grouped[row["condition_id"]].append(row)
    output: list[dict[str, Any]] = []
    for condition, rows in sorted(grouped.items(), key=lambda item: (min(r["trade_timestamp"] for r in item[1]), item[0])):
        if len(rows) < 2:
            continue
        sides = Counter(row["signal_outcome"] for row in rows)
        equal_status = "agreement" if len(sides) == 1 else "disagreement"
        weighted = defaultdict(float)
        for row in rows:
            weighted[row["signal_outcome"]] += frozen_weights[row["wallet_id"]]
        weighted_order = sorted(weighted.items(), key=lambda item: (-item[1], item[0]))
        weighted_side = weighted_order[0][0] if len(weighted_order) == 1 or weighted_order[0][1] > weighted_order[1][1] else "TIE"
        representative = rows[0]
        winning = representative["winning_outcome"]
        equal_side = next(iter(sides)) if equal_status == "agreement" else "DISAGREEMENT"
        equal_matched = equal_status == "agreement" and equal_side.casefold() == winning.casefold()
        equal_prices = [float(row["reported_price"]) for row in rows if row["signal_outcome"] == equal_side]
        equal_value = (
            (1.0 if equal_matched else 0.0) - min(0.99, max(equal_prices) + CONSERVATIVE_COST)
            if equal_prices else None
        )
        weighted_matched = weighted_side != "TIE" and weighted_side.casefold() == winning.casefold()
        weighted_prices = [float(row["reported_price"]) for row in rows if row["signal_outcome"] == weighted_side]
        weighted_value = (
            (1.0 if weighted_matched else 0.0) - min(0.99, max(weighted_prices) + CONSERVATIVE_COST)
            if weighted_prices else None
        )
        output.append(
            {
                "condition_id": condition,
                "fold": representative["fold"],
                "market_slug": representative["market_slug"],
                "asset_class": representative["asset_class"],
                "wallet_count": len(rows),
                "wallet_ids": ";".join(sorted(row["wallet_id"] for row in rows)),
                "equal_consensus_status": equal_status,
                "equal_consensus_side": equal_side,
                "equal_consensus_matched": str(equal_matched).lower(),
                "equal_conservative_value": "" if equal_value is None else equal_value,
                "weighted_consensus_side": weighted_side,
                "weighted_consensus_matched": str(weighted_matched).lower(),
                "weighted_conservative_value": "" if weighted_value is None else weighted_value,
                "winning_outcome": winning,
            }
        )
    return output


def _stress(signals: list[dict[str, Any]], delay: float, cost: float) -> dict[str, Any]:
    rows = [
        row for row in signals
        if float(row["raw_time_to_expiry_seconds"]) - delay >= MINIMUM_DECISION_WINDOW_SECONDS
    ]
    values = [
        (1.0 if row["matched_outcome"] else 0.0) - min(0.99, float(row["reported_price"]) + cost)
        for row in rows
    ]
    return {
        "delay_seconds": delay,
        "adverse_entry_cost": cost,
        "sample_size": len(rows),
        "expectancy": statistics.mean(values) if values else 0.0,
        "max_drawdown": _max_drawdown(values),
    }


def validate_specialist_alpha(
    signals: list[dict[str, Any]], wallets: list[dict[str, Any]], folds: list[dict[str, Any]],
    consensus: list[dict[str, Any]], repeatable: bool,
) -> dict[str, Any]:
    all_metrics = _metrics(signals)
    date_counts = Counter(row["trade_datetime_utc"][:10] for row in signals)
    condition_folds: dict[str, set[int]] = defaultdict(set)
    for row in signals:
        condition_folds[row["condition_id"]].add(int(row["fold"]))
    gates = {
        "four_frozen_wallets_present": {row["wallet_id"] for row in wallets} == set(FROZEN_SPECIALISTS),
        "market_group_leakage_absent": all(len(value) == 1 for value in condition_folds.values()),
        "chronological_fold_order": all(
            folds[index]["last_trade_utc"] <= folds[index + 1]["first_trade_utc"]
            for index in range(len(folds) - 1)
            if folds[index]["sample_size"] and folds[index + 1]["sample_size"]
        ),
        "deterministic_repeat_export": repeatable,
        "selection_leakage_absent": False,
        "positive_conservative_expectancy": all_metrics["expectancy"] > 0,
        "positive_expectancy_confidence": all_metrics["expectancy_95_low"] > 0,
        "all_three_folds_positive": all(row["expectancy"] > 0 for row in folds),
        "at_least_two_wallets_confidently_positive": sum(row["expectancy_95_low"] > 0 for row in wallets) >= 2,
        "date_concentration_below_40_percent": bool(signals) and max(date_counts.values()) / len(signals) <= 0.40,
        "consensus_sample_at_least_30": len(consensus) >= 30,
        "direct_liquidity_and_spread_join_available": False,
    }
    return {
        "gates": gates,
        "all_mechanical_validation_passed": all(
            gates[key] for key in (
                "four_frozen_wallets_present", "market_group_leakage_absent",
                "chronological_fold_order", "deterministic_repeat_export",
            )
        ),
        "go_gate_passed": all(gates.values()),
        "irreversible_decision": "NO_GO_PERMANENTLY_FREEZE_WALLET_INTELLIGENCE",
        "selection_leakage_reason": (
            "The four wallets were selected using outcomes from the same bounded dataset; "
            "chronological row folds cannot create an untouched wallet-selection test."
        ),
    }


def run_wallet_specialist_alpha_validation(
    trade_csv: Path = DEFAULT_TRADE_INPUT,
    outcome_csv: Path = DEFAULT_OUTCOME_INPUT,
    skill_csv: Path = DEFAULT_SKILL_INPUT,
    output_dir: Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    trades = _read_csv(trade_csv)
    outcomes = _read_csv(outcome_csv)
    skill = _read_csv(skill_csv)
    selected = {row["wallet_id"] for row in skill if row.get("evidence_classification") == "above_baseline_evidence"}
    if selected != set(FROZEN_SPECIALISTS):
        raise ValueError("frozen specialist set does not match the committed H1 candidates")
    frozen_weights = {
        row["wallet_id"]: math.sqrt(float(row["resolved_positions"]))
        for row in skill if row["wallet_id"] in FROZEN_SPECIALISTS
    }
    signals, exclusions = build_specialist_signals(trades, outcomes)
    population_wallets = {
        row["wallet_id"].lower(): ("BTC", "ETH", "SOL")
        for row in trades
        if row.get("wallet_id", "").lower() not in FROZEN_SPECIALISTS
    }
    population_signals, population_exclusions = build_specialist_signals(
        trades, outcomes, population_wallets
    )
    wallets = summarize_wallets(signals)
    folds = summarize_folds(signals)
    consensus = summarize_consensus(signals, frozen_weights)

    signal_text = _render_csv(signals, SIGNAL_FIELDS)
    wallet_fields = list(wallets[0]) if wallets else ["wallet_id"]
    fold_fields = list(folds[0]) if folds else ["fold"]
    consensus_fields = list(consensus[0]) if consensus else ["condition_id"]
    wallet_text = _render_csv(wallets, wallet_fields)
    fold_text = _render_csv(folds, fold_fields)
    consensus_text = _render_csv(consensus, consensus_fields)
    repeatable = signal_text == _render_csv(signals, SIGNAL_FIELDS)
    validation = validate_specialist_alpha(signals, wallets, folds, consensus, repeatable)
    overall = _metrics(signals)
    stress = {
        "reported_price": _stress(signals, 0.0, 0.0),
        "conservative": _stress(signals, OBSERVATION_DELAY_SECONDS, CONSERVATIVE_COST),
        "severe": _stress(signals, SEVERE_DELAY_SECONDS, SEVERE_COST),
    }
    equal_agreements = [row for row in consensus if row["equal_consensus_status"] == "agreement"]
    weighted_decisions = [row for row in consensus if row["weighted_consensus_side"] != "TIE"]
    equal_values = [float(row["equal_conservative_value"]) for row in equal_agreements]
    weighted_values = [float(row["weighted_conservative_value"]) for row in weighted_decisions]
    asset_results = {
        asset: _metrics([row for row in signals if row["asset_class"] == asset])
        for asset in ("BTC", "ETH", "SOL")
    }
    windows = [float(row["modeled_decision_window_seconds"]) for row in signals]
    summary = {
        "task": "Wallet Specialist Alpha Chronological Validation v1",
        "decision": validation["irreversible_decision"],
        "frozen_specialists": {key: list(value) for key, value in FROZEN_SPECIALISTS.items()},
        "protocol": {
            "signal": "earliest BUY per frozen wallet and condition; simultaneous rows choose largest notional",
            "folds": "three contiguous global chronological condition-ID groups",
            "observation_delay_seconds": OBSERVATION_DELAY_SECONDS,
            "minimum_decision_window_seconds": MINIMUM_DECISION_WINDOW_SECONDS,
            "conservative_cost": CONSERVATIVE_COST,
            "severe_delay_seconds": SEVERE_DELAY_SECONDS,
            "severe_cost": SEVERE_COST,
            "threshold_tuning": False,
        },
        "overall": overall,
        "folds": folds,
        "wallets": wallets,
        "stress": stress,
        "consensus": {
            "overlap_markets": len(consensus),
            "equal_agreement_markets": len(equal_agreements),
            "equal_agreement_win_rate": sum(row["equal_consensus_matched"] == "true" for row in equal_agreements) / len(equal_agreements) if equal_agreements else 0.0,
            "equal_agreement_expectancy": statistics.mean(equal_values) if equal_values else 0.0,
            "weighted_decision_markets": len(weighted_decisions),
            "weighted_win_rate": sum(row["weighted_consensus_matched"] == "true" for row in weighted_decisions) / len(weighted_decisions) if weighted_decisions else 0.0,
            "weighted_expectancy": statistics.mean(weighted_values) if weighted_values else 0.0,
            "disagreement_markets": sum(row["equal_consensus_status"] == "disagreement" for row in consensus),
        },
        "asset_results": asset_results,
        "timing_before_expiry": {
            "minimum_seconds": min(windows) if windows else 0.0,
            "median_seconds": statistics.median(windows) if windows else 0.0,
            "mean_seconds": statistics.mean(windows) if windows else 0.0,
            "maximum_seconds": max(windows) if windows else 0.0,
            "at_least_120_seconds": sum(value >= 120 for value in windows),
            "at_least_180_seconds": sum(value >= 180 for value in windows),
        },
        "filter_interactions": {
            "liquidity_coverage_rows": 0,
            "spread_coverage_rows": 0,
            "liquidity_interaction": "NOT_MEASURABLE_FAIL_CLOSED",
            "spread_interaction": "NOT_MEASURABLE_FAIL_CLOSED",
            "reason": "Existing wallet history is not joined to contemporaneous order-book snapshots.",
        },
        "concentration": {
            "unique_markets": len({row["condition_id"] for row in signals}),
            "utc_dates": dict(sorted(Counter(row["trade_datetime_utc"][:10] for row in signals).items())),
            "assets": dict(sorted(Counter(row["asset_class"] for row in signals).items())),
        },
        "exclusions": exclusions,
        "baselines": {
            "random_side_win_rate": 0.5,
            "prior_population_wallet_match_rate": 0.524609,
            "contemporaneous_price_value_baseline": 0.0,
            "same_protocol_population": _metrics(population_signals),
            "same_protocol_population_wallets": len({row["wallet_id"] for row in population_signals}),
            "same_protocol_population_exclusions": population_exclusions,
        },
        "unknowns": [
            "untouched wallet-selection sample",
            "actual public observation delay for these historical trades",
            "delayed executable quote",
            "direct spread and order-book liquidity at entry",
            "queue position, fill probability, and market impact",
        ],
        "validation": validation,
        "holdout": {"sealed_outcomes_read": False, "holdout_evaluation_run": False},
    }
    report = render_report(summary)

    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "wallet_specialist_signals.csv": signal_text,
        "wallet_specialist_results.csv": wallet_text,
        "wallet_specialist_fold_results.csv": fold_text,
        "wallet_specialist_consensus.csv": consensus_text,
        "wallet_specialist_summary.json": json.dumps(summary, indent=2, sort_keys=True) + "\n",
        "wallet_specialist_validation.json": json.dumps(validation, indent=2, sort_keys=True) + "\n",
        "wallet_specialist_alpha_report.md": report,
    }
    for name, text in files.items():
        (output_dir / name).write_text(text, encoding="utf-8", newline="")
    hashes = {name: hashlib.sha256(text.encode("utf-8")).hexdigest() for name, text in files.items()}
    (output_dir / "reproducibility_hashes.json").write_text(
        json.dumps({"algorithm": "sha256", "files": hashes}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="",
    )
    return summary


def render_report(summary: dict[str, Any]) -> str:
    overall = summary["overall"]
    consensus = summary["consensus"]
    lines = [
        "# Wallet Specialist Alpha Chronological Validation v1",
        "",
        "## Irreversible Decision",
        "",
        "**NO-GO: Wallet Intelligence is permanently frozen as a failed research direction.**",
        "",
        "The four wallets remain descriptively unusual, but the branch does not provide scientifically valid, executable alpha evidence. This is not a trading recommendation.",
        "",
        "## Frozen Protocol",
        "",
        f"- Candidates: {len(summary['frozen_specialists'])}",
        f"- Chronological folds: {FOLD_COUNT}, globally grouped by condition ID",
        f"- Observation delay: {OBSERVATION_DELAY_SECONDS:.0f} seconds",
        f"- Minimum remaining decision window: {MINIMUM_DECISION_WINDOW_SECONDS:.0f} seconds",
        f"- Conservative adverse entry burden: {CONSERVATIVE_COST:.2f}",
        "- Signal: earliest BUY per wallet-market; no threshold or wallet tuning",
        "",
        "## Results",
        "",
        f"- Eligible signals: {overall['sample_size']}",
        f"- Match rate: {overall['win_rate']:.2%} (Wilson 95% {overall['win_rate_wilson_95_low']:.2%}-{overall['win_rate_wilson_95_high']:.2%})",
        f"- Reported-price expectancy: {summary['stress']['reported_price']['expectancy']:.6f}",
        f"- Conservative expectancy: {overall['expectancy']:.6f} (95% {overall['expectancy_95_low']:.6f} to {overall['expectancy_95_high']:.6f})",
        f"- Conservative maximum drawdown: {overall['max_drawdown']:.6f}",
        f"- Severe expectancy: {summary['stress']['severe']['expectancy']:.6f}",
        f"- Unique markets: {summary['concentration']['unique_markets']}",
        f"- Same-protocol non-candidate population: {summary['baselines']['same_protocol_population']['sample_size']} signals, {summary['baselines']['same_protocol_population']['win_rate']:.2%} match, {summary['baselines']['same_protocol_population']['expectancy']:.6f} conservative expectancy",
        "",
        "## Individual Wallets",
        "",
        "| Wallet | N | Win rate | Conservative expectancy | 95% expectancy CI | Positive folds |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary["wallets"]:
        lines.append(
            f"| `{row['wallet_id']}` | {row['sample_size']} | {row['win_rate']:.2%} | "
            f"{row['expectancy']:.6f} | {row['expectancy_95_low']:.6f} to {row['expectancy_95_high']:.6f} | "
            f"{row['positive_fold_count']}/{row['nonempty_fold_count']} |"
        )
    lines.extend(
        [
            "",
            "## Consensus",
            "",
            f"- Markets with at least two specialists: {consensus['overlap_markets']}",
            f"- Equal-consensus agreements: {consensus['equal_agreement_markets']}, win rate {consensus['equal_agreement_win_rate']:.2%}",
            f"- Equal-consensus conservative expectancy: {consensus['equal_agreement_expectancy']:.6f}",
            f"- Weighted-consensus decisions: {consensus['weighted_decision_markets']}, win rate {consensus['weighted_win_rate']:.2%}",
            f"- Weighted-consensus conservative expectancy: {consensus['weighted_expectancy']:.6f}",
            f"- Disagreement markets: {consensus['disagreement_markets']}",
            "- The consensus sample is too small to establish improved robustness.",
            "",
            "## Assets And Timing",
            "",
            f"- BTC: {summary['asset_results']['BTC']['sample_size']} signals, expectancy {summary['asset_results']['BTC']['expectancy']:.6f}",
            f"- ETH: {summary['asset_results']['ETH']['sample_size']} signals, expectancy {summary['asset_results']['ETH']['expectancy']:.6f}",
            f"- SOL: {summary['asset_results']['SOL']['sample_size']} signals, expectancy {summary['asset_results']['SOL']['expectancy']:.6f}",
            f"- Modeled decision-window median: {summary['timing_before_expiry']['median_seconds']:.3f} seconds",
            "- Liquidity and spread interactions: not measurable; zero contemporaneous order-book joins, fail closed.",
            "",
            "## Scientific Justification",
            "",
            "1. Candidate selection used outcomes from the same bounded history, so no untouched wallet-selection test exists.",
            "2. Aggregate expectancy is negative under the fixed conservative cost and delay assumptions.",
            "3. Wallet performance is split: two candidates pass the cost stress descriptively and two fail it.",
            "4. Market overlap is too sparse for a credible consensus strategy.",
            "5. History is concentrated by wallet and date, with one candidate entirely on one UTC date.",
            "6. Historical rows lack delayed executable quotes, direct spread/liquidity joins, queue position, and fill evidence.",
            "",
            "Higher outcome-match rates therefore do not establish executable value. Continuing Wallet exploration would require new selection and execution evidence, contradicting the final-sprint stop rule.",
            "",
            "## Next Branch",
            "",
            "Return to the preserved Repricing branch and test the slower 30-180 second continuation/reversion derivative using existing public sessions. This targets the known two-second execution failure without resuming credential or wallet infrastructure.",
        ]
    )
    return "\n".join(lines) + "\n"
