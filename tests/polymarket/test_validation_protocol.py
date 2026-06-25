from __future__ import annotations

import csv
import json
import tempfile
import unittest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from polymarket.feature_engine.schema import COLUMNS
from polymarket.validation_protocol.cli import main
from polymarket.validation_protocol.protocol import (
    LABEL_COLUMNS,
    ProtocolConfig,
    ValidationProtocol,
    load_development_rows,
)


class ValidationProtocolTests(unittest.TestCase):
    def test_chronological_splits_and_boundary_exclusion(self) -> None:
        with _workspace_temp() as folder:
            dataset = _write_dataset(Path(folder) / "public.csv", windows=20)
            root = Path(folder) / "protocol"
            manifest = ValidationProtocol(ProtocolConfig(
                dataset_path=dataset, output_root=root,
            )).freeze()
            assignments = _rows(root / "split_assignments.csv")

            by_window = {}
            for row in assignments:
                by_window.setdefault(row["window_start"], set()).add(
                    row["assignment"]
                )
            self.assertTrue(all(len(value) == 1 for value in by_window.values()))
            self.assertEqual(manifest["splits"]["window_counts"]["excluded"], 4)
            self.assertEqual(
                sum(manifest["splits"]["row_counts"].values()), 60
            )
            active = [
                row for row in assignments if row["assignment"] != "excluded"
            ]
            order = {"train": 0, "validation": 1, "holdout": 2}
            ranks = [order[row["assignment"]] for row in active]
            self.assertEqual(ranks, sorted(ranks))

    def test_holdout_labels_are_sealed_from_development_loader(self) -> None:
        with _workspace_temp() as folder:
            dataset = _write_dataset(Path(folder) / "public.csv", windows=20)
            root = Path(folder) / "protocol"
            manifest = ValidationProtocol(ProtocolConfig(
                dataset_path=dataset, output_root=root,
            )).freeze()
            train, validation = load_development_rows(root)
            holdout_features = _rows(root / "holdout_features.csv")

            self.assertTrue(train)
            self.assertTrue(validation)
            self.assertTrue(holdout_features)
            self.assertTrue(
                all(column not in holdout_features[0] for column in LABEL_COLUMNS)
            )
            self.assertTrue(manifest["holdout"]["labels_sealed"])
            self.assertNotIn("class_balance", manifest["holdout"])

    def test_freeze_is_byte_deterministic_and_hash_verified(self) -> None:
        with _workspace_temp() as folder:
            dataset = _write_dataset(Path(folder) / "public.csv", windows=20)
            root = Path(folder) / "protocol"
            protocol = ValidationProtocol(ProtocolConfig(
                dataset_path=dataset, output_root=root,
            ))
            first = protocol.freeze()
            bytes_before = {
                path.name: path.read_bytes() for path in root.iterdir()
            }
            second = protocol.freeze()

            self.assertEqual(first, second)
            self.assertEqual(
                bytes_before,
                {path.name: path.read_bytes() for path in root.iterdir()},
            )
            self.assertEqual(protocol.verify(), first)

    def test_verify_rejects_tampered_artifact(self) -> None:
        with _workspace_temp() as folder:
            dataset = _write_dataset(Path(folder) / "public.csv", windows=20)
            root = Path(folder) / "protocol"
            protocol = ValidationProtocol(ProtocolConfig(
                dataset_path=dataset, output_root=root,
            ))
            protocol.freeze()
            with (root / "train.csv").open("a", encoding="utf-8") as handle:
                handle.write("tampered\n")
            with self.assertRaisesRegex(ValueError, "artifact hash mismatch"):
                protocol.verify()

    def test_rejects_mock_or_non_authoritative_rows(self) -> None:
        with _workspace_temp() as folder:
            dataset = _write_dataset(Path(folder) / "public.csv", windows=20)
            rows = _rows(dataset)
            rows[0]["market_source"] = "mock"
            _write_rows(dataset, rows)
            with self.assertRaisesRegex(ValueError, "public rows only"):
                ValidationProtocol(ProtocolConfig(
                    dataset_path=dataset,
                    output_root=Path(folder) / "protocol",
                )).freeze()

    def test_cli_freeze_inspect_and_verify(self) -> None:
        with _workspace_temp() as folder:
            dataset = _write_dataset(Path(folder) / "public.csv", windows=20)
            root = Path(folder) / "protocol"
            common = ["--dataset", str(dataset), "--output-root", str(root)]
            self.assertEqual(main(["freeze", *common]), 0)
            self.assertEqual(main(["inspect", *common]), 0)
            self.assertEqual(main(["verify", *common]), 0)


def _write_dataset(path: Path, windows: int) -> Path:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows = []
    for window in range(windows):
        window_start = start + timedelta(minutes=5 * window)
        window_end = window_start + timedelta(minutes=5)
        for asset in ("BTC", "ETH", "SOL"):
            row = {column: "0" for column in COLUMNS}
            row.update({
                "market_id": f"{asset}-{window:03d}",
                "asset": asset,
                "market_source": "public",
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
                "feature_timestamp": (
                    window_start + timedelta(seconds=60)
                ).isoformat(),
                "outcome": str((window + len(asset)) % 2),
                "resolution_timestamp": (
                    window_end + timedelta(seconds=30)
                ).isoformat(),
                "label_source": "polymarket_gamma_resolved",
                "source_session": "fixture/session.jsonl",
            })
            rows.append(row)
    _write_rows(path, rows)
    return path


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@contextmanager
def _workspace_temp():
    root = Path("tests/polymarket")
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as folder:
        yield folder
