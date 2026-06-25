from __future__ import annotations

from dataclasses import dataclass
from typing import TextIO
import sys

from polymarket.edge_engine_v4.opportunity import (
    CryptoMarket,
    Direction,
    LagMeasurement,
    PolymarketSnapshot,
    ReferencePrice,
)
from .market_lifecycle import MarketLifecycleRecord, MarketLifecycleState


@dataclass(frozen=True)
class LiveSignal:
    market: CryptoMarket
    reference: ReferencePrice | None
    snapshot: PolymarketSnapshot | None
    measurement: LagMeasurement | None
    action: str
    reason: str
    lifecycle_state: str = "active"
    detected_after_open_seconds: float = 0.0
    window_phase: str = "active"


class LiveConsole:
    def __init__(
        self,
        quiet: bool = False,
        show_skipped: bool = False,
        stream: TextIO | None = None,
    ) -> None:
        self.quiet = quiet
        self.show_skipped = show_skipped
        self.stream = stream or sys.stdout
        self.cycles = 0
        self.signals = 0

    def cycle_started(self) -> None:
        self.cycles += 1

    def emit(self, signal: LiveSignal) -> None:
        if self.quiet:
            return
        if signal.action == "SKIP" and not self.show_skipped:
            return
        if signal.action.startswith("BUY"):
            self.signals += 1
        print(format_live_signal(signal), file=self.stream, flush=True)


def format_live_signal(signal: LiveSignal) -> str:
    market = signal.market
    snapshot = signal.snapshot
    reference = signal.reference
    measurement = signal.measurement
    timestamp = (
        snapshot.timestamp if snapshot
        else reference.timestamp if reference
        else market.window_start
    )
    seconds_left = snapshot.seconds_to_expiry if snapshot else max(
        0.0, (market.window_end - timestamp).total_seconds()
    )
    external_direction = (
        "FLAT"
        if not measurement or measurement.direction is Direction.NONE
        else measurement.direction.value
    )
    external_move = (
        measurement.external_price_change * 100.0 if measurement else 0.0
    )
    market_move = (
        measurement.polymarket_yes_price_change if measurement else 0.0
    )
    yes_price = f"{snapshot.yes_price:.3f}" if snapshot else "N/A"
    no_price = f"{snapshot.no_price:.3f}" if snapshot else "N/A"
    external_price = f"{reference.price:,.4f}" if reference else "N/A"
    lag_score = f"{measurement.lag_score:.3f}" if measurement else "N/A"
    confidence = f"{measurement.confidence:.1%}" if measurement else "N/A"
    shadow_suffix = " (shadow)" if signal.action.startswith("BUY") else ""
    return (
        f"[{timestamp:%H:%M:%S}] {market.asset} 5m\n"
        f"Lifecycle: {signal.lifecycle_state}\n"
        f"Detected after open: {signal.detected_after_open_seconds:.1f}s\n"
        f"Window: {signal.window_phase}\n"
        f"Market: {market.question}\n"
        f"Time left: {_format_duration(seconds_left)} | Expiry: {market.window_end:%H:%M:%S UTC}\n"
        f"External price: {external_price}\n"
        f"External: {external_direction} {external_move:+.3f}%\n"
        f"Polymarket YES: {yes_price} | NO: {no_price} | Move: {market_move:+.3f}\n"
        f"Lag score: {lag_score} | Confidence: {confidence}\n"
        f"Action: {signal.action}{shadow_suffix}\n"
        f"Reason: {signal.reason}\n"
    )


def signal_from_measurement(
    market: CryptoMarket,
    reference: ReferencePrice,
    snapshot: PolymarketSnapshot,
    measurement: LagMeasurement,
    opportunity_accepted: bool,
    lifecycle: MarketLifecycleRecord | None = None,
) -> LiveSignal:
    if measurement.qualified and opportunity_accepted:
        action = "BUY YES" if measurement.direction is Direction.UP else "BUY NO"
        reason = (
            f"{market.asset} moved {measurement.direction.value.lower()}, "
            "Polymarket has not fully repriced"
        )
    elif measurement.qualified:
        action = "HOLD"
        reason = "lag persists, but the shadow signal was already recorded for this market"
    elif measurement.reason == "polymarket_already_repriced":
        action, reason = "HOLD", "Polymarket already repriced"
    elif measurement.reason == "external_move_below_threshold":
        action, reason = "HOLD", "weak external move"
    elif measurement.reason == "confidence_below_threshold":
        action, reason = "HOLD", "insufficient confidence"
    elif measurement.reason == "liquidity_below_minimum":
        action, reason = "SKIP", "low liquidity"
    elif measurement.reason == "near_expiry_insufficient_time":
        action, reason = "SKIP", "too close to expiry"
    elif measurement.reason == "late_entry_window":
        action, reason = "SKIP", "late window: entries disabled with less than 60 seconds remaining"
    else:
        action, reason = "SKIP", measurement.reason.replace("_", " ")
    state, delay, phase = _lifecycle_fields(lifecycle, snapshot.seconds_to_expiry)
    return LiveSignal(
        market, reference, snapshot, measurement, action, reason,
        state, delay, phase,
    )


def skipped_signal(
    market: CryptoMarket,
    reason: str,
    reference: ReferencePrice | None = None,
    lifecycle: MarketLifecycleRecord | None = None,
) -> LiveSignal:
    readable = {
        "missing_reference_price": "insufficient data: missing external reference",
        "liquidity_below_minimum": "low liquidity",
    }.get(reason, reason.replace("_", " "))
    seconds_left = (
        max(0.0, (market.window_end - reference.timestamp).total_seconds())
        if reference else 0.0
    )
    state, delay, phase = _lifecycle_fields(lifecycle, seconds_left)
    return LiveSignal(
        market, reference, None, None, "SKIP", readable,
        state, delay, phase,
    )


class LifecycleConsole(LiveConsole):
    def emit(self, signal: LiveSignal) -> None:
        if self.quiet:
            return
        print(format_lifecycle_signal(signal), file=self.stream, flush=True)


def format_lifecycle_signal(signal: LiveSignal) -> str:
    market = signal.market
    timestamp = (
        signal.snapshot.timestamp if signal.snapshot
        else signal.reference.timestamp if signal.reference
        else market.window_start
    )
    seconds_left = (
        signal.snapshot.seconds_to_expiry if signal.snapshot
        else max(0.0, (market.window_end - timestamp).total_seconds())
    )
    quote = "available" if signal.snapshot else "unavailable"
    return (
        f"[{timestamp:%H:%M:%S}] {market.asset} 5m lifecycle\n"
        f"State: {signal.lifecycle_state}\n"
        f"Market: {market.question}\n"
        f"Time left: {_format_duration(seconds_left)}\n"
        f"Detected after open: {signal.detected_after_open_seconds:.1f}s\n"
        f"Window timing: {signal.window_phase}\n"
        f"Quote: {quote}\n"
    )


def _lifecycle_fields(
    lifecycle: MarketLifecycleRecord | None,
    seconds_left: float,
) -> tuple[str, float, str]:
    if lifecycle:
        state = lifecycle.state.value
        delay = lifecycle.seconds_after_open_when_detected
    else:
        state = MarketLifecycleState.ACTIVE.value
        delay = 0.0
    phase = (
        "early" if delay <= 15 and seconds_left >= 285
        else "late" if seconds_left < 60 or delay > 60
        else "active"
    )
    return state, delay, phase


def _format_duration(seconds: float) -> str:
    total = max(0, int(seconds))
    minutes, remainder = divmod(total, 60)
    return f"{minutes:02d}:{remainder:02d}"
