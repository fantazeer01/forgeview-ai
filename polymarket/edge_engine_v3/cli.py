from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from .live_data import PolymarketPollingFeed, PolymarketWebSocketFeed
from .features import CausalLiveFeatureBuilder, ExternalReferenceStore
from .session import LiveSessionStore
from .shadow import ShadowExecutionEngine
from .validation import LiveAlphaValidator, LiveValidationConfig


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="edge-engine-v3",
        description="Read-only Polymarket live shadow alpha validation",
    )
    commands = root.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture", help="Capture live data, then shadow-validate it")
    capture.add_argument("--token-id", action="append", required=True)
    capture.add_argument("--duration", type=int, default=300)
    capture.add_argument("--transport", choices=["websocket", "poll"], default="websocket")
    capture.add_argument("--session", type=Path, default=Path("polymarket/runs/v3/latest/session"))
    _common(capture)

    replay = commands.add_parser("replay", help="Deterministically replay a captured live session")
    replay.add_argument("--session", type=Path, required=True)
    _common(replay)
    return root


def _common(command: argparse.ArgumentParser) -> None:
    command.add_argument("--output", type=Path, default=Path("polymarket/runs/v3/latest"))
    command.add_argument(
        "--model-report",
        type=Path,
        default=Path("polymarket/runs/v2/latest/validation_report.json"),
    )
    command.add_argument("--reference-file", type=Path)
    command.add_argument("--minimum-trades", type=int, default=30)


async def _capture(args: argparse.Namespace) -> list:
    store = LiveSessionStore(args.session)
    feed = PolymarketWebSocketFeed() if args.transport == "websocket" else PolymarketPollingFeed()
    ticks = []
    external = ExternalReferenceStore(args.reference_file) if args.reference_file else None
    features = CausalLiveFeatureBuilder(external)
    shadow = ShadowExecutionEngine()
    last_bucket: dict[str, int] = {}
    async for raw, tick in feed.stream(args.token_id, args.duration):
        store.append(raw, tick)
        ticks.append(tick)
        bucket = int(tick.timestamp.timestamp())
        if last_bucket.get(tick.market_id) != bucket:
            decision = shadow.on_snapshot(features.build(tick))
            last_bucket[tick.market_id] = bucket
            print(
                f"{tick.timestamp.isoformat()} {tick.token_id[:12]} "
                f"bid={tick.best_bid:.4f} ask={tick.best_ask:.4f} "
                f"score={decision.score:.3f} action={decision.action}"
            )
    if not ticks:
        raise ValueError("Live capture completed without usable quote ticks")
    return ticks


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        ticks = asyncio.run(_capture(args)) if args.command == "capture" else LiveSessionStore.load_ticks(args.session)
        config = LiveValidationConfig(
            model_report=args.model_report,
            output_dir=args.output,
            reference_file=args.reference_file,
            minimum_trades=args.minimum_trades,
        )
        report = LiveAlphaValidator(ticks, config).run()
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2
    print("\nREAL-MARKET VALIDATION")
    print(f"Live simulated P&L: ${report.live_simulated_pnl:+,.2f}")
    print(f"Model/live divergence: {report.divergence_score:.2f}/100")
    print(f"Signal drift: {report.signal_drift_score:.2f}/100")
    print(f"Edge decay: {report.edge_decay_score:.2f}/100")
    print(f"Stability: {report.stability_score:.2f}/100")
    print(f"Evidence sufficient: {'YES' if report.evidence_sufficient else 'NO'}")
    print(f"Verdict: {report.verdict}")
    print(f"Artifacts: {args.output.resolve()}")
    return 0
