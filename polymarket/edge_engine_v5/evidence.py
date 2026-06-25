from __future__ import annotations

from enum import Enum

from .config import CaptureConfig
from .metrics import EvidenceMetrics
from polymarket.edge_engine_v4.opportunity import Opportunity


class EvidenceVerdict(str, Enum):
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NO_EDGE = "NO_EDGE"
    WEAK_EDGE = "WEAK_EDGE"
    POTENTIAL_EDGE = "POTENTIAL_EDGE"


class OpportunityGate:
    """Conservatively permits at most one opportunity per market window."""

    def __init__(self) -> None:
        self._emitted_markets: set[str] = set()

    def accept(self, opportunity: Opportunity) -> bool:
        if opportunity.market_id in self._emitted_markets:
            return False
        self._emitted_markets.add(opportunity.market_id)
        return True


def evidence_verdict(metrics: EvidenceMetrics, config: CaptureConfig) -> EvidenceVerdict:
    reference_coverage = metrics.reference_coverage_percentage / 100.0
    data_gap = metrics.data_gap_percentage / 100.0
    if (
        metrics.completed_market_windows < config.min_completed_windows
        or metrics.shadow_trades < config.min_shadow_trades
        or reference_coverage < config.min_reference_coverage
        or data_gap > config.max_data_gap
    ):
        return EvidenceVerdict.INSUFFICIENT_DATA
    if (
        metrics.simulated_pnl <= 0
        or metrics.win_rate < 0.45
        or metrics.max_drawdown > config.max_drawdown * 2
        or metrics.edge_decay > 0.80
    ):
        return EvidenceVerdict.NO_EDGE
    if (
        metrics.simulated_pnl > 0
        and metrics.win_rate >= 0.50
        and metrics.max_drawdown <= config.max_drawdown
        and metrics.edge_decay <= config.max_edge_decay
        and metrics.latency_sensitivity <= config.max_latency_sensitivity
    ):
        return EvidenceVerdict.POTENTIAL_EDGE
    return EvidenceVerdict.WEAK_EDGE
