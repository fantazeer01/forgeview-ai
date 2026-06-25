from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class Direction(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    NONE = "NONE"


@dataclass(frozen=True)
class CryptoMarket:
    market_id: str
    question: str
    asset: str
    window_start: datetime
    window_end: datetime
    yes_token_id: str
    no_token_id: str
    liquidity: float
    volume: float
    active: bool
    closed: bool


@dataclass(frozen=True)
class ReferencePrice:
    timestamp: datetime
    asset: str
    price: float
    source: str


@dataclass(frozen=True)
class PolymarketSnapshot:
    timestamp: datetime
    market_id: str
    asset: str
    yes_price: float
    no_price: float
    yes_bid: float
    yes_ask: float
    liquidity: float
    seconds_to_expiry: float
    quote_timestamp: datetime | None = None
    yes_bid_size: float | None = None
    yes_ask_size: float | None = None
    total_bid_depth: float | None = None
    total_ask_depth: float | None = None
    source_latency_seconds: float | None = None


@dataclass(frozen=True)
class LagMeasurement:
    external_price_change: float
    polymarket_yes_price_change: float
    lag_seconds: float
    lag_score: float
    direction: Direction
    confidence: float
    qualified: bool
    reason: str


@dataclass(frozen=True)
class Opportunity:
    asset: str
    market_id: str
    question: str
    direction: Direction
    yes_token_id: str
    no_token_id: str
    external_move: float
    polymarket_move: float
    lag_score: float
    confidence: float
    reason: str
    timestamp: datetime


@dataclass(frozen=True)
class SkippedMarket:
    timestamp: datetime
    market_id: str
    asset: str
    question: str
    reason: str


def to_dict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return to_dict(asdict(value))
    if isinstance(value, dict):
        return {key: to_dict(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_dict(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value
