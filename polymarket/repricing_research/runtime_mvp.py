from __future__ import annotations

import argparse
import json
import os
import shutil
import time
import uuid
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, time as datetime_time, timedelta
from pathlib import Path
from typing import Any, Callable

from polymarket.edge_engine_v5.power_preflight import (
    WindowsSleepInhibitor,
    inspect_windows_power,
)

from .paper_core import FrozenPaperConfig, RestartSafePaperCore
from .paper_runtime import (
    ManagedRepricingPaperRuntime,
    PaperRuntimeConfig,
    PaperRuntimeHealth,
    RuntimeTerminalDrainError,
)
from .v5_stream_adapter import (
    V5JsonlPaperAdapter,
    V5StreamUnavailableError,
)


class RuntimeAlreadyRunningError(RuntimeError):
    """Raised when another process owns the runtime lock."""


@dataclass(frozen=True)
class RepricingRuntimeMVPConfig:
    session_path: Path | None
    state_directory: Path
    output_directory: Path
    session_root: Path | None = None
    poll_interval_seconds: float = 1.0
    max_polls: int | None = None
    max_runtime_seconds: float | None = None
    max_restarts: int = 3
    restart_backoff_seconds: float = 1.0
    dry_run: bool = False
    minimum_free_disk_bytes: int = 2 * 1024 * 1024 * 1024
    require_safe_power: bool = True
    max_event_staleness_seconds: float = 30.0
    max_write_latency_seconds: float = 0.5
    max_events_per_batch: int = 1000
    max_backlog_bytes: int = 64 * 1024 * 1024
    max_processing_stall_seconds: float = 30.0
    heartbeat_interval_seconds: float = 5.0
    terminal_drain_seconds: float = 60.0

    def __post_init__(self) -> None:
        if self.max_restarts < 0:
            raise ValueError("max restarts must be non-negative")
        if self.restart_backoff_seconds < 0:
            raise ValueError("restart backoff must be non-negative")
        if self.session_path is None and self.session_root is None:
            raise ValueError("session_path or session_root is required")
        if self.minimum_free_disk_bytes <= 0:
            raise ValueError("minimum free disk bytes must be positive")
        PaperRuntimeConfig(
            session_path=self.session_path or self.session_root / "session.jsonl",
            database_path=self.database_path,
            health_path=self.heartbeat_path,
            poll_interval_seconds=self.poll_interval_seconds,
            max_polls=self.max_polls,
            max_runtime_seconds=self.max_runtime_seconds,
            dry_run=self.dry_run,
            max_event_staleness_seconds=self.max_event_staleness_seconds,
            max_write_latency_seconds=self.max_write_latency_seconds,
            max_events_per_batch=self.max_events_per_batch,
            max_backlog_bytes=self.max_backlog_bytes,
            max_processing_stall_seconds=self.max_processing_stall_seconds,
            heartbeat_interval_seconds=self.heartbeat_interval_seconds,
            safe_shutdown_path=self.safe_shutdown_path,
            terminal_drain_seconds=self.terminal_drain_seconds,
            require_session_completed=not self.dry_run,
        )

    @property
    def database_path(self) -> Path:
        return self.state_directory / "repricing_paper.sqlite3"

    @property
    def lock_path(self) -> Path:
        return self.state_directory / "repricing_runtime.lock"

    @property
    def status_path(self) -> Path:
        return self.output_directory / "repricing_runtime_status.json"

    @property
    def heartbeat_path(self) -> Path:
        return self.output_directory / "repricing_runtime_heartbeat.json"

    @property
    def safe_shutdown_path(self) -> Path:
        return self.output_directory / "repricing_runtime_safe_shutdown.json"

    @property
    def summary_path(self) -> Path:
        return self.output_directory / "repricing_runtime_summary.json"

    @property
    def log_path(self) -> Path:
        return self.output_directory / "repricing_runtime.log"

    @classmethod
    def from_json(cls, path: str | Path) -> RepricingRuntimeMVPConfig:
        source = Path(path).resolve()
        # Windows PowerShell 5 writes `-Encoding utf8` with a BOM. Accept it so
        # launch configuration can be validated before a producer is started.
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError("runtime configuration must be a JSON object")
        required = ("state_directory", "output_directory")
        missing = [name for name in required if name not in payload]
        if missing:
            raise ValueError(f"runtime configuration missing: {', '.join(missing)}")

        def resolve(value: str) -> Path:
            candidate = Path(value)
            return (source.parent / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()

        return cls(
            session_path=(
                resolve(payload["session_path"])
                if payload.get("session_path") is not None else None
            ),
            state_directory=resolve(payload["state_directory"]),
            output_directory=resolve(payload["output_directory"]),
            session_root=(
                resolve(payload["session_root"])
                if payload.get("session_root") is not None else None
            ),
            poll_interval_seconds=float(payload.get("poll_interval_seconds", 1.0)),
            max_polls=(int(payload["max_polls"]) if payload.get("max_polls") is not None else None),
            max_runtime_seconds=(
                float(payload["max_runtime_seconds"])
                if payload.get("max_runtime_seconds") is not None else None
            ),
            max_restarts=int(payload.get("max_restarts", 3)),
            restart_backoff_seconds=float(payload.get("restart_backoff_seconds", 1.0)),
            dry_run=bool(payload.get("dry_run", False)),
            minimum_free_disk_bytes=int(
                payload.get("minimum_free_disk_bytes", 2 * 1024 * 1024 * 1024)
            ),
            require_safe_power=bool(payload.get("require_safe_power", True)),
            max_event_staleness_seconds=float(
                payload.get("max_event_staleness_seconds", 30.0)
            ),
            max_write_latency_seconds=float(
                payload.get("max_write_latency_seconds", 0.5)
            ),
            max_events_per_batch=int(payload.get("max_events_per_batch", 1000)),
            max_backlog_bytes=int(
                payload.get("max_backlog_bytes", 64 * 1024 * 1024)
            ),
            max_processing_stall_seconds=float(
                payload.get("max_processing_stall_seconds", 30.0)
            ),
            heartbeat_interval_seconds=float(
                payload.get("heartbeat_interval_seconds", 5.0)
            ),
            terminal_drain_seconds=float(
                payload.get("terminal_drain_seconds", 60.0)
            ),
        )


class RuntimeInstanceLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._handle = None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        if self.path.stat().st_size == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            handle.close()
            raise RuntimeAlreadyRunningError(
                f"repricing runtime lock is already held: {self.path}"
            ) from exc
        handle.seek(0)
        handle.truncate()
        handle.write(
            (json.dumps({"pid": os.getpid()}, sort_keys=True) + "\n").encode("utf-8")
        )
        handle.flush()
        self._handle = handle

    def release(self) -> None:
        if self._handle is None:
            return
        self._handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        self._handle.close()
        self._handle = None

    def __enter__(self) -> RuntimeInstanceLock:
        self.acquire()
        return self

    def __exit__(self, *_: object) -> None:
        self.release()


class RuntimeOutputManager:
    COUNTERS = (
        "events_received",
        "valid_signals",
        "rejected_signals",
        "positions_opened",
        "positions_closed",
    )

    def __init__(
        self,
        config: RepricingRuntimeMVPConfig,
        session_id: str,
        now: Callable[[], datetime],
    ) -> None:
        self.config = config
        self.session_id = session_id
        self.now = now
        self._previous: dict[str, float | int] = {}
        self._last_observed_at: datetime | None = None
        self._summary = self._load_summary()

    def begin_attempt(self) -> None:
        self._previous = {}
        self._last_observed_at = None

    def observe_health(self, health: PaperRuntimeHealth) -> None:
        current = asdict(health)
        observed_at = self.now()
        day = observed_at.astimezone(UTC).date().isoformat()
        bucket = self._day(day)
        for name in self.COUNTERS:
            value = int(current[name])
            prior = int(self._previous.get(name, 0))
            bucket[name] += max(0, value - prior)
        if self._last_observed_at is not None:
            self._add_runtime_duration(self._last_observed_at, observed_at)
        bucket["current_open_positions"] = health.current_open_positions
        self._previous = {name: int(current[name]) for name in self.COUNTERS}
        self._last_observed_at = observed_at
        self._summary["generated_at_utc"] = observed_at.isoformat()
        self._summary["session_id"] = self.session_id
        self._write_summary()
        self.log(
            "runtime_health",
            status=health.status,
            polls_completed=health.polls_completed,
            events_received=health.events_received,
            current_open_positions=health.current_open_positions,
            last_error=health.last_error,
        )

    def record_failure(self, error: str) -> None:
        bucket = self._day(self.now().astimezone(UTC).date().isoformat())
        bucket["runtime_failures"] += 1
        self._summary["last_error"] = error
        self._write_summary()

    def record_restart(self) -> None:
        bucket = self._day(self.now().astimezone(UTC).date().isoformat())
        bucket["restart_count"] += 1
        self._summary["restart_count"] += 1
        self._write_summary()

    def write_status(self, **values: Any) -> dict[str, Any]:
        status = {
            "session_id": self.session_id,
            "updated_at_utc": self.now().isoformat(),
            **values,
        }
        _write_json(self.config.status_path, status)
        return status

    def log(self, event: str, level: str = "INFO", **values: Any) -> None:
        row = {
            "timestamp": self.now().isoformat(),
            "level": level,
            "event": event,
            "session_id": self.session_id,
            **values,
        }
        self.config.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")

    def _load_summary(self) -> dict[str, Any]:
        if self.config.summary_path.exists():
            payload = json.loads(self.config.summary_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict) and "daily" in payload:
                return payload
        return {
            "session_id": self.session_id,
            "generated_at_utc": self.now().isoformat(),
            "restart_count": 0,
            "last_error": None,
            "daily": {},
        }

    def _day(self, day: str) -> dict[str, Any]:
        return self._summary["daily"].setdefault(day, {
            "runtime_duration_seconds": 0.0,
            "events_received": 0,
            "valid_signals": 0,
            "rejected_signals": 0,
            "positions_opened": 0,
            "positions_closed": 0,
            "current_open_positions": 0,
            "runtime_failures": 0,
            "restart_count": 0,
        })

    def _write_summary(self) -> None:
        _write_json(self.config.summary_path, self._summary)

    def _add_runtime_duration(self, start: datetime, end: datetime) -> None:
        cursor = start.astimezone(UTC)
        finish = end.astimezone(UTC)
        while cursor < finish:
            midnight = datetime.combine(
                cursor.date() + timedelta(days=1), datetime_time.min, tzinfo=UTC
            )
            boundary = min(midnight, finish)
            self._day(cursor.date().isoformat())["runtime_duration_seconds"] += (
                boundary - cursor
            ).total_seconds()
            cursor = boundary


class ContinuousRepricingPaperMVP:
    def __init__(
        self,
        config: RepricingRuntimeMVPConfig,
        *,
        now: Callable[[], datetime] | None = None,
        sleeper: Callable[[float], None] | None = None,
        session_id_factory: Callable[[], str] | None = None,
        runtime_factory: Callable[..., ManagedRepricingPaperRuntime] | None = None,
        sleep_inhibitor_factory: Callable[[], Any] | None = None,
    ) -> None:
        self.config = config
        self.now = now or (lambda: datetime.now(UTC))
        self.sleeper = sleeper or time.sleep
        self.session_id_factory = session_id_factory or self._new_session_id
        self.runtime_factory = runtime_factory or ManagedRepricingPaperRuntime
        self.sleep_inhibitor_factory = (
            sleep_inhibitor_factory or WindowsSleepInhibitor
        )

    def run(self, *, install_signal_handlers: bool = True) -> dict[str, Any]:
        with RuntimeInstanceLock(self.config.lock_path), self.sleep_inhibitor_factory():
            preflight = validate_runtime_preflight(self.config)
            session_resolver = (
                (lambda: resolve_latest_v5_session(self.config.session_root))
                if self.config.session_root is not None else None
            )
            session_id, startup_restarts = self._session_identity()
            outputs = RuntimeOutputManager(self.config, session_id, self.now)
            outputs.log("runtime_mvp_start", preflight=preflight)
            outputs.write_status(
                status="STARTING",
                runtime_alive=True,
                process_id=os.getpid(),
                restart_count=startup_restarts,
                last_error=None,
                preflight=preflight,
            )
            restart_count = startup_restarts
            if startup_restarts:
                outputs.record_restart()
                outputs.log("runtime_mvp_process_recovery", restart_count=restart_count)
            while True:
                runtime_config = PaperRuntimeConfig(
                    session_path=Path(preflight["session_path"]),
                    database_path=self.config.database_path,
                    health_path=self.config.heartbeat_path,
                    poll_interval_seconds=self.config.poll_interval_seconds,
                    max_polls=self.config.max_polls,
                    max_runtime_seconds=self.config.max_runtime_seconds,
                    dry_run=self.config.dry_run,
                    session_id=session_id,
                    max_event_staleness_seconds=self.config.max_event_staleness_seconds,
                    max_write_latency_seconds=self.config.max_write_latency_seconds,
                    max_events_per_batch=self.config.max_events_per_batch,
                    max_backlog_bytes=self.config.max_backlog_bytes,
                    max_processing_stall_seconds=self.config.max_processing_stall_seconds,
                    heartbeat_interval_seconds=self.config.heartbeat_interval_seconds,
                    safe_shutdown_path=self.config.safe_shutdown_path,
                    terminal_drain_seconds=self.config.terminal_drain_seconds,
                    require_session_completed=not self.config.dry_run,
                )
                outputs.begin_attempt()
                runtime_kwargs = {
                    "now": self.now,
                    "health_observer": outputs.observe_health,
                }
                if session_resolver is not None:
                    runtime_kwargs["session_resolver"] = session_resolver
                runtime = self.runtime_factory(runtime_config, **runtime_kwargs)
                try:
                    health = runtime.run(
                        install_signal_handlers=install_signal_handlers
                    )
                    if (
                        not self.config.dry_run
                        and (
                            not health.session_completed_seen
                            or health.session_health_status != "complete"
                            or not health.terminal_drain_completed
                        )
                    ):
                        raise RuntimeTerminalDrainError(
                            "managed runtime stopped without verified terminal "
                            "session reconciliation"
                        )
                except V5StreamUnavailableError as exc:
                    error = f"{type(exc).__name__}: {exc}"
                    outputs.record_failure(error)
                    outputs.log("runtime_recoverable_failure", "WARNING", error=error)
                    if restart_count >= self.config.max_restarts:
                        status = outputs.write_status(
                            status="FAILED",
                            runtime_alive=False,
                            process_id=0,
                            restart_count=restart_count,
                            last_error=error,
                            preflight=preflight,
                        )
                        raise
                    restart_count += 1
                    outputs.record_restart()
                    outputs.write_status(
                        status="RESTARTING",
                        runtime_alive=True,
                        process_id=os.getpid(),
                        restart_count=restart_count,
                        last_error=error,
                        preflight=preflight,
                    )
                    self.sleeper(self.config.restart_backoff_seconds)
                    continue
                except Exception as exc:
                    error = f"{type(exc).__name__}: {exc}"
                    outputs.record_failure(error)
                    outputs.log("runtime_unrecoverable_failure", "ERROR", error=error)
                    outputs.write_status(
                        status="FAILED_CLOSED",
                        runtime_alive=False,
                        process_id=0,
                        restart_count=restart_count,
                        last_error=error,
                        preflight=preflight,
                    )
                    raise
                status = outputs.write_status(
                    status="STOPPED",
                    runtime_alive=False,
                    process_id=0,
                    restart_count=restart_count,
                    last_error=health.last_error,
                    preflight=preflight,
                )
                outputs.log("runtime_mvp_stop", restart_count=restart_count)
                return status

    def _new_session_id(self) -> str:
        timestamp = self.now().astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
        return f"repricing-{timestamp}-{uuid.uuid4().hex[:8]}"

    def _session_identity(self) -> tuple[str, int]:
        if self.config.status_path.exists():
            try:
                previous = json.loads(
                    self.config.status_path.read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError):
                previous = {}
            if previous.get("runtime_alive") and previous.get("session_id"):
                return (
                    str(previous["session_id"]),
                    int(previous.get("restart_count", 0)) + 1,
                )
        return self.session_id_factory(), 0


def resolve_latest_v5_session(session_root: Path | None) -> Path:
    if session_root is None or not session_root.is_dir():
        raise V5StreamUnavailableError(f"v5 session root does not exist: {session_root}")
    candidates = [
        path for path in session_root.glob("*/session.jsonl")
        if path.parent.name != "latest" and path.is_file()
    ]
    if not candidates:
        direct = session_root / "session.jsonl"
        if direct.is_file():
            return direct.resolve()
        raise V5StreamUnavailableError(
            f"v5 session root contains no session.jsonl: {session_root}"
        )
    return max(
        candidates,
        key=lambda path: (path.stat().st_mtime_ns, path.parent.name),
    ).resolve()


def validate_runtime_preflight(
    config: RepricingRuntimeMVPConfig,
    *,
    power_inspector=inspect_windows_power,
    disk_usage=shutil.disk_usage,
    write_clock: Callable[[], float] = time.perf_counter,
) -> dict[str, Any]:
    protected = ("holdout", "sealed")
    paths = tuple(
        path for path in (
            config.session_path,
            config.session_root,
            config.state_directory,
            config.output_directory,
        ) if path is not None
    )
    if any(token in str(path).casefold() for path in paths for token in protected):
        raise ValueError("runtime paths may not reference sealed holdout locations")
    session_path = (
        resolve_latest_v5_session(config.session_root)
        if config.session_root is not None else config.session_path
    )
    if session_path is None or not session_path.is_file():
        raise V5StreamUnavailableError(
            f"v5 session does not exist: {session_path}"
        )
    first_event = None
    with session_path.open("rb") as handle:
        for raw in handle:
            if raw.endswith(b"\n") and raw.strip():
                first_event = V5JsonlPaperAdapter._decode_event(raw, 0)
                V5JsonlPaperAdapter._validate_event(first_event, 0)
                break
    if first_event is None:
        raise ValueError("v5 session has no complete event")
    maximum_write_latency = 0.0
    for directory in (config.state_directory, config.output_directory):
        directory.mkdir(parents=True, exist_ok=True)
        marker = directory / f".repricing-preflight-{os.getpid()}.tmp"
        started = write_clock()
        marker.write_text("ok", encoding="ascii")
        marker.unlink()
        maximum_write_latency = max(maximum_write_latency, write_clock() - started)
    disk = disk_usage(config.state_directory)
    if disk.free < config.minimum_free_disk_bytes:
        raise ValueError(
            f"free disk space {disk.free} is below required {config.minimum_free_disk_bytes}"
        )
    if maximum_write_latency > config.max_write_latency_seconds:
        raise ValueError(
            "preflight write latency exceeds runtime safety threshold"
        )
    power = power_inspector()
    if config.require_safe_power and not power.safe_for_overnight:
        raise ValueError(
            "Windows power configuration is not safe for overnight runtime"
        )
    with RestartSafePaperCore(config.database_path) as core:
        fingerprint = core.config.fingerprint
        core_state = core.validation_snapshot()
    expected = FrozenPaperConfig().fingerprint
    if fingerprint != expected:
        raise ValueError("paper core frozen strategy fingerprint mismatch")
    return {
        "status": "PASS",
        "configuration_valid": True,
        "directories_writable": True,
        "session_readable": True,
        "session_path": str(session_path.resolve()),
        "session_rotation_enabled": config.session_root is not None,
        "power": power.to_dict(),
        "sleep_inhibitor": "WindowsSleepInhibitor",
        "sleep_inhibitor_required": True,
        "free_disk_bytes": disk.free,
        "minimum_free_disk_bytes": config.minimum_free_disk_bytes,
        "preflight_write_latency_ms": round(maximum_write_latency * 1000.0, 3),
        "max_write_latency_ms": config.max_write_latency_seconds * 1000.0,
        "max_event_staleness_seconds": config.max_event_staleness_seconds,
        "max_events_per_batch": config.max_events_per_batch,
        "max_backlog_bytes": config.max_backlog_bytes,
        "max_processing_stall_seconds": config.max_processing_stall_seconds,
        "heartbeat_interval_seconds": config.heartbeat_interval_seconds,
        "terminal_drain_seconds": config.terminal_drain_seconds,
        "session_completed_required": not config.dry_run,
        "safe_shutdown_path": str(config.safe_shutdown_path.resolve()),
        "detector_state": "FROZEN_CONFIG_VERIFIED",
        "paper_core_state": "RECOVERABLE",
        "strategy_fingerprint": fingerprint,
        "pending_events": core_state["pending_events"],
        "open_positions": core_state["open_positions"],
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repricing-runtime-mvp",
        description="Continuous paper-only repricing runtime MVP",
    )
    parser.add_argument("--config", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = RepricingRuntimeMVPConfig.from_json(args.config)
    status = ContinuousRepricingPaperMVP(config).run()
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
