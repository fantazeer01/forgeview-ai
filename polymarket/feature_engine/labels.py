from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class OutcomeLabel:
    outcome: int
    resolution_timestamp: datetime
    source: str


def resolve_from_reference(
    window_start: datetime,
    window_end: datetime,
    prices: list[tuple[datetime, float]],
    tolerance_seconds: float,
) -> OutcomeLabel | None:
    if not prices:
        return None
    ordered = sorted(prices)
    opening = min(ordered, key=lambda row: abs((row[0] - window_start).total_seconds()))
    closing = min(ordered, key=lambda row: abs((row[0] - window_end).total_seconds()))
    if abs((opening[0] - window_start).total_seconds()) > tolerance_seconds:
        return None
    if abs((closing[0] - window_end).total_seconds()) > tolerance_seconds:
        return None
    return OutcomeLabel(
        outcome=int(closing[1] >= opening[1]),
        resolution_timestamp=window_end,
        source="reference_window_return",
    )
