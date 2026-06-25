from __future__ import annotations

import csv
import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from polymarket.dataset_quality.analyzer import DatasetQualityAnalyzer
from polymarket.dataset_quality.cli import main
from polymarket.feature_engine.export import write_csv
from polymarket.feature_engine.schema import TrainingRow


class DatasetQualityTests(unittest.TestCase):
    def test_analyzer_counts_quality_dimensions(self) -> None:
        with _workspace_temp() as folder:
            root = Path(folder)
            dataset = root / "dataset.csv"
            rows = [
                _row("public-up", "BTC", "public", 1),
                _row("public-down", "ETH", "public", 0),
                _row("mock-up", "SOL", "mock", 1, detection_delay=None),
            ]
            write_csv(dataset, rows)
            metrics = DatasetQualityAnalyzer(dataset).analyze()

            self.assertEqual(metrics.total_samples, 3)
            self.assertEqual(metrics.public_samples, 2)
            self.assertEqual(metrics.mock_samples, 1)
            self.assertEqual(metrics.asset_counts, {"BTC": 1, "ETH": 1, "SOL": 1})
            self.assertEqual(metrics.public_only_sample_count, 2)
            self.assertGreater(metrics.missing_values, 0)
            self.assertFalse(metrics.training_recommended)

    def test_duplicates_are_detected(self) -> None:
        with _workspace_temp() as folder:
            dataset = Path(folder) / "dataset.csv"
            row = _row("same", "BTC", "public", 1)
            write_csv(dataset, [row, row])
            metrics = DatasetQualityAnalyzer(dataset).analyze()
            self.assertEqual(metrics.duplicate_rows, 1)
            self.assertEqual(metrics.duplicate_market_ids, 1)
            self.assertEqual(metrics.duplicate_rate_percentage, 50.0)

    def test_build_public_writes_csv_parquet_and_report(self) -> None:
        with _workspace_temp() as folder:
            root = Path(folder)
            dataset = root / "dataset.csv"
            output = root / "output"
            write_csv(dataset, [
                _row("public-up", "BTC", "public", 1),
                _row("mock-down", "ETH", "mock", 0),
            ])

            self.assertEqual(main([
                "build-public",
                "--dataset", str(dataset),
                "--output-root", str(output),
            ]), 0)
            with (output / "public_only.csv").open(encoding="utf-8") as handle:
                public_rows = list(csv.DictReader(handle))
            self.assertEqual(len(public_rows), 1)
            self.assertEqual(public_rows[0]["market_source"], "public")
            parquet = (output / "public_only.parquet").read_bytes()
            self.assertEqual(parquet[:4], b"PAR1")
            self.assertEqual(parquet[-4:], b"PAR1")
            report = json.loads(
                (output / "quality_report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["public_only_sample_count"], 1)

    def test_balanced_complete_public_dataset_is_recommended(self) -> None:
        with _workspace_temp() as folder:
            dataset = Path(folder) / "dataset.csv"
            rows = [
                _row(f"market-{index}", ("BTC", "ETH", "SOL")[index % 3],
                     "public", index % 2)
                for index in range(20)
            ]
            write_csv(dataset, rows)
            metrics = DatasetQualityAnalyzer(dataset).analyze()
            self.assertEqual(metrics.dataset_quality_score, 100.0)
            self.assertTrue(metrics.training_recommended)


def _row(
    market_id: str,
    asset: str,
    source: str,
    outcome: int,
    detection_delay: float | None = 5.0,
) -> TrainingRow:
    return TrainingRow(
        market_id=market_id,
        asset=asset,
        market_source=source,
        window_start="2026-01-01T12:00:00+00:00",
        window_end="2026-01-01T12:05:00+00:00",
        feature_timestamp="2026-01-01T12:01:00+00:00",
        market_age_seconds=60.0,
        seconds_to_expiry=240.0,
        return_5s=0.001,
        return_15s=0.002,
        return_30s=0.003,
        return_60s=0.004,
        momentum_short=-0.001,
        momentum_medium=-0.002,
        volatility_30s=0.01,
        volatility_60s=0.02,
        yes_price=0.51,
        no_price=0.49,
        yes_no_spread=0.02,
        probability_change_15s=0.01,
        probability_change_30s=0.02,
        lag_score=0.6,
        confidence_score=0.7,
        detection_delay=detection_delay,
        early_window_flag=1,
        late_window_flag=0,
        outcome=outcome,
        resolution_timestamp="2026-01-01T12:05:00+00:00",
        label_source="reference_window_return",
        source_session="test/session.jsonl",
    )


def _workspace_temp() -> tempfile.TemporaryDirectory:
    return tempfile.TemporaryDirectory(dir=Path("tests/polymarket"))


if __name__ == "__main__":
    unittest.main()
