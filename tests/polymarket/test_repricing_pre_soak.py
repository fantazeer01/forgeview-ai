from __future__ import annotations

import json
import tempfile
import unittest
from collections import namedtuple
from datetime import UTC, datetime
from pathlib import Path

from polymarket.edge_engine_v5.power_preflight import PowerPreflight
from polymarket.repricing_research import (
    RepricingRuntimeMVPConfig,
    run_open_position_restart_drills,
    run_pre_soak_verification,
)
from polymarket.repricing_research.pre_soak import (
    run_session_rotation_drill,
    run_stale_event_guard_drill,
    run_write_latency_guard_drill,
)
from polymarket.repricing_research.runtime_mvp import (
    resolve_latest_v5_session,
    validate_runtime_preflight,
)


Disk = namedtuple("Disk", "total used free")
NOW = datetime(2026, 6, 28, 18, 0, 0, tzinfo=UTC)
SAFE_POWER = PowerPreflight("Windows", 0, 0, True, (), ())
UNSAFE_POWER = PowerPreflight(
    "Windows", 900, 0, False, ("AC sleep timeout is 900 seconds",), ()
)


class RepricingPreSoakTests(unittest.TestCase):
    def test_power_disk_and_write_latency_preflight_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session)
            config = self._config(root, session)
            ticks = iter((0.0, 0.01, 0.01, 0.02))

            result = validate_runtime_preflight(
                config,
                power_inspector=lambda: SAFE_POWER,
                disk_usage=lambda _path: Disk(10_000, 1_000, 9_000),
                write_clock=lambda: next(ticks),
            )

            self.assertTrue(result["power"]["safe_for_overnight"])
            self.assertEqual(result["free_disk_bytes"], 9_000)
            self.assertLessEqual(result["preflight_write_latency_ms"], 20.0)

    def test_unsafe_power_low_disk_and_slow_write_each_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session)
            config = self._config(root, session)
            with self.assertRaisesRegex(ValueError, "power"):
                validate_runtime_preflight(
                    config,
                    power_inspector=lambda: UNSAFE_POWER,
                    disk_usage=lambda _path: Disk(10_000, 1_000, 9_000),
                )
            with self.assertRaisesRegex(ValueError, "disk"):
                validate_runtime_preflight(
                    config,
                    power_inspector=lambda: SAFE_POWER,
                    disk_usage=lambda _path: Disk(10_000, 9_999, 1),
                )
            ticks = iter((0.0, 1.0, 1.0, 2.0))
            with self.assertRaisesRegex(ValueError, "write latency"):
                validate_runtime_preflight(
                    config,
                    power_inspector=lambda: SAFE_POWER,
                    disk_usage=lambda _path: Disk(10_000, 1_000, 9_000),
                    write_clock=lambda: next(ticks),
                )

    def test_latest_session_resolution_and_rotation_drill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sessions = root / "sessions"
            first = sessions / "20260628_170000" / "session.jsonl"
            second = sessions / "20260628_170030" / "session.jsonl"
            first.parent.mkdir(parents=True)
            second.parent.mkdir(parents=True)
            self._write(first)
            self._write(second)
            self.assertEqual(resolve_latest_v5_session(sessions), second.resolve())

            result = run_session_rotation_drill(root / "drill", lambda: NOW)
            self.assertTrue(result["passed"])
            self.assertEqual(result["rotation_count"], 1)

    def test_all_open_position_restart_drills_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_open_position_restart_drills(Path(tmp), lambda: NOW)
            self.assertEqual(result, {
                "restart_with_open_position": True,
                "restart_during_processing": True,
                "restart_after_graceful_shutdown": True,
            })

    def test_stale_event_and_write_latency_guards_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stale = run_stale_event_guard_drill(root / "stale")
            write = run_write_latency_guard_drill(root / "write", lambda: NOW)
            self.assertTrue(stale["passed"])
            self.assertTrue(stale["stale_event_detected"])
            self.assertTrue(write["passed"])
            self.assertIn("write latency", write["last_error"])

    def test_full_verifier_emits_ready_verdict_and_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            output = root / "output"
            self._write(session)
            config = self._config(root, session)

            result = run_pre_soak_verification(
                config,
                output,
                power_inspector=lambda: SAFE_POWER,
                disk_usage=lambda _path: Disk(10_000, 1_000, 9_000),
                now=lambda: NOW,
            )

            self.assertEqual(result["verdict"], "READY_FOR_24H_SOAK")
            self.assertEqual(result["remaining_blockers"], [])
            for name in (
                "repricing_pre_soak_report.md",
                "repricing_pre_soak_validation.json",
                "repricing_runtime_readiness.json",
            ):
                self.assertTrue((output / name).exists())
            readiness = json.loads(
                (output / "repricing_runtime_readiness.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(readiness["verdict"], "READY_FOR_24H_SOAK")
            self.assertFalse(readiness["soak_launched"])

    @staticmethod
    def _config(root: Path, session: Path) -> RepricingRuntimeMVPConfig:
        return RepricingRuntimeMVPConfig(
            session_path=session,
            state_directory=root / "state",
            output_directory=root / "runtime-output",
            minimum_free_disk_bytes=100,
            require_safe_power=True,
            max_event_staleness_seconds=30,
            max_write_latency_seconds=0.5,
            max_polls=1,
            dry_run=True,
        )

    @staticmethod
    def _write(path: Path) -> None:
        event = {
            "event": "session_started",
            "timestamp": "2026-06-28T17:00:00+00:00",
            "payload": {},
        }
        path.write_text(json.dumps(event) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
