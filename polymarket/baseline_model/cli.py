from __future__ import annotations

import argparse
from pathlib import Path

from .runner import BaselineConfig, BaselineRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="polymarket-baseline-model")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "inspect", "verify"):
        command = commands.add_parser(name)
        command.add_argument(
            "--protocol-root",
            type=Path,
            default=Path("polymarket/data/validation_protocol/v1"),
        )
        command.add_argument(
            "--output-root",
            type=Path,
            default=Path("polymarket/models/baseline_v1"),
        )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runner = BaselineRunner(BaselineConfig(
        protocol_root=args.protocol_root,
        output_root=args.output_root,
    ))
    try:
        if args.command == "run":
            report = runner.run()
            heading = "BASELINE DEVELOPMENT EVALUATION COMPLETE"
        elif args.command == "verify":
            report = runner.verify()
            heading = "BASELINE DEVELOPMENT EVALUATION VERIFIED"
        else:
            report = runner.inspect()
            heading = "BASELINE DEVELOPMENT EVALUATION"
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}")
        return 2
    print(heading)
    print(f"Verdict: {report['verdict']}")
    print(f"Best model: {report['best_model']}")
    print(f"Validation rows: {report['data']['validation_rows']}")
    print(f"Holdout sealed: {report['holdout']['sealed']}")
    print(f"Report: {args.output_root / 'validation_report.json'}")
    return 0
