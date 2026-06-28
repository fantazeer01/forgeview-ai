from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from polymarket.repricing_research import (
    FrozenPaperConfig,
    InjectedFailure,
    RepricingConfig,
    RestartSafePaperCore,
    StrategyFingerprintMismatch,
    build_repricing_dataset,
)


class RestartSafeRepricingPaperCoreTests(unittest.TestCase):
    def test_open_position_survives_restart_and_duplicate_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / "paper.sqlite3"
            events = self._winning_events()
            core = RestartSafePaperCore(database)
            core.ingest_event("fixture", 0, events[0])
            core.ingest_event("fixture", 1, events[1])
            self.assertEqual(len(core.open_positions()), 1)
            core.close()

            recovered = RestartSafePaperCore(database)
            self.assertEqual(len(recovered.open_positions()), 1)
            recovered.ingest_event("fixture", 1, events[1])
            recovered.ingest_event("fixture", 2, events[1])
            self.assertEqual(len(recovered.signals()), 1)
            self.assertEqual(len(recovered.positions()), 1)
            self.assertEqual(recovered.validation_snapshot()["pending_events"], 0)
            recovered.close()

    def test_closed_position_is_not_reopened_or_recredited(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / "paper.sqlite3"
            events = self._winning_events()
            with RestartSafePaperCore(database) as core:
                for index, event in enumerate(events):
                    core.ingest_event("fixture", index, event)
                expected = core.validation_snapshot()

            with RestartSafePaperCore(database) as recovered:
                for index, event in enumerate(events):
                    recovered.ingest_event("fixture", index, event)
                actual = recovered.validation_snapshot()
                self.assertEqual(actual, expected)
                self.assertEqual(actual["open_positions"], 0)
                self.assertEqual(actual["counts"]["trades"], 1)
                self.assertAlmostEqual(actual["realized_pnl"], 0.02)

    def test_recovery_is_deterministic_at_open_failure_boundaries(self) -> None:
        stages = (
            "after_raw_persist",
            "before_signal_admission",
            "after_signal_admission",
            "after_position_open",
            "before_cursor_commit",
            "after_cursor_commit",
        )
        for stage in stages:
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as tmp:
                database = Path(tmp) / "paper.sqlite3"
                snapshot, signal, _ = self._winning_events()
                core = RestartSafePaperCore(database)
                core.ingest_event("fixture", 0, snapshot)
                with self.assertRaises(InjectedFailure):
                    core.ingest_event("fixture", 1, signal, fail_at=stage)
                core.close()

                with RestartSafePaperCore(database) as recovered:
                    state = recovered.validation_snapshot()
                    self.assertEqual(state["counts"]["signals"], 1)
                    self.assertEqual(state["counts"]["positions"], 1)
                    self.assertEqual(state["open_positions"], 1)
                    self.assertEqual(state["pending_events"], 0)

    def test_recovery_is_deterministic_at_close_failure_boundaries(self) -> None:
        for stage in ("after_trade_close", "before_cursor_commit", "after_cursor_commit"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as tmp:
                database = Path(tmp) / "paper.sqlite3"
                snapshot, signal, close = self._winning_events()
                core = RestartSafePaperCore(database)
                core.ingest_event("fixture", 0, snapshot)
                core.ingest_event("fixture", 1, signal)
                with self.assertRaises(InjectedFailure):
                    core.ingest_event("fixture", 2, close, fail_at=stage)
                core.close()

                with RestartSafePaperCore(database) as recovered:
                    state = recovered.validation_snapshot()
                    self.assertEqual(state["counts"]["trades"], 1)
                    self.assertEqual(state["open_positions"], 0)
                    self.assertAlmostEqual(state["realized_pnl"], 0.02)

    def test_fingerprint_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / "paper.sqlite3"
            RestartSafePaperCore(database).close()
            changed = replace(FrozenPaperConfig(), minimum_confidence=0.46)
            with self.assertRaises(StrategyFingerprintMismatch):
                RestartSafePaperCore(database, changed)

    def test_lifecycle_close_uses_last_durable_quote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / "paper.sqlite3"
            snapshot, signal, _ = self._winning_events()
            lifecycle = {
                "event": "market_lifecycle",
                "timestamp": "2026-01-01T00:05:00+00:00",
                "payload": {"market_id": "m1", "current": "closed"},
            }
            with RestartSafePaperCore(database) as core:
                for index, event in enumerate((snapshot, signal, lifecycle)):
                    core.ingest_event("fixture", index, event)
                self.assertEqual(len(core.open_positions()), 0)
                self.assertEqual(core.trades()[0]["exit_reason"], "expiry")
                self.assertAlmostEqual(core.trades()[0]["exit_price"], 0.50)

    def test_causal_replay_matches_offline_frozen_simulator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            database = root / "paper.sqlite3"
            events = self._winning_events()
            session.write_text(
                "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
                encoding="utf-8",
            )
            offline = build_repricing_dataset(
                [session], RepricingConfig(min_seconds_to_expiry=60.0)
            )
            with RestartSafePaperCore(database) as core:
                for index, event in enumerate(events):
                    core.ingest_event("fixture", index, event)
                signals = core.signals()
                trades = core.trades()

            self.assertEqual(len(offline), len(signals), 1)
            self.assertEqual(trades[0]["side"], offline[0].side)
            self.assertEqual(trades[0]["entry_timestamp"], offline[0].entry_timestamp)
            self.assertEqual(trades[0]["exit_timestamp"], offline[0].simulated_exit_timestamp)
            self.assertEqual(trades[0]["exit_reason"], offline[0].simulated_exit_reason)
            self.assertAlmostEqual(
                trades[0]["pnl_after_slippage"],
                offline[0].simulated_pnl_after_slippage,
            )

    @staticmethod
    def _winning_events() -> list[dict[str, object]]:
        return [
            {
                "event": "polymarket_snapshot",
                "timestamp": "2026-01-01T00:01:00+00:00",
                "payload": {
                    "asset": "BTC",
                    "market_id": "m1",
                    "yes_price": 0.50,
                    "no_price": 0.50,
                    "seconds_to_expiry": 240,
                },
            },
            {
                "event": "lag_measurement",
                "timestamp": "2026-01-01T00:01:00+00:00",
                "payload": {
                    "market_id": "m1",
                    "measurement": {
                        "confidence": 0.45,
                        "direction": "UP",
                        "external_price_change": 0.001,
                        "lag_score": 0.65,
                        "polymarket_yes_price_change": 0.0,
                        "qualified": False,
                        "reason": "confidence_below_threshold",
                    },
                },
            },
            {
                "event": "polymarket_snapshot",
                "timestamp": "2026-01-01T00:01:30+00:00",
                "payload": {
                    "asset": "BTC",
                    "market_id": "m1",
                    "yes_price": 0.54,
                    "no_price": 0.46,
                    "seconds_to_expiry": 210,
                },
            },
        ]


if __name__ == "__main__":
    unittest.main()
