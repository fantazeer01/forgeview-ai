from __future__ import annotations

from .models import Decision, ExitReason, MarketSnapshot, Position, ScoreBreakdown, Side


class DecisionEngine:
    def __init__(
        self,
        entry_threshold: float = 0.7,
        exit_threshold: float = 0.3,
        convergence_threshold: float = 0.03,
        timeout_steps: int = 3,
    ) -> None:
        if exit_threshold >= entry_threshold:
            raise ValueError("exit_threshold must be below entry_threshold")
        if timeout_steps < 1:
            raise ValueError("timeout_steps must be at least 1")
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.convergence_threshold = convergence_threshold
        self.timeout_steps = timeout_steps

    def decide(
        self,
        snapshot: MarketSnapshot,
        breakdown: ScoreBreakdown,
        position: Position | None,
        step: int,
    ) -> Decision:
        if position is None:
            if breakdown.score > self.entry_threshold:
                side = Side.YES if snapshot.reference_probability > snapshot.yes_price else Side.NO
                return Decision("OPEN", side, "edge_score_above_threshold")
            return Decision("HOLD", reason="no_entry")

        if breakdown.score < self.exit_threshold:
            return Decision("CLOSE", position.side, ExitReason.SCORE.value)
        if abs(snapshot.reference_probability - snapshot.yes_price) <= self.convergence_threshold:
            return Decision("CLOSE", position.side, ExitReason.CONVERGENCE.value)
        if step - position.opened_step >= self.timeout_steps:
            return Decision("CLOSE", position.side, ExitReason.TIMEOUT.value)
        return Decision("HOLD", position.side, "position_open")
