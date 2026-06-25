from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MarketDescriptor:
    market_id: str
    asset: str
    question: str
    window_start: datetime
    window_end: datetime

    @property
    def slug(self) -> str:
        prefix = {"BTC": "btc", "ETH": "eth", "SOL": "sol"}[self.asset]
        return f"{prefix}-updown-5m-{int(self.window_start.timestamp())}"


@dataclass(frozen=True)
class ResolutionRecord:
    market_id: str
    asset: str
    question: str
    slug: str
    outcome: int | None
    outcome_name: str
    resolution_timestamp: datetime | None
    resolution_source: str
    retrieval_timestamp: datetime
    status: str
    reason: str

    @property
    def resolved(self) -> bool:
        return self.status == "resolved" and self.outcome in (0, 1)
