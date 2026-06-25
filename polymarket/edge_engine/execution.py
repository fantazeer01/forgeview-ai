from __future__ import annotations

from uuid import uuid4

from .models import ClosedTrade, ExitReason, MarketSnapshot, Position, ScoreBreakdown, Side


class PaperExecutionEngine:
    def __init__(self, stake_per_trade: float = 100.0, slippage_bps: float = 0.0) -> None:
        if stake_per_trade <= 0:
            raise ValueError("stake_per_trade must be positive")
        if slippage_bps < 0:
            raise ValueError("slippage_bps cannot be negative")
        self.stake_per_trade = stake_per_trade
        self.slippage = slippage_bps / 10_000.0

    def open_position(
        self,
        snapshot: MarketSnapshot,
        breakdown: ScoreBreakdown,
        side: Side,
        step: int,
    ) -> Position:
        raw_price = snapshot.contract_price(side)
        fill_price = min(0.999999, raw_price * (1.0 + self.slippage))
        quantity = self.stake_per_trade / fill_price
        return Position(
            trade_id=uuid4().hex[:12],
            market_id=snapshot.market_id,
            question=snapshot.question,
            side=side,
            quantity=quantity,
            entry_price=fill_price,
            entry_score=breakdown.score,
            opened_at=snapshot.timestamp,
            opened_step=step,
            last_price=fill_price,
            last_score=breakdown.score,
        )

    def mark(self, position: Position, snapshot: MarketSnapshot, breakdown: ScoreBreakdown) -> None:
        position.last_price = snapshot.contract_price(position.side)
        position.last_score = breakdown.score

    def close_position(
        self,
        position: Position,
        snapshot: MarketSnapshot,
        breakdown: ScoreBreakdown,
        reason: ExitReason,
        step: int,
    ) -> ClosedTrade:
        raw_price = snapshot.contract_price(position.side)
        exit_price = max(0.000001, raw_price * (1.0 - self.slippage))
        pnl = (exit_price - position.entry_price) * position.quantity
        return ClosedTrade(
            trade_id=position.trade_id,
            market_id=position.market_id,
            question=position.question,
            side=position.side,
            quantity=position.quantity,
            entry_price=position.entry_price,
            exit_price=exit_price,
            entry_score=position.entry_score,
            exit_score=breakdown.score,
            opened_at=position.opened_at,
            closed_at=snapshot.timestamp,
            exit_reason=reason,
            pnl=pnl,
            return_pct=pnl / position.cost,
            holding_steps=step - position.opened_step,
        )
