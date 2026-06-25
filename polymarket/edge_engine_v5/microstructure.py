from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from polymarket.edge_engine_v4.opportunity import PolymarketSnapshot


MICROSTRUCTURE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class MicrostructureSnapshot:
    schema_version: int
    timestamp: datetime
    market_id: str
    asset: str
    quote_timestamp: datetime | None
    quote_age_seconds: float | None
    refresh_latency_seconds: float | None
    time_since_last_quote_update_seconds: float | None
    yes_price: float
    no_price: float
    yes_bid: float
    yes_ask: float
    bid_ask_spread: float
    yes_bid_size: float | None
    yes_ask_size: float | None
    total_bid_depth: float | None
    total_ask_depth: float | None
    book_imbalance: float | None
    repricing_velocity: float | None
    repricing_acceleration: float | None
    yes_change_frequency_30s: float
    no_change_frequency_30s: float
    consecutive_quote_stability: int
    spread_change: float | None
    spread_velocity: float | None
    spread_compression: float | None
    cross_asset_yes_dispersion: float | None
    cross_asset_relative_yes: float | None


class MicrostructureTracker:
    """Derives strictly as-of microstructure state from saved quote observations."""

    def __init__(self) -> None:
        self.history: dict[str, list[tuple[datetime, float, float]]] = {}
        self.latest_by_asset: dict[str, tuple[datetime, float]] = {}
        self.last_quote_timestamp: dict[str, datetime] = {}
        self.last_fingerprint: dict[str, tuple] = {}
        self.last_change_observed: dict[str, datetime] = {}
        self.stability: dict[str, int] = {}

    def observe(
        self, snapshot: PolymarketSnapshot, observed_at: datetime
    ) -> MicrostructureSnapshot:
        history = self.history.setdefault(snapshot.market_id, [])
        spread = snapshot.yes_ask - snapshot.yes_bid
        previous = history[-1] if history else None
        prior = history[-2] if len(history) >= 2 else None
        fingerprint = (
            snapshot.yes_price, snapshot.yes_bid, snapshot.yes_ask,
            snapshot.total_bid_depth, snapshot.total_ask_depth,
        )
        changed = self.last_fingerprint.get(snapshot.market_id) != fingerprint
        if changed:
            self.last_fingerprint[snapshot.market_id] = fingerprint
            self.last_change_observed[snapshot.market_id] = observed_at
        self.stability[snapshot.market_id] = (
            1 if changed else self.stability.get(snapshot.market_id, 1) + 1
        )
        quote_timestamp = snapshot.quote_timestamp
        last_quote = self.last_quote_timestamp.get(snapshot.market_id)
        quote_age = (
            max(0.0, (observed_at - quote_timestamp).total_seconds())
            if quote_timestamp else None
        )
        since_update = (
            max(0.0, (
                observed_at - self.last_change_observed[snapshot.market_id]
            ).total_seconds())
            if snapshot.market_id in self.last_change_observed else None
        )
        if quote_timestamp:
            self.last_quote_timestamp[snapshot.market_id] = quote_timestamp
        velocity = _slope(previous, (observed_at, snapshot.yes_price, spread), 1)
        previous_velocity = _slope(
            prior, previous, 1
        ) if prior and previous else None
        acceleration = (
            (velocity - previous_velocity)
            / max(1e-9, (observed_at - previous[0]).total_seconds())
            if velocity is not None and previous_velocity is not None and previous
            else None
        )
        spread_change = spread - previous[2] if previous else None
        spread_velocity = _slope(previous, (observed_at, snapshot.yes_price, spread), 2)
        depth_total = (
            snapshot.total_bid_depth + snapshot.total_ask_depth
            if snapshot.total_bid_depth is not None
            and snapshot.total_ask_depth is not None else None
        )
        imbalance = (
            (snapshot.total_bid_depth - snapshot.total_ask_depth) / depth_total
            if depth_total not in (None, 0) else None
        )
        cutoff = observed_at - timedelta(seconds=30)
        recent = [
            row for row in history if row[0] >= cutoff
        ] + [(observed_at, snapshot.yes_price, spread)]
        changes = sum(
            current[1] != previous_row[1]
            for previous_row, current in zip(recent, recent[1:])
        )
        self.latest_by_asset[snapshot.asset] = (observed_at, snapshot.yes_price)
        synchronized = [
            price for timestamp, price in self.latest_by_asset.values()
            if 0 <= (observed_at - timestamp).total_seconds() <= 5
        ]
        dispersion = (
            max(synchronized) - min(synchronized)
            if len(synchronized) >= 2 else None
        )
        relative = (
            snapshot.yes_price - sum(synchronized) / len(synchronized)
            if len(synchronized) >= 2 else None
        )
        event = MicrostructureSnapshot(
            schema_version=MICROSTRUCTURE_SCHEMA_VERSION,
            timestamp=observed_at,
            market_id=snapshot.market_id,
            asset=snapshot.asset,
            quote_timestamp=quote_timestamp,
            quote_age_seconds=quote_age,
            refresh_latency_seconds=snapshot.source_latency_seconds,
            time_since_last_quote_update_seconds=since_update,
            yes_price=snapshot.yes_price,
            no_price=snapshot.no_price,
            yes_bid=snapshot.yes_bid,
            yes_ask=snapshot.yes_ask,
            bid_ask_spread=spread,
            yes_bid_size=snapshot.yes_bid_size,
            yes_ask_size=snapshot.yes_ask_size,
            total_bid_depth=snapshot.total_bid_depth,
            total_ask_depth=snapshot.total_ask_depth,
            book_imbalance=imbalance,
            repricing_velocity=velocity,
            repricing_acceleration=acceleration,
            yes_change_frequency_30s=changes / 30.0,
            no_change_frequency_30s=changes / 30.0,
            consecutive_quote_stability=self.stability[snapshot.market_id],
            spread_change=spread_change,
            spread_velocity=spread_velocity,
            spread_compression=-spread_change if spread_change is not None else None,
            cross_asset_yes_dispersion=dispersion,
            cross_asset_relative_yes=relative,
        )
        history.append((observed_at, snapshot.yes_price, spread))
        return event


def _slope(previous, current, value_index):
    if not previous or not current:
        return None
    seconds = (current[0] - previous[0]).total_seconds()
    if seconds <= 0:
        return None
    return (current[value_index] - previous[value_index]) / seconds


def microstructure_coverage(events: list[MicrostructureSnapshot]) -> dict:
    fields = (
        "quote_timestamp", "quote_age_seconds", "refresh_latency_seconds",
        "yes_bid_size", "yes_ask_size", "total_bid_depth", "total_ask_depth",
        "book_imbalance", "repricing_velocity", "repricing_acceleration",
        "bid_ask_spread", "spread_change", "spread_velocity",
        "spread_compression", "cross_asset_yes_dispersion",
        "cross_asset_relative_yes",
    )
    total = len(events)
    return {
        "schema_version": MICROSTRUCTURE_SCHEMA_VERSION,
        "events": total,
        "field_coverage_percentage": {
            field: round(
                sum(getattr(event, field) is not None for event in events)
                / total * 100.0,
                4,
            ) if total else 0.0
            for field in fields
        },
        "by_asset": {
            asset: sum(event.asset == asset for event in events)
            for asset in ("BTC", "ETH", "SOL")
        },
    }
