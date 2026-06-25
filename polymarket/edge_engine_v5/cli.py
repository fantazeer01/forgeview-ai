from __future__ import annotations

import argparse
import json
from pathlib import Path

from polymarket.edge_engine_v4.config import SUPPORTED_ASSETS

from .config import CaptureConfig
from .long_capture import LongShadowCapture
from .replay import replay_capture
from .diagnostics import diagnostics_dict, inspect_session
from .live_console import LifecycleConsole, LiveConsole


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="edge-engine-v5",
        description="Long-running BTC/ETH/SOL shadow capture and edge evidence",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture", help="Run a rotating long shadow capture")
    capture.add_argument("--assets", nargs="+", choices=SUPPORTED_ASSETS, default=list(SUPPORTED_ASSETS))
    capture.add_argument("--duration", type=float, default=3_600.0)
    capture.add_argument("--poll-interval", type=float, default=2.0)
    capture.add_argument("--discovery-interval", type=float, default=30.0)
    capture.add_argument("--output-root", type=Path, default=Path("polymarket/runs/v5"))
    capture.add_argument("--mock", action="store_true")
    capture.add_argument("--no-mock-fallback", action="store_true")
    capture.add_argument("--min-completed-windows", type=int, default=30)
    capture.add_argument("--min-shadow-trades", type=int, default=20)
    capture.add_argument("--min-entry-seconds", type=float, default=60.0)
    capture.add_argument("--external-move-threshold-bps", type=float, default=8.0)
    capture.add_argument("--repricing-ratio", type=float, default=0.50)
    capture.add_argument("--min-confidence", type=float, default=0.65)

    live = commands.add_parser("live", help="Print live market analysis while capturing evidence")
    live.add_argument("--assets", nargs="+", choices=SUPPORTED_ASSETS, default=list(SUPPORTED_ASSETS))
    live.add_argument("--duration", type=float, default=3_600.0)
    live.add_argument("--poll-interval", type=float, default=5.0)
    live.add_argument("--discovery-interval", type=float, default=5.0)
    live.add_argument("--output-root", type=Path, default=Path("polymarket/runs/v5"))
    live.add_argument("--min-confidence", type=float, default=0.65)
    live.add_argument("--quiet", action="store_true")
    live.add_argument("--show-skipped", action="store_true")
    live.add_argument("--mock", action="store_true")
    live.add_argument("--no-mock-fallback", action="store_true")
    live.add_argument("--min-entry-seconds", type=float, default=60.0)

    lifecycle = commands.add_parser(
        "lifecycle",
        help="Track current five-minute market lifecycles without signal-focused output",
    )
    lifecycle.add_argument(
        "--assets", nargs="+", choices=SUPPORTED_ASSETS,
        default=list(SUPPORTED_ASSETS),
    )
    lifecycle.add_argument("--duration", type=float, default=600.0)
    lifecycle.add_argument("--poll-interval", type=float, default=1.0)
    lifecycle.add_argument("--discovery-interval", type=float, default=1.0)
    lifecycle.add_argument(
        "--output-root", type=Path, default=Path("polymarket/runs/v5")
    )
    lifecycle.add_argument("--quiet", action="store_true")
    lifecycle.add_argument("--mock", action="store_true")
    lifecycle.add_argument("--no-mock-fallback", action="store_true")

    replay = commands.add_parser("replay", help="Deterministically replay session.jsonl")
    replay.add_argument("--session", type=Path, required=True)
    replay.add_argument("--output", type=Path)

    inspect = commands.add_parser("inspect", help="Inspect a v5 session without replaying it")
    inspect.add_argument("--session", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "inspect":
            diagnostics = diagnostics_dict(inspect_session(args.session))
            print(json.dumps(diagnostics, indent=2))
            return 0
        if args.command == "replay":
            output, report = replay_capture(args.session, args.output)
        else:
            is_live = args.command == "live"
            is_lifecycle = args.command == "lifecycle"
            config = CaptureConfig(
                assets=tuple(args.assets),
                duration_seconds=args.duration,
                poll_interval_seconds=args.poll_interval,
                discovery_interval_seconds=args.discovery_interval,
                output_root=args.output_root,
                mock=args.mock,
                allow_mock_fallback=not args.no_mock_fallback,
                lifecycle_only=is_lifecycle,
                min_entry_seconds_remaining=(
                    args.min_entry_seconds
                    if not is_lifecycle else 60.0
                ),
                external_move_threshold_bps=(
                    args.external_move_threshold_bps
                    if not (is_live or is_lifecycle) else 8.0
                ),
                repricing_ratio=(
                    args.repricing_ratio
                    if not (is_live or is_lifecycle) else 0.50
                ),
                min_confidence=(
                    args.min_confidence if not is_lifecycle else 0.65
                ),
                min_completed_windows=(
                    30 if (is_live or is_lifecycle) else args.min_completed_windows
                ),
                min_shadow_trades=(
                    20 if (is_live or is_lifecycle) else args.min_shadow_trades
                ),
            )
            console = (
                LiveConsole(args.quiet, args.show_skipped)
                if is_live
                else LifecycleConsole(quiet=args.quiet, show_skipped=True)
                if is_lifecycle
                else None
            )
            output, report = LongShadowCapture(
                config, live_console=console
            ).run()
    except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 2
    metrics = report["metrics"]
    print("\nV5 EDGE EVIDENCE")
    print(f"Verdict: {report['verdict']}")
    print(f"Completed windows: {metrics['completed_market_windows']}")
    print(f"Opportunities: {metrics['opportunities_detected']}")
    print(f"Shadow trades: {metrics['shadow_trades']}")
    print(f"Simulated P&L: ${metrics['simulated_pnl']:+,.2f}")
    print(f"Reference coverage: {metrics['reference_coverage_percentage']:.2f}%")
    print(f"Data gaps: {metrics['data_gap_percentage']:.2f}%")
    print(f"Artifacts: {Path(output).resolve()}")
    return 0
