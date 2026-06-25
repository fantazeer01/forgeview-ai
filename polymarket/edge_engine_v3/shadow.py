from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from polymarket.edge_engine.decision import DecisionEngine
from polymarket.edge_engine.models import MarketSnapshot, Side
from polymarket.edge_engine.scoring import EdgeScorer

from .models import ShadowDecision, ShadowTrade


@dataclass
class _Position:
    trade_id: str
    market_id: str
    side: Side
    opened_at: datetime
    entry_price: float
    quantity: float
    entry_score: float
    opened_step: int


class ShadowExecutionEngine:
    """Pure simulation. It contains no network or order-submission capability."""

    def __init__(
        self,
        stake: float = 100.0,
        slippage_bps: float = 10.0,
        timeout_updates: int = 8,
    ) -> None:
        self.stake = stake
        self.slippage = slippage_bps / 10_000.0
        self.scorer = EdgeScorer()
        self.decider = DecisionEngine(timeout_steps=timeout_updates)
        self.positions: dict[str, _Position] = {}
        self.steps: dict[str, int] = {}
        self.decisions: list[ShadowDecision] = []
        self.trades: list[ShadowTrade] = []
        self.latest: dict[str, MarketSnapshot] = {}
        self.sequence = 0

    def on_snapshot(self, snapshot: MarketSnapshot) -> ShadowDecision:
        market = snapshot.market_id
        step = self.steps.get(market, 0)
        score = self.scorer.score(snapshot)
        position = self.positions.get(market)
        proxy = None
        if position:
            proxy = type("PositionProxy", (), {
                "side": position.side,
                "opened_step": position.opened_step,
            })()
        decision = self.decider.decide(snapshot, score, proxy, step)
        log = ShadowDecision(
            snapshot.timestamp, market, decision.action, decision.side,
            score.score, snapshot.yes_price, snapshot.reference_probability,
            decision.reason,
        )
        self.decisions.append(log)
        if decision.action == "OPEN" and decision.side is not None:
            self.sequence += 1
            raw = snapshot.contract_price(decision.side)
            fill = min(0.999999, raw + self.slippage)
            self.positions[market] = _Position(
                f"shadow-{self.sequence:06d}", market, decision.side,
                snapshot.timestamp, fill, self.stake / fill, score.score, step,
            )
        elif decision.action == "CLOSE" and position:
            self._close(position, snapshot, score.score, decision.reason, step)
            del self.positions[market]
        self.latest[market] = snapshot
        self.steps[market] = step + 1
        return log

    def finalize(self) -> None:
        for market, position in list(self.positions.items()):
            snapshot = self.latest[market]
            score = self.scorer.score(snapshot).score
            self._close(position, snapshot, score, "end_of_session", self.steps[market])
            del self.positions[market]

    def _close(self, position: _Position, snapshot: MarketSnapshot, score: float, reason: str, step: int) -> None:
        exit_price = max(0.000001, snapshot.contract_price(position.side) - self.slippage)
        pnl = (exit_price - position.entry_price) * position.quantity
        self.trades.append(ShadowTrade(
            trade_id=position.trade_id,
            market_id=position.market_id,
            side=position.side,
            opened_at=position.opened_at,
            closed_at=snapshot.timestamp,
            entry_price=round(position.entry_price, 6),
            exit_price=round(exit_price, 6),
            quantity=round(position.quantity, 8),
            entry_score=position.entry_score,
            exit_score=score,
            exit_reason=reason,
            pnl=round(pnl, 6),
            return_pct=round(pnl / self.stake, 8),
            holding_updates=step - position.opened_step,
        ))
