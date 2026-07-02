import json
import tempfile
import unittest
from pathlib import Path

from polymarket.repricing_research.stress_analysis import (
    _max_drawdown,
    _quote_replay_row,
    _stress_row,
)


class RepricingStressAnalysisTests(unittest.TestCase):
    def test_stress_is_deterministic_and_costs_are_adverse(self) -> None:
        row = {
            "source_session": "session",
            "market_id": "market",
            "entry_timestamp": "2026-07-01T00:00:00+00:00",
            "asset": "BTC",
            "side": "YES",
            "external_price_move": "0.001",
            "repricing_velocity": "0.002",
            "repricing_acceleration": "0",
            "quote_age_seconds": "2",
            "bid_ask_spread": "0.01",
            "yes_ask_size": "100",
            "yes_bid_size": "100",
            "simulated_pnl_after_slippage": "0.10",
            "session_number": 1,
        }
        scenario = {"name": "stress", "delay_seconds": 2, "spread_multiplier": 1, "quote_age_multiplier": 1, "transaction_cost": 0.01, "miss_rate": 0, "order_size_shares": 100, "max_fill_fraction": 1}
        first = _stress_row(row, scenario)
        second = _stress_row(row, scenario)
        self.assertEqual(first, second)
        self.assertLess(first["stressed_pnl"], first["base_pnl"])

    def test_drawdown_is_chronological(self) -> None:
        self.assertAlmostEqual(_max_drawdown([0.1, -0.2, 0.05, -0.1]), 0.25)

    def test_quote_replay_uses_executable_ask_then_bid(self) -> None:
        row = {
            "entry_timestamp": "2026-07-01T00:00:00+00:00",
            "market_id": "market",
            "asset": "BTC",
            "side": "YES",
            "external_price_move": "0.001",
            "bid_ask_spread": "0.02",
            "quote_age_seconds": "1",
            "simulated_pnl_after_slippage": "0.01",
            "session_number": 1,
            "_execution_snapshots": [
                ("2026-07-01T00:00:00+00:00", {"yes_ask": 0.50, "yes_bid": 0.48, "yes_ask_size": 10, "yes_bid_size": 10}),
                ("2026-07-01T00:00:02+00:00", {"yes_ask": 0.55, "yes_bid": 0.54, "yes_ask_size": 10, "yes_bid_size": 10}),
            ],
        }
        scenario = {"name": "quote", "delay_seconds": 0, "order_size_shares": 1, "transaction_cost": 0}

        result = _quote_replay_row(row, scenario)

        self.assertAlmostEqual(result["stressed_pnl"], 0.04)
        self.assertEqual(result["fill_ratio"], 1.0)


if __name__ == "__main__":
    unittest.main()
