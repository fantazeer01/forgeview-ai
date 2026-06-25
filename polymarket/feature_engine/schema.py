from __future__ import annotations

from dataclasses import dataclass, fields


@dataclass(frozen=True)
class TrainingRow:
    market_id: str
    asset: str
    market_source: str
    window_start: str
    window_end: str
    feature_timestamp: str
    market_age_seconds: float
    seconds_to_expiry: float
    return_5s: float | None
    return_15s: float | None
    return_30s: float | None
    return_60s: float | None
    momentum_short: float | None
    momentum_medium: float | None
    volatility_30s: float | None
    volatility_60s: float | None
    yes_price: float
    no_price: float
    yes_no_spread: float
    probability_change_15s: float | None
    probability_change_30s: float | None
    lag_score: float | None
    confidence_score: float | None
    detection_delay: float | None
    early_window_flag: int
    late_window_flag: int
    outcome: int
    resolution_timestamp: str
    label_source: str
    source_session: str
    quote_age_seconds: float | None = None
    time_since_quote_update_seconds: float | None = None
    repricing_velocity: float | None = None
    repricing_acceleration: float | None = None
    yes_change_frequency_30s: float | None = None
    no_change_frequency_30s: float | None = None
    consecutive_quote_stability: float | None = None
    bid_ask_spread: float | None = None
    spread_change: float | None = None
    spread_velocity: float | None = None
    spread_compression: float | None = None
    yes_bid_size: float | None = None
    yes_ask_size: float | None = None
    total_bid_depth: float | None = None
    total_ask_depth: float | None = None
    book_imbalance: float | None = None
    market_refresh_latency: float | None = None
    cross_asset_yes_dispersion: float | None = None
    cross_asset_relative_yes: float | None = None


COLUMNS = tuple(field.name for field in fields(TrainingRow))
IDENTIFIER_COLUMNS = {
    "market_id", "asset", "market_source", "window_start", "window_end", "feature_timestamp",
    "resolution_timestamp", "label_source", "source_session",
}
LABEL_COLUMNS = {"outcome"}
FEATURE_COLUMNS = tuple(
    name for name in COLUMNS if name not in IDENTIFIER_COLUMNS | LABEL_COLUMNS
)
MICROSTRUCTURE_FEATURE_COLUMNS = (
    "quote_age_seconds", "time_since_quote_update_seconds",
    "repricing_velocity", "repricing_acceleration",
    "yes_change_frequency_30s", "no_change_frequency_30s",
    "consecutive_quote_stability", "bid_ask_spread",
    "spread_change", "spread_velocity", "spread_compression",
    "yes_bid_size", "yes_ask_size", "total_bid_depth", "total_ask_depth",
    "book_imbalance", "market_refresh_latency",
    "cross_asset_yes_dispersion", "cross_asset_relative_yes",
)
CORE_FEATURE_COLUMNS = tuple(
    name for name in FEATURE_COLUMNS if name not in MICROSTRUCTURE_FEATURE_COLUMNS
)
NUMERIC_COLUMNS = tuple(
    name for name in COLUMNS if name not in IDENTIFIER_COLUMNS
)
