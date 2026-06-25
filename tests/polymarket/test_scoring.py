import unittest
from datetime import datetime, timezone

from polymarket.edge_engine.models import MarketSnapshot
from polymarket.edge_engine.scoring import EdgeScorer


class EdgeScorerTests(unittest.TestCase):
    def test_exact_weighted_formula(self) -> None:
        snapshot = MarketSnapshot(
            timestamp=datetime.now(timezone.utc),
            market_id="test",
            question="Test?",
            yes_price=0.25,
            reference_probability=0.65,
            volume_spike=0.6,
            momentum=0.5,
            stability=0.9,
        )
        result = EdgeScorer().score(snapshot)
        self.assertAlmostEqual(result.price_lag, 0.8)
        self.assertAlmostEqual(result.score, 0.4 * 0.8 + 0.3 * 0.6 + 0.2 * 0.5 + 0.1 * 0.9)

    def test_inputs_are_validated(self) -> None:
        with self.assertRaises(ValueError):
            MarketSnapshot(
                timestamp=datetime.now(timezone.utc),
                market_id="bad",
                question="Bad?",
                yes_price=1.2,
                reference_probability=0.5,
                volume_spike=0.5,
                momentum=0.5,
                stability=0.5,
            )


if __name__ == "__main__":
    unittest.main()
