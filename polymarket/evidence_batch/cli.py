from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import BatchConfig, EvidenceBatchPipeline
from polymarket.edge_engine_v5.power_preflight import inspect_windows_power


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="polymarket-evidence-batch")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Capture public data and process the batch")
    resume = commands.add_parser(
        "resume", help="Resume post-processing from an existing v5 session"
    )
    commands.add_parser(
        "preflight", help="Check Windows power settings for overnight capture"
    )
    for command in (run, resume):
        command.add_argument("--assets", nargs="+", default=["BTC", "ETH", "SOL"])
        command.add_argument(
            "--runs-root", type=Path, default=Path("polymarket/runs/v5")
        )
        command.add_argument(
            "--resolution-root",
            type=Path,
            default=Path("polymarket/data/resolutions"),
        )
        command.add_argument(
            "--training-root",
            type=Path,
            default=Path("polymarket/data/training"),
        )
        command.add_argument(
            "--batch-root",
            type=Path,
            default=Path("polymarket/runs/evidence_batches"),
        )
        command.add_argument(
            "--resolution-mode", choices=("refresh", "replay"), default="refresh"
        )
        command.add_argument("--resolution-fixture", type=Path)
    run.add_argument("--duration", type=float, default=21_600.0)
    run.add_argument("--poll-interval", type=float, default=2.0)
    run.add_argument("--discovery-interval", type=float, default=5.0)
    resume.add_argument("--session", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "preflight":
        result = inspect_windows_power()
        print("OVERNIGHT CAPTURE PREFLIGHT")
        print(f"Platform: {result.platform}")
        print(f"AC sleep timeout: {result.sleep_ac_seconds}")
        print(f"AC hibernate timeout: {result.hibernate_ac_seconds}")
        print(f"Safe for overnight: {str(result.safe_for_overnight).lower()}")
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        for command in result.commands:
            print(f"CHECK/SET: {command}")
        return 0 if result.safe_for_overnight else 2
    config = BatchConfig(
        assets=tuple(args.assets),
        duration_seconds=getattr(args, "duration", 21_600.0),
        poll_interval_seconds=getattr(args, "poll_interval", 2.0),
        discovery_interval_seconds=getattr(args, "discovery_interval", 5.0),
        runs_root=args.runs_root,
        resolution_root=args.resolution_root,
        training_root=args.training_root,
        batch_root=args.batch_root,
        resolution_mode=args.resolution_mode,
        resolution_fixture=args.resolution_fixture,
    )
    pipeline = EvidenceBatchPipeline(config)
    manifest_path, manifest = (
        pipeline.run()
        if args.command == "run"
        else pipeline.resume(args.session)
    )
    print("PUBLIC EVIDENCE BATCH")
    print(f"Status: {manifest['status']}")
    print(f"Verdict: {manifest['verdict']}")
    if manifest.get("dataset"):
        print(f"Clean rows: {manifest['dataset']['clean_rows']}")
        print(
            "Rows by asset: "
            f"{manifest['dataset']['rows_by_asset']}"
        )
        print(
            "Feature completeness: "
            f"{manifest['dataset']['feature_completeness_percentage']:.2f}%"
        )
    if manifest.get("failed_stage"):
        print(f"Failed stage: {manifest['failed_stage']}")
        print(f"Error: {manifest.get('error', '')}")
    print(f"Manifest: {manifest_path.resolve()}")
    return 0 if manifest["status"] == "completed" else 2
