from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from polymarket.dataset_quality.analyzer import DatasetQualityAnalyzer
from polymarket.dataset_quality.filters import public_only, to_training_rows
from polymarket.dataset_quality.report import write_quality_report
from polymarket.edge_engine_v5.config import CaptureConfig
from polymarket.edge_engine_v5.long_capture import LongShadowCapture
from polymarket.edge_engine_v5.continuity import session_continuity
from polymarket.edge_engine_v5.power_preflight import (
    WindowsSleepInhibitor, inspect_windows_power,
)
from polymarket.feature_engine.config import FeatureConfig
from polymarket.feature_engine.dataset_builder import DatasetBuilder
from polymarket.feature_engine.export import write_csv, write_parquet
from polymarket.resolution_engine.cli import main as resolution_main


@dataclass(frozen=True)
class BatchConfig:
    assets: tuple[str, ...] = ("BTC", "ETH", "SOL")
    duration_seconds: float = 21_600.0
    poll_interval_seconds: float = 2.0
    discovery_interval_seconds: float = 5.0
    runs_root: Path = Path("polymarket/runs/v5")
    resolution_root: Path = Path("polymarket/data/resolutions")
    training_root: Path = Path("polymarket/data/training")
    batch_root: Path = Path("polymarket/runs/evidence_batches")
    resolution_mode: str = "refresh"
    resolution_fixture: Path | None = None
    total_target: int = 1_000
    per_asset_target: int = 200
    require_safe_power: bool = True

    def __post_init__(self) -> None:
        if self.resolution_mode not in {"refresh", "replay"}:
            raise ValueError("resolution_mode must be refresh or replay")
        if self.total_target < 1 or self.per_asset_target < 1:
            raise ValueError("sample targets must be positive")


class EvidenceBatchPipeline:
    def __init__(
        self,
        config: BatchConfig,
        capture_runner: Callable[[CaptureConfig], Path] | None = None,
        resolution_runner: Callable[[list[str]], int] | None = None,
    ) -> None:
        self.config = config
        self.capture_runner = capture_runner or _capture_public
        self.resolution_runner = resolution_runner or resolution_main

    def run(self) -> tuple[Path, dict]:
        power = inspect_windows_power()
        if self.config.require_safe_power and not power.safe_for_overnight:
            return self._failed_manifest(
                None, "power_preflight",
                RuntimeError(
                    "unsafe Windows power configuration: "
                    + "; ".join(power.warnings)
                    + ". Run: " + " && ".join(power.commands[:2])
                ),
            )
        capture_config = CaptureConfig(
            assets=self.config.assets,
            duration_seconds=self.config.duration_seconds,
            poll_interval_seconds=self.config.poll_interval_seconds,
            discovery_interval_seconds=self.config.discovery_interval_seconds,
            output_root=self.config.runs_root,
            mock=False,
            allow_mock_fallback=False,
        )
        try:
            with WindowsSleepInhibitor():
                session_dir = self.capture_runner(capture_config)
        except Exception as exc:
            return self._failed_manifest(None, "capture", exc)
        return self.resume(session_dir / "session.jsonl", invocation_mode="run")

    def resume(
        self, session: Path, invocation_mode: str = "resume"
    ) -> tuple[Path, dict]:
        session = session.resolve()
        if session.is_dir():
            session = session / "session.jsonl"
        if not session.exists():
            return self._failed_manifest(session, "session_validation",
                                         FileNotFoundError(str(session)))
        if not _session_is_completed(session):
            return self._failed_manifest(
                session,
                "session_validation",
                RuntimeError(
                    "session has no terminal session_completed event; capture may still be active"
                ),
            )
        batch_dir = self.config.batch_root / session.parent.name
        manifest_path = batch_dir / "batch_manifest.json"
        manifest = self._base_manifest(session, invocation_mode)
        batch_dir.mkdir(parents=True, exist_ok=True)
        lock_path = self.config.batch_root / ".pipeline.lock"
        try:
            lock_fd = _acquire_lock(lock_path)
        except Exception as exc:
            return self._failed_manifest(session, "batch_lock", exc)
        try:
            snapshot_root, snapshot_index = _materialize_session_snapshot(
                self.config.runs_root, batch_dir, session
            )
            manifest["stages"]["session_snapshot"] = _stage(
                "completed", snapshot_index
            )
            manifest["session_snapshot"] = _load_json(snapshot_index)
            resolution_command = (
                "reconcile"
                if self.config.resolution_mode == "refresh"
                else "replay"
            )
            resolution_args = [
                resolution_command,
                "--runs-root", str(snapshot_root),
                "--output-root", str(self.config.resolution_root),
            ]
            if self.config.resolution_fixture:
                resolution_args += ["--fixture", str(self.config.resolution_fixture)]
            if self.resolution_runner(resolution_args) != 0:
                raise RuntimeError("resolution stage returned non-zero status")
            resolution_report = _load_json(
                self.config.resolution_root / "reconciliation_report.json"
            )
            manifest["stages"]["resolution"] = _stage(
                "completed",
                self.config.resolution_root / "reconciliation_report.json",
            )

            build = DatasetBuilder(FeatureConfig(
                runs_root=snapshot_root,
                output_root=self.config.training_root,
                resolutions_path=self.config.resolution_root / "resolutions.jsonl",
            )).build()
            manifest["stages"]["features"] = _stage(
                "completed", build.summary_path
            )

            analyzer = DatasetQualityAnalyzer(build.csv_path)
            metrics = analyzer.analyze()
            write_quality_report(
                self.config.training_root / "quality_report.json", metrics
            )
            _, raw_rows = analyzer.load_rows()
            selected = to_training_rows(public_only(raw_rows))
            write_csv(self.config.training_root / "public_only.csv", selected)
            write_parquet(
                self.config.training_root / "public_only.parquet", selected
            )
            manifest["stages"]["quality"] = _stage(
                "completed", self.config.training_root / "quality_report.json"
            )

            missingness = _load_json(
                self.config.training_root / "missingness_diagnostics.json"
            )
            progress = _progress(metrics, self.config)
            verdict = _verdict(metrics, progress)
            completeness = manifest["capture"].get("campaign_completeness", {})
            continuity = manifest["capture"]["observation_continuity"]
            if (
                completeness.get("status")
                not in (None, "complete", "legacy_unknown")
                or continuity["status"] != "continuous"
            ):
                verdict = "INCOMPLETE_CAMPAIGN"
            manifest.update({
                "status": "completed",
                "verdict": verdict,
                "resolution": {
                    key: resolution_report.get(key)
                    for key in (
                        "total_markets", "resolved", "unresolved", "missing",
                        "ambiguous", "cancelled", "malformed",
                        "authoritative_coverage_percentage",
                    )
                },
                "dataset": {
                    "clean_rows": metrics.total_samples,
                    "rows_by_asset": metrics.asset_counts,
                    "up_count": metrics.up_count,
                    "down_count": metrics.down_count,
                    "minority_class_percentage": metrics.minority_class_percentage,
                    "feature_completeness_percentage": (
                        metrics.feature_completeness_percentage
                    ),
                    "dataset_quality_score": metrics.dataset_quality_score,
                    "quality_engine_recommended": metrics.training_recommended,
                    "sparse_rows_excluded": len(
                        missingness.get("excluded_rows", [])
                    ),
                },
                "progress": progress,
                "project_training_authorized": verdict == "DATA_GATE_PASSED",
                "artifacts": _artifact_map(self.config, session),
            })
        except Exception as exc:
            failed_stage = next(
                (
                    name for name in (
                        "session_snapshot", "resolution", "features", "quality"
                    )
                    if manifest["stages"][name]["status"] != "completed"
                ),
                "post_processing",
            )
            manifest["status"] = "failed"
            manifest["verdict"] = "BATCH_FAILED"
            manifest["failed_stage"] = failed_stage
            manifest["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            os.close(lock_fd)
            lock_path.unlink(missing_ok=True)
        _write_manifest(manifest_path, manifest)
        return manifest_path, manifest

    def _base_manifest(self, session: Path, invocation_mode: str) -> dict:
        capture = _session_metadata(session)
        return {
            "schema_version": 1,
            "batch_id": session.parent.name,
            "mode": invocation_mode,
            "source_session": str(session),
            "source_session_sha256": _sha256(session),
            "capture": capture,
            "configuration": _jsonable(asdict(self.config)),
            "status": "running",
            "verdict": "PENDING",
            "stages": {
                "capture": {
                    "status": "completed",
                    "artifact": str(session),
                    "sha256": _sha256(session),
                },
                "session_snapshot": {"status": "pending"},
                "resolution": {"status": "pending"},
                "features": {"status": "pending"},
                "quality": {"status": "pending"},
            },
        }

    def _failed_manifest(
        self, session: Path | None, stage: str, exc: Exception
    ) -> tuple[Path, dict]:
        batch_id = session.parent.name if session else "capture_failed"
        path = self.config.batch_root / batch_id / "batch_manifest.json"
        manifest = {
            "schema_version": 1,
            "batch_id": batch_id,
            "status": "failed",
            "verdict": "BATCH_FAILED",
            "failed_stage": stage,
            "error": f"{type(exc).__name__}: {exc}",
            "configuration": _jsonable(asdict(self.config)),
        }
        _write_manifest(path, manifest)
        return path, manifest


def _capture_public(config: CaptureConfig) -> Path:
    output, _ = LongShadowCapture(config).run()
    return output


def _session_metadata(path: Path) -> dict:
    first = last = None
    started = {}
    completed = {}
    events = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            event = json.loads(line)
            events.append(event)
            timestamp = str(event.get("timestamp", ""))
            first = first or timestamp
            last = timestamp
            if event.get("event") == "session_started":
                started = event.get("payload", {})
            elif event.get("event") == "session_completed":
                completed = event.get("payload", {})
    continuity = session_continuity(events)
    completeness = dict(completed.get(
        "campaign_completeness",
        {"status": "legacy_unknown"},
    ))
    if continuity["status"] != "continuous":
        completeness["status"] = "incomplete_campaign"
        completeness["rejection_reasons"] = continuity["rejection_reasons"]
    return {
        "started_at": first,
        "ended_at": last,
        "mode": started.get("mode", "unknown"),
        "assets": started.get("assets", []),
        "duration_seconds": started.get("duration_seconds"),
        "poll_interval_seconds": started.get("poll_interval_seconds"),
        "allow_mock_fallback": False,
        "campaign_completeness": completeness,
        "observation_continuity": continuity,
        "discovery_failure_count": completed.get("discovery_failure_count", 0),
    }


def _session_is_completed(path: Path) -> bool:
    last_event = ""
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                last_event = str(json.loads(line).get("event", ""))
            except json.JSONDecodeError:
                return False
    return last_event == "session_completed"


def _materialize_session_snapshot(
    runs_root: Path, batch_dir: Path, source_session: Path
) -> tuple[Path, Path]:
    cutoff = _completion_timestamp(source_session)
    snapshot_root = batch_dir / "input_sessions"
    if snapshot_root.exists():
        resolved = snapshot_root.resolve()
        if batch_dir.resolve() not in resolved.parents:
            raise RuntimeError(f"unsafe snapshot path: {resolved}")
        shutil.rmtree(snapshot_root)
    entries = []
    for candidate in sorted(runs_root.glob("*/session.jsonl")):
        if candidate.parent.name == "latest":
            continue
        last_timestamp = _last_event_timestamp(candidate)
        if last_timestamp > cutoff:
            continue
        destination = snapshot_root / candidate.parent.name / "session.jsonl"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(candidate, destination)
        entries.append({
            "session": candidate.parent.name,
            "last_event_timestamp": last_timestamp,
            "terminal": _session_is_completed(candidate),
            "sha256": _sha256(destination),
        })
    if not entries:
        raise RuntimeError("no completed sessions available at source-session cutoff")
    index = {
        "source_session": source_session.parent.name,
        "cutoff_timestamp": cutoff,
        "sessions": entries,
        "session_count": len(entries),
    }
    index_path = batch_dir / "input_sessions.json"
    _write_manifest(index_path, index)
    return snapshot_root, index_path


def _completion_timestamp(path: Path) -> str:
    last = None
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            event = json.loads(line)
            if event.get("event") == "session_completed":
                last = str(event["timestamp"])
    if last is None:
        raise RuntimeError(f"session is not completed: {path}")
    return last


def _last_event_timestamp(path: Path) -> str:
    last = None
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            event = json.loads(line)
            last = str(event.get("timestamp", ""))
    if not last:
        raise RuntimeError(f"session has no valid events: {path}")
    return last


def _progress(metrics, config: BatchConfig) -> dict:
    by_asset = {
        asset: {
            "current": metrics.asset_counts.get(asset, 0),
            "target": config.per_asset_target,
            "percentage": round(
                min(1.0, metrics.asset_counts.get(asset, 0)
                    / config.per_asset_target) * 100, 2
            ),
        }
        for asset in config.assets
    }
    return {
        "total": {
            "current": metrics.total_samples,
            "target": config.total_target,
            "percentage": round(
                min(1.0, metrics.total_samples / config.total_target) * 100, 2
            ),
        },
        "by_asset": by_asset,
    }


def _verdict(metrics, progress: dict) -> str:
    if (
        metrics.total_samples < progress["total"]["target"]
        or any(
            row["current"] < row["target"]
            for row in progress["by_asset"].values()
        )
    ):
        return "INSUFFICIENT_PUBLIC_SAMPLE"
    if not metrics.training_recommended:
        return "DATA_QUALITY_FAILED"
    return "DATA_GATE_PASSED"


def _stage(status: str, artifact: Path) -> dict:
    if not artifact.exists():
        raise FileNotFoundError(f"Expected fresh artifact was not produced: {artifact}")
    return {
        "status": status,
        "artifact": str(artifact.resolve()),
        "sha256": _sha256(artifact),
    }


def _artifact_map(config: BatchConfig, session: Path) -> dict:
    paths = {
        "session": session,
        "resolutions": config.resolution_root / "resolutions.jsonl",
        "reconciliation_report": (
            config.resolution_root / "reconciliation_report.json"
        ),
        "dataset_csv": config.training_root / "dataset.csv",
        "dataset_parquet": config.training_root / "dataset.parquet",
        "feature_summary": config.training_root / "feature_summary.json",
        "missingness_diagnostics": (
            config.training_root / "missingness_diagnostics.json"
        ),
        "quality_report": config.training_root / "quality_report.json",
        "public_only_csv": config.training_root / "public_only.csv",
        "public_only_parquet": config.training_root / "public_only.parquet",
        "campaign_stdout_log": session.parent / "campaign.stdout.log",
        "campaign_stderr_log": session.parent / "campaign.stderr.log",
    }
    return {
        name: {"path": str(path.resolve()), "sha256": _sha256(path)}
        for name, path in paths.items() if path.exists()
    }


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Required stage artifact missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_manifest(path: Path, manifest: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _acquire_lock(path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        return os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(
            f"another evidence batch is already writing canonical artifacts: {path}"
        ) from exc


def _jsonable(value):
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value
