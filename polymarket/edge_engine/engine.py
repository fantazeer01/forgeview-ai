from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .data import MarketDataProvider
from .decision import DecisionEngine
from .execution import PaperExecutionEngine
from .logging import RunLogger, configure_logger
from .models import ExitReason, MarketSnapshot, Position, ScoreBreakdown
from .pnl import PnLTracker
from .scoring import EdgeScorer


@dataclass(frozen=True)
class EngineConfig:
    initial_cash: float = 10_000.0
    stake_per_trade: float = 100.0
    entry_threshold: float = 0.7
    exit_threshold: float = 0.3
    convergence_threshold: float = 0.03
    timeout_steps: int = 3
    slippage_bps: float = 0.0
    close_at_end: bool = True
    output_dir: Path = Path("polymarket/runs/latest")
    verbose: bool = False


class EdgeEngine:
    def __init__(self, provider: MarketDataProvider, config: EngineConfig | None = None) -> None:
        self.provider = provider
        self.config = config or EngineConfig()
        self.scorer = EdgeScorer()
        self.decisions = DecisionEngine(
            entry_threshold=self.config.entry_threshold,
            exit_threshold=self.config.exit_threshold,
            convergence_threshold=self.config.convergence_threshold,
            timeout_steps=self.config.timeout_steps,
        )
        self.execution = PaperExecutionEngine(
            stake_per_trade=self.config.stake_per_trade,
            slippage_bps=self.config.slippage_bps,
        )
        self.pnl = PnLTracker(self.config.initial_cash)
        self.positions: dict[str, Position] = {}
        self.market_steps: dict[str, int] = {}
        self.last_observation: dict[str, tuple[MarketSnapshot, ScoreBreakdown, int]] = {}
        self.run_log = RunLogger(self.config.output_dir)
        self.logger = configure_logger(self.config.verbose)

    def run(self) -> dict[str, float | int]:
        last_timestamp: datetime | None = None
        snapshots_seen = 0

        for snapshot in self.provider.snapshots():
            snapshots_seen += 1
            last_timestamp = snapshot.timestamp
            step = self.market_steps.get(snapshot.market_id, 0)
            breakdown = self.scorer.score(snapshot)
            position = self.positions.get(snapshot.market_id)

            if position:
                self.execution.mark(position, snapshot, breakdown)
            decision = self.decisions.decide(snapshot, breakdown, position, step)
            self.run_log.event(
                "decision",
                {"snapshot": snapshot, "score": breakdown, "decision": decision, "step": step},
            )

            if decision.action == "OPEN" and decision.side is not None:
                opened = self.execution.open_position(snapshot, breakdown, decision.side, step)
                self.positions[snapshot.market_id] = opened
                self.logger.info(
                    "OPEN  %-3s %-14s price=%.3f score=%.3f stake=$%.2f",
                    opened.side.value, opened.market_id, opened.entry_price,
                    opened.entry_score, opened.cost,
                )
                self.run_log.event("trade_opened", {"position": opened})
            elif decision.action == "CLOSE" and position is not None:
                trade = self.execution.close_position(
                    position, snapshot, breakdown, ExitReason(decision.reason), step
                )
                self.pnl.record_close(trade)
                del self.positions[snapshot.market_id]
                self.logger.info(
                    "CLOSE %-3s %-14s price=%.3f pnl=%+.2f reason=%s",
                    trade.side.value, trade.market_id, trade.exit_price,
                    trade.pnl, trade.exit_reason.value,
                )
                self.run_log.event("trade_closed", {"trade": trade})

            self.last_observation[snapshot.market_id] = (snapshot, breakdown, step)
            self.market_steps[snapshot.market_id] = step + 1
            self.run_log.equity(snapshot.timestamp, self.pnl.summary(list(self.positions.values())))

        if snapshots_seen == 0:
            raise ValueError("Market data provider returned no snapshots")
        if self.config.close_at_end:
            self._close_remaining_positions()

        summary = self.pnl.summary(list(self.positions.values()))
        summary["snapshots_processed"] = snapshots_seen
        self.run_log.write_trades(self.pnl.closed_trades)
        self.run_log.write_summary(summary)
        if last_timestamp is not None:
            self.run_log.equity(last_timestamp, summary)
        return summary

    def _close_remaining_positions(self) -> None:
        for market_id, position in list(self.positions.items()):
            snapshot, breakdown, step = self.last_observation[market_id]
            trade = self.execution.close_position(
                position, snapshot, breakdown, ExitReason.END_OF_DATA, step
            )
            self.pnl.record_close(trade)
            del self.positions[market_id]
            self.logger.info(
                "CLOSE %-3s %-14s price=%.3f pnl=%+.2f reason=%s",
                trade.side.value, trade.market_id, trade.exit_price,
                trade.pnl, trade.exit_reason.value,
            )
            self.run_log.event("trade_closed", {"trade": trade})
