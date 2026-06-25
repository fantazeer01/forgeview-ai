"""Research-only wallet intelligence schema for public Polymarket profiles."""

from .ingestion import ingest_wallets, inspect_outputs, summarize_outputs
from .schema import (
    TRADE_HISTORY_FIELDS,
    WALLET_RESEARCH_FIELDS,
    WATCHED_WALLETS_FIELDS,
    TradeHistoryRecord,
    WalletResearchRecord,
    WatchedWallet,
)
from .trade_history import run_fixture_ingestion

__all__ = [
    "WALLET_RESEARCH_FIELDS",
    "WATCHED_WALLETS_FIELDS",
    "TRADE_HISTORY_FIELDS",
    "TradeHistoryRecord",
    "WalletResearchRecord",
    "WatchedWallet",
    "ingest_wallets",
    "inspect_outputs",
    "run_fixture_ingestion",
    "summarize_outputs",
]
