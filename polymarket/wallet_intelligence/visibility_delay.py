"""H2 public wallet activity visibility-delay analysis.

The existing trade-history batch is retrospective. It records trade time and
fetch time, but not when each row first became publicly observable. This
module preserves that distinction while producing deterministic evidence for
the H2 research decision.
"""

from __future__ import annotations

import csv
import json
import statistics
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .trade_history import file_sha256


DEFAULT_VISIBILITY_SKILL_INPUT = Path(
    "polymarket/models/wallet_intelligence_v1/outcome_skill_baseline_v1/wallet_skill_baseline.csv"
)
DEFAULT_VISIBILITY_TRADE_INPUT = Path(
    "polymarket/data/wallet_intelligence/trade_history_broader_v1/trade_history_normalized.csv"
)
DEFAULT_VISIBILITY_OUTPUT = Path(
    "polymarket/models/wallet_intelligence_v1/activity_visibility_delay_v1"
)

VISIBILITY_VERSION = "wallet_activity_visibility_delay_v1"
GROUP_BY_CLASSIFICATION = {
    "above_baseline_evidence": ("A", "above_baseline"),
    "sample_size_consistent_with_baseline": ("B", "baseline"),
    "below_baseline_evidence": ("C", "below_baseline"),
}
GROUP_ORDER = {"A": 0, "B": 1, "C": 2}
PUBLICATION_FIELDS = (
    "publication_timestamp",
    "published_timestamp",
    "published_at",
    "first_seen_timestamp",
    "first_seen_at",
)

VISIBILITY_FIELDS = [
    "wallet_group",
    "wallet_group_label",
    "wallet_id",
    "profile_url",
    "evidence_classification",
    "wallet_event_sequence",
    "activity_type",
    "trade_timestamp",
    "trade_datetime_utc",
    "publication_timestamp",
    "publication_datetime_utc",
    "publication_timestamp_source",
    "source_fetch_timestamp",
    "source_fetch_datetime_utc",
    "measurable_publication_delay_seconds",
    "retrospective_retrieval_lag_seconds",
    "delay_measurement_status",
    "timestamp_completeness",
    "event_ordering_key",
    "transaction_hash",
    "condition_id",
    "token_id",
    "market_slug",
    "event_slug",
    "asset_class",
    "outcome",
    "side",
    "price",
    "size",
    "source_endpoint_name",
    "source_endpoint",
    "dedupe_key",
]


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def run_wallet_visibility_delay_sprint(
    skill_csv: Path = DEFAULT_VISIBILITY_SKILL_INPUT,
    trade_csv: Path = DEFAULT_VISIBILITY_TRADE_INPUT,
    output_dir: Path = DEFAULT_VISIBILITY_OUTPUT,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    skill_rows = load_csv(skill_csv)
    trade_rows = load_csv(trade_csv)
    rows, summary = build_wallet_visibility_delay(
        skill_rows,
        trade_rows,
        generated_at=generated_at,
        skill_csv=skill_csv,
        trade_csv=trade_csv,
        output_dir=output_dir,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "wallet_visibility_delay.csv"
    summary_path = output_dir / "wallet_visibility_delay_summary.json"
    report_path = output_dir / "wallet_visibility_delay_report.md"

    write_visibility_csv(csv_path, rows)
    first_hash = file_sha256(csv_path)
    write_visibility_csv(csv_path, rows)
    second_hash = file_sha256(csv_path)
    summary["validation"]["repeatable_export"] = first_hash == second_hash
    summary["validation"]["all_validation_passed"] = all(
        value for value in summary["validation"].values() if isinstance(value, bool)
    )
    report_path.write_text(render_visibility_report(summary), encoding="utf-8")
    summary["reproducibility_hashes"] = {
        "wallet_visibility_delay_csv_sha256": file_sha256(csv_path),
        "wallet_visibility_delay_report_md_sha256": file_sha256(report_path),
        "csv_repeat_export_hash_match": first_hash == second_hash,
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def build_wallet_visibility_delay(
    skill_rows: list[dict[str, str]],
    trade_rows: list[dict[str, str]],
    *,
    generated_at: str | None = None,
    skill_csv: Path | None = None,
    trade_csv: Path | None = None,
    output_dir: Path | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    wallet_metadata: dict[str, dict[str, str]] = {}
    for row in skill_rows:
        classification = row.get("evidence_classification") or ""
        if classification not in GROUP_BY_CLASSIFICATION:
            continue
        wallet_id = (row.get("wallet_id") or "").lower()
        group, label = GROUP_BY_CLASSIFICATION[classification]
        wallet_metadata[wallet_id] = {
            "wallet_group": group,
            "wallet_group_label": label,
            "evidence_classification": classification,
            "profile_url": row.get("profile_url") or "",
        }

    candidates: list[tuple[dict[str, str], dict[str, str]]] = []
    for source in trade_rows:
        wallet_id = (source.get("wallet_id") or "").lower()
        if wallet_id not in wallet_metadata or not _is_fast_crypto_trade(source):
            continue
        candidates.append((source, wallet_metadata[wallet_id]))

    candidates.sort(
        key=lambda item: (
            GROUP_ORDER[item[1]["wallet_group"]],
            (item[0].get("wallet_id") or "").lower(),
            _timestamp_sort_value(item[0].get("activity_timestamp") or item[0].get("activity_datetime_utc")),
            item[0].get("transaction_hash") or "",
            item[0].get("dedupe_key") or "",
        )
    )

    sequence_by_wallet: Counter[str] = Counter()
    rows: list[dict[str, str]] = []
    for source, metadata in candidates:
        wallet_id = (source.get("wallet_id") or "").lower()
        sequence_by_wallet[wallet_id] += 1
        trade_dt = _parse_timestamp(source.get("activity_timestamp") or source.get("activity_datetime_utc"))
        fetch_dt = _parse_timestamp(source.get("source_fetch_timestamp"))
        publication_value, publication_source = _publication_timestamp(source)
        publication_dt = _parse_timestamp(publication_value)
        measured_delay = None
        delay_status = "unknown_missing_publication_timestamp"
        if publication_dt and trade_dt:
            candidate_delay = (publication_dt - trade_dt).total_seconds()
            if candidate_delay >= 0:
                measured_delay = candidate_delay
                delay_status = "measured_trade_to_publication"
            else:
                delay_status = "invalid_publication_precedes_trade"
        retrieval_lag = (fetch_dt - trade_dt).total_seconds() if fetch_dt and trade_dt else None
        completeness = sum(value is not None for value in (trade_dt, publication_dt, fetch_dt))
        ordering_key = "|".join(
            [
                _iso(trade_dt),
                source.get("transaction_hash") or "",
                source.get("dedupe_key") or "",
            ]
        )
        rows.append(
            {
                "wallet_group": metadata["wallet_group"],
                "wallet_group_label": metadata["wallet_group_label"],
                "wallet_id": wallet_id,
                "profile_url": source.get("profile_url") or metadata["profile_url"],
                "evidence_classification": metadata["evidence_classification"],
                "wallet_event_sequence": str(sequence_by_wallet[wallet_id]),
                "activity_type": source.get("activity_type") or "",
                "trade_timestamp": source.get("activity_timestamp") or "",
                "trade_datetime_utc": _iso(trade_dt),
                "publication_timestamp": publication_value,
                "publication_datetime_utc": _iso(publication_dt),
                "publication_timestamp_source": publication_source,
                "source_fetch_timestamp": source.get("source_fetch_timestamp") or "",
                "source_fetch_datetime_utc": _iso(fetch_dt),
                "measurable_publication_delay_seconds": _seconds(measured_delay),
                "retrospective_retrieval_lag_seconds": _seconds(retrieval_lag),
                "delay_measurement_status": delay_status,
                "timestamp_completeness": f"{completeness}_of_3",
                "event_ordering_key": ordering_key,
                "transaction_hash": source.get("transaction_hash") or "",
                "condition_id": source.get("condition_id") or "",
                "token_id": source.get("token_id") or source.get("asset_id") or "",
                "market_slug": source.get("market_slug") or "",
                "event_slug": source.get("event_slug") or "",
                "asset_class": source.get("asset_class") or "",
                "outcome": source.get("outcome") or "",
                "side": source.get("side") or "",
                "price": source.get("price") or "",
                "size": source.get("size") or "",
                "source_endpoint_name": source.get("source_endpoint_name") or "",
                "source_endpoint": source.get("source_endpoint") or "",
                "dedupe_key": source.get("dedupe_key") or "",
            }
        )

    generated_at = generated_at or _derived_generated_at(rows)
    group_summary = {
        group: _group_summary(rows, group, wallet_metadata)
        for group in ("A", "B", "C")
    }
    measured_delays = _numeric_values(rows, "measurable_publication_delay_seconds")
    retrieval_lags = _numeric_values(rows, "retrospective_retrieval_lag_seconds")
    unknown_timing_count = sum(row["delay_measurement_status"] != "measured_trade_to_publication" for row in rows)
    validation = validate_wallet_visibility_delay(rows, wallet_metadata)
    summary: dict[str, Any] = {
        "task": "Wallet Activity Visibility Delay Sprint v1",
        "visibility_version": VISIBILITY_VERSION,
        "hypothesis": "H2: Wallet activity becomes publicly observable early enough to support future copy-trading research.",
        "generated_at_utc": generated_at,
        "input_skill_csv": str(skill_csv or ""),
        "input_trade_csv": str(trade_csv or ""),
        "output_dir": str(output_dir or ""),
        "wallet_count": len({row["wallet_id"] for row in rows}),
        "trades_analyzed": len(rows),
        "wallet_groups": group_summary,
        "timing_field_discovery": {
            "trade_time": "available as activity_timestamp/activity_datetime_utc with second precision",
            "publication_time": "unavailable in the retrospective Data API activity export",
            "source_fetch_time": "available, but records bounded batch retrieval rather than first public visibility",
            "event_ordering": "deterministic within wallet using trade time, transaction hash, and dedupe key",
        },
        "timestamp_completeness": {
            "trade_time_count": sum(bool(row["trade_datetime_utc"]) for row in rows),
            "publication_time_count": sum(bool(row["publication_datetime_utc"]) for row in rows),
            "source_fetch_time_count": sum(bool(row["source_fetch_datetime_utc"]) for row in rows),
            "unknown_timing_count": unknown_timing_count,
        },
        "measured_publication_delay_seconds": _stats(measured_delays),
        "retrospective_retrieval_lag_seconds": _stats(retrieval_lags),
        "visibility_comparison": {
            "result": "not_measurable",
            "reason": "No trade has a publication or first-seen timestamp; group retrieval-age differences reflect retrospective batch composition, not API visibility speed.",
        },
        "evidence_supporting_h2": [
            "No direct evidence supports H2 because publication or first-seen timestamps are absent.",
            f"Trade occurrence, fetch timestamps, transaction hashes, and event ordering are complete for {len(rows)} rows, but they support only a future prospective test.",
        ],
        "evidence_against_h2": [
            f"Publication or first-seen time is absent for {unknown_timing_count} of {len(rows)} trades.",
            "The Data API activity timestamp represents the trade event, not when the API published the row.",
            "Source fetch timestamps came from retrospective bounded pages and cannot measure API latency.",
            "The cohort is selected retrospectively from H1 and remains exposed to selection and bounded-history bias.",
        ],
        "final_conclusion": "INCONCLUSIVE",
        "final_conclusion_reason": "H2 cannot be supported or rejected from retrospective activity exports because no per-trade publication or first-seen timestamp exists. The observed timestamps establish event order and retrieval age only.",
        "biggest_blocker": "Missing prospective first-seen timestamp for each public wallet trade.",
        "recommended_h3": "Wallet Detection-To-Expiry Feasibility Sprint v1, using prospectively recorded first-seen times before interpreting remaining actionable time.",
        "validation": validation,
    }
    return rows, summary


def validate_wallet_visibility_delay(
    rows: list[dict[str, str]], wallet_metadata: dict[str, dict[str, str]]
) -> dict[str, Any]:
    expected_wallets = set(wallet_metadata)
    row_wallets = {row["wallet_id"] for row in rows}
    sort_keys = [
        (
            GROUP_ORDER[row["wallet_group"]],
            row["wallet_id"],
            row["event_ordering_key"],
        )
        for row in rows
    ]
    measured = [row for row in rows if row["delay_measurement_status"] == "measured_trade_to_publication"]
    return {
        "all_selected_wallets_have_trades": expected_wallets == row_wallets,
        "all_rows_are_fast_crypto": all(
            row["asset_class"] in {"BTC", "ETH", "SOL"} for row in rows
        ),
        "all_rows_have_group_classification": all(row["wallet_group"] in GROUP_ORDER for row in rows),
        "trade_timestamp_parse_complete": all(bool(row["trade_datetime_utc"]) for row in rows),
        "source_fetch_timestamp_parse_complete": all(bool(row["source_fetch_datetime_utc"]) for row in rows),
        "measured_delays_non_negative": all(
            float(row["measurable_publication_delay_seconds"]) >= 0 for row in measured
        ),
        "unknown_delay_rows_explicit": all(
            row["measurable_publication_delay_seconds"]
            or row["delay_measurement_status"].startswith(("unknown_", "invalid_"))
            for row in rows
        ),
        "deterministic_ordering": sort_keys == sorted(sort_keys),
        "output_schema_complete": all(list(row) == VISIBILITY_FIELDS for row in rows),
        "event_sequences_consecutive": _event_sequences_consecutive(rows),
        "no_publication_fetch_substitution": all(
            not row["publication_timestamp"] or row["publication_timestamp_source"] != "source_fetch_timestamp"
            for row in rows
        ),
        "evidence_groups_present": {row["wallet_group"] for row in rows} == {"A", "B", "C"},
    }


def write_visibility_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=VISIBILITY_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def render_visibility_report(summary: dict[str, Any]) -> str:
    delay = summary["measured_publication_delay_seconds"]
    retrieval = summary["retrospective_retrieval_lag_seconds"]
    lines = [
        "# Wallet Activity Visibility Delay Sprint v1",
        "",
        "Hypothesis: H2 - Wallet activity becomes publicly observable early enough to support future copy-trading research.",
        "",
        "This is a retrospective public-data timing study, not a trading signal or a copy-trading recommendation.",
        "",
        "## Observed Evidence",
        "",
        f"- Wallets analyzed: {summary['wallet_count']}",
        f"- Fast-crypto trades analyzed: {summary['trades_analyzed']}",
        f"- Trade timestamps available: {summary['timestamp_completeness']['trade_time_count']}",
        f"- Publication/first-seen timestamps available: {summary['timestamp_completeness']['publication_time_count']}",
        f"- Fetch timestamps available: {summary['timestamp_completeness']['source_fetch_time_count']}",
        f"- Unknown publication timing: {summary['timestamp_completeness']['unknown_timing_count']}",
        "",
        "## Wallet Groups",
        "",
    ]
    for group in ("A", "B", "C"):
        item = summary["wallet_groups"][group]
        lines.append(
            f"- Group {group} `{item['label']}`: {item['wallet_count']} wallets, "
            f"{item['trades_analyzed']} trades, {item['unknown_timing_count']} unknown publication delays"
        )
    lines.extend(
        [
            "",
            "## Delay Measurement",
            "",
            f"- Minimum publication delay: {_display(delay['minimum'])}",
            f"- Median publication delay: {_display(delay['median'])}",
            f"- Mean publication delay: {_display(delay['mean'])}",
            f"- Maximum publication delay: {_display(delay['maximum'])}",
            "- Publication delay is unavailable because the source contains no publication or first-seen timestamp.",
            "- Retrospective retrieval lag is reported separately and must not be interpreted as API latency.",
            f"- Retrieval-lag minimum / median / mean / maximum: {_display(retrieval['minimum'])} / {_display(retrieval['median'])} / {_display(retrieval['mean'])} / {_display(retrieval['maximum'])}",
            "",
            "## Visibility Comparison",
            "",
            summary["visibility_comparison"]["result"],
            "",
            summary["visibility_comparison"]["reason"],
            "",
            "## Evidence Supporting H2",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in summary["evidence_supporting_h2"])
    lines.extend(["", "## Evidence Against H2", ""])
    lines.extend(f"- {item}" for item in summary["evidence_against_h2"])
    lines.extend(
        [
            "",
            "## Final Conclusion",
            "",
            summary["final_conclusion"],
            "",
            summary["final_conclusion_reason"],
            "",
            "## Biggest Blocker",
            "",
            summary["biggest_blocker"],
            "",
            "## Recommended H3",
            "",
            summary["recommended_h3"],
        ]
    )
    return "\n".join(lines) + "\n"


def _is_fast_crypto_trade(row: dict[str, str]) -> bool:
    return (
        row.get("asset_class") in {"BTC", "ETH", "SOL"}
        and (row.get("up_down_market") or "").lower() == "true"
        and row.get("market_type") == "fast_crypto_up_down"
        and row.get("activity_type") == "TRADE"
    )


def _publication_timestamp(row: dict[str, str]) -> tuple[str, str]:
    for field in PUBLICATION_FIELDS:
        if row.get(field):
            return row[field], field
    return "", "unavailable"


def _parse_timestamp(value: str | None) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        numeric = float(value)
    except ValueError:
        numeric = None
    if numeric is not None:
        if numeric > 10_000_000_000:
            numeric /= 1000
        try:
            return datetime.fromtimestamp(numeric, tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _timestamp_sort_value(value: str | None) -> float:
    parsed = _parse_timestamp(value)
    return parsed.timestamp() if parsed else float("inf")


def _iso(value: datetime | None) -> str:
    return value.replace(microsecond=0).isoformat() if value else ""


def _seconds(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6f}"


def _numeric_values(rows: list[dict[str, str]], field: str) -> list[float]:
    return [float(row[field]) for row in rows if row.get(field)]


def _stats(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "minimum": None, "median": None, "mean": None, "maximum": None}
    return {
        "count": len(values),
        "minimum": round(min(values), 6),
        "median": round(statistics.median(values), 6),
        "mean": round(statistics.fmean(values), 6),
        "maximum": round(max(values), 6),
    }


def _group_summary(
    rows: list[dict[str, str]], group: str, wallet_metadata: dict[str, dict[str, str]]
) -> dict[str, Any]:
    group_rows = [row for row in rows if row["wallet_group"] == group]
    wallets = sorted(wallet for wallet, metadata in wallet_metadata.items() if metadata["wallet_group"] == group)
    measured = _numeric_values(group_rows, "measurable_publication_delay_seconds")
    retrieval = _numeric_values(group_rows, "retrospective_retrieval_lag_seconds")
    return {
        "label": next((metadata["wallet_group_label"] for metadata in wallet_metadata.values() if metadata["wallet_group"] == group), ""),
        "wallet_count": len(wallets),
        "wallet_ids": wallets,
        "trades_analyzed": len(group_rows),
        "trade_timestamp_count": sum(bool(row["trade_datetime_utc"]) for row in group_rows),
        "publication_timestamp_count": sum(bool(row["publication_datetime_utc"]) for row in group_rows),
        "source_fetch_timestamp_count": sum(bool(row["source_fetch_datetime_utc"]) for row in group_rows),
        "unknown_timing_count": sum(row["delay_measurement_status"] != "measured_trade_to_publication" for row in group_rows),
        "measured_publication_delay_seconds": _stats(measured),
        "retrospective_retrieval_lag_seconds": _stats(retrieval),
    }


def _event_sequences_consecutive(rows: list[dict[str, str]]) -> bool:
    sequences: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        sequences[row["wallet_id"]].append(int(row["wallet_event_sequence"]))
    return all(values == list(range(1, len(values) + 1)) for values in sequences.values())


def _derived_generated_at(rows: list[dict[str, str]]) -> str:
    values = [row["source_fetch_datetime_utc"] for row in rows if row["source_fetch_datetime_utc"]]
    return max(values) if values else ""


def _display(value: Any) -> str:
    return "unavailable" if value is None else str(value)
