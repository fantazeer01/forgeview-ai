"""H1 wallet outcome-skill baseline for public Wallet Intelligence evidence.

This module tests whether visible public wallet outcome choices differ from a
random baseline. It is descriptive and falsification-oriented; it does not
compute financial results, execution quality, trade recommendations, or live
signals.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .trade_history import file_sha256


DEFAULT_WALLET_SKILL_INPUT = Path(
    "polymarket/models/wallet_intelligence_v1/market_outcome_resolution_v1/market_outcome_join.csv"
)
DEFAULT_WALLET_SKILL_OUTPUT = Path("polymarket/models/wallet_intelligence_v1/outcome_skill_baseline_v1")
DEFAULT_WALLET_SKILL_SCORE_INPUT = Path(
    "polymarket/models/wallet_intelligence_v1/wallet_score_broader_evidence_v1/wallet_scores.csv"
)
DEFAULT_WALLET_SKILL_WATCHLIST_INPUT = Path(
    "polymarket/models/wallet_intelligence_v1/wallet_watchlist_broader_v1/wallet_watchlist.csv"
)

MIN_RESOLVED_POSITIONS = 30
Z_THRESHOLD = 1.96
RANDOM_BASELINE_RATE = 0.5
SKILL_VERSION = "wallet_outcome_skill_baseline_v1"

WALLET_SKILL_FIELDS = [
    "wallet_id",
    "profile_url",
    "wallet_score",
    "score_band",
    "watchlist_priority_bucket",
    "watchlist_reason_codes",
    "total_fast_crypto_positions",
    "resolved_positions",
    "matched_outcomes",
    "unmatched_outcomes",
    "unresolved_positions",
    "insufficient_evidence_positions",
    "unresolved_fraction",
    "high_confidence_resolved_positions",
    "match_rate",
    "population_baseline_rate",
    "random_baseline_rate",
    "leave_one_out_population_rate",
    "difference_vs_population_baseline",
    "difference_vs_random_baseline",
    "z_score_vs_population_baseline",
    "z_score_vs_random_baseline",
    "wilson_ci_low",
    "wilson_ci_high",
    "btc_resolved_positions",
    "eth_resolved_positions",
    "sol_resolved_positions",
    "sample_gate_status",
    "evidence_classification",
    "invalidation_risks",
]

FORBIDDEN_FIELD_FRAGMENTS = (
    "pnl",
    "roi",
    "sharpe",
    "alpha",
    "profit",
    "copyability",
    "execution_quality",
    "trading_recommendation",
)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def run_wallet_outcome_skill_baseline(
    input_csv: Path = DEFAULT_WALLET_SKILL_INPUT,
    output_dir: Path = DEFAULT_WALLET_SKILL_OUTPUT,
    *,
    score_csv: Path = DEFAULT_WALLET_SKILL_SCORE_INPUT,
    watchlist_csv: Path = DEFAULT_WALLET_SKILL_WATCHLIST_INPUT,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)

    outcome_rows = load_csv(input_csv)
    score_rows = load_csv(score_csv) if score_csv.exists() else []
    watchlist_rows = load_csv(watchlist_csv) if watchlist_csv.exists() else []

    rows, summary = build_wallet_outcome_skill_baseline(
        outcome_rows,
        score_rows=score_rows,
        watchlist_rows=watchlist_rows,
        generated_at=generated_at,
        input_csv=input_csv,
        output_dir=output_dir,
    )

    csv_path = output_dir / "wallet_skill_baseline.csv"
    summary_path = output_dir / "wallet_skill_summary.json"
    report_path = output_dir / "wallet_skill_report.md"

    write_wallet_skill_csv(csv_path, rows)
    first_hash = file_sha256(csv_path)
    write_wallet_skill_csv(csv_path, rows)
    second_hash = file_sha256(csv_path)
    summary["validation"]["repeatable_export"] = first_hash == second_hash
    summary["validation"]["all_validation_passed"] = all(
        value for value in summary["validation"].values() if isinstance(value, bool)
    )

    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report = render_wallet_skill_report(summary)
    report_path.write_text(report, encoding="utf-8")
    summary["reproducibility_hashes"] = {
        "wallet_skill_baseline_csv_sha256": file_sha256(csv_path),
        "wallet_skill_summary_json_sha256": file_sha256(summary_path),
        "wallet_skill_report_md_sha256": file_sha256(report_path),
        "csv_repeat_export_hash_match": first_hash == second_hash,
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def build_wallet_outcome_skill_baseline(
    outcome_rows: list[dict[str, str]],
    *,
    score_rows: list[dict[str, str]] | None = None,
    watchlist_rows: list[dict[str, str]] | None = None,
    generated_at: str = "",
    input_csv: Path | None = None,
    output_dir: Path | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    score_by_wallet = {(row.get("wallet_id") or "").lower(): row for row in score_rows or []}
    watchlist_by_wallet = {(row.get("wallet_id") or "").lower(): row for row in watchlist_rows or []}
    fast_rows = [row for row in outcome_rows if _is_fast_crypto_row(row)]
    tested_rows = [row for row in fast_rows if row.get("lifecycle_resolution_status") in {"matched_outcome", "unmatched_outcome"}]
    matched_total = sum(1 for row in tested_rows if row.get("lifecycle_resolution_status") == "matched_outcome")
    population_total = len(tested_rows)
    population_rate = matched_total / population_total if population_total else 0.0

    wallet_counts: dict[str, Counter[str]] = defaultdict(Counter)
    wallet_assets: dict[str, Counter[str]] = defaultdict(Counter)
    wallet_profile: dict[str, str] = {}
    for row in fast_rows:
        wallet_id = (row.get("wallet_id") or "").lower()
        wallet_profile[wallet_id] = row.get("profile_url") or ""
        status = row.get("lifecycle_resolution_status") or ""
        wallet_counts[wallet_id]["total_fast_crypto_positions"] += 1
        if status == "unresolved_market":
            wallet_counts[wallet_id]["unresolved_positions"] += 1
        elif status == "insufficient_evidence":
            wallet_counts[wallet_id]["insufficient_evidence_positions"] += 1
        elif status in {"matched_outcome", "unmatched_outcome"}:
            wallet_counts[wallet_id]["resolved_positions"] += 1
            wallet_assets[wallet_id][row.get("asset_class") or ""] += 1
            if status == "matched_outcome":
                wallet_counts[wallet_id]["matched_outcomes"] += 1
            else:
                wallet_counts[wallet_id]["unmatched_outcomes"] += 1
            if row.get("join_confidence") == "high":
                wallet_counts[wallet_id]["high_confidence_resolved_positions"] += 1

    results = []
    for wallet_id in sorted(wallet_counts):
        counts = wallet_counts[wallet_id]
        resolved = counts["resolved_positions"]
        matched = counts["matched_outcomes"]
        total_fast = counts["total_fast_crypto_positions"]
        unresolved = counts["unresolved_positions"]
        insufficient = counts["insufficient_evidence_positions"]
        match_rate = matched / resolved if resolved else 0.0
        loo_total = population_total - resolved
        loo_matched = matched_total - matched
        loo_rate = loo_matched / loo_total if loo_total else population_rate
        diff_population = match_rate - population_rate if resolved else 0.0
        diff_random = match_rate - RANDOM_BASELINE_RATE if resolved else 0.0
        z_population = _z_score(matched, resolved, population_rate)
        z_random = _z_score(matched, resolved, RANDOM_BASELINE_RATE)
        ci_low, ci_high = _wilson_interval(matched, resolved)
        sample_gate = "passed" if resolved >= MIN_RESOLVED_POSITIONS else "insufficient_resolved_sample"
        classification = _classify_wallet(
            resolved=resolved,
            ci_low=ci_low,
            ci_high=ci_high,
            z_population=z_population,
            population_rate=population_rate,
        )
        score = score_by_wallet.get(wallet_id, {})
        watchlist = watchlist_by_wallet.get(wallet_id, {})
        results.append(
            {
                "wallet_id": wallet_id,
                "profile_url": wallet_profile.get(wallet_id, ""),
                "wallet_score": score.get("wallet_score") or score.get("score") or "",
                "score_band": score.get("score_band") or "",
                "watchlist_priority_bucket": watchlist.get("priority_bucket") or "",
                "watchlist_reason_codes": watchlist.get("reason_codes") or "",
                "total_fast_crypto_positions": str(total_fast),
                "resolved_positions": str(resolved),
                "matched_outcomes": str(matched),
                "unmatched_outcomes": str(counts["unmatched_outcomes"]),
                "unresolved_positions": str(unresolved),
                "insufficient_evidence_positions": str(insufficient),
                "unresolved_fraction": _fmt(unresolved / total_fast if total_fast else 0.0),
                "high_confidence_resolved_positions": str(counts["high_confidence_resolved_positions"]),
                "match_rate": _fmt(match_rate),
                "population_baseline_rate": _fmt(population_rate),
                "random_baseline_rate": _fmt(RANDOM_BASELINE_RATE),
                "leave_one_out_population_rate": _fmt(loo_rate),
                "difference_vs_population_baseline": _fmt(diff_population),
                "difference_vs_random_baseline": _fmt(diff_random),
                "z_score_vs_population_baseline": _fmt(z_population),
                "z_score_vs_random_baseline": _fmt(z_random),
                "wilson_ci_low": _fmt(ci_low),
                "wilson_ci_high": _fmt(ci_high),
                "btc_resolved_positions": str(wallet_assets[wallet_id]["BTC"]),
                "eth_resolved_positions": str(wallet_assets[wallet_id]["ETH"]),
                "sol_resolved_positions": str(wallet_assets[wallet_id]["SOL"]),
                "sample_gate_status": sample_gate,
                "evidence_classification": classification,
                "invalidation_risks": _invalidation_risks(classification, resolved),
            }
        )

    validation = validate_wallet_outcome_skill(results, fast_rows, tested_rows)
    conclusion = _sprint_conclusion(results, population_total, population_rate)
    summary = {
        "task": "Wallet Outcome Skill Baseline Sprint v1",
        "hypothesis": "H1: Some public wallets consistently make better decisions than random.",
        "generated_at_utc": generated_at,
        "input_csv": str(input_csv or ""),
        "output_dir": str(output_dir or ""),
        "skill_version": SKILL_VERSION,
        "wallet_count": len(results),
        "fast_crypto_positions": len(fast_rows),
        "resolved_positions": population_total,
        "matched_outcomes": matched_total,
        "unmatched_outcomes": population_total - matched_total,
        "unresolved_positions": sum(1 for row in fast_rows if row.get("lifecycle_resolution_status") == "unresolved_market"),
        "insufficient_evidence_positions": sum(1 for row in fast_rows if row.get("lifecycle_resolution_status") == "insufficient_evidence"),
        "baseline_statistics": {
            "population_match_rate": _fmt(population_rate),
            "random_baseline_rate": _fmt(RANDOM_BASELINE_RATE),
            "population_difference_vs_random": _fmt(population_rate - RANDOM_BASELINE_RATE),
            "minimum_resolved_positions_per_wallet": MIN_RESOLVED_POSITIONS,
            "z_threshold": Z_THRESHOLD,
        },
        "asset_breakdown": _asset_breakdown(tested_rows),
        "classification_counts": dict(sorted(Counter(row["evidence_classification"] for row in results).items())),
        "wallets_with_above_baseline_evidence": [
            row["wallet_id"] for row in results if row["evidence_classification"] == "above_baseline_evidence"
        ],
        "wallets_with_below_baseline_evidence": [
            row["wallet_id"] for row in results if row["evidence_classification"] == "below_baseline_evidence"
        ],
        "wallets_with_insufficient_evidence": [
            row["wallet_id"] for row in results if row["evidence_classification"] == "insufficient_evidence"
        ],
        "evidence_supporting_h1": conclusion["supporting_evidence"],
        "evidence_against_h1": conclusion["counter_evidence"],
        "final_conclusion": conclusion["final_conclusion"],
        "final_conclusion_reason": conclusion["reason"],
        "recommended_next_hypothesis": conclusion["recommended_next_hypothesis"],
        "observed_not_interpreted_as": [
            "financial result",
            "execution feasibility",
            "visibility-delay evidence",
            "liquidity evidence",
            "complete-history evidence",
            "trading instruction",
        ],
        "validation": validation,
    }
    return results, summary


def validate_wallet_outcome_skill(
    rows: list[dict[str, str]],
    fast_rows: list[dict[str, str]],
    tested_rows: list[dict[str, str]],
) -> dict[str, Any]:
    resolved_sum = sum(int(row["resolved_positions"]) for row in rows)
    matched_sum = sum(int(row["matched_outcomes"]) for row in rows)
    unresolved_sum = sum(int(row["unresolved_positions"]) for row in rows)
    insufficient_sum = sum(int(row["insufficient_evidence_positions"]) for row in rows)
    forbidden_fields = [
        field for field in WALLET_SKILL_FIELDS if any(fragment in field.lower() for fragment in FORBIDDEN_FIELD_FRAGMENTS)
    ]
    forbidden_content_rows = [
        row["wallet_id"]
        for row in rows
        if any(fragment in " ".join(row.values()).lower() for fragment in FORBIDDEN_FIELD_FRAGMENTS)
    ]
    return {
        "all_tested_rows_are_resolved_binary_fast_crypto": all(
            _is_fast_crypto_row(row)
            and row.get("lifecycle_resolution_status") in {"matched_outcome", "unmatched_outcome"}
            and row.get("winning_outcome") in {"Up", "Down"}
            for row in tested_rows
        ),
        "wallet_counts_reconcile_to_aggregate": resolved_sum == len(tested_rows),
        "matched_counts_reconcile_to_aggregate": matched_sum
        == sum(1 for row in tested_rows if row.get("lifecycle_resolution_status") == "matched_outcome"),
        "unresolved_and_insufficient_counts_reconcile": unresolved_sum + insufficient_sum + resolved_sum == len(fast_rows),
        "baseline_definitions_present": bool(MIN_RESOLVED_POSITIONS and Z_THRESHOLD and RANDOM_BASELINE_RATE),
        "deterministic_ordering": [row["wallet_id"] for row in rows] == sorted(row["wallet_id"] for row in rows),
        "output_schema_complete": all(set(row) == set(WALLET_SKILL_FIELDS) for row in rows),
        "no_forbidden_metric_fields": not forbidden_fields,
        "forbidden_metric_fields": forbidden_fields,
        "no_forbidden_claims": not forbidden_content_rows,
        "forbidden_claim_rows": forbidden_content_rows[:20],
    }


def write_wallet_skill_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=WALLET_SKILL_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def render_wallet_skill_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Wallet Outcome Skill Baseline Sprint v1",
        "",
        "Hypothesis: H1 - Some public wallets consistently make better decisions than random.",
        "",
        "This sprint tries to disprove H1 using currently available public evidence. It is not a trading signal, not investment advice, and not an execution-quality study.",
        "",
        "## Observed Evidence",
        "",
        f"- Wallets evaluated: {summary['wallet_count']}",
        f"- Fast crypto lifecycle positions: {summary['fast_crypto_positions']}",
        f"- Resolved positions tested: {summary['resolved_positions']}",
        f"- Matched outcomes: {summary['matched_outcomes']}",
        f"- Unmatched outcomes: {summary['unmatched_outcomes']}",
        f"- Population match rate: {summary['baseline_statistics']['population_match_rate']}",
        f"- Random baseline rate: {summary['baseline_statistics']['random_baseline_rate']}",
        "",
        "## Classification Counts",
        "",
    ]
    for key, value in summary["classification_counts"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Evidence Supporting H1",
            "",
        ]
    )
    for item in summary["evidence_supporting_h1"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Evidence Against H1", ""])
    for item in summary["evidence_against_h1"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Final Conclusion",
            "",
            f"{summary['final_conclusion']}",
            "",
            summary["final_conclusion_reason"],
            "",
            "## Recommended Next Hypothesis",
            "",
            summary["recommended_next_hypothesis"],
        ]
    )
    return "\n".join(lines) + "\n"


def _is_fast_crypto_row(row: dict[str, str]) -> bool:
    return row.get("asset_class") in {"BTC", "ETH", "SOL"} and row.get("up_down_market") == "true"


def _classify_wallet(
    *,
    resolved: int,
    ci_low: float,
    ci_high: float,
    z_population: float,
    population_rate: float,
) -> str:
    if resolved < MIN_RESOLVED_POSITIONS:
        return "insufficient_evidence"
    if z_population >= Z_THRESHOLD and ci_low > RANDOM_BASELINE_RATE and ci_low > population_rate:
        return "above_baseline_evidence"
    if z_population <= -Z_THRESHOLD and ci_high < population_rate:
        return "below_baseline_evidence"
    return "sample_size_consistent_with_baseline"


def _sprint_conclusion(rows: list[dict[str, str]], population_total: int, population_rate: float) -> dict[str, Any]:
    above = [row for row in rows if row["evidence_classification"] == "above_baseline_evidence"]
    below = [row for row in rows if row["evidence_classification"] == "below_baseline_evidence"]
    inconclusive = [row for row in rows if row["evidence_classification"] == "sample_size_consistent_with_baseline"]
    insufficient = [row for row in rows if row["evidence_classification"] == "insufficient_evidence"]
    supporting = [
        f"{len(above)} wallets exceeded the population baseline under the minimum sample and uncertainty gates.",
        f"The aggregate resolved-position match rate was {_fmt(population_rate)} over {population_total} resolved fast-crypto rows.",
    ]
    if above:
        supporting.append("Above-baseline wallets: " + ", ".join(row["wallet_id"] for row in above) + ".")
    counter = [
        f"{len(below)} wallets showed below-baseline evidence under the same gates.",
        f"{len(inconclusive)} wallets were consistent with the population baseline after sample-size adjustment.",
        f"{len(insufficient)} wallets failed the minimum resolved-position sample gate.",
        "The wallet set is retrospectively selected and therefore exposed to selection and survivorship bias.",
        "The current evidence does not measure public visibility delay, actionable time remaining, fill certainty, or complete wallet history.",
    ]
    if len(above) >= 2 and not below and population_rate - RANDOM_BASELINE_RATE >= 0.03:
        return {
            "final_conclusion": "SUPPORTED",
            "reason": "H1 is supported for this bounded evidence because multiple wallets clear conservative above-baseline gates without symmetric below-baseline evidence.",
            "supporting_evidence": supporting,
            "counter_evidence": counter,
            "recommended_next_hypothesis": "H2: Wallet Activity Visibility Delay Sprint v1",
        }
    if not above and population_rate <= RANDOM_BASELINE_RATE + 0.01:
        return {
            "final_conclusion": "REJECTED",
            "reason": "H1 is rejected for this bounded evidence because no wallet clears the above-baseline gates and aggregate outcome quality is indistinguishable from random.",
            "supporting_evidence": supporting,
            "counter_evidence": counter,
            "recommended_next_hypothesis": "Stop or sharply narrow public-wallet strategy research before adding new wallet infrastructure.",
        }
    return {
        "final_conclusion": "INCONCLUSIVE",
        "reason": "H1 is not disproven, but it is not convincingly supported: several wallets clear above-baseline gates, several fail in the opposite direction, and major retrospective-data invalidation risks remain.",
        "supporting_evidence": supporting,
        "counter_evidence": counter,
        "recommended_next_hypothesis": "H2: Wallet Activity Visibility Delay Sprint v1, but only for wallets that cleared the above-baseline H1 gates.",
    }


def _invalidation_risks(classification: str, resolved: int) -> str:
    risks = [
        "retrospective_selection_bias",
        "bounded_history",
        "missing_visibility_delay",
        "missing_entry_exit_linkage",
        "missing_liquidity_context",
    ]
    if resolved < MIN_RESOLVED_POSITIONS:
        risks.append("small_sample")
    if classification == "above_baseline_evidence":
        risks.append("requires_out_of_sample_confirmation")
    return ";".join(risks)


def _asset_breakdown(rows: list[dict[str, str]]) -> dict[str, dict[str, int]]:
    breakdown: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        asset = row.get("asset_class") or "other"
        status = row.get("lifecycle_resolution_status") or ""
        breakdown[asset]["resolved_positions"] += 1
        if status == "matched_outcome":
            breakdown[asset]["matched_outcomes"] += 1
        elif status == "unmatched_outcome":
            breakdown[asset]["unmatched_outcomes"] += 1
    return {asset: dict(counts) for asset, counts in sorted(breakdown.items())}


def _z_score(matches: int, total: int, baseline: float) -> float:
    if total <= 0 or baseline <= 0 or baseline >= 1:
        return 0.0
    standard_error = math.sqrt(baseline * (1 - baseline) / total)
    return ((matches / total) - baseline) / standard_error if standard_error else 0.0


def _wilson_interval(matches: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return 0.0, 0.0
    p_hat = matches / total
    denominator = 1 + z * z / total
    center = (p_hat + z * z / (2 * total)) / denominator
    margin = (z / denominator) * math.sqrt((p_hat * (1 - p_hat) / total) + (z * z / (4 * total * total)))
    return max(0.0, center - margin), min(1.0, center + margin)


def _fmt(value: float) -> str:
    return f"{value:.6f}"
