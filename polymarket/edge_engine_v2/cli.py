from __future__ import annotations

import argparse
import json
from pathlib import Path

from .data import (
    HybridProxyData,
    PolymarketHistoryClient,
    ReplayStore,
    prices_to_causal_proxy,
)
from .models import to_dict
from .simulator import SimulatorConfig
from .validation import AlphaValidationSystem, ValidationConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="edge-engine-v2",
        description="Polymarket Edge Engine v2 — deterministic alpha validation",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Run complete walk-forward robustness validation")
    run.add_argument("--input", type=Path, help="Replayable JSONL dataset; offline hybrid proxy by default")
    run.add_argument("--output", type=Path, default=Path("polymarket/runs/v2/latest"))
    run.add_argument("--seed", type=int, default=42)
    run.add_argument("--windows", type=int, default=6)
    run.add_argument("--stake", type=float, default=100.0)
    run.add_argument("--slippage-bps", type=float, default=10.0)
    run.add_argument("--latency", type=int, default=1)
    run.add_argument("--timeout", type=int, default=8)

    fetch = commands.add_parser("fetch", help="Fetch public Polymarket token price history into replay JSONL")
    fetch.add_argument("--token-id", required=True)
    fetch.add_argument("--output", type=Path, required=True)
    fetch.add_argument("--market-id")
    fetch.add_argument("--question", default="Polymarket historical token")
    fetch.add_argument("--interval", default="max", choices=["max", "all", "1m", "1w", "1d", "6h", "1h"])
    fetch.add_argument("--fidelity", type=int, default=60)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "fetch":
            history = PolymarketHistoryClient().fetch(
                args.token_id, interval=args.interval, fidelity=args.fidelity
            )
            rows = prices_to_causal_proxy(
                history, args.market_id or args.token_id, args.question
            )
            destination = ReplayStore.save(rows, args.output)
            print(f"Saved {len(rows)} replayable snapshots to {destination.resolve()}")
            return 0

        if args.input:
            snapshots = ReplayStore.load(args.input)
            source = str(args.input)
        else:
            snapshots = HybridProxyData(seed=args.seed).generate()
            source = "deterministic hybrid proxy"
            ReplayStore.save(snapshots, args.output / "dataset.jsonl")

        simulator = SimulatorConfig(
            stake=args.stake,
            slippage_bps=args.slippage_bps,
            latency_steps=args.latency,
            timeout_steps=args.timeout,
        )
        config = ValidationConfig(
            seed=args.seed,
            windows=args.windows,
            simulator=simulator,
            output_dir=args.output,
        )
        report = AlphaValidationSystem(snapshots, config).run()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 2

    print("\nALPHA VALIDATION RESULT")
    print(f"Data: {source}")
    print(f"Baseline P&L: ${report.baseline.pnl:,.2f}")
    for window in report.baseline.windows:
        print(
            f"  Window {window.window_id}: P&L ${window.pnl:+,.2f} | "
            f"trades {window.trades} | drawdown {window.max_drawdown:.2%}"
        )
    print(f"Robustness score: {report.robustness_score:.2f}/100")
    print(f"Noise: {'YES' if report.answers['noise'] else 'NO'}")
    print(f"Different periods: {'YES' if report.answers['time_periods'] else 'NO'}")
    print(f"Execution delay: {'YES' if report.answers['execution_delay'] else 'NO'}")
    print(f"Signal lag: {'YES' if report.answers['signal_lag'] else 'NO'}")
    print(f"Verdict: {report.verdict}")
    print(f"Artifacts: {args.output.resolve()}")
    return 0
