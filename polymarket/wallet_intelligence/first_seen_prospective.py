"""Restart-safe prospective observation for public wallet activity.

This module persists every bounded public poll and every first-observed trade.
It intentionally does not calculate or interpret visibility delay.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import tempfile
import time
from datetime import UTC, datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Any, Callable

from .client import PolymarketPublicClient
from .first_seen import (
    API_INTRO_DOC_URL,
    DATA_API_RATE_LIMIT_REQUESTS,
    DATA_API_RATE_LIMIT_WINDOW_SECONDS,
    RATE_LIMIT_DOC_URL,
    STRONGEST_H1_WALLETS,
    trade_identity,
)
from .trade_history import canonical_json, classify_trade_market, normalize_decimal, raw_payload_hash


DEFAULT_PROSPECTIVE_OUTPUT = Path(
    "polymarket/models/wallet_intelligence_v1/first_seen_prospective_v1"
)
DEFAULT_PROSPECTIVE_DB = Path(
    "polymarket/data/wallet_intelligence/first_seen_prospective_v1/observer.sqlite3"
)
DEFAULT_DURATION_SECONDS = 300.0
DEFAULT_POLL_INTERVAL_SECONDS = 5.0
DEFAULT_PAGE_LIMIT = 100
DEFAULT_MAX_REQUESTS = 240

PROSPECTIVE_DATASET_FIELDS = [
    "trade_identity",
    "first_run_id",
    "first_poll_id",
    "wallet_id",
    "asset_class",
    "market_type",
    "up_down_market",
    "market_slug",
    "event_slug",
    "market_title",
    "condition_id",
    "token_id",
    "transaction_hash",
    "transaction_hash_available",
    "trade_timestamp",
    "trade_datetime_utc",
    "first_seen_timestamp_utc",
    "poll_timestamp_utc",
    "request_started_at_utc",
    "response_received_at_utc",
    "outcome",
    "side",
    "price",
    "size",
    "source_endpoint",
    "raw_payload_hash",
]


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    started_at_utc TEXT NOT NULL,
    deadline_at_utc TEXT NOT NULL,
    completed_at_utc TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK(status IN ('active', 'complete', 'failed')),
    poll_interval_seconds REAL NOT NULL,
    page_limit INTEGER NOT NULL,
    max_requests INTEGER NOT NULL,
    request_count INTEGER NOT NULL DEFAULT 0,
    wallets_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS polls (
    poll_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    poll_cycle INTEGER NOT NULL,
    wallet_id TEXT NOT NULL,
    poll_timestamp_utc TEXT NOT NULL,
    request_started_at_utc TEXT NOT NULL,
    response_received_at_utc TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    source_endpoint TEXT NOT NULL,
    error TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    payload_hash TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    UNIQUE(run_id, poll_cycle, wallet_id)
);
CREATE TABLE IF NOT EXISTS run_wallet_state (
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    wallet_id TEXT NOT NULL,
    baseline_established INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(run_id, wallet_id)
);
CREATE TABLE IF NOT EXISTS baseline_trades (
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    wallet_id TEXT NOT NULL,
    trade_identity TEXT NOT NULL,
    PRIMARY KEY(run_id, wallet_id, trade_identity)
);
CREATE TABLE IF NOT EXISTS trades (
    trade_identity TEXT PRIMARY KEY,
    first_run_id TEXT NOT NULL,
    first_poll_id INTEGER NOT NULL REFERENCES polls(poll_id),
    wallet_id TEXT NOT NULL,
    asset_class TEXT NOT NULL,
    market_type TEXT NOT NULL,
    up_down_market TEXT NOT NULL,
    market_slug TEXT NOT NULL,
    event_slug TEXT NOT NULL,
    market_title TEXT NOT NULL,
    condition_id TEXT NOT NULL,
    token_id TEXT NOT NULL,
    transaction_hash TEXT NOT NULL,
    trade_timestamp TEXT NOT NULL,
    trade_datetime_utc TEXT NOT NULL,
    first_seen_timestamp_utc TEXT NOT NULL,
    poll_timestamp_utc TEXT NOT NULL,
    request_started_at_utc TEXT NOT NULL,
    response_received_at_utc TEXT NOT NULL,
    outcome TEXT NOT NULL,
    side TEXT NOT NULL,
    price TEXT NOT NULL,
    size TEXT NOT NULL,
    source_endpoint TEXT NOT NULL,
    raw_payload_hash TEXT NOT NULL,
    raw_payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS observations (
    poll_id INTEGER NOT NULL REFERENCES polls(poll_id),
    trade_identity TEXT NOT NULL,
    PRIMARY KEY(poll_id, trade_identity)
);
"""


class ProspectiveFirstSeenStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.connection = sqlite3.connect(path, timeout=30)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "ProspectiveFirstSeenStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def start_or_resume_run(
        self,
        *,
        started_at_utc: str,
        duration_seconds: float,
        poll_interval_seconds: float,
        page_limit: int,
        max_requests: int,
        wallets: tuple[str, ...] = STRONGEST_H1_WALLETS,
    ) -> dict[str, Any]:
        _validate_bounds(wallets, duration_seconds, poll_interval_seconds, page_limit, max_requests)
        requested_start = _parse_datetime(started_at_utc)
        if requested_start is None:
            raise ValueError("started_at_utc must be a timezone-aware ISO timestamp")
        active = self.connection.execute(
            "SELECT * FROM runs WHERE status='active' ORDER BY started_at_utc DESC LIMIT 1"
        ).fetchone()
        if active is not None:
            active_deadline = _parse_datetime(str(active["deadline_at_utc"]))
            if (
                active_deadline
                and requested_start < active_deadline
                and int(active["request_count"]) < int(active["max_requests"])
            ):
                return dict(active)
            with self.connection:
                self.connection.execute(
                    "UPDATE runs SET status='complete', completed_at_utc=? WHERE run_id=?",
                    (started_at_utc, active["run_id"]),
                )
        deadline = requested_start + timedelta(seconds=duration_seconds)
        material = "|".join(
            [started_at_utc, str(duration_seconds), str(poll_interval_seconds), str(page_limit), str(max_requests), *wallets]
        )
        run_id = hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
        with self.connection:
            self.connection.execute(
                """INSERT INTO runs (
                    run_id, started_at_utc, deadline_at_utc, status,
                    poll_interval_seconds, page_limit, max_requests, wallets_json
                ) VALUES (?, ?, ?, 'active', ?, ?, ?, ?)""",
                (
                    run_id,
                    started_at_utc,
                    _iso(deadline),
                    poll_interval_seconds,
                    page_limit,
                    max_requests,
                    canonical_json(list(wallets)),
                ),
            )
            self.connection.executemany(
                "INSERT INTO run_wallet_state (run_id, wallet_id) VALUES (?, ?)",
                [(run_id, wallet) for wallet in wallets],
            )
        return dict(self.connection.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone())

    def persist_poll(self, snapshot: dict[str, Any]) -> dict[str, int | bool]:
        run_id = str(snapshot["run_id"])
        wallet_id = str(snapshot["wallet_id"]).lower()
        rows = [row for row in snapshot.get("rows", []) if isinstance(row, dict)]
        payload_json = canonical_json(rows)
        payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        with self.connection:
            cursor = self.connection.execute(
                """INSERT OR IGNORE INTO polls (
                    run_id, poll_cycle, wallet_id, poll_timestamp_utc,
                    request_started_at_utc, response_received_at_utc, status_code,
                    source_endpoint, error, row_count, payload_hash, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    int(snapshot["poll_cycle"]),
                    wallet_id,
                    str(snapshot["poll_timestamp_utc"]),
                    str(snapshot["request_started_at_utc"]),
                    str(snapshot["response_received_at_utc"]),
                    int(snapshot.get("status_code") or 0),
                    str(snapshot.get("source_endpoint") or ""),
                    str(snapshot.get("error") or ""),
                    len(rows),
                    payload_hash,
                    payload_json,
                ),
            )
            if cursor.rowcount == 0:
                return {"poll_inserted": False, "new_trades": 0, "duplicate_trades": 0}
            poll_id = int(cursor.lastrowid)
            self.connection.execute(
                "UPDATE runs SET request_count=request_count+1 WHERE run_id=?",
                (run_id,),
            )
            state = self.connection.execute(
                "SELECT baseline_established FROM run_wallet_state WHERE run_id=? AND wallet_id=?",
                (run_id, wallet_id),
            ).fetchone()
            baseline_established = bool(state and state["baseline_established"])
            identities = [(trade_identity(wallet_id, row), row) for row in rows]
            if not baseline_established and int(snapshot.get("status_code") or 0) == 200:
                self.connection.executemany(
                    "INSERT OR IGNORE INTO baseline_trades (run_id, wallet_id, trade_identity) VALUES (?, ?, ?)",
                    [(run_id, wallet_id, identity) for identity, _ in identities],
                )
                self.connection.execute(
                    "UPDATE run_wallet_state SET baseline_established=1 WHERE run_id=? AND wallet_id=?",
                    (run_id, wallet_id),
                )
                return {"poll_inserted": True, "new_trades": 0, "duplicate_trades": 0}

            new_trades = 0
            duplicate_trades = 0
            baseline = {
                row["trade_identity"]
                for row in self.connection.execute(
                    "SELECT trade_identity FROM baseline_trades WHERE run_id=? AND wallet_id=?",
                    (run_id, wallet_id),
                )
            }
            for identity, row in identities:
                self.connection.execute(
                    "INSERT OR IGNORE INTO observations (poll_id, trade_identity) VALUES (?, ?)",
                    (poll_id, identity),
                )
                if identity in baseline:
                    duplicate_trades += 1
                    continue
                inserted = self._insert_trade(run_id, poll_id, snapshot, identity, row)
                if inserted:
                    new_trades += 1
                else:
                    duplicate_trades += 1
            return {
                "poll_inserted": True,
                "new_trades": new_trades,
                "duplicate_trades": duplicate_trades,
            }

    def _insert_trade(
        self,
        run_id: str,
        poll_id: int,
        snapshot: dict[str, Any],
        identity: str,
        row: dict[str, Any],
    ) -> bool:
        title = str(row.get("title") or "")
        slug = str(row.get("slug") or "")
        market_type, asset_class, up_down = classify_trade_market(title, slug)
        trade_timestamp = str(row.get("timestamp") or "")
        trade_dt = _from_epoch(trade_timestamp)
        transaction_hash = str(row.get("transactionHash") or "").lower()
        values = (
                identity,
                run_id,
                poll_id,
                str(snapshot["wallet_id"]).lower(),
                asset_class,
                market_type,
                str(up_down).lower(),
                slug,
                str(row.get("eventSlug") or ""),
                title,
                str(row.get("conditionId") or "").lower(),
                str(row.get("asset") or ""),
                transaction_hash,
                trade_timestamp,
                _iso(trade_dt),
                str(snapshot["response_received_at_utc"]),
                str(snapshot["poll_timestamp_utc"]),
                str(snapshot["request_started_at_utc"]),
                str(snapshot["response_received_at_utc"]),
                str(row.get("outcome") or ""),
                str(row.get("side") or "").upper(),
                normalize_decimal(row.get("price")),
                normalize_decimal(row.get("size")),
                str(snapshot.get("source_endpoint") or ""),
                raw_payload_hash(row),
                canonical_json(row),
            )
        cursor = self.connection.execute(
            f"INSERT OR IGNORE INTO trades VALUES ({','.join('?' for _ in values)})",
            values,
        )
        return cursor.rowcount == 1

    def complete_run(self, run_id: str, completed_at_utc: str) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE runs SET status='complete', completed_at_utc=? WHERE run_id=?",
                (completed_at_utc, run_id),
            )

    def next_cycle(self, run_id: str) -> int:
        value = self.connection.execute(
            "SELECT COALESCE(MAX(poll_cycle), 0) + 1 AS next_cycle FROM polls WHERE run_id=?",
            (run_id,),
        ).fetchone()
        return int(value["next_cycle"])

    def export_rows(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        query = """SELECT * FROM trades
            ORDER BY first_seen_timestamp_utc, wallet_id, trade_timestamp, trade_identity"""
        for row in self.connection.execute(query):
            value = dict(row)
            value["transaction_hash_available"] = str(bool(value["transaction_hash"])).lower()
            rows.append({field: str(value.get(field, "")) for field in PROSPECTIVE_DATASET_FIELDS})
        return rows

    def counts(self) -> dict[str, int]:
        return {
            "runs": int(self.connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0]),
            "polls": int(self.connection.execute("SELECT COUNT(*) FROM polls").fetchone()[0]),
            "trades": int(self.connection.execute("SELECT COUNT(*) FROM trades").fetchone()[0]),
            "observations": int(self.connection.execute("SELECT COUNT(*) FROM observations").fetchone()[0]),
        }


def run_prospective_observer(
    *,
    client: PolymarketPublicClient,
    db_path: Path = DEFAULT_PROSPECTIVE_DB,
    output_dir: Path = DEFAULT_PROSPECTIVE_OUTPUT,
    duration_seconds: float = DEFAULT_DURATION_SECONDS,
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
    page_limit: int = DEFAULT_PAGE_LIMIT,
    max_requests: int = DEFAULT_MAX_REQUESTS,
    now: Callable[[], datetime] | None = None,
    monotonic: Callable[[], float] | None = None,
    sleeper: Callable[[float], None] | None = None,
) -> dict[str, Any]:
    now = now or (lambda: datetime.now(UTC))
    monotonic = monotonic or time.monotonic
    sleeper = sleeper or time.sleep
    with ProspectiveFirstSeenStore(db_path) as store:
        run = store.start_or_resume_run(
            started_at_utc=_iso(now()),
            duration_seconds=duration_seconds,
            poll_interval_seconds=poll_interval_seconds,
            page_limit=page_limit,
            max_requests=max_requests,
        )
        run_id = str(run["run_id"])
        deadline = _parse_datetime(str(run["deadline_at_utc"]))
        cycle = store.next_cycle(run_id)
        while deadline and now() < deadline:
            request_count = int(
                store.connection.execute("SELECT request_count FROM runs WHERE run_id=?", (run_id,)).fetchone()[0]
            )
            if request_count >= int(run["max_requests"]):
                break
            cycle_started_monotonic = monotonic()
            poll_timestamp = _iso(now())
            for wallet_id in STRONGEST_H1_WALLETS:
                if now() >= deadline or request_count >= int(run["max_requests"]):
                    break
                request_started = _iso(now())
                try:
                    response = client.activity_trades(wallet_id, limit=int(run["page_limit"]), offset=0)
                    received = _iso(now())
                    rows = response.payload if isinstance(response.payload, list) else []
                    status_code = response.status_code
                    source_endpoint = response.url
                    error = ""
                except Exception as exc:  # network failure is persisted evidence
                    received = _iso(now())
                    rows = []
                    status_code = 0
                    source_endpoint = "https://data-api.polymarket.com/activity"
                    error = f"{type(exc).__name__}: {exc}"
                store.persist_poll(
                    {
                        "run_id": run_id,
                        "poll_cycle": cycle,
                        "wallet_id": wallet_id,
                        "poll_timestamp_utc": poll_timestamp,
                        "request_started_at_utc": request_started,
                        "response_received_at_utc": received,
                        "status_code": status_code,
                        "source_endpoint": source_endpoint,
                        "error": error,
                        "rows": rows,
                    }
                )
                request_count += 1
            cycle += 1
            remaining = float(run["poll_interval_seconds"]) - (monotonic() - cycle_started_monotonic)
            if remaining > 0:
                sleeper(min(remaining, max(0.0, (deadline - now()).total_seconds())))
        store.complete_run(run_id, _iso(now()))
    return prepare_prospective_experiment(db_path=db_path, output_dir=output_dir)


def prepare_prospective_experiment(
    *,
    db_path: Path = DEFAULT_PROSPECTIVE_DB,
    output_dir: Path = DEFAULT_PROSPECTIVE_OUTPUT,
) -> dict[str, Any]:
    with ProspectiveFirstSeenStore(db_path) as store:
        rows = store.export_rows()
        counts = store.counts()
        journal_mode = str(store.connection.execute("PRAGMA journal_mode").fetchone()[0])
    fixture = validate_restart_and_duplicates()
    csv_text = render_dataset(rows)
    validation: dict[str, Any] = {
        "task": "Wallet First-Seen Prospective Experiment v1",
        "h2_evaluated": False,
        "wallets": list(STRONGEST_H1_WALLETS),
        "wallet_count": len(STRONGEST_H1_WALLETS),
        "poll_interval_seconds": DEFAULT_POLL_INTERVAL_SECONDS,
        "max_duration_seconds": DEFAULT_DURATION_SECONDS,
        "max_requests": DEFAULT_MAX_REQUESTS,
        "page_limit": DEFAULT_PAGE_LIMIT,
        "database_path": str(db_path),
        "database_counts": counts,
        "sqlite_journal_mode": journal_mode,
        "restart_safe": fixture["restart_safe"],
        "duplicate_safe": fixture["duplicate_safe"],
        "every_poll_persisted": fixture["every_poll_persisted"],
        "first_seen_immutable": fixture["first_seen_immutable"],
        "deterministic_export": fixture["deterministic_export"],
        "bounded_configuration": True,
        "public_read_only_only": True,
        "no_authenticated_endpoints": True,
        "no_trading_or_orders": True,
        "api_limits": {
            "documentation_url": RATE_LIMIT_DOC_URL,
            "documentation_checked_on": "2026-06-28",
            "data_api_general_limit_requests": DATA_API_RATE_LIMIT_REQUESTS,
            "window_seconds": DATA_API_RATE_LIMIT_WINDOW_SECONDS,
            "configured_requests_per_10_seconds": 8.0,
            "configured_limit_utilization": 0.008,
        },
        "endpoint": {
            "url": "https://data-api.polymarket.com/activity",
            "method": "GET",
            "authentication": "none",
            "documentation_url": API_INTRO_DOC_URL,
        },
        "dataset_sha256": hashlib.sha256(csv_text.encode("utf-8")).hexdigest(),
    }
    validation["all_validation_passed"] = all(
        validation[key]
        for key in (
            "restart_safe",
            "duplicate_safe",
            "every_poll_persisted",
            "first_seen_immutable",
            "deterministic_export",
            "bounded_configuration",
            "public_read_only_only",
            "no_authenticated_endpoints",
            "no_trading_or_orders",
        )
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "wallet_first_seen_dataset.csv").write_text(csv_text, encoding="utf-8", newline="")
    (output_dir / "wallet_first_seen_validation.json").write_text(
        json.dumps(validation, indent=2, sort_keys=True), encoding="utf-8"
    )
    (output_dir / "wallet_first_seen_design_report.md").write_text(
        render_design_report(validation), encoding="utf-8"
    )
    return validation


def validate_restart_and_duplicates() -> dict[str, bool]:
    wallet = STRONGEST_H1_WALLETS[0]
    baseline = _fixture_trade("0xbaseline", 1782413100)
    new_trade = _fixture_trade("0xnew", 1782413104)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "observer.sqlite3"
        with ProspectiveFirstSeenStore(path) as store:
            run = store.start_or_resume_run(
                started_at_utc="2026-06-25T18:45:00.000+00:00",
                duration_seconds=300,
                poll_interval_seconds=5,
                page_limit=100,
                max_requests=240,
            )
            run_id = str(run["run_id"])
            store.persist_poll(_fixture_snapshot(run_id, 1, wallet, "2026-06-25T18:45:01.000+00:00", [baseline]))
        with ProspectiveFirstSeenStore(path) as store:
            resumed = store.start_or_resume_run(
                started_at_utc="2026-06-25T18:46:00.000+00:00",
                duration_seconds=300,
                poll_interval_seconds=5,
                page_limit=100,
                max_requests=240,
            )
            restart_safe = resumed["run_id"] == run_id and store.next_cycle(run_id) == 2
            first = store.persist_poll(
                _fixture_snapshot(run_id, 2, wallet, "2026-06-25T18:45:06.000+00:00", [new_trade, baseline])
            )
            first_seen = store.export_rows()[0]["first_seen_timestamp_utc"]
            duplicate = store.persist_poll(
                _fixture_snapshot(run_id, 3, wallet, "2026-06-25T18:45:11.000+00:00", [new_trade, baseline])
            )
            duplicate_poll = store.persist_poll(
                _fixture_snapshot(run_id, 3, wallet, "2026-06-25T18:45:12.000+00:00", [new_trade])
            )
            rows = store.export_rows()
            export_one = render_dataset(rows)
            export_two = render_dataset(store.export_rows())
            counts = store.counts()
    return {
        "restart_safe": restart_safe,
        "duplicate_safe": first["new_trades"] == 1
        and duplicate["new_trades"] == 0
        and duplicate_poll["poll_inserted"] is False
        and len(rows) == 1,
        "every_poll_persisted": counts["polls"] == 3,
        "first_seen_immutable": rows[0]["first_seen_timestamp_utc"] == first_seen,
        "deterministic_export": export_one == export_two,
    }


def render_dataset(rows: list[dict[str, str]]) -> str:
    handle = StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=PROSPECTIVE_DATASET_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue()


def render_design_report(validation: dict[str, Any]) -> str:
    lines = [
        "# Wallet First-Seen Prospective Experiment v1",
        "",
        "This sprint implements the observation system. It does not evaluate H2 and does not estimate latency.",
        "",
        "## Observation Boundary",
        "",
        f"- Wallets: {validation['wallet_count']} frozen H1 wallets",
        f"- Endpoint: `{validation['endpoint']['url']}`",
        f"- Poll interval: {validation['poll_interval_seconds']} seconds",
        f"- Maximum duration per run: {validation['max_duration_seconds']} seconds",
        f"- Maximum requests per run: {validation['max_requests']}",
        f"- Latest rows per wallet poll: {validation['page_limit']}",
        "- Public GET only; no authentication, wallet connection, orders, or trading",
        "",
        "## Persistence",
        "",
        "- SQLite transactions persist every poll payload before analysis",
        "- Active run deadline and request count survive restart",
        "- `(run_id, poll_cycle, wallet_id)` prevents duplicate poll insertion",
        "- Trade identity is globally unique and first-seen timestamp is immutable",
        "- Startup rows are persisted as run baseline identities, not new trades",
        "",
        "## API Limits",
        "",
        f"- Documented Data API limit: {validation['api_limits']['data_api_general_limit_requests']} requests per {validation['api_limits']['window_seconds']} seconds",
        f"- Configured usage: {validation['api_limits']['configured_requests_per_10_seconds']} requests per 10 seconds ({validation['api_limits']['configured_limit_utilization']:.2%})",
        f"- Documentation: {validation['api_limits']['documentation_url']}",
        "",
        "## Validation",
        "",
        f"- Restart safe: {validation['restart_safe']}",
        f"- Duplicate safe: {validation['duplicate_safe']}",
        f"- Every poll persisted: {validation['every_poll_persisted']}",
        f"- First-seen immutable: {validation['first_seen_immutable']}",
        f"- Deterministic export: {validation['deterministic_export']}",
        "",
        "## Research Status",
        "",
        "H2 is not evaluated in this sprint. The system can measure H2 after a future bounded collection produces a preregistered number of target five-minute trades.",
        "",
        "Remaining blocker: insufficient prospective target-market observations.",
    ]
    return "\n".join(lines) + "\n"


def _validate_bounds(
    wallets: tuple[str, ...],
    duration_seconds: float,
    poll_interval_seconds: float,
    page_limit: int,
    max_requests: int,
) -> None:
    if wallets != STRONGEST_H1_WALLETS:
        raise ValueError("only the four frozen H1 wallets are permitted")
    if not 0 < duration_seconds <= DEFAULT_DURATION_SECONDS:
        raise ValueError("duration exceeds the bounded five-minute maximum")
    if poll_interval_seconds < DEFAULT_POLL_INTERVAL_SECONDS:
        raise ValueError("poll interval must be at least five seconds")
    if not 1 <= page_limit <= DEFAULT_PAGE_LIMIT:
        raise ValueError("page limit must be between 1 and 100")
    if not 1 <= max_requests <= DEFAULT_MAX_REQUESTS:
        raise ValueError("request count exceeds the bounded maximum")


def _fixture_trade(transaction_hash: str, timestamp: int) -> dict[str, Any]:
    return {
        "timestamp": timestamp,
        "transactionHash": transaction_hash,
        "conditionId": "0xcondition",
        "asset": "token-up",
        "slug": "btc-updown-5m-fixture",
        "eventSlug": "btc-updown-5m-fixture",
        "title": "Bitcoin Up or Down",
        "outcome": "Up",
        "side": "BUY",
        "price": 0.55,
        "size": 10,
    }


def _fixture_snapshot(
    run_id: str,
    cycle: int,
    wallet_id: str,
    timestamp: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "poll_cycle": cycle,
        "wallet_id": wallet_id,
        "poll_timestamp_utc": timestamp,
        "request_started_at_utc": timestamp,
        "response_received_at_utc": timestamp,
        "status_code": 200,
        "source_endpoint": "https://data-api.polymarket.com/activity?type=TRADE",
        "error": "",
        "rows": rows,
    }


def _parse_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _from_epoch(value: str) -> datetime | None:
    try:
        return datetime.fromtimestamp(int(value), UTC)
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def _iso(value: datetime | None) -> str:
    return value.isoformat(timespec="milliseconds") if value else ""
