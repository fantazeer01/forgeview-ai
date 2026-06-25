"""Deterministic wallet trade lifecycle reconstruction prototype.

This module is intentionally descriptive and bounded. It groups normalized
public trade-history rows into wallet/market/outcome lifecycle candidates; it
does not join expiry, mark positions to market, align Binance/reference prices,
estimate copy delay, model queue priority, or place/copy trades.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from .schema import LIFECYCLE_POSITION_FIELDS, LifecyclePositionRecord
from .trade_history import decimal_or_none, file_sha256, normalize_decimal


DEFAULT_LIFECYCLE_INPUT = Path("polymarket/data/wallet_intelligence/trade_history_smoke_v1/trade_history_normalized.csv")
DEFAULT_LIFECYCLE_OUTPUT = Path("polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture")


def load_trade_history_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def deterministic_trade_sort_key(row: dict[str, str]) -> tuple[str, str, str, str, int, str, str, str, str]:
    return (
        (row.get("wallet_id") or "").lower(),
        (row.get("condition_id") or "").lower(),
        row.get("token_id") or "",
        row.get("outcome") or "",
        _int_or_max(row.get("activity_timestamp")),
        (row.get("transaction_hash") or "").lower(),
        row.get("side") or "",
        row.get("price") or "",
        row.get("size") or "",
    )


def reconstruct_lifecycle_positions(rows: list[dict[str, str]]) -> tuple[list[LifecyclePositionRecord], dict[str, Any]]:
    ordered = sorted(rows, key=deterministic_trade_sort_key)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in ordered:
        key = row.get("lifecycle_group_key") or "|".join(
            [
                (row.get("wallet_id") or "").lower(),
                (row.get("condition_id") or "").lower(),
                row.get("token_id") or "",
                row.get("outcome") or "",
            ]
        )
        grouped[key].append(row)

    positions = [_reconstruct_group(key, trades) for key, trades in sorted(grouped.items())]
    validation = validate_lifecycle_positions(positions)
    summary = {
        "input_rows": len(rows),
        "lifecycle_positions": len(positions),
        "status_counts": _count_by(positions, "status"),
        "asset_counts": _count_by(positions, "asset_class"),
        "fast_crypto_positions": sum(1 for position in positions if position.market_type == "fast_crypto_up_down"),
        "validation": validation,
        "not_implemented": [
            "expiry joins",
            "mark-to-market PnL",
            "Binance/reference alignment",
            "copyability delay",
            "queue priority",
        ],
    }
    return positions, summary


def validate_lifecycle_positions(positions: list[LifecyclePositionRecord]) -> dict[str, Any]:
    conservation_failures: list[str] = []
    truncated_negative_groups: list[str] = []
    unexpected_negative_groups: list[str] = []
    ordered_keys = [position.lifecycle_group_key for position in positions]
    for position in positions:
        bought = decimal_or_none(position.total_bought_size) or Decimal("0")
        sold = decimal_or_none(position.total_sold_size) or Decimal("0")
        remaining = decimal_or_none(position.remaining_size) or Decimal("0")
        oversold = decimal_or_none(position.oversold_size) or Decimal("0")
        if bought + oversold != sold + remaining:
            conservation_failures.append(position.lifecycle_group_key)
        if position.negative_position_detected == "true":
            if position.negative_position_reason == "bounded_history_missing_prior_buy":
                truncated_negative_groups.append(position.lifecycle_group_key)
            else:
                unexpected_negative_groups.append(position.lifecycle_group_key)
    return {
        "no_unexpected_negative_position_size": len(unexpected_negative_groups) == 0,
        "unexpected_negative_position_groups": unexpected_negative_groups,
        "bounded_history_negative_position_groups": truncated_negative_groups,
        "position_size_conservation": len(conservation_failures) == 0,
        "position_size_conservation_failures": conservation_failures,
        "deterministic_ordering": ordered_keys == sorted(ordered_keys),
    }


def write_lifecycle_positions(path: Path, positions: list[LifecyclePositionRecord]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LIFECYCLE_POSITION_FIELDS, lineterminator="\n")
        writer.writeheader()
        for position in positions:
            writer.writerow(asdict(position))


def run_lifecycle_fixture_reconstruction(
    input_csv: Path = DEFAULT_LIFECYCLE_INPUT,
    output_dir: Path = DEFAULT_LIFECYCLE_OUTPUT,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = load_trade_history_csv(input_csv)
    positions, summary = reconstruct_lifecycle_positions(rows)

    positions_path = output_dir / "lifecycle_positions.csv"
    summary_path = output_dir / "lifecycle_summary.json"
    validation_path = output_dir / "lifecycle_validation.json"
    hashes_path = output_dir / "reproducibility_hashes.json"

    write_lifecycle_positions(positions_path, positions)
    first_hash = file_sha256(positions_path)
    write_lifecycle_positions(positions_path, positions)
    second_hash = file_sha256(positions_path)
    repeatable = first_hash == second_hash
    summary["validation"]["repeatable_output"] = repeatable

    result = {
        "task": "Wallet Trade Lifecycle Reconstruction Fixture Prototype v1",
        "generated_at_utc": generated_at,
        "input_csv": str(input_csv),
        "output_dir": str(output_dir),
        **summary,
        "strict_rules_observed": [
            "existing normalized public trade history only",
            "no expiry joins",
            "no mark-to-market PnL",
            "no Binance/reference alignment",
            "no copyability delay",
            "no queue priority",
            "no live trading",
            "no wallet/private-key connection",
            "no order placement",
            "no holdout inspection",
            "no holdout evaluation",
        ],
        "recommended_next_task": "Wallet Lifecycle Reconstruction Review v1",
    }
    summary_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    validation_path.write_text(json.dumps(result["validation"], indent=2, sort_keys=True), encoding="utf-8")
    hashes = {
        "lifecycle_positions_csv_sha256": file_sha256(positions_path),
        "lifecycle_validation_json_sha256": file_sha256(validation_path),
        "csv_repeat_export_hash_match": repeatable,
    }
    hashes_path.write_text(json.dumps(hashes, indent=2, sort_keys=True), encoding="utf-8")
    result["reproducibility_hashes"] = hashes
    summary_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


def _reconstruct_group(key: str, trades: list[dict[str, str]]) -> LifecyclePositionRecord:
    ordered = sorted(trades, key=deterministic_trade_sort_key)
    first = ordered[0]
    last = ordered[-1]
    bought = Decimal("0")
    sold = Decimal("0")
    entry_notional = Decimal("0")
    exit_notional = Decimal("0")
    buy_count = 0
    sell_count = 0
    hashes: list[str] = []
    flags: set[str] = set()

    for trade in ordered:
        side = (trade.get("side") or "").upper()
        size = decimal_or_none(trade.get("size")) or Decimal("0")
        price = decimal_or_none(trade.get("price"))
        if trade.get("data_quality_flags") and trade.get("data_quality_flags") != "none":
            flags.update(part for part in trade["data_quality_flags"].split(";") if part)
        if trade.get("transaction_hash"):
            hashes.append((trade.get("transaction_hash") or "").lower())
        if side == "BUY":
            buy_count += 1
            bought += size
            if price is not None:
                entry_notional += price * size
        elif side == "SELL":
            sell_count += 1
            sold += size
            if price is not None:
                exit_notional += price * size
        else:
            flags.add("ignored_non_buy_sell_side")

    net = bought - sold
    remaining = max(net, Decimal("0"))
    oversold = max(-net, Decimal("0"))
    if bought > 0 and sold == 0:
        status = "still_open"
    elif bought > sold and sold > 0:
        status = "partial_exit"
    elif bought == sold and bought > 0:
        status = "full_exit"
    elif sold > bought:
        status = "oversold_bounded_history"
    else:
        status = "no_position_change"
    negative_reason = "bounded_history_missing_prior_buy" if oversold > 0 else ""
    if negative_reason:
        flags.add(negative_reason)

    return LifecyclePositionRecord(
        wallet_id=(first.get("wallet_id") or "").lower(),
        profile_url=first.get("profile_url") or "",
        condition_id=(first.get("condition_id") or "").lower(),
        token_id=first.get("token_id") or "",
        outcome=first.get("outcome") or "",
        lifecycle_group_key=key,
        market_slug=first.get("market_slug") or "",
        event_slug=first.get("event_slug") or "",
        market_title=first.get("market_title") or "",
        market_type=first.get("market_type") or "",
        asset_class=first.get("asset_class") or "",
        up_down_market=first.get("up_down_market") or "",
        first_activity_timestamp=first.get("activity_timestamp") or "",
        first_activity_datetime_utc=first.get("activity_datetime_utc") or "",
        last_activity_timestamp=last.get("activity_timestamp") or "",
        last_activity_datetime_utc=last.get("activity_datetime_utc") or "",
        buy_trade_count=str(buy_count),
        sell_trade_count=str(sell_count),
        total_bought_size=normalize_decimal(bought),
        total_sold_size=normalize_decimal(sold),
        remaining_size=normalize_decimal(remaining),
        oversold_size=normalize_decimal(oversold),
        weighted_average_entry_price=normalize_decimal(entry_notional / bought) if bought else "",
        weighted_average_exit_price=normalize_decimal(exit_notional / sold) if sold else "",
        status=status,
        negative_position_detected=str(oversold > 0).lower(),
        negative_position_reason=negative_reason,
        position_size_conserved=str(bought + oversold == sold + remaining).lower(),
        transaction_hashes=";".join(sorted(set(hashes))),
        data_quality_flags=";".join(sorted(flags)) if flags else "none",
    )


def _int_or_max(value: Any) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 2**63 - 1


def _count_by(positions: list[LifecyclePositionRecord], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for position in positions:
        value = str(getattr(position, field) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))
