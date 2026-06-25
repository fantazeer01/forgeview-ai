from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from polymarket.edge_engine.models import Side


class ReferenceMode(str, Enum):
    EXTERNAL = "external"
    CAUSAL_PROXY = "causal_proxy"


@dataclass(frozen=True)
class LiveTick:
    timestamp: datetime
    token_id: str
    market_id: str
    best_bid: float
    best_ask: float
    last_trade: float | None = None
    trade_size: float = 0.0
    source_event: str = "best_bid_ask"

    @property
    def midpoint(self) -> float:
        return (self.best_bid + self.best_ask) / 2.0

    @property
    def spread(self) -> float:
        return self.best_ask - self.best_bid


@dataclass(frozen=True)
class ShadowDecision:
    timestamp: datetime
    market_id: str
    action: str
    side: Side | None
    score: float
    price: float
    reference_probability: float
    reason: str


@dataclass(frozen=True)
class ShadowTrade:
    trade_id: str
    market_id: str
    side: Side
    opened_at: datetime
    closed_at: datetime
    entry_price: float
    exit_price: float
    quantity: float
    entry_score: float
    exit_score: float
    exit_reason: str
    pnl: float
    return_pct: float
    holding_updates: int


@dataclass(frozen=True)
class LiveValidationReport:
    session_fingerprint: str
    session_start: datetime
    session_end: datetime
    reference_mode: ReferenceMode
    external_reference_coverage: float
    snapshots: int
    decisions: int
    trades: int
    live_simulated_pnl: float
    live_return_pct: float
    max_drawdown: float
    model_expected_pnl: float
    pnl_deviation: float
    divergence_score: float
    signal_drift_score: float
    edge_decay_score: float
    stability_score: float
    noise_ratio: float
    period_pnl: tuple[float, ...]
    verdict: str
    evidence_sufficient: bool
    caveats: tuple[str, ...]


def to_dict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return to_dict(asdict(value))
    if isinstance(value, dict):
        return {key: to_dict(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [to_dict(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value
