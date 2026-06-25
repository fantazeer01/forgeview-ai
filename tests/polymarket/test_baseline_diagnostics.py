from __future__ import annotations

import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from polymarket.baseline_diagnostics.runner import (
    DiagnosticsConfig,
    DiagnosticsRunner,
)


class BaselineDiagnosticsTests(unittest.TestCase):
    def test_required_artifacts_and_single_conclusion(self) -> None:
        with _workspace_temp() as folder:
            runner = _runner(Path(folder))
            report = runner.run()
            self.assertIn(report["conclusion"], {
                "NO_INFORMATION_BEYOND_YES_PRICE",
                "WEAK_INFORMATION_PRESENT",
                "REGIME_SPECIFIC_SIGNAL_PRESENT",
                "FEATURE_SET_INCOMPLETE",
            })
            for name in (
                "diagnostics_report.md", "diagnostics_report.json",
                "segment_metrics.csv", "feature_diagnostics.csv",
                "calibration_analysis.csv", "regime_analysis.csv",
            ):
                self.assertTrue((Path(folder) / name).exists())

    def test_diagnostics_are_deterministic_and_verifiable(self) -> None:
        with _workspace_temp() as folder:
            root = Path(folder)
            runner = _runner(root)
            first = runner.run()
            before = {
                path.name: path.read_bytes() for path in root.iterdir()
            }
            second = runner.run()
            self.assertEqual(first, second)
            self.assertEqual(
                before, {path.name: path.read_bytes() for path in root.iterdir()}
            )
            self.assertEqual(runner.verify(), first)

    def test_holdout_labels_are_never_opened(self) -> None:
        with _workspace_temp() as folder:
            original_open = Path.open

            def guarded_open(path, *args, **kwargs):
                if path.name == "sealed_holdout_labels.csv":
                    raise AssertionError("sealed holdout must not be opened")
                return original_open(path, *args, **kwargs)

            with patch.object(Path, "open", guarded_open):
                report = _runner(Path(folder)).run()
            self.assertTrue(report["holdout"]["sealed"])
            self.assertFalse(report["holdout"]["outcomes_read"])

    def test_fixed_groups_and_required_segments_are_reported(self) -> None:
        with _workspace_temp() as folder:
            report = _runner(Path(folder)).run()
            self.assertEqual(
                set(report["feature_group_tests"]),
                {
                    "yes_calibration", "market_only", "external_only",
                    "lag_only", "yes_plus_external", "yes_plus_lag",
                    "yes_plus_market_dynamics", "combined_baseline",
                },
            )
            segments = {row["segment"] for row in report["segments"]}
            self.assertTrue({
                "asset_BTC", "asset_ETH", "asset_SOL",
                "window_early", "window_middle", "window_late",
                "volatility_low", "volatility_medium", "volatility_high",
                "lag_low", "lag_medium", "lag_high",
            } <= segments)

    def test_redundancy_and_exactly_one_recommendation_are_recorded(self) -> None:
        with _workspace_temp() as folder:
            report = _runner(Path(folder)).run()
            pairs = {
                (row["left"], row["right"])
                for row in report["feature_stability"]["redundancies"]
            }
            self.assertIn(("yes_price", "yes_no_spread"), pairs)
            self.assertTrue(report["recommendation"]["exactly_one"])


def _runner(output: Path) -> DiagnosticsRunner:
    return DiagnosticsRunner(DiagnosticsConfig(
        protocol_root=Path("polymarket/data/validation_protocol/v1"),
        baseline_root=Path("polymarket/models/baseline_v1"),
        output_root=output,
    ))


@contextmanager
def _workspace_temp():
    root = Path("tests/polymarket")
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as folder:
        yield folder
