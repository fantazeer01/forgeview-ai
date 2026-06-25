from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from .reconcile import reconcile
from .resolver import GammaResolutionClient, parse_resolution
from .sessions import collect_markets
from .storage import (
    read_raw,
    read_raw_retrieval_times,
    write_raw,
    write_resolutions,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="polymarket-resolution-engine")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("reconcile", "replay"):
        command = commands.add_parser(name)
        command.add_argument(
            "--runs-root", type=Path, default=Path("polymarket/runs/v5")
        )
        command.add_argument(
            "--output-root",
            type=Path,
            default=Path("polymarket/data/resolutions"),
        )
        command.add_argument(
            "--proxy-dataset",
            type=Path,
            default=None,
        )
        command.add_argument("--fixture", type=Path)
    commands.choices["reconcile"].add_argument("--timeout", type=float, default=15.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    markets = collect_markets(args.runs_root)
    retrieved = datetime.now(timezone.utc)
    try:
        proxy_dataset = args.proxy_dataset or _build_proxy_dataset(
            args.runs_root, args.output_root
        )
        if args.command == "replay":
            fixture = args.fixture or args.output_root / "raw_gamma_events.jsonl"
            raw_by_id = read_raw(fixture)
            retrieval_by_id = read_raw_retrieval_times(fixture)
            raw_rows = None
        elif args.fixture:
            raw_by_id = read_raw(args.fixture)
            retrieval_by_id = read_raw_retrieval_times(args.fixture)
            raw_rows = None
        else:
            client = GammaResolutionClient(args.timeout)
            raw_by_id = {}
            retrieval_by_id = {}
            raw_rows = []
            for market in markets:
                try:
                    event = client.fetch_event(market.slug)
                except OSError:
                    event = None
                raw_by_id[market.market_id] = event
                retrieval_by_id[market.market_id] = retrieved
                raw_rows.append({
                    "market_id": market.market_id,
                    "slug": market.slug,
                    "retrieval_timestamp": retrieved.isoformat(),
                    "event": event,
                })
        records = [
            parse_resolution(
                market,
                raw_by_id.get(market.market_id),
                retrieval_by_id.get(market.market_id, retrieved),
            )
            for market in markets
        ]
        args.output_root.mkdir(parents=True, exist_ok=True)
        if raw_rows is not None:
            write_raw(args.output_root / "raw_gamma_events.jsonl", raw_rows)
        write_resolutions(args.output_root / "resolutions.jsonl", records)
        report = reconcile(records, proxy_dataset, args.output_root)
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}")
        return 2
    print("AUTHORITATIVE RESOLUTION RECONCILIATION")
    print(f"Markets: {report['total_markets']}")
    print(f"Resolved: {report['resolved']}")
    print(f"Matched proxy: {report['matched']}")
    print(f"Mismatched proxy: {report['mismatched']}")
    print(f"Unresolved/missing: {report['unresolved'] + report['missing']}")
    print(f"Coverage: {report['authoritative_coverage_percentage']:.2f}%")
    print(f"Agreement: {report['agreement_percentage']:.2f}%")
    print(f"Artifacts: {args.output_root}")
    return 0


def _build_proxy_dataset(runs_root: Path, output_root: Path) -> Path:
    from polymarket.feature_engine.config import FeatureConfig
    from polymarket.feature_engine.dataset_builder import DatasetBuilder

    proxy_root = output_root / "proxy_reference_dataset"
    result = DatasetBuilder(FeatureConfig(
        runs_root=runs_root,
        output_root=proxy_root,
        resolutions_path=output_root / "_proxy_mode_no_resolutions.jsonl",
        allow_proxy_labels=True,
        max_missing_features_per_row=20,
    )).build()
    return result.csv_path
