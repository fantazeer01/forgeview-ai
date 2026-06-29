from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .paper_core import RestartSafePaperCore


class V5StreamValidationError(ValueError):
    """Raised when a v5 JSONL source cannot be resumed safely."""


class V5StreamUnavailableError(RuntimeError):
    """Raised when a configured stream is temporarily unavailable."""


@dataclass(frozen=True)
class V5StreamSyncResult:
    source_id: str
    source_path: str
    verified_events: int
    ingested_events: int
    ingested_lag_measurements: int
    last_event_index: int | None
    last_event_timestamp: str | None
    deferred_trailing_bytes: int
    processed_events: int
    reached_eof: bool
    remaining_bytes: int
    batch_limit_reached: bool
    replaying_committed_prefix: bool
    session_completed_seen: bool
    session_health_status: str | None
    session_health_errors: tuple[str, ...]


class V5JsonlPaperAdapter:
    """Incrementally feed complete v5 JSONL events into the paper core."""

    def __init__(
        self,
        session_path: str | Path,
        core: RestartSafePaperCore,
        *,
        max_line_bytes: int = 1024 * 1024,
    ) -> None:
        self.session_path = Path(session_path).resolve()
        self.core = core
        normalized = str(self.session_path).casefold()
        self.source_id = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        self._byte_offset = 0
        self._next_event_index = 0
        self._last_timestamp: datetime | None = None
        self._initialized = False
        self._last_sync_lag_measurements = 0
        self._max_line_bytes = max_line_bytes
        if self._max_line_bytes <= 0:
            raise ValueError("maximum v5 line bytes must be positive")

    def sync(
        self,
        *,
        max_events: int | None = None,
        progress_callback: Callable[[], None] | None = None,
    ) -> V5StreamSyncResult:
        if max_events is not None and max_events <= 0:
            raise ValueError("maximum sync events must be positive")
        if not self.session_path.is_file():
            raise V5StreamUnavailableError(
                f"v5 session does not exist: {self.session_path}"
            )
        size = self.session_path.stat().st_size
        if self._initialized and size < self._byte_offset:
            raise V5StreamValidationError("v5 session was truncated after synchronization")

        verified = 0
        lag_measurements = 0
        self._last_sync_lag_measurements = 0
        deferred = 0
        cursor = self.core.source_cursor(self.source_id)
        starting_cursor = cursor
        local_offset = self._byte_offset
        local_next_index = self._next_event_index
        local_last_timestamp = self._last_timestamp
        new_events: list[tuple[int, dict[str, Any]]] = []
        processed_events = 0
        reached_eof = False
        session_completed_seen = False
        session_health_status: str | None = None
        session_health_errors: list[str] = []
        with self.session_path.open("rb") as handle:
            handle.seek(local_offset)
            while True:
                if max_events is not None and processed_events >= max_events:
                    break
                line_start = handle.tell()
                raw_line = handle.readline(self._max_line_bytes + 1)
                if not raw_line:
                    reached_eof = True
                    break
                if len(raw_line) > self._max_line_bytes:
                    raise V5StreamValidationError(
                        f"event {local_next_index} exceeds maximum line size"
                    )
                if not raw_line.endswith(b"\n"):
                    deferred = len(raw_line)
                    handle.seek(line_start)
                    break
                event = self._decode_event(raw_line, local_next_index)
                timestamp = self._validate_event(event, local_next_index)
                if local_last_timestamp is not None and timestamp < local_last_timestamp:
                    raise V5StreamValidationError(
                        f"event {local_next_index} timestamp is out of order"
                    )
                if local_next_index == 0:
                    self._register_source(event)
                if cursor is not None and local_next_index <= cursor:
                    try:
                        self.core.verify_source_event(
                            self.source_id, local_next_index, event
                        )
                    except ValueError as exc:
                        raise V5StreamValidationError(str(exc)) from exc
                    verified += 1
                    if progress_callback is not None:
                        progress_callback()
                else:
                    new_events.append((local_next_index, event))
                    if event["event"] == "lag_measurement":
                        lag_measurements += 1
                if event["event"] == "session_completed":
                    session_completed_seen = True
                    session_health_status, errors = self._session_health(event)
                    session_health_errors.extend(errors)
                local_last_timestamp = timestamp
                local_next_index += 1
                processed_events += 1
                local_offset = handle.tell()

        try:
            self.core.ingest_event_batch(
                self.source_id,
                new_events,
                progress_callback=progress_callback,
            )
        except ValueError as exc:
            raise V5StreamValidationError(str(exc)) from exc
        self._last_sync_lag_measurements = lag_measurements
        self._last_timestamp = local_last_timestamp
        self._next_event_index = local_next_index
        self._byte_offset = local_offset

        committed = self.core.source_cursor(self.source_id)
        stopped_at_batch_limit = (
            max_events is not None and processed_events >= max_events
        )
        if (
            committed is not None
            and self._next_event_index <= committed
            and not stopped_at_batch_limit
        ):
            raise V5StreamValidationError(
                "v5 session is truncated before the committed event cursor"
            )
        self._initialized = True
        remaining_bytes = max(0, self.session_path.stat().st_size - self._byte_offset)
        batch_limit_reached = (
            max_events is not None
            and processed_events >= max_events
            and remaining_bytes > 0
        )
        return V5StreamSyncResult(
            source_id=self.source_id,
            source_path=str(self.session_path),
            verified_events=verified,
            ingested_events=len(new_events),
            ingested_lag_measurements=lag_measurements,
            last_event_index=committed,
            last_event_timestamp=(
                self._last_timestamp.isoformat()
                if self._last_timestamp is not None else None
            ),
            deferred_trailing_bytes=deferred,
            processed_events=processed_events,
            reached_eof=reached_eof,
            remaining_bytes=remaining_bytes,
            batch_limit_reached=batch_limit_reached,
            replaying_committed_prefix=(
                starting_cursor is not None and self._next_event_index <= starting_cursor
            ),
            session_completed_seen=session_completed_seen,
            session_health_status=session_health_status,
            session_health_errors=tuple(session_health_errors),
        )

    @property
    def last_event_timestamp(self) -> str | None:
        return (
            self._last_timestamp.isoformat()
            if self._last_timestamp is not None else None
        )

    @property
    def last_sync_lag_measurements(self) -> int:
        return self._last_sync_lag_measurements

    @property
    def byte_offset(self) -> int:
        return self._byte_offset

    @staticmethod
    def _session_health(event: dict[str, Any]) -> tuple[str | None, list[str]]:
        payload = event.get("payload", {})
        campaign = payload.get("campaign_completeness", {})
        continuity = payload.get("observation_continuity", {})
        campaign_status = campaign.get("status") if isinstance(campaign, dict) else None
        continuity_status = continuity.get("status") if isinstance(continuity, dict) else None
        errors: list[str] = []
        if campaign_status not in {None, "complete"}:
            errors.append(f"campaign_completeness:{campaign_status}")
        if continuity_status not in {None, "continuous"}:
            errors.append(f"observation_continuity:{continuity_status}")
        status = "complete" if not errors else "incomplete"
        return status, errors

    def _register_source(self, event: dict[str, Any]) -> None:
        canonical = json.dumps(event, sort_keys=True, separators=(",", ":"))
        first_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        try:
            self.core.register_stream_source(
                self.source_id,
                str(self.session_path),
                first_hash,
                event["timestamp"],
            )
        except ValueError as exc:
            raise V5StreamValidationError(str(exc)) from exc

    @staticmethod
    def _decode_event(raw_line: bytes, event_index: int) -> dict[str, Any]:
        try:
            decoded = raw_line.decode("utf-8")
            event = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise V5StreamValidationError(
                f"event {event_index} is not valid UTF-8 JSON"
            ) from exc
        if not isinstance(event, dict):
            raise V5StreamValidationError(f"event {event_index} is not an object")
        return event

    @staticmethod
    def _validate_event(event: dict[str, Any], event_index: int) -> datetime:
        kind = event.get("event")
        timestamp_text = event.get("timestamp")
        payload = event.get("payload")
        if not isinstance(kind, str) or not kind:
            raise V5StreamValidationError(f"event {event_index} has no event type")
        if not isinstance(timestamp_text, str):
            raise V5StreamValidationError(f"event {event_index} has no timestamp")
        try:
            timestamp = datetime.fromisoformat(timestamp_text)
        except ValueError as exc:
            raise V5StreamValidationError(
                f"event {event_index} has an invalid timestamp"
            ) from exc
        if timestamp.tzinfo is None:
            raise V5StreamValidationError(
                f"event {event_index} timestamp is not timezone-aware"
            )
        if not isinstance(payload, dict):
            raise V5StreamValidationError(f"event {event_index} payload is not an object")
        if kind == "polymarket_snapshot":
            V5JsonlPaperAdapter._require_fields(
                payload,
                ("market_id", "asset", "yes_price", "no_price", "seconds_to_expiry"),
                event_index,
            )
            if payload["asset"] not in {"BTC", "ETH", "SOL"}:
                raise V5StreamValidationError(
                    f"event {event_index} has an unsupported asset"
                )
            for name in ("yes_price", "no_price", "seconds_to_expiry"):
                try:
                    value = float(payload[name])
                except (TypeError, ValueError) as exc:
                    raise V5StreamValidationError(
                        f"event {event_index} has invalid {name}"
                    ) from exc
                if not math.isfinite(value):
                    raise V5StreamValidationError(
                        f"event {event_index} has non-finite {name}"
                    )
                if name in {"yes_price", "no_price"} and not 0.0 <= value <= 1.0:
                    raise V5StreamValidationError(
                        f"event {event_index} has out-of-range {name}"
                    )
                if name == "seconds_to_expiry" and value < 0.0:
                    raise V5StreamValidationError(
                        f"event {event_index} has negative seconds_to_expiry"
                    )
        elif kind == "lag_measurement":
            V5JsonlPaperAdapter._require_fields(
                payload, ("market_id", "measurement"), event_index
            )
            measurement = payload["measurement"]
            if not isinstance(measurement, dict):
                raise V5StreamValidationError(
                    f"event {event_index} measurement is not an object"
                )
            V5JsonlPaperAdapter._require_fields(
                measurement,
                (
                    "confidence",
                    "direction",
                    "external_price_change",
                    "lag_score",
                    "polymarket_yes_price_change",
                    "qualified",
                    "reason",
                ),
                event_index,
            )
            if measurement["direction"] not in {"UP", "DOWN", "NONE"}:
                raise V5StreamValidationError(
                    f"event {event_index} has invalid detector direction"
                )
            if not isinstance(measurement["reason"], str):
                raise V5StreamValidationError(
                    f"event {event_index} has invalid detector reason"
                )
            if not isinstance(measurement["qualified"], bool):
                raise V5StreamValidationError(
                    f"event {event_index} has invalid qualified flag"
                )
            for name in (
                "confidence",
                "external_price_change",
                "lag_score",
                "polymarket_yes_price_change",
            ):
                try:
                    value = float(measurement[name])
                except (TypeError, ValueError) as exc:
                    raise V5StreamValidationError(
                        f"event {event_index} has invalid detector {name}"
                    ) from exc
                if not math.isfinite(value):
                    raise V5StreamValidationError(
                        f"event {event_index} has non-finite detector {name}"
                    )
        return timestamp

    @staticmethod
    def _require_fields(
        payload: dict[str, Any], fields: tuple[str, ...], event_index: int
    ) -> None:
        missing = [field for field in fields if field not in payload]
        if missing:
            names = ", ".join(missing)
            raise V5StreamValidationError(
                f"event {event_index} is missing required fields: {names}"
            )
