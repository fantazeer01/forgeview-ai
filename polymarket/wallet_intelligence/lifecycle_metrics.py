"""Bounded wallet-level lifecycle metrics.

This module computes structural metrics from existing lifecycle position
candidates only. It intentionally does not compute PnL, ROI, Sharpe,
copyability, ranking, scoring, mark-to-market values, reference alignment, or
queue/fill assumptions.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from statistics import median
from typing import Any

from .trade_history import decimal_or_none, file_sha256, normalize_decimal


DEFAULT_LIFECYCLE_METRICS_INPUT = Path(
    "polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture/lifecycle_positions.csv"
)
DEFAULT_LIFECYCLE_METRICS_OUTPUT = Path("polymarket/models/wallet_intelligence_v1/lifecycle_metrics")
NEAR_FLAT_RESIDUAL_THRESHOLD = Decimal("0.1")

WALLET_METRICS_FIELDS = [
    "wallet_id",
    "profile_url",
    "total_lifecycle_positions",
    "still_open_positions",
    "partial_exits",
    "full_exits",
    "oversold_bounded_history",
    "average_position_size",
    "median_position_size",
    "average_buy_count_per_lifecycle",
    "average_sell_count_per_lifecycle",
    "average_events_per_lifecycle",
    "percentage_still_open_positions",
    "percentage_sell_only_lifecycles",
    "buy_trade_count",
    "sell_trade_count",
    "total_visible_bought_size",
    "total_visible_sold_size",
    "remaining_visible_size",
    "oversold_visible_size",
    "near_flat_residual_count",
    "fast_crypto_lifecycle_count",
    "fast_crypto_lifecycle_share",
    "dominant_asset",
    "asset_concentration",
    "dominant_outcome",
    "outcome_concentration",
]

FORBIDDEN_METRIC_FRAGMENTS = (
    "pnl",
    "roi",
    "sharpe",
    "copyability",
    "score",
    "ranking",
    "mark_to_market",
)


def load_lifecycle_positions(path: Path = DEFAULT_LIFECYCLE_METRICS_INPUT) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def compute_wallet_lifecycle_metrics(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("wallet_id") or "").lower()].append(row)

    metrics = [_metrics_for_wallet(wallet_id, grouped[wallet_id]) for wallet_id in sorted(grouped)]
    aggregate = _aggregate_summary(rows, metrics)
    validation = validate_wallet_lifecycle_metrics(rows, metrics)
    validation_bools = [value for value in validation.values() if isinstance(value, bool)]
    validation["all_validation_passed"] = all(validation_bools)
    summary = {
        "task": "Wallet Lifecycle Metrics v1",
        "input_rows": len(rows),
        "wallets_analyzed": len(metrics),
        "near_flat_residual_threshold_shares": normalize_decimal(NEAR_FLAT_RESIDUAL_THRESHOLD),
        "aggregate": aggregate,
        "validation": validation,
        "not_computed": [
            "PnL",
            "ROI",
            "Sharpe",
            "copyability",
            "wallet scoring",
            "wallet ranking",
            "mark-to-market values",
            "expiry joins",
            "Binance/reference alignment",
            "queue modelling",
        ],
        "recommended_next_task": "Wallet Lifecycle Metrics Review v1",
    }
    return metrics, summary


def validate_wallet_lifecycle_metrics(rows: list[dict[str, str]], metrics: list[dict[str, str]]) -> dict[str, Any]:
    row_wallets = {(row.get("wallet_id") or "").lower() for row in rows}
    metric_wallets = {row["wallet_id"] for row in metrics}
    count_total = sum(int(row["total_lifecycle_positions"]) for row in metrics)
    status_total = sum(
        int(row["still_open_positions"])
        + int(row["partial_exits"])
        + int(row["full_exits"])
        + int(row["oversold_bounded_history"])
        for row in metrics
    )
    buy_count = sum(int(row["buy_trade_count"]) for row in metrics)
    sell_count = sum(int(row["sell_trade_count"]) for row in metrics)
    expected_buy = sum(int(row.get("buy_trade_count") or 0) for row in rows)
    expected_sell = sum(int(row.get("sell_trade_count") or 0) for row in rows)
    shares_valid = all(
        _required_decimal(row[field]) is not None and Decimal("0") <= _required_decimal(row[field]) <= Decimal("1")
        for row in metrics
        for field in (
            "percentage_still_open_positions",
            "percentage_sell_only_lifecycles",
            "fast_crypto_lifecycle_share",
            "asset_concentration",
            "outcome_concentration",
        )
    )
    decimals_parse = all(
        decimal_or_none(row[field]) is not None
        for row in metrics
        for field in (
            "average_position_size",
            "median_position_size",
            "average_buy_count_per_lifecycle",
            "average_sell_count_per_lifecycle",
            "average_events_per_lifecycle",
            "total_visible_bought_size",
            "total_visible_sold_size",
            "remaining_visible_size",
            "oversold_visible_size",
        )
    )
    forbidden_present = [
        field
        for field in WALLET_METRICS_FIELDS
        for fragment in FORBIDDEN_METRIC_FRAGMENTS
        if fragment in field.lower()
    ]
    ordered = [row["wallet_id"] for row in metrics] == sorted(row["wallet_id"] for row in metrics)
    return {
        "wallet_coverage": row_wallets == metric_wallets,
        "input_position_count_matches": count_total == len(rows),
        "status_count_conservation": status_total == len(rows),
        "buy_trade_count_matches": buy_count == expected_buy,
        "sell_trade_count_matches": sell_count == expected_sell,
        "share_fields_in_range": shares_valid,
        "decimal_metric_fields_parse": decimals_parse,
        "forbidden_metric_fields_absent": not forbidden_present,
        "forbidden_metric_fields": forbidden_present,
        "deterministic_wallet_ordering": ordered,
    }


def write_wallet_metrics_csv(path: Path, metrics: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=WALLET_METRICS_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in metrics:
            writer.writerow(row)


def run_lifecycle_metrics(
    input_csv: Path = DEFAULT_LIFECYCLE_METRICS_INPUT,
    output_dir: Path = DEFAULT_LIFECYCLE_METRICS_OUTPUT,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = load_lifecycle_positions(input_csv)
    metrics, summary = compute_wallet_lifecycle_metrics(rows)

    csv_path = output_dir / "wallet_metrics.csv"
    summary_path = output_dir / "wallet_metrics_summary.json"
    report_path = output_dir / "wallet_metrics_report.md"
    compatibility_csv_path = output_dir / "wallet_lifecycle_metrics.csv"

    write_wallet_metrics_csv(csv_path, metrics)
    first_hash = file_sha256(csv_path)
    write_wallet_metrics_csv(csv_path, metrics)
    second_hash = file_sha256(csv_path)
    deterministic = first_hash == second_hash
    write_wallet_metrics_csv(compatibility_csv_path, metrics)

    summary = {
        "generated_at_utc": generated_at,
        "input_csv": str(input_csv),
        "output_dir": str(output_dir),
        **summary,
    }
    summary["validation"]["deterministic_csv_repeat_export"] = deterministic
    validation_bools = [value for value in summary["validation"].values() if isinstance(value, bool)]
    summary["validation"]["all_validation_passed"] = all(validation_bools)
    hashes = {
        "wallet_metrics_csv_sha256": file_sha256(csv_path),
        "wallet_lifecycle_metrics_csv_sha256": file_sha256(compatibility_csv_path),
        "deterministic_csv_repeat_export": deterministic,
    }
    summary["reproducibility_hashes"] = hashes
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report_path.write_text(_build_report(summary, metrics), encoding="utf-8")
    return summary


def _metrics_for_wallet(wallet_id: str, rows: list[dict[str, str]]) -> dict[str, str]:
    total = len(rows)
    status_counts = Counter(row.get("status") or "unknown" for row in rows)
    asset_counts = Counter(row.get("asset_class") or "unknown" for row in rows)
    outcome_counts = Counter(row.get("outcome") or "unknown" for row in rows)
    buy_count = sum(int(row.get("buy_trade_count") or 0) for row in rows)
    sell_count = sum(int(row.get("sell_trade_count") or 0) for row in rows)
    bought = sum(_decimal(row.get("total_bought_size")) for row in rows)
    sold = sum(_decimal(row.get("total_sold_size")) for row in rows)
    remaining = sum(_decimal(row.get("remaining_size")) for row in rows)
    oversold = sum(_decimal(row.get("oversold_size")) for row in rows)
    position_sizes = [_visible_position_size(row) for row in rows]
    sell_only = sum(1 for row in rows if int(row.get("buy_trade_count") or 0) == 0 and int(row.get("sell_trade_count") or 0) > 0)
    near_flat = sum(1 for row in rows if _is_near_flat(row))
    dominant_asset, asset_concentration = _dominant_share(asset_counts, total)
    dominant_outcome, outcome_concentration = _dominant_share(outcome_counts, total)
    fast_crypto = sum(1 for row in rows if row.get("market_type") == "fast_crypto_up_down")
    return {
        "wallet_id": wallet_id,
        "profile_url": rows[0].get("profile_url") or "",
        "total_lifecycle_positions": str(total),
        "still_open_positions": str(status_counts["still_open"]),
        "partial_exits": str(status_counts["partial_exit"]),
        "full_exits": str(status_counts["full_exit"]),
        "oversold_bounded_history": str(status_counts["oversold_bounded_history"]),
        "average_position_size": _mean(position_sizes),
        "median_position_size": normalize_decimal(Decimal(str(median(position_sizes))) if position_sizes else Decimal("0")),
        "average_buy_count_per_lifecycle": _ratio(Decimal(buy_count), Decimal(total)),
        "average_sell_count_per_lifecycle": _ratio(Decimal(sell_count), Decimal(total)),
        "average_events_per_lifecycle": _ratio(Decimal(buy_count + sell_count), Decimal(total)),
        "percentage_still_open_positions": _ratio(Decimal(status_counts["still_open"]), Decimal(total)),
        "percentage_sell_only_lifecycles": _ratio(Decimal(sell_only), Decimal(total)),
        "buy_trade_count": str(buy_count),
        "sell_trade_count": str(sell_count),
        "total_visible_bought_size": normalize_decimal(bought),
        "total_visible_sold_size": normalize_decimal(sold),
        "remaining_visible_size": normalize_decimal(remaining),
        "oversold_visible_size": normalize_decimal(oversold),
        "near_flat_residual_count": str(near_flat),
        "fast_crypto_lifecycle_count": str(fast_crypto),
        "fast_crypto_lifecycle_share": _ratio(Decimal(fast_crypto), Decimal(total)),
        "dominant_asset": dominant_asset,
        "asset_concentration": asset_concentration,
        "dominant_outcome": dominant_outcome,
        "outcome_concentration": outcome_concentration,
    }


def _aggregate_summary(rows: list[dict[str, str]], metrics: list[dict[str, str]]) -> dict[str, Any]:
    statuses = Counter(row.get("status") or "unknown" for row in rows)
    return {
        "total_lifecycle_positions": len(rows),
        "wallets_analyzed": len(metrics),
        "status_counts": dict(sorted(statuses.items())),
        "buy_trade_count": sum(int(row["buy_trade_count"]) for row in metrics),
        "sell_trade_count": sum(int(row["sell_trade_count"]) for row in metrics),
        "near_flat_residual_count": sum(int(row["near_flat_residual_count"]) for row in metrics),
        "sell_only_lifecycles": sum(
            int(Decimal(row["percentage_sell_only_lifecycles"]) * Decimal(row["total_lifecycle_positions"]))
            for row in metrics
        ),
    }


def _build_report(summary: dict[str, Any], metrics: list[dict[str, str]]) -> str:
    lines = [
        "# Wallet Lifecycle Metrics v1",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "## Scope",
        "",
        "Metrics are computed from existing lifecycle positions only. No PnL, ROI, Sharpe, copyability, wallet scoring, wallet ranking, mark-to-market values, expiry joins, reference alignment, queue modelling, order placement, wallet/private-key use, holdout inspection, or holdout evaluation was added.",
        "",
        "## Aggregate",
        "",
        f"- Wallets analyzed: {summary['wallets_analyzed']}",
        f"- Lifecycle positions: {summary['aggregate']['total_lifecycle_positions']}",
        f"- BUY trades visible: {summary['aggregate']['buy_trade_count']}",
        f"- SELL trades visible: {summary['aggregate']['sell_trade_count']}",
        f"- Near-flat residual threshold: {summary['near_flat_residual_threshold_shares']} shares",
        f"- Near-flat residual count: {summary['aggregate']['near_flat_residual_count']}",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in summary["aggregate"]["status_counts"].items():
        lines.append(f"- `{status}`: {count}")
    lines.extend(["", "## Wallet Rows", ""])
    for row in metrics:
        lines.append(
            f"- `{row['wallet_id']}`: positions={row['total_lifecycle_positions']}, still_open={row['still_open_positions']}, partial={row['partial_exits']}, full={row['full_exits']}, oversold={row['oversold_bounded_history']}"
        )
    lines.extend(["", "## Validation", ""])
    for name, value in summary["validation"].items():
        lines.append(f"- `{name}`: {str(value).lower()}")
    lines.extend(["", "## Recommended Next Task", "", f"`{summary['recommended_next_task']}`", ""])
    return "\n".join(lines)


def _decimal(value: Any) -> Decimal:
    return decimal_or_none(value) or Decimal("0")


def _required_decimal(value: Any) -> Decimal | None:
    return decimal_or_none(value)


def _visible_position_size(row: dict[str, str]) -> Decimal:
    bought = _decimal(row.get("total_bought_size"))
    sold = _decimal(row.get("total_sold_size"))
    return bought if bought > 0 else sold


def _is_near_flat(row: dict[str, str]) -> bool:
    bought = _decimal(row.get("total_bought_size"))
    sold = _decimal(row.get("total_sold_size"))
    residual = abs(bought - sold)
    return bought > 0 and sold > 0 and Decimal("0") < residual <= NEAR_FLAT_RESIDUAL_THRESHOLD


def _mean(values: list[Decimal]) -> str:
    if not values:
        return "0"
    return normalize_decimal(sum(values) / Decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> str:
    if denominator == 0:
        return "0"
    return normalize_decimal(numerator / denominator)


def _dominant_share(counts: Counter[str], total: int) -> tuple[str, str]:
    if total == 0 or not counts:
        return "unknown", "0"
    dominant, count = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0]
    return dominant, _ratio(Decimal(count), Decimal(total))
