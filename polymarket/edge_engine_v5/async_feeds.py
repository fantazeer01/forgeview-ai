from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime
from threading import Lock

from polymarket.edge_engine_v4.market_discovery import DiscoveryFailure


class AsyncDiscovery:
    def __init__(self, feed, workers: int = 1) -> None:
        self.feed = feed
        self.executor = ThreadPoolExecutor(
            max_workers=workers, thread_name_prefix="market-discovery"
        )
        self.future: Future | None = None
        self.cached = ([], [])
        self.failures = []
        self.lock = Lock()

    def discover(self, assets, timestamp):
        with self.lock:
            self.failures = []
            if self.future and self.future.done():
                try:
                    self.cached = self.future.result()
                except Exception as exc:
                    self.failures = [DiscoveryFailure(
                        timestamp=timestamp,
                        endpoint_url=getattr(exc, "url", "unknown"),
                        exception_type=type(exc).__name__,
                        exception_message=str(exc),
                    )]
                else:
                    self.failures = list(getattr(self.feed, "failures", []))
                self.future = None
            if self.future is None:
                self.future = self.executor.submit(
                    self.feed.discover, assets, timestamp
                )
            return self.cached

    def close(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)


class AsyncReferenceFeed:
    def __init__(self, feed) -> None:
        self.feed = feed
        self.executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="crypto-reference"
        )
        self.future: Future | None = None
        self.cached = []
        self.lock = Lock()

    def fetch(self, assets, timestamp):
        with self.lock:
            if self.future and self.future.done():
                try:
                    self.cached = self.future.result()
                except Exception:
                    self.cached = []
                self.future = None
            if self.future is None:
                self.future = self.executor.submit(
                    self.feed.fetch, assets, timestamp
                )
            return [replace(row, timestamp=timestamp) for row in self.cached]

    def close(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)


class AsyncQuoteFeed:
    def __init__(self, feed, workers: int = 3) -> None:
        self.feed = feed
        self.executor = ThreadPoolExecutor(
            max_workers=workers, thread_name_prefix="polymarket-quote"
        )
        self.futures: dict[str, Future] = {}
        self.cached = {}
        self.errors: dict[str, Exception] = {}
        self.lock = Lock()

    def fetch(self, market, timestamp):
        with self.lock:
            future = self.futures.get(market.market_id)
            if future and future.done():
                try:
                    self.cached[market.market_id] = future.result()
                    self.errors.pop(market.market_id, None)
                except Exception as exc:
                    self.errors[market.market_id] = exc
                self.futures.pop(market.market_id, None)
            if market.market_id not in self.futures:
                self.futures[market.market_id] = self.executor.submit(
                    self.feed.fetch, market, timestamp
                )
            if market.market_id in self.errors and market.market_id not in self.cached:
                raise self.errors.pop(market.market_id)
            snapshot = self.cached.get(market.market_id)
            if snapshot is None:
                raise ValueError("quote_pending")
            return replace(
                snapshot,
                timestamp=timestamp,
                seconds_to_expiry=max(
                    0.0, (market.window_end - timestamp).total_seconds()
                ),
            )

    def close(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)


def close_async_feeds(*feeds) -> None:
    for feed in feeds:
        close = getattr(feed, "close", None)
        if close:
            close()
