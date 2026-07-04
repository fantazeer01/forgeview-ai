from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from polymarket.passive_liquidity import _evaluate_attempt


class PassiveLiquidityTests(unittest.TestCase):
    def _row(self, seconds: int, bid: float, ask: float) -> dict:
        timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds)
        return {
            "session_number": 1,
            "market_id": "m1",
            "asset": "BTC",
            "timestamp": timestamp.isoformat(),
            "seconds_to_expiry": 120 - seconds,
            "quote_age_seconds": 1.0,
            "yes_bid": bid,
            "yes_ask": ask,
            "yes_bid_size": 100.0,
            "yes_ask_size": 100.0,
            "spread": ask - bid,
            "valid": True,
            "stale": False,
        }

    def test_no_depletion_means_no_fill_and_no_pnl(self):
        history = [self._row(i, 0.45, 0.55) for i in range(0, 10)]
        result = _evaluate_attempt(history[0], history, 5)
        self.assertIsNotNone(result)
        self.assertEqual(result["filled_shares"], 0)
        self.assertEqual(result["pnl"], 0)

    def test_one_sided_bid_fill_realizes_adverse_selection(self):
        history = [self._row(0, 0.45, 0.55)]
        history.extend(self._row(i, 0.40, 0.50) for i in range(1, 10))
        result = _evaluate_attempt(history[0], history, 5)
        self.assertTrue(result["bid_fill_proxy"])
        self.assertFalse(result["ask_fill_proxy"])
        self.assertLess(result["pnl"], 0)

    def test_two_sided_depletion_can_capture_spread(self):
        history = [self._row(0, 0.45, 0.55)]
        history.append(self._row(1, 0.40, 0.50))
        history.append(self._row(2, 0.60, 0.65))
        history.extend(self._row(i, 0.50, 0.60) for i in range(3, 10))
        result = _evaluate_attempt(history[0], history, 5)
        self.assertTrue(result["two_sided_fill_proxy"])
        self.assertGreater(result["spread_capture_pnl"], 0)

    def test_missing_timeout_quote_fails_closed(self):
        history = [self._row(0, 0.45, 0.55), self._row(1, 0.44, 0.54)]
        self.assertIsNone(_evaluate_attempt(history[0], history, 30))


if __name__ == "__main__":
    unittest.main()
