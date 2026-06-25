from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from polymarket.repricing_research import (
    RepricingConfig,
    build_repricing_dataset,
    simulate_repricing_strategy,
)
from polymarket.repricing_research.cli import build_parser


class RepricingResearchTests(unittest.TestCase):
    def test_cli_accepts_balanced_collection_replay_options(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "--session", "session.jsonl",
            "--output", "out",
            "--timeout", "180",
            "--min-seconds-to-expiry", "60",
            "--signal-reason", "qualified_external_move_not_repriced",
            "--signal-reason", "confidence_below_threshold",
        ])

        self.assertEqual(args.min_seconds_to_expiry, 60)
        self.assertEqual(args.signal_reason, [
            "qualified_external_move_not_repriced",
            "confidence_below_threshold",
        ])

    def test_builds_repricing_label_and_simulates_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            session = Path(tmp) / "session.jsonl"
            self._write_session(session)

            rows = build_repricing_dataset(
                [session],
                RepricingConfig(
                    repricing_target=0.03,
                    stop_loss=0.03,
                    max_holding_seconds=180,
                    conservative_slippage=0.02,
                ),
            )
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row.side, "YES")
            self.assertTrue(row.repriced_favorably)
            self.assertEqual(row.simulated_exit_reason, "repricing_target")
            self.assertAlmostEqual(row.polymarket_price_move_after_30s, 0.04)
            self.assertAlmostEqual(row.simulated_pnl_after_slippage, 0.02)

            summary = simulate_repricing_strategy(rows)
            self.assertEqual(summary.signals, 1)
            self.assertEqual(summary.wins, 1)
            self.assertAlmostEqual(summary.win_rate, 1.0)

    def test_ignores_final_outcome_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            session = Path(tmp) / "session.jsonl"
            self._write_session(session, include_outcome_like_event=True)
            rows = build_repricing_dataset([session])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].source_session, str(session))

    def _write_session(
        self,
        path: Path,
        *,
        include_outcome_like_event: bool = False,
    ) -> None:
        events = [
            {
                "event": "reference_price",
                "timestamp": "2026-01-01T00:00:00+00:00",
                "payload": {"asset": "BTC", "price": 100.0, "source": "test"},
            },
            {
                "event": "reference_price",
                "timestamp": "2026-01-01T00:01:00+00:00",
                "payload": {"asset": "BTC", "price": 101.0, "source": "test"},
            },
            self._snapshot("2026-01-01T00:01:00+00:00", 0.50, 240),
            self._micro("2026-01-01T00:01:00+00:00"),
            {
                "event": "lag_measurement",
                "timestamp": "2026-01-01T00:01:00+00:00",
                "payload": {
                    "market_id": "m1",
                    "measurement": {
                        "confidence": 0.60,
                        "direction": "UP",
                        "external_price_change": 0.01,
                        "lag_score": 0.75,
                        "polymarket_yes_price_change": 0.0,
                        "qualified": False,
                        "reason": "confidence_below_threshold",
                    },
                },
            },
            self._snapshot("2026-01-01T00:01:30+00:00", 0.54, 210),
            self._snapshot("2026-01-01T00:02:00+00:00", 0.55, 180),
        ]
        if include_outcome_like_event:
            events.append({
                "event": "session_completed",
                "timestamp": "2026-01-01T00:05:00+00:00",
                "payload": {"outcome": 0},
            })
        with path.open("w", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event, sort_keys=True) + "\n")

    def _snapshot(self, timestamp: str, yes_price: float, seconds_to_expiry: float):
        return {
            "event": "polymarket_snapshot",
            "timestamp": timestamp,
            "payload": {
                "asset": "BTC",
                "market_id": "m1",
                "yes_price": yes_price,
                "no_price": 1.0 - yes_price,
                "seconds_to_expiry": seconds_to_expiry,
            },
        }

    def _micro(self, timestamp: str):
        return {
            "event": "microstructure_snapshot",
            "timestamp": timestamp,
            "payload": {
                "asset": "BTC",
                "market_id": "m1",
                "quote_age_seconds": 1.0,
                "repricing_velocity": 0.0,
                "repricing_acceleration": 0.0,
                "spread_compression": 0.0,
                "book_imbalance": 0.1,
                "cross_asset_yes_dispersion": 0.02,
            },
        }


if __name__ == "__main__":
    unittest.main()
