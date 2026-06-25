from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from polymarket.baseline_model.cli import main
from polymarket.baseline_model.logistic import fit_logistic
from polymarket.baseline_model.metrics import probability_metrics
from polymarket.baseline_model.runner import BaselineConfig, BaselineRunner
from polymarket.feature_engine.schema import COLUMNS


class BaselineModelTests(unittest.TestCase):
    def test_probability_metrics_are_correct(self) -> None:
        metrics = probability_metrics([0, 1], [0.25, 0.75])
        self.assertAlmostEqual(metrics["brier_score"], 0.0625)
        self.assertAlmostEqual(metrics["log_loss"], 0.2876820725)
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertEqual(metrics["roc_auc"], 1.0)

    def test_logistic_fit_is_deterministic(self) -> None:
        matrix = [[1.0, -1.0], [1.0, -0.5], [1.0, 0.5], [1.0, 1.0]]
        outcomes = [0, 0, 1, 1]
        first = fit_logistic(matrix, outcomes)
        second = fit_logistic(matrix, outcomes)
        self.assertEqual(first, second)
        self.assertLess(first.predict([[1.0, -1.0]])[0], 0.5)
        self.assertGreater(first.predict([[1.0, 1.0]])[0], 0.5)

    def test_runner_is_deterministic_and_writes_required_outputs(self) -> None:
        with _workspace_temp() as folder:
            protocol = _write_protocol(Path(folder) / "protocol")
            output = Path(folder) / "models"
            runner = BaselineRunner(BaselineConfig(
                protocol_root=protocol, output_root=output
            ))
            first = runner.run()
            bytes_before = {
                path.relative_to(output): path.read_bytes()
                for path in output.rglob("*") if path.is_file()
            }
            second = runner.run()
            self.assertEqual(first, second)
            self.assertEqual(
                bytes_before,
                {
                    path.relative_to(output): path.read_bytes()
                    for path in output.rglob("*") if path.is_file()
                },
            )
            self.assertEqual(runner.verify(), first)
            for name in (
                "MODEL_CARD.md", "validation_report.json",
                "validation_report.md", "predictions_validation.csv",
                "feature_importance.csv", "training_config.json",
                "reproducibility_hashes.json",
            ):
                self.assertTrue((output / name).exists())

    def test_preprocessing_is_fitted_from_train_only(self) -> None:
        with _workspace_temp() as folder:
            protocol = _write_protocol(Path(folder) / "protocol")
            output = Path(folder) / "models"
            validation = _rows(protocol / "validation.csv")
            for row in validation:
                row["return_5s"] = "999999"
            _write_rows(protocol / "validation.csv", validation)
            manifest = json.loads(
                (protocol / "protocol_manifest.json").read_text(encoding="utf-8")
            )
            manifest["artifacts"]["validation.csv"]["sha256"] = _sha256(
                protocol / "validation.csv"
            )
            (protocol / "protocol_manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            report = BaselineRunner(BaselineConfig(
                protocol_root=protocol, output_root=output
            )).run()
            train_values = [
                float(row["return_5s"]) for row in _rows(protocol / "train.csv")
            ]
            expected_mean = sum(train_values) / len(train_values)
            actual = report["logistic_model"]["preprocessing"]["return_5s"]["mean"]
            self.assertAlmostEqual(actual, expected_mean)
            self.assertNotEqual(actual, 999999)

    def test_runner_never_opens_sealed_holdout_labels(self) -> None:
        with _workspace_temp() as folder:
            protocol = _write_protocol(Path(folder) / "protocol")
            output = Path(folder) / "models"
            original_open = Path.open

            def guarded_open(path, *args, **kwargs):
                if path.name == "sealed_holdout_labels.csv":
                    raise AssertionError("sealed holdout must not be opened")
                return original_open(path, *args, **kwargs)

            with patch.object(Path, "open", guarded_open):
                report = BaselineRunner(BaselineConfig(
                    protocol_root=protocol, output_root=output
                )).run()
            self.assertFalse(report["holdout"]["outcomes_read"])
            self.assertTrue(report["holdout"]["sealed"])

    def test_all_models_use_identical_validation_rows(self) -> None:
        with _workspace_temp() as folder:
            protocol = _write_protocol(Path(folder) / "protocol")
            output = Path(folder) / "models"
            report = BaselineRunner(BaselineConfig(
                protocol_root=protocol, output_root=output
            )).run()
            counts = {
                metrics["count"] for metrics
                in report["metrics"]["validation"]["overall"].values()
            }
            self.assertEqual(counts, {report["data"]["validation_rows"]})

    def test_cli_run_inspect_verify(self) -> None:
        with _workspace_temp() as folder:
            protocol = _write_protocol(Path(folder) / "protocol")
            output = Path(folder) / "models"
            common = [
                "--protocol-root", str(protocol),
                "--output-root", str(output),
            ]
            self.assertEqual(main(["run", *common]), 0)
            self.assertEqual(main(["inspect", *common]), 0)
            self.assertEqual(main(["verify", *common]), 0)


def _write_protocol(root: Path) -> Path:
    root.mkdir(parents=True)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    train = []
    validation = []
    for index in range(36):
        target = train if index < 24 else validation
        asset = ("BTC", "ETH", "SOL")[index % 3]
        outcome = int(index % 4 in (2, 3))
        signal = 0.002 if outcome else -0.002
        row = {column: "0" for column in COLUMNS}
        window_start = start + timedelta(minutes=5 * index)
        row.update({
            "market_id": f"market-{index}",
            "asset": asset,
            "market_source": "public",
            "window_start": window_start.isoformat(),
            "window_end": (window_start + timedelta(minutes=5)).isoformat(),
            "feature_timestamp": (
                window_start + timedelta(seconds=60)
            ).isoformat(),
            "return_5s": str(signal),
            "return_15s": str(signal),
            "return_30s": str(signal),
            "return_60s": str(signal),
            "momentum_short": str(signal),
            "momentum_medium": str(signal),
            "volatility_30s": "0.001",
            "volatility_60s": "0.001",
            "yes_price": "0.55" if outcome else "0.45",
            "no_price": "0.45" if outcome else "0.55",
            "yes_no_spread": "0.1" if outcome else "-0.1",
            "probability_change_15s": str(signal),
            "probability_change_30s": str(signal),
            "lag_score": "0.8" if outcome else "0.2",
            "confidence_score": "0.8",
            "detection_delay": "2",
            "early_window_flag": "1",
            "late_window_flag": "0",
            "outcome": str(outcome),
            "resolution_timestamp": (
                window_start + timedelta(minutes=6)
            ).isoformat(),
            "label_source": "polymarket_gamma_resolved",
            "source_session": "fixture/session.jsonl",
        })
        target.append(row)
    _write_rows(root / "train.csv", train)
    _write_rows(root / "validation.csv", validation)
    manifest = {
        "protocol_id": "fixture",
        "artifacts": {
            "train.csv": {"sha256": _sha256(root / "train.csv")},
            "validation.csv": {"sha256": _sha256(root / "validation.csv")},
        },
        "holdout": {"label_commitment_sha256": "sealed-fixture-hash"},
    }
    (root / "protocol_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (root / "sealed_holdout_labels.csv").write_text(
        "market_id,outcome\nforbidden,1\n", encoding="utf-8"
    )
    return root


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@contextmanager
def _workspace_temp():
    root = Path("tests/polymarket")
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as folder:
        yield folder
