from __future__ import annotations

import math
from typing import Iterable


EPSILON = 1e-12


def probability_metrics(
    outcomes: list[int], probabilities: list[float]
) -> dict:
    if len(outcomes) != len(probabilities) or not outcomes:
        raise ValueError("outcomes and probabilities must be non-empty and aligned")
    probabilities = [clip_probability(value) for value in probabilities]
    predictions = [int(value >= 0.5) for value in probabilities]
    tp = sum(y == 1 and p == 1 for y, p in zip(outcomes, predictions))
    tn = sum(y == 0 and p == 0 for y, p in zip(outcomes, predictions))
    fp = sum(y == 0 and p == 1 for y, p in zip(outcomes, predictions))
    fn = sum(y == 1 and p == 0 for y, p in zip(outcomes, predictions))
    positives = tp + fn
    negatives = tn + fp
    return {
        "count": len(outcomes),
        "log_loss": round(sum(
            -(y * math.log(p) + (1 - y) * math.log(1 - p))
            for y, p in zip(outcomes, probabilities)
        ) / len(outcomes), 10),
        "brier_score": round(sum(
            (p - y) ** 2 for y, p in zip(outcomes, probabilities)
        ) / len(outcomes), 10),
        "accuracy": round((tp + tn) / len(outcomes), 10),
        "balanced_accuracy": round((
            (tp / positives if positives else 0.0)
            + (tn / negatives if negatives else 0.0)
        ) / 2, 10) if positives and negatives else None,
        "roc_auc": _auc(outcomes, probabilities),
        "precision": round(tp / (tp + fp), 10) if tp + fp else None,
        "recall": round(tp / positives, 10) if positives else None,
        "calibration_error": _expected_calibration_error(
            outcomes, probabilities
        ),
        "calibration_table": calibration_table(outcomes, probabilities),
    }


def calibration_table(
    outcomes: list[int], probabilities: list[float], bins: int = 10
) -> list[dict]:
    output = []
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        members = [
            (y, p) for y, p in zip(outcomes, probabilities)
            if lower <= p < upper or (index == bins - 1 and p == 1.0)
        ]
        output.append({
            "bin": index,
            "lower": lower,
            "upper": upper,
            "count": len(members),
            "mean_probability": round(
                sum(p for _, p in members) / len(members), 10
            ) if members else None,
            "observed_frequency": round(
                sum(y for y, _ in members) / len(members), 10
            ) if members else None,
        })
    return output


def clip_probability(value: float) -> float:
    return min(1.0 - EPSILON, max(EPSILON, float(value)))


def _expected_calibration_error(
    outcomes: list[int], probabilities: list[float]
) -> float:
    table = calibration_table(outcomes, probabilities)
    total = len(outcomes)
    return round(sum(
        row["count"] / total
        * abs(row["mean_probability"] - row["observed_frequency"])
        for row in table if row["count"]
    ), 10)


def _auc(outcomes: list[int], probabilities: list[float]) -> float | None:
    positives = sum(outcomes)
    negatives = len(outcomes) - positives
    if not positives or not negatives:
        return None
    ordered = sorted(zip(probabilities, outcomes), key=lambda item: item[0])
    rank_sum = 0.0
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][0] == ordered[index][0]:
            end += 1
        average_rank = (index + 1 + end) / 2
        rank_sum += average_rank * sum(
            outcome for _, outcome in ordered[index:end]
        )
        index = end
    auc = (
        rank_sum - positives * (positives + 1) / 2
    ) / (positives * negatives)
    return round(auc, 10)
