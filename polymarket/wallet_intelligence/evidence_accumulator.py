"""Autonomous, bounded H2/H3 wallet evidence accumulation."""

from __future__ import annotations

import csv
import json
import math
import os
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from .client import PolymarketPublicClient
from .first_seen_prospective import (
    DEFAULT_DURATION_SECONDS,
    DEFAULT_MAX_REQUESTS,
    DEFAULT_PAGE_LIMIT,
    DEFAULT_POLL_INTERVAL_SECONDS,
    DEFAULT_PROSPECTIVE_DB,
    DEFAULT_PROSPECTIVE_OUTPUT,
    ProspectiveFirstSeenStore,
    run_prospective_observer,
)
from .market_outcome import PublicMarketMetadataClient


DEFAULT_ACCUMULATOR_DB = Path(
    "polymarket/data/wallet_intelligence/first_seen_prospective_v1/accumulator.sqlite3"
)
DEFAULT_ACCUMULATOR_OUTPUT = Path(
    "polymarket/models/wallet_intelligence_v1/autonomous_evidence_accumulator_v1"
)
DEFAULT_SEED_DECISION_WINDOWS = Path(
    "polymarket/models/wallet_intelligence_v1/decision_window_v1/wallet_decision_window.csv"
)
DEFAULT_SEED_FIRST_SEEN_SUMMARY = Path(
    "polymarket/models/wallet_intelligence_v1/first_seen_detection_v1/wallet_first_seen_summary.json"
)

MAX_SESSIONS = 60
MIN_ELIGIBLE_TRADES = 100
MIN_WALLETS = 3
MIN_TRADES_PER_WALLET = 10
MAX_WALLET_SHARE = 0.60
MIN_SESSIONS = 10
MIN_DATES = 5
MIN_ASSETS = 2
MIN_TRADES_PER_ASSET = 20
MIN_COMPLETENESS = 0.95
H2_MAX_DELAY_SECONDS = 30.0
H3_MIN_WINDOW_SECONDS = 60.0


ACCUMULATOR_SCHEMA = """
CREATE TABLE IF NOT EXISTS accumulator_control (
    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
    status TEXT NOT NULL,
    process_id INTEGER NOT NULL DEFAULT 0,
    stop_reason TEXT NOT NULL DEFAULT '',
    updated_at_utc TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS accumulator_sessions (
    session_number INTEGER PRIMARY KEY,
    status TEXT NOT NULL CHECK(status IN ('active', 'complete', 'failed')),
    observer_run_id TEXT NOT NULL DEFAULT '',
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT NOT NULL DEFAULT '',
    eligible_trades_after INTEGER NOT NULL DEFAULT 0,
    action_after TEXT NOT NULL DEFAULT 'CONTINUE',
    error TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS expiry_cache (
    market_slug TEXT PRIMARY KEY,
    condition_id TEXT NOT NULL,
    expiry_timestamp_utc TEXT NOT NULL,
    source TEXT NOT NULL,
    fetched_at_utc TEXT NOT NULL
);
"""


class EvidenceAccumulatorStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.connection = sqlite3.connect(path, timeout=30)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        self.connection.executescript(ACCUMULATOR_SCHEMA)
        with self.connection:
            self.connection.execute(
                """INSERT OR IGNORE INTO accumulator_control
                (singleton, status) VALUES (1, 'ready')"""
            )

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "EvidenceAccumulatorStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def reserve_session(self, started_at_utc: str) -> dict[str, Any]:
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            active = self.connection.execute(
                "SELECT * FROM accumulator_sessions WHERE status='active' ORDER BY session_number LIMIT 1"
            ).fetchone()
            if active is not None:
                self.connection.commit()
                return dict(active)
            next_number = int(
                self.connection.execute(
                    "SELECT COALESCE(MAX(session_number), 1) + 1 FROM accumulator_sessions"
                ).fetchone()[0]
            )
            if next_number > MAX_SESSIONS:
                raise RuntimeError("60-session evidence budget is exhausted")
            self.connection.execute(
                """INSERT INTO accumulator_sessions
                (session_number, status, started_at_utc) VALUES (?, 'active', ?)""",
                (next_number, started_at_utc),
            )
            self._set_control("running", "", started_at_utc, os.getpid())
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        return dict(
            self.connection.execute(
                "SELECT * FROM accumulator_sessions WHERE session_number=?", (next_number,)
            ).fetchone()
        )

    def complete_session(
        self,
        session_number: int,
        *,
        completed_at_utc: str,
        observer_run_id: str,
        eligible_trades: int,
        action: str,
    ) -> None:
        with self.connection:
            self.connection.execute(
                """UPDATE accumulator_sessions SET status='complete', observer_run_id=?,
                completed_at_utc=?, eligible_trades_after=?, action_after=?, error=''
                WHERE session_number=?""",
                (observer_run_id, completed_at_utc, eligible_trades, action, session_number),
            )
            status = "stopped" if action != "CONTINUE" else "ready"
            self._set_control(status, _stop_reason(action), completed_at_utc, 0)

    def fail_session(self, session_number: int, error: str, failed_at_utc: str) -> None:
        with self.connection:
            self.connection.execute(
                """UPDATE accumulator_sessions SET status='active', error=?
                WHERE session_number=?""",
                (error, session_number),
            )
            self._set_control("failed", "session_error", failed_at_utc, 0)

    def apply_decision(self, session_number: int, action: str, stop_reason: str, updated_at_utc: str) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE accumulator_sessions SET action_after=? WHERE session_number=?",
                (action, session_number),
            )
            status = "stopped" if action != "CONTINUE" else "ready"
            self._set_control(status, stop_reason, updated_at_utc, 0)

    def set_background_process(self, pid: int, started_at_utc: str) -> None:
        with self.connection:
            self._set_control("background_running", "", started_at_utc, pid)

    def control(self) -> dict[str, Any]:
        return dict(self.connection.execute("SELECT * FROM accumulator_control WHERE singleton=1").fetchone())

    def sessions(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute("SELECT * FROM accumulator_sessions ORDER BY session_number")]

    def completed_session_count(self) -> int:
        # Session 1 is the committed five-minute feasibility experiment.
        return 1 + int(
            self.connection.execute(
                "SELECT COUNT(*) FROM accumulator_sessions WHERE status='complete'"
            ).fetchone()[0]
        )

    def cache_expiry(
        self, market_slug: str, condition_id: str, expiry: str, source: str, fetched_at_utc: str
    ) -> None:
        with self.connection:
            self.connection.execute(
                """INSERT INTO expiry_cache VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(market_slug) DO UPDATE SET
                condition_id=excluded.condition_id,
                expiry_timestamp_utc=excluded.expiry_timestamp_utc,
                source=excluded.source,
                fetched_at_utc=excluded.fetched_at_utc""",
                (market_slug, condition_id.lower(), expiry, source, fetched_at_utc),
            )

    def expiry_cache(self) -> dict[str, dict[str, str]]:
        return {row["market_slug"]: dict(row) for row in self.connection.execute("SELECT * FROM expiry_cache")}

    def _set_control(self, status: str, stop_reason: str, updated_at: str, pid: int) -> None:
        self.connection.execute(
            """UPDATE accumulator_control SET status=?, process_id=?, stop_reason=?,
            updated_at_utc=? WHERE singleton=1""",
            (status, pid, stop_reason, updated_at),
        )


def prepare_accumulator_progress(
    *,
    accumulator_db: Path = DEFAULT_ACCUMULATOR_DB,
    observer_db: Path = DEFAULT_PROSPECTIVE_DB,
    output_dir: Path = DEFAULT_ACCUMULATOR_OUTPUT,
    seed_decision_windows: Path = DEFAULT_SEED_DECISION_WINDOWS,
    seed_first_seen_summary: Path = DEFAULT_SEED_FIRST_SEEN_SUMMARY,
) -> dict[str, Any]:
    with EvidenceAccumulatorStore(accumulator_db) as state:
        with ProspectiveFirstSeenStore(observer_db) as observer:
            observer_rows = observer.export_rows()
            observer_counts = observer.counts()
            request_counts = _observer_request_counts(observer)
            observer_run_configs = _observer_run_configs(observer)
        evidence = build_accumulated_evidence(
            _read_csv(seed_decision_windows), observer_rows, state.expiry_cache()
        )
        progress = evaluate_h2_h3_gates(
            evidence,
            session_count=state.completed_session_count(),
            request_counts=_seed_and_observer_requests(seed_first_seen_summary, request_counts),
        )
        session_records = state.sessions()
        for session in session_records:
            session["observer_runtime"] = observer_run_configs.get(session["observer_run_id"], {})
        last_runtime = next(
            (
                session["observer_runtime"]
                for session in reversed(session_records)
                if session["status"] == "complete" and session["observer_runtime"]
            ),
            {},
        )
        progress.update(
            {
                "task": "Wallet Autonomous Evidence Accumulator v1",
                "automation_status": state.control()["status"],
                "process_id": state.control()["process_id"],
                "persistent_state": {
                    "accumulator_database": str(accumulator_db),
                    "observer_database": str(observer_db),
                    "observer_counts": observer_counts,
                    "session_records": session_records,
                },
                "last_completed_session_runtime": last_runtime,
                "frozen_runtime": {
                    "poll_interval_seconds": DEFAULT_POLL_INTERVAL_SECONDS,
                    "session_duration_seconds": DEFAULT_DURATION_SECONDS,
                    "page_limit": DEFAULT_PAGE_LIMIT,
                    "max_requests_per_session": DEFAULT_MAX_REQUESTS,
                    "maximum_sessions": MAX_SESSIONS,
                },
                "decision_contract": _decision_contract(),
            }
        )
    write_progress_artifacts(progress, output_dir)
    return progress


def run_autonomous_accumulator(
    *,
    activity_client: PolymarketPublicClient,
    metadata_client: PublicMarketMetadataClient,
    accumulator_db: Path = DEFAULT_ACCUMULATOR_DB,
    observer_db: Path = DEFAULT_PROSPECTIVE_DB,
    observer_output: Path = DEFAULT_PROSPECTIVE_OUTPUT,
    output_dir: Path = DEFAULT_ACCUMULATOR_OUTPUT,
    seed_decision_windows: Path = DEFAULT_SEED_DECISION_WINDOWS,
    seed_first_seen_summary: Path = DEFAULT_SEED_FIRST_SEEN_SUMMARY,
    session_runner: Callable[..., dict[str, Any]] = run_prospective_observer,
    now: Callable[[], datetime] | None = None,
    session_limit: int | None = None,
    session_duration_seconds: float = DEFAULT_DURATION_SECONDS,
) -> dict[str, Any]:
    if session_limit is not None and session_limit < 1:
        raise ValueError("session_limit must be positive when provided")
    if not 0 < session_duration_seconds <= DEFAULT_DURATION_SECONDS:
        raise ValueError("session_duration_seconds exceeds the bounded maximum")
    now = now or (lambda: datetime.now(UTC))
    max_requests = min(
        DEFAULT_MAX_REQUESTS,
        math.ceil(session_duration_seconds / DEFAULT_POLL_INTERVAL_SECONDS) * 4,
    )
    sessions_this_launch = 0
    progress = prepare_accumulator_progress(
        accumulator_db=accumulator_db,
        observer_db=observer_db,
        output_dir=output_dir,
        seed_decision_windows=seed_decision_windows,
        seed_first_seen_summary=seed_first_seen_summary,
    )
    while (
        progress["action"] == "CONTINUE"
        and progress["sessions"]["completed"] < MAX_SESSIONS
        and (session_limit is None or sessions_this_launch < session_limit)
    ):
        started = _iso(now())
        with EvidenceAccumulatorStore(accumulator_db) as state:
            session = state.reserve_session(started)
        number = int(session["session_number"])
        try:
            session_runner(
                client=activity_client,
                db_path=observer_db,
                output_dir=observer_output,
                duration_seconds=session_duration_seconds,
                poll_interval_seconds=DEFAULT_POLL_INTERVAL_SECONDS,
                page_limit=DEFAULT_PAGE_LIMIT,
                max_requests=max_requests,
            )
            with EvidenceAccumulatorStore(accumulator_db) as state:
                with ProspectiveFirstSeenStore(observer_db) as observer:
                    observer_rows = observer.export_rows()
                    run_id = _latest_observer_run_id(observer)
                refresh_expiry_cache(observer_rows, state, metadata_client, _iso(now()))
            progress = prepare_accumulator_progress(
                accumulator_db=accumulator_db,
                observer_db=observer_db,
                output_dir=output_dir,
                seed_decision_windows=seed_decision_windows,
                seed_first_seen_summary=seed_first_seen_summary,
            )
            sessions_this_launch += 1
            with EvidenceAccumulatorStore(accumulator_db) as state:
                state.complete_session(
                    number,
                    completed_at_utc=_iso(now()),
                    observer_run_id=run_id,
                    eligible_trades=progress["evidence"]["eligible_trades"],
                    action=progress["action"],
                )
            progress = prepare_accumulator_progress(
                accumulator_db=accumulator_db,
                observer_db=observer_db,
                output_dir=output_dir,
                seed_decision_windows=seed_decision_windows,
                seed_first_seen_summary=seed_first_seen_summary,
            )
            with EvidenceAccumulatorStore(accumulator_db) as state:
                state.apply_decision(number, progress["action"], progress["stop_reason"], _iso(now()))
            progress = prepare_accumulator_progress(
                accumulator_db=accumulator_db,
                observer_db=observer_db,
                output_dir=output_dir,
                seed_decision_windows=seed_decision_windows,
                seed_first_seen_summary=seed_first_seen_summary,
            )
        except Exception as exc:
            with EvidenceAccumulatorStore(accumulator_db) as state:
                state.fail_session(number, f"{type(exc).__name__}: {exc}", _iso(now()))
            prepare_accumulator_progress(
                accumulator_db=accumulator_db,
                observer_db=observer_db,
                output_dir=output_dir,
                seed_decision_windows=seed_decision_windows,
                seed_first_seen_summary=seed_first_seen_summary,
            )
            raise
    return progress


def launch_accumulator_background(
    *,
    accumulator_db: Path = DEFAULT_ACCUMULATOR_DB,
    observer_db: Path = DEFAULT_PROSPECTIVE_DB,
    observer_output: Path = DEFAULT_PROSPECTIVE_OUTPUT,
    output_dir: Path = DEFAULT_ACCUMULATOR_OUTPUT,
    session_limit: int | None = None,
    session_duration_seconds: float = DEFAULT_DURATION_SECONDS,
) -> dict[str, Any]:
    progress = prepare_accumulator_progress(
        accumulator_db=accumulator_db, observer_db=observer_db, output_dir=output_dir
    )
    if progress["action"] != "CONTINUE":
        return {"started": False, "reason": progress["stop_reason"], "progress": progress}
    with EvidenceAccumulatorStore(accumulator_db) as state:
        current = state.control()
        if int(current["process_id"]) and _pid_running(int(current["process_id"])):
            return {"started": False, "reason": "already_running", "process_id": current["process_id"]}
    output_dir.mkdir(parents=True, exist_ok=True)
    command = background_command(
        accumulator_db,
        observer_db,
        observer_output,
        output_dir,
        session_limit=session_limit,
        session_duration_seconds=session_duration_seconds,
    )
    stdout = (output_dir / "accumulator_stdout.log").open("ab")
    stderr = (output_dir / "accumulator_stderr.log").open("ab")
    kwargs: dict[str, Any] = {"stdin": subprocess.DEVNULL, "stdout": stdout, "stderr": stderr}
    if os.name == "nt":
        kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
        )
    else:
        kwargs["start_new_session"] = True
    process = subprocess.Popen(command, **kwargs)
    stdout.close()
    stderr.close()
    started = _iso(datetime.now(UTC))
    with EvidenceAccumulatorStore(accumulator_db) as state:
        state.set_background_process(process.pid, started)
    return {"started": True, "process_id": process.pid, "command": command}


def background_command(
    accumulator_db: Path,
    observer_db: Path,
    observer_output: Path,
    output_dir: Path,
    *,
    session_limit: int | None = None,
    session_duration_seconds: float = DEFAULT_DURATION_SECONDS,
) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "polymarket.wallet_intelligence",
        "wallet-evidence-accumulator",
        "run",
        "--accumulator-database",
        str(accumulator_db),
        "--observer-database",
        str(observer_db),
        "--observer-output",
        str(observer_output),
        "--output",
        str(output_dir),
        "--session-duration",
        str(session_duration_seconds),
    ]
    if session_limit is not None:
        command.extend(["--session-limit", str(session_limit)])
    return command


def build_accumulated_evidence(
    seed_rows: list[dict[str, str]],
    observer_rows: list[dict[str, str]],
    expiry_cache: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    evidence: dict[str, dict[str, Any]] = {}
    for row in seed_rows:
        identity = row.get("trade_identity", "")
        first_seen = _parse_datetime(row.get("first_seen_timestamp_utc", ""))
        trade_time = _parse_datetime(row.get("trade_datetime_utc", ""))
        expiry = _parse_datetime(row.get("expiry_timestamp_utc", ""))
        evidence[identity] = _evidence_row(row, first_seen, trade_time, expiry, True)
    for row in observer_rows:
        slug = row.get("market_slug", "")
        if not _is_target_market(row):
            continue
        cached = expiry_cache.get(slug, {})
        expiry = None
        if cached and cached.get("condition_id", "").lower() == row.get("condition_id", "").lower():
            expiry = _parse_datetime(cached.get("expiry_timestamp_utc", ""))
        identity = row.get("trade_identity", "")
        if identity in evidence:
            continue
        evidence[identity] = _evidence_row(
            row,
            _parse_datetime(row.get("first_seen_timestamp_utc", "")),
            _parse_datetime(row.get("trade_datetime_utc", "")),
            expiry,
            bool(expiry),
        )
    return [evidence[key] for key in sorted(evidence, key=lambda key: (evidence[key]["first_seen"], key))]


def refresh_expiry_cache(
    observer_rows: list[dict[str, str]],
    state: EvidenceAccumulatorStore,
    metadata_client: PublicMarketMetadataClient,
    fetched_at_utc: str,
) -> None:
    cached = state.expiry_cache()
    exemplars = {row.get("market_slug", ""): row for row in observer_rows if _is_target_market(row)}
    for slug in sorted(exemplars):
        row = exemplars[slug]
        if slug in cached and cached[slug]["condition_id"] == row.get("condition_id", "").lower():
            continue
        market = metadata_client.get_market_by_slug(slug)
        if not isinstance(market, dict):
            continue
        condition = str(market.get("conditionId") or market.get("condition_id") or "").lower()
        expiry = _parse_datetime(str(market.get("endDate") or ""))
        if condition != row.get("condition_id", "").lower() or expiry is None:
            continue
        state.cache_expiry(slug, condition, _iso(expiry), "gamma_markets_slug", fetched_at_utc)


def evaluate_h2_h3_gates(
    evidence: list[dict[str, Any]], *, session_count: int, request_counts: dict[str, int]
) -> dict[str, Any]:
    total = len(evidence)
    h2_rows = [row for row in evidence if row["delay_seconds"] is not None]
    h3_rows = [row for row in evidence if row["window_seconds"] is not None]
    h2_successes = sum(float(row["delay_seconds"]) <= H2_MAX_DELAY_SECONDS for row in h2_rows)
    h3_successes = sum(float(row["window_seconds"]) >= H3_MIN_WINDOW_SECONDS for row in h3_rows)
    wallet_counts = Counter(row["wallet_id"] for row in evidence)
    asset_counts = Counter(row["asset_class"] for row in evidence)
    dates = {row["first_seen"][:10] for row in evidence if row["first_seen"]}
    identities = [row["trade_identity"] for row in evidence]
    request_total = request_counts["successful"] + request_counts["failed"]
    request_rate = request_counts["successful"] / request_total if request_total else 0.0
    completeness = {
        "trade_and_first_seen_timestamps": len(h2_rows) / total if total else 0.0,
        "gamma_expiry": len(h3_rows) / total if total else 0.0,
        "stable_identity_uniqueness": len(set(identities)) / total if total else 0.0,
        "public_request_success_rate": request_rate,
    }
    diversity = {
        "wallets": len(wallet_counts),
        "wallet_trade_counts": dict(sorted(wallet_counts.items())),
        "largest_wallet_share": max(wallet_counts.values()) / total if total else 0.0,
        "assets": len(asset_counts),
        "asset_trade_counts": dict(sorted(asset_counts.items())),
        "dates": len(dates),
        "utc_dates": sorted(dates),
    }
    gates = {
        "eligible_trades": total >= MIN_ELIGIBLE_TRADES,
        "wallet_count": len(wallet_counts) >= MIN_WALLETS,
        "trades_per_wallet": len(wallet_counts) >= MIN_WALLETS
        and all(count >= MIN_TRADES_PER_WALLET for count in wallet_counts.values()),
        "wallet_concentration": total > 0 and max(wallet_counts.values()) / total <= MAX_WALLET_SHARE,
        "sessions": session_count >= MIN_SESSIONS,
        "dates": len(dates) >= MIN_DATES,
        "asset_count": len(asset_counts) >= MIN_ASSETS,
        "trades_per_asset": len(asset_counts) >= MIN_ASSETS
        and all(count >= MIN_TRADES_PER_ASSET for count in asset_counts.values()),
        "timestamp_completeness": completeness["trade_and_first_seen_timestamps"] >= MIN_COMPLETENESS,
        "expiry_completeness": completeness["gamma_expiry"] >= MIN_COMPLETENESS,
        "identity_uniqueness": completeness["stable_identity_uniqueness"] == 1.0,
        "request_completeness": request_rate >= MIN_COMPLETENESS,
    }
    minimum_evidence_passed = all(gates.values())
    h2 = _hypothesis_status(
        h2_successes, len(h2_rows), minimum_evidence_passed,
        support_point=0.80, support_lower=0.70, reject_point=0.50, reject_upper=0.60,
    )
    h3 = _hypothesis_status(
        h3_successes, len(h3_rows), minimum_evidence_passed,
        support_point=0.70, support_lower=0.60, reject_point=0.30, reject_upper=0.40,
    )
    if h2["conclusion"] == "REJECTED" or h3["conclusion"] == "REJECTED":
        action = "FREEZE"
        stop_reason = "REJECT_REACHED"
    elif h2["conclusion"] == "SUPPORTED" and h3["conclusion"] == "SUPPORTED":
        action = "GRADUATE_TO_ENGINEERING"
        stop_reason = "SUPPORT_REACHED"
    elif session_count >= MAX_SESSIONS:
        action = "FREEZE"
        stop_reason = "SESSION_BUDGET_EXHAUSTED"
    else:
        action = "CONTINUE"
        stop_reason = ""
    return {
        "action": action,
        "stop_reason": stop_reason,
        "evidence": {
            "eligible_trades": total,
            "h2_measurable_trades": len(h2_rows),
            "h3_measurable_trades": len(h3_rows),
            "diversity": diversity,
            "completeness": completeness,
            "request_counts": request_counts,
        },
        "sessions": {
            "completed": session_count,
            "maximum": MAX_SESSIONS,
            "remaining": max(0, MAX_SESSIONS - session_count),
        },
        "minimum_evidence": {"passed": minimum_evidence_passed, "gates": gates},
        "h2": h2,
        "h3": h3,
        "remaining": {
            "eligible_trades": max(0, MIN_ELIGIBLE_TRADES - total),
            "wallets": max(0, MIN_WALLETS - len(wallet_counts)),
            "sessions": max(0, MIN_SESSIONS - session_count),
            "dates": max(0, MIN_DATES - len(dates)),
        },
    }


def write_progress_artifacts(progress: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    gate_status = {
        "action": progress["action"],
        "stop_reason": progress["stop_reason"],
        "h2": progress["h2"],
        "h3": progress["h3"],
        "minimum_evidence": progress["minimum_evidence"],
        "decision_contract": progress["decision_contract"],
        "automatic_stop": {
            "support_reached": progress["stop_reason"] == "SUPPORT_REACHED",
            "reject_reached": progress["stop_reason"] == "REJECT_REACHED",
            "session_budget_exhausted": progress["stop_reason"] == "SESSION_BUDGET_EXHAUSTED",
        },
    }
    _atomic_write(output_dir / "wallet_progress.json", json.dumps(progress, indent=2, sort_keys=True) + "\n")
    _atomic_write(output_dir / "wallet_gate_status.json", json.dumps(gate_status, indent=2, sort_keys=True) + "\n")
    _atomic_write(output_dir / "wallet_progress_report.md", render_progress_report(progress))


def render_progress_report(progress: dict[str, Any]) -> str:
    evidence = progress["evidence"]
    return "\n".join(
        [
            "# Wallet Autonomous Evidence Accumulator v1",
            "",
            "This is public, read-only research automation. It is not trading or a profitability claim.",
            "",
            "## Automation",
            "",
            f"- Status: `{progress.get('automation_status', 'unknown')}`",
            f"- Program action: `{progress['action']}`",
            f"- Stop reason: `{progress['stop_reason'] or 'none'}`",
            f"- Completed sessions: {progress['sessions']['completed']} / {progress['sessions']['maximum']}",
            f"- Remaining session budget: {progress['sessions']['remaining']}",
            "",
            "## Evidence",
            "",
            f"- Eligible trades: {evidence['eligible_trades']} / {MIN_ELIGIBLE_TRADES}",
            f"- Wallets: {evidence['diversity']['wallets']} / {MIN_WALLETS}",
            f"- UTC dates: {evidence['diversity']['dates']} / {MIN_DATES}",
            f"- Assets: {evidence['diversity']['assets']} / {MIN_ASSETS}",
            f"- H2: {progress['h2']['successes']} / {progress['h2']['trials']}, `{progress['h2']['conclusion']}`",
            f"- H3: {progress['h3']['successes']} / {progress['h3']['trials']}, `{progress['h3']['conclusion']}`",
            "",
            "## Automatic Stop",
            "",
            "The process stops when both hypotheses reach support, either reaches rejection, or session 60 completes.",
            "Progress artifacts are replaced atomically after every completed session.",
        ]
    ) + "\n"


def _hypothesis_status(
    successes: int,
    trials: int,
    evidence_ready: bool,
    *,
    support_point: float,
    support_lower: float,
    reject_point: float,
    reject_upper: float,
) -> dict[str, Any]:
    point = successes / trials if trials else 0.0
    lower, upper = _wilson(successes, trials)
    conclusion = "INCONCLUSIVE"
    if evidence_ready and point >= support_point and lower >= support_lower:
        conclusion = "SUPPORTED"
    elif evidence_ready and point <= reject_point and upper <= reject_upper:
        conclusion = "REJECTED"
    return {
        "successes": successes,
        "trials": trials,
        "point_estimate": point,
        "wilson_95": {"lower": lower, "upper": upper},
        "conclusion": conclusion,
    }


def _decision_contract() -> dict[str, Any]:
    return {
        "h2": {
            "success_definition": "first_seen_delay_seconds <= 30",
            "support": {"minimum_point_estimate": 0.80, "minimum_wilson_lower": 0.70},
            "reject": {"maximum_point_estimate": 0.50, "maximum_wilson_upper": 0.60},
        },
        "h3": {
            "success_definition": "decision_window_seconds >= 60",
            "support": {"minimum_point_estimate": 0.70, "minimum_wilson_lower": 0.60},
            "reject": {"maximum_point_estimate": 0.30, "maximum_wilson_upper": 0.40},
        },
        "confidence_interval": "two_sided_95_percent_wilson",
        "minimum_eligible_trades": MIN_ELIGIBLE_TRADES,
        "maximum_sessions": MAX_SESSIONS,
    }


def _wilson(successes: int, trials: int) -> tuple[float, float]:
    if trials == 0:
        return 0.0, 1.0
    z = 1.959963984540054
    point = successes / trials
    denominator = 1 + z * z / trials
    center = (point + z * z / (2 * trials)) / denominator
    half = z * math.sqrt(point * (1 - point) / trials + z * z / (4 * trials * trials)) / denominator
    return center - half, center + half


def _evidence_row(
    row: dict[str, str],
    first_seen: datetime | None,
    trade_time: datetime | None,
    expiry: datetime | None,
    gamma_verified: bool,
) -> dict[str, Any]:
    return {
        "trade_identity": row.get("trade_identity", ""),
        "wallet_id": row.get("wallet_id", "").lower(),
        "asset_class": row.get("asset_class", ""),
        "market_slug": row.get("market_slug", ""),
        "first_seen": _iso(first_seen) if first_seen else "",
        "delay_seconds": (first_seen - trade_time).total_seconds() if first_seen and trade_time else None,
        "window_seconds": (expiry - first_seen).total_seconds() if first_seen and expiry else None,
        "gamma_verified_expiry": gamma_verified,
    }


def _is_target_market(row: dict[str, str]) -> bool:
    slug = row.get("market_slug", "")
    return row.get("asset_class", "") in {"BTC", "ETH", "SOL"} and "-updown-5m-" in slug


def _observer_request_counts(store: ProspectiveFirstSeenStore) -> dict[str, int]:
    total = int(store.connection.execute("SELECT COUNT(*) FROM polls").fetchone()[0])
    successful = int(store.connection.execute("SELECT COUNT(*) FROM polls WHERE status_code=200").fetchone()[0])
    return {"successful": successful, "failed": total - successful}


def _seed_and_observer_requests(seed_summary: Path, observer: dict[str, int]) -> dict[str, int]:
    seed = json.loads(seed_summary.read_text(encoding="utf-8"))
    return {
        "successful": int(seed.get("requests_successful", 0)) + observer["successful"],
        "failed": int(seed.get("requests_failed", 0)) + observer["failed"],
    }


def _latest_observer_run_id(store: ProspectiveFirstSeenStore) -> str:
    row = store.connection.execute("SELECT run_id FROM runs ORDER BY started_at_utc DESC LIMIT 1").fetchone()
    return str(row[0]) if row else ""


def _observer_run_configs(store: ProspectiveFirstSeenStore) -> dict[str, dict[str, Any]]:
    configs: dict[str, dict[str, Any]] = {}
    for row in store.connection.execute(
        """SELECT run_id, started_at_utc, deadline_at_utc, completed_at_utc,
        status, poll_interval_seconds, page_limit, max_requests, request_count
        FROM runs ORDER BY started_at_utc"""
    ):
        started = _parse_datetime(str(row["started_at_utc"]))
        deadline = _parse_datetime(str(row["deadline_at_utc"]))
        configs[str(row["run_id"])] = {
            "status": str(row["status"]),
            "started_at_utc": str(row["started_at_utc"]),
            "completed_at_utc": str(row["completed_at_utc"]),
            "session_duration_seconds": (deadline - started).total_seconds() if started and deadline else None,
            "poll_interval_seconds": float(row["poll_interval_seconds"]),
            "page_limit": int(row["page_limit"]),
            "max_requests": int(row["max_requests"]),
            "request_count": int(row["request_count"]),
        }
    return configs


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _parse_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="milliseconds")


def _stop_reason(action: str) -> str:
    if action == "GRADUATE_TO_ENGINEERING":
        return "SUPPORT_REACHED"
    if action == "FREEZE":
        return "DECISION_OR_BUDGET_REACHED"
    return ""


def _pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(text.encode("utf-8"))
    os.replace(temporary, path)
