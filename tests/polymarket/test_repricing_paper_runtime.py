from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from polymarket.repricing_research import (
    ManagedRepricingPaperRuntime,
    PaperRuntimeConfig,
    RestartSafePaperCore,
    V5StreamValidationError,
)
from polymarket.repricing_research.paper_runtime import build_parser


FIXED_NOW = datetime(2026, 6, 28, 16, 0, 0, tzinfo=timezone.utc)


class ManagedRepricingPaperRuntimeTests(unittest.TestCase):
    def test_runtime_starts_and_stops_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session, self._events())
            runtime = self._runtime(root, session)

            health = runtime.run()

            self.assertEqual(health.status, "STOPPED")
            self.assertEqual(health.polls_completed, 1)
            self.assertEqual(health.runtime_start_timestamp, FIXED_NOW.isoformat())
            self.assertEqual(health.runtime_stop_timestamp, FIXED_NOW.isoformat())
            self.assertIsNone(health.last_error)

    def test_events_flow_into_positions_trades_and_health(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session, self._events())
            runtime = self._runtime(root, session)

            health = runtime.run()
            saved = json.loads((root / "health.json").read_text(encoding="utf-8"))

            self.assertEqual(health.events_received, 3)
            self.assertEqual(health.events_accepted, 3)
            self.assertEqual(health.events_rejected, 0)
            self.assertEqual(health.positions_opened, 1)
            self.assertEqual(health.positions_closed, 1)
            self.assertEqual(health.current_open_positions, 0)
            self.assertEqual(saved, health.__dict__)
            with RestartSafePaperCore(root / "paper.sqlite3") as core:
                self.assertEqual(len(core.trades()), 1)

    def test_duplicate_source_replay_is_idempotent_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session, self._events())
            self._runtime(root, session).run()

            second = self._runtime(root, session).run()

            self.assertEqual(second.events_accepted, 0)
            self.assertEqual(second.duplicate_events_skipped, 3)
            self.assertEqual(second.positions_opened, 0)
            self.assertEqual(second.positions_closed, 0)
            with RestartSafePaperCore(root / "paper.sqlite3") as core:
                self.assertEqual(len(core.positions()), 1)
                self.assertEqual(len(core.trades()), 1)

    def test_open_position_survives_runtime_restart_and_then_closes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            events = self._events()
            self._write(session, events[:2])
            first = self._runtime(root, session).run()
            self.assertEqual(first.current_open_positions, 1)

            self._append(session, events[2:])
            second = self._runtime(root, session).run()

            self.assertEqual(second.recovered_open_positions, 1)
            self.assertEqual(second.positions_closed, 1)
            self.assertEqual(second.current_open_positions, 0)
            with RestartSafePaperCore(root / "paper.sqlite3") as core:
                self.assertEqual(core.trades()[0]["exit_reason"], "repricing_target")

    def test_invalid_stream_fails_closed_and_records_health_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            session.write_text('{"event":"lag_measurement"}\n', encoding="utf-8")
            runtime = self._runtime(root, session)

            with self.assertRaises(V5StreamValidationError):
                runtime.run()

            saved = json.loads((root / "health.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "FAILED")
            self.assertEqual(saved["events_rejected"], 1)
            self.assertIn("V5StreamValidationError", saved["last_error"])
            with RestartSafePaperCore(root / "paper.sqlite3") as core:
                self.assertEqual(core.validation_snapshot()["pending_events"], 0)

    def test_pre_requested_stop_is_graceful_and_recoverable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session, self._events())
            runtime = self._runtime(root, session)
            runtime.request_stop()

            health = runtime.run()

            self.assertEqual(health.status, "STOPPED")
            self.assertEqual(health.polls_completed, 0)
            self.assertTrue((root / "paper.sqlite3").exists())

    def test_bounded_dry_run_health_output_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session, self._events())
            self._runtime(root, session).run()
            first = (root / "health.json").read_bytes()

            (root / "paper.sqlite3").unlink()
            (root / "health.json").unlink()
            self._runtime(root, session).run()
            second = (root / "health.json").read_bytes()

            self.assertEqual(first, second)

    def test_cli_accepts_bounded_dry_run_contract(self) -> None:
        args = build_parser().parse_args([
            "--session", "session.jsonl",
            "--database", "paper.sqlite3",
            "--health", "health.json",
            "--dry-run",
            "--max-polls", "1",
        ])
        config = PaperRuntimeConfig(
            session_path=args.session,
            database_path=args.database,
            health_path=args.health,
            max_polls=args.max_polls,
            dry_run=args.dry_run,
        )
        self.assertTrue(config.dry_run)
        self.assertEqual(config.max_polls, 1)

    @staticmethod
    def _runtime(root: Path, session: Path) -> ManagedRepricingPaperRuntime:
        return ManagedRepricingPaperRuntime(
            PaperRuntimeConfig(
                session_path=session,
                database_path=root / "paper.sqlite3",
                health_path=root / "health.json",
                poll_interval_seconds=0.0,
                max_polls=1,
                dry_run=True,
            ),
            now=lambda: FIXED_NOW,
            monotonic=lambda: 0.0,
        )

    @classmethod
    def _events(cls) -> list[dict[str, object]]:
        return [
            cls._snapshot("2026-06-28T15:00:00+00:00", 0.50, 240),
            {
                "event": "lag_measurement",
                "timestamp": "2026-06-28T15:00:00+00:00",
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
            cls._snapshot("2026-06-28T15:00:30+00:00", 0.54, 210),
        ]

    @staticmethod
    def _snapshot(timestamp: str, yes_price: float, expiry: float) -> dict[str, object]:
        return {
            "event": "polymarket_snapshot",
            "timestamp": timestamp,
            "payload": {
                "asset": "BTC",
                "market_id": "m1",
                "yes_price": yes_price,
                "no_price": 1.0 - yes_price,
                "seconds_to_expiry": expiry,
            },
        }

    @staticmethod
    def _write(path: Path, events: list[dict[str, object]]) -> None:
        path.write_text(
            "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
            encoding="utf-8",
        )

    @staticmethod
    def _append(path: Path, events: list[dict[str, object]]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event, sort_keys=True) + "\n")


if __name__ == "__main__":
    unittest.main()
