from __future__ import annotations

import argparse
from pathlib import Path

from polymarket.feature_engine.export import write_csv, write_parquet

from .analyzer import DatasetQualityAnalyzer, QualityMetrics
from .filters import public_only, to_training_rows
from .report import write_quality_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="polymarket-dataset-quality")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("analyze", "build-public"):
        command = commands.add_parser(name)
        command.add_argument(
            "--dataset",
            type=Path,
            default=Path("polymarket/data/training/dataset.csv"),
        )
        command.add_argument(
            "--output-root",
            type=Path,
            default=Path("polymarket/data/training"),
        )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    analyzer = DatasetQualityAnalyzer(args.dataset)
    try:
        metrics = analyzer.analyze()
        if args.command == "build-public":
            _, rows = analyzer.load_rows()
            selected = to_training_rows(public_only(rows))
            write_csv(args.output_root / "public_only.csv", selected)
            write_parquet(args.output_root / "public_only.parquet", selected)
            print(f"Public subset built: {len(selected)} samples")
        write_quality_report(args.output_root / "quality_report.json", metrics)
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}")
        return 2
    _print_metrics(metrics, args.output_root)
    return 0


def _print_metrics(metrics: QualityMetrics, output_root: Path) -> None:
    print("DATASET QUALITY")
    print(f"Total samples: {metrics.total_samples}")
    print(f"Public samples: {metrics.public_samples}")
    print(f"Mock samples: {metrics.mock_samples}")
    print(f"BTC: {metrics.asset_counts['BTC']}")
    print(f"ETH: {metrics.asset_counts['ETH']}")
    print(f"SOL: {metrics.asset_counts['SOL']}")
    print(f"UP count: {metrics.up_count}")
    print(f"DOWN count: {metrics.down_count}")
    print(f"Class imbalance: {metrics.class_imbalance_percentage:.2f}%")
    print(f"Missing values: {metrics.missing_values_percentage:.2f}%")
    print(
        f"Feature completeness: "
        f"{metrics.feature_completeness_percentage:.2f}%"
    )
    print(f"Duplicate rows: {metrics.duplicate_rows}")
    print(f"Quality score: {metrics.dataset_quality_score:.2f}/100")
    print(f"Training recommended: {str(metrics.training_recommended).lower()}")
    print(f"Reason: {metrics.reason}")
    print(f"Report: {output_root / 'quality_report.json'}")
