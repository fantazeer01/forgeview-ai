"""Research watchlist generated from existing Wallet Score outputs only.

The watchlist is for monitoring and deeper analysis triage. It is not a
trading signal, copy-trading recommendation, profitability ranking, or alpha
claim.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from .trade_history import decimal_or_none, file_sha256


DEFAULT_WATCHLIST_INPUT = Path("polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_scores.csv")
DEFAULT_WATCHLIST_OUTPUT = Path("polymarket/models/wallet_intelligence_v1/wallet_watchlist_v1")
WATCHLIST_VERSION = "wallet_watchlist_v1_from_score_fixture"
MINIMUM_VISIBLE_LIFECYCLES = 5

WATCHLIST_FIELDS = [
    "wallet_id",
    "profile_url",
    "score",
    "priority_bucket",
    "reason_codes",
    "structural_strengths",
    "structural_risks",
    "recommended_next_research_action",
    "source_score_version",
    "source_scores_sha256",
    "watchlist_version",
]

FORBIDDEN_METRIC_FRAGMENTS = (
    "pnl",
    "roi",
    "sharpe",
    "copyability",
    "alpha",
    "profit",
    "mark_to_market",
    "ranking",
)

FORBIDDEN_CLAIM_PHRASES = (
    "trading signal",
    "copy-trading recommendation",
    "profitability ranking",
    "alpha claim",
    "recommended trade",
    "best wallet",
)

REQUIRED_DISCLAIMERS = (
    "monitoring/research artifact",
    "not a trading signal",
    "not a copy-trading recommendation",
    "based only on bounded public history",
)


def load_wallet_scores(path: Path = DEFAULT_WATCHLIST_INPUT) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def compute_wallet_watchlist(
    rows: list[dict[str, str]],
    *,
    source_scores_sha256: str = "",
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    included: list[dict[str, str]] = []
    excluded: list[dict[str, str]] = []
    for row in rows:
        if _passes_minimum_visibility(row):
            included.append(_watchlist_row(row, source_scores_sha256=source_scores_sha256))
        else:
            excluded.append(
                {
                    "wallet_id": (row.get("wallet_id") or "").lower(),
                    "reason": "minimum_visibility_failed",
                }
            )
    included = sorted(
        included,
        key=lambda row: (
            _bucket_order(row["priority_bucket"]),
            -_decimal(row["score"]),
            row["wallet_id"],
        ),
    )
    validation = validate_wallet_watchlist(included)
    validation_bools = [value for value in validation.values() if isinstance(value, bool)]
    validation["all_validation_passed"] = all(validation_bools)
    summary = {
        "task": "Wallet Watchlist v1",
        "watchlist_version": WATCHLIST_VERSION,
        "source": "existing Wallet Score outputs only",
        "wallets_input": len(rows),
        "wallets_included": len(included),
        "wallets_excluded": len(excluded),
        "excluded_wallets": excluded,
        "minimum_visibility": {
            "minimum_lifecycle_positions": MINIMUM_VISIBLE_LIFECYCLES,
            "missing_required_metric_count": "0",
            "known_score_bucket_required": True,
        },
        "priority_bucket_counts": dict(sorted(Counter(row["priority_bucket"] for row in included).items())),
        "validation": validation,
        "not_computed": [
            "PnL",
            "ROI",
            "Sharpe",
            "copyability",
            "alpha",
            "profitability",
            "mark-to-market values",
            "wallet ranking",
            "trading recommendations",
        ],
        "required_disclaimers": list(REQUIRED_DISCLAIMERS),
        "recommended_next_task": "Wallet Watchlist Review v1",
    }
    return included, summary


def validate_wallet_watchlist(rows: list[dict[str, str]]) -> dict[str, Any]:
    ordered = rows == sorted(
        rows,
        key=lambda row: (
            _bucket_order(row["priority_bucket"]),
            -_decimal(row["score"]),
            row["wallet_id"],
        ),
    )
    schema_complete = all(set(row.keys()) == set(WATCHLIST_FIELDS) for row in rows)
    reason_codes_present = all(bool(row["reason_codes"]) and row["reason_codes"] != "none" for row in rows)
    actions_present = all(bool(row["recommended_next_research_action"]) for row in rows)
    forbidden_metric_fields = [
        field
        for field in WATCHLIST_FIELDS
        for fragment in FORBIDDEN_METRIC_FRAGMENTS
        if fragment in field.lower()
    ]
    content = "\n".join(
        " ".join(
            [
                row["reason_codes"],
                row["structural_strengths"],
                row["structural_risks"],
                row["recommended_next_research_action"],
            ]
        ).lower()
        for row in rows
    )
    forbidden_claims = [
        phrase
        for phrase in FORBIDDEN_CLAIM_PHRASES
        if phrase in content and not phrase.startswith("not ")
    ]
    return {
        "deterministic_ordering": ordered,
        "output_schema_completeness": schema_complete,
        "reason_codes_present": reason_codes_present,
        "research_actions_present": actions_present,
        "no_forbidden_metric_fields": not forbidden_metric_fields,
        "forbidden_metric_fields": forbidden_metric_fields,
        "no_forbidden_claims": not forbidden_claims,
        "forbidden_claim_phrases": forbidden_claims,
    }


def write_watchlist_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=WATCHLIST_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def run_wallet_watchlist(
    input_csv: Path = DEFAULT_WATCHLIST_INPUT,
    output_dir: Path = DEFAULT_WATCHLIST_OUTPUT,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    source_hash = file_sha256(input_csv)
    scores = load_wallet_scores(input_csv)
    rows, summary = compute_wallet_watchlist(scores, source_scores_sha256=source_hash)

    csv_path = output_dir / "wallet_watchlist.csv"
    summary_path = output_dir / "wallet_watchlist_summary.json"
    report_path = output_dir / "wallet_watchlist_report.md"

    write_watchlist_csv(csv_path, rows)
    first_hash = file_sha256(csv_path)
    write_watchlist_csv(csv_path, rows)
    second_hash = file_sha256(csv_path)
    repeatable = first_hash == second_hash
    summary = {
        "generated_at_utc": generated_at,
        "source_scores_csv": str(input_csv),
        "source_scores_sha256": source_hash,
        "output_dir": str(output_dir),
        **summary,
    }
    summary["validation"]["repeatable_export"] = repeatable
    validation_bools = [value for value in summary["validation"].values() if isinstance(value, bool)]
    summary["validation"]["all_validation_passed"] = all(validation_bools)
    summary["reproducibility_hashes"] = {
        "wallet_watchlist_csv_sha256": file_sha256(csv_path),
        "csv_repeat_export_hash_match": repeatable,
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report_path.write_text(_build_watchlist_report(summary, rows), encoding="utf-8")
    return summary


def _watchlist_row(row: dict[str, str], *, source_scores_sha256: str) -> dict[str, str]:
    reason_codes = _reason_codes(row)
    return {
        "wallet_id": (row.get("wallet_id") or "").lower(),
        "profile_url": row.get("profile_url") or "",
        "score": row.get("wallet_score") or "0",
        "priority_bucket": row.get("score_band") or "unknown",
        "reason_codes": ";".join(reason_codes),
        "structural_strengths": "; ".join(_structural_strengths(row)) or "none",
        "structural_risks": "; ".join(_structural_risks(row)) or "none",
        "recommended_next_research_action": _next_research_action(row),
        "source_score_version": row.get("score_version") or "",
        "source_scores_sha256": source_scores_sha256,
        "watchlist_version": WATCHLIST_VERSION,
    }


def _passes_minimum_visibility(row: dict[str, str]) -> bool:
    return (
        _int(row.get("total_lifecycle_positions")) >= MINIMUM_VISIBLE_LIFECYCLES
        and _int(row.get("missing_required_metric_count")) == 0
        and (row.get("score_band") or "") in {
            "high_priority",
            "medium_priority",
            "low_priority",
            "insufficient_visible_structure",
        }
    )


def _reason_codes(row: dict[str, str]) -> list[str]:
    codes = [f"bucket_{row.get('score_band') or 'unknown'}", "minimum_visibility_passed"]
    if _decimal(row.get("fast_crypto_lifecycle_share")) >= Decimal("0.75"):
        codes.append("fast_crypto_relevant")
    elif _decimal(row.get("fast_crypto_lifecycle_share")) == 0:
        codes.append("no_fast_crypto_visibility")
    if _int(row.get("partial_exits")) > 0:
        codes.append("visible_partial_exit_activity")
    if _decimal(row.get("percentage_still_open_positions")) >= Decimal("0.90"):
        codes.append("all_or_mostly_open_visibility")
    if _decimal(row.get("bounded_history_penalty")) > 0 or _int(row.get("oversold_bounded_history")) > 0:
        codes.append("bounded_history_artifact_risk")
    if _decimal(row.get("concentration_penalty")) > 0:
        codes.append("concentration_risk")
    if _decimal(row.get("small_sample_penalty")) > 0:
        codes.append("small_visible_sample")
    if _decimal(row.get("near_flat_ambiguity_penalty")) > 0:
        codes.append("near_flat_residual_ambiguity")
    return codes


def _structural_strengths(row: dict[str, str]) -> list[str]:
    strengths: list[str] = []
    if _int(row.get("total_lifecycle_positions")) >= 25:
        strengths.append("strong visible lifecycle coverage")
    elif _int(row.get("total_lifecycle_positions")) >= MINIMUM_VISIBLE_LIFECYCLES:
        strengths.append("minimum visible lifecycle coverage")
    if _decimal(row.get("fast_crypto_lifecycle_share")) >= Decimal("0.75"):
        strengths.append("high fast-crypto lifecycle share")
    if _int(row.get("partial_exits")) > 0:
        strengths.append("visible partial-exit structure")
    if _decimal(row.get("event_density_component")) >= Decimal("8"):
        strengths.append("visible repeated event density")
    if _decimal(row.get("specialization_component")) >= Decimal("7"):
        strengths.append("interpretable market specialization")
    return strengths


def _structural_risks(row: dict[str, str]) -> list[str]:
    risks = ["bounded public history only"]
    if _decimal(row.get("percentage_still_open_positions")) >= Decimal("0.90"):
        risks.append("all or mostly open visible lifecycle state")
    if _decimal(row.get("fast_crypto_lifecycle_share")) == 0:
        risks.append("no visible fast-crypto lifecycle share")
    if _decimal(row.get("small_sample_penalty")) > 0:
        risks.append("small visible lifecycle sample")
    if _decimal(row.get("bounded_history_penalty")) > 0:
        risks.append("bounded-history artifact risk")
    if _decimal(row.get("concentration_penalty")) > 0:
        risks.append("high concentration limits generality")
    if _decimal(row.get("near_flat_ambiguity_penalty")) > 0:
        risks.append("near-flat residual ambiguity")
    if row.get("score_band") == "insufficient_visible_structure":
        risks.append("insufficient visible structure bucket")
    return risks


def _next_research_action(row: dict[str, str]) -> str:
    bucket = row.get("score_band") or ""
    if bucket == "high_priority":
        return "include in research watchlist and review bounded public history first"
    if bucket == "medium_priority":
        return "include in research watchlist and prepare deeper public-history review"
    if bucket == "low_priority":
        return "keep in research watchlist and revisit after deeper public-history evidence"
    return "retain as low-visibility control unless additional bounded public history is collected"


def _build_watchlist_report(summary: dict[str, Any], rows: list[dict[str, str]]) -> str:
    lines = [
        "# Wallet Watchlist v1",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "## Scope",
        "",
        "This is a monitoring/research artifact. It is not a trading signal, not a copy-trading recommendation, and not a profitability ranking. It is based only on bounded public history and existing Wallet Score outputs.",
        "",
        "## Source",
        "",
        f"- Source scores CSV: `{summary['source_scores_csv']}`",
        f"- Source scores SHA-256: `{summary['source_scores_sha256']}`",
        f"- Wallets input: {summary['wallets_input']}",
        f"- Wallets included: {summary['wallets_included']}",
        f"- Wallets excluded: {summary['wallets_excluded']}",
        "",
        "## Priority Bucket Counts",
        "",
    ]
    for bucket, count in summary["priority_bucket_counts"].items():
        lines.append(f"- `{bucket}`: {count}")
    lines.extend(["", "## Watchlist Rows", ""])
    for row in rows:
        lines.append(
            f"- `{row['wallet_id']}`: score={row['score']}, bucket={row['priority_bucket']}, reasons={row['reason_codes']}"
        )
        lines.append(f"  - strengths: {row['structural_strengths']}")
        lines.append(f"  - risks: {row['structural_risks']}")
        lines.append(f"  - next research action: {row['recommended_next_research_action']}")
    lines.extend(["", "## Validation", ""])
    for name, value in summary["validation"].items():
        lines.append(f"- `{name}`: {str(value).lower()}")
    lines.extend(
        [
            "",
            "## Explicit Non-Claims",
            "",
            "- No profitability claims.",
            "- No alpha claims.",
            "- No PnL, ROI, or Sharpe metrics.",
            "- No copy-trading recommendation.",
            "- No mark-to-market values.",
            "- No trading recommendation.",
            "",
            "## Recommended Next Task",
            "",
            f"`{summary['recommended_next_task']}`",
            "",
        ]
    )
    return "\n".join(lines)


def _bucket_order(bucket: str) -> int:
    return {
        "high_priority": 0,
        "medium_priority": 1,
        "low_priority": 2,
        "insufficient_visible_structure": 3,
    }.get(bucket, 9)


def _decimal(value: Any) -> Decimal:
    return decimal_or_none(value) or Decimal("0")


def _int(value: Any) -> int:
    try:
        return int(Decimal(str(value or "0")))
    except Exception:
        return 0
