from __future__ import annotations

import csv
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
from polymarket.repricing_research.random_baseline import (
    RandomBaselineConfig,
    run_random_baseline,
    write_random_baseline_outputs,
)


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

    def test_random_baseline_is_deterministic_and_distribution_matched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            detector = root / "detector.csv"
            self._write_random_baseline_session(session)
            self._write_detector_rows(detector)
            config = RandomBaselineConfig(trials=20, seed=7)

            first_rows, first_summary = run_random_baseline(
                [detector], [session], config
            )
            second_rows, second_summary = run_random_baseline(
                [detector], [session], config
            )

            self.assertEqual(first_rows, second_rows)
            self.assertEqual(first_summary, second_summary)
            self.assertEqual(first_summary["sample_size"], 2)
            self.assertEqual(
                first_summary["matched_batch_asset_side_counts"],
                {"batch_001:BTC:NO": 1, "batch_001:BTC:YES": 1},
            )
            outputs = write_random_baseline_outputs(
                root / "output", first_rows, first_summary
            )
            self.assertEqual(set(outputs), {"results", "summary", "report"})
            self.assertTrue(all(Path(path).exists() for path in outputs.values()))

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

    def _write_random_baseline_session(self, path: Path) -> None:
        events = [{
            "event": "session_started",
            "timestamp": "2026-01-01T00:00:00+00:00",
            "payload": {},
        }]
        for market, minute in (("m1", 0), ("m2", 5), ("m3", 10)):
            for offset, yes_price in ((0, 0.45), (30, 0.50), (60, 0.55), (90, 0.48)):
                timestamp = (
                    f"2026-01-01T00:{minute + offset // 60:02d}:"
                    f"{offset % 60:02d}+00:00"
                )
                events.append({
                    "event": "polymarket_snapshot",
                    "timestamp": timestamp,
                    "payload": {
                        "asset": "BTC",
                        "market_id": market,
                        "yes_price": yes_price,
                        "no_price": 1.0 - yes_price,
                        "seconds_to_expiry": 240 - offset,
                    },
                })
        events.append({
            "event": "session_completed",
            "timestamp": "2026-01-01T00:15:00+00:00",
            "payload": {},
        })
        with path.open("w", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event, sort_keys=True) + "\n")

    def _write_detector_rows(self, path: Path) -> None:
        fields = [
            "entry_timestamp", "asset", "side", "time_to_expiry_seconds",
            "repriced_favorably", "simulated_pnl_before_slippage",
            "simulated_pnl_after_slippage",
        ]
        rows = [
            ["2026-01-01T00:00:00+00:00", "BTC", "YES", 240, True, 0.05, 0.03],
            ["2026-01-01T00:05:00+00:00", "BTC", "NO", 240, False, -0.03, -0.05],
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(fields)
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
