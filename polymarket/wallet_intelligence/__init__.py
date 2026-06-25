"""Research-only wallet intelligence schema for public Polymarket profiles."""

from .ingestion import ingest_wallets, inspect_outputs, summarize_outputs
from .schema import (
    LIFECYCLE_POSITION_FIELDS,
    TRADE_HISTORY_FIELDS,
    WALLET_RESEARCH_FIELDS,
    WATCHED_WALLETS_FIELDS,
    LifecyclePositionRecord,
    TradeHistoryRecord,
    WalletResearchRecord,
    WatchedWallet,
)
from .trade_history import run_fixture_ingestion
from .lifecycle import run_lifecycle_fixture_reconstruction
from .lifecycle_metrics import run_lifecycle_metrics
from .wallet_score import run_wallet_score_fixture
from .wallet_watchlist import run_wallet_watchlist
from .copyability_sprint import run_wallet_copyability_sprint

__all__ = [
    "LIFECYCLE_POSITION_FIELDS",
    "WALLET_RESEARCH_FIELDS",
    "WATCHED_WALLETS_FIELDS",
    "TRADE_HISTORY_FIELDS",
    "LifecyclePositionRecord",
    "TradeHistoryRecord",
    "WalletResearchRecord",
    "WatchedWallet",
    "ingest_wallets",
    "inspect_outputs",
    "run_fixture_ingestion",
    "run_lifecycle_fixture_reconstruction",
    "run_lifecycle_metrics",
    "run_wallet_score_fixture",
    "run_wallet_watchlist",
    "run_wallet_copyability_sprint",
    "summarize_outputs",
]
