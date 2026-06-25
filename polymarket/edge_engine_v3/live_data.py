from __future__ import annotations

import asyncio
import json
import time
import urllib.parse
import urllib.request
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from .models import LiveTick


def _timestamp(value: str | int | float | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    number = float(value)
    if number > 10_000_000_000:
        number /= 1000.0
    return datetime.fromtimestamp(number, tz=timezone.utc)


class PolymarketEventParser:
    """Converts public CLOB WebSocket events into normalized quote ticks."""

    def __init__(self) -> None:
        self.books: dict[str, tuple[float, float]] = {}
        self.markets: dict[str, str] = {}

    def parse(self, payload: str | dict | list) -> list[LiveTick]:
        data = json.loads(payload) if isinstance(payload, str) else payload
        events = data if isinstance(data, list) else [data]
        ticks: list[LiveTick] = []
        for event in events:
            if not isinstance(event, dict):
                continue
            event_type = event.get("event_type", "")
            if event_type == "book":
                asset = str(event["asset_id"])
                bids = [float(row["price"]) for row in event.get("bids", [])]
                asks = [float(row["price"]) for row in event.get("asks", [])]
                if bids and asks:
                    self.books[asset] = (max(bids), min(asks))
                    self.markets[asset] = str(event.get("market", asset))
                    ticks.append(self._tick(asset, event, event_type))
            elif event_type == "best_bid_ask":
                asset = str(event["asset_id"])
                self.books[asset] = (float(event["best_bid"]), float(event["best_ask"]))
                self.markets[asset] = str(event.get("market", asset))
                ticks.append(self._tick(asset, event, event_type))
            elif event_type == "price_change":
                for change in event.get("price_changes", []):
                    asset = str(change["asset_id"])
                    if "best_bid" in change and "best_ask" in change:
                        bid, ask = float(change["best_bid"]), float(change["best_ask"])
                        if 0 <= bid < ask <= 1:
                            self.books[asset] = (bid, ask)
                            self.markets[asset] = str(event.get("market", asset))
                            ticks.append(self._tick(asset, event, event_type))
            elif event_type == "last_trade_price":
                asset = str(event["asset_id"])
                if asset in self.books:
                    ticks.append(self._tick(
                        asset, event, event_type,
                        last_trade=float(event["price"]),
                        trade_size=float(event.get("size", 0)),
                    ))
        return ticks

    def _tick(
        self,
        asset: str,
        event: dict,
        event_type: str,
        last_trade: float | None = None,
        trade_size: float = 0.0,
    ) -> LiveTick:
        bid, ask = self.books[asset]
        return LiveTick(
            timestamp=_timestamp(event.get("timestamp")),
            token_id=asset,
            market_id=self.markets.get(asset, asset),
            best_bid=bid,
            best_ask=ask,
            last_trade=last_trade,
            trade_size=trade_size,
            source_event=event_type,
        )


class PolymarketWebSocketFeed:
    URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

    async def stream(self, token_ids: list[str], duration_seconds: int) -> AsyncIterator[tuple[str, LiveTick]]:
        try:
            import websockets
        except ImportError as exc:
            raise RuntimeError(
                "WebSocket capture requires: python -m pip install -e .[live]"
            ) from exc
        parser = PolymarketEventParser()
        started = time.monotonic()
        async with websockets.connect(self.URL, ping_interval=20, ping_timeout=20) as socket:
            await socket.send(json.dumps({
                "assets_ids": token_ids,
                "type": "market",
                "custom_feature_enabled": True,
            }))
            while time.monotonic() - started < duration_seconds:
                remaining = duration_seconds - (time.monotonic() - started)
                try:
                    raw = await asyncio.wait_for(socket.recv(), timeout=max(0.1, remaining))
                except TimeoutError:
                    break
                for tick in parser.parse(raw):
                    if tick.token_id in token_ids:
                        yield raw, tick


class PolymarketPollingFeed:
    """Public REST fallback; emits midpoint ticks without authentication."""

    URL = "https://clob.polymarket.com/book"

    async def stream(
        self,
        token_ids: list[str],
        duration_seconds: int,
        interval_seconds: float = 2.0,
    ) -> AsyncIterator[tuple[str, LiveTick]]:
        started = time.monotonic()
        while time.monotonic() - started < duration_seconds:
            for token_id in token_ids:
                query = urllib.parse.urlencode({"token_id": token_id})
                request = urllib.request.Request(
                    f"{self.URL}?{query}",
                    headers={"User-Agent": "polymarket-edge-engine-v3/3.0"},
                )
                raw = await asyncio.to_thread(
                    lambda: urllib.request.urlopen(request, timeout=15).read().decode("utf-8")
                )
                book = json.loads(raw)
                bids = [float(row["price"]) for row in book.get("bids", [])]
                asks = [float(row["price"]) for row in book.get("asks", [])]
                if bids and asks:
                    tick = LiveTick(
                        timestamp=_timestamp(book.get("timestamp")),
                        token_id=token_id,
                        market_id=str(book.get("market", token_id)),
                        best_bid=max(bids),
                        best_ask=min(asks),
                        last_trade=float(book["last_trade_price"]) if book.get("last_trade_price") else None,
                        source_event="rest_book",
                    )
                    yield raw, tick
            await asyncio.sleep(interval_seconds)
