from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class Side(str, Enum):
    YES = "YES"
    NO = "NO"


class ExitReason(str, Enum):
    SCORE = "score_below_threshold"
    CONVERGENCE = "convergence"
    TIMEOUT = "timeout"
    END_OF_DATA = "end_of_data"


@dataclass(frozen=True)
class MarketSnapshot:
    timestamp: datetime
    market_id: str
    question: str
    yes_price: float
    reference_probability: float
    volume_spike: float
    momentum: float
    stability: float

    def __post_init__(self) -> None:
        for name in ("yes_price", "reference_probability", "volume_spike", "momentum", "stability"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1, got {value}")
        if not self.market_id:
            raise ValueError("market_id cannot be empty")

    @property
    def no_price(self) -> float:
        return 1.0 - self.yes_price

    def contract_price(self, side: Side) -> float:
        return self.yes_price if side is Side.YES else self.no_price


@dataclass(frozen=True)
class ScoreBreakdown:
    price_lag: float
    volume_spike: float
    momentum: float
    stability: float
    score: float


@dataclass(frozen=True)
class Decision:
    action: str
    side: Side | None = None
    reason: str = ""


@dataclass
class Position:
    trade_id: str
    market_id: str
    question: str
    side: Side
    quantity: float
    entry_price: float
    entry_score: float
    opened_at: datetime
    opened_step: int
    last_price: float
    last_score: float

    @property
    def cost(self) -> float:
        return self.entry_price * self.quantity

    def unrealized_pnl(self) -> float:
        return (self.last_price - self.entry_price) * self.quantity


@dataclass(frozen=True)
class ClosedTrade:
    trade_id: str
    market_id: str
    question: str
    side: Side
    quantity: float
    entry_price: float
    exit_price: float
    entry_score: float
    exit_score: float
    opened_at: datetime
    closed_at: datetime
    exit_reason: ExitReason
    pnl: float
    return_pct: float
    holding_steps: int


def serializable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        value = asdict(value)
    if isinstance(value, dict):
        return {key: serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serializable(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value
