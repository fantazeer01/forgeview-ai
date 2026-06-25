from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path

from polymarket.edge_engine_v4.config import ScannerConfig
from polymarket.edge_engine_v4.lag_detector import LagDetector
from polymarket.edge_engine_v4.opportunity import (
    CryptoMarket,
    Opportunity,
    PolymarketSnapshot,
    ReferencePrice,
    SkippedMarket,
)
from .config import CaptureConfig
from .evidence import EvidenceVerdict, OpportunityGate, evidence_verdict
from .market_rotation import Lifecycle, TrackedMarket
from .metrics import aggregate_metrics
from .report import EventStore, write_evidence_artifacts
from .long_capture import LongShadowAdapter
from .continuity import session_continuity


def replay_capture(
    session_path: str | Path,
    output_dir: str | Path | None = None,
) -> tuple[Path, dict]:
    source = Path(session_path)
    events = EventStore.read(source)
    started = next(row for row in events if row["event"] == "session_started")
    settings = started["payload"]
    config = CaptureConfig(
        assets=tuple(settings["assets"]),
        duration_seconds=float(settings["duration_seconds"]),
        poll_interval_seconds=float(settings["poll_interval_seconds"]),
        near_expiry_seconds=float(settings["near_expiry_seconds"]),
        min_entry_seconds_remaining=float(
            settings.get("min_entry_seconds_remaining", 60.0)
        ),
        min_liquidity=float(settings["min_liquidity"]),
        external_move_threshold_bps=float(
            settings.get("external_move_threshold_bps", 8.0)
        ),
        repricing_ratio=float(settings.get("repricing_ratio", 0.50)),
        min_confidence=float(settings.get("min_confidence", 0.65)),
        min_completed_windows=int(settings["min_completed_windows"]),
        min_shadow_trades=int(settings["min_shadow_trades"]),
        min_reference_coverage=float(settings["min_reference_coverage"]),
        max_data_gap=float(settings["max_data_gap"]),
        max_drawdown=float(settings["max_drawdown"]),
        max_edge_decay=float(settings["max_edge_decay"]),
        max_latency_sensitivity=float(settings["max_latency_sensitivity"]),
        mock=True,
    )
    detector = LagDetector(ScannerConfig(
        assets=config.assets,
        duration_seconds=config.duration_seconds,
        poll_interval_seconds=config.poll_interval_seconds,
        min_liquidity=config.min_liquidity,
        min_seconds_to_expiry=config.near_expiry_seconds,
        external_move_threshold_bps=config.external_move_threshold_bps,
        repricing_ratio=config.repricing_ratio,
        min_confidence=config.min_confidence,
        mock=True,
    ))
    output = Path(output_dir) if output_dir else source.parent
    markets: dict[str, TrackedMarket] = {}
    references: dict[tuple[datetime, str], ReferencePrice] = {}
    baseline_refs: dict[str, ReferencePrice] = {}
    baseline_markets: dict[str, PolymarketSnapshot] = {}
    opportunities: list[Opportunity] = []
    opportunity_gate = OpportunityGate()
    skipped: list[SkippedMarket] = []
    adapter = LongShadowAdapter(config.poll_interval_seconds)
    counters = {
        "expected_reference_points": 0,
        "successful_reference_points": 0,
        "expected_market_points": 0,
        "successful_market_points": 0,
    }
    mode = str(settings["mode"])
    fallback_reason = ""
    tick_timestamps: set[datetime] = set()
    derived_quote_failures = 0
    mock_reference_events = 0
    counters_loaded = False
    campaign_completeness: dict = {}
    microstructure_coverage: dict = {}
    discovery_failures: list[dict] = []
    continuity = session_continuity(events)

    for event in events:
        timestamp = datetime.fromisoformat(event["timestamp"])
        payload = event["payload"]
        if event["event"] == "market_lifecycle":
            market_data = payload.get("market")
            market_id = payload.get("market_id")
            if market_data:
                market = _market(market_data)
                market_id = market.market_id
                markets.setdefault(
                    market_id,
                    TrackedMarket(
                        market=market,
                        lifecycle=Lifecycle.DISCOVERED,
                        discovered_at=timestamp,
                        updated_at=timestamp,
                    ),
                )
            if market_id in markets:
                markets[market_id].lifecycle = Lifecycle(payload["current"])
                markets[market_id].updated_at = timestamp
        elif event["event"] == "reference_price":
            reference = ReferencePrice(
                timestamp=timestamp,
                asset=payload["asset"],
                price=float(payload["price"]),
                source=payload["source"],
            )
            references[(timestamp, reference.asset)] = reference
            tick_timestamps.add(timestamp)
            if reference.source == "mock":
                mock_reference_events += 1
        elif event["event"] == "polymarket_snapshot":
            tick_timestamps.add(timestamp)
            snapshot = PolymarketSnapshot(
                timestamp=timestamp,
                market_id=payload["market_id"],
                asset=payload["asset"],
                yes_price=float(payload["yes_price"]),
                no_price=float(payload["no_price"]),
                yes_bid=float(payload["yes_bid"]),
                yes_ask=float(payload["yes_ask"]),
                liquidity=float(payload["liquidity"]),
                seconds_to_expiry=float(payload["seconds_to_expiry"]),
            )
            tracked = markets[snapshot.market_id]
            tracked.snapshots += 1
            reference = references.get((timestamp, snapshot.asset))
            if reference is None:
                skipped.append(SkippedMarket(
                    timestamp, snapshot.market_id, snapshot.asset,
                    tracked.market.question, "missing_reference_price",
                ))
                continue
            if (
                snapshot.market_id in baseline_refs
                and baseline_refs[snapshot.market_id].source != reference.source
            ):
                previous_source = baseline_refs[snapshot.market_id].source
                baseline_refs[snapshot.market_id] = reference
                baseline_markets[snapshot.market_id] = snapshot
                skipped.append(SkippedMarket(
                    timestamp, snapshot.market_id, snapshot.asset,
                    tracked.market.question,
                    f"reference_source_changed:{previous_source}->{reference.source}",
                ))
                continue
            baseline_refs.setdefault(snapshot.market_id, reference)
            baseline_markets.setdefault(snapshot.market_id, snapshot)
            measurement = detector.measure(
                reference,
                baseline_refs[snapshot.market_id],
                snapshot,
                baseline_markets[snapshot.market_id],
            )
            if (
                measurement.qualified
                and snapshot.seconds_to_expiry
                < config.min_entry_seconds_remaining
            ):
                measurement = replace(
                    measurement,
                    qualified=False,
                    reason="late_entry_window",
                )
            if measurement.qualified:
                market = tracked.market
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
                tracked.opportunities += 1
                if opportunity_gate.accept(opportunity):
                    opportunities.append(opportunity)
                    adapter.submit(opportunity, snapshot)
                else:
                    skipped.append(SkippedMarket(
                        timestamp, snapshot.market_id, snapshot.asset,
                        tracked.market.question, "duplicate_opportunity_suppressed",
                    ))
                    adapter.observe(
                        tracked.market,
                        snapshot,
                        baseline_markets[snapshot.market_id],
                        measurement.external_price_change,
                    )
            else:
                adapter.observe(
                    tracked.market,
                    snapshot,
                    baseline_markets[snapshot.market_id],
                    measurement.external_price_change,
                )
                skipped.append(SkippedMarket(
                    timestamp, snapshot.market_id, snapshot.asset,
                    tracked.market.question, measurement.reason,
                ))
        elif event["event"] == "skipped":
            # Detector skips are recomputed from snapshots. Preserve discovery,
            # lifecycle, quote, and reference skips that have no snapshot.
            detector_reasons = {
                "liquidity_below_minimum",
                "near_expiry_insufficient_time",
                "external_move_below_threshold",
                "polymarket_already_repriced",
                "confidence_below_threshold",
                "duplicate_opportunity_suppressed",
            }
            if (
                payload["reason"] not in detector_reasons
                and not payload["reason"].startswith("reference_source_changed:")
            ):
                skipped.append(SkippedMarket(
                    timestamp=timestamp,
                    market_id=payload["market_id"],
                    asset=payload["asset"],
                    question=payload["question"],
                    reason=payload["reason"],
                ))
            if payload["reason"].startswith(
                ("polymarket_quote_error", "missing_reference")
            ):
                tick_timestamps.add(timestamp)
                derived_quote_failures += 1
        elif event["event"] == "discovery_failure":
            discovery_failures.append(payload)
        elif event["event"] in {"capture_checkpoint", "session_completed"}:
            counters.update({
                key: int(payload[key]) for key in counters
            })
            fallback_reason = str(payload.get("fallback_reason", ""))
            mode = str(payload.get("mode", mode))
            if event["event"] == "session_completed":
                campaign_completeness = dict(
                    payload.get("campaign_completeness", {})
                )
                microstructure_coverage = dict(
                    payload.get("microstructure_coverage", {})
                )
            counters_loaded = True

    if not counters_loaded:
        # Legacy/interrupted sessions have valid events but no completion
        # counters. Reconstruct conservative denominators from the event stream.
        counters["successful_reference_points"] = sum(
            event["event"] == "reference_price" for event in events
        )
        counters["expected_reference_points"] = (
            len(tick_timestamps) * len(config.assets)
        )
        counters["successful_market_points"] = sum(
            event["event"] == "polymarket_snapshot" for event in events
        )
        counters["expected_market_points"] = (
            counters["successful_market_points"] + derived_quote_failures
        )
        fallback_reason = "inferred_counters_missing_session_completed"
    if mock_reference_events and mode == "public":
        mode = "mock_fallback"
        fallback_reason = (
            f"{fallback_reason};mock_reference_events_detected:{mock_reference_events}"
        ).strip(";")

    adapter.finalize()
    metrics = aggregate_metrics(
        total_markets=len(markets),
        completed_windows=sum(
            row.lifecycle is Lifecycle.CLOSED and row.snapshots > 0
            for row in markets.values()
        ),
        opportunities=opportunities,
        trades=adapter.shadow.trades,
        expected_reference_points=counters["expected_reference_points"],
        successful_reference_points=counters["successful_reference_points"],
        expected_market_points=counters["expected_market_points"],
        successful_market_points=counters["successful_market_points"],
    )
    verdict = evidence_verdict(metrics, config)
    if mode == "mock_fallback":
        verdict = EvidenceVerdict.INSUFFICIENT_DATA
    if continuity["status"] != "continuous":
        verdict = EvidenceVerdict.INSUFFICIENT_DATA
        campaign_completeness["status"] = "incomplete_campaign"
        campaign_completeness["rejection_reasons"] = continuity[
            "rejection_reasons"
        ]
    report = write_evidence_artifacts(
        output,
        list(markets.values()),
        opportunities,
        adapter.shadow.trades,
        skipped,
        metrics,
        verdict,
        mode,
        fallback_reason,
        campaign_completeness=campaign_completeness,
        discovery_failures=discovery_failures,
        observation_continuity=continuity,
        microstructure_coverage=microstructure_coverage,
    )
    return output, report


def _market(payload: dict) -> CryptoMarket:
    return CryptoMarket(
        market_id=payload["market_id"],
        question=payload["question"],
        asset=payload["asset"],
        window_start=datetime.fromisoformat(payload["window_start"]),
        window_end=datetime.fromisoformat(payload["window_end"]),
        yes_token_id=payload["yes_token_id"],
        no_token_id=payload["no_token_id"],
        liquidity=float(payload["liquidity"]),
        volume=float(payload["volume"]),
        active=bool(payload["active"]),
        closed=bool(payload["closed"]),
    )
