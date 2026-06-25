from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from polymarket.edge_engine_v4.config import ScannerConfig
from polymarket.edge_engine.models import MarketSnapshot
from polymarket.edge_engine_v3.shadow import ShadowExecutionEngine
from polymarket.edge_engine_v4.crypto_reference import PublicCryptoReferenceFeed
from polymarket.edge_engine_v4.lag_detector import LagDetector
from polymarket.edge_engine_v4.market_discovery import PolymarketMarketDiscovery
from polymarket.edge_engine_v4.opportunity import (
    CryptoMarket,
    Direction,
    Opportunity,
    PolymarketSnapshot,
    ReferencePrice,
    SkippedMarket,
)
from polymarket.edge_engine_v4.scanner import (
    PolymarketQuoteFeed,
    V3OpportunityAdapter,
)

from .config import CaptureConfig
from .evidence import EvidenceVerdict, OpportunityGate, evidence_verdict
from .market_rotation import (
    Lifecycle,
    MarketRotation,
    MockRotatingDiscovery,
)
from .metrics import aggregate_metrics
from .report import EventStore, update_latest, write_evidence_artifacts
from .scheduler import CaptureScheduler, discovery_due
from .continuity import observation_continuity
from .async_feeds import (
    AsyncDiscovery, AsyncQuoteFeed, AsyncReferenceFeed, close_async_feeds,
)
from .live_console import LiveConsole, signal_from_measurement, skipped_signal
from .market_lifecycle import (
    LifecycleEvent,
    MarketLifecycleState,
    MarketLifecycleTracker,
)
from .microstructure import MicrostructureTracker
from .microstructure import (
    MICROSTRUCTURE_SCHEMA_VERSION, microstructure_coverage,
)


class MockLongQuoteFeed:
    """Deterministic quote paths reset for every five-minute market."""

    def fetch(self, market: CryptoMarket, timestamp: datetime) -> PolymarketSnapshot:
        elapsed = max(0.0, (timestamp - market.window_start).total_seconds())
        phase = min(5, int(elapsed // 60))
        paths = {
            "BTC": (0.50, 0.50, 0.505, 0.53, 0.61, 0.66),
            "ETH": (0.50, 0.50, 0.495, 0.47, 0.39, 0.34),
            "SOL": (0.50, 0.50, 0.50, 0.52, 0.60, 0.64),
        }
        price = paths[market.asset][phase]
        return PolymarketSnapshot(
            timestamp=timestamp,
            market_id=market.market_id,
            asset=market.asset,
            yes_price=price,
            no_price=1.0 - price,
            yes_bid=max(0.001, price - 0.01),
            yes_ask=min(0.999, price + 0.01),
            liquidity=market.liquidity,
            seconds_to_expiry=max(0.0, (market.window_end - timestamp).total_seconds()),
            quote_timestamp=timestamp,
            yes_bid_size=600.0 + phase * 15.0,
            yes_ask_size=550.0 - phase * 10.0,
            total_bid_depth=2_500.0 + phase * 40.0,
            total_ask_depth=2_300.0 - phase * 30.0,
            source_latency_seconds=0.001,
        )


class MockLongReferenceFeed:
    BASE = {"BTC": 60_000.0, "ETH": 3_000.0, "SOL": 140.0}

    def fetch(self, assets: tuple[str, ...], timestamp: datetime) -> list[ReferencePrice]:
        phase = min(4, int(timestamp.timestamp() % 300 // 60))
        moves = (0.0, 0.0002, 0.0030, 0.0034, 0.0035)
        window = int(timestamp.timestamp()) // 300
        drift = (window % 20) * 0.0001
        rows = []
        for asset in assets:
            direction = -1.0 if asset == "ETH" else 1.0
            price = self.BASE[asset] * (1.0 + drift + direction * moves[phase])
            rows.append(ReferencePrice(timestamp, asset, round(price, 8), "mock"))
        return rows


class LongShadowAdapter(V3OpportunityAdapter):
    """Adds post-entry observations while preserving v3 shadow execution."""

    def __init__(self, poll_interval_seconds: float = 1.0) -> None:
        super().__init__()
        timeout_updates = max(4, round(60.0 / poll_interval_seconds))
        self.shadow = ShadowExecutionEngine(timeout_updates=timeout_updates)

    def observe(
        self,
        market: CryptoMarket,
        snapshot: PolymarketSnapshot,
        baseline_market: PolymarketSnapshot,
        external_change: float,
    ) -> bool:
        if market.market_id not in self.shadow.positions:
            return False
        sign = 1.0 if external_change >= 0 else -1.0
        expected_move = min(0.30, abs(external_change * 10_000.0) / 1000.0)
        reference = max(
            0.001,
            min(0.999, baseline_market.yes_price + sign * expected_move),
        )
        self.shadow.on_snapshot(MarketSnapshot(
            timestamp=snapshot.timestamp,
            market_id=market.market_id,
            question=market.question,
            yes_price=snapshot.yes_price,
            reference_probability=reference,
            volume_spike=0.20,
            momentum=0.20,
            stability=0.80,
        ))
        return True


class LongShadowCapture:
    def __init__(
        self,
        config: CaptureConfig,
        discovery=None,
        reference_feed=None,
        quote_feed=None,
        live_console: LiveConsole | None = None,
    ) -> None:
        self.config = config
        self.discovery = discovery
        self.reference_feed = reference_feed
        self.quote_feed = quote_feed
        self.live_console = live_console

    def run(self) -> tuple[Path, dict]:
        mode = "mock" if self.config.mock else "public"
        fallback_reason = ""
        mock_mode = self.config.mock
        start = (
            datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
            if mock_mode else datetime.now(timezone.utc)
        )
        session_dir = _allocate_session_dir(self.config.output_root)
        session_dir.mkdir(parents=True, exist_ok=False)
        stdout_log = session_dir / "campaign.stdout.log"
        stderr_log = session_dir / "campaign.stderr.log"
        stdout_log.write_text(
            f"capture_start_utc={start.isoformat()}\n", encoding="utf-8"
        )
        stderr_log.write_text("", encoding="utf-8")
        store = EventStore(session_dir)
        store.append("session_started", start, {
            "mode": mode,
            "assets": self.config.assets,
            "duration_seconds": self.config.duration_seconds,
            "poll_interval_seconds": self.config.poll_interval_seconds,
            "near_expiry_seconds": self.config.near_expiry_seconds,
            "min_entry_seconds_remaining": self.config.min_entry_seconds_remaining,
            "min_liquidity": self.config.min_liquidity,
            "external_move_threshold_bps": self.config.external_move_threshold_bps,
            "repricing_ratio": self.config.repricing_ratio,
            "min_confidence": self.config.min_confidence,
            "min_completed_windows": self.config.min_completed_windows,
            "min_shadow_trades": self.config.min_shadow_trades,
            "min_reference_coverage": self.config.min_reference_coverage,
            "max_data_gap": self.config.max_data_gap,
            "max_drawdown": self.config.max_drawdown,
            "max_edge_decay": self.config.max_edge_decay,
            "max_latency_sensitivity": self.config.max_latency_sensitivity,
            "lifecycle_only": self.config.lifecycle_only,
            "microstructure_schema_version": MICROSTRUCTURE_SCHEMA_VERSION,
        })

        discovery = self.discovery or (
            MockRotatingDiscovery() if mock_mode
            else PolymarketMarketDiscovery(self.config.request_timeout_seconds)
        )
        reference_feed = self.reference_feed or (
            MockLongReferenceFeed() if mock_mode
            else PublicCryptoReferenceFeed(self.config.request_timeout_seconds)
        )
        quote_feed = self.quote_feed or (
            MockLongQuoteFeed() if mock_mode
            else PolymarketQuoteFeed(self.config.request_timeout_seconds)
        )
        if not mock_mode:
            discovery = AsyncDiscovery(discovery)
            reference_feed = AsyncReferenceFeed(reference_feed)
            quote_feed = AsyncQuoteFeed(quote_feed, workers=len(self.config.assets))
        rotation = MarketRotation(self.config.near_expiry_seconds)
        lifecycle_tracker = MarketLifecycleTracker(
            self.config.assets,
            newly_opened_seconds=15.0,
            near_expiry_seconds=self.config.min_entry_seconds_remaining,
        )
        lag_config = ScannerConfig(
            assets=self.config.assets,
            duration_seconds=self.config.duration_seconds,
            poll_interval_seconds=self.config.poll_interval_seconds,
            min_liquidity=self.config.min_liquidity,
            min_seconds_to_expiry=self.config.near_expiry_seconds,
            external_move_threshold_bps=self.config.external_move_threshold_bps,
            repricing_ratio=self.config.repricing_ratio,
            min_confidence=self.config.min_confidence,
            mock=mock_mode,
        )
        detector = LagDetector(lag_config)
        adapter = LongShadowAdapter(self.config.poll_interval_seconds)
        opportunities: list[Opportunity] = []
        opportunity_gate = OpportunityGate()
        skipped: list[SkippedMarket] = []
        baseline_refs: dict[str, ReferencePrice] = {}
        baseline_markets: dict[str, PolymarketSnapshot] = {}
        microstructure_tracker = MicrostructureTracker()
        microstructure_events = []
        expected_refs = successful_refs = 0
        expected_market_points = successful_market_points = 0
        last_discovery: datetime | None = None
        discovery_failures: list[dict] = []
        checkpoint_timestamps: list[datetime] = []

        scheduler = CaptureScheduler(
            self.config.duration_seconds,
            self.config.poll_interval_seconds,
            mock_mode,
            mock_start=start,
        )
        for _, timestamp in scheduler.ticks():
            if self.live_console:
                self.live_console.cycle_started()
            if discovery_due(timestamp, last_discovery, self.config.discovery_interval_seconds):
                try:
                    discovered, discovery_skips = discovery.discover(self.config.assets, timestamp)
                except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
                    discovered, discovery_skips = [], []
                    failure = {
                        "timestamp": timestamp.isoformat(),
                        "endpoint_url": getattr(exc, "url", "unknown"),
                        "exception_type": type(exc).__name__,
                        "exception_message": str(exc),
                    }
                    discovery_failures.append(failure)
                    store.append("discovery_failure", timestamp, failure)
                    with stderr_log.open("a", encoding="utf-8") as handle:
                        handle.write(
                            f"{timestamp.isoformat()} discovery_failure "
                            f"{type(exc).__name__}: {exc}\n"
                        )
                for failure_row in getattr(discovery, "failures", []):
                    failure = {
                        "timestamp": failure_row.timestamp.isoformat(),
                        "endpoint_url": failure_row.endpoint_url,
                        "exception_type": failure_row.exception_type,
                        "exception_message": failure_row.exception_message,
                    }
                    discovery_failures.append(failure)
                    store.append("discovery_failure", timestamp, failure)
                    with stderr_log.open("a", encoding="utf-8") as handle:
                        handle.write(
                            f"{failure['timestamp']} discovery_failure "
                            f"{failure['exception_type']}: "
                            f"{failure['exception_message']} "
                            f"url={failure['endpoint_url']}\n"
                        )
                if (
                    not discovered
                    and self.config.allow_mock_fallback
                    and not mock_mode
                    and not rotation.markets
                ):
                    mock_mode = True
                    mode = "mock_fallback"
                    fallback_reason = fallback_reason or "no_live_five_minute_markets_found"
                    discovery = MockRotatingDiscovery()
                    reference_feed = MockLongReferenceFeed()
                    quote_feed = MockLongQuoteFeed()
                    discovered, discovery_skips = discovery.discover(self.config.assets, timestamp)
                    store.append("capture_mode_changed", timestamp, {
                        "mode": mode,
                        "reason": fallback_reason,
                    })
                for row in discovery_skips:
                    skipped.append(row)
                    store.append("skipped", timestamp, row)
                for tracked, previous, current in rotation.ingest(discovered, timestamp):
                    store.append("market_lifecycle", timestamp, {
                        "market": tracked.market,
                        "previous": previous.value,
                        "current": current.value,
                    })
                lifecycle_events = lifecycle_tracker.ingest(discovered, timestamp)
                _store_lifecycle_events(store, lifecycle_events)
                _reset_rollover_baselines(
                    lifecycle_events, baseline_refs, baseline_markets
                )
                for market in discovered:
                    if market.liquidity < self.config.min_liquidity:
                        previous_lifecycle = rotation.markets[market.market_id].lifecycle
                        rotation.mark_skipped(
                            market.market_id,
                            "liquidity_below_minimum",
                            timestamp,
                        )
                        row = SkippedMarket(
                            timestamp,
                            market.market_id,
                            market.asset,
                            market.question,
                            "liquidity_below_minimum",
                        )
                        skipped.append(row)
                        store.append("skipped", timestamp, row)
                        if self.live_console:
                            self.live_console.emit(skipped_signal(market, row.reason))
                        store.append("market_lifecycle", timestamp, {
                            "market_id": market.market_id,
                            "previous": previous_lifecycle.value,
                            "current": Lifecycle.SKIPPED.value,
                        })
                last_discovery = timestamp
            else:
                for tracked, previous, current in rotation.update(timestamp):
                    store.append("market_lifecycle", timestamp, {
                        "market_id": tracked.market.market_id,
                        "previous": previous.value,
                        "current": current.value,
                    })
                lifecycle_events = lifecycle_tracker.update(timestamp)
                _store_lifecycle_events(store, lifecycle_events)
                _reset_rollover_baselines(
                    lifecycle_events, baseline_refs, baseline_markets
                )

            expected_refs += len(self.config.assets)
            try:
                references = reference_feed.fetch(self.config.assets, timestamp)
            except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
                references = []
                fallback_reason = fallback_reason or f"reference_feed_error:{type(exc).__name__}"
            successful_refs += len(references)
            ref_by_asset = {row.asset: row for row in references}
            for reference in references:
                store.append("reference_price", timestamp, reference)

            lifecycle_event_index = len(lifecycle_tracker.events)
            current_records = lifecycle_tracker.current_markets(timestamp)
            _store_lifecycle_events(
                store, lifecycle_tracker.events[lifecycle_event_index:]
            )
            for lifecycle_record in current_records:
                market = lifecycle_record.market
                tracked = rotation.markets[market.market_id]
                if tracked.lifecycle is Lifecycle.SKIPPED:
                    continue
                expected_market_points += 1
                reference = ref_by_asset.get(market.asset)
                if reference is None:
                    row = SkippedMarket(
                        timestamp, market.market_id, market.asset,
                        market.question, "missing_reference_price",
                    )
                    skipped.append(row)
                    store.append("skipped", timestamp, row)
                    if self.live_console:
                        self.live_console.emit(skipped_signal(
                            market, row.reason, lifecycle=lifecycle_record
                        ))
                    continue
                try:
                    snapshot = quote_feed.fetch(market, timestamp)
                except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
                    lifecycle_events = lifecycle_tracker.mark_quote_unavailable(
                        market.market_id,
                        timestamp,
                        f"polymarket_quote_error:{type(exc).__name__}",
                    )
                    _store_lifecycle_events(store, lifecycle_events)
                    row = SkippedMarket(
                        timestamp, market.market_id, market.asset, market.question,
                        f"polymarket_quote_error:{type(exc).__name__}",
                    )
                    skipped.append(row)
                    store.append("skipped", timestamp, row)
                    if self.live_console and lifecycle_events:
                        self.live_console.emit(
                            skipped_signal(
                                market, row.reason, reference, lifecycle_record
                            )
                        )
                    continue
                lifecycle_events = lifecycle_tracker.mark_quote_available(
                    market.market_id, timestamp
                )
                _store_lifecycle_events(store, lifecycle_events)
                successful_market_points += 1
                tracked.snapshots += 1
                store.append("polymarket_snapshot", timestamp, snapshot)
                micro_event = microstructure_tracker.observe(snapshot, timestamp)
                microstructure_events.append(micro_event)
                store.append("microstructure_snapshot", timestamp, micro_event)
                if self.config.lifecycle_only:
                    if self.live_console:
                        self.live_console.emit(
                            skipped_signal(
                                market,
                                "lifecycle_observation",
                                reference,
                                lifecycle_record,
                            )
                        )
                    continue
                if (
                    market.market_id in baseline_refs
                    and baseline_refs[market.market_id].source != reference.source
                ):
                    previous_source = baseline_refs[market.market_id].source
                    baseline_refs[market.market_id] = reference
                    baseline_markets[market.market_id] = snapshot
                    row = SkippedMarket(
                        timestamp, market.market_id, market.asset, market.question,
                        f"reference_source_changed:{previous_source}->{reference.source}",
                    )
                    skipped.append(row)
                    store.append("skipped", timestamp, row)
                    if self.live_console:
                        self.live_console.emit(
                            skipped_signal(
                                market, row.reason, reference, lifecycle_record
                            )
                        )
                    continue
                baseline_refs.setdefault(market.market_id, reference)
                baseline_markets.setdefault(market.market_id, snapshot)
                measurement = detector.measure(
                    reference,
                    baseline_refs[market.market_id],
                    snapshot,
                    baseline_markets[market.market_id],
                )
                measurement = apply_entry_time_guard(
                    measurement,
                    snapshot,
                    self.config.min_entry_seconds_remaining,
                )
                store.append("lag_measurement", timestamp, {
                    "market_id": market.market_id,
                    "measurement": measurement,
                })
                if measurement.qualified:
                    opportunity = Opportunity(
                        asset=market.asset,
                        market_id=market.market_id,
                        question=market.question,
                        direction=measurement.direction,
                        yes_token_id=market.yes_token_id,
                        no_token_id=market.no_token_id,
                        external_move=measurement.external_price_change,
                        polymarket_move=measurement.polymarket_yes_price_change,
                        lag_score=measurement.lag_score,
                        confidence=measurement.confidence,
                        reason=measurement.reason,
                        timestamp=timestamp,
                    )
                    accepted = opportunity_gate.accept(opportunity)
                    if self.live_console:
                        self.live_console.emit(signal_from_measurement(
                            market, reference, snapshot, measurement, accepted,
                            lifecycle_record,
                        ))
                    if accepted:
                        tracked.opportunities += 1
                        opportunities.append(opportunity)
                        store.append("opportunity", timestamp, opportunity)
                        adapter.submit(opportunity, snapshot)
                        store.append("shadow_decision", timestamp, adapter.shadow.decisions[-1])
                    else:
                        row = SkippedMarket(
                            timestamp, market.market_id, market.asset,
                            market.question, "duplicate_opportunity_suppressed",
                        )
                        skipped.append(row)
                        store.append("skipped", timestamp, row)
                        if adapter.observe(
                            market,
                            snapshot,
                            baseline_markets[market.market_id],
                            measurement.external_price_change,
                        ):
                            store.append(
                                "shadow_decision",
                                timestamp,
                                adapter.shadow.decisions[-1],
                            )
                else:
                    if self.live_console:
                        self.live_console.emit(signal_from_measurement(
                            market, reference, snapshot, measurement, False,
                            lifecycle_record,
                        ))
                    if adapter.observe(
                        market,
                        snapshot,
                        baseline_markets[market.market_id],
                        measurement.external_price_change,
                    ):
                        store.append(
                            "shadow_decision",
                            timestamp,
                            adapter.shadow.decisions[-1],
                        )
                    row = SkippedMarket(
                        timestamp, market.market_id, market.asset,
                        market.question, measurement.reason,
                    )
                    skipped.append(row)
                    store.append("skipped", timestamp, row)
            store.append("capture_checkpoint", timestamp, {
                "expected_reference_points": expected_refs,
                "successful_reference_points": successful_refs,
                "expected_market_points": expected_market_points,
                "successful_market_points": successful_market_points,
                "mode": mode,
                "discovery_failure_count": len(discovery_failures),
            })
            checkpoint_timestamps.append(timestamp)

        actual_completion = (
            start + timedelta(seconds=self.config.duration_seconds)
            if mock_mode else datetime.now(timezone.utc)
        )
        monotonic_elapsed = (
            self.config.duration_seconds if mock_mode else scheduler.elapsed_seconds
        )
        observed_utc_span = (actual_completion - start).total_seconds()
        tolerance = max(5.0, self.config.duration_seconds * 0.01)
        temporal_complete = (
            monotonic_elapsed + tolerance >= self.config.duration_seconds
            and observed_utc_span + tolerance >= self.config.duration_seconds
        )
        continuity = observation_continuity(
            expected_duration_seconds=self.config.duration_seconds,
            poll_interval_seconds=self.config.poll_interval_seconds,
            started_at=start,
            completed_at=actual_completion,
            checkpoint_timestamps=checkpoint_timestamps,
        )
        complete = temporal_complete and continuity["status"] == "continuous"
        rejection_reasons = list(continuity["rejection_reasons"])
        if not temporal_complete:
            rejection_reasons.append("temporal_runtime_shortfall")
        campaign_completeness = {
            "status": "complete" if complete else "incomplete_campaign",
            "expected_duration_seconds": self.config.duration_seconds,
            "actual_utc_start_timestamp": start.isoformat(),
            "actual_utc_completion_timestamp": actual_completion.isoformat(),
            "monotonic_elapsed_runtime_seconds": round(monotonic_elapsed, 6),
            "observed_utc_span_seconds": round(observed_utc_span, 6),
            "coverage_percentage": round(
                max(0.0, min(1.0, observed_utc_span / self.config.duration_seconds))
                * 100.0, 4
            ),
            "material_shortfall_seconds": round(
                max(0.0, self.config.duration_seconds - observed_utc_span), 6
            ),
            "wall_clock_discontinuity_count": len(
                scheduler.clock_discontinuities
            ),
            "wall_clock_discontinuities": scheduler.clock_discontinuities,
            "rejection_reasons": rejection_reasons,
        }
        for discontinuity in scheduler.clock_discontinuities:
            store.append("wall_clock_discontinuity", actual_completion, discontinuity)
        final_timestamp = actual_completion
        for tracked, previous, current in rotation.update(final_timestamp):
            store.append("market_lifecycle", final_timestamp, {
                "market_id": tracked.market.market_id,
                "previous": previous.value,
                "current": current.value,
            })
        adapter.finalize()
        micro_coverage = microstructure_coverage(microstructure_events)
        for trade in adapter.shadow.trades:
            store.append("shadow_trade", trade.closed_at, trade)
        store.append("session_completed", final_timestamp, {
            "expected_reference_points": expected_refs,
            "successful_reference_points": successful_refs,
            "expected_market_points": expected_market_points,
            "successful_market_points": successful_market_points,
            "fallback_reason": fallback_reason,
            "mode": mode,
            "campaign_completeness": campaign_completeness,
            "observation_continuity": continuity,
            "discovery_failure_count": len(discovery_failures),
            "microstructure_coverage": micro_coverage,
        })

        metrics = aggregate_metrics(
            total_markets=len(rotation.markets),
            completed_windows=len(rotation.completed),
            opportunities=opportunities,
            trades=adapter.shadow.trades,
            expected_reference_points=expected_refs,
            successful_reference_points=successful_refs,
            expected_market_points=expected_market_points,
            successful_market_points=successful_market_points,
        )
        verdict = evidence_verdict(metrics, self.config)
        if mode == "mock_fallback":
            verdict = EvidenceVerdict.INSUFFICIENT_DATA
        if not complete:
            verdict = EvidenceVerdict.INSUFFICIENT_DATA
        report = write_evidence_artifacts(
            session_dir,
            list(rotation.markets.values()),
            opportunities,
            adapter.shadow.trades,
            skipped,
            metrics,
            verdict,
            mode,
            fallback_reason,
            lifecycle_tracker.events,
            lifecycle_tracker.summary(),
            campaign_completeness,
            discovery_failures,
            continuity,
            microstructure_coverage=micro_coverage,
        )
        with stdout_log.open("a", encoding="utf-8") as handle:
            handle.write(
                f"capture_completion_utc={actual_completion.isoformat()}\n"
                f"campaign_completeness={campaign_completeness['status']}\n"
                f"monotonic_elapsed_seconds={monotonic_elapsed:.6f}\n"
                f"observed_utc_span_seconds={observed_utc_span:.6f}\n"
                f"discovery_failure_count={len(discovery_failures)}\n"
            )
        update_latest(session_dir, self.config.output_root)
        close_async_feeds(discovery, reference_feed, quote_feed)
        return session_dir, report


def _allocate_session_dir(output_root: Path) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0)
    while True:
        candidate = output_root / timestamp.strftime("%Y%m%d_%H%M%S")
        if not candidate.exists():
            return candidate
        timestamp += timedelta(seconds=1)


def _store_lifecycle_events(
    store: EventStore,
    events: list[LifecycleEvent],
) -> None:
    for event in events:
        store.append("lifecycle_tracking", event.timestamp, event)


def _reset_rollover_baselines(
    events: list[LifecycleEvent],
    baseline_refs: dict[str, ReferencePrice],
    baseline_markets: dict[str, PolymarketSnapshot],
) -> None:
    for event in events:
        if event.event != "rollover":
            continue
        previous_market = event.reason.split("->", 1)[0]
        baseline_refs.pop(previous_market, None)
        baseline_markets.pop(previous_market, None)


def apply_entry_time_guard(
    measurement,
    snapshot: PolymarketSnapshot,
    min_entry_seconds_remaining: float,
):
    if (
        measurement.qualified
        and snapshot.seconds_to_expiry < min_entry_seconds_remaining
    ):
        return replace(
            measurement,
            qualified=False,
            reason="late_entry_window",
        )
    return measurement
