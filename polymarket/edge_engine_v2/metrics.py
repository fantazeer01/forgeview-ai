from __future__ import annotations

import math
import statistics


def max_drawdown(equity: list[float]) -> float:
    if not equity:
        return 0.0
    peak = equity[0]
    worst = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            worst = max(worst, (peak - value) / peak)
    return worst


def safe_stdev(values: list[float]) -> float:
    return statistics.pstdev(values) if len(values) > 1 else 0.0


def clamp_score(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def coefficient_stability(values: list[float]) -> float:
    if not values:
        return 0.0
    if all(abs(value) < 1e-9 for value in values):
        return 0.0
    mean_abs = abs(statistics.fmean(values))
    dispersion = safe_stdev(values)
    if mean_abs < 1e-9:
        return 0.0 if dispersion else 100.0
    return clamp_score(100.0 / (1.0 + dispersion / mean_abs))


def downside_ratio(value: float, reference: float) -> float:
    if reference <= 0:
        return 0.0
    return max(0.0, min(1.0, value / reference))
