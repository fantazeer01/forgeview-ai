"""Bounded structural wallet score fixture.

This module implements Wallet Score v1 as a deterministic research-priority
score over existing wallet lifecycle metrics only. It intentionally does not
compute profitability, alpha, ROI, PnL, Sharpe, execution quality,
copyability, mark-to-market values, final outcome quality, or trading advice.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from .trade_history import decimal_or_none, file_sha256, normalize_decimal


DEFAULT_WALLET_SCORE_INPUT = Path("polymarket/models/wallet_intelligence_v1/lifecycle_metrics/wallet_metrics.csv")
DEFAULT_WALLET_SCORE_OUTPUT = Path("polymarket/models/wallet_intelligence_v1/wallet_score_fixture")
WALLET_SCORE_VERSION = "wallet_score_v1_structural_fixture"

ALLOWED_SCORE_INPUTS = [
    "total_lifecycle_positions",
    "fast_crypto_lifecycle_count",
    "fast_crypto_lifecycle_share",
    "partial_exits",
    "percentage_still_open_positions",
    "percentage_sell_only_lifecycles",
    "oversold_bounded_history",
    "average_buy_count_per_lifecycle",
    "average_sell_count_per_lifecycle",
    "average_events_per_lifecycle",
    "near_flat_residual_count",
    "dominant_asset",
    "asset_concentration",
    "dominant_outcome",
    "outcome_concentration",
]

REPORT_ONLY_FIELDS = ["wallet_id", "profile_url"]

FORBIDDEN_SCORE_INPUTS = [
    "pnl",
    "roi",
    "realized_profit",
    "realized_pnl",
    "sharpe",
    "execution_quality",
    "copyability",
    "alpha",
    "mark_to_market",
    "wallet_ranking",
    "final_resolved_win_loss",
    "sealed_holdout",
    "private_wallet",
    "order_placement",
    "authenticated_trading",
]

WALLET_SCORE_FIELDS = [
    "wallet_id",
    "profile_url",
    "wallet_score",
    "score_band",
    "coverage_component",
    "fast_crypto_component",
    "lifecycle_activity_component",
    "event_density_component",
    "specialization_component",
    "bounded_history_penalty",
    "still_open_penalty",
    "small_sample_penalty",
    "concentration_penalty",
    "near_flat_ambiguity_penalty",
    "total_lifecycle_positions",
    "fast_crypto_lifecycle_count",
    "fast_crypto_lifecycle_share",
    "partial_exits",
    "percentage_still_open_positions",
    "percentage_sell_only_lifecycles",
    "oversold_bounded_history",
    "average_events_per_lifecycle",
    "dominant_asset",
    "asset_concentration",
    "dominant_outcome",
    "outcome_concentration",
    "missing_required_metric_count",
    "score_version",
    "source_metrics_sha256",
]

COMPONENT_BOUNDS = {
    "coverage_component": (Decimal("0"), Decimal("25")),
    "fast_crypto_component": (Decimal("0"), Decimal("25")),
    "lifecycle_activity_component": (Decimal("0"), Decimal("15")),
    "event_density_component": (Decimal("0"), Decimal("15")),
    "specialization_component": (Decimal("0"), Decimal("10")),
}

PENALTY_BOUNDS = {
    "bounded_history_penalty": (Decimal("0"), Decimal("20")),
    "still_open_penalty": (Decimal("0"), Decimal("15")),
    "small_sample_penalty": (Decimal("0"), Decimal("20")),
    "concentration_penalty": (Decimal("0"), Decimal("10")),
    "near_flat_ambiguity_penalty": (Decimal("0"), Decimal("5")),
}


def load_wallet_metrics(path: Path = DEFAULT_WALLET_SCORE_INPUT) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def compute_wallet_scores(rows: list[dict[str, str]], *, source_metrics_sha256: str = "") -> tuple[list[dict[str, str]], dict[str, Any]]:
    records = [_score_row(row, source_metrics_sha256=source_metrics_sha256) for row in rows]
    records = sorted(
        records,
        key=lambda row: (
            -_decimal(row["wallet_score"]),
            -_decimal(row["fast_crypto_lifecycle_share"]),
            -int(row["total_lifecycle_positions"] or 0),
            row["wallet_id"],
        ),
    )
    validation = validate_wallet_scores(rows, records)
    validation_bools = [value for value in validation.values() if isinstance(value, bool)]
    validation["all_validation_passed"] = all(validation_bools)
    summary = {
        "task": "Wallet Score Fixture Implementation v1",
        "score_version": WALLET_SCORE_VERSION,
        "wallets_scored": len(records),
        "score_bounds": {"minimum": "0", "maximum": "100"},
        "score_band_counts": dict(sorted(Counter(row["score_band"] for row in records).items())),
        "forbidden_input_audit": {
            "allowed_score_inputs": ALLOWED_SCORE_INPUTS,
            "report_only_fields": REPORT_ONLY_FIELDS,
            "forbidden_score_inputs": FORBIDDEN_SCORE_INPUTS,
            "forbidden_inputs_used": validation["forbidden_inputs_used"],
        },
        "validation": validation,
        "not_computed": [
            "profitability",
            "alpha",
            "ROI",
            "PnL",
            "Sharpe",
            "realized profit",
            "execution quality",
            "copyability",
            "mark-to-market values",
            "final resolved win/loss outcomes",
            "sealed holdout labels or outputs",
            "private wallet data",
            "order-placement data",
            "authenticated trading data",
        ],
        "recommended_next_task": "Wallet Score Fixture Review v1",
    }
    return records, summary


def validate_wallet_scores(source_rows: list[dict[str, str]], score_rows: list[dict[str, str]]) -> dict[str, Any]:
    source_fields = set(source_rows[0].keys()) if source_rows else set()
    required_source_fields = set(ALLOWED_SCORE_INPUTS + REPORT_ONLY_FIELDS)
    missing_source_fields = sorted(required_source_fields - source_fields)
    forbidden_used = [
        field
        for field in ALLOWED_SCORE_INPUTS
        for forbidden in FORBIDDEN_SCORE_INPUTS
        if forbidden in field.lower()
    ]
    ordered_wallets = [row["wallet_id"] for row in score_rows]
    expected_ordered = [
        row["wallet_id"]
        for row in sorted(
            score_rows,
            key=lambda row: (
                -_decimal(row["wallet_score"]),
                -_decimal(row["fast_crypto_lifecycle_share"]),
                -int(row["total_lifecycle_positions"] or 0),
                row["wallet_id"],
            ),
        )
    ]
    score_bounds = all(Decimal("0") <= _decimal(row["wallet_score"]) <= Decimal("100") for row in score_rows)
    deterministic_score_calculation = _deterministic_by_wallet(source_rows, score_rows)
    missing_metric_handling = all(int(row["missing_required_metric_count"]) == 0 for row in score_rows) and not missing_source_fields
    component_bounds = _fields_within_bounds(score_rows, COMPONENT_BOUNDS)
    penalty_bounds = _fields_within_bounds(score_rows, PENALTY_BOUNDS)
    schema_complete = all(set(WALLET_SCORE_FIELDS) == set(row.keys()) for row in score_rows)
    source_provenance = all(row["source_metrics_sha256"] for row in score_rows)
    return {
        "score_bounds": score_bounds,
        "deterministic_score_calculation": deterministic_score_calculation,
        "deterministic_ordering": ordered_wallets == expected_ordered,
        "no_forbidden_metrics_used": not forbidden_used,
        "forbidden_inputs_used": forbidden_used,
        "missing_metric_handling": missing_metric_handling,
        "missing_source_fields": missing_source_fields,
        "allowed_input_set_exact_match": sorted(ALLOWED_SCORE_INPUTS)
        == sorted(
            [
                "total_lifecycle_positions",
                "fast_crypto_lifecycle_count",
                "fast_crypto_lifecycle_share",
                "partial_exits",
                "percentage_still_open_positions",
                "percentage_sell_only_lifecycles",
                "oversold_bounded_history",
                "average_buy_count_per_lifecycle",
                "average_sell_count_per_lifecycle",
                "average_events_per_lifecycle",
                "near_flat_residual_count",
                "dominant_asset",
                "asset_concentration",
                "dominant_outcome",
                "outcome_concentration",
            ]
        ),
        "component_bounds": component_bounds,
        "penalty_bounds": penalty_bounds,
        "output_schema_completeness": schema_complete,
        "source_provenance_completeness": source_provenance,
    }


def write_wallet_scores_csv(path: Path, records: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=WALLET_SCORE_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in records:
            writer.writerow(row)


def run_wallet_score_fixture(
    input_csv: Path = DEFAULT_WALLET_SCORE_INPUT,
    output_dir: Path = DEFAULT_WALLET_SCORE_OUTPUT,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    source_hash = file_sha256(input_csv)
    source_rows = load_wallet_metrics(input_csv)
    scores, summary = compute_wallet_scores(source_rows, source_metrics_sha256=source_hash)

    csv_path = output_dir / "wallet_scores.csv"
    summary_path = output_dir / "wallet_scores_summary.json"
    validation_path = output_dir / "wallet_score_validation.json"
    report_path = output_dir / "wallet_score_report.md"

    write_wallet_scores_csv(csv_path, scores)
    first_hash = file_sha256(csv_path)
    write_wallet_scores_csv(csv_path, scores)
    second_hash = file_sha256(csv_path)
    deterministic = first_hash == second_hash

    summary = {
        "generated_at_utc": generated_at,
        "source_metrics_csv": str(input_csv),
        "source_metrics_sha256": source_hash,
        "output_dir": str(output_dir),
        **summary,
    }
    summary["validation"]["repeatable_export"] = deterministic
    validation_bools = [value for value in summary["validation"].values() if isinstance(value, bool)]
    summary["validation"]["all_validation_passed"] = all(validation_bools)
    summary["reproducibility_hashes"] = {
        "wallet_scores_csv_sha256": file_sha256(csv_path),
        "csv_repeat_export_hash_match": deterministic,
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    validation_path.write_text(json.dumps(summary["validation"], indent=2, sort_keys=True), encoding="utf-8")
    report_path.write_text(_build_score_report(summary, scores), encoding="utf-8")
    return summary


def _score_row(row: dict[str, str], *, source_metrics_sha256: str) -> dict[str, str]:
    missing_count = _missing_required_metric_count(row)
    total = _int(row.get("total_lifecycle_positions"))
    fast_count = _int(row.get("fast_crypto_lifecycle_count"))
    partial_exits = _int(row.get("partial_exits"))
    oversold = _int(row.get("oversold_bounded_history"))
    near_flat = _int(row.get("near_flat_residual_count"))
    fast_share = _decimal(row.get("fast_crypto_lifecycle_share"))
    still_open_share = _decimal(row.get("percentage_still_open_positions"))
    sell_only_share = _decimal(row.get("percentage_sell_only_lifecycles"))
    avg_sell = _decimal(row.get("average_sell_count_per_lifecycle"))
    avg_events = _decimal(row.get("average_events_per_lifecycle"))
    asset_concentration = _decimal(row.get("asset_concentration"))
    outcome_concentration = _decimal(row.get("outcome_concentration"))

    coverage = _coverage_component(total)
    fast_crypto = _fast_crypto_component(fast_share, fast_count)
    lifecycle_activity = _lifecycle_activity_component(partial_exits, total, avg_sell)
    event_density = _event_density_component(avg_events)
    specialization = _specialization_component(row.get("dominant_asset") or "", asset_concentration, outcome_concentration)
    bounded_history = _bounded_history_penalty(sell_only_share, oversold)
    still_open = _still_open_penalty(still_open_share)
    small_sample = _small_sample_penalty(total)
    concentration = _concentration_penalty(asset_concentration, outcome_concentration)
    near_flat_penalty = _near_flat_ambiguity_penalty(near_flat, total)

    score = _clip(
        coverage
        + fast_crypto
        + lifecycle_activity
        + event_density
        + specialization
        - bounded_history
        - still_open
        - small_sample
        - concentration
        - near_flat_penalty,
        Decimal("0"),
        Decimal("100"),
    )

    return {
        "wallet_id": (row.get("wallet_id") or "").lower(),
        "profile_url": row.get("profile_url") or "",
        "wallet_score": normalize_decimal(score),
        "score_band": _score_band(score),
        "coverage_component": normalize_decimal(coverage),
        "fast_crypto_component": normalize_decimal(fast_crypto),
        "lifecycle_activity_component": normalize_decimal(lifecycle_activity),
        "event_density_component": normalize_decimal(event_density),
        "specialization_component": normalize_decimal(specialization),
        "bounded_history_penalty": normalize_decimal(bounded_history),
        "still_open_penalty": normalize_decimal(still_open),
        "small_sample_penalty": normalize_decimal(small_sample),
        "concentration_penalty": normalize_decimal(concentration),
        "near_flat_ambiguity_penalty": normalize_decimal(near_flat_penalty),
        "total_lifecycle_positions": str(total),
        "fast_crypto_lifecycle_count": str(fast_count),
        "fast_crypto_lifecycle_share": normalize_decimal(fast_share),
        "partial_exits": str(partial_exits),
        "percentage_still_open_positions": normalize_decimal(still_open_share),
        "percentage_sell_only_lifecycles": normalize_decimal(sell_only_share),
        "oversold_bounded_history": str(oversold),
        "average_events_per_lifecycle": normalize_decimal(avg_events),
        "dominant_asset": row.get("dominant_asset") or "",
        "asset_concentration": normalize_decimal(asset_concentration),
        "dominant_outcome": row.get("dominant_outcome") or "",
        "outcome_concentration": normalize_decimal(outcome_concentration),
        "missing_required_metric_count": str(missing_count),
        "score_version": WALLET_SCORE_VERSION,
        "source_metrics_sha256": source_metrics_sha256,
    }


def _coverage_component(total: int) -> Decimal:
    if total < 5:
        return Decimal("0")
    if total <= 9:
        return Decimal("8")
    if total <= 24:
        return Decimal("15")
    if total <= 49:
        return Decimal("21")
    return Decimal("25")


def _fast_crypto_component(fast_share: Decimal, fast_count: int) -> Decimal:
    share_points = _clip(Decimal("20") * fast_share, Decimal("0"), Decimal("20"))
    if fast_count < 5:
        count_points = Decimal("0")
    elif fast_count <= 9:
        count_points = Decimal("2")
    elif fast_count <= 24:
        count_points = Decimal("4")
    else:
        count_points = Decimal("5")
    return _clip(share_points + count_points, Decimal("0"), Decimal("25"))


def _lifecycle_activity_component(partial_exits: int, total: int, avg_sell: Decimal) -> Decimal:
    share = Decimal("0") if total == 0 else Decimal(partial_exits) / Decimal(total)
    if share == 0:
        partial_points = Decimal("0")
    elif share < Decimal("0.10"):
        partial_points = Decimal("4")
    elif share < Decimal("0.35"):
        partial_points = Decimal("8")
    elif share <= Decimal("0.75"):
        partial_points = Decimal("12")
    else:
        partial_points = Decimal("8")
    sell_support = Decimal("3") if avg_sell > 0 else Decimal("0")
    return _clip(partial_points + sell_support, Decimal("0"), Decimal("15"))


def _event_density_component(avg_events: Decimal) -> Decimal:
    if avg_events < Decimal("1"):
        return Decimal("0")
    if avg_events < Decimal("2"):
        return Decimal("8")
    if avg_events <= Decimal("8"):
        return Decimal("15")
    if avg_events <= Decimal("20"):
        return Decimal("11")
    return Decimal("6")


def _specialization_component(dominant_asset: str, asset_concentration: Decimal, outcome_concentration: Decimal) -> Decimal:
    asset_points = Decimal("4") if dominant_asset.upper() in {"BTC", "ETH", "SOL"} else Decimal("0")
    if Decimal("0.30") <= asset_concentration <= Decimal("0.80"):
        concentration_points = Decimal("4")
    elif Decimal("0.80") < asset_concentration <= Decimal("0.95"):
        concentration_points = Decimal("3")
    elif asset_concentration > Decimal("0.95"):
        concentration_points = Decimal("1")
    else:
        concentration_points = Decimal("0")
    outcome_points = Decimal("2") if outcome_concentration <= Decimal("0.70") else Decimal("0")
    return _clip(asset_points + concentration_points + outcome_points, Decimal("0"), Decimal("10"))


def _bounded_history_penalty(sell_only_share: Decimal, oversold: int) -> Decimal:
    return _clip(_clip(sell_only_share * Decimal("20"), Decimal("0"), Decimal("15")) + min(Decimal("5"), Decimal(oversold) * Decimal("2.5")), Decimal("0"), Decimal("20"))


def _still_open_penalty(still_open_share: Decimal) -> Decimal:
    if still_open_share <= Decimal("0.50"):
        return Decimal("0")
    if still_open_share <= Decimal("0.75"):
        return Decimal("5")
    if still_open_share <= Decimal("0.90"):
        return Decimal("10")
    return Decimal("15")


def _small_sample_penalty(total: int) -> Decimal:
    if total < 5:
        return Decimal("20")
    if total <= 9:
        return Decimal("10")
    if total <= 14:
        return Decimal("5")
    return Decimal("0")


def _concentration_penalty(asset_concentration: Decimal, outcome_concentration: Decimal) -> Decimal:
    penalty = Decimal("0")
    if asset_concentration > Decimal("0.95"):
        penalty += Decimal("5")
    if outcome_concentration > Decimal("0.75"):
        penalty += Decimal("5")
    return penalty


def _near_flat_ambiguity_penalty(near_flat: int, total: int) -> Decimal:
    share = Decimal("0") if total == 0 else Decimal(near_flat) / Decimal(total)
    if share <= Decimal("0.05"):
        return Decimal("0")
    if share <= Decimal("0.20"):
        return Decimal("2")
    return Decimal("5")


def _score_band(score: Decimal) -> str:
    if score >= Decimal("75"):
        return "high_priority"
    if score >= Decimal("50"):
        return "medium_priority"
    if score >= Decimal("25"):
        return "low_priority"
    return "insufficient_visible_structure"


def _build_score_report(summary: dict[str, Any], scores: list[dict[str, str]]) -> str:
    lines = [
        "# Wallet Score Fixture Implementation v1",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "## Scope",
        "",
        "Wallet scores are bounded structural research-priority labels only. They do not indicate profitability, alpha, ROI, PnL, Sharpe, execution quality, copyability, or trading suitability.",
        "",
        "## Source",
        "",
        f"- Source metrics CSV: `{summary['source_metrics_csv']}`",
        f"- Source metrics SHA-256: `{summary['source_metrics_sha256']}`",
        f"- Wallets scored: {summary['wallets_scored']}",
        "",
        "## Forbidden Inputs Confirmed",
        "",
    ]
    for item in summary["forbidden_input_audit"]["forbidden_score_inputs"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Allowed Score Inputs", ""])
    for item in ALLOWED_SCORE_INPUTS:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Score Band Distribution", ""])
    for band, count in summary["score_band_counts"].items():
        lines.append(f"- `{band}`: {count}")
    lines.extend(["", "## Component And Penalty Summary", ""])
    lines.append("- Positive components: coverage, fast-crypto relevance, lifecycle activity, event-density consistency, and specialization.")
    lines.append("- Penalties: SELL-only/bounded-history risk, excessive still-open share, small visible sample, excessive concentration, and near-flat residual ambiguity.")
    lines.extend(["", "## Wallet Score Rows", ""])
    for row in scores:
        lines.append(
            f"- `{row['wallet_id']}`: score={row['wallet_score']}, band={row['score_band']}, positions={row['total_lifecycle_positions']}, fast_crypto_share={row['fast_crypto_lifecycle_share']}"
        )
    lines.extend(["", "## Validation", ""])
    for name, value in summary["validation"].items():
        lines.append(f"- `{name}`: {str(value).lower()}")
    lines.extend(["", "## Recommended Next Task", "", f"`{summary['recommended_next_task']}`", ""])
    return "\n".join(lines)


def _missing_required_metric_count(row: dict[str, str]) -> int:
    return sum(1 for field in ALLOWED_SCORE_INPUTS if row.get(field) in (None, ""))


def _deterministic_by_wallet(source_rows: list[dict[str, str]], score_rows: list[dict[str, str]]) -> bool:
    by_wallet = score_rows_by_wallet(score_rows)
    for row in source_rows:
        wallet = (row.get("wallet_id") or "").lower()
        expected = _score_row(row, source_metrics_sha256=by_wallet.get(wallet, {}).get("source_metrics_sha256", ""))
        if wallet not in by_wallet:
            return False
        if expected != by_wallet[wallet]:
            return False
    return True


def score_rows_by_wallet(score_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["wallet_id"]: row for row in score_rows}


def _fields_within_bounds(rows: list[dict[str, str]], bounds: dict[str, tuple[Decimal, Decimal]]) -> bool:
    return all(low <= _decimal(row[field]) <= high for row in rows for field, (low, high) in bounds.items())


def _decimal(value: Any) -> Decimal:
    return decimal_or_none(value) or Decimal("0")


def _int(value: Any) -> int:
    try:
        return int(Decimal(str(value or "0")))
    except Exception:
        return 0


def _clip(value: Decimal, low: Decimal, high: Decimal) -> Decimal:
    return max(low, min(high, value))
