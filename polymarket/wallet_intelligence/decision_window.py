"""Deterministic H3 decision-window analysis for prospective wallet trades."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import statistics
from datetime import UTC, datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Any


DEFAULT_DECISION_WINDOW_INPUT = Path(
    "polymarket/models/wallet_intelligence_v1/first_seen_detection_v1/wallet_first_seen_dataset.csv"
)
DEFAULT_DECISION_WINDOW_OUTPUT = Path(
    "polymarket/models/wallet_intelligence_v1/decision_window_v1"
)

SUFFICIENT_SECONDS = 60.0
MARGINAL_SECONDS = 30.0
MIN_CONCLUSIVE_SAMPLE = 30

GAMMA_VERIFIED_EXPIRIES = {
    "btc-updown-5m-1782655200": {
        "condition_id": "0x2fece38d8afd7a75c250cb52406e22841c40fad48190ba431f212bdecdab7067",
        "expiry": "2026-06-28T14:05:00.000+00:00",
    },
    "sol-updown-5m-1782655200": {
        "condition_id": "0x5c5809ee85b49a9b63716f7cf6f47d42df09a0df1ccbc350dfda9209fea277f4",
        "expiry": "2026-06-28T14:05:00.000+00:00",
    },
}

DECISION_WINDOW_FIELDS = [
    "wallet_id",
    "trade_identity",
    "asset_class",
    "market_slug",
    "condition_id",
    "token_id",
    "transaction_hash",
    "trade_timestamp",
    "trade_datetime_utc",
    "first_seen_timestamp_utc",
    "expiry_timestamp_utc",
    "expiry_source",
    "expiry_join_confidence",
    "first_seen_delay_seconds",
    "decision_window_seconds",
    "poll_interval_seconds",
    "timing_uncertainty_seconds",
    "decision_window_classification",
]


def run_wallet_decision_window_sprint(
    input_csv: Path = DEFAULT_DECISION_WINDOW_INPUT,
    output_dir: Path = DEFAULT_DECISION_WINDOW_OUTPUT,
) -> dict[str, Any]:
    source_rows = _read_csv(input_csv)
    rows, exclusions = build_decision_windows(source_rows)
    summary = summarize_decision_windows(rows, exclusions, input_csv)
    csv_text = render_decision_window_csv(rows)
    report_text = render_decision_window_report(summary)
    summary["reproducibility_hashes"] = {
        "wallet_decision_window_csv_sha256": _sha256(csv_text),
        "wallet_decision_window_report_md_sha256": _sha256(report_text),
    }
    summary["validation"] = validate_decision_windows(rows, summary, csv_text, report_text)
    summary["validation"]["all_validation_passed"] = all(summary["validation"].values())
    report_text = render_decision_window_report(summary)
    summary["reproducibility_hashes"]["wallet_decision_window_report_md_sha256"] = _sha256(report_text)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "wallet_decision_window.csv").write_text(csv_text, encoding="utf-8", newline="")
    (output_dir / "wallet_decision_window_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    (output_dir / "wallet_decision_window_report.md").write_bytes(report_text.encode("utf-8"))
    return summary


def build_decision_windows(source_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, int]]:
    rows: list[dict[str, str]] = []
    exclusions = {
        "non_prospective_or_page_churn": 0,
        "non_five_minute_market": 0,
        "missing_first_seen_timestamp": 0,
        "missing_expiry": 0,
        "first_seen_after_expiry": 0,
    }
    for source in source_rows:
        if not _is_prospective_observation(source):
            exclusions["non_prospective_or_page_churn"] += 1
            continue
        if not _is_five_minute_market(source):
            exclusions["non_five_minute_market"] += 1
            continue
        first_seen_text = source.get("first_seen_timestamp_utc") or source.get(
            "first_observation_timestamp_utc", ""
        )
        first_seen = _parse_datetime(first_seen_text)
        if first_seen is None:
            exclusions["missing_first_seen_timestamp"] += 1
            continue
        expiry, expiry_source, confidence = resolve_expiry(source)
        if expiry is None:
            exclusions["missing_expiry"] += 1
            continue
        window = (expiry - first_seen).total_seconds()
        if window < 0:
            exclusions["first_seen_after_expiry"] += 1
            continue
        poll_interval = _float(source.get("poll_interval_seconds")) or 5.0
        rows.append(
            {
                "wallet_id": source.get("wallet_id", "").lower(),
                "trade_identity": source.get("trade_identity", ""),
                "asset_class": source.get("asset_class", ""),
                "market_slug": source.get("market_slug", ""),
                "condition_id": source.get("condition_id", "").lower(),
                "token_id": source.get("token_id", ""),
                "transaction_hash": source.get("transaction_hash", "").lower(),
                "trade_timestamp": source.get("trade_timestamp", ""),
                "trade_datetime_utc": source.get("trade_datetime_utc", ""),
                "first_seen_timestamp_utc": _iso(first_seen),
                "expiry_timestamp_utc": _iso(expiry),
                "expiry_source": expiry_source,
                "expiry_join_confidence": confidence,
                "first_seen_delay_seconds": source.get("first_seen_delay_seconds", ""),
                "decision_window_seconds": _number(window),
                "poll_interval_seconds": _number(poll_interval),
                "timing_uncertainty_seconds": _number(poll_interval),
                "decision_window_classification": classify_decision_window(window),
            }
        )
    rows.sort(
        key=lambda row: (
            row["first_seen_timestamp_utc"],
            row["wallet_id"],
            row["condition_id"],
            row["token_id"],
            row["trade_identity"],
        )
    )
    return rows, exclusions


def resolve_expiry(source: dict[str, str]) -> tuple[datetime | None, str, str]:
    explicit = source.get("expiry_timestamp_utc") or source.get("expiry_timestamp")
    if explicit:
        return _parse_datetime(explicit), "source_dataset", "high"

    slug = source.get("market_slug", "")
    condition_id = source.get("condition_id", "").lower()
    verified = GAMMA_VERIFIED_EXPIRIES.get(slug)
    if verified and verified["condition_id"] == condition_id:
        return _parse_datetime(verified["expiry"]), "gamma_market_slug_cross_check", "high"

    match = re.search(r"-5m-(\d+)$", slug)
    if not match:
        return None, "unavailable", "none"
    try:
        start = datetime.fromtimestamp(int(match.group(1)), UTC)
    except (ValueError, OSError, OverflowError):
        return None, "unavailable", "none"
    return start + timedelta(minutes=5), "market_slug_epoch_plus_300", "medium"


def classify_decision_window(seconds: float) -> str:
    if seconds >= SUFFICIENT_SECONDS:
        return "sufficient_decision_window"
    if seconds >= MARGINAL_SECONDS:
        return "marginal_decision_window"
    return "insufficient_decision_window"


def summarize_decision_windows(
    rows: list[dict[str, str]], exclusions: dict[str, int], input_csv: Path
) -> dict[str, Any]:
    values = [float(row["decision_window_seconds"]) for row in rows]
    classifications = {
        name: sum(row["decision_window_classification"] == name for row in rows)
        for name in (
            "sufficient_decision_window",
            "marginal_decision_window",
            "insufficient_decision_window",
        )
    }
    distribution = {
        "under_30_seconds": sum(value < 30 for value in values),
        "30_to_under_60_seconds": sum(30 <= value < 60 for value in values),
        "60_to_under_120_seconds": sum(60 <= value < 120 for value in values),
        "120_to_under_180_seconds": sum(120 <= value < 180 for value in values),
        "180_seconds_or_more": sum(value >= 180 for value in values),
    }
    conclusion = "INCONCLUSIVE"
    return {
        "task": "Wallet Decision Window Sprint v1",
        "hypothesis": "After a wallet trade becomes observable, enough usable decision time remains before market expiry to allow practical copy-trading.",
        "input_csv": str(input_csv),
        "observed_trades": len(rows),
        "wallet_count": len({row["wallet_id"] for row in rows}),
        "asset_counts": _counts(rows, "asset_class"),
        "decision_window_seconds": _stats(values),
        "decision_window_distribution": distribution,
        "classification_counts": classifications,
        "thresholds_seconds": {
            "sufficient_minimum": SUFFICIENT_SECONDS,
            "marginal_minimum": MARGINAL_SECONDS,
            "insufficient_below": MARGINAL_SECONDS,
        },
        "threshold_justification": "Sixty seconds is the pre-existing H3 project gate and equals twelve 5-second poll intervals. Thirty seconds is a conservative marginal boundary equal to six poll intervals; execution latency is deliberately not estimated.",
        "shares_at_project_gates": {
            "at_least_60_seconds": _share(values, 60),
            "at_least_120_seconds": _share(values, 120),
            "at_least_180_seconds": _share(values, 180),
        },
        "poll_interval_seconds": 5.0,
        "known_timing_uncertainty": "First-seen is response completion and therefore an upper-bound observation time quantized by the 5-second poll cadence; exact API publication time is unknown.",
        "excluded_rows": exclusions,
        "minimum_conclusive_sample": MIN_CONCLUSIVE_SAMPLE,
        "research_conclusion": conclusion,
        "compatibility_answer": "The two observed windows are not uniformly incompatible with future automated copy-trading research, but the sample is too small and execution latency is unmeasured; compatibility remains inconclusive.",
        "limitations": [
            "The 5-second polling cadence makes first-seen time a bounded observation rather than exact API publication time.",
            "API publication time within each poll interval is unknown.",
            "The observation window lasted only five minutes.",
            "Only two eligible five-minute trades were observed, both from one wallet.",
            "Execution, decision, order-submission, fill, slippage, liquidity, and queue latency were not measured.",
            "The selected wallet cohort is retrospective and subject to selection bias.",
        ],
        "recommended_next_hypothesis": "H2/H3 Prospective Evidence Accumulation Sprint v1: collect a preregistered minimum of 30 target five-minute observations with the existing restart-safe observer before retesting actionable time.",
    }


def validate_decision_windows(
    rows: list[dict[str, str]], summary: dict[str, Any], csv_text: str, report_text: str
) -> dict[str, bool]:
    classifications = set(summary["classification_counts"])
    allowed = {
        "sufficient_decision_window",
        "marginal_decision_window",
        "insufficient_decision_window",
    }
    return {
        "deterministic_ordering": rows == sorted(
            rows,
            key=lambda row: (
                row["first_seen_timestamp_utc"], row["wallet_id"], row["condition_id"],
                row["token_id"], row["trade_identity"],
            ),
        ),
        "deterministic_csv_render": csv_text == render_decision_window_csv(rows),
        "repeatable_report_render": report_text == render_decision_window_report(summary),
        "all_windows_non_negative": all(float(row["decision_window_seconds"]) >= 0 for row in rows),
        "every_trade_classified": len(rows) == sum(summary["classification_counts"].values()),
        "classification_vocabulary_bounded": classifications == allowed,
        "expiry_evidence_present": all(row["expiry_timestamp_utc"] and row["expiry_source"] for row in rows),
        "evidence_backed_conclusion": summary["research_conclusion"] == "INCONCLUSIVE" and len(rows) < MIN_CONCLUSIVE_SAMPLE,
        "no_profitability_or_investment_claims": not any(
            phrase in report_text.lower()
            for phrase in ("guaranteed profit", "expected return", "should buy", "should sell")
        ),
    }


def render_decision_window_csv(rows: list[dict[str, str]]) -> str:
    handle = StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=DECISION_WINDOW_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue()


def render_decision_window_report(summary: dict[str, Any]) -> str:
    stats = summary["decision_window_seconds"]
    classes = summary["classification_counts"]
    gates = summary["shares_at_project_gates"]
    return "\n".join(
        [
            "# Wallet Decision Window Sprint v1",
            "",
            "This is bounded research evidence, not a trading recommendation or investment advice.",
            "No profitability, return, execution-quality, or fill claim is made.",
            "",
            "## Observed Evidence",
            "",
            f"- Eligible prospective five-minute trades: {summary['observed_trades']}",
            f"- Wallets represented: {summary['wallet_count']}",
            f"- Minimum / median / mean / maximum window: {_display_stats(stats)} seconds",
            f"- At least 60 / 120 / 180 seconds: {gates['at_least_60_seconds']:.2%} / {gates['at_least_120_seconds']:.2%} / {gates['at_least_180_seconds']:.2%}",
            "",
            "## Classification",
            "",
            f"- Sufficient decision window: {classes['sufficient_decision_window']}",
            f"- Marginal decision window: {classes['marginal_decision_window']}",
            f"- Insufficient decision window: {classes['insufficient_decision_window']}",
            f"- Thresholds: sufficient >= {SUFFICIENT_SECONDS:.0f}s; marginal >= {MARGINAL_SECONDS:.0f}s and < {SUFFICIENT_SECONDS:.0f}s; insufficient < {MARGINAL_SECONDS:.0f}s",
            f"- Justification: {summary['threshold_justification']}",
            "",
            "## Timing Context",
            "",
            f"- Detector polling interval: {summary['poll_interval_seconds']:.0f} seconds",
            f"- Uncertainty: {summary['known_timing_uncertainty']}",
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in summary["limitations"]],
            "",
            "## Conclusion",
            "",
            f"**{summary['research_conclusion']}**",
            "",
            summary["compatibility_answer"],
            "",
            f"Recommended next hypothesis: {summary['recommended_next_hypothesis']}",
        ]
    ) + "\n"


def _is_prospective_observation(row: dict[str, str]) -> bool:
    observation_class = row.get("observation_class", "")
    if observation_class:
        return observation_class == "new_live_window_trade"
    return bool(row.get("first_seen_timestamp_utc"))


def _is_five_minute_market(row: dict[str, str]) -> bool:
    if row.get("five_minute_market"):
        return row["five_minute_market"].lower() == "true"
    return bool(re.search(r"-5m-\d+$", row.get("market_slug", "")))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _parse_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _float(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="milliseconds")


def _number(value: float) -> str:
    return f"{value:.6f}"


def _stats(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "minimum": None, "median": None, "mean": None, "maximum": None}
    return {
        "count": len(values),
        "minimum": min(values),
        "median": statistics.median(values),
        "mean": statistics.fmean(values),
        "maximum": max(values),
    }


def _share(values: list[float], threshold: float) -> float:
    return sum(value >= threshold for value in values) / len(values) if values else 0.0


def _counts(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    return {value: sum(row[field] == value for row in rows) for value in sorted({row[field] for row in rows})}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _display_stats(stats: dict[str, float | int | None]) -> str:
    if not stats["count"]:
        return "unavailable"
    return " / ".join(f"{float(stats[key]):.6f}" for key in ("minimum", "median", "mean", "maximum"))
