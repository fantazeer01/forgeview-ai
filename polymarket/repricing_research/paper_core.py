from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .simulator import SIGNAL_REASONS


class StrategyFingerprintMismatch(RuntimeError):
    """Raised when an existing ledger belongs to another strategy contract."""


class InjectedFailure(RuntimeError):
    """Test-only interruption at a named durability boundary."""


@dataclass(frozen=True)
class FrozenPaperConfig:
    external_move_threshold_bps: float = 6.0
    repricing_ratio: float = 0.65
    minimum_confidence: float = 0.45
    minimum_entry_seconds: float = 60.0
    repricing_target: float = 0.03
    stop_loss: float = 0.03
    max_holding_seconds: float = 180.0
    conservative_slippage: float = 0.02
    signal_reasons: tuple[str, ...] = tuple(sorted(SIGNAL_REASONS))

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class RestartSafePaperCore:
    """Causal, restart-safe paper position state machine.

    Raw events are committed before processing. A transition and its processed
    cursor are committed together, so recovery only needs to replay unprocessed
    journal rows.
    """

    def __init__(
        self,
        database_path: str | Path,
        config: FrozenPaperConfig | None = None,
    ) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.config = config or FrozenPaperConfig()
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = FULL")
        self._create_schema()
        self._verify_fingerprint()
        self.recover()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> RestartSafePaperCore:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def ingest_event(
        self,
        source_id: str,
        event_index: int,
        event: dict[str, Any],
        fail_at: str | None = None,
    ) -> None:
        canonical = json.dumps(event, sort_keys=True, separators=(",", ":"))
        with self.connection:
            existing = self.connection.execute(
                "SELECT event_json FROM raw_events WHERE source_id = ? AND event_index = ?",
                (source_id, event_index),
            ).fetchone()
            if existing is not None and existing["event_json"] != canonical:
                raise ValueError("event identity was reused with different content")
            self.connection.execute(
                """
                INSERT OR IGNORE INTO raw_events(source_id, event_index, event_json)
                VALUES (?, ?, ?)
                """,
                (source_id, event_index, canonical),
            )
        self._inject(fail_at, "after_raw_persist")
        self.recover(fail_at=fail_at)

    def recover(self, fail_at: str | None = None) -> None:
        while True:
            row = self.connection.execute(
                """
                SELECT id, source_id, event_index, event_json
                FROM raw_events WHERE processed = 0 ORDER BY id LIMIT 1
                """
            ).fetchone()
            if row is None:
                return
            self.connection.execute("BEGIN IMMEDIATE")
            try:
                event = json.loads(row["event_json"])
                self._apply_event(row["source_id"], row["event_index"], event, fail_at)
                self._inject(fail_at, "before_cursor_commit")
                self.connection.execute(
                    "UPDATE raw_events SET processed = 1 WHERE id = ?", (row["id"],)
                )
                self.connection.execute(
                    """
                    INSERT INTO source_cursors(source_id, last_event_index, last_raw_id)
                    VALUES (?, ?, ?)
                    ON CONFLICT(source_id) DO UPDATE SET
                        last_event_index = excluded.last_event_index,
                        last_raw_id = excluded.last_raw_id
                    """,
                    (row["source_id"], row["event_index"], row["id"]),
                )
                self.connection.commit()
            except Exception:
                self.connection.rollback()
                raise
            self._inject(fail_at, "after_cursor_commit")

    def signals(self) -> list[dict[str, Any]]:
        return self._rows("SELECT * FROM signals ORDER BY admitted_at, signal_key")

    def positions(self) -> list[dict[str, Any]]:
        return self._rows("SELECT * FROM positions ORDER BY entry_timestamp, position_id")

    def open_positions(self) -> list[dict[str, Any]]:
        return self._rows(
            "SELECT * FROM positions WHERE status = 'OPEN' ORDER BY entry_timestamp"
        )

    def trades(self) -> list[dict[str, Any]]:
        return self._rows("SELECT * FROM trades ORDER BY exit_timestamp, trade_id")

    def source_cursor(self, source_id: str) -> int | None:
        row = self.connection.execute(
            "SELECT last_event_index FROM source_cursors WHERE source_id = ?",
            (source_id,),
        ).fetchone()
        return int(row["last_event_index"]) if row is not None else None

    def register_stream_source(
        self,
        source_id: str,
        source_path: str,
        first_event_hash: str,
        first_event_timestamp: str,
    ) -> None:
        with self.connection:
            row = self.connection.execute(
                "SELECT * FROM stream_sources WHERE source_id = ?", (source_id,)
            ).fetchone()
            expected = (source_path, first_event_hash, first_event_timestamp)
            if row is not None:
                actual = (
                    row["source_path"],
                    row["first_event_hash"],
                    row["first_event_timestamp"],
                )
                if actual != expected:
                    raise ValueError("stream source identity does not match ledger metadata")
                return
            self.connection.execute(
                """
                INSERT INTO stream_sources(
                    source_id, source_path, first_event_hash, first_event_timestamp
                ) VALUES (?, ?, ?, ?)
                """,
                (source_id, source_path, first_event_hash, first_event_timestamp),
            )

    def stream_source(self, source_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT * FROM stream_sources WHERE source_id = ?", (source_id,)
        ).fetchone()
        return dict(row) if row is not None else None

    def verify_source_event(
        self, source_id: str, event_index: int, event: dict[str, Any]
    ) -> None:
        row = self.connection.execute(
            """
            SELECT event_json FROM raw_events
            WHERE source_id = ? AND event_index = ?
            """,
            (source_id, event_index),
        ).fetchone()
        if row is None:
            raise ValueError("processed source event is missing from the raw journal")
        canonical = json.dumps(event, sort_keys=True, separators=(",", ":"))
        if row["event_json"] != canonical:
            raise ValueError("source event differs from the committed raw journal")

    def validation_snapshot(self) -> dict[str, Any]:
        counts = {}
        for table in ("raw_events", "signals", "positions", "trades"):
            counts[table] = self.connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
        pending = self.connection.execute(
            "SELECT COUNT(*) FROM raw_events WHERE processed = 0"
        ).fetchone()[0]
        realized = self.connection.execute(
            "SELECT realized_pnl FROM paper_account WHERE id = 1"
        ).fetchone()[0]
        return {
            "strategy_fingerprint": self.config.fingerprint,
            "counts": counts,
            "open_positions": len(self.open_positions()),
            "pending_events": pending,
            "realized_pnl": realized,
        }

    def _apply_event(
        self,
        source_id: str,
        event_index: int,
        event: dict[str, Any],
        fail_at: str | None,
    ) -> None:
        kind = event.get("event")
        payload = event.get("payload", {})
        timestamp = event.get("timestamp")
        if not isinstance(timestamp, str):
            raise ValueError("event timestamp is required")
        if kind == "polymarket_snapshot":
            self._apply_snapshot(timestamp, payload, fail_at)
        elif kind == "lag_measurement":
            self._apply_lag_measurement(
                source_id, event_index, timestamp, payload, fail_at
            )
        elif kind in {"market_lifecycle", "lifecycle_tracking"}:
            self._apply_lifecycle(timestamp, payload, fail_at)

    def _apply_lifecycle(
        self, timestamp: str, payload: dict[str, Any], fail_at: str | None
    ) -> None:
        current = payload.get("current", payload.get("current_state"))
        if current != "closed":
            return
        market = payload.get("market", {})
        market_id = payload.get("market_id") or (
            market.get("market_id") if isinstance(market, dict) else None
        )
        if not market_id:
            return
        snapshot = self.connection.execute(
            "SELECT * FROM latest_snapshots WHERE market_id = ?", (market_id,)
        ).fetchone()
        if snapshot is None:
            return
        positions = self.connection.execute(
            "SELECT * FROM positions WHERE market_id = ? AND status = 'OPEN'",
            (market_id,),
        ).fetchall()
        for position in positions:
            exit_price = (
                snapshot["yes_price"] if position["side"] == "YES"
                else snapshot["no_price"]
            )
            self._close_position(position, timestamp, exit_price, "expiry")
            self._inject(fail_at, "after_trade_close")

    def _apply_snapshot(
        self, timestamp: str, payload: dict[str, Any], fail_at: str | None
    ) -> None:
        market_id = str(payload["market_id"])
        asset = str(payload["asset"])
        yes_price = float(payload["yes_price"])
        no_price = float(payload["no_price"])
        seconds_to_expiry = float(payload["seconds_to_expiry"])
        self.connection.execute(
            """
            INSERT INTO latest_snapshots(
                market_id, timestamp, asset, yes_price, no_price, seconds_to_expiry
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(market_id) DO UPDATE SET
                timestamp = excluded.timestamp,
                asset = excluded.asset,
                yes_price = excluded.yes_price,
                no_price = excluded.no_price,
                seconds_to_expiry = excluded.seconds_to_expiry
            WHERE excluded.timestamp >= latest_snapshots.timestamp
            """,
            (market_id, timestamp, asset, yes_price, no_price, seconds_to_expiry),
        )
        positions = self.connection.execute(
            "SELECT * FROM positions WHERE market_id = ? AND status = 'OPEN'",
            (market_id,),
        ).fetchall()
        for position in positions:
            current_price = yes_price if position["side"] == "YES" else no_price
            move = current_price - position["entry_price"]
            elapsed = (
                datetime.fromisoformat(timestamp)
                - datetime.fromisoformat(position["entry_timestamp"])
            ).total_seconds()
            reason = None
            if move >= self.config.repricing_target:
                reason = "repricing_target"
            elif move <= -self.config.stop_loss:
                reason = "stop_loss"
            elif elapsed >= self.config.max_holding_seconds:
                reason = "timeout"
            elif seconds_to_expiry <= 0:
                reason = "expiry"
            if reason is not None:
                self._close_position(position, timestamp, current_price, reason)
                self._inject(fail_at, "after_trade_close")

    def _apply_lag_measurement(
        self,
        source_id: str,
        event_index: int,
        timestamp: str,
        payload: dict[str, Any],
        fail_at: str | None,
    ) -> None:
        measurement = payload.get("measurement", {})
        reason = measurement.get("reason")
        direction = measurement.get("direction")
        if reason not in set(self.config.signal_reasons) or direction not in {"UP", "DOWN"}:
            return
        market_id = str(payload["market_id"])
        snapshot = self.connection.execute(
            "SELECT * FROM latest_snapshots WHERE market_id = ?", (market_id,)
        ).fetchone()
        if snapshot is None or snapshot["seconds_to_expiry"] < self.config.minimum_entry_seconds:
            return
        side = "YES" if direction == "UP" else "NO"
        overlap = self.connection.execute(
            """
            SELECT 1 FROM positions
            WHERE market_id = ? AND side = ? AND status = 'OPEN'
            """,
            (market_id, side),
        ).fetchone()
        if overlap is not None:
            return
        signal_identity = f"{market_id}|{direction}|{timestamp}"
        signal_key = hashlib.sha256(signal_identity.encode("utf-8")).hexdigest()
        self._inject(fail_at, "before_signal_admission")
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO signals(
                signal_key, source_id, event_index, admitted_at, market_id,
                asset, direction, side, reason, measurement_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal_key,
                source_id,
                event_index,
                timestamp,
                market_id,
                snapshot["asset"],
                direction,
                side,
                reason,
                json.dumps(measurement, sort_keys=True, separators=(",", ":")),
            ),
        )
        if cursor.rowcount == 0:
            return
        self._inject(fail_at, "after_signal_admission")
        entry_price = snapshot["yes_price"] if side == "YES" else snapshot["no_price"]
        self.connection.execute(
            """
            INSERT INTO positions(
                position_id, signal_key, market_id, asset, side,
                entry_timestamp, entry_price, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN')
            """,
            (
                signal_key,
                signal_key,
                market_id,
                snapshot["asset"],
                side,
                snapshot["timestamp"],
                entry_price,
            ),
        )
        self._inject(fail_at, "after_position_open")

    def _close_position(
        self,
        position: sqlite3.Row,
        timestamp: str,
        exit_price: float,
        reason: str,
    ) -> None:
        pnl_before = exit_price - position["entry_price"]
        pnl_after = pnl_before - self.config.conservative_slippage
        close_identity = f"{position['position_id']}|{timestamp}|{reason}"
        trade_id = hashlib.sha256(close_identity.encode("utf-8")).hexdigest()
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO trades(
                trade_id, position_id, signal_key, market_id, asset, side,
                entry_timestamp, entry_price, exit_timestamp, exit_price,
                exit_reason, pnl_before_slippage, pnl_after_slippage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade_id,
                position["position_id"],
                position["signal_key"],
                position["market_id"],
                position["asset"],
                position["side"],
                position["entry_timestamp"],
                position["entry_price"],
                timestamp,
                exit_price,
                reason,
                pnl_before,
                pnl_after,
            ),
        )
        if cursor.rowcount == 0:
            return
        self.connection.execute(
            """
            UPDATE positions SET status = 'CLOSED', closed_trade_id = ?
            WHERE position_id = ? AND status = 'OPEN'
            """,
            (trade_id, position["position_id"]),
        )
        self.connection.execute(
            "UPDATE paper_account SET realized_pnl = realized_pnl + ? WHERE id = 1",
            (pnl_after,),
        )

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS raw_events(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                event_index INTEGER NOT NULL,
                event_json TEXT NOT NULL,
                processed INTEGER NOT NULL DEFAULT 0 CHECK(processed IN (0, 1)),
                UNIQUE(source_id, event_index)
            );
            CREATE TABLE IF NOT EXISTS source_cursors(
                source_id TEXT PRIMARY KEY,
                last_event_index INTEGER NOT NULL,
                last_raw_id INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS stream_sources(
                source_id TEXT PRIMARY KEY,
                source_path TEXT NOT NULL UNIQUE,
                first_event_hash TEXT NOT NULL,
                first_event_timestamp TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS latest_snapshots(
                market_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                asset TEXT NOT NULL,
                yes_price REAL NOT NULL,
                no_price REAL NOT NULL,
                seconds_to_expiry REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS signals(
                signal_key TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                event_index INTEGER NOT NULL,
                admitted_at TEXT NOT NULL,
                market_id TEXT NOT NULL,
                asset TEXT NOT NULL,
                direction TEXT NOT NULL,
                side TEXT NOT NULL,
                reason TEXT NOT NULL,
                measurement_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS positions(
                position_id TEXT PRIMARY KEY,
                signal_key TEXT NOT NULL UNIQUE REFERENCES signals(signal_key),
                market_id TEXT NOT NULL,
                asset TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_timestamp TEXT NOT NULL,
                entry_price REAL NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('OPEN', 'CLOSED')),
                closed_trade_id TEXT UNIQUE
            );
            CREATE UNIQUE INDEX IF NOT EXISTS one_open_market_side
            ON positions(market_id, side) WHERE status = 'OPEN';
            CREATE TABLE IF NOT EXISTS trades(
                trade_id TEXT PRIMARY KEY,
                position_id TEXT NOT NULL UNIQUE REFERENCES positions(position_id),
                signal_key TEXT NOT NULL UNIQUE REFERENCES signals(signal_key),
                market_id TEXT NOT NULL,
                asset TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_timestamp TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_timestamp TEXT NOT NULL,
                exit_price REAL NOT NULL,
                exit_reason TEXT NOT NULL,
                pnl_before_slippage REAL NOT NULL,
                pnl_after_slippage REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS paper_account(
                id INTEGER PRIMARY KEY CHECK(id = 1),
                realized_pnl REAL NOT NULL
            );
            INSERT OR IGNORE INTO paper_account(id, realized_pnl) VALUES (1, 0.0);
            """
        )

    def _verify_fingerprint(self) -> None:
        row = self.connection.execute(
            "SELECT value FROM metadata WHERE key = 'strategy_fingerprint'"
        ).fetchone()
        if row is None:
            with self.connection:
                self.connection.execute(
                    "INSERT INTO metadata(key, value) VALUES ('strategy_fingerprint', ?)",
                    (self.config.fingerprint,),
                )
        elif row["value"] != self.config.fingerprint:
            self.close()
            raise StrategyFingerprintMismatch(
                "ledger strategy fingerprint does not match frozen configuration"
            )

    def _rows(self, query: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute(query).fetchall()]

    @staticmethod
    def _inject(requested: str | None, stage: str) -> None:
        if requested == stage:
            raise InjectedFailure(stage)
