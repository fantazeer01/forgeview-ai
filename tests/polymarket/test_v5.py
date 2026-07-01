import shutil
import time
from io import StringIO
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from polymarket.edge_engine.models import Side
from polymarket.edge_engine_v3.models import ShadowTrade
from polymarket.edge_engine_v4.opportunity import (
    CryptoMarket, Opportunity, Direction, PolymarketSnapshot,
)
from polymarket.edge_engine_v5.config import CaptureConfig
from polymarket.edge_engine_v5.evidence import (
    EvidenceVerdict,
    OpportunityGate,
    evidence_verdict,
)
from polymarket.edge_engine_v5.diagnostics import inspect_session
from polymarket.edge_engine_v5.long_capture import LongShadowCapture
from polymarket.edge_engine_v5.long_capture import (
    _reset_rollover_baselines,
    apply_entry_time_guard,
)
from polymarket.edge_engine_v5.live_console import (
    LiveConsole,
    LiveSignal,
    format_live_signal,
)
from polymarket.edge_engine_v5.market_rotation import Lifecycle, MarketRotation
from polymarket.edge_engine_v5.market_lifecycle import (
    MarketLifecycleState,
    MarketLifecycleTracker,
)
from polymarket.edge_engine_v5.metrics import EvidenceMetrics, aggregate_metrics
from polymarket.edge_engine_v5.replay import replay_capture
from polymarket.edge_engine_v5.report import EventStore
from polymarket.edge_engine_v5.scheduler import CaptureScheduler
from polymarket.edge_engine_v4.market_discovery import DiscoveryFailure
from polymarket.edge_engine_v5.continuity import observation_continuity
from polymarket.edge_engine_v5.async_feeds import (
    AsyncDiscovery, AsyncQuoteFeed, AsyncReferenceFeed, close_async_feeds,
)
from polymarket.edge_engine_v5.microstructure import MicrostructureTracker
from polymarket.edge_engine_v5.power_preflight import inspect_windows_power
from unittest.mock import patch


class EdgeEngineV5Tests(unittest.TestCase):
    ROOT = Path("polymarket/runs/v5/test-output")

    def setUp(self) -> None:
        shutil.rmtree(self.ROOT, ignore_errors=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.ROOT, ignore_errors=True)

    def test_microstructure_tracker_derives_depth_velocity_and_cross_asset(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        tracker = MicrostructureTracker()
        first = tracker.observe(_micro_quote(
            "btc", "BTC", start, 0.50, 100, 80
        ), start)
        second = tracker.observe(_micro_quote(
            "eth", "ETH", start + timedelta(seconds=1), 0.55, 90, 110
        ), start + timedelta(seconds=1))
        third = tracker.observe(_micro_quote(
            "btc", "BTC", start + timedelta(seconds=2), 0.52, 120, 80
        ), start + timedelta(seconds=2))

        self.assertIsNone(first.repricing_velocity)
        self.assertAlmostEqual(second.book_imbalance, -0.1)
        self.assertAlmostEqual(third.repricing_velocity, 0.01)
        self.assertAlmostEqual(third.book_imbalance, 0.2)
        self.assertIsNotNone(third.cross_asset_yes_dispersion)
        self.assertEqual(third.schema_version, 1)

    def test_microstructure_tracker_quote_stability_and_acceleration(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        tracker = MicrostructureTracker()
        tracker.observe(_micro_quote("btc", "BTC", start, 0.50, 100, 100), start)
        stable = tracker.observe(_micro_quote(
            "btc", "BTC", start + timedelta(seconds=2), 0.50, 100, 100
        ), start + timedelta(seconds=2))
        moving = tracker.observe(_micro_quote(
            "btc", "BTC", start + timedelta(seconds=4), 0.54, 120, 80
        ), start + timedelta(seconds=4))
        self.assertEqual(stable.consecutive_quote_stability, 2)
        self.assertEqual(moving.consecutive_quote_stability, 1)
        self.assertIsNotNone(moving.repricing_acceleration)

    def test_market_rotation_tracks_lifecycle_without_duplicates(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        market = CryptoMarket(
            "market", "BTC Up or Down?", "BTC", start, start + timedelta(minutes=5),
            "yes", "no", 1000, 5000, True, False,
        )
        rotation = MarketRotation(near_expiry_seconds=30)
        rotation.ingest([market, market], start)
        self.assertEqual(len(rotation.markets), 1)
        self.assertEqual(rotation.markets["market"].lifecycle, Lifecycle.ACTIVE)
        rotation.update(start + timedelta(minutes=4, seconds=40))
        self.assertEqual(rotation.markets["market"].lifecycle, Lifecycle.NEAR_EXPIRY)
        rotation.markets["market"].snapshots = 2
        rotation.update(start + timedelta(minutes=5))
        self.assertEqual(rotation.markets["market"].lifecycle, Lifecycle.CLOSED)
        self.assertEqual(len(rotation.completed), 1)

    def test_evidence_aggregation(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        opportunities = [
            Opportunity(
                "BTC", "market", "BTC?", Direction.UP, "yes", "no",
                0.01, 0.0, 0.9, 0.9, "qualified", start,
            )
        ]
        trades = [
            self._trade("win", 5.0, start),
            self._trade("loss", -2.0, start + timedelta(minutes=1)),
        ]
        metrics = aggregate_metrics(10, 8, opportunities, trades, 100, 98, 80, 76)
        self.assertEqual(metrics.simulated_pnl, 3.0)
        self.assertEqual(metrics.win_rate, 0.5)
        self.assertEqual(metrics.reference_coverage_percentage, 98.0)
        self.assertEqual(metrics.data_gap_percentage, 5.0)

    def test_conservative_verdict_logic(self) -> None:
        config = CaptureConfig(
            min_completed_windows=10,
            min_shadow_trades=5,
        )
        insufficient = self._metrics(completed=9, trades=10, pnl=100)
        self.assertEqual(
            evidence_verdict(insufficient, config),
            EvidenceVerdict.INSUFFICIENT_DATA,
        )
        no_edge = self._metrics(completed=10, trades=5, pnl=-1)
        self.assertEqual(evidence_verdict(no_edge, config), EvidenceVerdict.NO_EDGE)
        weak = self._metrics(
            completed=10, trades=5, pnl=10, win_rate=0.5,
            drawdown=0.07, decay=0.4, latency=0.2,
        )
        self.assertEqual(evidence_verdict(weak, config), EvidenceVerdict.WEAK_EDGE)
        potential = self._metrics(
            completed=10, trades=5, pnl=10, win_rate=0.6,
            drawdown=0.02, decay=0.2, latency=0.2,
        )
        self.assertEqual(
            evidence_verdict(potential, config),
            EvidenceVerdict.POTENTIAL_EDGE,
        )

    def test_opportunity_gate_allows_one_signal_per_market(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        opportunity = Opportunity(
            "BTC", "market", "BTC?", Direction.UP, "yes", "no",
            0.01, 0.0, 0.9, 0.9, "qualified", start,
        )
        gate = OpportunityGate()
        self.assertTrue(gate.accept(opportunity))
        self.assertFalse(gate.accept(opportunity))

    def test_mock_capture_replay_and_artifacts(self) -> None:
        config = CaptureConfig(
            duration_seconds=900,
            poll_interval_seconds=60,
            discovery_interval_seconds=60,
            output_root=self.ROOT,
            mock=True,
            min_completed_windows=1,
            min_shadow_trades=1,
        )
        session_dir, capture_report = LongShadowCapture(config).run()
        session_events = EventStore.read(session_dir / "session.jsonl")
        envelope_times = [
            datetime.fromisoformat(event["timestamp"]) for event in session_events
        ]
        self.assertEqual(envelope_times, sorted(envelope_times))
        self.assertEqual(session_events[-1]["event"], "session_completed")
        for event in session_events:
            if event["event"] == "shadow_trade":
                self.assertLessEqual(
                    datetime.fromisoformat(event["payload"]["closed_at"]),
                    datetime.fromisoformat(event["timestamp"]),
                )
        replay_dir = self.ROOT / "replay"
        _, replay_report = replay_capture(session_dir / "session.jsonl", replay_dir)
        self.assertEqual(capture_report["metrics"], replay_report["metrics"])
        self.assertEqual(capture_report["verdict"], replay_report["verdict"])
        self.assertEqual(
            capture_report["campaign_completeness"],
            replay_report["campaign_completeness"],
        )
        for name in (
            "session.jsonl", "markets.csv", "opportunities.csv", "trades.csv",
            "skipped_markets.csv", "evidence_report.json", "report.md",
        ):
            self.assertTrue((session_dir / name).exists(), name)
            self.assertTrue((self.ROOT / "latest" / name).exists(), f"latest/{name}")
        self.assertTrue((session_dir / "campaign.stdout.log").exists())
        self.assertTrue((session_dir / "campaign.stderr.log").exists())
        self.assertEqual(
            capture_report["campaign_completeness"]["status"], "complete"
        )
        diagnostics = inspect_session(session_dir / "session.jsonl")
        self.assertTrue(diagnostics.has_capture_checkpoint)
        self.assertGreater(diagnostics.reference_snapshots, 0)
        self.assertEqual(diagnostics.snapshots_without_exact_reference, 0)
        events = [
            __import__("json").loads(line)
            for line in (session_dir / "session.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()
        ]
        micro = [
            row for row in events if row["event"] == "microstructure_snapshot"
        ]
        snapshots = [
            row for row in events if row["event"] == "polymarket_snapshot"
        ]
        self.assertEqual(len(micro), len(snapshots))
        self.assertTrue(all(row["payload"]["schema_version"] == 1 for row in micro))

    def test_scheduler_detects_backward_wall_clock_jump(self) -> None:
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        state = {"mono": 0.0, "utc": 0.0, "jumped": False}

        def monotonic():
            return state["mono"]

        def utc_now():
            return base + timedelta(seconds=state["utc"])

        def sleep(seconds):
            state["mono"] += seconds
            state["utc"] += seconds
            if state["mono"] >= 2 and not state["jumped"]:
                state["utc"] -= 20
                state["jumped"] = True

        scheduler = CaptureScheduler(
            4, 1, False, utc_now=utc_now, monotonic=monotonic, sleep=sleep
        )
        list(scheduler.ticks())
        self.assertAlmostEqual(scheduler.elapsed_seconds, 4.0)
        self.assertGreaterEqual(len(scheduler.clock_discontinuities), 1)
        self.assertLess(
            float(scheduler.clock_discontinuities[-1]["drift_seconds"]), 0
        )

    def test_fixed_deadline_scheduler_does_not_add_work_delay(self) -> None:
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        state = {"mono": 0.0}

        def monotonic():
            return state["mono"]

        def utc_now():
            return base + timedelta(seconds=state["mono"])

        def sleep(seconds):
            state["mono"] += seconds

        scheduler = CaptureScheduler(
            6, 2, False, utc_now=utc_now, monotonic=monotonic, sleep=sleep
        )
        timestamps = []
        for _, timestamp in scheduler.ticks():
            timestamps.append(timestamp)
            state["mono"] += 0.75
        self.assertEqual(
            [(b - a).total_seconds() for a, b in zip(timestamps, timestamps[1:])],
            [2.0, 2.0],
        )

    def test_async_discovery_does_not_block_cached_reads(self) -> None:
        class SlowDiscovery:
            failures = []
            def discover(self, assets, timestamp):
                time.sleep(0.05)
                return ["market"], []

        feed = AsyncDiscovery(SlowDiscovery())
        started = time.monotonic()
        self.assertEqual(feed.discover(("BTC",), datetime.now(timezone.utc)), ([], []))
        self.assertLess(time.monotonic() - started, 0.02)
        time.sleep(0.07)
        self.assertEqual(
            feed.discover(("BTC",), datetime.now(timezone.utc))[0], ["market"]
        )
        close_async_feeds(feed)

    def test_async_discovery_wraps_worker_exception_as_failure(self) -> None:
        class FailedDiscovery:
            failures = []

            def discover(self, assets, timestamp):
                time.sleep(0.05)
                raise IncompleteReadLike("partial response")

        class IncompleteReadLike(Exception):
            url = "https://example.test/events"

        feed = AsyncDiscovery(FailedDiscovery())
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(feed.discover(("BTC",), start), ([], []))
        time.sleep(0.07)
        self.assertEqual(feed.discover(("BTC",), start), ([], []))
        self.assertEqual(len(feed.failures), 1)
        self.assertIsInstance(feed.failures[0], DiscoveryFailure)
        self.assertEqual(feed.failures[0].endpoint_url, IncompleteReadLike.url)
        self.assertEqual(feed.failures[0].exception_type, "IncompleteReadLike")
        close_async_feeds(feed)

    def test_quote_timeout_does_not_block_cadence(self) -> None:
        class SlowQuote:
            def fetch(self, market, timestamp):
                time.sleep(0.05)
                raise TimeoutError("slow quote")

        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        market = CryptoMarket(
            "market", "BTC?", "BTC", start, start + timedelta(minutes=5),
            "yes", "no", 1000, 1000, True, False,
        )
        feed = AsyncQuoteFeed(SlowQuote(), workers=1)
        began = time.monotonic()
        with self.assertRaises(ValueError):
            feed.fetch(market, start)
        self.assertLess(time.monotonic() - began, 0.02)
        time.sleep(0.07)
        with self.assertRaises(TimeoutError):
            feed.fetch(market, start + timedelta(seconds=2))
        close_async_feeds(feed)

    def test_accelerated_slow_feeds_recover_full_checkpoint_cadence(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        state = {"mono": 0.0}
        scheduler = CaptureScheduler(
            20, 2, False,
            utc_now=lambda: start + timedelta(seconds=state["mono"]),
            monotonic=lambda: state["mono"],
            sleep=lambda seconds: state.__setitem__(
                "mono", state["mono"] + seconds
            ),
        )
        checkpoints = []
        for _, timestamp in scheduler.ticks():
            checkpoints.append(timestamp)
            state["mono"] += 0.2  # simulated non-blocking processing overhead
        continuity = observation_continuity(
            expected_duration_seconds=20,
            poll_interval_seconds=2,
            started_at=start,
            completed_at=start + timedelta(seconds=20),
            checkpoint_timestamps=checkpoints[:10],
        )
        self.assertEqual(continuity["status"], "continuous")
        self.assertEqual(continuity["checkpoint_coverage_percentage"], 100.0)

    def test_power_preflight_blocks_nonzero_ac_sleep(self) -> None:
        class Result:
            stdout = (
                "Current AC Power Setting Index: 0x00000384\n"
                "Current DC Power Setting Index: 0x00000000\n"
            )
            stderr = ""

        with patch("platform.system", return_value="Windows"):
            result = inspect_windows_power(run_command=lambda *a, **k: Result())
        self.assertFalse(result.safe_for_overnight)
        self.assertEqual(result.sleep_ac_seconds, 900)
        self.assertIn("powercfg /change standby-timeout-ac 0", result.commands)

    def test_power_preflight_accepts_disabled_ac_sleep(self) -> None:
        class Result:
            stdout = (
                "Current AC Power Setting Index: 0x00000000\n"
                "Current DC Power Setting Index: 0x00000384\n"
            )
            stderr = ""

        with patch("platform.system", return_value="Windows"):
            result = inspect_windows_power(run_command=lambda *a, **k: Result())
        self.assertTrue(result.safe_for_overnight)

    def test_capture_cli_accepts_balanced_repricing_thresholds(self) -> None:
        from polymarket.edge_engine_v5.cli import build_parser

        parser = build_parser()
        args = parser.parse_args([
            "capture",
            "--duration", "43200",
            "--external-move-threshold-bps", "6",
            "--repricing-ratio", "0.65",
            "--min-confidence", "0.45",
            "--min-entry-seconds", "60",
            "--no-mock-fallback",
        ])

        self.assertEqual(args.command, "capture")
        self.assertEqual(args.external_move_threshold_bps, 6)
        self.assertEqual(args.repricing_ratio, 0.65)
        self.assertEqual(args.min_confidence, 0.45)
        self.assertEqual(args.min_entry_seconds, 60)
        self.assertTrue(args.no_mock_fallback)

    def test_normal_campaign_has_continuous_observation_coverage(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        result = observation_continuity(
            expected_duration_seconds=600,
            poll_interval_seconds=2,
            started_at=start,
            completed_at=start + timedelta(seconds=600),
            checkpoint_timestamps=[
                start + timedelta(seconds=index * 2)
                for index in range(300)
            ],
        )
        self.assertEqual(result["status"], "continuous")
        self.assertEqual(result["checkpoint_coverage_percentage"], 100.0)
        self.assertEqual(result["gaps_over_300_seconds"], 0)

    def test_terminal_gap_fails_continuity(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        result = observation_continuity(
            expected_duration_seconds=600,
            poll_interval_seconds=2,
            started_at=start,
            completed_at=start + timedelta(seconds=600),
            checkpoint_timestamps=[
                start + timedelta(seconds=index * 2)
                for index in range(100)
            ],
        )
        self.assertEqual(result["status"], "incomplete")
        self.assertGreater(result["terminal_gap_seconds"], 300)
        self.assertIn(
            "checkpoint_gap_over_300_seconds", result["rejection_reasons"]
        )

    def test_sparse_checkpoints_fail_density_without_long_gap(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        result = observation_continuity(
            expected_duration_seconds=600,
            poll_interval_seconds=2,
            started_at=start,
            completed_at=start + timedelta(seconds=600),
            checkpoint_timestamps=[
                start + timedelta(seconds=index * 4)
                for index in range(150)
            ],
        )
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["checkpoint_coverage_percentage"], 50.0)
        self.assertEqual(result["gaps_over_300_seconds"], 0)

    def test_host_sleep_pattern_fails_despite_matching_endpoint_span(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        checkpoints = [
            start + timedelta(seconds=index * 2) for index in range(100)
        ]
        checkpoints += [
            start + timedelta(seconds=500 + index * 2)
            for index in range(50)
        ]
        result = observation_continuity(
            expected_duration_seconds=600,
            poll_interval_seconds=2,
            started_at=start,
            completed_at=start + timedelta(seconds=600),
            checkpoint_timestamps=checkpoints,
        )
        self.assertEqual(result["status"], "incomplete")
        self.assertGreater(result["max_checkpoint_gap_seconds"], 300)

    def test_repeated_discovery_failures_are_independent_events(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)

        class FailedDiscovery:
            def __init__(self):
                self.calls = 0
                self.failures = []

            def discover(self, assets, now):
                self.calls += 1
                self.failures = [DiscoveryFailure(
                    now,
                    f"https://example.test/events?call={self.calls}",
                    "OSError",
                    f"failure-{self.calls}",
                )]
                return [], []

        config = CaptureConfig(
            duration_seconds=3,
            poll_interval_seconds=1,
            discovery_interval_seconds=1,
            output_root=self.ROOT,
            mock=True,
        )
        session_dir, report = LongShadowCapture(
            config, discovery=FailedDiscovery()
        ).run()
        events = [
            row for row in __import__("json").loads(
                "[" + ",".join(
                    (session_dir / "session.jsonl").read_text(
                        encoding="utf-8"
                    ).splitlines()
                ) + "]"
            )
            if row["event"] == "discovery_failure"
        ]
        self.assertEqual(len(events), 3)
        self.assertEqual(len(report["discovery_failures"]), 3)
        self.assertNotIn("market_discovery_error", report["fallback_reason"])

    def test_interrupted_legacy_session_infers_coverage(self) -> None:
        config = CaptureConfig(
            duration_seconds=600,
            poll_interval_seconds=60,
            discovery_interval_seconds=60,
            output_root=self.ROOT,
            mock=True,
            min_completed_windows=1,
            min_shadow_trades=1,
        )
        session_dir, _ = LongShadowCapture(config).run()
        original = session_dir / "session.jsonl"
        legacy = session_dir / "legacy_interrupted.jsonl"
        rows = [
            line for line in original.read_text(encoding="utf-8").splitlines()
            if '"event":"session_completed"' not in line
            and '"event":"capture_checkpoint"' not in line
        ]
        legacy.write_text("\n".join(rows) + "\n", encoding="utf-8")
        _, report = replay_capture(legacy, self.ROOT / "legacy-replay")
        self.assertEqual(report["metrics"]["reference_coverage_percentage"], 100.0)
        self.assertEqual(report["metrics"]["data_gap_percentage"], 0.0)
        diagnostics = inspect_session(legacy)
        self.assertIn("no session_completed", diagnostics.missing_reference_reason)

    def test_live_signal_formatting(self) -> None:
        start = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        market = CryptoMarket(
            "market", "Bitcoin Up or Down - 5m", "BTC",
            start, start + timedelta(minutes=5), "yes", "no",
            10_000, 50_000, True, False,
        )
        from polymarket.edge_engine_v4.opportunity import (
            LagMeasurement,
            PolymarketSnapshot,
            ReferencePrice,
        )
        reference = ReferencePrice(start, "BTC", 60_100, "test")
        snapshot = PolymarketSnapshot(
            start, "market", "BTC", 0.43, 0.57, 0.42, 0.44, 10_000, 240
        )
        measurement = LagMeasurement(
            0.0008, -0.02, 5.0, 0.74, Direction.UP,
            0.68, True, "qualified_external_move_not_repriced",
        )
        rendered = format_live_signal(LiveSignal(
            market, reference, snapshot, measurement,
            "BUY YES", "BTC moved up, Polymarket has not fully repriced",
        ))
        self.assertIn("BTC 5m", rendered)
        self.assertIn("External: UP +0.080%", rendered)
        self.assertIn("Polymarket YES: 0.430 | NO: 0.570", rendered)
        self.assertIn("Action: BUY YES (shadow)", rendered)

        flat = format_live_signal(LiveSignal(
            market, reference, snapshot,
            LagMeasurement(
                0.0, 0.0, 0.0, 0.0, Direction.NONE,
                0.1, False, "external_move_below_threshold",
            ),
            "HOLD", "weak external move",
        ))
        self.assertIn("External: FLAT +0.000%", flat)

    def test_live_mode_loop_prints_and_preserves_artifacts(self) -> None:
        stream = StringIO()
        console = LiveConsole(show_skipped=True, stream=stream)
        config = CaptureConfig(
            duration_seconds=180,
            poll_interval_seconds=60,
            discovery_interval_seconds=60,
            output_root=self.ROOT,
            mock=True,
            min_completed_windows=1,
            min_shadow_trades=1,
        )
        session_dir, _ = LongShadowCapture(
            config, live_console=console
        ).run()
        output = stream.getvalue()
        self.assertEqual(console.cycles, 3)
        self.assertIn("BTC 5m", output)
        self.assertIn("Action:", output)
        self.assertTrue((session_dir / "session.jsonl").exists())
        self.assertTrue((session_dir / "evidence_report.json").exists())
        self.assertTrue((session_dir / "lifecycle_events.csv").exists())
        self.assertTrue((session_dir / "lifecycle_summary.json").exists())

        quiet_stream = StringIO()
        quiet = LiveConsole(quiet=True, show_skipped=True, stream=quiet_stream)
        LongShadowCapture(config, live_console=quiet).run()
        self.assertEqual(quiet_stream.getvalue(), "")

    def test_lifecycle_state_transitions_and_early_detection(self) -> None:
        start = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        market = CryptoMarket(
            "market", "BTC Up or Down?", "BTC",
            start, start + timedelta(minutes=5), "yes", "no",
            10_000, 50_000, True, False,
        )
        tracker = MarketLifecycleTracker(("BTC",))
        tracker.ingest([market], start + timedelta(seconds=6))
        record = tracker.records["market"]
        self.assertEqual(record.state, MarketLifecycleState.NEWLY_OPENED)
        self.assertEqual(record.seconds_after_open_when_detected, 6)
        self.assertTrue(record.caught_early)
        tracker.update(start + timedelta(minutes=2))
        self.assertEqual(record.state, MarketLifecycleState.ACTIVE)
        tracker.update(start + timedelta(minutes=4, seconds=30))
        self.assertEqual(record.state, MarketLifecycleState.NEAR_EXPIRY)
        tracker.update(start + timedelta(minutes=5))
        self.assertEqual(record.state, MarketLifecycleState.CLOSED)

    def test_late_market_signal_is_forced_to_skip(self) -> None:
        from polymarket.edge_engine_v4.opportunity import (
            LagMeasurement,
            PolymarketSnapshot,
        )
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        measurement = LagMeasurement(
            0.01, 0.0, 5.0, 0.9, Direction.UP,
            0.9, True, "qualified_external_move_not_repriced",
        )
        snapshot = PolymarketSnapshot(
            start, "market", "BTC", 0.5, 0.5,
            0.49, 0.51, 10_000, 59,
        )
        guarded = apply_entry_time_guard(measurement, snapshot, 60)
        self.assertFalse(guarded.qualified)
        self.assertEqual(guarded.reason, "late_entry_window")

    def test_rollover_resets_previous_market_baseline(self) -> None:
        from polymarket.edge_engine_v4.opportunity import (
            PolymarketSnapshot,
            ReferencePrice,
        )
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        old = CryptoMarket(
            "old", "BTC old", "BTC", start, start + timedelta(minutes=5),
            "yes-old", "no-old", 10_000, 50_000, True, False,
        )
        new = CryptoMarket(
            "new", "BTC new", "BTC", start + timedelta(minutes=5),
            start + timedelta(minutes=10), "yes-new", "no-new",
            10_000, 50_000, True, False,
        )
        tracker = MarketLifecycleTracker(("BTC",))
        tracker.ingest([old, new], start)
        events = tracker.update(start + timedelta(minutes=5))
        baselines = {"old": ReferencePrice(start, "BTC", 60_000, "test")}
        market_baselines = {
            "old": PolymarketSnapshot(
                start, "old", "BTC", 0.5, 0.5,
                0.49, 0.51, 10_000, 300,
            )
        }
        _reset_rollover_baselines(events, baselines, market_baselines)
        self.assertNotIn("old", baselines)
        self.assertNotIn("old", market_baselines)
        self.assertEqual(tracker.rollover_count, 1)

    def test_quote_unavailable_recovers_next_poll(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        market = CryptoMarket(
            "market", "SOL?", "SOL", start, start + timedelta(minutes=5),
            "yes", "no", 10_000, 50_000, True, False,
        )
        tracker = MarketLifecycleTracker(("SOL",))
        tracker.ingest([market], start)
        tracker.mark_quote_unavailable("market", start, "ValueError")
        self.assertEqual(
            tracker.records["market"].state,
            MarketLifecycleState.QUOTE_UNAVAILABLE,
        )
        tracker.mark_quote_available("market", start + timedelta(seconds=1))
        self.assertEqual(
            tracker.records["market"].state,
            MarketLifecycleState.NEWLY_OPENED,
        )
        self.assertEqual(tracker.records["market"].quote_errors, 1)

    def test_lifecycle_summary_counts_delay_errors_and_rollover(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        first = CryptoMarket(
            "first", "BTC first", "BTC", start, start + timedelta(minutes=5),
            "y1", "n1", 10_000, 50_000, True, False,
        )
        second = CryptoMarket(
            "second", "BTC second", "BTC", start + timedelta(minutes=5),
            start + timedelta(minutes=10), "y2", "n2",
            10_000, 50_000, True, False,
        )
        tracker = MarketLifecycleTracker(("BTC",))
        tracker.ingest([first], start + timedelta(seconds=10))
        tracker.mark_quote_unavailable("first", start + timedelta(seconds=11), "test")
        tracker.ingest([second], start + timedelta(minutes=6, seconds=5))
        tracker.update(start + timedelta(minutes=6, seconds=5))
        summary = tracker.summary()
        self.assertEqual(summary["markets_detected"], 2)
        self.assertEqual(summary["markets_caught_within_15_seconds"], 1)
        self.assertEqual(summary["markets_caught_after_60_seconds"], 1)
        self.assertEqual(summary["quote_error_count"], 1)
        self.assertEqual(summary["rollover_count"], 1)

    @staticmethod
    def _trade(trade_id: str, pnl: float, timestamp: datetime) -> ShadowTrade:
        return ShadowTrade(
            trade_id=trade_id,
            market_id="market",
            side=Side.YES,
            opened_at=timestamp,
            closed_at=timestamp + timedelta(seconds=1),
            entry_price=0.5,
            exit_price=0.5 + pnl / 200,
            quantity=200,
            entry_score=0.8,
            exit_score=0.2,
            exit_reason="test",
            pnl=pnl,
            return_pct=pnl / 100,
            holding_updates=1,
        )

    @staticmethod
    def _metrics(
        completed: int,
        trades: int,
        pnl: float,
        win_rate: float = 0.6,
        drawdown: float = 0.02,
        decay: float = 0.2,
        latency: float = 0.2,
    ) -> EvidenceMetrics:
        return EvidenceMetrics(
            total_markets_observed=completed,
            completed_market_windows=completed,
            opportunities_detected=trades,
            opportunity_rate=1.0,
            shadow_trades=trades,
            simulated_pnl=pnl,
            win_rate=win_rate,
            avg_win=2.0,
            avg_loss=-1.0,
            max_drawdown=drawdown,
            edge_decay=decay,
            latency_sensitivity=latency,
            reference_coverage_percentage=99.0,
            data_gap_percentage=1.0,
        )


def _micro_quote(market_id, asset, timestamp, price, bid_depth, ask_depth):
    return PolymarketSnapshot(
        timestamp=timestamp,
        market_id=market_id,
        asset=asset,
        yes_price=price,
        no_price=1 - price,
        yes_bid=price - 0.01,
        yes_ask=price + 0.01,
        liquidity=10_000,
        seconds_to_expiry=240,
        quote_timestamp=timestamp,
        yes_bid_size=bid_depth / 2,
        yes_ask_size=ask_depth / 2,
        total_bid_depth=bid_depth,
        total_ask_depth=ask_depth,
        source_latency_seconds=0.01,
    )


if __name__ == "__main__":
    unittest.main()
