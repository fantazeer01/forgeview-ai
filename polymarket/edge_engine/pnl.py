from __future__ import annotations

from dataclasses import dataclass, field

from .models import ClosedTrade, Position


@dataclass
class PnLTracker:
    initial_cash: float
    realized_pnl: float = 0.0
    closed_trades: list[ClosedTrade] = field(default_factory=list)

    def record_close(self, trade: ClosedTrade) -> None:
        self.closed_trades.append(trade)
        self.realized_pnl += trade.pnl

    def unrealized_pnl(self, positions: list[Position]) -> float:
        return sum(position.unrealized_pnl() for position in positions)

    def summary(self, positions: list[Position]) -> dict[str, float | int]:
        unrealized = self.unrealized_pnl(positions)
        wins = sum(trade.pnl > 0 for trade in self.closed_trades)
        losses = sum(trade.pnl < 0 for trade in self.closed_trades)
        total = len(self.closed_trades)
        return {
            "initial_cash": round(self.initial_cash, 2),
            "realized_pnl": round(self.realized_pnl, 2),
            "unrealized_pnl": round(unrealized, 2),
            "total_pnl": round(self.realized_pnl + unrealized, 2),
            "ending_equity": round(self.initial_cash + self.realized_pnl + unrealized, 2),
            "closed_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / total, 4) if total else 0.0,
            "open_positions": len(positions),
        }
