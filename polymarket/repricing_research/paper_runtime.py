from __future__ import annotations

import argparse
import json
import signal
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .paper_core import RestartSafePaperCore
from .v5_stream_adapter import V5JsonlPaperAdapter, V5StreamValidationError


@dataclass(frozen=True)
class PaperRuntimeConfig:
    session_path: Path
    database_path: Path
    health_path: Path
    poll_interval_seconds: float = 1.0
    max_polls: int | None = None
    max_runtime_seconds: float | None = None
    dry_run: bool = False
    session_id: str = ""

    def __post_init__(self) -> None:
        if self.poll_interval_seconds < 0:
            raise ValueError("poll interval must be non-negative")
        if self.max_polls is not None and self.max_polls < 1:
            raise ValueError("max polls must be at least one")
        if self.max_runtime_seconds is not None and self.max_runtime_seconds <= 0:
            raise ValueError("max runtime must be positive")
        if self.dry_run and self.max_polls is None and self.max_runtime_seconds is None:
            raise ValueError("dry run requires a poll or runtime bound")


@dataclass
class PaperRuntimeHealth:
    session_id: str
    status: str
    runtime_alive: bool
    runtime_start_timestamp: str
    runtime_stop_timestamp: str | None
    last_poll_timestamp: str | None
    last_event_timestamp: str | None
    last_successful_processing_timestamp: str | None
    events_received: int
    events_accepted: int
    events_rejected: int
    duplicate_events_skipped: int
    positions_opened: int
    positions_closed: int
    valid_signals: int
    rejected_signals: int
    recovered_open_positions: int
    current_open_positions: int
    polls_completed: int
    last_error: str | None
    source_path: str
    database_path: str
    strategy_fingerprint: str | None
    detector_state: str
    paper_core_state: str
    dry_run: bool


class ManagedRepricingPaperRuntime:
    """Managed paper-only loop around the v5 adapter and durable core."""

    def __init__(
        self,
        config: PaperRuntimeConfig,
        *,
        now: Callable[[], datetime] | None = None,
        monotonic: Callable[[], float] | None = None,
        health_observer: Callable[[PaperRuntimeHealth], None] | None = None,
    ) -> None:
        self.config = config
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._monotonic = monotonic or time.monotonic
        self._health_observer = health_observer
        self._stop_requested = threading.Event()
        self._health: PaperRuntimeHealth | None = None

    def request_stop(self) -> None:
        self._stop_requested.set()

    @property
    def health(self) -> PaperRuntimeHealth | None:
        return self._health

    def run(self, *, install_signal_handlers: bool = False) -> PaperRuntimeHealth:
        started_at = self._timestamp()
        self._health = PaperRuntimeHealth(
            session_id=self.config.session_id,
            status="STARTING",
            runtime_alive=True,
            runtime_start_timestamp=started_at,
            runtime_stop_timestamp=None,
            last_poll_timestamp=None,
            last_event_timestamp=None,
            last_successful_processing_timestamp=None,
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
            polls_completed=0,
            last_error=None,
            source_path=str(self.config.session_path.resolve()),
            database_path=str(self.config.database_path.resolve()),
            strategy_fingerprint=None,
            detector_state="NOT_INITIALIZED",
            paper_core_state="NOT_INITIALIZED",
            dry_run=self.config.dry_run,
        )
        self._write_health()
        handlers = self._install_signal_handlers() if install_signal_handlers else {}
        core: RestartSafePaperCore | None = None
        started_monotonic = self._monotonic()
        try:
            core = RestartSafePaperCore(self.config.database_path)
            adapter = V5JsonlPaperAdapter(self.config.session_path, core)
            self._health.strategy_fingerprint = core.config.fingerprint
            self._health.detector_state = "FROZEN_CONFIG_VERIFIED"
            self._health.paper_core_state = "READY"
            self._health.recovered_open_positions = len(core.open_positions())
            self._health.current_open_positions = len(core.open_positions())
            self._health.status = "RUNNING"
            self._write_health()

            while not self._stop_requested.is_set():
                if self._limit_reached(started_monotonic):
                    break
                before = core.validation_snapshot()
                self._health.last_poll_timestamp = self._timestamp()
                try:
                    result = adapter.sync()
                except V5StreamValidationError as exc:
                    after = core.validation_snapshot()
                    accepted = self._apply_ledger_delta(before, after)
                    valid_signals = (
                        after["counts"]["signals"] - before["counts"]["signals"]
                    )
                    self._health.events_received += accepted + 1
                    self._health.events_accepted += accepted
                    self._health.events_rejected += 1
                    self._health.valid_signals += valid_signals
                    self._health.rejected_signals += max(
                        0, adapter.last_sync_lag_measurements - valid_signals
                    )
                    self._health.last_event_timestamp = adapter.last_event_timestamp
                    self._health.last_error = f"{type(exc).__name__}: {exc}"
                    self._health.status = "FAILED"
                    self._write_health()
                    raise
                after = core.validation_snapshot()
                accepted = self._apply_ledger_delta(before, after)
                valid_signals = (
                    after["counts"]["signals"] - before["counts"]["signals"]
                )
                self._health.events_received += accepted + result.verified_events
                self._health.events_accepted += accepted
                self._health.duplicate_events_skipped += result.verified_events
                self._health.valid_signals += valid_signals
                self._health.rejected_signals += max(
                    0, result.ingested_lag_measurements - valid_signals
                )
                self._health.last_event_timestamp = result.last_event_timestamp
                self._health.last_successful_processing_timestamp = self._timestamp()
                self._health.polls_completed += 1
                self._write_health()
                if self._limit_reached(started_monotonic):
                    break
                self._stop_requested.wait(self.config.poll_interval_seconds)
        except KeyboardInterrupt:
            self.request_stop()
        except Exception as exc:
            if self._health.status != "FAILED":
                self._health.status = "FAILED"
                self._health.last_error = f"{type(exc).__name__}: {exc}"
                self._write_health()
            raise
        finally:
            if core is not None:
                self._health.current_open_positions = len(core.open_positions())
                core.close()
                self._health.paper_core_state = (
                    "CLOSED_FAILED" if self._health.status == "FAILED"
                    else "CLOSED_RECOVERABLE"
                )
            if self._health.status != "FAILED":
                self._health.status = "STOPPED"
            self._health.runtime_alive = False
            self._health.runtime_stop_timestamp = self._timestamp()
            self._write_health()
            self._restore_signal_handlers(handlers)
        return self._health

    def _apply_ledger_delta(self, before: dict, after: dict) -> int:
        accepted = after["counts"]["raw_events"] - before["counts"]["raw_events"]
        self._health.positions_opened += (
            after["counts"]["positions"] - before["counts"]["positions"]
        )
        self._health.positions_closed += (
            after["counts"]["trades"] - before["counts"]["trades"]
        )
        self._health.current_open_positions = after["open_positions"]
        return accepted

    def _limit_reached(self, started_monotonic: float) -> bool:
        if (
            self.config.max_polls is not None
            and self._health.polls_completed >= self.config.max_polls
        ):
            return True
        return (
            self.config.max_runtime_seconds is not None
            and self._monotonic() - started_monotonic
            >= self.config.max_runtime_seconds
        )

    def _write_health(self) -> None:
        path = self.config.health_path
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(asdict(self._health), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        if self._health_observer is not None:
            self._health_observer(self._health)

    def _timestamp(self) -> str:
        value = self._now()
        if value.tzinfo is None:
            raise ValueError("runtime clock must be timezone-aware")
        return value.isoformat()

    def _install_signal_handlers(self) -> dict[int, object]:
        if threading.current_thread() is not threading.main_thread():
            return {}
        previous = {}

        def handle_stop(_signum, _frame) -> None:
            self.request_stop()

        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.getsignal(signum)
            signal.signal(signum, handle_stop)
        return previous

    @staticmethod
    def _restore_signal_handlers(previous: dict[int, object]) -> None:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repricing-paper-runtime",
        description="Managed paper-only runtime for frozen repricing events",
    )
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--health", type=Path, required=True)
    parser.add_argument("--poll-interval", type=float, default=1.0)
    parser.add_argument("--max-polls", type=int)
    parser.add_argument("--max-runtime-seconds", type=float)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--session-id", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = PaperRuntimeConfig(
        session_path=args.session,
        database_path=args.database,
        health_path=args.health,
        poll_interval_seconds=args.poll_interval,
        max_polls=args.max_polls,
        max_runtime_seconds=args.max_runtime_seconds,
        dry_run=args.dry_run,
        session_id=args.session_id,
    )
    health = ManagedRepricingPaperRuntime(config).run(install_signal_handlers=True)
    print(json.dumps(asdict(health), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
