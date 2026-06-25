from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import SUPPORTED_ASSETS, ScannerConfig
from .scanner import CryptoLagScanner, replay_session


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="edge-engine-v4",
        description="BTC/ETH/SOL five-minute Polymarket lag scanner (shadow only)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    scan = commands.add_parser("scan", help="Discover and scan active crypto five-minute markets")
    scan.add_argument("--assets", nargs="+", choices=SUPPORTED_ASSETS, default=list(SUPPORTED_ASSETS))
    scan.add_argument("--duration", type=float, default=300.0)
    scan.add_argument("--poll-interval", type=float, default=2.0)
    scan.add_argument("--min-liquidity", type=float, default=500.0)
    scan.add_argument("--output", type=Path, default=Path("polymarket/runs/v4/latest"))
    scan.add_argument("--mock", action="store_true", help="Use deterministic offline feeds")
    scan.add_argument("--no-mock-fallback", action="store_true")

    replay = commands.add_parser("replay", help="Replay a saved v4 scanner session")
    replay.add_argument("--session", type=Path, required=True)
    replay.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "replay":
            summary = replay_session(args.session, args.output)
        else:
            config = ScannerConfig(
                assets=tuple(args.assets),
                duration_seconds=args.duration,
                poll_interval_seconds=args.poll_interval,
                min_liquidity=args.min_liquidity,
                output_dir=args.output,
                mock=args.mock,
                allow_mock_fallback=not args.no_mock_fallback,
            )
            summary = CryptoLagScanner(config).run()
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 2
    print("\nV4 CRYPTO LAG SCAN")
    print(json.dumps(summary, indent=2))
    output = args.output if getattr(args, "output", None) else args.session.parent
    print(f"Artifacts: {Path(output).resolve()}")
    return 0
