from __future__ import annotations

from dataclasses import dataclass

from polymarket.edge_engine.decision import DecisionEngine
from polymarket.edge_engine.models import MarketSnapshot, Side
from polymarket.edge_engine.scoring import EdgeScorer

from .metrics import max_drawdown
from .models import ExecutedTrade, OpenPosition, WindowResult


@dataclass(frozen=True)
class SimulatorConfig:
    initial_cash: float = 10_000.0
    stake: float = 100.0
    entry_threshold: float = 0.7
    exit_threshold: float = 0.3
    convergence: float = 0.03
    timeout_steps: int = 8
    slippage_bps: float = 10.0
    latency_steps: int = 1


@dataclass(frozen=True)
class _PendingOrder:
    action: str
    market_id: str
    side: Side
    signal_step: int
    execute_step: int
    signal_snapshot: MarketSnapshot
    score: float
    reason: str


class WindowSimulator:
    def __init__(self, config: SimulatorConfig) -> None:
        self.config = config
        self.scorer = EdgeScorer()
        self.decisions = DecisionEngine(
            entry_threshold=config.entry_threshold,
            exit_threshold=config.exit_threshold,
            convergence_threshold=config.convergence,
            timeout_steps=config.timeout_steps,
        )

    def run(
        self,
        snapshots: list[MarketSnapshot],
        run_id: str,
        window_id: int,
    ) -> tuple[WindowResult, list[ExecutedTrade]]:
        ordered = sorted(snapshots, key=lambda row: (row.timestamp, row.market_id))
        positions: dict[str, OpenPosition] = {}
        pending: dict[str, _PendingOrder] = {}
        market_steps: dict[str, int] = {}
        latest: dict[str, MarketSnapshot] = {}
        trades: list[ExecutedTrade] = []
        realized = 0.0
        equity_curve = [self.config.initial_cash]
        trade_sequence = 0

        for snapshot in ordered:
            market_id = snapshot.market_id
            step = market_steps.get(market_id, 0)
            latest[market_id] = snapshot

            order = pending.get(market_id)
            if order and step >= order.execute_step:
                if order.action == "OPEN" and market_id not in positions:
                    trade_sequence += 1
                    raw = snapshot.contract_price(order.side)
                    entry_price = min(0.999999, raw + self.config.slippage_bps / 10_000.0)
                    positions[market_id] = OpenPosition(
                        trade_id=f"{run_id}-w{window_id:02d}-t{trade_sequence:04d}",
                        run_id=run_id,
                        window_id=window_id,
                        market_id=market_id,
                        side=order.side,
                        signal_at=order.signal_snapshot.timestamp,
                        opened_at=snapshot.timestamp,
                        entry_price=entry_price,
                        quantity=self.config.stake / entry_price,
                        entry_score=order.score,
                        opened_step=step,
                        entry_delay_steps=step - order.signal_step,
                    )
                elif order.action == "CLOSE" and market_id in positions:
                    trade = self._close(
                        positions.pop(market_id), snapshot, order.score,
                        order.reason, step,
                    )
                    trades.append(trade)
                    realized += trade.pnl
                pending.pop(market_id, None)

            position = positions.get(market_id)
            breakdown = self.scorer.score(snapshot)
            proxy_position = None
            if position is not None:
                # DecisionEngine only needs side and opened_step from this object.
                proxy_position = type("PositionProxy", (), {
                    "side": position.side,
                    "opened_step": position.opened_step,
                })()
            decision = self.decisions.decide(snapshot, breakdown, proxy_position, step)
            if market_id not in pending:
                if decision.action == "OPEN" and decision.side is not None:
                    if self.config.latency_steps == 0:
                        trade_sequence += 1
                        raw = snapshot.contract_price(decision.side)
                        entry_price = min(0.999999, raw + self.config.slippage_bps / 10_000.0)
                        positions[market_id] = OpenPosition(
                            trade_id=f"{run_id}-w{window_id:02d}-t{trade_sequence:04d}",
                            run_id=run_id,
                            window_id=window_id,
                            market_id=market_id,
                            side=decision.side,
                            signal_at=snapshot.timestamp,
                            opened_at=snapshot.timestamp,
                            entry_price=entry_price,
                            quantity=self.config.stake / entry_price,
                            entry_score=breakdown.score,
                            opened_step=step,
                            entry_delay_steps=0,
                        )
                    else:
                        pending[market_id] = _PendingOrder(
                            "OPEN", market_id, decision.side, step,
                            step + self.config.latency_steps, snapshot,
                            breakdown.score, decision.reason,
                        )
                elif decision.action == "CLOSE" and position is not None:
                    if self.config.latency_steps == 0:
                        trade = self._close(
                            positions.pop(market_id), snapshot, breakdown.score,
                            decision.reason, step,
                        )
                        trades.append(trade)
                        realized += trade.pnl
                    else:
                        pending[market_id] = _PendingOrder(
                            "CLOSE", market_id, position.side, step,
                            step + self.config.latency_steps, snapshot,
                            breakdown.score, decision.reason,
                        )

            unrealized = sum(
                (latest[pos.market_id].contract_price(pos.side) - pos.entry_price) * pos.quantity
                for pos in positions.values()
                if pos.market_id in latest
            )
            equity_curve.append(self.config.initial_cash + realized + unrealized)
            market_steps[market_id] = step + 1

        for market_id, position in list(positions.items()):
            snapshot = latest[market_id]
            score = self.scorer.score(snapshot).score
            step = market_steps[market_id]
            trade = self._close(position, snapshot, score, "end_of_window", step)
            trades.append(trade)
            realized += trade.pnl

        equity_curve.append(self.config.initial_cash + realized)
        wins = sum(trade.pnl > 0 for trade in trades)
        result = WindowResult(
            run_id=run_id,
            window_id=window_id,
            start=ordered[0].timestamp,
            end=ordered[-1].timestamp,
            snapshots=len(ordered),
            trades=len(trades),
            pnl=round(realized, 6),
            return_pct=round(realized / self.config.initial_cash, 8),
            max_drawdown=round(max_drawdown(equity_curve), 8),
            win_rate=round(wins / len(trades), 6) if trades else 0.0,
        )
        return result, trades

    def _close(
        self,
        position: OpenPosition,
        snapshot: MarketSnapshot,
        score: float,
        reason: str,
        step: int,
    ) -> ExecutedTrade:
        raw = snapshot.contract_price(position.side)
        exit_price = max(0.000001, raw - self.config.slippage_bps / 10_000.0)
        pnl = (exit_price - position.entry_price) * position.quantity
        return ExecutedTrade(
            trade_id=position.trade_id,
            run_id=position.run_id,
            window_id=position.window_id,
            market_id=position.market_id,
            side=position.side,
            signal_at=position.signal_at,
            opened_at=position.opened_at,
            closed_at=snapshot.timestamp,
            entry_price=entry_price_round(position.entry_price),
            exit_price=entry_price_round(exit_price),
            quantity=round(position.quantity, 8),
            entry_score=position.entry_score,
            exit_score=score,
            exit_reason=reason,
            pnl=round(pnl, 6),
            return_pct=round(pnl / self.config.stake, 8),
            holding_steps=step - position.opened_step,
            entry_delay_steps=position.entry_delay_steps,
        )


def entry_price_round(value: float) -> float:
    return round(value, 6)
