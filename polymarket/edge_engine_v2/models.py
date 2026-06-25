from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from polymarket.edge_engine.models import MarketSnapshot, Side


@dataclass(frozen=True)
class ExecutedTrade:
    trade_id: str
    run_id: str
    window_id: int
    market_id: str
    side: Side
    signal_at: datetime
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
    holding_steps: int
    entry_delay_steps: int


@dataclass
class OpenPosition:
    trade_id: str
    run_id: str
    window_id: int
    market_id: str
    side: Side
    signal_at: datetime
    opened_at: datetime
    entry_price: float
    quantity: float
    entry_score: float
    opened_step: int
    entry_delay_steps: int


@dataclass(frozen=True)
class WindowResult:
    run_id: str
    window_id: int
    start: datetime
    end: datetime
    snapshots: int
    trades: int
    pnl: float
    return_pct: float
    max_drawdown: float
    win_rate: float


@dataclass(frozen=True)
class ScenarioResult:
    run_id: str
    scenario: str
    parameter: float
    pnl: float
    max_drawdown: float
    trades: int
    win_rate: float
    windows_profitable_ratio: float
    window_pnl_stdev: float
    windows: tuple[WindowResult, ...]
    trade_log: tuple[ExecutedTrade, ...]


@dataclass(frozen=True)
class ValidationReport:
    dataset_fingerprint: str
    generated_at: datetime
    seed: int
    baseline: ScenarioResult
    scenarios: tuple[ScenarioResult, ...]
    consistency_score: float
    noise_resilience_score: float
    profitability_stability_score: float
    drawdown_control_score: float
    scenario_pnl_variance: float
    robustness_score: float
    verdict: str
    answers: dict[str, bool]
    normalization_checks: dict[str, Any]


def to_dict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return to_dict(asdict(value))
    if isinstance(value, dict):
        return {key: to_dict(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [to_dict(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Side):
        return value.value
    return value


Snapshot = MarketSnapshot
