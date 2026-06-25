from __future__ import annotations

import argparse
from pathlib import Path

from .report import build_validation_report


parser = argparse.ArgumentParser(prog="polymarket-microstructure-validation")
parser.add_argument("--session", type=Path, required=True)
parser.add_argument("--replay-report", type=Path, required=True)
parser.add_argument("--feature-export", type=Path, required=True)
parser.add_argument("--feature-export-repeat", type=Path, required=True)
parser.add_argument(
    "--output-root", type=Path,
    default=Path("polymarket/microstructure_validation_v1"),
)
args = parser.parse_args()
report = build_validation_report(
    args.session, args.replay_report, args.feature_export,
    args.feature_export_repeat, args.output_root,
)
print(f"Decision: {report['decision']}")
print(f"Microstructure events: {report['capture']['microstructure_events']}")
print(f"Replay compatible: {report['replay']['compatible']}")
