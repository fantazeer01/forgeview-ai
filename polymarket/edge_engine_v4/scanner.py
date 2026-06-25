from __future__ import annotations

import json
import math
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from polymarket.edge_engine.models import MarketSnapshot
from polymarket.edge_engine_v3.shadow import ShadowExecutionEngine

from .config import ScannerConfig
from .crypto_reference import MockCryptoReferenceFeed, PublicCryptoReferenceFeed
from .lag_detector import LagDetector
from .market_discovery import MockMarketDiscovery, PolymarketMarketDiscovery
from .opportunity import (
    CryptoMarket,
    Direction,
    Opportunity,
    PolymarketSnapshot,
    ReferencePrice,
    SkippedMarket,
)
from .reporting import SessionStore, write_reports


class PolymarketQuoteFeed:
    BOOK_URL = "https://clob.polymarket.com/book"

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def fetch(self, market: CryptoMarket, timestamp: datetime) -> PolymarketSnapshot:
        requested_at = time.monotonic()
        query = urllib.parse.urlencode({"token_id": market.yes_token_id})
        request = urllib.request.Request(
            f"{self.BOOK_URL}?{query}",
            headers={"User-Agent": "forgeview-polymarket-v4/4.0"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            book = json.loads(response.read().decode("utf-8"))
        bid_rows = [
            (float(row["price"]), float(row.get("size", 0.0)))
            for row in book.get("bids", [])
        ]
        ask_rows = [
            (float(row["price"]), float(row.get("size", 0.0)))
            for row in book.get("asks", [])
        ]
        bids = [row[0] for row in bid_rows]
        asks = [row[0] for row in ask_rows]
        if not bids or not asks:
            raise ValueError(f"Empty YES order book for {market.market_id}")
        bid, ask = max(bids), min(asks)
        bid_size = sum(size for price, size in bid_rows if price == bid)
        ask_size = sum(size for price, size in ask_rows if price == ask)
        quote_timestamp = _book_timestamp(book.get("timestamp"))
        yes_price = (bid + ask) / 2.0
        return PolymarketSnapshot(
            timestamp=timestamp,
            market_id=market.market_id,
            asset=market.asset,
            yes_price=round(yes_price, 8),
            no_price=round(1.0 - yes_price, 8),
            yes_bid=bid,
            yes_ask=ask,
            liquidity=market.liquidity,
            seconds_to_expiry=max(0.0, (market.window_end - timestamp).total_seconds()),
            quote_timestamp=quote_timestamp,
            yes_bid_size=bid_size,
            yes_ask_size=ask_size,
            total_bid_depth=sum(size for _, size in bid_rows),
            total_ask_depth=sum(size for _, size in ask_rows),
            source_latency_seconds=max(0.0, time.monotonic() - requested_at),
        )


class MockPolymarketQuoteFeed:
    def __init__(self) -> None:
        self.step = 0

    def fetch(self, market: CryptoMarket, timestamp: datetime) -> PolymarketSnapshot:
        # BTC/SOL external impulses initially lead probability; ETH mirrors down.
        paths = {
            "BTC": (0.50, 0.50, 0.505, 0.52, 0.61, 0.64),
            "ETH": (0.50, 0.50, 0.495, 0.48, 0.39, 0.36),
            "SOL": (0.50, 0.50, 0.50, 0.515, 0.60, 0.63),
        }
        path = paths[market.asset]
        price = path[min(self.step, len(path) - 1)]
        return PolymarketSnapshot(
            timestamp=timestamp,
            market_id=market.market_id,
            asset=market.asset,
            yes_price=price,
            no_price=1.0 - price,
            yes_bid=max(0.001, price - 0.01),
            yes_ask=min(0.999, price + 0.01),
            liquidity=market.liquidity,
            seconds_to_expiry=max(0.0, (market.window_end - timestamp).total_seconds()),
            quote_timestamp=timestamp,
            yes_bid_size=500.0 + self.step * 10.0,
            yes_ask_size=480.0 - min(self.step * 5.0, 100.0),
            total_bid_depth=2_000.0 + self.step * 20.0,
            total_ask_depth=1_900.0 - min(self.step * 10.0, 200.0),
            source_latency_seconds=0.001,
        )

    def advance(self) -> None:
        self.step += 1


class V3OpportunityAdapter:
    """Maps qualified lag opportunities into the existing v3 shadow engine."""

    def __init__(self) -> None:
        self.shadow = ShadowExecutionEngine(timeout_updates=4)

    def submit(self, opportunity: Opportunity, snapshot: PolymarketSnapshot) -> None:
        sign = 1.0 if opportunity.direction is Direction.UP else -1.0
        reference = max(
            0.001,
            min(0.999, snapshot.yes_price + sign * max(0.20, opportunity.lag_score * 0.45)),
        )
        self.shadow.on_snapshot(MarketSnapshot(
            timestamp=opportunity.timestamp,
            market_id=opportunity.market_id,
            question=opportunity.question,
            yes_price=snapshot.yes_price,
            reference_probability=reference,
            volume_spike=max(0.75, opportunity.confidence),
            momentum=max(0.75, opportunity.confidence),
            stability=0.85,
        ))

    def finalize(self) -> None:
        self.shadow.finalize()


def _book_timestamp(value) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
        if number > 10_000_000_000:
            number /= 1000.0
        return datetime.fromtimestamp(number, tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None


class CryptoLagScanner:
    def __init__(
        self,
        config: ScannerConfig,
        discovery=None,
        reference_feed=None,
        quote_feed=None,
    ) -> None:
        self.config = config
        self.discovery = discovery
        self.reference_feed = reference_feed
        self.quote_feed = quote_feed
        self.detector = LagDetector(config)

    def run(self) -> dict:
        mock_mode = self.config.mock
        discovery = self.discovery or (
            MockMarketDiscovery() if mock_mode
            else PolymarketMarketDiscovery(self.config.request_timeout_seconds)
        )
        reference_feed = self.reference_feed or (
            MockCryptoReferenceFeed() if mock_mode
            else PublicCryptoReferenceFeed(self.config.request_timeout_seconds)
        )
        quote_feed = self.quote_feed or (
            MockPolymarketQuoteFeed() if mock_mode
            else PolymarketQuoteFeed(self.config.request_timeout_seconds)
        )
        now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc) if mock_mode else datetime.now(timezone.utc)
        fallback_reason = ""

        try:
            markets, skipped = discovery.discover(self.config.assets, now)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            markets, skipped = [], []
            fallback_reason = f"market_discovery_error:{type(exc).__name__}"

        if not markets and self.config.allow_mock_fallback and not mock_mode:
            mock_mode = True
            fallback_reason = fallback_reason or "no_live_five_minute_markets_found"
            now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
            discovery = MockMarketDiscovery()
            reference_feed = MockCryptoReferenceFeed()
            quote_feed = MockPolymarketQuoteFeed()
            markets, mock_skips = discovery.discover(self.config.assets, now)
            skipped.extend(mock_skips)
        if not markets:
            raise ValueError("No eligible BTC/ETH/SOL five-minute markets found")

        store = SessionStore(self.config.output_dir)
        store.write_markets(markets)
        opportunities: list[Opportunity] = []
        adapter = V3OpportunityAdapter()
        baseline_refs: dict[str, ReferencePrice] = {}
        baseline_markets: dict[str, PolymarketSnapshot] = {}
        iterations = max(2, math.ceil(self.config.duration_seconds / self.config.poll_interval_seconds))
        started = time.monotonic()

        for iteration in range(iterations):
            timestamp = (
                now + timedelta(seconds=iteration * self.config.poll_interval_seconds)
                if mock_mode else datetime.now(timezone.utc)
            )
            try:
                references = reference_feed.fetch(self.config.assets, timestamp)
            except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
                if not self.config.allow_mock_fallback:
                    raise
                reference_feed = MockCryptoReferenceFeed()
                references = reference_feed.fetch(self.config.assets, timestamp)
                fallback_reason = fallback_reason or f"reference_feed_error:{type(exc).__name__}"
            ref_by_asset = {row.asset: row for row in references}
            for reference in references:
                store.append_reference(reference)

            for market in markets:
                reference = ref_by_asset.get(market.asset)
                if reference is None:
                    skipped.append(SkippedMarket(
                        timestamp, market.market_id, market.asset, market.question,
                        "missing_reference_price",
                    ))
                    continue
                if timestamp < market.window_start:
                    skipped.append(SkippedMarket(
                        timestamp, market.market_id, market.asset, market.question,
                        "market_window_not_started",
                    ))
                    continue
                if timestamp >= market.window_end:
                    skipped.append(SkippedMarket(
                        timestamp, market.market_id, market.asset, market.question,
                        "market_window_expired",
                    ))
                    continue
                try:
                    snapshot = quote_feed.fetch(market, timestamp)
                except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
                    skipped.append(SkippedMarket(
                        timestamp, market.market_id, market.asset, market.question,
                        f"polymarket_quote_error:{type(exc).__name__}",
                    ))
                    continue
                store.append_polymarket(snapshot)
                baseline_refs.setdefault(market.asset, reference)
                baseline_markets.setdefault(market.market_id, snapshot)
                measurement = self.detector.measure(
                    reference,
                    baseline_refs[market.asset],
                    snapshot,
                    baseline_markets[market.market_id],
                )
                if measurement.qualified:
                    opportunity = Opportunity(
                        asset=market.asset,
                        market_id=market.market_id,
                        question=market.question,
                        direction=measurement.direction,
                        yes_token_id=market.yes_token_id,
                        no_token_id=market.no_token_id,
                        external_move=measurement.external_price_change,
                        polymarket_move=measurement.polymarket_yes_price_change,
                        lag_score=measurement.lag_score,
                        confidence=measurement.confidence,
                        reason=measurement.reason,
                        timestamp=timestamp,
                    )
                    opportunities.append(opportunity)
                    adapter.submit(opportunity, snapshot)
                else:
                    skipped.append(SkippedMarket(
                        timestamp, market.market_id, market.asset, market.question,
                        measurement.reason,
                    ))
            if isinstance(quote_feed, MockPolymarketQuoteFeed):
                quote_feed.advance()
            if not mock_mode and iteration < iterations - 1:
                remaining = self.config.duration_seconds - (time.monotonic() - started)
                if remaining <= 0:
                    break
                time.sleep(min(self.config.poll_interval_seconds, remaining))

        adapter.finalize()
        summary = write_reports(
            self.config.output_dir,
            markets,
            opportunities,
            skipped,
            adapter.shadow.decisions,
            adapter.shadow.trades,
            mock_mode=mock_mode,
            fallback_reason=fallback_reason,
        )
        return summary


def replay_session(session_dir: str | Path, output_dir: str | Path | None = None) -> dict:
    session = Path(session_dir)
    markets, references, snapshots = SessionStore.load(session)
    output = Path(output_dir) if output_dir else session.parent
    config = ScannerConfig(
        assets=tuple(sorted({market.asset for market in markets})),
        duration_seconds=1,
        poll_interval_seconds=1,
        output_dir=output,
        mock=True,
    )
    detector = LagDetector(config)
    market_by_id = {row.market_id: row for row in markets}
    refs_by_time = {(row.timestamp, row.asset): row for row in references}
    baseline_refs: dict[str, ReferencePrice] = {}
    baseline_markets: dict[str, PolymarketSnapshot] = {}
    opportunities: list[Opportunity] = []
    skipped: list[SkippedMarket] = []
    adapter = V3OpportunityAdapter()

    for snapshot in sorted(snapshots, key=lambda row: (row.timestamp, row.market_id)):
        market = market_by_id[snapshot.market_id]
        reference = refs_by_time.get((snapshot.timestamp, market.asset))
        if reference is None:
            skipped.append(SkippedMarket(
                snapshot.timestamp, market.market_id, market.asset, market.question,
                "missing_reference_price",
            ))
            continue
        baseline_refs.setdefault(market.asset, reference)
        baseline_markets.setdefault(market.market_id, snapshot)
        measurement = detector.measure(
            reference, baseline_refs[market.asset],
            snapshot, baseline_markets[market.market_id],
        )
        if measurement.qualified:
            opportunity = Opportunity(
                market.asset, market.market_id, market.question,
                measurement.direction, market.yes_token_id, market.no_token_id,
                measurement.external_price_change,
                measurement.polymarket_yes_price_change,
                measurement.lag_score, measurement.confidence,
                measurement.reason, snapshot.timestamp,
            )
            opportunities.append(opportunity)
            adapter.submit(opportunity, snapshot)
        else:
            skipped.append(SkippedMarket(
                snapshot.timestamp, market.market_id, market.asset, market.question,
                measurement.reason,
            ))
    adapter.finalize()
    return write_reports(
        output, markets, opportunities, skipped,
        adapter.shadow.decisions, adapter.shadow.trades,
        mock_mode=True, fallback_reason="replay",
        preserve_session=True,
    )
