from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class LogisticModel:
    coefficients: tuple[float, ...]
    iterations: int
    converged: bool

    def predict(self, matrix: list[list[float]]) -> list[float]:
        return [_sigmoid(_dot(self.coefficients, row)) for row in matrix]


def fit_logistic(
    matrix: list[list[float]],
    outcomes: list[int],
    l2_penalty: float = 1.0,
    max_iterations: int = 100,
    tolerance: float = 1e-9,
) -> LogisticModel:
    if not matrix or len(matrix) != len(outcomes):
        raise ValueError("training matrix and outcomes must be aligned")
    width = len(matrix[0])
    if not width or any(len(row) != width for row in matrix):
        raise ValueError("training matrix must be rectangular")
    coefficients = [0.0] * width
    converged = False
    for iteration in range(1, max_iterations + 1):
        probabilities = [_sigmoid(_dot(coefficients, row)) for row in matrix]
        gradient = [0.0] * width
        hessian = [[0.0] * width for _ in range(width)]
        for row, outcome, probability in zip(matrix, outcomes, probabilities):
            residual = outcome - probability
            weight = max(1e-9, probability * (1.0 - probability))
            for left in range(width):
                gradient[left] += row[left] * residual
                for right in range(left, width):
                    hessian[left][right] += (
                        row[left] * row[right] * weight
                    )
        for left in range(width):
            for right in range(left):
                hessian[left][right] = hessian[right][left]
            if left:
                gradient[left] -= l2_penalty * coefficients[left]
                hessian[left][left] += l2_penalty
            hessian[left][left] += 1e-9
        step = _solve(hessian, gradient)
        coefficients = [
            value + delta for value, delta in zip(coefficients, step)
        ]
        if max(abs(delta) for delta in step) < tolerance:
            converged = True
            break
    return LogisticModel(tuple(coefficients), iteration, converged)


def _sigmoid(value: float) -> float:
    if value >= 0:
        decay = math.exp(-min(value, 700.0))
        return 1.0 / (1.0 + decay)
    growth = math.exp(max(value, -700.0))
    return growth / (1.0 + growth)


def _dot(left, right) -> float:
    return sum(a * b for a, b in zip(left, right))


def _solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    size = len(vector)
    augmented = [
        [float(value) for value in matrix[row]] + [float(vector[row])]
        for row in range(size)
    ]
    for column in range(size):
        pivot = max(
            range(column, size),
            key=lambda row: abs(augmented[row][column]),
        )
        if abs(augmented[pivot][column]) < 1e-14:
            raise ValueError("logistic Hessian is singular")
        augmented[column], augmented[pivot] = (
            augmented[pivot], augmented[column]
        )
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor:
                augmented[row] = [
                    current - factor * pivot_value
                    for current, pivot_value
                    in zip(augmented[row], augmented[column])
                ]
    return [augmented[row][-1] for row in range(size)]
