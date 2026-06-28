from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable


@dataclass(frozen=True)
class RandomBaselineConfig:
    trials: int = 1000
    seed: int = 20260628
    min_seconds_to_expiry: float = 60.0
    expiry_bucket_seconds: int = 60
    max_holding_seconds: float = 180.0
    repricing_target: float = 0.03
    stop_loss: float = 0.03
    conservative_slippage: float = 0.02


@dataclass(frozen=True)
class _Snapshot:
    timestamp: datetime
    market_id: str
    asset: str
    yes_price: float
    no_price: float
    seconds_to_expiry: float


@dataclass(frozen=True)
class _Candidate:
    batch: int
    market_id: str
    asset: str
    side: str
    expiry_bucket: int
    entry_timestamp: datetime
    exit_timestamp: datetime
    pnl_before_slippage: float
    pnl_after_slippage: float
    won: bool


def run_random_baseline(
    detector_csv_paths: Iterable[str | Path],
    session_paths: Iterable[str | Path],
    config: RandomBaselineConfig | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cfg = config or RandomBaselineConfig()
    csv_paths = [Path(path) for path in detector_csv_paths]
    sessions = [Path(path) for path in session_paths]
    if len(csv_paths) != len(sessions) or not csv_paths:
        raise ValueError("detector CSV and session counts must match and be nonzero")
    if cfg.trials <= 0:
        raise ValueError("trials must be positive")

    detector_rows = _read_detector_rows(csv_paths)
    pools: dict[tuple[int, str, str, int], list[_Candidate]] = defaultdict(list)
    observed_seconds = 0.0
    for batch, session_path in enumerate(sessions):
        session_pools, duration = _build_candidate_pools(batch, session_path, cfg)
        observed_seconds += duration
        for key, values in session_pools.items():
            pools[key].extend(values)

    templates = sorted(
        detector_rows,
        key=lambda row: (row["batch"], row["entry_timestamp"], row["asset"], row["side"]),
    )
    for row in templates:
        key = (row["batch"], row["asset"], row["side"], row["expiry_bucket"])
        if not pools.get(key):
            raise ValueError(f"no random candidates for matched stratum {key}")

    detector_metrics = _detector_metrics(templates, observed_seconds)
    rng = random.Random(cfg.seed)
    trial_rows: list[dict[str, Any]] = []
    for trial in range(1, cfg.trials + 1):
        selected = _draw_trial(templates, pools, rng)
        metrics = _candidate_metrics(selected, observed_seconds)
        trial_rows.append({"trial": trial, **metrics})

    summary = _summarize(
        cfg,
        csv_paths,
        sessions,
        detector_metrics,
        trial_rows,
        templates,
        observed_seconds,
    )
    return trial_rows, summary


def write_random_baseline_outputs(
    output_dir: str | Path,
    trial_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / "random_baseline_results.csv"
    json_path = output / "random_baseline_summary.json"
    report_path = output / "random_baseline_report.md"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(trial_rows[0]))
        writer.writeheader()
        writer.writerows(trial_rows)
    json_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_report_markdown(summary), encoding="utf-8")
    return {
        "results": str(csv_path),
        "summary": str(json_path),
        "report": str(report_path),
    }


def _read_detector_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for batch, path in enumerate(paths):
        with path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                expiry = float(row["time_to_expiry_seconds"])
                rows.append({
                    "batch": batch,
                    "entry_timestamp": row["entry_timestamp"],
                    "asset": row["asset"],
                    "side": row["side"],
                    "expiry_bucket": int(expiry // 60) * 60,
                    "won": row["repriced_favorably"].lower() == "true",
                    "pnl_before_slippage": float(row["simulated_pnl_before_slippage"]),
                    "pnl_after_slippage": float(row["simulated_pnl_after_slippage"]),
                })
    return rows


def _build_candidate_pools(
    batch: int,
    session_path: Path,
    config: RandomBaselineConfig,
) -> tuple[dict[tuple[int, str, str, int], list[_Candidate]], float]:
    snapshots: dict[str, list[_Snapshot]] = defaultdict(list)
    started = None
    completed = None
    with session_path.open(encoding="utf-8") as handle:
        for line in handle:
            event = json.loads(line)
            timestamp = datetime.fromisoformat(event["timestamp"])
            payload = event["payload"]
            if event["event"] == "session_started":
                started = timestamp
            elif event["event"] == "session_completed":
                completed = timestamp
            elif event["event"] == "polymarket_snapshot":
                snapshots[payload["market_id"]].append(_Snapshot(
                    timestamp=timestamp,
                    market_id=payload["market_id"],
                    asset=payload["asset"],
                    yes_price=float(payload["yes_price"]),
                    no_price=float(payload["no_price"]),
                    seconds_to_expiry=float(payload["seconds_to_expiry"]),
                ))
    if started is None or completed is None:
        raise ValueError(f"session is incomplete: {session_path}")

    pools: dict[tuple[int, str, str, int], list[_Candidate]] = defaultdict(list)
    for market_snapshots in snapshots.values():
        market_snapshots.sort(key=lambda row: row.timestamp)
        for index, entry in enumerate(market_snapshots):
            if entry.seconds_to_expiry < config.min_seconds_to_expiry:
                continue
            end = min(
                entry.timestamp + timedelta(seconds=config.max_holding_seconds),
                entry.timestamp + timedelta(seconds=entry.seconds_to_expiry - 1),
            )
            future = [
                row for row in market_snapshots[index:]
                if row.timestamp <= end
            ]
            if len(future) < 2:
                continue
            bucket = (
                int(entry.seconds_to_expiry // config.expiry_bucket_seconds)
                * config.expiry_bucket_seconds
            )
            for side in ("YES", "NO"):
                candidate = _evaluate_candidate(batch, entry, future, side, bucket, config)
                pools[(batch, entry.asset, side, bucket)].append(candidate)
    return pools, (completed - started).total_seconds()


def _evaluate_candidate(
    batch: int,
    entry: _Snapshot,
    future: list[_Snapshot],
    side: str,
    bucket: int,
    config: RandomBaselineConfig,
) -> _Candidate:
    entry_price = entry.yes_price if side == "YES" else entry.no_price
    moves = [
        (
            row.timestamp,
            (row.yes_price if side == "YES" else row.no_price) - entry_price,
        )
        for row in future
    ]
    target = next(
        ((timestamp, move) for timestamp, move in moves if move >= config.repricing_target),
        None,
    )
    stop = next(
        ((timestamp, move) for timestamp, move in moves if move <= -config.stop_loss),
        None,
    )
    if target and (not stop or target[0] <= stop[0]):
        exit_timestamp, pnl = target
        won = True
    elif stop:
        exit_timestamp, pnl = stop
        won = False
    else:
        exit_timestamp, pnl = moves[-1]
        won = False
    return _Candidate(
        batch=batch,
        market_id=entry.market_id,
        asset=entry.asset,
        side=side,
        expiry_bucket=bucket,
        entry_timestamp=entry.timestamp,
        exit_timestamp=exit_timestamp,
        pnl_before_slippage=pnl,
        pnl_after_slippage=pnl - config.conservative_slippage,
        won=won,
    )


def _draw_trial(
    templates: list[dict[str, Any]],
    pools: dict[tuple[int, str, str, int], list[_Candidate]],
    rng: random.Random,
) -> list[_Candidate]:
    selected: list[_Candidate] = []
    intervals: dict[tuple[int, str, str], list[tuple[datetime, datetime]]] = defaultdict(list)
    used: set[tuple[int, str, str, datetime]] = set()
    for row in templates:
        key = (row["batch"], row["asset"], row["side"], row["expiry_bucket"])
        pool = pools[key]
        choice = None
        for _ in range(5000):
            candidate = pool[rng.randrange(len(pool))]
            identity = (
                candidate.batch,
                candidate.market_id,
                candidate.side,
                candidate.entry_timestamp,
            )
            position_key = (candidate.batch, candidate.market_id, candidate.side)
            overlaps = any(
                candidate.entry_timestamp < end and candidate.exit_timestamp > start
                for start, end in intervals[position_key]
            )
            if identity not in used and not overlaps:
                choice = candidate
                break
        if choice is None:
            raise RuntimeError(f"unable to draw non-overlapping candidate for {key}")
        selected.append(choice)
        used.add((choice.batch, choice.market_id, choice.side, choice.entry_timestamp))
        intervals[(choice.batch, choice.market_id, choice.side)].append(
            (choice.entry_timestamp, choice.exit_timestamp)
        )
    return selected


def _detector_metrics(rows: list[dict[str, Any]], observed_seconds: float) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: row["entry_timestamp"])
    return _metrics(
        [row["won"] for row in ordered],
        [row["pnl_before_slippage"] for row in ordered],
        [row["pnl_after_slippage"] for row in ordered],
        observed_seconds,
    )


def _candidate_metrics(rows: list[_Candidate], observed_seconds: float) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: row.entry_timestamp)
    return _metrics(
        [row.won for row in ordered],
        [row.pnl_before_slippage for row in ordered],
        [row.pnl_after_slippage for row in ordered],
        observed_seconds,
    )


def _metrics(
    wins: list[bool],
    pnl_before: list[float],
    pnl_after: list[float],
    observed_seconds: float,
) -> dict[str, Any]:
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for pnl in pnl_after:
        equity += pnl
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
    sample_size = len(wins)
    return {
        "sample_size": sample_size,
        "wins": sum(wins),
        "win_rate": sum(wins) / sample_size,
        "pnl_before_slippage": round(sum(pnl_before), 8),
        "pnl_after_slippage": round(sum(pnl_after), 8),
        "expectancy_after_slippage": sum(pnl_after) / sample_size,
        "max_drawdown": round(max_drawdown, 8),
        "signals_per_hour": sample_size / (observed_seconds / 3600.0),
    }


def _summarize(
    config: RandomBaselineConfig,
    detector_paths: list[Path],
    sessions: list[Path],
    detector: dict[str, Any],
    trials: list[dict[str, Any]],
    templates: list[dict[str, Any]],
    observed_seconds: float,
) -> dict[str, Any]:
    random_summary = {}
    for metric in ("win_rate", "expectancy_after_slippage", "max_drawdown", "signals_per_hour"):
        values = [float(row[metric]) for row in trials]
        random_summary[metric] = {
            "mean": mean(values),
            "median": median(values),
            "p2_5": _percentile(values, 0.025),
            "p97_5": _percentile(values, 0.975),
            "minimum": min(values),
            "maximum": max(values),
        }
    expectancy_exceedances = sum(
        row["expectancy_after_slippage"] >= detector["expectancy_after_slippage"]
        for row in trials
    )
    win_exceedances = sum(row["win_rate"] >= detector["win_rate"] for row in trials)
    expectancy_p = (expectancy_exceedances + 1) / (len(trials) + 1)
    win_p = (win_exceedances + 1) / (len(trials) + 1)
    expectancy_supported = (
        detector["expectancy_after_slippage"]
        > random_summary["expectancy_after_slippage"]["p97_5"]
    )
    win_supported = detector["win_rate"] > random_summary["win_rate"]["p97_5"]
    if expectancy_supported and win_supported:
        conclusion = "SUPPORTED"
    elif (
        detector["expectancy_after_slippage"]
        <= random_summary["expectancy_after_slippage"]["mean"]
        and detector["win_rate"] <= random_summary["win_rate"]["mean"]
    ):
        conclusion = "REJECTED"
    else:
        conclusion = "INCONCLUSIVE"

    asset_side = Counter((row["batch"], row["asset"], row["side"]) for row in templates)
    expiry = Counter((row["batch"], row["expiry_bucket"]) for row in templates)
    baseline_expectancy = random_summary["expectancy_after_slippage"]["mean"]
    return {
        "sprint": "balanced_repricing_random_baseline_v1",
        "hypothesis": "Observed positive expectancy is not explained by random entry timing alone.",
        "baseline_specification": {
            **asdict(config),
            "entry_sampling": "uniform over eligible public snapshots within matched batch, asset, side, and 60-second expiry bucket",
            "position_rule": "unique entry and no overlapping position for the same batch, market, and side",
            "distribution_matching": "exact detector count by batch, asset, side, and expiry bucket in every trial",
            "decision_rule": {
                "SUPPORTED": "detector expectancy and win rate both exceed random 97.5th percentiles",
                "REJECTED": "detector expectancy and win rate both fail to exceed random means",
                "INCONCLUSIVE": "all other measured outcomes",
            },
        },
        "inputs": {
            "detector_csvs": [str(path) for path in detector_paths],
            "sessions": [str(path) for path in sessions],
        },
        "observed_hours": observed_seconds / 3600.0,
        "sample_size": len(templates),
        "matched_batch_asset_side_counts": {
            f"batch_{batch + 1:03d}:{asset}:{side}": count
            for (batch, asset, side), count in sorted(asset_side.items())
        },
        "matched_batch_expiry_bucket_counts": {
            f"batch_{batch + 1:03d}:{bucket}": count
            for (batch, bucket), count in sorted(expiry.items())
        },
        "detector": detector,
        "random_baseline": random_summary,
        "differences": {
            "win_rate_absolute": detector["win_rate"] - random_summary["win_rate"]["mean"],
            "win_rate_relative": (
                detector["win_rate"] / random_summary["win_rate"]["mean"] - 1.0
            ),
            "expectancy_absolute": detector["expectancy_after_slippage"] - baseline_expectancy,
            "expectancy_relative_to_absolute_baseline": (
                (detector["expectancy_after_slippage"] - baseline_expectancy)
                / abs(baseline_expectancy)
                if baseline_expectancy else None
            ),
            "max_drawdown_absolute": detector["max_drawdown"] - random_summary["max_drawdown"]["mean"],
            "signal_density_absolute": detector["signals_per_hour"] - random_summary["signals_per_hour"]["mean"],
        },
        "one_sided_monte_carlo_p_values": {
            "expectancy_at_least_detector": expectancy_p,
            "win_rate_at_least_detector": win_p,
        },
        "confidence_limitations": [
            "Only two independent 12-hour sessions and 172 detector signals are available.",
            "Snapshot observations are serially correlated within five-minute markets.",
            "The baseline reuses the same two observed market regimes and cannot test regime persistence.",
            "Uniform snapshot sampling is one defensible random-timing definition, not the only possible random baseline.",
            "Midpoint-like public prices do not establish executable fills, queue position, depth consumption, or fees.",
            "Signal density is matched by design and therefore is a control variable, not an independent advantage test.",
            "Detector datasets were selected by frozen rules on development sessions and remain exposed to development selection bias.",
        ],
        "invalidation_search": {
            "selection_bias": "not eliminated; detector and baseline use development sessions",
            "survivorship_bias": "reduced by sampling all eligible observed markets, not eliminated outside captured sessions",
            "detector_bias": "tested only against random timing with matched distributions",
            "sampling_bias": "possible from uniform snapshot weighting and serial correlation",
            "market_regime": "not testable with two adjacent sessions",
            "small_sample_effects": "material with 172 signals and two sessions",
        },
        "conclusion": conclusion,
        "holdout_status": "sealed_holdout_not_inspected_no_holdout_evaluation_run",
        "frozen_parameters_unchanged": True,
    }


def _percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _report_markdown(summary: dict[str, Any]) -> str:
    detector = summary["detector"]
    random_result = summary["random_baseline"]
    differences = summary["differences"]
    p_values = summary["one_sided_monte_carlo_p_values"]
    limitations = "\n".join(
        f"- {item}" for item in summary["confidence_limitations"]
    )
    invalidation = "\n".join(
        f"- {key.replace('_', ' ').title()}: {value}"
        for key, value in summary["invalidation_search"].items()
    )
    return f"""# Balanced Repricing Random Baseline Sprint v1

## Predefined Baseline

- Trials: {summary['baseline_specification']['trials']:,}
- Seed: {summary['baseline_specification']['seed']}
- Sample size per trial: {summary['sample_size']}
- Observed hours: {summary['observed_hours']:.6f}
- Matching: exact batch, asset, side, and 60-second expiry-bucket counts.
- Entry timing: uniform random eligible public snapshot.
- Paper rules: 180-second timeout, 0.03 target, 0.03 stop, 0.02 slippage,
  and no overlapping same-market/same-side position.

## Detector Versus Random

| Metric | Detector | Random mean | Random 95% interval | Difference |
|---|---:|---:|---:|---:|
| Win rate | {detector['win_rate']:.6f} | {random_result['win_rate']['mean']:.6f} | {random_result['win_rate']['p2_5']:.6f} to {random_result['win_rate']['p97_5']:.6f} | {differences['win_rate_absolute']:+.6f} |
| Expectancy after slippage | {detector['expectancy_after_slippage']:.6f} | {random_result['expectancy_after_slippage']['mean']:.6f} | {random_result['expectancy_after_slippage']['p2_5']:.6f} to {random_result['expectancy_after_slippage']['p97_5']:.6f} | {differences['expectancy_absolute']:+.6f} |
| Maximum drawdown | {detector['max_drawdown']:.6f} | {random_result['max_drawdown']['mean']:.6f} | {random_result['max_drawdown']['p2_5']:.6f} to {random_result['max_drawdown']['p97_5']:.6f} | {differences['max_drawdown_absolute']:+.6f} |
| Signals/hour | {detector['signals_per_hour']:.6f} | {random_result['signals_per_hour']['mean']:.6f} | {random_result['signals_per_hour']['p2_5']:.6f} to {random_result['signals_per_hour']['p97_5']:.6f} | {differences['signal_density_absolute']:+.6f} |

One-sided Monte Carlo exceedance probabilities:

- random expectancy at least detector: {p_values['expectancy_at_least_detector']:.6f};
- random win rate at least detector: {p_values['win_rate_at_least_detector']:.6f}.

## Invalidation Search

{invalidation}

## Confidence Limitations

{limitations}

## Conclusion

**{summary['conclusion']}**

The conclusion follows the decision rule declared in
`random_baseline_summary.json`. It is development evidence only. The sealed
holdout was not inspected, frozen detector settings were unchanged, and no
production, execution, parameter-tuning, or additional-capture authorization
follows from this sprint.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Frozen repricing random-entry baseline")
    parser.add_argument("--detector-csv", action="append", type=Path, required=True)
    parser.add_argument("--session", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--trials", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260628)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    trial_rows, summary = run_random_baseline(
        args.detector_csv,
        args.session,
        RandomBaselineConfig(trials=args.trials, seed=args.seed),
    )
    paths = write_random_baseline_outputs(args.output, trial_rows, summary)
    print(json.dumps({"conclusion": summary["conclusion"], **paths}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
