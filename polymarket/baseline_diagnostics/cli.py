from __future__ import annotations

import argparse
from pathlib import Path

from .runner import DiagnosticsConfig, DiagnosticsRunner


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="polymarket-baseline-diagnostics")
    parser.add_argument(
        "command", choices=("run", "inspect", "verify"), nargs="?", default="run"
    )
    parser.add_argument(
        "--protocol-root", type=Path,
        default=Path("polymarket/data/validation_protocol/v1"),
    )
    parser.add_argument(
        "--baseline-root", type=Path,
        default=Path("polymarket/models/baseline_v1"),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("polymarket/models/baseline_diagnostics_v1"),
    )
    args = parser.parse_args(argv)
    runner = DiagnosticsRunner(DiagnosticsConfig(
        protocol_root=args.protocol_root,
        baseline_root=args.baseline_root,
        output_root=args.output_root,
    ))
    try:
        report = (
            runner.run() if args.command == "run"
            else runner.verify() if args.command == "verify"
            else runner.inspect()
        )
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}")
        return 2
    print("BASELINE FAILURE DIAGNOSTICS")
    print(f"Conclusion: {report['conclusion']}")
    print(f"Strongest finding: {report['strongest_finding']}")
    print(f"Holdout sealed: {report['holdout']['sealed']}")
    print(f"Report: {args.output_root / 'diagnostics_report.json'}")
    return 0
