"""Public market outcome joins for Wallet Intelligence research.

This module joins existing wallet lifecycle candidates to public Polymarket
market metadata. It is outcome-aware but not performance-aware: it does not
compute PnL, ROI, returns, wallet ranking, copyability, or trading signals.
"""

from __future__ import annotations

import csv
import json
import time
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .lifecycle import load_trade_history_csv
from .schema import MARKET_OUTCOME_JOIN_FIELDS, MarketOutcomeJoinRecord
from .trade_history import file_sha256


DEFAULT_MARKET_OUTCOME_INPUT = Path(
    "polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_broader_v1/lifecycle_positions.csv"
)
DEFAULT_MARKET_OUTCOME_OUTPUT = Path("polymarket/models/wallet_intelligence_v1/market_outcome_resolution_v1")

FORBIDDEN_REPORT_TERMS = [
    "profit",
    "profitability",
    "roi",
    "sharpe",
    "alpha",
    "return",
    "investment advice",
    "trading recommendation",
]


class PublicMarketMetadataClient:
    """Small public read-only client for Gamma and CLOB metadata."""

    gamma_base = "https://gamma-api.polymarket.com"
    clob_base = "https://clob.polymarket.com"

    def __init__(self, *, timeout_seconds: float = 20.0, delay_seconds: float = 0.02) -> None:
        self.timeout_seconds = timeout_seconds
        self.delay_seconds = delay_seconds

    def get_market_by_slug(self, slug: str) -> dict[str, Any] | None:
        return self._get_json(f"{self.gamma_base}/markets/slug/{urllib.parse.quote(slug)}")

    def get_event_by_slug(self, slug: str) -> dict[str, Any] | None:
        return self._get_json(f"{self.gamma_base}/events/slug/{urllib.parse.quote(slug)}")

    def get_events_query_by_slug(self, slug: str) -> dict[str, Any] | None:
        payload = self._get_json(f"{self.gamma_base}/events?{urllib.parse.urlencode({'slug': slug})}")
        if isinstance(payload, list) and payload:
            return payload[0]
        return None

    def get_market_by_token(self, token_id: str) -> dict[str, Any] | None:
        return self._get_json(f"{self.gamma_base}/markets/token/{urllib.parse.quote(token_id)}")

    def get_clob_market(self, condition_id: str) -> dict[str, Any] | None:
        return self._get_json(f"{self.clob_base}/clob-markets/{urllib.parse.quote(condition_id)}")

    def _get_json(self, url: str) -> Any:
        if self.delay_seconds:
            time.sleep(self.delay_seconds)
        request = urllib.request.Request(url, headers={"User-Agent": "ForgeViewAI-wallet-outcome-join/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            return None


def run_market_outcome_resolution_sprint(
    input_csv: Path = DEFAULT_MARKET_OUTCOME_INPUT,
    output_dir: Path = DEFAULT_MARKET_OUTCOME_OUTPUT,
    *,
    client: Any | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    client = client or PublicMarketMetadataClient()
    output_dir.mkdir(parents=True, exist_ok=True)

    lifecycle_rows = load_trade_history_csv(input_csv)
    metadata_by_key = fetch_market_metadata(lifecycle_rows, client)
    joined_rows = join_lifecycle_outcomes(lifecycle_rows, metadata_by_key)
    validation = validate_market_outcome_joins(joined_rows)
    summary = build_market_outcome_summary(lifecycle_rows, joined_rows, validation, generated_at, input_csv, output_dir)

    csv_path = output_dir / "market_outcome_join.csv"
    summary_path = output_dir / "market_outcome_join_summary.json"
    report_path = output_dir / "market_outcome_join_report.md"
    hashes_path = output_dir / "reproducibility_hashes.json"

    write_market_outcome_join(csv_path, joined_rows)
    first_hash = file_sha256(csv_path)
    write_market_outcome_join(csv_path, joined_rows)
    second_hash = file_sha256(csv_path)
    summary["validation"]["repeatable_export"] = first_hash == second_hash

    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report = render_market_outcome_report(summary)
    report_path.write_text(report, encoding="utf-8")
    hashes = {
        "market_outcome_join_csv_sha256": file_sha256(csv_path),
        "market_outcome_join_summary_json_sha256": file_sha256(summary_path),
        "market_outcome_join_report_md_sha256": file_sha256(report_path),
        "csv_repeat_export_hash_match": first_hash == second_hash,
    }
    hashes_path.write_text(json.dumps(hashes, indent=2, sort_keys=True), encoding="utf-8")
    summary["reproducibility_hashes"] = hashes
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def fetch_market_metadata(rows: list[dict[str, str]], client: Any) -> dict[str, dict[str, Any]]:
    market_keys = sorted({_metadata_key(row) for row in rows})
    exemplar_by_key = {_metadata_key(row): row for row in rows}
    metadata: dict[str, dict[str, Any]] = {}
    for key in market_keys:
        row = exemplar_by_key[key]
        metadata[key] = fetch_one_market_metadata(row, client)
    return metadata


def fetch_one_market_metadata(row: dict[str, str], client: Any) -> dict[str, Any]:
    condition_id = (row.get("condition_id") or "").lower()
    token_id = row.get("token_id") or ""
    market_slug = row.get("market_slug") or ""
    event_slug = row.get("event_slug") or market_slug
    sources: list[str] = []
    errors: list[str] = []
    market: dict[str, Any] | None = None
    event: dict[str, Any] | None = None
    clob: dict[str, Any] | None = None

    if market_slug:
        payload = client.get_market_by_slug(market_slug)
        if isinstance(payload, dict) and payload:
            market = payload
            sources.append("gamma_markets_slug")
        else:
            errors.append("gamma_markets_slug_missing")
    primary_condition_matches = bool(
        market
        and condition_id
        and str(market.get("conditionId") or market.get("condition_id") or "").lower() == condition_id
    )
    if event_slug and not primary_condition_matches:
        payload = client.get_event_by_slug(event_slug)
        if isinstance(payload, dict) and payload:
            event = payload
            sources.append("gamma_events_slug")
            market = _choose_market_from_event(event, condition_id) or market
        else:
            errors.append("gamma_events_slug_missing")
            payload = client.get_events_query_by_slug(event_slug)
            if isinstance(payload, dict) and payload:
                event = payload
                sources.append("gamma_events_query_slug")
                market = _choose_market_from_event(event, condition_id) or market
            else:
                errors.append("gamma_events_query_slug_missing")
    if market is None and token_id:
        payload = client.get_market_by_token(token_id)
        if isinstance(payload, dict) and payload:
            market = payload
            sources.append("gamma_markets_token")
        else:
            errors.append("gamma_markets_token_missing")
    needs_clob_cross_check = not primary_condition_matches or not market or token_id == ""
    if condition_id and needs_clob_cross_check:
        payload = client.get_clob_market(condition_id)
        if isinstance(payload, dict) and payload:
            clob = payload
            sources.append("clob_markets_condition")
        else:
            errors.append("clob_markets_condition_missing")

    return {
        "market": market,
        "event": event,
        "clob": clob,
        "metadata_sources": sources,
        "metadata_errors": errors,
    }


def join_lifecycle_outcomes(
    rows: list[dict[str, str]],
    metadata_by_key: dict[str, dict[str, Any]],
) -> list[MarketOutcomeJoinRecord]:
    joined: list[MarketOutcomeJoinRecord] = []
    for row in sorted(rows, key=_lifecycle_sort_key):
        key = _metadata_key(row)
        metadata = metadata_by_key.get(key, {})
        resolution = resolve_lifecycle_row(row, metadata)
        joined.append(_record(row, resolution))
    return joined


def resolve_lifecycle_row(row: dict[str, str], metadata: dict[str, Any]) -> dict[str, str]:
    market = metadata.get("market") if isinstance(metadata.get("market"), dict) else None
    event = metadata.get("event") if isinstance(metadata.get("event"), dict) else None
    clob = metadata.get("clob") if isinstance(metadata.get("clob"), dict) else None
    sources = metadata.get("metadata_sources") or []
    errors = metadata.get("metadata_errors") or []
    condition_id = (row.get("condition_id") or "").lower()
    token_id = row.get("token_id") or ""
    lifecycle_outcome = row.get("outcome") or ""

    if not market:
        return _resolution(
            row,
            market,
            event,
            "insufficient_evidence",
            "",
            "",
            "insufficient_evidence",
            "low",
            "failed",
            ";".join(errors) or "missing_market_metadata",
            ";".join(sources),
            "false",
            _clob_token_outcome_status(clob, token_id, lifecycle_outcome),
            "false",
        )

    market_condition = str(market.get("conditionId") or market.get("condition_id") or "").lower()
    condition_match = str(bool(market_condition and market_condition == condition_id)).lower()
    conflicting = bool(market_condition and condition_id and market_condition != condition_id)
    event_id = str((event or {}).get("id") or market.get("eventId") or "")
    resolved_status, winning_outcome, outcome_prices, reason = parse_winning_outcome(market)
    clob_status = _clob_token_outcome_status(clob, token_id, lifecycle_outcome)

    if conflicting:
        lifecycle_status = "insufficient_evidence"
        join_status = "conflicting_metadata"
        confidence = "low"
        join_reason = "condition_id_conflict"
    elif resolved_status == "resolved" and winning_outcome:
        lifecycle_status = (
            "matched_outcome"
            if _same_outcome(lifecycle_outcome, winning_outcome)
            else "unmatched_outcome"
        )
        join_status = "joined"
        confidence = "high" if condition_match == "true" and clob_status in {"matched", "unavailable"} else "medium"
        join_reason = "resolved_terminal_outcome"
    elif resolved_status == "unresolved":
        lifecycle_status = "unresolved_market"
        join_status = "joined"
        confidence = "medium" if condition_match == "true" else "low"
        join_reason = reason
    else:
        lifecycle_status = "insufficient_evidence"
        join_status = "ambiguous"
        confidence = "low"
        join_reason = reason

    return _resolution(
        row,
        market,
        event,
        resolved_status,
        winning_outcome,
        outcome_prices,
        lifecycle_status,
        confidence,
        join_status,
        join_reason,
        ";".join(sources),
        condition_match,
        clob_status,
        str(conflicting).lower(),
        event_id=event_id,
    )


def parse_winning_outcome(market: dict[str, Any]) -> tuple[str, str, str, str]:
    closed = bool(market.get("closed"))
    resolution_status = str(market.get("umaResolutionStatus") or "").lower()
    automatically_resolved = bool(market.get("automaticallyResolved"))
    if not closed:
        return "unresolved", "", "", "market_not_closed"
    if resolution_status not in {"resolved", ""} and not automatically_resolved:
        return "unresolved", "", "", f"resolution_status:{resolution_status}"
    try:
        outcomes = _parse_json_list(market.get("outcomes"))
        prices = [float(value) for value in _parse_json_list(market.get("outcomePrices"))]
    except (TypeError, ValueError, json.JSONDecodeError):
        return "insufficient_evidence", "", "", "invalid_outcome_prices"
    if len(outcomes) != len(prices) or not outcomes:
        return "insufficient_evidence", "", "", "outcome_price_length_mismatch"
    winners = [str(outcome) for outcome, price in zip(outcomes, prices) if abs(price - 1.0) <= 0.001]
    losers = [str(outcome) for outcome, price in zip(outcomes, prices) if abs(price - 0.0) <= 0.001]
    price_blob = json.dumps(dict(zip([str(o) for o in outcomes], prices)), sort_keys=True)
    if len(winners) == 1 and len(losers) == len(outcomes) - 1:
        return "resolved", winners[0], price_blob, "terminal_outcome_prices"
    return "insufficient_evidence", "", price_blob, "non_terminal_or_ambiguous_outcome_prices"


def validate_market_outcome_joins(rows: list[MarketOutcomeJoinRecord]) -> dict[str, Any]:
    ordered_keys = [row.lifecycle_group_key for row in rows]
    row_dicts = [asdict(row) for row in rows]
    forbidden_fields = [field for field in MARKET_OUTCOME_JOIN_FIELDS if _forbidden_field(field)]
    forbidden_claim_rows = [
        row.lifecycle_group_key
        for row in rows
        if any(term in " ".join(asdict(row).values()).lower() for term in FORBIDDEN_REPORT_TERMS)
    ]
    return {
        "deterministic_ordering": ordered_keys == sorted(ordered_keys),
        "all_rows_have_confidence_labels": all(row.join_confidence for row in rows),
        "all_rows_have_lifecycle_resolution_status": all(row.lifecycle_resolution_status for row in rows),
        "unresolved_handling_present": any(row.lifecycle_resolution_status == "unresolved_market" for row in rows),
        "no_forbidden_metric_fields": not forbidden_fields,
        "forbidden_metric_fields": forbidden_fields,
        "no_forbidden_claims": not forbidden_claim_rows,
        "forbidden_claim_rows": forbidden_claim_rows[:20],
        "output_schema_complete": all(set(record) == set(MARKET_OUTCOME_JOIN_FIELDS) for record in row_dicts),
    }


def build_market_outcome_summary(
    lifecycle_rows: list[dict[str, str]],
    joined_rows: list[MarketOutcomeJoinRecord],
    validation: dict[str, Any],
    generated_at: str,
    input_csv: Path,
    output_dir: Path,
) -> dict[str, Any]:
    status_counts = Counter(row.lifecycle_resolution_status for row in joined_rows)
    join_counts = Counter(row.join_status for row in joined_rows)
    confidence_counts = Counter(row.join_confidence for row in joined_rows)
    resolved_rows = status_counts["matched_outcome"] + status_counts["unmatched_outcome"]
    total = len(joined_rows)
    unique_conditions = len({row.condition_id for row in joined_rows})
    resolved_conditions = len(
        {
            row.condition_id
            for row in joined_rows
            if row.lifecycle_resolution_status in {"matched_outcome", "unmatched_outcome"}
        }
    )
    unresolved_conditions = len(
        {row.condition_id for row in joined_rows if row.lifecycle_resolution_status == "unresolved_market"}
    )
    blocker_counts = Counter(row.join_reason for row in joined_rows if row.lifecycle_resolution_status == "insufficient_evidence")
    biggest_blocker = blocker_counts.most_common(1)[0][0] if blocker_counts else "none"
    join_success = total - join_counts["failed"] - join_counts["conflicting_metadata"]
    automatic_outcome_rows = resolved_rows
    return {
        "task": "Wallet Market Outcome Resolution Sprint v1",
        "generated_at_utc": generated_at,
        "input_csv": str(input_csv),
        "output_dir": str(output_dir),
        "lifecycle_positions_evaluated": total,
        "unique_conditions_evaluated": unique_conditions,
        "unique_market_slugs_evaluated": len({row.market_slug for row in joined_rows}),
        "join_success_rows": join_success,
        "join_success_rate": round(join_success / total, 6) if total else 0,
        "automatic_resolved_outcome_rows": automatic_outcome_rows,
        "automatic_resolved_outcome_rate": round(automatic_outcome_rows / total, 6) if total else 0,
        "resolved_market_conditions": resolved_conditions,
        "unresolved_market_conditions": unresolved_conditions,
        "lifecycle_resolution_status_counts": dict(sorted(status_counts.items())),
        "join_status_counts": dict(sorted(join_counts.items())),
        "join_confidence_counts": dict(sorted(confidence_counts.items())),
        "ambiguous_joins": join_counts["ambiguous"],
        "failed_joins": join_counts["failed"],
        "conflicting_metadata_rows": join_counts["conflicting_metadata"],
        "missing_metadata_rows": sum(1 for row in joined_rows if row.join_reason.startswith("gamma_")),
        "biggest_blocker": biggest_blocker,
        "research_answers": {
            "can_link_reliably": join_success == total and automatic_outcome_rows > 0,
            "automatic_success_percentage": round(100 * join_success / total, 2) if total else 0,
            "remaining_join_blocker": biggest_blocker,
            "additional_metadata_needed": [
                "complete full-history wallet activity",
                "settlement or redemption provenance for ambiguous/non-terminal markets",
                "closed-position timestamp semantics",
                "future liquidity and delay evidence for copyability research",
            ],
            "outcome_aware_wallet_intelligence_feasible": automatic_outcome_rows > 0 and join_success / total >= 0.95 if total else False,
        },
        "validation": validation,
        "strict_exclusions": [
            "no PnL",
            "no ROI",
            "no realized profit",
            "no Sharpe",
            "no returns",
            "no alpha claims",
            "no copyability claims",
            "no trading recommendations",
            "no Wallet Score changes",
            "no Wallet Watchlist changes",
            "no wallet/private-key connection",
            "no order placement",
            "no holdout inspection",
            "no holdout evaluation",
        ],
        "recommended_next_task": "Wallet Outcome-Aware Metrics Sprint v1",
    }


def render_market_outcome_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Wallet Market Outcome Resolution Sprint v1",
        "",
        f"Status: Complete",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "This is a public read-only Wallet Intelligence research artifact. It is not a trading signal, not a copy-trading recommendation, and not a wallet ranking.",
        "",
        "## Evidence",
        "",
        f"- Lifecycle positions evaluated: {summary['lifecycle_positions_evaluated']}",
        f"- Unique conditions evaluated: {summary['unique_conditions_evaluated']}",
        f"- Join success rate: {summary['join_success_rate']:.2%}",
        f"- Automatic resolved outcome rate: {summary['automatic_resolved_outcome_rate']:.2%}",
        f"- Resolved market conditions: {summary['resolved_market_conditions']}",
        f"- Unresolved market conditions: {summary['unresolved_market_conditions']}",
        f"- Ambiguous joins: {summary['ambiguous_joins']}",
        f"- Failed joins: {summary['failed_joins']}",
        f"- Conflicting metadata rows: {summary['conflicting_metadata_rows']}",
        "",
        "## Lifecycle Resolution Status Counts",
        "",
    ]
    for key, value in summary["lifecycle_resolution_status_counts"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Join Confidence Counts", ""])
    for key, value in summary["join_confidence_counts"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Research Answers",
            "",
            f"1. Lifecycle positions can be linked to public market metadata reliably: {summary['research_answers']['can_link_reliably']}.",
            f"2. Automatic metadata join success is {summary['research_answers']['automatic_success_percentage']}%.",
            f"3. Biggest blocker: `{summary['biggest_blocker']}`.",
            "4. Remaining ambiguity needs complete wallet history, settlement/redemption provenance for ambiguous cases, and timestamp-semantics review.",
            f"5. Outcome-aware Wallet Intelligence is technically feasible: {summary['research_answers']['outcome_aware_wallet_intelligence_feasible']}.",
            "",
            "## Safety Boundary",
            "",
            "The sprint classifies only matched outcome, unmatched outcome, unresolved market, or insufficient evidence. It does not compute value, performance, or execution quality.",
            "",
            "## Recommended Next Sprint",
            "",
            f"`{summary['recommended_next_task']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_market_outcome_join(path: Path, rows: list[MarketOutcomeJoinRecord]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MARKET_OUTCOME_JOIN_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def _record(row: dict[str, str], resolution: dict[str, str]) -> MarketOutcomeJoinRecord:
    return MarketOutcomeJoinRecord(
        wallet_id=(row.get("wallet_id") or "").lower(),
        profile_url=row.get("profile_url") or "",
        condition_id=(row.get("condition_id") or "").lower(),
        token_id=row.get("token_id") or "",
        outcome=row.get("outcome") or "",
        lifecycle_group_key=row.get("lifecycle_group_key") or "",
        market_slug=row.get("market_slug") or "",
        event_slug=row.get("event_slug") or "",
        market_title=row.get("market_title") or "",
        market_type=row.get("market_type") or "",
        asset_class=row.get("asset_class") or "",
        up_down_market=row.get("up_down_market") or "",
        first_activity_timestamp=row.get("first_activity_timestamp") or "",
        first_activity_datetime_utc=row.get("first_activity_datetime_utc") or "",
        last_activity_timestamp=row.get("last_activity_timestamp") or "",
        last_activity_datetime_utc=row.get("last_activity_datetime_utc") or "",
        lifecycle_status=row.get("status") or "",
        **resolution,
    )


def _resolution(
    row: dict[str, str],
    market: dict[str, Any] | None,
    event: dict[str, Any] | None,
    resolved_status: str,
    winning_outcome: str,
    outcome_prices: str,
    lifecycle_resolution_status: str,
    join_confidence: str,
    join_status: str,
    join_reason: str,
    metadata_sources: str,
    condition_id_match: str,
    token_outcome_cross_check: str,
    conflicting_metadata: str,
    *,
    event_id: str = "",
) -> dict[str, str]:
    market = market or {}
    event = event or {}
    return {
        "market_id": str(market.get("id") or ""),
        "event_id": event_id or str(event.get("id") or ""),
        "expiry_timestamp": str(market.get("endDate") or event.get("endDate") or ""),
        "resolution_timestamp": str(market.get("closedTime") or event.get("closedTime") or ""),
        "resolved_status": resolved_status,
        "winning_outcome": winning_outcome,
        "outcome_prices": outcome_prices,
        "lifecycle_resolution_status": lifecycle_resolution_status,
        "join_confidence": join_confidence,
        "join_status": join_status,
        "join_reason": join_reason,
        "metadata_sources": metadata_sources,
        "condition_id_match": condition_id_match,
        "token_outcome_cross_check": token_outcome_cross_check,
        "conflicting_metadata": conflicting_metadata,
    }


def _choose_market_from_event(event: dict[str, Any], condition_id: str) -> dict[str, Any] | None:
    markets = event.get("markets")
    if not isinstance(markets, list):
        return None
    matches = [market for market in markets if str(market.get("conditionId") or "").lower() == condition_id]
    return matches[0] if len(matches) == 1 and isinstance(matches[0], dict) else None


def _clob_token_outcome_status(clob: dict[str, Any] | None, token_id: str, outcome: str) -> str:
    if not clob:
        return "unavailable"
    tokens = clob.get("t") or clob.get("tokens")
    if not isinstance(tokens, list):
        return "unavailable"
    for token in tokens:
        if not isinstance(token, dict):
            continue
        clob_token = str(token.get("t") or token.get("token_id") or "")
        clob_outcome = str(token.get("o") or token.get("outcome") or "")
        if clob_token == token_id:
            return "matched" if _same_outcome(clob_outcome, outcome) else "conflict"
    return "token_missing"


def _same_outcome(left: str, right: str) -> bool:
    return left.strip().lower() == right.strip().lower()


def _parse_json_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return json.loads(value)
    raise TypeError("not a list")


def _lifecycle_sort_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row.get("lifecycle_group_key") or "",
        (row.get("wallet_id") or "").lower(),
        (row.get("condition_id") or "").lower(),
        row.get("token_id") or "",
    )


def _metadata_key(row: dict[str, str]) -> str:
    return "|".join(
        [
            (row.get("condition_id") or "").lower(),
            row.get("market_slug") or "",
            row.get("event_slug") or "",
        ]
    )


def _forbidden_field(field: str) -> bool:
    lowered = field.lower()
    return any(term in lowered for term in ("pnl", "roi", "profit", "sharpe", "alpha", "return"))
