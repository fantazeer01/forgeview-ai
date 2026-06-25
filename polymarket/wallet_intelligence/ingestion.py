"""Normalize public Polymarket wallet data into research-only artifacts."""

from __future__ import annotations

import csv
import html
import json
import math
import re
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable

from .client import PolymarketPublicClient, PublicResponse
from .schema import WatchedWallet


ADDRESS_RE = re.compile(r"^@?(0x[a-fA-F0-9]{40})$")
ANY_ADDRESS_RE = re.compile(r"0x[a-fA-F0-9]{40}")
UNAVAILABLE = "unavailable_from_public_profile_snapshot"
PUBLIC_ENDPOINTS = {
    "positions": "https://data-api.polymarket.com/positions",
    "closed_positions": "https://data-api.polymarket.com/closed-positions",
    "activity": "https://data-api.polymarket.com/activity",
    "value": "https://data-api.polymarket.com/value",
    "traded": "https://data-api.polymarket.com/traded",
}


def load_watched_wallets(path: Path) -> list[WatchedWallet]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            WatchedWallet(
                wallet_id=(row.get("wallet_id") or "").strip(),
                profile_url=(row.get("profile_url") or "").strip(),
                label=(row.get("label") or "").strip(),
                source=(row.get("source") or "").strip(),
                notes=(row.get("notes") or "").strip(),
            )
            for row in reader
            if (row.get("wallet_id") or "").strip()
        ]


def resolve_wallet_id(seed: WatchedWallet, client: PolymarketPublicClient) -> tuple[str | None, str]:
    direct = ADDRESS_RE.match(seed.wallet_id)
    if direct:
        return direct.group(1), "seed_wallet_id"

    url_tail = seed.profile_url.rstrip("/").split("/")[-1]
    tail_match = ADDRESS_RE.match(url_tail)
    if tail_match:
        return tail_match.group(1), "profile_url_tail"

    try:
        page = client.get_text(seed.profile_url)
    except Exception as exc:  # pragma: no cover - exercised by network failures
        return None, f"profile_page_unavailable: {exc}"

    resolved = _resolve_from_profile_html(seed.wallet_id, page.payload)
    if resolved:
        return resolved, "profile_page_embedded_address"
    return None, "no_confident_public_wallet_address_found"


def _resolve_from_profile_html(seed_id: str, text: str) -> str | None:
    next_data = _extract_next_data(text)
    if next_data is not None:
        candidates = _profile_address_candidates(next_data, seed_id)
        if candidates:
            return candidates[0]

    addresses = ANY_ADDRESS_RE.findall(text)
    unique = []
    for address in addresses:
        normalized = address.lower()
        if normalized not in unique:
            unique.append(normalized)
    return unique[0] if len(unique) == 1 else None


def _extract_next_data(text: str) -> Any | None:
    marker = '<script id="__NEXT_DATA__" type="application/json"'
    start = text.find(marker)
    if start < 0:
        return None
    start = text.find(">", start)
    end = text.find("</script>", start)
    if start < 0 or end < 0:
        return None
    raw = html.unescape(text[start + 1 : end])
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _profile_address_candidates(value: Any, seed_id: str) -> list[str]:
    seed_norm = seed_id.lstrip("@").lower()
    preferred: list[str] = []
    fallback: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            object_text = json.dumps(node, sort_keys=True, default=str).lower()
            for key in ("proxyWallet", "proxy_wallet", "address", "wallet", "user"):
                address = node.get(key)
                if isinstance(address, str) and ANY_ADDRESS_RE.fullmatch(address):
                    target = preferred if seed_norm and seed_norm in object_text else fallback
                    target.append(address.lower())
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(value)
    ordered: list[str] = []
    for address in preferred + fallback:
        if address not in ordered:
            ordered.append(address)
    return ordered


def ingest_wallets(
    input_path: Path,
    output_dir: Path,
    *,
    client: PolymarketPublicClient | None = None,
    position_limit: int = 50,
    activity_limit: int = 50,
    retrieved_at: str | None = None,
) -> dict[str, Any]:
    client = client or PolymarketPublicClient()
    retrieved_at = retrieved_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)

    seeds = load_watched_wallets(input_path)
    raw_records: list[dict[str, Any]] = []
    profile_rows: list[dict[str, Any]] = []
    position_rows: list[dict[str, Any]] = []

    for seed in seeds:
        wallet_address, resolution_note = resolve_wallet_id(seed, client)
        endpoint_records: dict[str, Any] = {}
        source_urls: dict[str, str] = {}
        endpoint_errors: dict[str, str] = {}

        if wallet_address:
            for endpoint_name, fetch in (
                ("positions", lambda: client.positions(wallet_address, position_limit)),
                ("closed_positions", lambda: client.closed_positions(wallet_address, position_limit)),
                ("activity", lambda: client.activity(wallet_address, activity_limit)),
                ("value", lambda: client.value(wallet_address)),
                ("traded", lambda: client.traded(wallet_address)),
            ):
                try:
                    response = fetch()
                    endpoint_records[endpoint_name] = response.payload
                    source_urls[endpoint_name] = response.url
                except Exception as exc:  # pragma: no cover - network-specific
                    endpoint_records[endpoint_name] = []
                    endpoint_errors[endpoint_name] = str(exc)
        else:
            endpoint_errors["resolution"] = resolution_note

        raw_records.append(
            {
                "seed": asdict(seed),
                "resolved_wallet_id": wallet_address,
                "resolution_note": resolution_note,
                "retrieved_at": retrieved_at,
                "source_urls": source_urls,
                "endpoint_errors": endpoint_errors,
                "raw": endpoint_records,
            }
        )
        profile, positions = normalize_wallet_snapshot(
            seed=seed,
            resolved_wallet_id=wallet_address,
            resolution_note=resolution_note,
            endpoint_records=endpoint_records,
            endpoint_errors=endpoint_errors,
            source_urls=source_urls,
            retrieved_at=retrieved_at,
            position_limit=position_limit,
            activity_limit=activity_limit,
        )
        profile_rows.append(profile)
        position_rows.extend(positions)

    summary = build_summary(profile_rows, position_rows, input_path, output_dir, retrieved_at)
    write_outputs(output_dir, raw_records, profile_rows, position_rows, summary)
    return summary


def normalize_wallet_snapshot(
    *,
    seed: WatchedWallet,
    resolved_wallet_id: str | None,
    resolution_note: str,
    endpoint_records: dict[str, Any],
    endpoint_errors: dict[str, str],
    source_urls: dict[str, str],
    retrieved_at: str,
    position_limit: int,
    activity_limit: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    active_positions = _as_list(endpoint_records.get("positions"))
    closed_positions = _as_list(endpoint_records.get("closed_positions"))
    all_positions = [("active", item) for item in active_positions] + [
        ("closed", item) for item in closed_positions
    ]

    position_rows = [
        normalize_position(seed, resolved_wallet_id, status, item, source_urls, retrieved_at)
        for status, item in all_positions
    ]

    pnl_values = [_num(item.get("realizedPnl")) for item in closed_positions]
    cash_values = [_num(item.get("cashPnl")) for item in active_positions]
    total_pnl = _sum_available(pnl_values + cash_values)
    biggest_win = _max_available(pnl_values + cash_values)
    avg_entry = _mean_available([_num(item.get("avgPrice")) for _, item in all_positions])
    avg_exit = _mean_available([_num(item.get("curPrice")) for item in closed_positions])
    market_types = Counter(row["market_type"] for row in position_rows)
    exposure = Counter(row["asset_exposure"] for row in position_rows)
    outcomes = Counter((row["outcome"] or "unknown").lower() for row in position_rows)
    yes_count = sum(outcomes[key] for key in ("yes", "up"))
    no_count = sum(outcomes[key] for key in ("no", "down"))
    fast_crypto_count = sum(1 for row in position_rows if row["is_fast_crypto_market"] == "true")
    weather_count = sum(1 for row in position_rows if row["market_type"] == "weather")
    sizing = summarize_sizing(all_positions)
    cheap = summarize_cheap_entries(all_positions)
    repeated = summarize_repeated_patterns(position_rows)
    holding = summarize_holding_evidence(closed_positions)
    late_entry = summarize_late_entry(endpoint_records.get("activity"), activity_limit)
    traded_count = _extract_traded_count(endpoint_records.get("traded"))
    data_notes = data_availability_notes(
        resolved_wallet_id,
        resolution_note,
        endpoint_errors,
        active_positions,
        closed_positions,
        position_limit,
    )
    copyability_score, copyability_notes = copyability_assessment(
        fast_crypto_count=fast_crypto_count,
        position_count=len(position_rows),
        avg_entry=avg_entry,
        late_entry=late_entry,
        unresolved=resolved_wallet_id is None,
    )

    profile = {
        "wallet_id": resolved_wallet_id or seed.wallet_id,
        "seed_wallet_id": seed.wallet_id,
        "profile_url": seed.profile_url,
        "label": seed.label,
        "source": seed.source,
        "notes": seed.notes,
        "resolved_wallet_address": resolved_wallet_id or "",
        "wallet_resolution_note": resolution_note,
        "retrieved_at": retrieved_at,
        "total_pnl": _fmt(total_pnl),
        "prediction_count": traded_count,
        "biggest_win": _fmt(biggest_win),
        "active_positions_count": len(active_positions) if resolved_wallet_id else "",
        "closed_positions_count": len(closed_positions) if resolved_wallet_id else "",
        "market_types": _counter_json(market_types),
        "btc_exposure": exposure.get("BTC", 0),
        "eth_exposure": exposure.get("ETH", 0),
        "sol_exposure": exposure.get("SOL", 0),
        "fast_crypto_positions_count": fast_crypto_count,
        "weather_or_other_positions_count": weather_count + sum(
            count for key, count in market_types.items() if key not in ("fast_crypto", "weather")
        ),
        "yes_position_count": yes_count,
        "no_position_count": no_count,
        "yes_no_distribution": _counter_json(outcomes),
        "average_entry_price": _fmt(avg_entry),
        "average_exit_or_resolution_price": _fmt(avg_exit),
        "average_holding_time_seconds": UNAVAILABLE,
        "position_sizing_summary": sizing,
        "repeated_market_patterns": repeated,
        "late_entry_behavior": late_entry,
        "cheap_side_buying_behavior": cheap,
        "hold_to_resolution_vs_exit_before_expiry": holding,
        "drawdown_behavior": UNAVAILABLE,
        "copyability_score": copyability_score,
        "copyability_risk_notes": copyability_notes,
        "data_availability_notes": data_notes,
        "source_urls": json.dumps(source_urls, sort_keys=True),
    }
    return profile, position_rows


def normalize_position(
    seed: WatchedWallet,
    resolved_wallet_id: str | None,
    status: str,
    item: dict[str, Any],
    source_urls: dict[str, str],
    retrieved_at: str,
) -> dict[str, Any]:
    title = str(item.get("title") or "")
    slug = str(item.get("slug") or item.get("eventSlug") or "")
    market_type = classify_market_type(title, slug)
    exposure = classify_exposure(title, slug)
    avg_price = _num(item.get("avgPrice"))
    return {
        "wallet_id": resolved_wallet_id or seed.wallet_id,
        "profile_url": seed.profile_url,
        "position_status": status,
        "source_endpoint": "positions" if status == "active" else "closed_positions",
        "title": title,
        "slug": slug,
        "event_slug": item.get("eventSlug") or "",
        "asset": item.get("asset") or "",
        "condition_id": item.get("conditionId") or "",
        "outcome": item.get("outcome") or "",
        "avg_price": _fmt(avg_price),
        "cur_price": _fmt(_num(item.get("curPrice"))),
        "realized_pnl": _fmt(_num(item.get("realizedPnl"))),
        "cash_pnl": _fmt(_num(item.get("cashPnl"))),
        "total_bought": _fmt(_num(item.get("totalBought"))),
        "size": _fmt(_num(item.get("size"))),
        "initial_value": _fmt(_num(item.get("initialValue"))),
        "current_value": _fmt(_num(item.get("currentValue"))),
        "timestamp": item.get("timestamp") or "",
        "end_date": item.get("endDate") or "",
        "market_type": market_type,
        "asset_exposure": exposure,
        "is_fast_crypto_market": str(market_type == "fast_crypto").lower(),
        "is_cheap_entry": str(avg_price is not None and avg_price <= 0.2).lower(),
        "source_url": source_urls.get("positions" if status == "active" else "closed_positions", ""),
        "retrieved_at": retrieved_at,
    }


def classify_market_type(title: str, slug: str) -> str:
    text = f"{title} {slug}".lower()
    has_crypto = any(token in text for token in ("bitcoin", "btc", "ethereum", "eth", "solana", " sol-", " sol "))
    has_fast = any(token in text for token in ("up or down", "updown", "15m", "5m", "1h", "hour"))
    if has_crypto and has_fast:
        return "fast_crypto"
    if any(token in text for token in ("weather", "temperature", "rain", "snow")):
        return "weather"
    if has_crypto:
        return "crypto_other"
    return "other"


def classify_exposure(title: str, slug: str) -> str:
    text = f"{title} {slug}".lower()
    if "bitcoin" in text or "btc" in text:
        return "BTC"
    if "ethereum" in text or re.search(r"\beth\b", text):
        return "ETH"
    if "solana" in text or re.search(r"\bsol\b", text):
        return "SOL"
    return "OTHER"


def summarize_sizing(all_positions: list[tuple[str, dict[str, Any]]]) -> str:
    values = [_num(item.get("totalBought")) for _, item in all_positions]
    available = [value for value in values if value is not None and math.isfinite(value)]
    if not available:
        return UNAVAILABLE
    return json.dumps(
        {
            "count": len(available),
            "min": round(min(available), 6),
            "median": round(median(available), 6),
            "mean": round(mean(available), 6),
            "max": round(max(available), 6),
        },
        sort_keys=True,
    )


def summarize_cheap_entries(all_positions: list[tuple[str, dict[str, Any]]]) -> str:
    prices = [_num(item.get("avgPrice")) for _, item in all_positions]
    available = [price for price in prices if price is not None]
    if not available:
        return UNAVAILABLE
    cheap = sum(1 for price in available if price <= 0.20)
    ten_to_twenty = sum(1 for price in available if 0.10 <= price <= 0.20)
    return json.dumps(
        {
            "avg_price_count": len(available),
            "cheap_le_20c_count": cheap,
            "ten_to_twenty_cent_count": ten_to_twenty,
            "cheap_le_20c_share": round(cheap / len(available), 6),
        },
        sort_keys=True,
    )


def summarize_repeated_patterns(position_rows: list[dict[str, Any]]) -> str:
    if not position_rows:
        return UNAVAILABLE
    by_type = Counter(row["market_type"] for row in position_rows)
    by_exposure = Counter(row["asset_exposure"] for row in position_rows)
    examples = [row["slug"] for row in position_rows[:5] if row.get("slug")]
    return json.dumps(
        {"market_types": by_type, "exposures": by_exposure, "recent_examples": examples},
        sort_keys=True,
    )


def summarize_holding_evidence(closed_positions: list[dict[str, Any]]) -> str:
    if not closed_positions:
        return UNAVAILABLE
    resolution_like = sum(1 for item in closed_positions if _num(item.get("curPrice")) in (0.0, 1.0))
    return json.dumps(
        {
            "closed_positions_with_resolution_like_price": resolution_like,
            "closed_positions_count": len(closed_positions),
            "note": "Closed-position snapshots expose resolution-like prices but not enough entry/exit event history to prove hold-to-expiry.",
        },
        sort_keys=True,
    )


def summarize_late_entry(activity_payload: Any, activity_limit: int) -> str:
    activities = _as_list(activity_payload)
    trade_like = [item for item in activities if str(item.get("type") or "").lower() in {"trade", "buy", "sell"}]
    if not trade_like:
        return f"{UNAVAILABLE}: no trade-like activity rows in first {activity_limit} public activity records"
    late_count = 0
    analyzable = 0
    for item in trade_like:
        timestamp = _num(item.get("timestamp"))
        end_ts = _parse_end_ts(item.get("endDate"))
        if timestamp is None or end_ts is None:
            continue
        analyzable += 1
        if 0 <= end_ts - timestamp <= 180:
            late_count += 1
    if not analyzable:
        return f"{UNAVAILABLE}: trade-like public activity rows lack endDate or timestamp"
    return json.dumps({"trade_like_rows": len(trade_like), "analyzable_rows": analyzable, "late_3m_count": late_count})


def copyability_assessment(
    *,
    fast_crypto_count: int,
    position_count: int,
    avg_entry: float | None,
    late_entry: str,
    unresolved: bool,
) -> tuple[int, str]:
    if unresolved:
        return 0, "Not copyable from current data because the public profile could not be resolved to a wallet address."
    if position_count == 0:
        return 5, "Not copyable from current data because no public positions were returned."
    score = 15
    if fast_crypto_count:
        score += min(30, fast_crypto_count * 3)
    if avg_entry is not None and avg_entry <= 0.35:
        score += 10
    if UNAVAILABLE in late_entry:
        score -= 10
    score = max(0, min(60, score))
    notes = (
        "Research-only score capped at 60 because public snapshots do not expose complete entry timing, "
        "fill sequence, liquidity, or observation delay."
    )
    return score, notes


def data_availability_notes(
    resolved_wallet_id: str | None,
    resolution_note: str,
    endpoint_errors: dict[str, str],
    active_positions: list[dict[str, Any]],
    closed_positions: list[dict[str, Any]],
    position_limit: int,
) -> str:
    notes = [f"wallet_resolution={resolution_note}"]
    if not resolved_wallet_id:
        notes.append("position endpoints skipped because profile address was unavailable")
    if endpoint_errors:
        notes.append(f"endpoint_errors={json.dumps(endpoint_errors, sort_keys=True)}")
    notes.append("average_holding_time and drawdown unavailable from positions/closed-positions snapshots")
    notes.append("late-entry behavior requires deeper trade/activity history")
    if len(closed_positions) >= position_limit:
        notes.append(f"closed_positions may be truncated at public snapshot limit {position_limit}")
    if not active_positions and not closed_positions and resolved_wallet_id:
        notes.append("public endpoints returned no positions for this wallet")
    return "; ".join(notes)


def build_summary(
    profile_rows: list[dict[str, Any]],
    position_rows: list[dict[str, Any]],
    input_path: Path,
    output_dir: Path,
    retrieved_at: str,
) -> dict[str, Any]:
    data_by_wallet = {
        row["wallet_id"]: {
            "profile_url": row["profile_url"],
            "resolved_wallet_address": row["resolved_wallet_address"],
            "active_positions_count": row["active_positions_count"],
            "closed_positions_count": row["closed_positions_count"],
            "fast_crypto_positions_count": row["fast_crypto_positions_count"],
            "market_types": row["market_types"],
            "copyability_score": row["copyability_score"],
            "data_availability_notes": row["data_availability_notes"],
        }
        for row in profile_rows
    }
    fast_wallets = [
        row["wallet_id"]
        for row in profile_rows
        if _int(row.get("fast_crypto_positions_count")) > 0
    ]
    weather_wallets = [
        row["wallet_id"]
        for row in profile_rows
        if "weather" in str(row.get("market_types", "")).lower()
    ]
    enough_visible = [
        row["wallet_id"]
        for row in profile_rows
        if _int(row.get("closed_positions_count")) + _int(row.get("active_positions_count")) >= 10
    ]
    copyable = [
        row["wallet_id"]
        for row in profile_rows
        if _int(row.get("copyability_score")) >= 30
    ]
    return {
        "task": "Wallet Intelligence Data Ingestion v1",
        "retrieved_at": retrieved_at,
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "public_source_endpoints": PUBLIC_ENDPOINTS,
        "wallets_attempted": len(profile_rows),
        "wallets_resolved": sum(1 for row in profile_rows if row.get("resolved_wallet_address")),
        "wallets_with_positions": sum(
            1
            for row in profile_rows
            if _int(row.get("active_positions_count")) + _int(row.get("closed_positions_count")) > 0
        ),
        "position_rows": len(position_rows),
        "fast_market_crypto_wallets": fast_wallets,
        "weather_or_other_wallets": weather_wallets,
        "wallets_with_enough_visible_data_for_strategy_inference": enough_visible,
        "research_only_copyable_wallets": copyable,
        "wallets_requiring_deeper_transaction_or_history_data": [
            row["wallet_id"] for row in profile_rows
        ],
        "data_availability_by_wallet": data_by_wallet,
        "biggest_data_gaps": [
            "Full trade/fill history is not captured by first-page public profile snapshots.",
            "Average holding time is unavailable without linked entry and exit timestamps.",
            "Late-entry and Binance-lag behavior require timestamped trade history plus external price series.",
            "Copyability cannot be treated as executable because observation delay, liquidity, and fill priority are unknown.",
        ],
        "recommended_next_task": "Wallet Intelligence Behavior Metrics v1",
    }


def write_outputs(
    output_dir: Path,
    raw_records: list[dict[str, Any]],
    profile_rows: list[dict[str, Any]],
    position_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    with (output_dir / "wallets_raw.jsonl").open("w", encoding="utf-8") as handle:
        for record in raw_records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    _write_csv(output_dir / "wallet_profiles.csv", profile_rows)
    _write_csv(output_dir / "wallet_positions.csv", position_rows)
    (output_dir / "wallet_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "ingestion_report.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "ingestion_report.md").write_text(render_report(summary), encoding="utf-8")


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Wallet Intelligence Data Ingestion v1",
        "",
        f"Retrieved at: {summary['retrieved_at']}",
        "",
        "This report uses public Polymarket profile/data endpoints only. It contains no wallet/private-key, order-placement, live-trading, trade-copying, holdout-evaluation, or capture-campaign capability.",
        "",
        "## Summary",
        "",
        f"- Wallets attempted: {summary['wallets_attempted']}",
        f"- Wallets resolved to public addresses: {summary['wallets_resolved']}",
        f"- Wallets with visible positions: {summary['wallets_with_positions']}",
        f"- Normalized position rows: {summary['position_rows']}",
        f"- Fast-market crypto wallets: {', '.join(summary['fast_market_crypto_wallets']) or 'none'}",
        f"- Weather/other wallets: {', '.join(summary['weather_or_other_wallets']) or 'none'}",
        f"- Enough visible data for strategy inference: {', '.join(summary['wallets_with_enough_visible_data_for_strategy_inference']) or 'none'}",
        f"- Research-only copyable wallets: {', '.join(summary['research_only_copyable_wallets']) or 'none'}",
        "",
        "## Data Availability By Wallet",
        "",
    ]
    for wallet_id, details in summary["data_availability_by_wallet"].items():
        lines.extend(
            [
                f"### {wallet_id}",
                "",
                f"- Profile URL: {details['profile_url']}",
                f"- Resolved wallet address: {details['resolved_wallet_address'] or 'unresolved'}",
                f"- Active positions: {details['active_positions_count']}",
                f"- Closed positions: {details['closed_positions_count']}",
                f"- Fast crypto positions: {details['fast_crypto_positions_count']}",
                f"- Market types: `{details['market_types']}`",
                f"- Copyability score: {details['copyability_score']}",
                f"- Notes: {details['data_availability_notes']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Biggest Data Gaps",
            "",
            *[f"- {gap}" for gap in summary["biggest_data_gaps"]],
            "",
            f"## Recommended Next Task",
            "",
            summary["recommended_next_task"],
            "",
        ]
    )
    return "\n".join(lines)


def inspect_outputs(output_dir: Path) -> dict[str, Any]:
    summary_path = output_dir / "wallet_summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"missing wallet summary: {summary_path}")
    return json.loads(summary_path.read_text(encoding="utf-8"))


def summarize_outputs(output_dir: Path) -> str:
    summary = inspect_outputs(output_dir)
    return render_report(summary)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if rows:
        fieldnames = list(rows[0].keys())
    else:
        fieldnames = ["wallet_id"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _as_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _num(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _int(value: Any) -> int:
    try:
        if value in (None, ""):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _fmt(value: float | None) -> str:
    if value is None:
        return UNAVAILABLE
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _sum_available(values: Iterable[float | None]) -> float | None:
    available = [value for value in values if value is not None]
    return sum(available) if available else None


def _max_available(values: Iterable[float | None]) -> float | None:
    available = [value for value in values if value is not None]
    return max(available) if available else None


def _mean_available(values: Iterable[float | None]) -> float | None:
    available = [value for value in values if value is not None]
    return mean(available) if available else None


def _counter_json(counter: Counter[str]) -> str:
    return json.dumps(dict(counter), sort_keys=True)


def _parse_end_ts(value: Any) -> float | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _extract_traded_count(payload: Any) -> str:
    if isinstance(payload, dict) and "traded" in payload:
        return str(payload["traded"])
    return UNAVAILABLE
