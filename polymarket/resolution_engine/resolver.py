from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

from polymarket.edge_engine_v4.market_discovery import parse_json_array

from .models import MarketDescriptor, ResolutionRecord


class GammaResolutionClient:
    BASE_URL = "https://gamma-api.polymarket.com"

    def __init__(self, timeout: float = 15.0) -> None:
        self.timeout = timeout

    def fetch_event(self, slug: str) -> dict[str, Any] | None:
        url = f"{self.BASE_URL}/events?{urllib.parse.urlencode({'slug': slug})}"
        request = urllib.request.Request(
            url, headers={"User-Agent": "forgeview-resolution-engine/1.0"}
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, list) or not payload:
            return None
        return payload[0]


def parse_resolution(
    descriptor: MarketDescriptor,
    event: dict[str, Any] | None,
    retrieval_timestamp: datetime | None = None,
) -> ResolutionRecord:
    retrieved = retrieval_timestamp or datetime.now(timezone.utc)
    if not event:
        return _record(descriptor, retrieved, status="missing", reason="event_not_found")
    markets = event.get("markets")
    if not isinstance(markets, list):
        return _record(descriptor, retrieved, status="malformed", reason="missing_markets")
    matching = [
        market for market in markets
        if str(market.get("conditionId", "")) == descriptor.market_id
    ]
    if len(matching) != 1:
        return _record(
            descriptor,
            retrieved,
            status="missing" if not matching else "ambiguous",
            reason="condition_id_not_found" if not matching else "duplicate_condition_id",
        )
    market = matching[0]
    if not bool(market.get("closed")):
        return _record(descriptor, retrieved, status="unresolved", reason="market_not_closed")
    if bool(market.get("cancelled", False)):
        return _record(descriptor, retrieved, status="cancelled", reason="market_cancelled")
    resolution_status = str(market.get("umaResolutionStatus", "")).lower()
    automatically_resolved = bool(market.get("automaticallyResolved", False))
    if resolution_status != "resolved" and not automatically_resolved:
        return _record(
            descriptor, retrieved, status="unresolved",
            reason=f"resolution_status:{resolution_status or 'missing'}",
        )
    try:
        outcomes = parse_json_array(market.get("outcomes"))
        prices = [float(value) for value in parse_json_array(market.get("outcomePrices"))]
    except (ValueError, TypeError, json.JSONDecodeError):
        return _record(descriptor, retrieved, status="malformed", reason="invalid_outcomes")
    if len(outcomes) != 2 or len(prices) != 2:
        return _record(descriptor, retrieved, status="malformed", reason="non_binary_market")
    mapping = {name.strip().lower(): price for name, price in zip(outcomes, prices)}
    if set(mapping) != {"up", "down"}:
        return _record(
            descriptor, retrieved, status="malformed",
            reason="outcomes_are_not_up_down",
        )
    up, down = mapping["up"], mapping["down"]
    if _terminal(up, 1.0) and _terminal(down, 0.0):
        outcome, name = 1, "UP"
    elif _terminal(up, 0.0) and _terminal(down, 1.0):
        outcome, name = 0, "DOWN"
    else:
        return _record(
            descriptor, retrieved, status="ambiguous",
            reason=f"non_terminal_prices:{up:.6f},{down:.6f}",
        )
    resolution_timestamp = _timestamp(
        market.get("closedTime")
        or market.get("umaEndDate")
        or event.get("closedTime")
        or descriptor.window_end.isoformat()
    )
    source = str(
        market.get("resolutionSource")
        or event.get("resolutionSource")
        or "Polymarket Gamma API"
    )
    return ResolutionRecord(
        market_id=descriptor.market_id,
        asset=descriptor.asset,
        question=descriptor.question,
        slug=descriptor.slug,
        outcome=outcome,
        outcome_name=name,
        resolution_timestamp=resolution_timestamp,
        resolution_source=source,
        retrieval_timestamp=retrieved,
        status="resolved",
        reason="",
    )


def _terminal(value: float, target: float) -> bool:
    return abs(value - target) <= 0.001


def _timestamp(value: str) -> datetime:
    normalized = value.replace(" ", "T", 1).replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _record(
    descriptor: MarketDescriptor,
    retrieved: datetime,
    status: str,
    reason: str,
) -> ResolutionRecord:
    return ResolutionRecord(
        market_id=descriptor.market_id,
        asset=descriptor.asset,
        question=descriptor.question,
        slug=descriptor.slug,
        outcome=None,
        outcome_name="",
        resolution_timestamp=None,
        resolution_source="Polymarket Gamma API",
        retrieval_timestamp=retrieved,
        status=status,
        reason=reason,
    )
