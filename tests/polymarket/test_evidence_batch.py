from __future__ import annotations

import json
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from pathlib import Path

from polymarket.evidence_batch.pipeline import BatchConfig, EvidenceBatchPipeline
from polymarket.edge_engine_v5.power_preflight import PowerPreflight


class EvidenceBatchTests(unittest.TestCase):
    def test_run_blocks_unsafe_power_configuration(self) -> None:
        with _workspace_temp() as folder:
            paths = _paths(Path(folder))
            pipeline = EvidenceBatchPipeline(
                BatchConfig(
                    runs_root=paths["runs"],
                    resolution_root=paths["resolutions"],
                    training_root=paths["training"],
                    batch_root=paths["batches"],
                ),
                capture_runner=lambda _: self.fail("capture must not start"),
            )
            unsafe = PowerPreflight(
                "Windows", 900, 0, False,
                ("AC sleep timeout is 900 seconds",),
                ("powercfg /change standby-timeout-ac 0",),
            )
            with patch(
                "polymarket.evidence_batch.pipeline.inspect_windows_power",
                return_value=unsafe,
            ):
                _, manifest = pipeline.run()
            self.assertEqual(manifest["failed_stage"], "power_preflight")
            self.assertEqual(manifest["verdict"], "BATCH_FAILED")

    def test_resume_pipeline_is_deterministic_and_enforces_sample_gate(self) -> None:
        with _workspace_temp() as folder:
            root = Path(folder)
            paths = _paths(root)
            session = _write_session(paths["runs"])
            fixture = _write_resolution_fixture(paths["fixture"])
            config = BatchConfig(
                assets=("BTC",),
                runs_root=paths["runs"],
                resolution_root=paths["resolutions"],
                training_root=paths["training"],
                batch_root=paths["batches"],
                resolution_mode="replay",
                resolution_fixture=fixture,
                total_target=10,
                per_asset_target=5,
                require_safe_power=False,
            )
            pipeline = EvidenceBatchPipeline(config)
            manifest_path, first = pipeline.resume(session)
            first_bytes = manifest_path.read_bytes()
            _, second = pipeline.resume(session)

            self.assertEqual(first_bytes, manifest_path.read_bytes())
            self.assertEqual(first, second)
            self.assertEqual(first["status"], "completed")
            self.assertEqual(first["verdict"], "INSUFFICIENT_PUBLIC_SAMPLE")
            self.assertFalse(first["project_training_authorized"])
            self.assertEqual(first["dataset"]["clean_rows"], 1)
            self.assertEqual(first["dataset"]["rows_by_asset"]["BTC"], 1)
            self.assertEqual(first["resolution"]["resolved"], 1)
            self.assertEqual(first["session_snapshot"]["session_count"], 1)

    def test_failed_stage_does_not_read_stale_artifact(self) -> None:
        with _workspace_temp() as folder:
            root = Path(folder)
            paths = _paths(root)
            session = _write_session(paths["runs"])
            paths["resolutions"].mkdir(parents=True)
            (paths["resolutions"] / "reconciliation_report.json").write_text(
                '{"resolved":999}', encoding="utf-8"
            )
            pipeline = EvidenceBatchPipeline(
                BatchConfig(
                    assets=("BTC",),
                    runs_root=paths["runs"],
                    resolution_root=paths["resolutions"],
                    training_root=paths["training"],
                    batch_root=paths["batches"],
                    resolution_mode="replay",
                ),
                resolution_runner=lambda _: 2,
            )
            _, manifest = pipeline.resume(session)
            self.assertEqual(manifest["status"], "failed")
            self.assertEqual(manifest["failed_stage"], "resolution")
            self.assertNotIn("resolution", manifest)

    def test_run_forces_public_capture_without_fallback(self) -> None:
        with _workspace_temp() as folder:
            root = Path(folder)
            paths = _paths(root)
            fixture = _write_resolution_fixture(paths["fixture"])
            observed = {}

            def capture_runner(config):
                observed["mock"] = config.mock
                observed["fallback"] = config.allow_mock_fallback
                return _write_session(paths["runs"]).parent

            pipeline = EvidenceBatchPipeline(
                BatchConfig(
                    assets=("BTC",),
                    runs_root=paths["runs"],
                    resolution_root=paths["resolutions"],
                    training_root=paths["training"],
                    batch_root=paths["batches"],
                    resolution_mode="replay",
                    resolution_fixture=fixture,
                    total_target=10,
                    per_asset_target=5,
                    require_safe_power=False,
                ),
                capture_runner=capture_runner,
            )
            _, manifest = pipeline.run()
            self.assertFalse(observed["mock"])
            self.assertFalse(observed["fallback"])
            self.assertEqual(manifest["mode"], "run")

    def test_refresh_mode_maps_to_resolution_reconcile_command(self) -> None:
        with _workspace_temp() as folder:
            root = Path(folder)
            paths = _paths(root)
            session = _write_session(paths["runs"])
            observed = {}

            def resolution_runner(args):
                observed["command"] = args[0]
                return 2

            pipeline = EvidenceBatchPipeline(
                BatchConfig(
                    assets=("BTC",),
                    runs_root=paths["runs"],
                    resolution_root=paths["resolutions"],
                    training_root=paths["training"],
                    batch_root=paths["batches"],
                    resolution_mode="refresh",
                ),
                resolution_runner=resolution_runner,
            )
            _, manifest = pipeline.resume(session)
            self.assertEqual(observed["command"], "reconcile")
            self.assertEqual(manifest["failed_stage"], "resolution")

    def test_overlapping_batch_fails_on_lock(self) -> None:
        with _workspace_temp() as folder:
            root = Path(folder)
            paths = _paths(root)
            session = _write_session(paths["runs"])
            paths["batches"].mkdir(parents=True)
            (paths["batches"] / ".pipeline.lock").write_text("busy")
            pipeline = EvidenceBatchPipeline(BatchConfig(
                assets=("BTC",),
                runs_root=paths["runs"],
                resolution_root=paths["resolutions"],
                training_root=paths["training"],
                batch_root=paths["batches"],
                resolution_mode="replay",
            ))
            _, manifest = pipeline.resume(session)
            self.assertEqual(manifest["status"], "failed")
            self.assertEqual(manifest["failed_stage"], "batch_lock")

    def test_active_session_is_rejected(self) -> None:
        with _workspace_temp() as folder:
            root = Path(folder)
            paths = _paths(root)
            session = _write_session(paths["runs"])
            lines = session.read_text(encoding="utf-8").splitlines()
            session.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
            pipeline = EvidenceBatchPipeline(BatchConfig(
                assets=("BTC",),
                runs_root=paths["runs"],
                resolution_root=paths["resolutions"],
                training_root=paths["training"],
                batch_root=paths["batches"],
                resolution_mode="replay",
            ))
            _, manifest = pipeline.resume(session)
            self.assertEqual(manifest["status"], "failed")
            self.assertEqual(manifest["failed_stage"], "session_validation")

    def test_incomplete_temporal_coverage_downgrades_manifest(self) -> None:
        with _workspace_temp() as folder:
            root = Path(folder)
            paths = _paths(root)
            session = _write_session(paths["runs"])
            rows = [
                json.loads(line)
                for line in session.read_text(encoding="utf-8").splitlines()
            ]
            rows[-1]["payload"]["campaign_completeness"] = {
                "status": "incomplete_temporal_coverage",
                "expected_duration_seconds": 300,
                "monotonic_elapsed_runtime_seconds": 300,
                "observed_utc_span_seconds": 120,
                "coverage_percentage": 40.0,
            }
            session.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            fixture = _write_resolution_fixture(paths["fixture"])
            pipeline = EvidenceBatchPipeline(BatchConfig(
                assets=("BTC",),
                runs_root=paths["runs"],
                resolution_root=paths["resolutions"],
                training_root=paths["training"],
                batch_root=paths["batches"],
                resolution_mode="replay",
                resolution_fixture=fixture,
                total_target=1,
                per_asset_target=1,
            ))
            _, manifest = pipeline.resume(session)
            self.assertEqual(manifest["status"], "completed")
            self.assertEqual(manifest["verdict"], "INCOMPLETE_CAMPAIGN")
            self.assertFalse(manifest["project_training_authorized"])
            self.assertEqual(
                manifest["capture"]["campaign_completeness"][
                    "coverage_percentage"
                ],
                40.0,
            )

    def test_usable_dataset_is_preserved_when_continuity_fails(self) -> None:
        with _workspace_temp() as folder:
            root = Path(folder)
            paths = _paths(root)
            session = _write_session(paths["runs"])
            rows = [
                json.loads(line)
                for line in session.read_text(encoding="utf-8").splitlines()
            ]
            rows = [
                row for index, row in enumerate(rows)
                if row["event"] != "capture_checkpoint" or index % 10 == 0
            ]
            session.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            fixture = _write_resolution_fixture(paths["fixture"])
            pipeline = EvidenceBatchPipeline(BatchConfig(
                assets=("BTC",),
                runs_root=paths["runs"],
                resolution_root=paths["resolutions"],
                training_root=paths["training"],
                batch_root=paths["batches"],
                resolution_mode="replay",
                resolution_fixture=fixture,
                total_target=1,
                per_asset_target=1,
            ))
            _, manifest = pipeline.resume(session)
            self.assertEqual(manifest["dataset"]["clean_rows"], 1)
            self.assertEqual(manifest["verdict"], "INCOMPLETE_CAMPAIGN")
            self.assertFalse(manifest["project_training_authorized"])


def _paths(root: Path) -> dict[str, Path]:
    return {
        "runs": root / "runs",
        "resolutions": root / "resolutions",
        "training": root / "training",
        "batches": root / "batches",
        "fixture": root / "fixture.jsonl",
    }


def _write_session(runs_root: Path) -> Path:
    session = runs_root / "batch-session" / "session.jsonl"
    session.parent.mkdir(parents=True)
    start = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=5)
    market = {
        "market_id": "condition-batch-1",
        "asset": "BTC",
        "question": "Bitcoin Up or Down",
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "yes_token_id": "yes",
        "no_token_id": "no",
        "active": True,
        "closed": False,
        "liquidity": 10_000,
        "volume": 20_000,
    }
    events = [{
        "event": "session_started",
        "timestamp": start.isoformat(),
        "payload": {
            "mode": "mock_fixture",
            "assets": ["BTC"],
            "duration_seconds": 300,
            "poll_interval_seconds": 5,
        },
    }, {
        "event": "market_lifecycle",
        "timestamp": start.isoformat(),
        "payload": {"current": "discovered", "market": market},
    }]
    for seconds in range(0, 301, 5):
        timestamp = start + timedelta(seconds=seconds)
        events.extend([{
            "event": "reference_price",
            "timestamp": timestamp.isoformat(),
            "payload": {
                "asset": "BTC",
                "price": 100 + seconds * 0.01,
                "source": "fixture",
                "timestamp": timestamp.isoformat(),
            },
        }, {
            "event": "polymarket_snapshot",
            "timestamp": timestamp.isoformat(),
            "payload": {
                "asset": "BTC",
                "market_id": market["market_id"],
                "yes_price": 0.5 + seconds * 0.0001,
                "no_price": 0.5 - seconds * 0.0001,
                "yes_bid": 0.49,
                "yes_ask": 0.51,
                "liquidity": 10_000,
                "seconds_to_expiry": 300 - seconds,
                "timestamp": timestamp.isoformat(),
            },
        }, {
            "event": "lag_measurement",
            "timestamp": timestamp.isoformat(),
            "payload": {
                "market_id": market["market_id"],
                "measurement": {"lag_score": 0.5, "confidence": 0.6},
            },
        }, {
            "event": "capture_checkpoint",
            "timestamp": timestamp.isoformat(),
            "payload": {
                "expected_reference_points": seconds // 5 + 1,
                "successful_reference_points": seconds // 5 + 1,
                "expected_market_points": seconds // 5 + 1,
                "successful_market_points": seconds // 5 + 1,
                "mode": "mock_fixture",
            },
        }])
    session.write_text(
        "\n".join(json.dumps(event) for event in events + [{
            "event": "session_completed",
            "timestamp": end.isoformat(),
            "payload": {"mode": "mock_fixture"},
        }]) + "\n",
        encoding="utf-8",
    )
    return session


def _write_resolution_fixture(path: Path) -> Path:
    path.write_text(json.dumps({
        "market_id": "condition-batch-1",
        "slug": "btc-updown-5m-1767268800",
        "retrieval_timestamp": "2026-01-01T12:06:00+00:00",
        "event": {
            "resolutionSource": "fixture",
            "markets": [{
                "conditionId": "condition-batch-1",
                "closed": True,
                "umaResolutionStatus": "resolved",
                "outcomes": json.dumps(["Up", "Down"]),
                "outcomePrices": json.dumps(["1", "0"]),
                "closedTime": "2026-01-01 12:05:30+00",
            }],
        },
    }) + "\n", encoding="utf-8")
    return path


def _workspace_temp() -> tempfile.TemporaryDirectory:
    return tempfile.TemporaryDirectory(dir=Path("tests/polymarket"))


if __name__ == "__main__":
    unittest.main()
