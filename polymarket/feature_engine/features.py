from __future__ import annotations

import math
from datetime import datetime, timedelta
from statistics import pstdev


def value_at_or_before(
    series: list[tuple[datetime, float]],
    target: datetime,
    max_age_seconds: float | None = None,
) -> float | None:
    candidates = [
        (timestamp, value) for timestamp, value in series if timestamp <= target
    ]
    if not candidates:
        return None
    timestamp, value = candidates[-1]
    if (
        max_age_seconds is not None
        and (target - timestamp).total_seconds() > max_age_seconds
    ):
        return None
    return value


def nearest_at_or_after(
    series: list[tuple[datetime, object]], target: datetime, before: datetime
) -> tuple[datetime, object] | None:
    return next(
        ((timestamp, value) for timestamp, value in series
         if target <= timestamp < before),
        None,
    )


def simple_return(
    series: list[tuple[datetime, float]],
    anchor: datetime,
    seconds: int,
    max_age_seconds: float | None = None,
) -> float | None:
    current = value_at_or_before(series, anchor, max_age_seconds)
    previous = value_at_or_before(
        series, anchor - timedelta(seconds=seconds), max_age_seconds
    )
    if current is None or previous in (None, 0):
        return None
    return current / previous - 1.0


def momentum(short_return: float | None, long_return: float | None) -> float | None:
    if short_return is None or long_return is None:
        return None
    return short_return - long_return


def realized_volatility(
    series: list[tuple[datetime, float]], anchor: datetime, seconds: int
) -> float | None:
    start = anchor - timedelta(seconds=seconds)
    values = [value for timestamp, value in series if start <= timestamp <= anchor]
    if len(values) < 3:
        return None
    returns = [
        math.log(current / previous)
        for previous, current in zip(values, values[1:])
        if previous > 0 and current > 0
    ]
    return pstdev(returns) if len(returns) >= 2 else None


def change(
    series: list[tuple[datetime, float]],
    anchor: datetime,
    seconds: int,
    max_age_seconds: float | None = None,
) -> float | None:
    current = value_at_or_before(series, anchor, max_age_seconds)
    previous = value_at_or_before(
        series, anchor - timedelta(seconds=seconds), max_age_seconds
    )
    if current is None or previous is None:
        return None
    return current - previous
