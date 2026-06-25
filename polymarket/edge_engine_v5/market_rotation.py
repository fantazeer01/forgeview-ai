from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from polymarket.edge_engine_v4.opportunity import CryptoMarket


class Lifecycle(str, Enum):
    DISCOVERED = "discovered"
    ACTIVE = "active"
    NEAR_EXPIRY = "near_expiry"
    CLOSED = "closed"
    SKIPPED = "skipped"


@dataclass
class TrackedMarket:
    market: CryptoMarket
    lifecycle: Lifecycle
    discovered_at: datetime
    updated_at: datetime
    snapshots: int = 0
    opportunities: int = 0
    skip_reason: str = ""


class MarketRotation:
    def __init__(self, near_expiry_seconds: float = 30.0) -> None:
        self.near_expiry_seconds = near_expiry_seconds
        self.markets: dict[str, TrackedMarket] = {}

    def ingest(
        self,
        markets: list[CryptoMarket],
        timestamp: datetime,
    ) -> list[tuple[TrackedMarket, Lifecycle, Lifecycle]]:
        transitions = []
        for market in markets:
            if market.market_id not in self.markets:
                tracked = TrackedMarket(
                    market=market,
                    lifecycle=Lifecycle.DISCOVERED,
                    discovered_at=timestamp,
                    updated_at=timestamp,
                )
                self.markets[market.market_id] = tracked
                transitions.append((tracked, Lifecycle.DISCOVERED, Lifecycle.DISCOVERED))
        transitions.extend(self.update(timestamp))
        return transitions

    def update(self, timestamp: datetime) -> list[tuple[TrackedMarket, Lifecycle, Lifecycle]]:
        transitions = []
        for tracked in self.markets.values():
            previous = tracked.lifecycle
            if tracked.lifecycle is Lifecycle.SKIPPED:
                continue
            if timestamp >= tracked.market.window_end:
                current = Lifecycle.CLOSED
            elif timestamp < tracked.market.window_start:
                current = Lifecycle.DISCOVERED
            elif (tracked.market.window_end - timestamp).total_seconds() <= self.near_expiry_seconds:
                current = Lifecycle.NEAR_EXPIRY
            else:
                current = Lifecycle.ACTIVE
            tracked.lifecycle = current
            tracked.updated_at = timestamp
            if current is not previous:
                transitions.append((tracked, previous, current))
        return transitions

    def mark_skipped(self, market_id: str, reason: str, timestamp: datetime) -> None:
        tracked = self.markets.get(market_id)
        if tracked:
            tracked.lifecycle = Lifecycle.SKIPPED
            tracked.skip_reason = reason
            tracked.updated_at = timestamp

    def observable(self) -> list[TrackedMarket]:
        return [
            row for row in self.markets.values()
            if row.lifecycle in {Lifecycle.ACTIVE, Lifecycle.NEAR_EXPIRY}
        ]

    @property
    def completed(self) -> list[TrackedMarket]:
        return [
            row for row in self.markets.values()
            if row.lifecycle is Lifecycle.CLOSED and row.snapshots > 0
        ]


class MockRotatingDiscovery:
    """Deterministic rolling five-minute markets for long mock captures."""

    def discover(self, assets: tuple[str, ...], now: datetime):
        anchor = int(now.timestamp()) // 300 * 300
        markets = []
        for asset in assets:
            for offset in (0, 300):
                start = datetime.fromtimestamp(anchor + offset, tz=timezone.utc)
                end = start + timedelta(minutes=5)
                suffix = int(start.timestamp())
                markets.append(CryptoMarket(
                    market_id=f"mock-{asset.lower()}-{suffix}",
                    question=f"{asset} Up or Down - mock {start.isoformat()}",
                    asset=asset,
                    window_start=start,
                    window_end=end,
                    yes_token_id=f"mock-{asset.lower()}-{suffix}-yes",
                    no_token_id=f"mock-{asset.lower()}-{suffix}-no",
                    liquidity=10_000.0,
                    volume=50_000.0,
                    active=True,
                    closed=False,
                ))
        return markets, []
