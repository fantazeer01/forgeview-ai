"""Schema definitions for research-only wallet intelligence records.

This module contains data shapes only. It has no wallet, key, trading, capture,
or model-training capability.
"""

from dataclasses import dataclass


WATCHED_WALLETS_FIELDS = [
    "wallet_id",
    "profile_url",
    "label",
    "source",
    "notes",
]


WALLET_RESEARCH_FIELDS = [
    "wallet_id",
    "profile_url",
    "label",
    "source",
    "notes",
    "total_pnl",
    "prediction_count",
    "biggest_win",
    "active_position_count",
    "closed_position_count",
    "market_types",
    "btc_exposure",
    "eth_exposure",
    "sol_exposure",
    "yes_position_count",
    "no_position_count",
    "yes_no_distribution",
    "average_entry_price",
    "average_exit_or_resolution_price",
    "average_holding_time_seconds",
    "position_sizing_summary",
    "repeated_market_patterns",
    "late_entry_behavior",
    "cheap_side_buying_behavior",
    "hold_to_resolution_vs_exit_before_expiry",
    "drawdown_behavior",
    "copyability_score",
    "copyability_notes",
]


TRADE_HISTORY_FIELDS = [
    "wallet_id",
    "profile_url",
    "source_endpoint",
    "source_endpoint_name",
    "activity_type",
    "activity_timestamp",
    "activity_datetime_utc",
    "transaction_hash",
    "condition_id",
    "token_id",
    "asset_id",
    "market_slug",
    "event_slug",
    "market_title",
    "outcome",
    "outcome_index",
    "side",
    "price",
    "size",
    "notional_value",
    "notional_source",
    "market_type",
    "asset_class",
    "up_down_market",
    "time_to_expiry_seconds",
    "expiry_timestamp",
    "expiry_source",
    "entry_or_exit_candidate",
    "lifecycle_group_key",
    "dedupe_key",
    "source_fetch_timestamp",
    "raw_payload_hash",
    "raw_page_hash",
    "normalization_version",
    "data_quality_flags",
]


LIFECYCLE_POSITION_FIELDS = [
    "wallet_id",
    "profile_url",
    "condition_id",
    "token_id",
    "outcome",
    "lifecycle_group_key",
    "market_slug",
    "event_slug",
    "market_title",
    "market_type",
    "asset_class",
    "up_down_market",
    "first_activity_timestamp",
    "first_activity_datetime_utc",
    "last_activity_timestamp",
    "last_activity_datetime_utc",
    "buy_trade_count",
    "sell_trade_count",
    "total_bought_size",
    "total_sold_size",
    "remaining_size",
    "oversold_size",
    "weighted_average_entry_price",
    "weighted_average_exit_price",
    "status",
    "negative_position_detected",
    "negative_position_reason",
    "position_size_conserved",
    "transaction_hashes",
    "data_quality_flags",
]

MARKET_OUTCOME_JOIN_FIELDS = [
    "wallet_id",
    "profile_url",
    "condition_id",
    "token_id",
    "outcome",
    "lifecycle_group_key",
    "market_slug",
    "event_slug",
    "market_title",
    "market_type",
    "asset_class",
    "up_down_market",
    "first_activity_timestamp",
    "first_activity_datetime_utc",
    "last_activity_timestamp",
    "last_activity_datetime_utc",
    "lifecycle_status",
    "market_id",
    "event_id",
    "expiry_timestamp",
    "resolution_timestamp",
    "resolved_status",
    "winning_outcome",
    "outcome_prices",
    "lifecycle_resolution_status",
    "join_confidence",
    "join_status",
    "join_reason",
    "metadata_sources",
    "condition_id_match",
    "token_outcome_cross_check",
    "conflicting_metadata",
]


@dataclass(frozen=True)
class WatchedWallet:
    wallet_id: str
    profile_url: str
    label: str = ""
    source: str = ""
    notes: str = ""


@dataclass(frozen=True)
class WalletResearchRecord:
    wallet_id: str
    profile_url: str
    label: str = ""
    source: str = ""
    notes: str = ""
    total_pnl: str = ""
    prediction_count: str = ""
    biggest_win: str = ""
    active_position_count: str = ""
    closed_position_count: str = ""
    market_types: str = ""
    btc_exposure: str = ""
    eth_exposure: str = ""
    sol_exposure: str = ""
    yes_position_count: str = ""
    no_position_count: str = ""
    yes_no_distribution: str = ""
    average_entry_price: str = ""
    average_exit_or_resolution_price: str = ""
    average_holding_time_seconds: str = ""
    position_sizing_summary: str = ""
    repeated_market_patterns: str = ""
    late_entry_behavior: str = ""
    cheap_side_buying_behavior: str = ""
    hold_to_resolution_vs_exit_before_expiry: str = ""
    drawdown_behavior: str = ""
    copyability_score: str = ""
    copyability_notes: str = ""


@dataclass(frozen=True)
class TradeHistoryRecord:
    wallet_id: str
    profile_url: str
    source_endpoint: str
    source_endpoint_name: str
    activity_type: str
    activity_timestamp: str
    activity_datetime_utc: str
    transaction_hash: str
    condition_id: str
    token_id: str
    asset_id: str
    market_slug: str
    event_slug: str
    market_title: str
    outcome: str
    outcome_index: str
    side: str
    price: str
    size: str
    notional_value: str
    notional_source: str
    market_type: str
    asset_class: str
    up_down_market: str
    time_to_expiry_seconds: str
    expiry_timestamp: str
    expiry_source: str
    entry_or_exit_candidate: str
    lifecycle_group_key: str
    dedupe_key: str
    source_fetch_timestamp: str
    raw_payload_hash: str
    raw_page_hash: str
    normalization_version: str
    data_quality_flags: str


@dataclass(frozen=True)
class LifecyclePositionRecord:
    wallet_id: str
    profile_url: str
    condition_id: str
    token_id: str
    outcome: str
    lifecycle_group_key: str
    market_slug: str
    event_slug: str
    market_title: str
    market_type: str
    asset_class: str
    up_down_market: str
    first_activity_timestamp: str
    first_activity_datetime_utc: str
    last_activity_timestamp: str
    last_activity_datetime_utc: str
    buy_trade_count: str
    sell_trade_count: str
    total_bought_size: str
    total_sold_size: str
    remaining_size: str
    oversold_size: str
    weighted_average_entry_price: str
    weighted_average_exit_price: str
    status: str
    negative_position_detected: str
    negative_position_reason: str
    position_size_conserved: str
    transaction_hashes: str
    data_quality_flags: str


@dataclass(frozen=True)
class MarketOutcomeJoinRecord:
    wallet_id: str
    profile_url: str
    condition_id: str
    token_id: str
    outcome: str
    lifecycle_group_key: str
    market_slug: str
    event_slug: str
    market_title: str
    market_type: str
    asset_class: str
    up_down_market: str
    first_activity_timestamp: str
    first_activity_datetime_utc: str
    last_activity_timestamp: str
    last_activity_datetime_utc: str
    lifecycle_status: str
    market_id: str
    event_id: str
    expiry_timestamp: str
    resolution_timestamp: str
    resolved_status: str
    winning_outcome: str
    outcome_prices: str
    lifecycle_resolution_status: str
    join_confidence: str
    join_status: str
    join_reason: str
    metadata_sources: str
    condition_id_match: str
    token_outcome_cross_check: str
    conflicting_metadata: str
