"""CLI for research-only wallet-intelligence public data ingestion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .client import PolymarketPublicClient
from .behavior_metrics import compute_behavior_metrics
from .ingestion import ingest_wallets, inspect_outputs, summarize_outputs
from .trade_history import DEFAULT_FIXTURE, DEFAULT_FIXTURE_OUTPUT, run_fixture_ingestion
from .trade_history import DEFAULT_SMOKE_OUTPUT, run_bounded_public_smoke
from .lifecycle import DEFAULT_LIFECYCLE_INPUT, DEFAULT_LIFECYCLE_OUTPUT, run_lifecycle_fixture_reconstruction
from .lifecycle_metrics import DEFAULT_LIFECYCLE_METRICS_INPUT, DEFAULT_LIFECYCLE_METRICS_OUTPUT, run_lifecycle_metrics
from .wallet_score import DEFAULT_WALLET_SCORE_INPUT, DEFAULT_WALLET_SCORE_OUTPUT, run_wallet_score_fixture
from .wallet_watchlist import DEFAULT_WATCHLIST_INPUT, DEFAULT_WATCHLIST_OUTPUT, run_wallet_watchlist
from .copyability_sprint import DEFAULT_COPYABILITY_OUTPUT, run_wallet_copyability_sprint
from .market_outcome import (
    DEFAULT_MARKET_OUTCOME_INPUT,
    DEFAULT_MARKET_OUTCOME_OUTPUT,
    PublicMarketMetadataClient,
    run_market_outcome_resolution_sprint,
)
from .outcome_skill import (
    DEFAULT_WALLET_SKILL_INPUT,
    DEFAULT_WALLET_SKILL_OUTPUT,
    DEFAULT_WALLET_SKILL_SCORE_INPUT,
    DEFAULT_WALLET_SKILL_WATCHLIST_INPUT,
    run_wallet_outcome_skill_baseline,
)


DEFAULT_INPUT = Path("polymarket/wallet_intelligence/watched_wallets.example.csv")
DEFAULT_OUTPUT = Path("polymarket/data/wallet_intelligence/v1")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Collect and normalize public wallet data.")
    ingest.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ingest.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ingest.add_argument("--position-limit", type=int, default=50)
    ingest.add_argument("--activity-limit", type=int, default=50)
    ingest.add_argument("--delay", type=float, default=0.25)

    inspect = subparsers.add_parser("inspect", help="Print the normalized summary JSON.")
    inspect.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)

    summarize = subparsers.add_parser("summarize", help="Print the Markdown ingestion report.")
    summarize.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)

    metrics = subparsers.add_parser("metrics", help="Compute behavior metrics from existing ingestion outputs.")
    metrics.add_argument("--input", type=Path, default=DEFAULT_OUTPUT)
    metrics.add_argument("--output", type=Path, default=Path("polymarket/models/wallet_intelligence_v1/behavior_metrics"))

    fixture = subparsers.add_parser(
        "trade-history-fixture",
        help="Normalize saved trade-history fixtures without public ingestion.",
    )
    fixture.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    fixture.add_argument("--output", type=Path, default=DEFAULT_FIXTURE_OUTPUT)
    fixture.add_argument(
        "--limits",
        type=Path,
        default=Path("polymarket/models/wallet_intelligence_v1/trade_history_ingestion_design/ingestion_limits.json"),
    )

    smoke = subparsers.add_parser(
        "trade-history-smoke",
        help="Run a bounded public read-only trade-history smoke for seed wallets.",
    )
    smoke.add_argument("--watched-wallets", type=Path, default=DEFAULT_INPUT)
    smoke.add_argument("--wallet-profiles", type=Path, default=Path("polymarket/data/wallet_intelligence/v1/wallet_profiles.csv"))
    smoke.add_argument("--output", type=Path, default=DEFAULT_SMOKE_OUTPUT)
    smoke.add_argument(
        "--limits",
        type=Path,
        default=Path("polymarket/models/wallet_intelligence_v1/trade_history_ingestion_design/ingestion_limits.json"),
    )
    smoke.add_argument("--max-wallets", type=int, default=6)
    smoke.add_argument("--page-size", type=int, default=100)
    smoke.add_argument("--max-pages-per-wallet", type=int, default=1)
    smoke.add_argument("--delay", type=float, default=1.0)

    lifecycle = subparsers.add_parser(
        "trade-lifecycle-fixture",
        help="Reconstruct deterministic lifecycle candidates from normalized trade-history CSV.",
    )
    lifecycle.add_argument("--input", type=Path, default=DEFAULT_LIFECYCLE_INPUT)
    lifecycle.add_argument("--output", type=Path, default=DEFAULT_LIFECYCLE_OUTPUT)

    lifecycle_metrics = subparsers.add_parser(
        "lifecycle-metrics",
        help="Compute bounded wallet-level lifecycle metrics from lifecycle positions.",
    )
    lifecycle_metrics.add_argument("--input", type=Path, default=DEFAULT_LIFECYCLE_METRICS_INPUT)
    lifecycle_metrics.add_argument("--output", type=Path, default=DEFAULT_LIFECYCLE_METRICS_OUTPUT)

    wallet_score = subparsers.add_parser(
        "wallet-score-fixture",
        help="Compute bounded structural wallet scores from existing lifecycle metrics.",
    )
    wallet_score.add_argument("--input", type=Path, default=DEFAULT_WALLET_SCORE_INPUT)
    wallet_score.add_argument("--output", type=Path, default=DEFAULT_WALLET_SCORE_OUTPUT)

    watchlist = subparsers.add_parser(
        "wallet-watchlist",
        help="Create a research-only watchlist from existing Wallet Score outputs.",
    )
    watchlist.add_argument("--input", type=Path, default=DEFAULT_WATCHLIST_INPUT)
    watchlist.add_argument("--output", type=Path, default=DEFAULT_WATCHLIST_OUTPUT)

    copyability = subparsers.add_parser(
        "copyability-sprint",
        help="Run the bounded public Wallet Copyability Feasibility Sprint.",
    )
    copyability.add_argument("--output", type=Path, default=DEFAULT_COPYABILITY_OUTPUT)
    copyability.add_argument("--delay", type=float, default=0.5)

    outcome = subparsers.add_parser(
        "market-outcome-resolution",
        help="Join lifecycle candidates to public market outcome metadata.",
    )
    outcome.add_argument("--input", type=Path, default=DEFAULT_MARKET_OUTCOME_INPUT)
    outcome.add_argument("--output", type=Path, default=DEFAULT_MARKET_OUTCOME_OUTPUT)
    outcome.add_argument("--delay", type=float, default=0.02)

    skill = subparsers.add_parser(
        "wallet-outcome-skill",
        help="Run the H1 wallet outcome-skill baseline sprint.",
    )
    skill.add_argument("--input", type=Path, default=DEFAULT_WALLET_SKILL_INPUT)
    skill.add_argument("--output", type=Path, default=DEFAULT_WALLET_SKILL_OUTPUT)
    skill.add_argument("--score-csv", type=Path, default=DEFAULT_WALLET_SKILL_SCORE_INPUT)
    skill.add_argument("--watchlist-csv", type=Path, default=DEFAULT_WALLET_SKILL_WATCHLIST_INPUT)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "ingest":
        summary = ingest_wallets(
            args.input,
            args.output,
            client=PolymarketPublicClient(delay_seconds=args.delay),
            position_limit=args.position_limit,
            activity_limit=args.activity_limit,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    if args.command == "inspect":
        print(json.dumps(inspect_outputs(args.output), indent=2, sort_keys=True))
        return 0
    if args.command == "summarize":
        print(summarize_outputs(args.output))
        return 0
    if args.command == "metrics":
        print(json.dumps(compute_behavior_metrics(args.input, args.output), indent=2, sort_keys=True))
        return 0
    if args.command == "trade-history-fixture":
        print(
            json.dumps(
                run_fixture_ingestion(args.fixture, args.output, limits_path=args.limits),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "trade-history-smoke":
        print(
            json.dumps(
                run_bounded_public_smoke(
                    client=PolymarketPublicClient(delay_seconds=args.delay),
                    watched_wallets_path=args.watched_wallets,
                    wallet_profiles_path=args.wallet_profiles,
                    output_dir=args.output,
                    limits_path=args.limits,
                    max_wallets=args.max_wallets,
                    page_size=args.page_size,
                    max_pages_per_wallet=args.max_pages_per_wallet,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "trade-lifecycle-fixture":
        print(
            json.dumps(
                run_lifecycle_fixture_reconstruction(args.input, args.output),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "lifecycle-metrics":
        print(
            json.dumps(
                run_lifecycle_metrics(args.input, args.output),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "wallet-score-fixture":
        print(
            json.dumps(
                run_wallet_score_fixture(args.input, args.output),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "wallet-watchlist":
        print(
            json.dumps(
                run_wallet_watchlist(args.input, args.output),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "copyability-sprint":
        print(
            json.dumps(
                run_wallet_copyability_sprint(
                    client=PolymarketPublicClient(delay_seconds=args.delay, timeout_seconds=20),
                    copyability_output_dir=args.output,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "market-outcome-resolution":
        print(
            json.dumps(
                run_market_outcome_resolution_sprint(
                    input_csv=args.input,
                    output_dir=args.output,
                    client=PublicMarketMetadataClient(delay_seconds=args.delay),
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "wallet-outcome-skill":
        print(
            json.dumps(
                run_wallet_outcome_skill_baseline(
                    input_csv=args.input,
                    output_dir=args.output,
                    score_csv=args.score_csv,
                    watchlist_csv=args.watchlist_csv,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
