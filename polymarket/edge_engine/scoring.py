from __future__ import annotations

from .models import MarketSnapshot, ScoreBreakdown


class EdgeScorer:
    PRICE_LAG_WEIGHT = 0.4
    VOLUME_SPIKE_WEIGHT = 0.3
    MOMENTUM_WEIGHT = 0.2
    STABILITY_WEIGHT = 0.1

    def score(self, snapshot: MarketSnapshot) -> ScoreBreakdown:
        price_lag = min(1.0, abs(snapshot.reference_probability - snapshot.yes_price) * 2.0)
        score = (
            self.PRICE_LAG_WEIGHT * price_lag
            + self.VOLUME_SPIKE_WEIGHT * snapshot.volume_spike
            + self.MOMENTUM_WEIGHT * snapshot.momentum
            + self.STABILITY_WEIGHT * snapshot.stability
        )
        return ScoreBreakdown(
            price_lag=price_lag,
            volume_spike=snapshot.volume_spike,
            momentum=snapshot.momentum,
            stability=snapshot.stability,
            score=round(score, 6),
        )
