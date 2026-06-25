import tempfile
import unittest
from pathlib import Path

from polymarket.edge_engine_v2.data import HybridProxyData, ReplayStore
from polymarket.edge_engine_v2.perturbation import perturb_snapshots
from polymarket.edge_engine_v2.simulator import SimulatorConfig
from polymarket.edge_engine_v2.walkforward import WalkForwardEngine
from polymarket.edge_engine_v2.validation import AlphaValidationSystem, ValidationConfig


class EdgeEngineV2Tests(unittest.TestCase):
    def test_replay_round_trip_and_fingerprint(self) -> None:
        rows = HybridProxyData(seed=7, markets=2, steps=20).generate()
        with tempfile.TemporaryDirectory() as temp:
            path = ReplayStore.save(rows, Path(temp) / "data.jsonl")
            loaded = ReplayStore.load(path)
            self.assertEqual(ReplayStore.fingerprint(rows), ReplayStore.fingerprint(loaded))

    def test_perturbations_are_seed_deterministic(self) -> None:
        rows = HybridProxyData(seed=8, markets=2, steps=20).generate()
        first = perturb_snapshots(rows, seed=99, price_noise_std=0.02, signal_dropout=0.1)
        second = perturb_snapshots(rows, seed=99, price_noise_std=0.02, signal_dropout=0.1)
        self.assertEqual(ReplayStore.fingerprint(first), ReplayStore.fingerprint(second))

    def test_full_validation_writes_report(self) -> None:
        rows = HybridProxyData(seed=42, markets=3, steps=90).generate()
        with tempfile.TemporaryDirectory() as temp:
            config = ValidationConfig(
                seed=42,
                windows=3,
                noise_levels=(0.01,),
                dropout_levels=(0.05,),
                signal_lags=(1,),
                execution_latencies=(0, 2),
                simulator=SimulatorConfig(latency_steps=1),
                output_dir=Path(temp),
            )
            report = AlphaValidationSystem(rows, config).run()
            self.assertGreaterEqual(report.robustness_score, 0)
            self.assertEqual(len(report.baseline.windows), 3)
            self.assertTrue((Path(temp) / "validation_report.json").exists())
            self.assertTrue((Path(temp) / "windows.csv").exists())
            self.assertTrue((Path(temp) / "trades.csv").exists())

    def test_zero_latency_executes_on_signal_snapshot(self) -> None:
        rows = HybridProxyData(seed=42, markets=2, steps=80).generate()
        result = WalkForwardEngine(
            windows=2,
            simulator_config=SimulatorConfig(latency_steps=0),
        ).run(rows, "zero-latency", "execution_latency", 0.0)
        self.assertGreater(result.trades, 0)
        self.assertTrue(all(trade.entry_delay_steps == 0 for trade in result.trade_log))


if __name__ == "__main__":
    unittest.main()
