from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .simulator import (
    RepricingConfig,
    build_repricing_dataset,
    simulate_repricing_strategy,
    write_outputs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repricing-research",
        description="Development-only Polymarket probability repricing research",
    )
    parser.add_argument("--session", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--target", type=float, default=0.03)
    parser.add_argument("--stop-loss", type=float, default=0.03)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--slippage", type=float, default=0.02)
    parser.add_argument("--min-seconds-to-expiry", type=float, default=35.0)
    parser.add_argument("--signal-reason", action="append")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config_kwargs = {
        "repricing_target": args.target,
        "stop_loss": args.stop_loss,
        "max_holding_seconds": args.timeout,
        "conservative_slippage": args.slippage,
        "min_seconds_to_expiry": args.min_seconds_to_expiry,
    }
    if args.signal_reason:
        config_kwargs["signal_reasons"] = tuple(args.signal_reason)
    config = RepricingConfig(**config_kwargs)
    rows = build_repricing_dataset(args.session, config)
    summary = simulate_repricing_strategy(rows)
    if args.output:
        write_outputs(args.output, rows, summary)
    print(json.dumps(asdict(summary), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
