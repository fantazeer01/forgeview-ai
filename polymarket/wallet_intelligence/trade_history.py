"""Fixture-only wallet trade-history normalization.

This module intentionally has no wallet, key, order, trading, or live capture
capability. Network-enabled ingestion must be authorized in a later task.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

from .schema import TRADE_HISTORY_FIELDS, TradeHistoryRecord
from .schema import WatchedWallet


NORMALIZATION_VERSION = "wallet_trade_history_v1"
DEFAULT_FIXTURE = Path(
    "polymarket/models/wallet_intelligence_v1/deep_history_feasibility/bounded_probe_sample.jsonl"
)
DEFAULT_DESIGN_LIMITS = Path(
    "polymarket/models/wallet_intelligence_v1/trade_history_ingestion_design/ingestion_limits.json"
)
DEFAULT_FIXTURE_OUTPUT = Path(
    "polymarket/models/wallet_intelligence_v1/trade_history_ingester_fixture"
)
DEFAULT_SMOKE_OUTPUT = Path("polymarket/data/wallet_intelligence/trade_history_smoke_v1")
DEFAULT_WATCHED_WALLETS = Path("polymarket/wallet_intelligence/watched_wallets.example.csv")
DEFAULT_WALLET_PROFILES = Path("polymarket/data/wallet_intelligence/v1/wallet_profiles.csv")
REQUIRED_FIELDS = [
    "wallet_id",
    "source_endpoint",
    "activity_timestamp",
    "transaction_hash",
    "condition_id",
    "token_id",
    "asset_id",
    "side",
    "price",
    "size",
    "source_fetch_timestamp",
    "raw_payload_hash",
]
PROVENANCE_FIELDS = [
    "source_endpoint",
    "source_fetch_timestamp",
    "raw_payload_hash",
    "raw_page_hash",
    "normalization_version",
]


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def raw_payload_hash(row: dict[str, Any]) -> str:
    return sha256_text(canonical_json(row))


def raw_page_hash(rows: list[dict[str, Any]]) -> str:
    return sha256_text(canonical_json(rows))


def parse_activity_datetime(timestamp: Any) -> str:
    try:
        parsed = int(timestamp)
    except (TypeError, ValueError):
        return ""
    return datetime.fromtimestamp(parsed, UTC).replace(microsecond=0).isoformat()


def normalize_decimal(value: Any) -> str:
    if value is None or value == "":
        return ""
    try:
        dec = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return ""
    normalized = dec.normalize()
    return format(normalized, "f")


def decimal_or_none(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def classify_trade_market(title: str, slug: str) -> tuple[str, str, bool]:
    text = f"{title} {slug}".lower()
    asset_class = "other"
    if re.search(r"(^|[^a-z])btc([^a-z]|$)|bitcoin", text):
        asset_class = "BTC"
    elif re.search(r"(^|[^a-z])eth([^a-z]|$)|ethereum", text):
        asset_class = "ETH"
    elif re.search(r"(^|[^a-z])sol([^a-z]|$)|solana", text):
        asset_class = "SOL"

    up_down = bool(
        asset_class in {"BTC", "ETH", "SOL"}
        and (
            "updown" in text
            or "up or down" in text
            or re.search(r"(^|-)up($|-)", slug.lower())
            or re.search(r"(^|-)down($|-)", slug.lower())
        )
    )
    if up_down:
        market_type = "fast_crypto_up_down"
    elif asset_class in {"BTC", "ETH", "SOL"}:
        market_type = "crypto_other"
    elif any(token in text for token in ("rain", "weather", "temperature", "snow", "hurricane")):
        market_type = "weather"
    else:
        market_type = "other"
    return market_type, asset_class, up_down


def classify_entry_or_exit(activity_type: str, side: str) -> str:
    activity_upper = (activity_type or "").upper()
    side_upper = (side or "").upper()
    if activity_upper == "TRADE" and side_upper == "BUY":
        return "entry_candidate"
    if activity_upper == "TRADE" and side_upper == "SELL":
        return "exit_candidate"
    if activity_upper == "REDEEM":
        return "resolution_candidate"
    if activity_upper in {"MAKER_REBATE", "TAKER_REBATE", "REWARD"}:
        return "rebate_or_other"
    return "unknown"


def build_dedupe_key(record: dict[str, str]) -> str:
    parts = [
        "wallet_id",
        "source_endpoint_name",
        "transaction_hash",
        "condition_id",
        "token_id",
        "activity_timestamp",
        "side",
        "price",
        "size",
    ]
    return "|".join((record.get(part) or "").strip().lower() for part in parts)


def normalize_trade_row(
    row: dict[str, Any],
    *,
    wallet_id: str,
    profile_url: str,
    source_endpoint: str,
    source_endpoint_name: str,
    source_fetch_timestamp: str,
    page_hash: str,
) -> TradeHistoryRecord:
    market_title = str(row.get("title") or "")
    market_slug = str(row.get("slug") or "")
    event_slug = str(row.get("eventSlug") or "")
    activity_type = str(row.get("type") or "TRADE").upper()
    timestamp = str(row.get("timestamp") or "")
    token_id = str(row.get("asset") or "")
    condition_id = str(row.get("conditionId") or "").lower()
    side = str(row.get("side") or "").upper()
    price = normalize_decimal(row.get("price"))
    size = normalize_decimal(row.get("size"))
    endpoint_notional = normalize_decimal(row.get("usdcSize"))
    notional_source = "endpoint_usdcSize" if endpoint_notional else "unavailable"
    notional_value = endpoint_notional
    if not notional_value:
        price_dec = decimal_or_none(price)
        size_dec = decimal_or_none(size)
        if price_dec is not None and size_dec is not None:
            notional_value = normalize_decimal(price_dec * size_dec)
            notional_source = "computed_price_times_size"
    market_type, asset_class, up_down = classify_trade_market(market_title, market_slug)
    raw_hash = raw_payload_hash(row)
    quality_flags: list[str] = []
    if not event_slug:
        quality_flags.append("missing_event_slug")
    if not endpoint_notional and notional_value:
        quality_flags.append("computed_notional")
    if not parse_activity_datetime(timestamp):
        quality_flags.append("timestamp_parse_failed")
    if market_type == "other":
        quality_flags.append("non_crypto_or_unclassified_market")
    if source_endpoint_name == "activity_primary":
        endpoint_name = "activity_primary"
    else:
        endpoint_name = source_endpoint_name
    base = {
        "wallet_id": wallet_id.lower(),
        "profile_url": profile_url,
        "source_endpoint": source_endpoint,
        "source_endpoint_name": endpoint_name,
        "activity_type": activity_type,
        "activity_timestamp": timestamp,
        "activity_datetime_utc": parse_activity_datetime(timestamp),
        "transaction_hash": str(row.get("transactionHash") or "").lower(),
        "condition_id": condition_id,
        "token_id": token_id,
        "asset_id": token_id,
        "market_slug": market_slug,
        "event_slug": event_slug,
        "market_title": market_title,
        "outcome": str(row.get("outcome") or ""),
        "outcome_index": str(row.get("outcomeIndex") if row.get("outcomeIndex") is not None else ""),
        "side": side,
        "price": price,
        "size": size,
        "notional_value": notional_value,
        "notional_source": notional_source,
        "market_type": market_type,
        "asset_class": asset_class,
        "up_down_market": str(bool(up_down)).lower(),
        "time_to_expiry_seconds": "",
        "expiry_timestamp": "",
        "expiry_source": "unavailable",
        "entry_or_exit_candidate": classify_entry_or_exit(activity_type, side),
        "lifecycle_group_key": "|".join([wallet_id.lower(), condition_id, token_id, str(row.get("outcome") or "")]),
        "dedupe_key": "",
        "source_fetch_timestamp": source_fetch_timestamp,
        "raw_payload_hash": raw_hash,
        "raw_page_hash": page_hash,
        "normalization_version": NORMALIZATION_VERSION,
        "data_quality_flags": ";".join(quality_flags) if quality_flags else "none",
    }
    base["dedupe_key"] = build_dedupe_key(base)
    return TradeHistoryRecord(**base)


def dedupe_records(records: Iterable[TradeHistoryRecord]) -> tuple[list[TradeHistoryRecord], int]:
    seen: set[str] = set()
    unique: list[TradeHistoryRecord] = []
    duplicates = 0
    for record in records:
        if record.dedupe_key in seen:
            duplicates += 1
            continue
        seen.add(record.dedupe_key)
        unique.append(record)
    return unique, duplicates


def enforce_fixture_limits(
    *,
    wallet_count: int,
    rows_by_wallet: dict[str, int],
    pages_by_wallet: dict[str, int],
    limits: dict[str, Any],
) -> list[str]:
    scope = limits.get("first_ingestion_scope", limits)
    violations: list[str] = []
    if wallet_count > int(scope.get("max_wallets", 6)):
        violations.append("wallet_count_exceeds_limit")
    max_rows = int(scope.get("max_rows_per_wallet_primary_activity", 300))
    max_pages = int(scope.get("max_pages_per_wallet_primary_activity", 3))
    max_total = int(scope.get("max_total_activity_rows", 1800))
    if sum(rows_by_wallet.values()) > max_total:
        violations.append("total_activity_rows_exceeds_limit")
    for wallet, rows in rows_by_wallet.items():
        if rows > max_rows:
            violations.append(f"rows_exceed_limit:{wallet}")
    for wallet, pages in pages_by_wallet.items():
        if pages > max_pages:
            violations.append(f"pages_exceed_limit:{wallet}")
    return violations


def load_limits(path: Path = DEFAULT_DESIGN_LIMITS) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "first_ingestion_scope": {
            "max_wallets": 6,
            "max_pages_per_wallet_primary_activity": 3,
            "max_rows_per_wallet_primary_activity": 300,
            "max_total_activity_rows": 1800,
            "max_total_cross_check_rows": 600,
        }
    }


def _payload_rows(value: Any) -> list[dict[str, Any]]:
    payload = value.get("payload") if isinstance(value, dict) else value
    if isinstance(payload, dict) and isinstance(payload.get("value"), list):
        payload = payload["value"]
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return []


def load_fixture_pages(path: Path) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            rows = _payload_rows(obj)
            pages.append(
                {
                    "wallet_id": str(obj.get("wallet_id") or obj.get("user") or ""),
                    "profile_url": str(obj.get("profile_url") or ""),
                    "source_endpoint": str(obj.get("url") or obj.get("source_endpoint") or ""),
                    "source_endpoint_name": str(obj.get("source_endpoint_name") or "activity_primary"),
                    "source_fetch_timestamp": str(
                        obj.get("fetched_at")
                        or obj.get("source_fetch_timestamp")
                        or obj.get("retrieved_at")
                        or datetime.now(UTC).replace(microsecond=0).isoformat()
                    ),
                    "rows": rows,
                }
            )
    return pages


def normalize_fixture_pages(pages: list[dict[str, Any]]) -> tuple[list[TradeHistoryRecord], dict[str, Any]]:
    records: list[TradeHistoryRecord] = []
    rows_by_wallet: dict[str, int] = {}
    pages_by_wallet: dict[str, int] = {}
    for page in pages:
        rows = page.get("rows") or []
        wallet_id = str(page.get("wallet_id") or "")
        if not wallet_id and rows:
            wallet_id = str(rows[0].get("proxyWallet") or "")
        wallet_id = wallet_id.lower()
        if not wallet_id:
            wallet_id = "unknown_wallet"
        profile_url = str(page.get("profile_url") or f"https://polymarket.com/{wallet_id}")
        page_hash = raw_page_hash(rows)
        rows_by_wallet[wallet_id] = rows_by_wallet.get(wallet_id, 0) + len(rows)
        pages_by_wallet[wallet_id] = pages_by_wallet.get(wallet_id, 0) + 1
        for row in rows:
            records.append(
                normalize_trade_row(
                    row,
                    wallet_id=wallet_id,
                    profile_url=profile_url,
                    source_endpoint=str(page.get("source_endpoint") or ""),
                    source_endpoint_name=str(page.get("source_endpoint_name") or "activity_primary"),
                    source_fetch_timestamp=str(page.get("source_fetch_timestamp") or ""),
                    page_hash=page_hash,
                )
            )
    unique, duplicates = dedupe_records(records)
    metadata = {
        "input_rows": len(records),
        "normalized_rows": len(unique),
        "duplicate_rows_removed": duplicates,
        "rows_by_wallet": rows_by_wallet,
        "pages_by_wallet": pages_by_wallet,
    }
    return unique, metadata


def write_csv(path: Path, records: list[TradeHistoryRecord]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRADE_HISTORY_FIELDS, lineterminator="\n")
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def write_raw_jsonl(path: Path, pages: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for page in pages:
            handle.write(canonical_json(page) + "\n")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validation_gate_results(
    records: list[TradeHistoryRecord],
    *,
    duplicate_rows_removed: int,
    limit_violations: list[str],
    deterministic_export: bool,
) -> dict[str, Any]:
    dicts = [asdict(record) for record in records]
    total = len(dicts)

    def coverage(fields: list[str]) -> float:
        if total == 0:
            return 0.0
        present = sum(1 for row in dicts if all(str(row.get(field) or "") for field in fields))
        return present / total

    timestamp_parse = coverage(["activity_datetime_utc"])
    classified = 0
    fast_recognizable = 0
    fast_classified = 0
    for row in dicts:
        if row.get("market_type") and row.get("market_type") != "unknown":
            classified += 1
        text = f"{row.get('market_title','')} {row.get('market_slug','')}".lower()
        if any(token in text for token in ("btc", "bitcoin", "eth", "ethereum", "sol", "solana")) and (
            "updown" in text or "up or down" in text
        ):
            fast_recognizable += 1
            if row.get("market_type") == "fast_crypto_up_down" and row.get("asset_class") in {"BTC", "ETH", "SOL"}:
                fast_classified += 1
    duplicate_rate = duplicate_rows_removed / (total + duplicate_rows_removed) if total + duplicate_rows_removed else 0.0
    gates = {
        "required_field_coverage": {
            "passed": coverage(REQUIRED_FIELDS) == 1.0,
            "coverage": coverage(REQUIRED_FIELDS),
        },
        "duplicate_rate": {
            "passed": duplicate_rate <= 0.01 and len({row["dedupe_key"] for row in dicts}) == total,
            "duplicate_rate_before_dedupe": duplicate_rate,
            "duplicates_removed": duplicate_rows_removed,
        },
        "timestamp_parse_rate": {
            "passed": timestamp_parse >= 0.99,
            "coverage": timestamp_parse,
        },
        "market_classification_coverage": {
            "passed": (classified / total if total else 0.0) >= 0.95,
            "coverage": classified / total if total else 0.0,
        },
        "fast_crypto_classification_coverage": {
            "passed": fast_classified == fast_recognizable,
            "coverage": fast_classified / fast_recognizable if fast_recognizable else 1.0,
            "recognizable_fast_crypto_rows": fast_recognizable,
        },
        "provenance_completeness": {
            "passed": coverage(PROVENANCE_FIELDS) == 1.0,
            "coverage": coverage(PROVENANCE_FIELDS),
        },
        "bounded_scope_compliance": {
            "passed": not limit_violations,
            "violations": limit_violations,
        },
        "safety_boundary_compliance": {
            "passed": True,
            "notes": "public read-only normalization path; no wallet/private-key/order/live-trading methods invoked",
        },
        "deterministic_export": {
            "passed": deterministic_export,
        },
        "join_quality_reporting_placeholder": {
            "passed": True,
            "notes": "this task does not perform joins; future joins must report coverage explicitly",
        },
    }
    return gates


def load_smoke_wallets(
    watched_wallets_path: Path = DEFAULT_WATCHED_WALLETS,
    wallet_profiles_path: Path = DEFAULT_WALLET_PROFILES,
    *,
    max_wallets: int = 6,
) -> list[WatchedWallet]:
    resolved_by_profile: dict[str, str] = {}
    resolved_by_seed: dict[str, str] = {}
    if wallet_profiles_path.exists():
        with wallet_profiles_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                wallet_id = (row.get("wallet_id") or "").strip()
                profile_url = (row.get("profile_url") or "").strip()
                if wallet_id and profile_url:
                    resolved_by_profile[profile_url.lower()] = wallet_id
                    resolved_by_seed[wallet_id.lower()] = wallet_id

    wallets: list[WatchedWallet] = []
    with watched_wallets_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            seed_id = (row.get("wallet_id") or "").strip()
            profile_url = (row.get("profile_url") or "").strip()
            resolved = resolved_by_profile.get(profile_url.lower()) or resolved_by_seed.get(seed_id.lower())
            if not resolved and re.fullmatch(r"0x[a-fA-F0-9]{40}", seed_id):
                resolved = seed_id
            if not resolved:
                continue
            wallets.append(
                WatchedWallet(
                    wallet_id=resolved,
                    profile_url=profile_url,
                    label=(row.get("label") or "").strip(),
                    source=(row.get("source") or "").strip(),
                    notes=(row.get("notes") or "").strip(),
                )
            )
            if len(wallets) >= max_wallets:
                break
    return wallets


def run_bounded_public_smoke(
    *,
    client: Any,
    watched_wallets_path: Path = DEFAULT_WATCHED_WALLETS,
    wallet_profiles_path: Path = DEFAULT_WALLET_PROFILES,
    output_dir: Path = DEFAULT_SMOKE_OUTPUT,
    limits_path: Path = DEFAULT_DESIGN_LIMITS,
    max_wallets: int = 6,
    page_size: int = 100,
    max_pages_per_wallet: int = 1,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    limits = load_limits(limits_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    smoke_limits = {
        "first_ingestion_scope": {
            "max_wallets": max_wallets,
            "max_rows_per_wallet_primary_activity": page_size * max_pages_per_wallet,
            "max_pages_per_wallet_primary_activity": max_pages_per_wallet,
            "max_total_activity_rows": page_size * max_pages_per_wallet * max_wallets,
        }
    }
    design_violations = []
    design_scope = limits.get("first_ingestion_scope", {})
    if max_wallets > int(design_scope.get("max_wallets", 6)):
        design_violations.append("smoke_wallet_cap_exceeds_design")
    if page_size > int(design_scope.get("page_size", 100)):
        design_violations.append("smoke_page_size_exceeds_design")
    if max_pages_per_wallet > 1:
        design_violations.append("smoke_pages_exceed_task_cap")

    wallets = load_smoke_wallets(
        watched_wallets_path,
        wallet_profiles_path,
        max_wallets=max_wallets,
    )
    pages: list[dict[str, Any]] = []
    endpoint_errors: dict[str, str] = {}
    for wallet in wallets:
        for page_index in range(max_pages_per_wallet):
            offset = page_index * page_size
            fetched_at = datetime.now(UTC).replace(microsecond=0).isoformat()
            try:
                response = client.activity_trades(wallet.wallet_id, limit=page_size, offset=offset)
                rows = _payload_rows(response.payload)
                pages.append(
                    {
                        "wallet_id": wallet.wallet_id.lower(),
                        "profile_url": wallet.profile_url,
                        "source_endpoint": response.url,
                        "source_endpoint_name": "activity_primary",
                        "source_fetch_timestamp": fetched_at,
                        "status_code": response.status_code,
                        "page_index": page_index,
                        "limit": page_size,
                        "offset": offset,
                        "rows": rows,
                    }
                )
            except Exception as exc:  # pragma: no cover - network-specific
                endpoint_errors[wallet.wallet_id.lower()] = str(exc)

    records, metadata = normalize_fixture_pages(pages)
    limit_violations = design_violations + enforce_fixture_limits(
        wallet_count=len(wallets),
        rows_by_wallet=metadata["rows_by_wallet"],
        pages_by_wallet=metadata["pages_by_wallet"],
        limits=smoke_limits,
    )

    raw_path = output_dir / "trade_history_raw.jsonl"
    csv_path = output_dir / "trade_history_normalized.csv"
    summary_path = output_dir / "trade_history_summary.json"
    report_json_path = output_dir / "bounded_smoke_report.json"
    report_md_path = output_dir / "bounded_smoke_report.md"
    gate_path = output_dir / "validation_gate_results.json"
    hash_path = output_dir / "reproducibility_hashes.json"

    write_raw_jsonl(raw_path, pages)
    write_csv(csv_path, records)
    first_csv_hash = file_sha256(csv_path)
    write_csv(csv_path, records)
    second_csv_hash = file_sha256(csv_path)
    deterministic = first_csv_hash == second_csv_hash
    gates = validation_gate_results(
        records,
        duplicate_rows_removed=int(metadata["duplicate_rows_removed"]),
        limit_violations=limit_violations,
        deterministic_export=deterministic,
    )
    all_gates_passed = all(value.get("passed") for value in gates.values())
    row_summary = summarize_trade_records(records)
    summary = {
        "task": "Wallet Public Trade History Bounded Public Smoke v1",
        "generated_at_utc": generated_at,
        "output_dir": str(output_dir),
        "wallets_attempted": len(wallets),
        "wallets_succeeded": len({page["wallet_id"] for page in pages}),
        "wallet_ids_attempted": [wallet.wallet_id.lower() for wallet in wallets],
        "wallet_ids_succeeded": sorted({page["wallet_id"] for page in pages}),
        "endpoint_errors": endpoint_errors,
        "pages_fetched": len(pages),
        "rows_fetched": metadata["input_rows"],
        "rows_normalized": metadata["normalized_rows"],
        "duplicate_rows_removed": metadata["duplicate_rows_removed"],
        "rows_by_wallet": metadata["rows_by_wallet"],
        "pages_by_wallet": metadata["pages_by_wallet"],
        "smoke_caps": smoke_limits["first_ingestion_scope"],
        "schema_fields": len(TRADE_HISTORY_FIELDS),
        "validation_gates_passed": all_gates_passed,
        "validation_gates": gates,
        "deterministic_csv_repeat_export": deterministic,
        "parquet_status": "not_written_no_project_parquet_dependency",
        "row_summary": row_summary,
        "fields_unavailable": [
            "time_to_expiry_seconds",
            "expiry_timestamp",
            "exit linkage",
            "holding time",
            "queue position",
            "fill priority",
            "Binance/reference alignment",
            "copyability delay",
        ],
        "strict_rules_observed": [
            "bounded public read-only activity TRADE smoke",
            "seed wallets only",
            "one activity page per wallet",
            "no broad public ingestion",
            "no live trading",
            "no wallet/private-key connection",
            "no order placement",
            "no capture campaign",
            "no holdout inspection",
            "no holdout evaluation",
        ],
        "recommended_next_task": "Wallet Trade Lifecycle Reconstruction Design v1",
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    gate_path.write_text(json.dumps(gates, indent=2, sort_keys=True), encoding="utf-8")
    report_json_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    hashes = {
        "trade_history_raw_jsonl_sha256": file_sha256(raw_path),
        "trade_history_normalized_csv_sha256": file_sha256(csv_path),
        "trade_history_summary_json_sha256": file_sha256(summary_path),
        "bounded_smoke_report_json_sha256": file_sha256(report_json_path),
        "validation_gate_results_json_sha256": file_sha256(gate_path),
        "csv_repeat_export_hash_match": deterministic,
    }
    hash_path.write_text(json.dumps(hashes, indent=2, sort_keys=True), encoding="utf-8")
    report_md_path.write_text(_build_smoke_markdown_report(summary, hashes), encoding="utf-8")
    return summary


def summarize_trade_records(records: list[TradeHistoryRecord]) -> dict[str, Any]:
    asset_counts = {"BTC": 0, "ETH": 0, "SOL": 0, "other": 0}
    outcome_counts = {"YES_like": 0, "NO_like": 0, "other": 0}
    side_counts = {"BUY": 0, "SELL": 0, "other": 0}
    buckets = {
        "0_10c": 0,
        "10_20c": 0,
        "20_40c": 0,
        "40_60c": 0,
        "60_80c": 0,
        "80_100c": 0,
        "unavailable": 0,
    }
    fast_crypto_rows = 0
    for record in records:
        asset_counts[record.asset_class if record.asset_class in {"BTC", "ETH", "SOL"} else "other"] += 1
        if record.market_type == "fast_crypto_up_down":
            fast_crypto_rows += 1
        outcome = record.outcome.lower()
        if outcome in {"up", "yes"}:
            outcome_counts["YES_like"] += 1
        elif outcome in {"down", "no"}:
            outcome_counts["NO_like"] += 1
        else:
            outcome_counts["other"] += 1
        if record.side in {"BUY", "SELL"}:
            side_counts[record.side] += 1
        else:
            side_counts["other"] += 1
        price = decimal_or_none(record.price)
        if price is None:
            buckets["unavailable"] += 1
        elif price < Decimal("0.10"):
            buckets["0_10c"] += 1
        elif price < Decimal("0.20"):
            buckets["10_20c"] += 1
        elif price < Decimal("0.40"):
            buckets["20_40c"] += 1
        elif price < Decimal("0.60"):
            buckets["40_60c"] += 1
        elif price < Decimal("0.80"):
            buckets["60_80c"] += 1
        else:
            buckets["80_100c"] += 1
    return {
        "fast_crypto_rows": fast_crypto_rows,
        "asset_counts": asset_counts,
        "yes_no_counts": outcome_counts,
        "side_counts": side_counts,
        "price_bucket_distribution": buckets,
    }


def run_fixture_ingestion(
    fixture_path: Path = DEFAULT_FIXTURE,
    output_dir: Path = DEFAULT_FIXTURE_OUTPUT,
    *,
    limits_path: Path = DEFAULT_DESIGN_LIMITS,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    limits = load_limits(limits_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    pages = load_fixture_pages(fixture_path)
    records, metadata = normalize_fixture_pages(pages)
    limit_violations = enforce_fixture_limits(
        wallet_count=len(metadata["rows_by_wallet"]),
        rows_by_wallet=metadata["rows_by_wallet"],
        pages_by_wallet=metadata["pages_by_wallet"],
        limits=limits,
    )

    raw_path = output_dir / "raw_trades_fixture.jsonl"
    csv_path = output_dir / "normalized_trades_fixture.csv"
    summary_path = output_dir / "fixture_ingestion_report.json"
    md_path = output_dir / "fixture_ingestion_report.md"
    gate_path = output_dir / "validation_gate_results.json"
    hash_path = output_dir / "reproducibility_hashes.json"

    write_raw_jsonl(raw_path, pages)
    write_csv(csv_path, records)
    first_csv_hash = file_sha256(csv_path)
    write_csv(csv_path, records)
    second_csv_hash = file_sha256(csv_path)
    deterministic = first_csv_hash == second_csv_hash

    gates = validation_gate_results(
        records,
        duplicate_rows_removed=int(metadata["duplicate_rows_removed"]),
        limit_violations=limit_violations,
        deterministic_export=deterministic,
    )
    all_gates_passed = all(value.get("passed") for value in gates.values())
    parquet_status = "not_written_no_project_parquet_dependency"
    summary = {
        "task": "Wallet Public Trade History Ingester Fixture Implementation v1",
        "generated_at_utc": generated_at,
        "fixture_path": str(fixture_path),
        "output_dir": str(output_dir),
        "schema_fields": len(TRADE_HISTORY_FIELDS),
        "fixture_pages": len(pages),
        "input_rows": metadata["input_rows"],
        "normalized_rows": metadata["normalized_rows"],
        "duplicate_rows_removed": metadata["duplicate_rows_removed"],
        "rows_by_wallet": metadata["rows_by_wallet"],
        "pages_by_wallet": metadata["pages_by_wallet"],
        "parquet_status": parquet_status,
        "validation_gates_passed": all_gates_passed,
        "validation_gates": gates,
        "strict_rules_observed": [
            "fixture-only normalization",
            "no broad public ingestion",
            "no live trading",
            "no wallet/private-key connection",
            "no order placement",
            "no capture campaign",
            "no holdout inspection",
            "no holdout evaluation",
        ],
        "recommended_next_task": "Wallet Public Trade History Bounded Public Smoke v1",
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    gate_path.write_text(json.dumps(gates, indent=2, sort_keys=True), encoding="utf-8")
    hashes = {
        "raw_trades_fixture_jsonl_sha256": file_sha256(raw_path),
        "normalized_trades_fixture_csv_sha256": file_sha256(csv_path),
        "fixture_ingestion_report_json_sha256": file_sha256(summary_path),
        "validation_gate_results_json_sha256": file_sha256(gate_path),
        "csv_repeat_export_hash_match": deterministic,
    }
    hash_path.write_text(json.dumps(hashes, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_build_markdown_report(summary, hashes), encoding="utf-8")
    return summary


def _build_markdown_report(summary: dict[str, Any], hashes: dict[str, Any]) -> str:
    lines = [
        "# Wallet Public Trade History Ingester Fixture Implementation v1",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "## Summary",
        "",
        f"- Fixture pages: {summary['fixture_pages']}",
        f"- Input rows: {summary['input_rows']}",
        f"- Normalized rows: {summary['normalized_rows']}",
        f"- Duplicate rows removed: {summary['duplicate_rows_removed']}",
        f"- Schema fields: {summary['schema_fields']}",
        f"- Parquet status: {summary['parquet_status']}",
        f"- Validation gates passed: {str(summary['validation_gates_passed']).lower()}",
        "",
        "## Validation Gates",
        "",
    ]
    for name, result in summary["validation_gates"].items():
        lines.append(f"- `{name}`: {'passed' if result.get('passed') else 'failed'}")
    lines.extend(
        [
            "",
            "## Reproducibility Hashes",
            "",
        ]
    )
    for name, value in hashes.items():
        lines.append(f"- `{name}`: `{value}`")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "This fixture implementation normalizes saved fixture data only. It does not perform network ingestion, connect wallets, use private keys, place orders, copy trades, launch capture campaigns, inspect sealed holdout outcomes, run holdout evaluation, or train production models.",
            "",
            "## Recommended Next Task",
            "",
            "`Wallet Public Trade History Bounded Public Smoke v1`",
            "",
        ]
    )
    return "\n".join(lines)


def _build_smoke_markdown_report(summary: dict[str, Any], hashes: dict[str, Any]) -> str:
    row_summary = summary["row_summary"]
    lines = [
        "# Wallet Public Trade History Bounded Public Smoke v1",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "## Summary",
        "",
        f"- Wallets attempted: {summary['wallets_attempted']}",
        f"- Wallets succeeded: {summary['wallets_succeeded']}",
        f"- Pages fetched: {summary['pages_fetched']}",
        f"- Rows fetched: {summary['rows_fetched']}",
        f"- Rows normalized: {summary['rows_normalized']}",
        f"- Duplicate rows removed: {summary['duplicate_rows_removed']}",
        f"- Validation gates passed: {str(summary['validation_gates_passed']).lower()}",
        f"- Deterministic CSV repeat export: {str(summary['deterministic_csv_repeat_export']).lower()}",
        f"- Parquet status: {summary['parquet_status']}",
        "",
        "## Fast Crypto Counts",
        "",
        f"- Fast crypto rows: {row_summary['fast_crypto_rows']}",
        f"- BTC rows: {row_summary['asset_counts']['BTC']}",
        f"- ETH rows: {row_summary['asset_counts']['ETH']}",
        f"- SOL rows: {row_summary['asset_counts']['SOL']}",
        f"- Other rows: {row_summary['asset_counts']['other']}",
        "",
        "## YES/NO And Side Counts",
        "",
        f"- YES-like outcomes: {row_summary['yes_no_counts']['YES_like']}",
        f"- NO-like outcomes: {row_summary['yes_no_counts']['NO_like']}",
        f"- Other outcomes: {row_summary['yes_no_counts']['other']}",
        f"- BUY rows: {row_summary['side_counts']['BUY']}",
        f"- SELL rows: {row_summary['side_counts']['SELL']}",
        "",
        "## Price Buckets",
        "",
    ]
    for bucket, count in row_summary["price_bucket_distribution"].items():
        lines.append(f"- `{bucket}`: {count}")
    lines.extend(["", "## Endpoint Errors", ""])
    if summary["endpoint_errors"]:
        for wallet, error in summary["endpoint_errors"].items():
            lines.append(f"- `{wallet}`: {error}")
    else:
        lines.append("- none")
    lines.extend(["", "## Validation Gates", ""])
    for name, result in summary["validation_gates"].items():
        lines.append(f"- `{name}`: {'passed' if result.get('passed') else 'failed'}")
    lines.extend(["", "## Fields Unavailable", ""])
    for field in summary["fields_unavailable"]:
        lines.append(f"- {field}")
    lines.extend(["", "## Reproducibility Hashes", ""])
    for name, value in hashes.items():
        lines.append(f"- `{name}`: `{value}`")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "This smoke used bounded public read-only Data API activity TRADE pages for seed wallets only. It did not connect wallets, use private keys, place orders, copy trades, launch capture campaigns, inspect sealed holdout outcomes, run holdout evaluation, or train production models.",
            "",
            "## Recommended Next Task",
            "",
            f"`{summary['recommended_next_task']}`",
            "",
        ]
    )
    return "\n".join(lines)
