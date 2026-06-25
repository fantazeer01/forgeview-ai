from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from polymarket.edge_engine_v4.opportunity import CryptoMarket


class MarketLifecycleState(str, Enum):
    WAITING_FOR_NEXT_WINDOW = "waiting_for_next_window"
    NEWLY_OPENED = "newly_opened"
    ACTIVE = "active"
    NEAR_EXPIRY = "near_expiry"
    CLOSED = "closed"
    QUOTE_UNAVAILABLE = "quote_unavailable"


@dataclass
class MarketLifecycleRecord:
    market: CryptoMarket
    state: MarketLifecycleState
    first_seen_timestamp: datetime
    first_quote_timestamp: datetime | None = None
    seconds_after_open_when_detected: float = 0.0
    quote_errors: int = 0
    updated_at: datetime | None = None

    def time_left(self, timestamp: datetime) -> float:
        return max(0.0, (self.market.window_end - timestamp).total_seconds())

    @property
    def caught_early(self) -> bool:
        return self.seconds_after_open_when_detected <= 15.0


@dataclass(frozen=True)
class LifecycleEvent:
    timestamp: datetime
    asset: str
    market_id: str
    question: str
    event: str
    previous_state: str
    current_state: str
    window_start: datetime
    window_end: datetime
    time_left_seconds: float
    first_seen_timestamp: datetime
    first_quote_timestamp: datetime | None
    seconds_after_open_when_detected: float
    quote_available: bool
    reason: str = ""


class MarketLifecycleTracker:
    def __init__(
        self,
        assets: tuple[str, ...],
        newly_opened_seconds: float = 15.0,
        near_expiry_seconds: float = 60.0,
    ) -> None:
        self.assets = assets
        self.newly_opened_seconds = newly_opened_seconds
        self.near_expiry_seconds = near_expiry_seconds
        self.records: dict[str, MarketLifecycleRecord] = {}
        self.current_by_asset: dict[str, str] = {}
        self.events: list[LifecycleEvent] = []
        self.rollover_count = 0

    def ingest(self, markets: list[CryptoMarket], timestamp: datetime) -> list[LifecycleEvent]:
        emitted: list[LifecycleEvent] = []
        for market in markets:
            if market.market_id in self.records:
                continue
            delay = max(0.0, (timestamp - market.window_start).total_seconds())
            record = MarketLifecycleRecord(
                market=market,
                state=self._state_for(market, timestamp),
                first_seen_timestamp=timestamp,
                seconds_after_open_when_detected=delay,
                updated_at=timestamp,
            )
            self.records[market.market_id] = record
            emitted.append(self._event(record, timestamp, "detected", record.state, record.state))
        self.events.extend(emitted)
        emitted.extend(self.update(timestamp))
        return emitted

    def update(self, timestamp: datetime) -> list[LifecycleEvent]:
        emitted: list[LifecycleEvent] = []
        for record in self.records.values():
            previous = record.state
            calculated = self._state_for(record.market, timestamp)
            if previous is MarketLifecycleState.QUOTE_UNAVAILABLE and calculated not in {
                MarketLifecycleState.CLOSED,
                MarketLifecycleState.WAITING_FOR_NEXT_WINDOW,
            }:
                calculated = MarketLifecycleState.QUOTE_UNAVAILABLE
            record.state = calculated
            record.updated_at = timestamp
            if calculated is not previous:
                emitted.append(self._event(
                    record, timestamp, "state_changed", previous, calculated
                ))

        for asset in self.assets:
            selected = self._select_for_asset(asset, timestamp)
            selected_id = selected.market.market_id if selected else ""
            previous_id = self.current_by_asset.get(asset, "")
            if selected_id != previous_id:
                if previous_id and selected_id:
                    self.rollover_count += 1
                    emitted.append(self._event(
                        selected,
                        timestamp,
                        "rollover",
                        self.records[previous_id].state,
                        selected.state,
                        reason=f"{previous_id}->{selected_id}",
                    ))
                self.current_by_asset[asset] = selected_id
        self.events.extend(emitted)
        return emitted

    def current_markets(self, timestamp: datetime) -> list[MarketLifecycleRecord]:
        self.update(timestamp)
        rows = []
        for asset in self.assets:
            market_id = self.current_by_asset.get(asset)
            if market_id:
                record = self.records[market_id]
                if record.market.window_start <= timestamp < record.market.window_end:
                    rows.append(record)
        return rows

    def mark_quote_available(
        self, market_id: str, timestamp: datetime
    ) -> list[LifecycleEvent]:
        record = self.records[market_id]
        previous = record.state
        if record.first_quote_timestamp is None:
            record.first_quote_timestamp = timestamp
        record.state = self._state_for(record.market, timestamp)
        record.updated_at = timestamp
        if record.state is previous:
            return []
        event = self._event(
            record, timestamp, "quote_recovered", previous, record.state
        )
        self.events.append(event)
        return [event]

    def mark_quote_unavailable(
        self, market_id: str, timestamp: datetime, reason: str
    ) -> list[LifecycleEvent]:
        record = self.records[market_id]
        previous = record.state
        record.state = MarketLifecycleState.QUOTE_UNAVAILABLE
        record.quote_errors += 1
        record.updated_at = timestamp
        if previous is MarketLifecycleState.QUOTE_UNAVAILABLE:
            return []
        event = self._event(
            record,
            timestamp,
            "quote_unavailable",
            previous,
            record.state,
            reason=reason,
        )
        self.events.append(event)
        return [event]

    def summary(self) -> dict[str, float | int]:
        records = list(self.records.values())
        delays = [row.seconds_after_open_when_detected for row in records]
        return {
            "markets_detected": len(records),
            "average_detection_delay_seconds": (
                round(sum(delays) / len(delays), 3) if delays else 0.0
            ),
            "markets_caught_within_15_seconds": sum(delay <= 15 for delay in delays),
            "markets_caught_after_60_seconds": sum(delay > 60 for delay in delays),
            "quote_error_count": sum(row.quote_errors for row in records),
            "rollover_count": self.rollover_count,
        }

    def _select_for_asset(
        self, asset: str, timestamp: datetime
    ) -> MarketLifecycleRecord | None:
        active = [
            row for row in self.records.values()
            if row.market.asset == asset
            and row.market.window_start <= timestamp < row.market.window_end
        ]
        if active:
            return max(active, key=lambda row: row.market.window_start)
        upcoming = [
            row for row in self.records.values()
            if row.market.asset == asset and row.market.window_start > timestamp
        ]
        return min(upcoming, key=lambda row: row.market.window_start) if upcoming else None

    def _state_for(
        self, market: CryptoMarket, timestamp: datetime
    ) -> MarketLifecycleState:
        if timestamp < market.window_start:
            return MarketLifecycleState.WAITING_FOR_NEXT_WINDOW
        if timestamp >= market.window_end:
            return MarketLifecycleState.CLOSED
        elapsed = (timestamp - market.window_start).total_seconds()
        remaining = (market.window_end - timestamp).total_seconds()
        if elapsed <= self.newly_opened_seconds:
            return MarketLifecycleState.NEWLY_OPENED
        if remaining <= self.near_expiry_seconds:
            return MarketLifecycleState.NEAR_EXPIRY
        return MarketLifecycleState.ACTIVE

    def _event(
        self,
        record: MarketLifecycleRecord,
        timestamp: datetime,
        event: str,
        previous: MarketLifecycleState,
        current: MarketLifecycleState,
        reason: str = "",
    ) -> LifecycleEvent:
        return LifecycleEvent(
            timestamp=timestamp,
            asset=record.market.asset,
            market_id=record.market.market_id,
            question=record.market.question,
            event=event,
            previous_state=previous.value,
            current_state=current.value,
            window_start=record.market.window_start,
            window_end=record.market.window_end,
            time_left_seconds=record.time_left(timestamp),
            first_seen_timestamp=record.first_seen_timestamp,
            first_quote_timestamp=record.first_quote_timestamp,
            seconds_after_open_when_detected=record.seconds_after_open_when_detected,
            quote_available=current is not MarketLifecycleState.QUOTE_UNAVAILABLE,
            reason=reason,
        )
