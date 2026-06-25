from __future__ import annotations

import argparse
from pathlib import Path

from .config import FeatureConfig
from .dataset_builder import DatasetBuilder


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="polymarket-feature-engine")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("build", "inspect"):
        command = commands.add_parser(name)
        command.add_argument(
            "--runs-root", type=Path, default=Path("polymarket/runs/v5")
        )
        command.add_argument(
            "--output-root", type=Path, default=Path("polymarket/data/training")
        )
    build = commands.choices["build"]
    build.add_argument("--feature-anchor-seconds", type=float, default=60.0)
    build.add_argument("--boundary-tolerance-seconds", type=float, default=15.0)
    build.add_argument(
        "--resolutions",
        type=Path,
        default=Path("polymarket/data/resolutions/resolutions.jsonl"),
    )
    build.add_argument(
        "--allow-proxy-labels",
        action="store_true",
        help="Explicitly allow external reference-return labels when authoritative outcomes are absent",
    )
    build.add_argument("--asof-max-age-seconds", type=float, default=15.0)
    build.add_argument("--max-missing-features-per-row", type=int, default=2)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = FeatureConfig(
        runs_root=args.runs_root,
        output_root=args.output_root,
        resolutions_path=getattr(
            args,
            "resolutions",
            Path("polymarket/data/resolutions/resolutions.jsonl"),
        ),
        allow_proxy_labels=getattr(args, "allow_proxy_labels", False),
        asof_max_age_seconds=getattr(args, "asof_max_age_seconds", 15.0),
        max_missing_features_per_row=getattr(
            args, "max_missing_features_per_row", 2
        ),
        feature_anchor_seconds=getattr(args, "feature_anchor_seconds", 60.0),
        boundary_tolerance_seconds=getattr(
            args, "boundary_tolerance_seconds", 15.0
        ),
    )
    builder = DatasetBuilder(config)
    try:
        if args.command == "build":
            result = builder.build()
            summary = result.summary
            print("FEATURE DATASET BUILT")
        else:
            summary = builder.inspect()
            print("FEATURE DATASET INSPECTION")
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}")
        return 2
    balance = summary.get("class_balance", {})
    print(f"Total samples: {summary.get('total_samples', 0)}")
    print(f"Assets: {summary.get('assets', {})}")
    print(f"UP count: {balance.get('UP', 0)}")
    print(f"DOWN count: {balance.get('DOWN', 0)}")
    print(f"Feature count: {summary.get('feature_count', 0)}")
    print(f"Missing values: {summary.get('total_missing_values', 0)}")
    print(f"Dataset path: {config.output_root / 'dataset.csv'}")
    return 0
