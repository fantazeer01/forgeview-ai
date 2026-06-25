import tempfile
import unittest
from pathlib import Path

from polymarket.edge_engine.data import MockMarketDataProvider
from polymarket.edge_engine.engine import EdgeEngine, EngineConfig
from polymarket.edge_engine.models import ExitReason


class EdgeEngineTests(unittest.TestCase):
    def test_mock_run_opens_closes_and_tracks_pnl(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = EdgeEngine(
                MockMarketDataProvider(),
                EngineConfig(output_dir=Path(temp_dir), timeout_steps=3),
            )
            summary = engine.run()

            self.assertEqual(summary["snapshots_processed"], 12)
            self.assertEqual(summary["closed_trades"], 3)
            self.assertEqual(summary["open_positions"], 0)
            self.assertGreater(summary["realized_pnl"], 0)
            reasons = {trade.exit_reason for trade in engine.pnl.closed_trades}
            self.assertEqual(
                reasons,
                {ExitReason.CONVERGENCE, ExitReason.SCORE, ExitReason.TIMEOUT},
            )
            self.assertTrue((Path(temp_dir) / "summary.json").exists())
            self.assertTrue((Path(temp_dir) / "trades.csv").exists())
            self.assertTrue((Path(temp_dir) / "events.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
