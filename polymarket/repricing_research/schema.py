from __future__ import annotations

from dataclasses import dataclass, fields


@dataclass(frozen=True)
class RepricingLabelRow:
    entry_timestamp: str
    asset: str
    market_id: str
    side: str
    yes_price_at_entry: float
    no_price_at_entry: float
    side_price_at_entry: float
    external_price_move: float
    external_return_5s: float | None
    external_return_15s: float | None
    external_return_30s: float | None
    external_return_60s: float | None
    momentum: float | None
    quote_age_seconds: float | None
    repricing_velocity: float | None
    repricing_acceleration: float | None
    spread_compression: float | None
    book_imbalance: float | None
    cross_asset_movement: float | None
    time_to_expiry_seconds: float
    lag_score: float | None
    polymarket_price_move_after_30s: float | None
    polymarket_price_move_after_60s: float | None
    polymarket_price_move_after_120s: float | None
    polymarket_price_move_after_180s: float | None
    max_favorable_excursion: float
    max_adverse_excursion: float
    time_to_repricing_seconds: float | None
    simulated_exit_timestamp: str
    simulated_exit_seconds: float
    simulated_exit_price: float
    simulated_exit_reason: str
    simulated_pnl_before_slippage: float
    simulated_pnl_after_slippage: float
    repriced_favorably: bool
    source_session: str


@dataclass(frozen=True)
class RepricingSimulationSummary:
    rows: int
    signals: int
    wins: int
    win_rate: float | None
    average_favorable_repricing: float | None
    average_adverse_move: float | None
    simulated_pnl_before_fees_slippage: float
    simulated_pnl_after_conservative_slippage: float
    max_drawdown: float
    expectancy_per_signal: float | None
    signals_per_hour: float | None
    first_entry_timestamp: str | None
    last_entry_timestamp: str | None


REPRICING_COLUMNS = tuple(field.name for field in fields(RepricingLabelRow))
