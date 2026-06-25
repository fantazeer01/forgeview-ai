from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass

from polymarket.edge_engine_v2.metrics import max_drawdown
from polymarket.edge_engine_v3.models import ShadowTrade
from polymarket.edge_engine_v4.opportunity import Opportunity


@dataclass(frozen=True)
class EvidenceMetrics:
    total_markets_observed: int
    completed_market_windows: int
    opportunities_detected: int
    opportunity_rate: float
    shadow_trades: int
    simulated_pnl: float
    win_rate: float
    avg_win: float
    avg_loss: float
    max_drawdown: float
    edge_decay: float
    latency_sensitivity: float
    reference_coverage_percentage: float
    data_gap_percentage: float


def aggregate_metrics(
    total_markets: int,
    completed_windows: int,
    opportunities: list[Opportunity],
    trades: list[ShadowTrade],
    expected_reference_points: int,
    successful_reference_points: int,
    expected_market_points: int,
    successful_market_points: int,
) -> EvidenceMetrics:
    pnls = [trade.pnl for trade in trades]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    equity = [10_000.0]
    for pnl in pnls:
        equity.append(equity[-1] + pnl)
    halfway = max(1, len(pnls) // 2)
    early = sum(pnls[:halfway])
    late = sum(pnls[halfway:])
    edge_decay = max(0.0, min(1.0, (early - late) / max(abs(early), 1.0)))

    # One-poll latency stress: adverse 20 bps round-trip per trade.
    stressed_pnl = sum(
        trade.pnl - trade.quantity * 0.002
        for trade in trades
    )
    total_pnl = sum(pnls)
    latency_sensitivity = max(
        0.0,
        min(1.0, (total_pnl - stressed_pnl) / max(abs(total_pnl), 1.0)),
    )
    reference_coverage = (
        successful_reference_points / expected_reference_points
        if expected_reference_points else 0.0
    )
    data_gap = (
        1.0 - successful_market_points / expected_market_points
        if expected_market_points else 1.0
    )
    return EvidenceMetrics(
        total_markets_observed=total_markets,
        completed_market_windows=completed_windows,
        opportunities_detected=len(opportunities),
        opportunity_rate=round(
            len(opportunities) / completed_windows, 6
        ) if completed_windows else 0.0,
        shadow_trades=len(trades),
        simulated_pnl=round(total_pnl, 6),
        win_rate=round(len(wins) / len(pnls), 6) if pnls else 0.0,
        avg_win=round(statistics.fmean(wins), 6) if wins else 0.0,
        avg_loss=round(statistics.fmean(losses), 6) if losses else 0.0,
        max_drawdown=round(max_drawdown(equity), 8),
        edge_decay=round(edge_decay, 6),
        latency_sensitivity=round(latency_sensitivity, 6),
        reference_coverage_percentage=round(reference_coverage * 100.0, 4),
        data_gap_percentage=round(data_gap * 100.0, 4),
    )
