from __future__ import annotations

import unittest

from polymarket.structural_mispricing import (
    TOTAL_COST,
    _build_episodes,
    _normalize_snapshot,
)


class StructuralMispricingTests(unittest.TestCase):
    def _payload(self, **changes):
        payload = {
            "asset": "BTC",
            "market_id": "m1",
            "quote_timestamp": "2026-01-01T00:00:00+00:00",
            "yes_bid": 0.48,
            "yes_ask": 0.50,
            "yes_bid_size": 100,
            "yes_ask_size": 80,
            "seconds_to_expiry": 120,
        }
        payload.update(changes)
        return payload

    def test_valid_book_has_negative_complete_set_margin(self):
        row = _normalize_snapshot(
            self._payload(), "2026-01-01T00:00:01+00:00", 1, "fixture"
        )
        self.assertTrue(row["valid"])
        self.assertFalse(row["crossed"])
        self.assertAlmostEqual(row["complete_set_acquisition_net_margin"], -0.02 - TOTAL_COST)
        self.assertAlmostEqual(row["complete_set_liquidation_net_margin"], -0.02 - TOTAL_COST)

    def test_crossed_book_is_detected_and_capacity_capped(self):
        row = _normalize_snapshot(
            self._payload(yes_bid=0.55, yes_ask=0.50, yes_bid_size=500, yes_ask_size=300),
            "2026-01-01T00:00:01+00:00", 1, "fixture",
        )
        self.assertTrue(row["crossed"])
        self.assertAlmostEqual(row["crossed_net_margin"], 0.04)
        self.assertEqual(row["executable_capacity_shares"], 125)

    def test_stale_cross_is_ineligible_for_episode(self):
        row = _normalize_snapshot(
            self._payload(yes_bid=0.55, yes_ask=0.50),
            "2026-01-01T00:00:10+00:00", 1, "fixture",
        )
        self.assertTrue(row["stale"])
        self.assertEqual(_build_episodes([row]), [])

    def test_wide_spread_episode_persistence(self):
        first = _normalize_snapshot(
            self._payload(yes_bid=0.40, yes_ask=0.50),
            "2026-01-01T00:00:01+00:00", 1, "fixture",
        )
        second_payload = self._payload(
            quote_timestamp="2026-01-01T00:00:03+00:00", yes_bid=0.41, yes_ask=0.50
        )
        second = _normalize_snapshot(second_payload, "2026-01-01T00:00:04+00:00", 1, "fixture")
        episodes = _build_episodes([first, second])
        wide = [row for row in episodes if row["kind"] == "wide_spread"]
        self.assertEqual(len(wide), 1)
        self.assertEqual((wide[0]["last_time"] - wide[0]["first_time"]).total_seconds(), 3)

    def test_invalid_prices_fail_validation(self):
        row = _normalize_snapshot(
            self._payload(yes_bid=-0.1), "2026-01-01T00:00:01+00:00", 1, "fixture"
        )
        self.assertFalse(row["valid"])


if __name__ == "__main__":
    unittest.main()
