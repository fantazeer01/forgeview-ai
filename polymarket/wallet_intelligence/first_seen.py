"""Bounded prospective first-seen observation for public wallet trades."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import statistics
import time
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from .client import PolymarketPublicClient
from .trade_history import canonical_json, classify_trade_market, normalize_decimal, raw_payload_hash


STRONGEST_H1_WALLETS = (
    "0x088df3b7e5c1b5c2d4b7dc760863153480cf025e",
    "0x1cc53dd33c49d0a222c61ebfd2f24ba48802b199",
    "0x29a55c2bf8efd1029c001477b34be47d3ca37752",
    "0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a",
)
DEFAULT_FIRST_SEEN_OUTPUT = Path(
    "polymarket/models/wallet_intelligence_v1/first_seen_detection_v1"
)
DEFAULT_DURATION_SECONDS = 300.0
DEFAULT_POLL_INTERVAL_SECONDS = 5.0
DEFAULT_PAGE_LIMIT = 100
DEFAULT_MAX_REQUESTS = 240
DATA_API_RATE_LIMIT_REQUESTS = 1000
DATA_API_RATE_LIMIT_WINDOW_SECONDS = 10
RATE_LIMIT_DOC_URL = "https://docs.polymarket.com/api-reference/rate-limits"
API_INTRO_DOC_URL = "https://docs.polymarket.com/api-reference/introduction"

FIRST_SEEN_FIELDS = [
    "wallet_id",
    "profile_url",
    "poll_cycle",
    "poll_started_at_utc",
    "request_started_at_utc",
    "response_received_at_utc",
    "first_observation_timestamp_utc",
    "trade_timestamp",
    "trade_datetime_utc",
    "first_seen_delay_seconds",
    "delay_measurement_status",
    "observation_class",
    "poll_interval_seconds",
    "response_latency_ms",
    "transaction_hash",
    "transaction_hash_available",
    "market_slug",
    "event_slug",
    "market_title",
    "condition_id",
    "token_id",
    "outcome",
    "side",
    "price",
    "size",
    "market_type",
    "asset_class",
    "up_down_market",
    "five_minute_market",
    "source_endpoint",
    "trade_identity",
    "raw_payload_hash",
]


def run_first_seen_experiment(
    *,
    client: PolymarketPublicClient,
    output_dir: Path = DEFAULT_FIRST_SEEN_OUTPUT,
    wallets: tuple[str, ...] = STRONGEST_H1_WALLETS,
    duration_seconds: float = DEFAULT_DURATION_SECONDS,
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
    page_limit: int = DEFAULT_PAGE_LIMIT,
    max_requests: int = DEFAULT_MAX_REQUESTS,
    now: Callable[[], datetime] | None = None,
    monotonic: Callable[[], float] | None = None,
    sleeper: Callable[[float], None] | None = None,
) -> dict[str, Any]:
    _validate_limits(wallets, duration_seconds, poll_interval_seconds, page_limit, max_requests)
    now = now or (lambda: datetime.now(UTC))
    monotonic = monotonic or time.monotonic
    sleeper = sleeper or time.sleep
    experiment_started = now()
    started_monotonic = monotonic()
    deadline = started_monotonic + duration_seconds
    snapshots: list[dict[str, Any]] = []
    cycle = 0
    requests = 0

    while monotonic() < deadline and requests < max_requests:
        cycle += 1
        poll_started = now()
        for wallet_id in wallets:
            if requests >= max_requests or monotonic() >= deadline:
                break
            request_started = now()
            response_received: datetime
            try:
                response = client.activity_trades(wallet_id, limit=page_limit, offset=0)
                response_received = now()
                payload = response.payload if isinstance(response.payload, list) else []
                snapshots.append(
                    {
                        "poll_cycle": cycle,
                        "poll_started_at_utc": _iso(poll_started),
                        "wallet_id": wallet_id,
                        "request_started_at_utc": _iso(request_started),
                        "response_received_at_utc": _iso(response_received),
                        "status_code": response.status_code,
                        "source_endpoint": response.url,
                        "rows": [row for row in payload if isinstance(row, dict)],
                        "error": "",
                    }
                )
            except Exception as exc:  # public-network failures are evidence
                response_received = now()
                snapshots.append(
                    {
                        "poll_cycle": cycle,
                        "poll_started_at_utc": _iso(poll_started),
                        "wallet_id": wallet_id,
                        "request_started_at_utc": _iso(request_started),
                        "response_received_at_utc": _iso(response_received),
                        "status_code": 0,
                        "source_endpoint": "https://data-api.polymarket.com/activity",
                        "rows": [],
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
            requests += 1
        target = started_monotonic + cycle * poll_interval_seconds
        remaining = min(target, deadline) - monotonic()
        if remaining > 0:
            sleeper(remaining)

    experiment_completed = now()
    return run_first_seen_from_snapshots(
        snapshots,
        output_dir=output_dir,
        wallets=wallets,
        experiment_started_at=_iso(experiment_started),
        experiment_completed_at=_iso(experiment_completed),
        configured_duration_seconds=duration_seconds,
        poll_interval_seconds=poll_interval_seconds,
        page_limit=page_limit,
        max_requests=max_requests,
    )


def run_first_seen_from_snapshots(
    snapshots: list[dict[str, Any]],
    *,
    output_dir: Path,
    wallets: tuple[str, ...] = STRONGEST_H1_WALLETS,
    experiment_started_at: str,
    experiment_completed_at: str,
    configured_duration_seconds: float,
    poll_interval_seconds: float,
    page_limit: int,
    max_requests: int,
) -> dict[str, Any]:
    rows, summary = analyze_first_seen_snapshots(
        snapshots,
        wallets=wallets,
        experiment_started_at=experiment_started_at,
        experiment_completed_at=experiment_completed_at,
        configured_duration_seconds=configured_duration_seconds,
        poll_interval_seconds=poll_interval_seconds,
        page_limit=page_limit,
        max_requests=max_requests,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "wallet_first_seen_dataset.csv"
    summary_path = output_dir / "wallet_first_seen_summary.json"
    report_path = output_dir / "wallet_first_seen_report.md"

    csv_text = render_first_seen_csv(rows)
    report_text = render_first_seen_report(summary)
    summary["validation"]["deterministic_csv_render"] = csv_text == render_first_seen_csv(rows)
    summary["validation"]["deterministic_report_render"] = report_text == render_first_seen_report(summary)
    summary["validation"]["all_validation_passed"] = all(
        value for value in summary["validation"].values() if isinstance(value, bool)
    )
    csv_path.write_text(csv_text, encoding="utf-8", newline="")
    report_text = render_first_seen_report(summary)
    report_path.write_text(report_text, encoding="utf-8")
    summary["reproducibility_hashes"] = {
        "wallet_first_seen_dataset_csv_sha256": _sha256_bytes(csv_text.encode("utf-8")),
        "wallet_first_seen_report_md_sha256": _sha256_bytes(report_text.encode("utf-8")),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def finalize_existing_first_seen_output(
    output_dir: Path = DEFAULT_FIRST_SEEN_OUTPUT,
) -> dict[str, Any]:
    """Apply live-window eligibility to an already captured bounded run.

    This supports deterministic recovery when a completed run predates the
    explicit historical page-churn classification. It performs no network
    requests.
    """
    csv_path = output_dir / "wallet_first_seen_dataset.csv"
    summary_path = output_dir / "wallet_first_seen_summary.json"
    report_path = output_dir / "wallet_first_seen_report.md"
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        source_rows = [dict(row) for row in csv.DictReader(handle)]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    start = _parse_datetime(summary["experiment_started_at_utc"])
    end = _parse_datetime(summary["experiment_completed_at_utc"])
    interval = float(summary["poll_interval_seconds"])
    live_start = start - timedelta(seconds=interval) if start else None
    rows: list[dict[str, str]] = []
    for source in source_rows:
        trade_dt = _parse_datetime(source.get("trade_datetime_utc") or "")
        first_seen_dt = _parse_datetime(source.get("first_observation_timestamp_utc") or "")
        is_live = bool(trade_dt and live_start and end and live_start <= trade_dt <= end)
        if is_live and trade_dt and first_seen_dt and first_seen_dt >= trade_dt:
            source["first_seen_delay_seconds"] = _seconds((first_seen_dt - trade_dt).total_seconds())
            source["delay_measurement_status"] = "measured_upper_bound"
            source["observation_class"] = "new_live_window_trade"
        elif is_live:
            source["first_seen_delay_seconds"] = ""
            source["delay_measurement_status"] = "unknown_missing_or_invalid_timestamp"
            source["observation_class"] = "new_live_window_trade"
        else:
            source["first_seen_delay_seconds"] = ""
            source["delay_measurement_status"] = "excluded_historical_page_churn"
            source["observation_class"] = "historical_page_churn"
        source["five_minute_market"] = str(
            _is_five_minute_market(source.get("market_title", ""), source.get("market_slug", ""))
        ).lower()
        rows.append({field: source.get(field, "") for field in FIRST_SEEN_FIELDS})
    rows.sort(
        key=lambda row: (
            row["first_observation_timestamp_utc"],
            row["wallet_id"],
            row["trade_timestamp"],
            row["trade_identity"],
        )
    )
    live_rows = [row for row in rows if row["observation_class"] == "new_live_window_trade"]
    delays = [float(row["first_seen_delay_seconds"]) for row in live_rows if row["first_seen_delay_seconds"]]
    five_minute_rows = [row for row in live_rows if row["five_minute_market"] == "true"]
    five_minute_delays = [
        float(row["first_seen_delay_seconds"])
        for row in five_minute_rows
        if row["first_seen_delay_seconds"]
    ]
    summary["newly_observed_identities"] = len(rows)
    summary["new_trades_detected"] = len(live_rows)
    summary["historical_page_churn_identities"] = len(rows) - len(live_rows)
    summary["five_minute_trades_detected"] = len(five_minute_rows)
    summary["measurable_first_seen_delays"] = len(delays)
    summary["unknown_first_seen_delays"] = len(live_rows) - len(delays)
    summary["first_seen_delay_seconds"] = _stats(delays)
    summary["five_minute_first_seen_delay_seconds"] = _stats(five_minute_delays)
    summary["can_h2_now_be_tested"] = bool(five_minute_delays)
    summary["research_conclusion"] = (
        "H2_MEASURABLE_PROSPECTIVELY"
        if five_minute_delays
        else "INCONCLUSIVE_NO_NEW_MEASURABLE_FIVE_MINUTE_TRADES"
    )
    summary["conclusion_detail"] = (
        "The bounded observer produced measurable trade-to-first-seen upper bounds. A larger preregistered prospective sample is still required before H2 can be supported or rejected."
        if five_minute_delays
        else "The observer is operational, but no newly observed five-minute trade had a measurable delay in this bounded window, so H2 remains untested."
    )
    churn_limit = "Historical identities rotating into the latest-100 page are excluded from first-seen delay statistics."
    if churn_limit not in summary["measurement_limits"]:
        summary["measurement_limits"].append(churn_limit)
    summary["validation"]["output_schema_complete"] = all(
        list(row) == FIRST_SEEN_FIELDS for row in rows
    )
    csv_text = render_first_seen_csv(rows)
    report_text = render_first_seen_report(summary)
    summary["validation"]["deterministic_csv_render"] = csv_text == render_first_seen_csv(rows)
    summary["validation"]["deterministic_report_render"] = report_text == render_first_seen_report(summary)
    summary["validation"]["all_validation_passed"] = all(
        value for value in summary["validation"].values() if isinstance(value, bool)
    )
    csv_path.write_text(csv_text, encoding="utf-8", newline="")
    report_text = render_first_seen_report(summary)
    report_path.write_text(report_text, encoding="utf-8")
    summary["reproducibility_hashes"] = {
        "wallet_first_seen_dataset_csv_sha256": _sha256_bytes(csv_text.encode("utf-8")),
        "wallet_first_seen_report_md_sha256": _sha256_bytes(report_text.encode("utf-8")),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def analyze_first_seen_snapshots(
    snapshots: list[dict[str, Any]],
    *,
    wallets: tuple[str, ...],
    experiment_started_at: str,
    experiment_completed_at: str,
    configured_duration_seconds: float,
    poll_interval_seconds: float,
    page_limit: int,
    max_requests: int,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    ordered = sorted(
        snapshots,
        key=lambda item: (
            int(item.get("poll_cycle") or 0),
            wallets.index(str(item.get("wallet_id") or "").lower())
            if str(item.get("wallet_id") or "").lower() in wallets
            else len(wallets),
            str(item.get("request_started_at_utc") or ""),
        ),
    )
    baseline_established: set[str] = set()
    baseline_identities: set[str] = set()
    seen: dict[str, dict[str, Any]] = {}
    previous_ids: dict[str, set[str]] = defaultdict(set)
    absent_since_previous: dict[str, set[str]] = defaultdict(set)
    duplicate_observations = 0
    missed_observations = 0
    reappearances = 0
    observed_rows = 0
    response_latencies: list[float] = []
    request_failures: list[dict[str, Any]] = []
    poll_audit: list[dict[str, Any]] = []

    for snapshot in ordered:
        wallet_id = str(snapshot.get("wallet_id") or "").lower()
        status_code = int(snapshot.get("status_code") or 0)
        request_dt = _parse_datetime(str(snapshot.get("request_started_at_utc") or ""))
        response_dt = _parse_datetime(str(snapshot.get("response_received_at_utc") or ""))
        latency_ms = (response_dt - request_dt).total_seconds() * 1000 if request_dt and response_dt else None
        if latency_ms is not None:
            response_latencies.append(latency_ms)
        success = status_code == 200 and isinstance(snapshot.get("rows"), list)
        source_rows = [row for row in snapshot.get("rows", []) if isinstance(row, dict)] if success else []
        if not success:
            request_failures.append(
                {
                    "poll_cycle": int(snapshot.get("poll_cycle") or 0),
                    "wallet_id": wallet_id,
                    "status_code": status_code,
                    "error": str(snapshot.get("error") or ""),
                }
            )
        current: dict[str, dict[str, Any]] = {}
        for source in source_rows:
            identity = trade_identity(wallet_id, source)
            current[identity] = source
        current_ids = set(current)
        observed_rows += len(current_ids)

        missing_now = set()
        if success and previous_ids[wallet_id] and source_rows:
            timestamps = [_trade_timestamp(row) for row in source_rows]
            valid_timestamps = [value for value in timestamps if value is not None]
            oldest_current = min(valid_timestamps) if valid_timestamps else None
            for identity in previous_ids[wallet_id] - current_ids:
                prior = seen.get(identity)
                prior_timestamp = _trade_timestamp(prior["source_row"]) if prior else None
                if oldest_current is not None and prior_timestamp is not None and prior_timestamp >= oldest_current:
                    missing_now.add(identity)
            missed_observations += len(missing_now)
            absent_since_previous[wallet_id].update(missing_now)

        if success and wallet_id not in baseline_established:
            baseline_established.add(wallet_id)
            baseline_identities.update(current_ids)
            for identity, source in current.items():
                seen.setdefault(identity, {"source_row": source, "baseline": True})
        elif success:
            for identity, source in current.items():
                if identity in seen:
                    duplicate_observations += 1
                    if identity in absent_since_previous[wallet_id]:
                        reappearances += 1
                        absent_since_previous[wallet_id].discard(identity)
                    continue
                seen[identity] = {
                    "source_row": source,
                    "baseline": False,
                    "snapshot": snapshot,
                    "response_latency_ms": latency_ms,
                }
        if success:
            previous_ids[wallet_id] = current_ids
        poll_audit.append(
            {
                "poll_cycle": int(snapshot.get("poll_cycle") or 0),
                "wallet_id": wallet_id,
                "status_code": status_code,
                "rows_returned": len(source_rows),
                "unique_rows_returned": len(current_ids),
                "response_latency_ms": round(latency_ms, 3) if latency_ms is not None else None,
                "missing_expected_rows": len(missing_now),
                "error": str(snapshot.get("error") or ""),
            }
        )

    records: list[dict[str, str]] = []
    experiment_start_dt = _parse_datetime(experiment_started_at)
    experiment_end_dt = _parse_datetime(experiment_completed_at)
    for identity, item in seen.items():
        if item.get("baseline"):
            continue
        source = item["source_row"]
        snapshot = item["snapshot"]
        trade_dt = _parse_trade_datetime(source)
        first_seen_dt = _parse_datetime(str(snapshot.get("response_received_at_utc") or ""))
        live_window_start = (
            experiment_start_dt - timedelta(seconds=poll_interval_seconds)
            if experiment_start_dt
            else None
        )
        live_window_trade = bool(
            trade_dt
            and live_window_start
            and experiment_end_dt
            and live_window_start <= trade_dt <= experiment_end_dt
        )
        delay = (
            (first_seen_dt - trade_dt).total_seconds()
            if live_window_trade and first_seen_dt and trade_dt
            else None
        )
        if not live_window_trade:
            delay_status = "excluded_historical_page_churn"
            observation_class = "historical_page_churn"
        elif delay is None:
            delay_status = "unknown_missing_or_invalid_timestamp"
            observation_class = "new_live_window_trade"
        elif delay < 0:
            delay_status = "invalid_first_seen_precedes_trade"
            observation_class = "new_live_window_trade"
            delay = None
        else:
            delay_status = "measured_upper_bound"
            observation_class = "new_live_window_trade"
        title = str(source.get("title") or "")
        slug = str(source.get("slug") or "")
        market_type, asset_class, up_down = classify_trade_market(title, slug)
        five_minute = _is_five_minute_market(title, slug)
        transaction_hash = str(source.get("transactionHash") or "").lower()
        records.append(
            {
                "wallet_id": str(snapshot.get("wallet_id") or "").lower(),
                "profile_url": f"https://polymarket.com/{str(snapshot.get('wallet_id') or '').lower()}",
                "poll_cycle": str(snapshot.get("poll_cycle") or ""),
                "poll_started_at_utc": str(snapshot.get("poll_started_at_utc") or ""),
                "request_started_at_utc": str(snapshot.get("request_started_at_utc") or ""),
                "response_received_at_utc": str(snapshot.get("response_received_at_utc") or ""),
                "first_observation_timestamp_utc": str(snapshot.get("response_received_at_utc") or ""),
                "trade_timestamp": str(source.get("timestamp") or ""),
                "trade_datetime_utc": _iso(trade_dt),
                "first_seen_delay_seconds": _seconds(delay),
                "delay_measurement_status": delay_status,
                "observation_class": observation_class,
                "poll_interval_seconds": _seconds(poll_interval_seconds),
                "response_latency_ms": _seconds(item.get("response_latency_ms")),
                "transaction_hash": transaction_hash,
                "transaction_hash_available": str(bool(transaction_hash)).lower(),
                "market_slug": slug,
                "event_slug": str(source.get("eventSlug") or ""),
                "market_title": title,
                "condition_id": str(source.get("conditionId") or "").lower(),
                "token_id": str(source.get("asset") or ""),
                "outcome": str(source.get("outcome") or ""),
                "side": str(source.get("side") or "").upper(),
                "price": normalize_decimal(source.get("price")),
                "size": normalize_decimal(source.get("size")),
                "market_type": market_type,
                "asset_class": asset_class,
                "up_down_market": str(up_down).lower(),
                "five_minute_market": str(five_minute).lower(),
                "source_endpoint": str(snapshot.get("source_endpoint") or ""),
                "trade_identity": identity,
                "raw_payload_hash": raw_payload_hash(source),
            }
        )
    records.sort(
        key=lambda row: (
            row["first_observation_timestamp_utc"],
            row["wallet_id"],
            row["trade_timestamp"],
            row["trade_identity"],
        )
    )

    live_records = [row for row in records if row["observation_class"] == "new_live_window_trade"]
    historical_churn = [row for row in records if row["observation_class"] == "historical_page_churn"]
    delays = [float(row["first_seen_delay_seconds"]) for row in live_records if row["first_seen_delay_seconds"]]
    five_minute_records = [row for row in live_records if row["five_minute_market"] == "true"]
    five_minute_delays = [
        float(row["first_seen_delay_seconds"])
        for row in five_minute_records
        if row["first_seen_delay_seconds"]
    ]
    successful_requests = sum(item["status_code"] == 200 for item in poll_audit)
    started_dt = _parse_datetime(experiment_started_at)
    completed_dt = _parse_datetime(experiment_completed_at)
    observed_duration = (completed_dt - started_dt).total_seconds() if started_dt and completed_dt else None
    can_measure = bool(five_minute_delays)
    conclusion = "H2_MEASURABLE_PROSPECTIVELY" if can_measure else "INCONCLUSIVE_NO_NEW_MEASURABLE_TRADES"
    summary: dict[str, Any] = {
        "task": "Wallet First-Seen Detection Sprint v1",
        "master_question": "What is the earliest moment at which a newly executed wallet trade becomes observable through public APIs?",
        "experiment_started_at_utc": experiment_started_at,
        "experiment_completed_at_utc": experiment_completed_at,
        "configured_duration_seconds": configured_duration_seconds,
        "observed_duration_seconds": round(observed_duration, 6) if observed_duration is not None else None,
        "wallets_observed": list(wallets),
        "wallet_count": len(wallets),
        "poll_interval_seconds": poll_interval_seconds,
        "poll_frequency_description": f"one cycle every {poll_interval_seconds:g} seconds; one request per wallet per cycle",
        "page_limit": page_limit,
        "max_requests": max_requests,
        "poll_cycles_attempted": max((item["poll_cycle"] for item in poll_audit), default=0),
        "requests_attempted": len(poll_audit),
        "requests_successful": successful_requests,
        "requests_failed": len(poll_audit) - successful_requests,
        "baseline_wallets_established": len(baseline_established),
        "baseline_unique_trades": len(baseline_identities),
        "response_rows_observed": observed_rows,
        "newly_observed_identities": len(records),
        "new_trades_detected": len(live_records),
        "historical_page_churn_identities": len(historical_churn),
        "five_minute_trades_detected": len(five_minute_records),
        "measurable_first_seen_delays": len(delays),
        "unknown_first_seen_delays": len(live_records) - len(delays),
        "duplicate_observations": duplicate_observations,
        "missed_observations": missed_observations,
        "reappearances_after_gap": reappearances,
        "first_seen_delay_seconds": _stats(delays),
        "five_minute_first_seen_delay_seconds": _stats(five_minute_delays),
        "response_latency_ms": _stats(response_latencies),
        "api_consistency": {
            "successful_request_rate": round(successful_requests / len(poll_audit), 6) if poll_audit else 0.0,
            "all_wallet_baselines_established": baseline_established == set(wallets),
            "request_failures": request_failures,
            "missed_observation_definition": "A previously seen identity is absent while its trade timestamp remains within the current page timestamp range.",
        },
        "rate_limit": {
            "documentation_url": RATE_LIMIT_DOC_URL,
            "documentation_checked_on": "2026-06-28",
            "data_api_general_limit_requests": DATA_API_RATE_LIMIT_REQUESTS,
            "data_api_general_limit_window_seconds": DATA_API_RATE_LIMIT_WINDOW_SECONDS,
            "configured_requests_per_10_seconds": round(len(wallets) * 10 / poll_interval_seconds, 6),
            "configured_limit_utilization": round(
                (len(wallets) * 10 / poll_interval_seconds) / DATA_API_RATE_LIMIT_REQUESTS, 6
            ),
            "enforcement_note": "Official documentation says excess requests are throttled on sliding windows.",
        },
        "endpoint": {
            "url": "https://data-api.polymarket.com/activity",
            "query": "user=<wallet>&type=TRADE&limit=100&offset=0&sortBy=TIMESTAMP&sortDirection=DESC",
            "authentication": "none",
            "api_documentation_url": API_INTRO_DOC_URL,
            "method": "GET",
        },
        "poll_audit": poll_audit,
        "can_h2_now_be_tested": can_measure,
        "research_conclusion": conclusion,
        "conclusion_detail": (
            "The bounded observer produced measurable trade-to-first-seen upper bounds. A larger preregistered prospective sample is still required before H2 can be supported or rejected."
            if can_measure
            else "The observer is operational, but no newly observed trade had a measurable delay in this bounded window, so H2 remains untested."
        ),
        "measurement_limits": [
            "First-seen delay is an upper bound containing API publication delay, polling interval, request duration, and local clock error.",
            "The experiment cannot identify the exact server publication timestamp between polls.",
            "A bounded latest-100 page can omit older activity during bursts.",
            "Historical identities rotating into the latest-100 page are excluded from first-seen delay statistics.",
            "The selected wallets are retrospective H1 candidates and are not an unbiased wallet sample.",
        ],
        "recommended_next_hypothesis": (
            "H3: Wallet Detection-To-Expiry Feasibility Sprint v1 after a preregistered H2 first-seen sample is large enough."
            if can_measure
            else "H2 remains active: repeat a longer but still bounded first-seen observation before H3."
        ),
        "validation": validate_first_seen(records, snapshots, wallets, poll_interval_seconds, max_requests),
    }
    return records, summary


def validate_first_seen(
    rows: list[dict[str, str]],
    snapshots: list[dict[str, Any]],
    wallets: tuple[str, ...],
    poll_interval_seconds: float,
    max_requests: int,
) -> dict[str, Any]:
    sort_keys = [
        (row["first_observation_timestamp_utc"], row["wallet_id"], row["trade_timestamp"], row["trade_identity"])
        for row in rows
    ]
    return {
        "only_approved_wallets": all(row["wallet_id"] in wallets for row in rows)
        and all(str(item.get("wallet_id") or "").lower() in wallets for item in snapshots),
        "public_read_only_endpoint_only": all(
            str(item.get("source_endpoint") or "").startswith("https://data-api.polymarket.com/activity")
            for item in snapshots
        ),
        "bounded_request_count": len(snapshots) <= max_requests,
        "poll_interval_positive": poll_interval_seconds > 0,
        "deterministic_ordering": sort_keys == sorted(sort_keys),
        "unique_trade_identities": len({row["trade_identity"] for row in rows}) == len(rows),
        "output_schema_complete": all(list(row) == FIRST_SEEN_FIELDS for row in rows),
        "measured_delays_non_negative": all(
            not row["first_seen_delay_seconds"] or float(row["first_seen_delay_seconds"]) >= 0 for row in rows
        ),
        "measured_delays_have_required_timestamps": all(
            row["delay_measurement_status"] != "measured_upper_bound"
            or (row["trade_datetime_utc"] and row["first_observation_timestamp_utc"])
            for row in rows
        ),
        "no_authenticated_or_execution_fields": not any(
            forbidden in field.lower()
            for field in FIRST_SEEN_FIELDS
            for forbidden in ("private_key", "api_key", "secret", "order_placement")
        ),
    }


def trade_identity(wallet_id: str, row: dict[str, Any]) -> str:
    transaction_hash = str(row.get("transactionHash") or "").lower()
    components = [
        wallet_id.lower(),
        transaction_hash,
        str(row.get("conditionId") or "").lower(),
        str(row.get("asset") or ""),
        str(row.get("timestamp") or ""),
        str(row.get("side") or "").lower(),
        normalize_decimal(row.get("price")),
        normalize_decimal(row.get("size")),
    ]
    return hashlib.sha256("|".join(components).encode("utf-8")).hexdigest()


def render_first_seen_csv(rows: list[dict[str, str]]) -> str:
    from io import StringIO

    handle = StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=FIRST_SEEN_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue()


def render_first_seen_report(summary: dict[str, Any]) -> str:
    delay = summary["first_seen_delay_seconds"]
    latency = summary["response_latency_ms"]
    lines = [
        "# Wallet First-Seen Detection Sprint v1",
        "",
        "This is a bounded public-data observation experiment. It is not permanent monitoring, a trading signal, or an execution system.",
        "",
        "## Experiment",
        "",
        f"- Observation start: {summary['experiment_started_at_utc']}",
        f"- Observation end: {summary['experiment_completed_at_utc']}",
        f"- Observed duration: {summary['observed_duration_seconds']} seconds",
        f"- Wallets: {summary['wallet_count']}",
        f"- Poll interval: {summary['poll_interval_seconds']} seconds",
        f"- Requests: {summary['requests_attempted']} attempted, {summary['requests_successful']} successful, {summary['requests_failed']} failed",
        f"- Endpoint: `{summary['endpoint']['url']}` (public GET, no authentication)",
        "",
        "## Observations",
        "",
        f"- Baseline unique trades: {summary['baseline_unique_trades']}",
        f"- Response rows observed: {summary['response_rows_observed']}",
        f"- Newly observed identities: {summary['newly_observed_identities']}",
        f"- New trades detected: {summary['new_trades_detected']}",
        f"- Target five-minute trades detected: {summary['five_minute_trades_detected']}",
        f"- Historical page-churn identities excluded: {summary['historical_page_churn_identities']}",
        f"- Measurable first-seen delays: {summary['measurable_first_seen_delays']}",
        f"- Unknown first-seen delays: {summary['unknown_first_seen_delays']}",
        f"- Duplicate observations: {summary['duplicate_observations']}",
        f"- Missed observations: {summary['missed_observations']}",
        f"- Reappearances after gap: {summary['reappearances_after_gap']}",
        "",
        "## Timing",
        "",
        f"- First-seen delay minimum / median / mean / maximum: {_display_stats(delay)}",
        f"- Five-minute delay minimum / median / mean / maximum: {_display_stats(summary['five_minute_first_seen_delay_seconds'])}",
        f"- Response latency minimum / median / mean / maximum ms: {_display_stats(latency)}",
        "- First-seen delay is a polling-quantized upper bound, not exact server publication latency.",
        "",
        "## API Limits",
        "",
        f"- Official Data API general limit: {summary['rate_limit']['data_api_general_limit_requests']} requests per {summary['rate_limit']['data_api_general_limit_window_seconds']} seconds",
        f"- Configured rate: {summary['rate_limit']['configured_requests_per_10_seconds']} requests per 10 seconds",
        f"- Limit utilization: {summary['rate_limit']['configured_limit_utilization']:.2%}",
        f"- Documentation: {summary['rate_limit']['documentation_url']}",
        "",
        "## Can H2 Now Be Tested?",
        "",
        "YES" if summary["can_h2_now_be_tested"] else "NO",
        "",
        summary["conclusion_detail"],
        "",
        "## Research Conclusion",
        "",
        summary["research_conclusion"],
        "",
        "## Recommended Next Hypothesis",
        "",
        summary["recommended_next_hypothesis"],
    ]
    return "\n".join(lines) + "\n"


def _validate_limits(
    wallets: tuple[str, ...],
    duration_seconds: float,
    poll_interval_seconds: float,
    page_limit: int,
    max_requests: int,
) -> None:
    if wallets != STRONGEST_H1_WALLETS:
        raise ValueError("the prospective experiment is restricted to the four frozen H1 wallets")
    if not 0 < duration_seconds <= DEFAULT_DURATION_SECONDS:
        raise ValueError(f"duration must be in (0, {DEFAULT_DURATION_SECONDS}]")
    if poll_interval_seconds < DEFAULT_POLL_INTERVAL_SECONDS:
        raise ValueError(f"poll interval must be at least {DEFAULT_POLL_INTERVAL_SECONDS} seconds")
    if not 1 <= page_limit <= DEFAULT_PAGE_LIMIT:
        raise ValueError(f"page limit must be in [1, {DEFAULT_PAGE_LIMIT}]")
    if not 1 <= max_requests <= DEFAULT_MAX_REQUESTS:
        raise ValueError(f"max requests must be in [1, {DEFAULT_MAX_REQUESTS}]")


def _trade_timestamp(row: dict[str, Any]) -> int | None:
    try:
        return int(row.get("timestamp"))
    except (TypeError, ValueError):
        return None


def _is_five_minute_market(title: str, slug: str) -> bool:
    text = f"{title} {slug}".lower()
    return bool(re.search(r"(^|[^a-z0-9])5m([^a-z0-9]|$)|5[ -]?min(?:ute)?s?", text))


def _parse_trade_datetime(row: dict[str, Any]) -> datetime | None:
    value = _trade_timestamp(row)
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(value, UTC)
    except (OSError, OverflowError, ValueError):
        return None


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _iso(value: datetime | None) -> str:
    return value.isoformat(timespec="milliseconds") if value else ""


def _seconds(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"


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


def _display_stats(stats: dict[str, Any]) -> str:
    return " / ".join(
        "unavailable" if stats[key] is None else str(stats[key])
        for key in ("minimum", "median", "mean", "maximum")
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
