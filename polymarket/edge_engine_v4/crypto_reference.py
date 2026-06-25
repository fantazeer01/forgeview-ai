from __future__ import annotations

import json
import math
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from .opportunity import ReferencePrice


class PublicCryptoReferenceFeed:
    BINANCE = "https://data-api.binance.vision/api/v3/ticker/price?symbol={symbol}USDT"
    COINBASE = "https://api.exchange.coinbase.com/products/{symbol}-USD/ticker"

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def fetch(self, assets: tuple[str, ...], timestamp: datetime | None = None) -> list[ReferencePrice]:
        timestamp = timestamp or datetime.now(timezone.utc)
        def fetch_asset(asset: str) -> ReferencePrice:
            try:
                payload = self._get(self.BINANCE.format(symbol=asset))
                return ReferencePrice(
                    timestamp, asset, float(payload["price"]), "binance"
                )
            except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
                payload = self._get(self.COINBASE.format(symbol=asset))
                return ReferencePrice(
                    timestamp, asset, float(payload["price"]), "coinbase"
                )
        with ThreadPoolExecutor(
            max_workers=len(assets), thread_name_prefix="reference-asset"
        ) as executor:
            return list(executor.map(fetch_asset, assets))

    def _get(self, url: str) -> dict:
        request = urllib.request.Request(url, headers={"User-Agent": "forgeview-polymarket-v4/4.0"})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))


class MockCryptoReferenceFeed:
    BASE = {"BTC": 60_000.0, "ETH": 3_000.0, "SOL": 140.0}

    def __init__(self) -> None:
        self.step = 0

    def fetch(self, assets: tuple[str, ...], timestamp: datetime | None = None) -> list[ReferencePrice]:
        timestamp = timestamp or datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        results = []
        for index, asset in enumerate(assets):
            # Deterministic impulse followed by continuation and mild reversal.
            impulse = (0.0002 * self.step) + (0.0025 if self.step >= 2 else 0.0)
            direction = 1.0 if asset != "ETH" else -1.0
            wobble = 0.00015 * math.sin(self.step + index)
            price = self.BASE[asset] * (1.0 + direction * impulse + wobble)
            results.append(ReferencePrice(timestamp, asset, round(price, 8), "mock"))
        self.step += 1
        return results
