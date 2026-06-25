from __future__ import annotations

import argparse
import json
from pathlib import Path

from .protocol import ProtocolConfig, ValidationProtocol


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="polymarket-validation-protocol")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("freeze", "inspect", "verify"):
        command = commands.add_parser(name)
        command.add_argument(
            "--dataset",
            type=Path,
            default=Path("polymarket/data/training/public_only.csv"),
        )
        command.add_argument(
            "--output-root",
            type=Path,
            default=Path("polymarket/data/validation_protocol/v1"),
        )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    protocol = ValidationProtocol(ProtocolConfig(
        dataset_path=args.dataset,
        output_root=args.output_root,
    ))
    try:
        if args.command == "freeze":
            manifest = protocol.freeze()
            heading = "VALIDATION PROTOCOL FROZEN"
        elif args.command == "verify":
            manifest = protocol.verify()
            heading = "VALIDATION PROTOCOL VERIFIED"
        else:
            manifest = protocol.inspect()
            heading = "VALIDATION PROTOCOL"
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 2

    counts = manifest["splits"]["row_counts"]
    print(heading)
    print(f"Protocol: {manifest['protocol_id']}")
    print(f"Source rows: {manifest['source']['row_count']}")
    print(
        "Rows: "
        f"train={counts['train']} validation={counts['validation']} "
        f"holdout={counts['holdout']} excluded={counts['excluded']}"
    )
    print(f"Holdout labels sealed: {manifest['holdout']['labels_sealed']}")
    print(f"Manifest: {args.output_root / 'protocol_manifest.json'}")
    return 0
