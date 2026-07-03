from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from polymarket.repricing_research.slower_horizon_validation import (
    TRANSACTION_COST,
    _evaluate,
    _executable_price,
    _holm_adjust,
)


class SlowerHorizonValidationTests(unittest.TestCase):
    def _history(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        return [
            (
                start + timedelta(seconds=seconds),
                {"yes_bid": 0.49 + seconds / 1000, "yes_ask": 0.51 + seconds / 1000},
            )
            for seconds in range(0, 201, 2)
        ]

    def _row(self):
        return {
            "entry_timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat(),
            "session_number": 1,
            "market_id": "market",
            "asset": "BTC",
            "side": "YES",
            "source_session": "fixture",
            "time_to_expiry_seconds": "300",
        }

    def test_continuation_uses_delayed_ask_and_fixed_horizon_bid(self):
        row = _evaluate(self._row(), self._history(), 30, "continuation")
        self.assertIsNotNone(row)
        self.assertAlmostEqual(row["entry_price"], 0.512)
        self.assertAlmostEqual(row["exit_price"], 0.52)
        self.assertAlmostEqual(row["pnl"], 0.008 - TRANSACTION_COST)

    def test_mean_reversion_trades_opposite_side(self):
        row = _evaluate(self._row(), self._history(), 30, "mean_reversion")
        self.assertIsNotNone(row)
        self.assertEqual(row["traded_side"], "NO")
        self.assertLess(row["pnl"], 0)

    def test_missing_terminal_snapshot_fails_closed(self):
        self.assertIsNone(_evaluate(self._row(), self._history()[:10], 180, "continuation"))

    def test_horizon_past_expiry_fails_closed(self):
        row = self._row()
        row["time_to_expiry_seconds"] = "119"
        self.assertIsNone(_evaluate(row, self._history(), 120, "continuation"))

    def test_executable_no_prices_are_complements(self):
        payload = {"yes_bid": 0.4, "yes_ask": 0.45}
        self.assertEqual(_executable_price(payload, "NO", entering=True), 0.6)
        self.assertEqual(_executable_price(payload, "NO", entering=False), 0.55)

    def test_holm_adjustment_never_creates_false_pass(self):
        rows = [
            {
                "matched_random_timing_p_value": 0.01,
                "signal_count": 10,
                "expectancy": 0.01,
                "bonferroni_8way_95_low": -0.001,
                "positive_sessions": 3,
                "session_count": 3,
                "largest_session_positive_pnl_share": 0.3,
                "largest_asset_positive_pnl_share": 0.3,
            },
            {
                "matched_random_timing_p_value": 0.2,
                "signal_count": 10,
                "expectancy": -0.01,
                "bonferroni_8way_95_low": -0.02,
                "positive_sessions": 0,
                "session_count": 3,
                "largest_session_positive_pnl_share": None,
                "largest_asset_positive_pnl_share": None,
            },
        ]
        _holm_adjust(rows)
        self.assertFalse(rows[0]["passes_all_gates"])
        self.assertFalse(rows[1]["passes_all_gates"])


if __name__ == "__main__":
    unittest.main()
