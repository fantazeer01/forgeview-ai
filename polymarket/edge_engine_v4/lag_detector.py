from __future__ import annotations

from datetime import datetime

from .config import ScannerConfig
from .opportunity import Direction, LagMeasurement, PolymarketSnapshot, ReferencePrice


class LagDetector:
    def __init__(self, config: ScannerConfig) -> None:
        self.config = config

    def measure(
        self,
        current_reference: ReferencePrice,
        baseline_reference: ReferencePrice,
        current_market: PolymarketSnapshot,
        baseline_market: PolymarketSnapshot,
    ) -> LagMeasurement:
        external_change = (
            current_reference.price / baseline_reference.price - 1.0
            if baseline_reference.price else 0.0
        )
        polymarket_change = current_market.yes_price - baseline_market.yes_price
        external_bps = external_change * 10_000.0
        expected_probability_move = min(0.30, abs(external_bps) / 1000.0)
        direction = (
            Direction.UP if external_bps >= self.config.external_move_threshold_bps
            else Direction.DOWN if external_bps <= -self.config.external_move_threshold_bps
            else Direction.NONE
        )
        aligned_market_move = polymarket_change if direction is Direction.UP else -polymarket_change
        repricing_ratio = (
            max(0.0, aligned_market_move) / expected_probability_move
            if expected_probability_move > 0 else 1.0
        )
        residual = max(0.0, 1.0 - repricing_ratio)
        move_strength = min(1.0, abs(external_bps) / max(self.config.external_move_threshold_bps * 4, 1.0))
        lag_score = residual * move_strength
        spread = current_market.yes_ask - current_market.yes_bid
        confidence = max(0.0, min(1.0, 0.70 * lag_score + 0.20 * move_strength + 0.10 * (1.0 - min(1.0, spread / 0.10))))
        lag_seconds = max(0.0, (current_reference.timestamp - baseline_reference.timestamp).total_seconds())

        reason = "qualified_external_move_not_repriced"
        qualified = True
        if current_market.liquidity < self.config.min_liquidity:
            qualified, reason = False, "liquidity_below_minimum"
        elif current_market.seconds_to_expiry < self.config.min_seconds_to_expiry:
            qualified, reason = False, "near_expiry_insufficient_time"
        elif direction is Direction.NONE:
            qualified, reason = False, "external_move_below_threshold"
        elif repricing_ratio >= self.config.repricing_ratio:
            qualified, reason = False, "polymarket_already_repriced"
        elif confidence < self.config.min_confidence:
            qualified, reason = False, "confidence_below_threshold"

        return LagMeasurement(
            external_price_change=round(external_change, 8),
            polymarket_yes_price_change=round(polymarket_change, 8),
            lag_seconds=round(lag_seconds, 3),
            lag_score=round(lag_score, 6),
            direction=direction,
            confidence=round(confidence, 6),
            qualified=qualified,
            reason=reason,
        )
