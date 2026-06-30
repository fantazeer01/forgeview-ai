from __future__ import annotations

import json
import math
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

from polymarket.repricing_research import (
    ManagedRepricingPaperRuntime,
    PaperRuntimeConfig,
    RestartSafePaperCore,
    RuntimeBackpressureError,
    RuntimeLivenessError,
    RuntimeSessionHealthError,
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

    def test_simulated_telemetry_stall_trips_watchdog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session, self._events())

            class StalledAdapter:
                def __init__(self, path, _core):
                    self.session_path = Path(path).resolve()
                    self.last_sync_lag_measurements = 0
                    self.last_event_timestamp = None

                def sync(self, *, max_events, progress_callback):
                    time.sleep(0.08)
                    progress_callback()

            runtime = ManagedRepricingPaperRuntime(
                PaperRuntimeConfig(
                    session_path=session,
                    database_path=root / "paper.sqlite3",
                    health_path=root / "health.json",
                    max_polls=1,
                    dry_run=True,
                    max_processing_stall_seconds=0.03,
                    heartbeat_interval_seconds=0.01,
                ),
                adapter_factory=StalledAdapter,
            )

            with self.assertRaises(RuntimeLivenessError):
                runtime.run()

            health = json.loads((root / "health.json").read_text(encoding="utf-8"))
            marker = json.loads(
                (root / "repricing_runtime_safe_shutdown.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(health["status"], "FAILED")
            self.assertTrue(health["watchdog_triggered"])
            self.assertEqual(health["fatal_error_code"], "TELEMETRY_STALLED")
            self.assertEqual(marker["status"], "FAILED_CLOSED")

    def test_host_suspend_watchdog_gap_has_distinct_fatal_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session, self._events())

            class SuspendedAdapter:
                def __init__(self, path, _core):
                    self.session_path = Path(path).resolve()
                    self.last_sync_lag_measurements = 0
                    self.last_event_timestamp = None

                def sync(self, *, max_events, progress_callback):
                    time.sleep(0.05)
                    progress_callback()

            def suspended_clock() -> float:
                if threading.current_thread().name == "repricing-runtime-watchdog":
                    return 100.0
                return 0.0

            runtime = ManagedRepricingPaperRuntime(
                PaperRuntimeConfig(
                    session_path=session,
                    database_path=root / "paper.sqlite3",
                    health_path=root / "health.json",
                    max_polls=1,
                    dry_run=True,
                    max_processing_stall_seconds=0.03,
                    heartbeat_interval_seconds=0.01,
                ),
                monotonic=suspended_clock,
                adapter_factory=SuspendedAdapter,
            )

            with self.assertRaises(RuntimeLivenessError):
                runtime.run()

            marker = json.loads(
                (root / "repricing_runtime_safe_shutdown.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(marker["fatal_error_code"], "HOST_SUSPEND_DETECTED")
            self.assertIn("host suspend", marker["error"])

    def test_backpressure_overload_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session, self._diagnostic_events(20))
            runtime = ManagedRepricingPaperRuntime(
                PaperRuntimeConfig(
                    session_path=session,
                    database_path=root / "paper.sqlite3",
                    health_path=root / "health.json",
                    max_polls=20,
                    dry_run=True,
                    max_events_per_batch=1,
                    max_backlog_bytes=1,
                ),
                now=lambda: FIXED_NOW,
                monotonic=lambda: 0.0,
                write_clock=lambda: 0.0,
            )

            with self.assertRaises(RuntimeBackpressureError):
                runtime.run()

            marker = json.loads(
                (root / "repricing_runtime_safe_shutdown.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(marker["fatal_error_code"], "BACKPRESSURE_OVERLOAD")
            with RestartSafePaperCore(root / "paper.sqlite3") as core:
                self.assertEqual(core.validation_snapshot()["pending_events"], 0)

    def test_fail_closed_shutdown_marker_is_durable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session, self._incomplete_session_events())
            runtime = ManagedRepricingPaperRuntime(
                PaperRuntimeConfig(
                    session_path=session,
                    database_path=root / "paper.sqlite3",
                    health_path=root / "health.json",
                    max_polls=1,
                    dry_run=True,
                ),
                now=lambda: FIXED_NOW,
                monotonic=lambda: 0.0,
                write_clock=lambda: 0.0,
            )

            with self.assertRaises(RuntimeSessionHealthError):
                runtime.run()

            first = (root / "repricing_runtime_safe_shutdown.json").read_bytes()
            marker = json.loads(first)
            self.assertEqual(marker["fatal_error_code"], "SESSION_HEALTH_INCOMPLETE")
            self.assertIn("observation_continuity:incomplete", marker["error"])
            self.assertEqual(
                first,
                (root / "repricing_runtime_safe_shutdown.json").read_bytes(),
            )

    def test_healthy_long_run_processes_bounded_batches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            events = self._diagnostic_events(5000)
            self._write(session, events)
            batch_size = 128
            runtime = ManagedRepricingPaperRuntime(
                PaperRuntimeConfig(
                    session_path=session,
                    database_path=root / "paper.sqlite3",
                    health_path=root / "health.json",
                    max_polls=math.ceil(len(events) / batch_size),
                    dry_run=True,
                    max_events_per_batch=batch_size,
                ),
                now=lambda: FIXED_NOW,
                monotonic=lambda: 0.0,
                write_clock=lambda: 0.0,
            )

            health = runtime.run()

            self.assertEqual(health.status, "STOPPED")
            self.assertEqual(health.events_received, 5000)
            self.assertEqual(health.polls_completed, 40)
            self.assertLessEqual(health.batch_events_processed, batch_size)
            self.assertFalse((root / "repricing_runtime_safe_shutdown.json").exists())
            with RestartSafePaperCore(root / "paper.sqlite3") as core:
                self.assertEqual(core.validation_snapshot()["counts"]["raw_events"], 5000)

    def test_incomplete_session_health_never_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session, self._incomplete_session_events())
            runtime = ManagedRepricingPaperRuntime(
                PaperRuntimeConfig(
                    session_path=session,
                    database_path=root / "paper.sqlite3",
                    health_path=root / "health.json",
                    max_polls=1,
                    dry_run=True,
                ),
                now=lambda: FIXED_NOW,
                monotonic=lambda: 0.0,
                write_clock=lambda: 0.0,
            )

            with self.assertRaises(RuntimeSessionHealthError):
                runtime.run()

            health = json.loads((root / "health.json").read_text(encoding="utf-8"))
            self.assertEqual(health["status"], "FAILED")
            self.assertEqual(health["fatal_error_code"], "SESSION_HEALTH_INCOMPLETE")

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
            write_clock=lambda: 0.0,
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
    def _diagnostic_events(count: int) -> list[dict[str, object]]:
        return [
            {
                "event": "skipped",
                "timestamp": "2026-06-28T15:00:00+00:00",
                "payload": {"index": index, "reason": "fixture"},
            }
            for index in range(count)
        ]

    @staticmethod
    def _incomplete_session_events() -> list[dict[str, object]]:
        return [
            {
                "event": "session_started",
                "timestamp": "2026-06-28T15:00:00+00:00",
                "payload": {"mode": "public"},
            },
            {
                "event": "session_completed",
                "timestamp": "2026-06-28T15:01:00+00:00",
                "payload": {
                    "campaign_completeness": {"status": "incomplete_campaign"},
                    "observation_continuity": {"status": "incomplete"},
                },
            },
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
