"""Read-only public Polymarket data client for wallet-intelligence research."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DATA_API_BASE = "https://data-api.polymarket.com"


@dataclass(frozen=True)
class PublicResponse:
    url: str
    status_code: int
    payload: Any


class PolymarketPublicClient:
    """Small public-data client with no wallet, key, order, or trading methods."""

    def __init__(self, delay_seconds: float = 0.25, timeout_seconds: float = 20.0):
        self.delay_seconds = delay_seconds
        self.timeout_seconds = timeout_seconds

    def get_json(self, path: str, params: dict[str, Any] | None = None) -> PublicResponse:
        if path.startswith("http"):
            url = path
        else:
            query = urlencode(params or {}, doseq=True)
            url = f"{DATA_API_BASE}{path}"
            if query:
                url = f"{url}?{query}"
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "ForgeViewAI wallet-intelligence research/1.0",
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                payload = json.loads(raw) if raw else None
                status = int(getattr(response, "status", 200))
        finally:
            if self.delay_seconds:
                time.sleep(self.delay_seconds)
        return PublicResponse(url=url, status_code=status, payload=payload)

    def get_text(self, url: str) -> PublicResponse:
        request = Request(
            url,
            headers={
                "Accept": "text/html,application/xhtml+xml",
                "User-Agent": "ForgeViewAI wallet-intelligence research/1.0",
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = response.read().decode("utf-8", errors="replace")
                status = int(getattr(response, "status", 200))
        finally:
            if self.delay_seconds:
                time.sleep(self.delay_seconds)
        return PublicResponse(url=url, status_code=status, payload=payload)

    def positions(self, user: str, limit: int = 50) -> PublicResponse:
        return self.get_json("/positions", {"user": user, "limit": limit})

    def closed_positions(self, user: str, limit: int = 50, offset: int = 0) -> PublicResponse:
        return self.get_json(
            "/closed-positions",
            {"user": user, "limit": limit, "offset": offset, "sortBy": "TIMESTAMP", "sortDirection": "DESC"},
        )

    def activity(self, user: str, limit: int = 50) -> PublicResponse:
        return self.get_json("/activity", {"user": user, "limit": limit})

    def activity_trades(self, user: str, limit: int = 100, offset: int = 0) -> PublicResponse:
        return self.get_json(
            "/activity",
            {
                "user": user,
                "type": "TRADE",
                "limit": limit,
                "offset": offset,
                "sortBy": "TIMESTAMP",
                "sortDirection": "DESC",
            },
        )

    def value(self, user: str) -> PublicResponse:
        return self.get_json("/value", {"user": user})

    def traded(self, user: str) -> PublicResponse:
        return self.get_json("/traded", {"user": user})
