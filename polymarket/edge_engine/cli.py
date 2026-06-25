from __future__ import annotations

import argparse
import json
from pathlib import Path

from .data import JsonLinesMarketDataProvider, MockMarketDataProvider
from .engine import EdgeEngine, EngineConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="edge-engine",
        description="Polymarket Edge Engine v1 — local paper trading research simulator",
    )
    parser.add_argument("--input", type=Path, help="Local JSONL market snapshots (default: mock scenario)")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("polymarket/runs/latest"),
        help="Run artifact directory",
    )
    parser.add_argument("--initial-cash", type=float, default=10_000.0)
    parser.add_argument("--stake", type=float, default=100.0, help="Notional cost per paper trade")
    parser.add_argument("--entry-threshold", type=float, default=0.7)
    parser.add_argument("--exit-threshold", type=float, default=0.3)
    parser.add_argument("--convergence", type=float, default=0.03)
    parser.add_argument("--timeout", type=int, default=3, help="Maximum market updates held")
    parser.add_argument("--slippage-bps", type=float, default=0.0)
    parser.add_argument("--keep-open", action="store_true", help="Do not liquidate positions at end of data")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    provider = JsonLinesMarketDataProvider(args.input) if args.input else MockMarketDataProvider()
    config = EngineConfig(
        initial_cash=args.initial_cash,
        stake_per_trade=args.stake,
        entry_threshold=args.entry_threshold,
        exit_threshold=args.exit_threshold,
        convergence_threshold=args.convergence,
        timeout_steps=args.timeout,
        slippage_bps=args.slippage_bps,
        close_at_end=not args.keep_open,
        output_dir=args.output,
        verbose=args.verbose,
    )

    try:
        summary = EdgeEngine(provider, config).run()
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2

    print("\nSIMULATION SUMMARY")
    print(json.dumps(summary, indent=2))
    print(f"\nArtifacts: {args.output.resolve()}")
    return 0
