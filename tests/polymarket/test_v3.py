import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from polymarket.edge_engine_v3.live_data import PolymarketEventParser
from polymarket.edge_engine_v3.models import LiveTick
from polymarket.edge_engine_v3.session import LiveSessionStore, resample_ticks
from polymarket.edge_engine_v3.validation import LiveAlphaValidator, LiveValidationConfig


class EdgeEngineV3Tests(unittest.TestCase):
    def test_websocket_event_parser(self) -> None:
        parser = PolymarketEventParser()
        ticks = parser.parse({
            "event_type": "best_bid_ask",
            "asset_id": "yes-token",
            "market": "market-1",
            "best_bid": "0.45",
            "best_ask": "0.49",
            "timestamp": "1760000000000",
        })
        self.assertEqual(len(ticks), 1)
        self.assertAlmostEqual(ticks[0].midpoint, 0.47)

    def test_session_round_trip_is_deterministic(self) -> None:
        ticks = self._ticks(20)
        with tempfile.TemporaryDirectory() as temp:
            store = LiveSessionStore(temp)
            for tick in ticks:
                store.append("{}", tick)
            loaded = LiveSessionStore.load_ticks(temp)
            self.assertEqual(
                LiveSessionStore.fingerprint(ticks),
                LiveSessionStore.fingerprint(loaded),
            )

    def test_proxy_mode_can_never_claim_true_alpha(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            report = LiveAlphaValidator(
                self._ticks(120),
                LiveValidationConfig(
                    output_dir=Path(temp),
                    minimum_trades=0,
                ),
            ).run()
            self.assertNotEqual(report.verdict, "TRUE_ALPHA")
            self.assertTrue((Path(temp) / "decisions.csv").exists())
            self.assertTrue((Path(temp) / "live_validation_report.json").exists())

    def test_duplicate_live_quotes_are_resampled(self) -> None:
        tick = self._ticks(1)[0]
        later = LiveTick(
            timestamp=tick.timestamp + timedelta(milliseconds=500),
            token_id=tick.token_id,
            market_id=tick.market_id,
            best_bid=tick.best_bid + 0.01,
            best_ask=tick.best_ask + 0.01,
        )
        sampled = resample_ticks([tick, later])
        self.assertEqual(len(sampled), 1)
        self.assertEqual(sampled[0], tick)

    @staticmethod
    def _ticks(count: int) -> list[LiveTick]:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        ticks = []
        price = 0.35
        for index in range(count):
            if index % 24 == 2:
                price = min(0.88, price + 0.20)
            else:
                price += (0.5 - price) * 0.08
            ticks.append(LiveTick(
                timestamp=start + timedelta(minutes=index),
                token_id="yes-token",
                market_id="market-1",
                best_bid=max(0.01, price - 0.01),
                best_ask=min(0.99, price + 0.01),
                trade_size=100.0 if index % 5 == 0 else 0.0,
                source_event="test",
            ))
        return ticks


if __name__ == "__main__":
    unittest.main()
