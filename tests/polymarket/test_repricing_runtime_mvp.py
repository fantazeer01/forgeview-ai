from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from polymarket.repricing_research import (
    ContinuousRepricingPaperMVP,
    RepricingRuntimeMVPConfig,
    RuntimeAlreadyRunningError,
    RuntimeInstanceLock,
    V5StreamUnavailableError,
    validate_runtime_preflight,
)
from polymarket.repricing_research.paper_runtime import PaperRuntimeHealth
from polymarket.repricing_research.runtime_mvp import RuntimeOutputManager, build_parser


FIXED_NOW = datetime(2026, 6, 28, 18, 0, 0, tzinfo=UTC)


class ContinuousRepricingPaperMVPTests(unittest.TestCase):
    def test_single_json_configuration_loads_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "runtime.json"
            config_path.write_text(json.dumps({
                "session_path": "input/session.jsonl",
                "state_directory": "state",
                "output_directory": "output",
                "poll_interval_seconds": 0,
                "max_polls": 1,
                "max_restarts": 2,
                "dry_run": True,
            }), encoding="utf-8")

            config = RepricingRuntimeMVPConfig.from_json(config_path)

            self.assertEqual(config.session_path, (root / "input/session.jsonl").resolve())
            self.assertEqual(config.database_path, (root / "state/repricing_paper.sqlite3").resolve())
            self.assertEqual(config.status_path.name, "repricing_runtime_status.json")
            self.assertTrue(config.dry_run)

    def test_preflight_validates_session_directories_and_frozen_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session, self._events())
            config = self._config(root, session)

            result = validate_runtime_preflight(config)

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["detector_state"], "FROZEN_CONFIG_VERIFIED")
            self.assertTrue(config.database_path.exists())

    def test_runtime_lock_prevents_second_instance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock_path = Path(tmp) / "runtime.lock"
            first = RuntimeInstanceLock(lock_path)
            first.acquire()
            try:
                with self.assertRaises(RuntimeAlreadyRunningError):
                    RuntimeInstanceLock(lock_path).acquire()
            finally:
                first.release()
            with RuntimeInstanceLock(lock_path):
                self.assertTrue(lock_path.exists())

    def test_bounded_mvp_writes_status_heartbeat_summary_and_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session, self._events())
            config = self._config(root, session)
            mvp = ContinuousRepricingPaperMVP(
                config,
                now=lambda: FIXED_NOW,
                session_id_factory=lambda: "repricing-test-session",
            )

            status = mvp.run(install_signal_handlers=False)

            heartbeat = self._read(config.heartbeat_path)
            summary = self._read(config.summary_path)
            log_rows = [json.loads(line) for line in config.log_path.read_text(
                encoding="utf-8"
            ).splitlines()]
            day = summary["daily"]["2026-06-28"]
            self.assertEqual(status["status"], "STOPPED")
            self.assertFalse(status["runtime_alive"])
            self.assertEqual(heartbeat["status"], "STOPPED")
            self.assertFalse(heartbeat["runtime_alive"])
            self.assertEqual(heartbeat["detector_state"], "FROZEN_CONFIG_VERIFIED")
            self.assertEqual(heartbeat["paper_core_state"], "CLOSED_RECOVERABLE")
            self.assertEqual(day["events_received"], 3)
            self.assertEqual(day["valid_signals"], 1)
            self.assertEqual(day["rejected_signals"], 0)
            self.assertEqual(day["positions_opened"], 1)
            self.assertEqual(day["positions_closed"], 1)
            log_events = [row["event"] for row in log_rows]
            self.assertEqual(log_events[0], "runtime_mvp_start")
            self.assertEqual(log_events[-1], "runtime_mvp_stop")
            self.assertIn("runtime_health", log_events)

    def test_recoverable_failure_restarts_and_updates_daily_stats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session, self._events())
            config = self._config(root, session, max_restarts=1)
            calls = []

            def factory(runtime_config, *, now, health_observer):
                calls.append(runtime_config)
                fail = len(calls) == 1

                class FakeRuntime:
                    def run(self, **_kwargs):
                        if fail:
                            raise V5StreamUnavailableError("temporary source gap")
                        health = self_outer._health(runtime_config.session_id)
                        health_observer(health)
                        return health

                return FakeRuntime()

            self_outer = self
            mvp = ContinuousRepricingPaperMVP(
                config,
                now=lambda: FIXED_NOW,
                sleeper=lambda _seconds: None,
                session_id_factory=lambda: "restart-session",
                runtime_factory=factory,
            )

            status = mvp.run(install_signal_handlers=False)

            summary = self._read(config.summary_path)
            day = summary["daily"]["2026-06-28"]
            self.assertEqual(status["restart_count"], 1)
            self.assertEqual(day["runtime_failures"], 1)
            self.assertEqual(day["restart_count"], 1)
            self.assertEqual(len(calls), 2)

    def test_daily_summary_counts_valid_and_rejected_detector_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            events = self._events()
            rejected = json.loads(json.dumps(events[1]))
            rejected["payload"]["measurement"].update({
                "direction": "NONE",
                "qualified": False,
                "reason": "external_move_below_threshold",
            })
            events.insert(2, rejected)
            self._write(session, events)
            config = self._config(root, session)
            ContinuousRepricingPaperMVP(
                config,
                now=lambda: FIXED_NOW,
                session_id_factory=lambda: "signal-count-session",
            ).run(install_signal_handlers=False)

            day = self._read(config.summary_path)["daily"]["2026-06-28"]
            self.assertEqual(day["events_received"], 4)
            self.assertEqual(day["valid_signals"], 1)
            self.assertEqual(day["rejected_signals"], 1)

    def test_unrecoverable_failure_stops_closed_without_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session, self._events())
            config = self._config(root, session, max_restarts=3)

            class BrokenRuntime:
                def run(self, **_kwargs):
                    raise ValueError("state integrity failure")

            mvp = ContinuousRepricingPaperMVP(
                config,
                now=lambda: FIXED_NOW,
                session_id_factory=lambda: "failed-session",
                runtime_factory=lambda *_args, **_kwargs: BrokenRuntime(),
            )

            with self.assertRaises(ValueError):
                mvp.run(install_signal_handlers=False)

            status = self._read(config.status_path)
            summary = self._read(config.summary_path)
            self.assertEqual(status["status"], "FAILED_CLOSED")
            self.assertEqual(status["restart_count"], 0)
            self.assertEqual(
                summary["daily"]["2026-06-28"]["runtime_failures"], 1
            )

    def test_preflight_rejects_holdout_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "sealed_holdout" / "session.jsonl"
            session.parent.mkdir()
            self._write(session, self._events())
            with self.assertRaises(ValueError):
                validate_runtime_preflight(self._config(root, session))

    def test_cli_requires_single_config_path(self) -> None:
        args = build_parser().parse_args(["--config", "runtime.json"])
        self.assertEqual(args.config, Path("runtime.json"))

    def test_process_recovery_reuses_unclean_session_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session, self._events())
            config = self._config(root, session, max_restarts=3)
            config.output_directory.mkdir(parents=True)
            config.status_path.write_text(json.dumps({
                "session_id": "unclean-session",
                "runtime_alive": True,
                "restart_count": 1,
                "status": "RUNNING",
            }), encoding="utf-8")
            mvp = ContinuousRepricingPaperMVP(
                config,
                now=lambda: FIXED_NOW,
                session_id_factory=lambda: "must-not-be-used",
            )

            status = mvp.run(install_signal_handlers=False)

            self.assertEqual(status["session_id"], "unclean-session")
            self.assertEqual(status["restart_count"], 2)

    def test_runtime_duration_is_split_at_utc_day_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            config = self._config(root, session)
            current = [datetime(2026, 6, 28, 23, 59, 59, tzinfo=UTC)]
            outputs = RuntimeOutputManager(config, "day-split", lambda: current[0])
            health = self._health("day-split")
            outputs.observe_health(health)
            current[0] = datetime(2026, 6, 29, 0, 0, 1, tzinfo=UTC)
            outputs.observe_health(health)

            summary = self._read(config.summary_path)
            self.assertEqual(
                summary["daily"]["2026-06-28"]["runtime_duration_seconds"], 1.0
            )
            self.assertEqual(
                summary["daily"]["2026-06-29"]["runtime_duration_seconds"], 1.0
            )

    @staticmethod
    def _config(
        root: Path,
        session: Path,
        *,
        max_restarts: int = 1,
    ) -> RepricingRuntimeMVPConfig:
        return RepricingRuntimeMVPConfig(
            session_path=session,
            state_directory=root / "state",
            output_directory=root / "output",
            poll_interval_seconds=0.0,
            max_polls=1,
            max_restarts=max_restarts,
            restart_backoff_seconds=0.0,
            dry_run=True,
        )

    @staticmethod
    def _health(session_id: str) -> PaperRuntimeHealth:
        timestamp = FIXED_NOW.isoformat()
        return PaperRuntimeHealth(
            session_id=session_id,
            status="STOPPED",
            runtime_alive=False,
            runtime_start_timestamp=timestamp,
            runtime_stop_timestamp=timestamp,
            last_poll_timestamp=timestamp,
            last_event_timestamp=timestamp,
            last_successful_processing_timestamp=timestamp,
            events_received=0,
            events_accepted=0,
            events_rejected=0,
            duplicate_events_skipped=0,
            positions_opened=0,
            positions_closed=0,
            valid_signals=0,
            rejected_signals=0,
            recovered_open_positions=0,
            current_open_positions=0,
            polls_completed=1,
            last_error=None,
            source_path="session.jsonl",
            database_path="paper.sqlite3",
            strategy_fingerprint=FrozenFingerprint.VALUE,
            detector_state="FROZEN_CONFIG_VERIFIED",
            paper_core_state="CLOSED_RECOVERABLE",
            dry_run=True,
        )

    @classmethod
    def _events(cls) -> list[dict[str, object]]:
        return [
            cls._snapshot("2026-06-28T17:00:00+00:00", 0.50, 240),
            {
                "event": "lag_measurement",
                "timestamp": "2026-06-28T17:00:00+00:00",
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
            cls._snapshot("2026-06-28T17:00:30+00:00", 0.54, 210),
        ]

    @staticmethod
    def _snapshot(timestamp: str, yes: float, expiry: float) -> dict[str, object]:
        return {
            "event": "polymarket_snapshot",
            "timestamp": timestamp,
            "payload": {
                "asset": "BTC",
                "market_id": "m1",
                "yes_price": yes,
                "no_price": 1.0 - yes,
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
    def _read(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))


class FrozenFingerprint:
    VALUE = "d5d389be45d472628aab06b3aeeb281593e74d48b82902e12712047c91fec010"


if __name__ == "__main__":
    unittest.main()
