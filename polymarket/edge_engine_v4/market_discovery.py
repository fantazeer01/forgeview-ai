from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Any

from .config import SUPPORTED_ASSETS
from .opportunity import CryptoMarket, SkippedMarket


ASSET_PATTERNS = {
    "BTC": re.compile(r"(?i)(?:\bBTC\b|\bBitcoin\b)"),
    "ETH": re.compile(r"(?i)(?:\bETH\b|\bEthereum\b)"),
    "SOL": re.compile(r"(?i)(?:\bSOL\b|\bSolana\b)"),
}
FIVE_MINUTE_PATTERN = re.compile(r"(?i)(?:5[\s-]*(?:minute|min)|5m|updown-5m)")
UP_DOWN_PATTERN = re.compile(r"(?i)\b(?:up|down|higher|lower)\b")


@dataclass(frozen=True)
class DiscoveryFailure:
    timestamp: datetime
    endpoint_url: str
    exception_type: str
    exception_message: str


def parse_json_array(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        parsed = json.loads(value)
        return [str(item) for item in parsed]
    return []


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def identify_asset(text: str) -> str | None:
    matches = [asset for asset, pattern in ASSET_PATTERNS.items() if pattern.search(text)]
    return matches[0] if len(matches) == 1 else None


class PolymarketMarketDiscovery:
    BASE_URL = "https://gamma-api.polymarket.com"

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout
        self.failures: list[DiscoveryFailure] = []

    def discover(
        self,
        assets: tuple[str, ...],
        now: datetime | None = None,
    ) -> tuple[list[CryptoMarket], list[SkippedMarket]]:
        now = now or datetime.now(timezone.utc)
        candidates: list[dict[str, Any]] = []
        seen: set[str] = set()
        self.failures = []

        def request(path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
            url = self._url(path, params)
            try:
                return self._get(path, params)
            except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
                self.failures.append(DiscoveryFailure(
                    timestamp=now,
                    endpoint_url=url,
                    exception_type=type(exc).__name__,
                    exception_message=str(exc),
                ))
                return []

        requests: list[tuple[str, dict[str, Any]]] = []
        anchor = int(now.timestamp()) // 300 * 300
        for asset in assets:
            prefix = {"BTC": "btc", "ETH": "eth", "SOL": "sol"}[asset]
            for offset in (-300, 0, 300):
                slug = f"{prefix}-updown-5m-{anchor + offset}"
                requests.append(("/events", {"slug": slug}))
        requests.append((
            "/events",
            {
                "active": "true", "closed": "false", "limit": 200,
                "order": "volume_24hr", "ascending": "false",
            },
        ))
        with ThreadPoolExecutor(
            max_workers=min(10, len(requests)),
            thread_name_prefix="gamma-discovery",
        ) as executor:
            responses = list(executor.map(lambda row: request(*row), requests))
        for index, events in enumerate(responses):
            broad = index == len(responses) - 1
            for event in events:
                if not broad:
                    candidates.extend(event.get("markets", []))
                    continue
                for market in event.get("markets", []):
                    text = (
                        f"{event.get('title', '')} "
                        f"{market.get('question', '')} "
                        f"{market.get('slug', '')}"
                    )
                    if (
                        identify_asset(text) in assets
                        and FIVE_MINUTE_PATTERN.search(text)
                    ):
                        candidates.append(market)

        markets: list[CryptoMarket] = []
        skipped: list[SkippedMarket] = []
        for raw in candidates:
            market_id = str(raw.get("conditionId") or raw.get("id") or "")
            if not market_id or market_id in seen:
                continue
            seen.add(market_id)
            parsed, reason, asset = self._parse_market(raw, assets)
            if parsed:
                if parsed.window_end <= now:
                    skipped.append(SkippedMarket(
                        timestamp=now,
                        market_id=parsed.market_id,
                        asset=parsed.asset,
                        question=parsed.question,
                        reason="window_expired",
                    ))
                else:
                    markets.append(parsed)
            else:
                skipped.append(SkippedMarket(
                    timestamp=now,
                    market_id=market_id or "unknown",
                    asset=asset or "UNKNOWN",
                    question=str(raw.get("question") or ""),
                    reason=reason,
                ))
        return sorted(markets, key=lambda row: (row.asset, row.window_end)), skipped

    def _parse_market(
        self,
        raw: dict[str, Any],
        assets: tuple[str, ...],
    ) -> tuple[CryptoMarket | None, str, str | None]:
        text = f"{raw.get('question', '')} {raw.get('slug', '')}"
        asset = identify_asset(text)
        if asset not in assets:
            return None, "unsupported_or_ambiguous_asset", asset
        slug_match = re.search(r"updown-5m-(\d+)", str(raw.get("slug", "")))
        if slug_match:
            start = datetime.fromtimestamp(int(slug_match.group(1)), tz=timezone.utc)
            end = start + timedelta(minutes=5)
        else:
            start = parse_timestamp(raw.get("startDate"))
            end = parse_timestamp(raw.get("endDate"))
        if not start or not end:
            return None, "missing_window", asset
        duration = (end - start).total_seconds()
        if not 240 <= duration <= 360:
            return None, f"not_five_minute_window:{duration:.0f}s", asset
        if not UP_DOWN_PATTERN.search(text) and "updown-5m" not in text.lower():
            return None, "not_up_down_market", asset
        outcomes = parse_json_array(raw.get("outcomes"))
        tokens = parse_json_array(raw.get("clobTokenIds"))
        if len(outcomes) != 2 or len(tokens) != 2:
            return None, "missing_binary_token_mapping", asset
        mapping = {name.strip().lower(): token for name, token in zip(outcomes, tokens)}
        yes = mapping.get("up") or mapping.get("yes")
        no = mapping.get("down") or mapping.get("no")
        if not yes or not no:
            return None, "unrecognized_outcomes", asset
        active = bool(raw.get("active", False))
        closed = bool(raw.get("closed", False))
        if not active or closed:
            return None, "inactive_or_closed", asset
        return CryptoMarket(
            market_id=str(raw.get("conditionId") or raw.get("id")),
            question=str(raw.get("question") or raw.get("slug")),
            asset=asset,
            window_start=start,
            window_end=end,
            yes_token_id=yes,
            no_token_id=no,
            liquidity=float(raw.get("liquidity") or 0),
            volume=float(raw.get("volume") or 0),
            active=active,
            closed=closed,
        ), "", asset

    def _get(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        url = self._url(path, params)
        request = urllib.request.Request(url, headers={"User-Agent": "forgeview-polymarket-v4/4.0"})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload if isinstance(payload, list) else payload.get("events", [])

    def _url(self, path: str, params: dict[str, Any]) -> str:
        return f"{self.BASE_URL}{path}?{urllib.parse.urlencode(params)}"


class MockMarketDiscovery:
    def discover(
        self,
        assets: tuple[str, ...],
        now: datetime | None = None,
    ) -> tuple[list[CryptoMarket], list[SkippedMarket]]:
        now = now or datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        start = now.replace(second=0, microsecond=0)
        end = start + timedelta(minutes=5)
        return [
            CryptoMarket(
                market_id=f"mock-{asset.lower()}-5m",
                question=f"{asset} Up or Down in the next 5 minutes?",
                asset=asset,
                window_start=start,
                window_end=end,
                yes_token_id=f"mock-{asset.lower()}-yes",
                no_token_id=f"mock-{asset.lower()}-no",
                liquidity=10_000.0,
                volume=50_000.0,
                active=True,
                closed=False,
            )
            for asset in assets
        ], []
