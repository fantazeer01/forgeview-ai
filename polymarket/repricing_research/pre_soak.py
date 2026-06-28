from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from .paper_core import InjectedFailure, RestartSafePaperCore
from .paper_runtime import ManagedRepricingPaperRuntime, PaperRuntimeConfig
from .runtime_mvp import (
    RepricingRuntimeMVPConfig,
    resolve_latest_v5_session,
    validate_runtime_preflight,
)


def run_pre_soak_verification(
    config: RepricingRuntimeMVPConfig,
    output_directory: Path,
    *,
    power_inspector=None,
    disk_usage=None,
    now: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    now = now or (lambda: datetime.now(UTC))
    preflight_kwargs = {}
    if power_inspector is not None:
        preflight_kwargs["power_inspector"] = power_inspector
    if disk_usage is not None:
        preflight_kwargs["disk_usage"] = disk_usage
    preflight = validate_runtime_preflight(config, **preflight_kwargs)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        restart_drills = run_open_position_restart_drills(root / "restart", now)
        rotation = run_session_rotation_drill(root / "rotation", now)
        stale_guard = run_stale_event_guard_drill(root / "stale")
        write_guard = run_write_latency_guard_drill(root / "write", now)
    gates = {
        "power_safe": bool(preflight["power"]["safe_for_overnight"]),
        "disk_reserve_pass": (
            preflight["free_disk_bytes"] >= preflight["minimum_free_disk_bytes"]
        ),
        "preflight_write_latency_pass": (
            preflight["preflight_write_latency_ms"]
            <= preflight["max_write_latency_ms"]
        ),
        "session_rotation_pass": rotation["passed"],
        "stale_event_guard_pass": stale_guard["passed"],
        "write_latency_guard_pass": write_guard["passed"],
        "restart_with_open_position_pass": restart_drills[
            "restart_with_open_position"
        ],
        "restart_during_processing_pass": restart_drills[
            "restart_during_processing"
        ],
        "restart_after_graceful_shutdown_pass": restart_drills[
            "restart_after_graceful_shutdown"
        ],
    }
    blockers = [name for name, passed in gates.items() if not passed]
    verdict = "READY_FOR_24H_SOAK" if not blockers else "NOT_READY"
    result = {
        "verdict": verdict,
        "verified_at_utc": now().isoformat(),
        "preflight": preflight,
        "gates": gates,
        "restart_drills": restart_drills,
        "session_rotation": rotation,
        "stale_event_guard": stale_guard,
        "write_latency_guard": write_guard,
        "remaining_blockers": blockers,
        "soak_launched": False,
        "live_trading_enabled": False,
        "holdout_accessed": False,
    }
    _write_artifacts(output_directory, result)
    return result


def run_open_position_restart_drills(
    root: Path, now: Callable[[], datetime]
) -> dict[str, bool]:
    root.mkdir(parents=True, exist_ok=True)
    events = _events()

    session_one = root / "open.jsonl"
    _write_events(session_one, events[:2])
    database_one = root / "open.sqlite3"
    _run_once(session_one, database_one, root / "open-health.json", now)
    with RestartSafePaperCore(database_one) as core:
        first_open = len(core.open_positions()) == 1
    recovered = _run_once(
        session_one, database_one, root / "open-health-2.json", now
    )
    with RestartSafePaperCore(database_one) as core:
        restart_open = (
            first_open
            and recovered.recovered_open_positions == 1
            and len(core.positions()) == 1
            and len(core.open_positions()) == 1
        )

    database_two = root / "processing.sqlite3"
    core = RestartSafePaperCore(database_two)
    core.ingest_event("processing", 0, events[0])
    interrupted = False
    try:
        core.ingest_event("processing", 1, events[1], fail_at="after_position_open")
    except InjectedFailure:
        interrupted = True
    finally:
        core.close()
    with RestartSafePaperCore(database_two) as recovered_core:
        restart_processing = (
            interrupted
            and len(recovered_core.positions()) == 1
            and len(recovered_core.open_positions()) == 1
            and recovered_core.validation_snapshot()["pending_events"] == 0
        )

    session_three = root / "graceful.jsonl"
    _write_events(session_three, events[:2])
    database_three = root / "graceful.sqlite3"
    first = _run_once(
        session_three, database_three, root / "graceful-health.json", now
    )
    _append_events(session_three, events[2:])
    second = _run_once(
        session_three, database_three, root / "graceful-health-2.json", now
    )
    with RestartSafePaperCore(database_three) as core:
        restart_graceful = (
            first.status == "STOPPED"
            and first.current_open_positions == 1
            and second.recovered_open_positions == 1
            and len(core.trades()) == 1
            and len(core.open_positions()) == 0
        )

    return {
        "restart_with_open_position": restart_open,
        "restart_during_processing": restart_processing,
        "restart_after_graceful_shutdown": restart_graceful,
    }


def run_session_rotation_drill(
    root: Path, now: Callable[[], datetime]
) -> dict[str, Any]:
    sessions = root / "sessions"
    first = sessions / "20260628_170000" / "session.jsonl"
    second = sessions / "20260628_170030" / "session.jsonl"
    first.parent.mkdir(parents=True, exist_ok=True)
    _write_events(first, _events()[:2])
    calls = 0

    def resolver() -> Path:
        nonlocal calls
        calls += 1
        if calls == 2:
            second.parent.mkdir(parents=True, exist_ok=True)
            _write_events(second, _events()[2:])
        return resolve_latest_v5_session(sessions)

    runtime = ManagedRepricingPaperRuntime(
        PaperRuntimeConfig(
            session_path=first,
            database_path=root / "rotation.sqlite3",
            health_path=root / "rotation-health.json",
            poll_interval_seconds=0,
            max_polls=2,
            dry_run=True,
        ),
        now=now,
        monotonic=lambda: 0.0,
        write_clock=lambda: 0.0,
        session_resolver=resolver,
    )
    health = runtime.run()
    with RestartSafePaperCore(root / "rotation.sqlite3") as core:
        passed = (
            health.session_rotation_count == 1
            and len(core.positions()) == 1
            and len(core.trades()) == 1
            and len(core.open_positions()) == 0
        )
    return {
        "passed": passed,
        "rotation_count": health.session_rotation_count,
        "selected_session_name": Path(health.source_path).parent.name,
    }


def run_stale_event_guard_drill(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    session = root / "stale.jsonl"
    _write_events(session, _events())
    current = datetime(2026, 6, 28, 18, 0, 0, tzinfo=UTC)
    runtime = ManagedRepricingPaperRuntime(
        PaperRuntimeConfig(
            session_path=session,
            database_path=root / "stale.sqlite3",
            health_path=root / "stale-health.json",
            poll_interval_seconds=0,
            max_polls=1,
            max_event_staleness_seconds=30,
        ),
        now=lambda: current,
        monotonic=lambda: 0.0,
        write_clock=lambda: 0.0,
    )
    failed = False
    try:
        runtime.run()
    except RuntimeError:
        failed = True
    return {
        "passed": failed and bool(runtime.health.stale_event_detected),
        "failed_closed": failed,
        "stale_event_detected": runtime.health.stale_event_detected,
    }


def run_write_latency_guard_drill(
    root: Path, now: Callable[[], datetime]
) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    session = root / "write.jsonl"
    _write_events(session, _events())
    ticks = iter(range(20))
    runtime = ManagedRepricingPaperRuntime(
        PaperRuntimeConfig(
            session_path=session,
            database_path=root / "write.sqlite3",
            health_path=root / "write-health.json",
            poll_interval_seconds=0,
            max_polls=1,
            dry_run=True,
            max_write_latency_seconds=0.5,
        ),
        now=now,
        monotonic=lambda: 0.0,
        write_clock=lambda: float(next(ticks)),
    )
    failed = False
    try:
        runtime.run()
    except RuntimeError:
        failed = True
    return {
        "passed": failed and runtime.health.status == "FAILED",
        "failed_closed": failed,
        "last_error": runtime.health.last_error,
    }


def _run_once(
    session: Path,
    database: Path,
    health: Path,
    now: Callable[[], datetime],
):
    return ManagedRepricingPaperRuntime(
        PaperRuntimeConfig(
            session_path=session,
            database_path=database,
            health_path=health,
            poll_interval_seconds=0,
            max_polls=1,
            dry_run=True,
        ),
        now=now,
        monotonic=lambda: 0.0,
        write_clock=lambda: 0.0,
    ).run()


def _events() -> list[dict[str, Any]]:
    return [
        _snapshot("2026-06-28T17:00:00+00:00", 0.50, 240),
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
        _snapshot("2026-06-28T17:00:30+00:00", 0.54, 210),
    ]


def _snapshot(timestamp: str, yes_price: float, expiry: float) -> dict[str, Any]:
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


def _write_events(path: Path, events: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )


def _append_events(path: Path, events: list[dict[str, Any]]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, sort_keys=True) + "\n")


def _write_artifacts(output: Path, result: dict[str, Any]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "repricing_pre_soak_validation.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    readiness = {
        "verdict": result["verdict"],
        "gates": result["gates"],
        "remaining_blockers": result["remaining_blockers"],
        "soak_launched": False,
    }
    (output / "repricing_runtime_readiness.json").write_text(
        json.dumps(readiness, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Repricing Pre-Soak Consolidation v1",
        "",
        f"Verdict: `{result['verdict']}`",
        "",
        "## Gates",
        "",
    ]
    lines.extend(
        f"- {name}: {'PASS' if passed else 'FAIL'}"
        for name, passed in result["gates"].items()
    )
    lines.extend(["", "## Remaining Blockers", ""])
    if result["remaining_blockers"]:
        lines.extend(f"- {item}" for item in result["remaining_blockers"])
    else:
        lines.append("- None before an explicitly authorized 24-hour soak.")
    lines.extend([
        "",
        "No soak was launched. Detector logic, thresholds, strategy, holdout,",
        "and live-trading boundaries remain unchanged.",
    ])
    (output / "repricing_pre_soak_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
