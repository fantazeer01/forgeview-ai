import json
import shutil
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from polymarket.edge_engine_v4.config import ScannerConfig
from polymarket.edge_engine_v4.lag_detector import LagDetector
from polymarket.edge_engine_v4.market_discovery import (
    PolymarketMarketDiscovery,
    identify_asset,
)
from polymarket.edge_engine_v4.opportunity import (
    CryptoMarket,
    Direction,
    PolymarketSnapshot,
    ReferencePrice,
)
from polymarket.edge_engine_v4.scanner import (
    CryptoLagScanner, PolymarketQuoteFeed, replay_session,
)
from unittest.mock import patch


class EdgeEngineV4Tests(unittest.TestCase):
    ROOT = Path("polymarket/runs/v4/test-output")

    def setUp(self) -> None:
        shutil.rmtree(self.ROOT, ignore_errors=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.ROOT, ignore_errors=True)

    def test_public_quote_feed_preserves_depth_and_server_timestamp(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        market = CryptoMarket(
            "market", "BTC?", "BTC", start, start + timedelta(minutes=5),
            "yes-token", "no-token", 1000, 1000, True, False,
        )
        payload = json.dumps({
            "timestamp": str(int(start.timestamp() * 1000)),
            "bids": [
                {"price": "0.49", "size": "100"},
                {"price": "0.48", "size": "200"},
            ],
            "asks": [
                {"price": "0.51", "size": "80"},
                {"price": "0.52", "size": "120"},
            ],
        }).encode()

        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return payload

        with patch("urllib.request.urlopen", return_value=Response()):
            snapshot = PolymarketQuoteFeed().fetch(
                market, start + timedelta(seconds=1)
            )
        self.assertEqual(snapshot.quote_timestamp, start)
        self.assertEqual(snapshot.yes_bid_size, 100)
        self.assertEqual(snapshot.yes_ask_size, 80)
        self.assertEqual(snapshot.total_bid_depth, 300)
        self.assertEqual(snapshot.total_ask_depth, 200)
        self.assertIsNotNone(snapshot.source_latency_seconds)

    def test_asset_detection_uses_strict_aliases(self) -> None:
        self.assertIsNone(identify_asset("Will Netherlands win?"))
        self.assertEqual(identify_asset("Bitcoin Up or Down in 5 minutes?"), "BTC")
        self.assertEqual(identify_asset("SOL updown-5m-123"), "SOL")

    def test_market_parser_maps_up_down_tokens(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        raw = {
            "conditionId": "condition",
            "question": "Bitcoin Up or Down in 5 minutes?",
            "slug": f"btc-updown-5m-{int(start.timestamp())}",
            "outcomes": json.dumps(["Up", "Down"]),
            "clobTokenIds": json.dumps(["yes-token", "no-token"]),
            "liquidity": "1000",
            "volume": "5000",
            "active": True,
            "closed": False,
        }
        market, reason, _ = PolymarketMarketDiscovery()._parse_market(raw, ("BTC",))
        self.assertEqual(reason, "")
        self.assertEqual(market.yes_token_id, "yes-token")
        self.assertEqual((market.window_end - market.window_start).total_seconds(), 300)

    def test_expired_market_is_excluded_from_discovery_result(self) -> None:
        class FixtureDiscovery(PolymarketMarketDiscovery):
            def _get(self, path, params):
                if params.get("slug"):
                    return []
                start = datetime(2026, 1, 1, tzinfo=timezone.utc)
                return [{
                    "markets": [{
                        "conditionId": "expired",
                        "question": "Bitcoin Up or Down in 5 minutes?",
                        "slug": f"btc-updown-5m-{int(start.timestamp())}",
                        "outcomes": json.dumps(["Up", "Down"]),
                        "clobTokenIds": json.dumps(["yes", "no"]),
                        "liquidity": "1000",
                        "volume": "1000",
                        "active": True,
                        "closed": False,
                    }]
                }]

        markets, skipped = FixtureDiscovery().discover(
            ("BTC",),
            datetime(2026, 1, 1, 1, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(markets, [])
        self.assertIn("window_expired", {row.reason for row in skipped})

    def test_discovery_keeps_partial_success_and_records_endpoint_failure(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        raw = {
            "conditionId": "partial",
            "question": "Bitcoin Up or Down in 5 minutes?",
            "slug": f"btc-updown-5m-{int(start.timestamp())}",
            "outcomes": json.dumps(["Up", "Down"]),
            "clobTokenIds": json.dumps(["yes", "no"]),
            "liquidity": "1000",
            "volume": "1000",
            "active": True,
            "closed": False,
        }

        class PartialDiscovery(PolymarketMarketDiscovery):
            def _get(self, path, params):
                if params.get("slug", "").endswith(str(int(start.timestamp()) - 300)):
                    raise OSError("temporary endpoint failure")
                if params.get("slug", "").endswith(str(int(start.timestamp()))):
                    return [{"markets": [raw]}]
                return []

        discovery = PartialDiscovery()
        markets, _ = discovery.discover(("BTC",), start)
        self.assertEqual([row.market_id for row in markets], ["partial"])
        self.assertEqual(len(discovery.failures), 1)
        self.assertEqual(discovery.failures[0].exception_type, "OSError")
        self.assertIn("slug=", discovery.failures[0].endpoint_url)

    def test_lag_detector_qualifies_unrepriced_external_move(self) -> None:
        config = ScannerConfig(duration_seconds=1, poll_interval_seconds=1)
        detector = LagDetector(config)
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        baseline_ref = ReferencePrice(start, "BTC", 60_000, "test")
        current_ref = ReferencePrice(start + timedelta(seconds=2), "BTC", 60_180, "test")
        baseline_market = PolymarketSnapshot(
            start, "market", "BTC", 0.50, 0.50, 0.49, 0.51, 10_000, 300
        )
        current_market = PolymarketSnapshot(
            start + timedelta(seconds=2), "market", "BTC",
            0.505, 0.495, 0.495, 0.515, 10_000, 298,
        )
        result = detector.measure(current_ref, baseline_ref, current_market, baseline_market)
        self.assertTrue(result.qualified)
        self.assertEqual(result.direction, Direction.UP)
        self.assertGreater(result.lag_score, 0.7)

    def test_mock_scan_and_replay_are_deterministic(self) -> None:
        scan_dir = self.ROOT / "scan"
        replay_dir = self.ROOT / "replay"
        config = ScannerConfig(
            duration_seconds=6,
            poll_interval_seconds=1,
            output_dir=scan_dir,
            mock=True,
        )
        scan_summary = CryptoLagScanner(config).run()
        replay_summary = replay_session(scan_dir / "session", replay_dir)
        self.assertGreater(scan_summary["opportunities"], 0)
        self.assertEqual(
            scan_summary["opportunities_by_asset"],
            replay_summary["opportunities_by_asset"],
        )
        for name in (
            "opportunities.csv",
            "skipped_markets.csv",
            "reference_prices.jsonl",
            "polymarket_snapshots.jsonl",
            "report.md",
            "summary.json",
        ):
            self.assertTrue((scan_dir / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
