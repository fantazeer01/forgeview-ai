"""Behavior metrics for existing wallet-intelligence ingestion outputs.

This module reads local normalized public-data snapshots only. It has no
network, wallet, private-key, order-placement, copy-trading, capture, holdout,
or production-model capability.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, median
from typing import Any


DEFAULT_INPUT_DIR = Path("polymarket/data/wallet_intelligence/v1")
DEFAULT_OUTPUT_DIR = Path("polymarket/models/wallet_intelligence_v1/behavior_metrics")
UNAVAILABLE = "unavailable_from_public_snapshot"
PRICE_BUCKETS = [
    ("0_10c", 0.0, 0.10),
    ("10_20c", 0.10, 0.20),
    ("20_40c", 0.20, 0.40),
    ("40_60c", 0.40, 0.60),
    ("60_80c", 0.60, 0.80),
    ("80_100c", 0.80, 1.0000001),
]


def compute_behavior_metrics(
    input_dir: Path = DEFAULT_INPUT_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    profiles = _read_csv(input_dir / "wallet_profiles.csv")
    positions = _read_csv(input_dir / "wallet_positions.csv")
    if not profiles:
        raise ValueError(f"no wallet profiles found under {input_dir}")
    if not positions:
        raise ValueError(f"no wallet positions found under {input_dir}")

    positions_by_wallet: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in positions:
        positions_by_wallet[row["wallet_id"]].append(row)

    profile_by_wallet = {row["wallet_id"]: row for row in profiles}
    metric_rows = [
        wallet_metrics(wallet_id, profile_by_wallet.get(wallet_id, {}), positions_by_wallet[wallet_id])
        for wallet_id in sorted(positions_by_wallet)
    ]
    risk_rows = [copyability_risk_row(row) for row in metric_rows]
    similarity_rows = similarity_matrix(metric_rows)
    cluster_rows = [cluster_row(row) for row in metric_rows]
    report = build_report(metric_rows, risk_rows, similarity_rows, cluster_rows, input_dir, output_dir, generated_at)
    write_behavior_outputs(output_dir, metric_rows, similarity_rows, cluster_rows, risk_rows, report)
    return report


def wallet_metrics(wallet_id: str, profile: dict[str, str], rows: list[dict[str, str]]) -> dict[str, Any]:
    total = len(rows)
    fast_rows = [row for row in rows if row.get("market_type") == "fast_crypto"]
    weather_rows = [row for row in rows if row.get("market_type") == "weather"]
    non_crypto_rows = [row for row in rows if row.get("asset_exposure") == "OTHER"]
    entry_prices = [_num(row.get("avg_price")) for row in rows]
    entry_prices = [value for value in entry_prices if value is not None]
    position_sizes = [_position_size(row) for row in rows]
    position_sizes = [value for value in position_sizes if value is not None]
    outcomes = Counter(_side(row.get("outcome", "")) for row in rows)
    buckets = Counter(entry_bucket(value) for value in entry_prices)
    exposures = Counter(row.get("asset_exposure") or "OTHER" for row in rows)
    fast_share = _safe_div(len(fast_rows), total)
    weather_share = _safe_div(len(weather_rows), total)
    cheap_count = sum(1 for value in entry_prices if value <= 0.20)
    favorite_count = sum(1 for value in entry_prices if value >= 0.60)
    yes_count = outcomes.get("YES", 0)
    no_count = outcomes.get("NO", 0)
    yes_no_total = yes_count + no_count
    classification = classify_wallet(total, fast_share, weather_share)
    size_concentration = _largest_share(position_sizes)
    repeated_asset_timeframe = repeated_asset_timeframe_pattern(rows)
    repeated_price_bucket = _top_counter_label(buckets)
    repeated_side = _top_counter_label(Counter(_side(row.get("outcome", "")) for row in rows if _side(row.get("outcome", "")) != "OTHER"))
    resolution_like = sum(1 for row in rows if row.get("position_status") == "closed" and _num(row.get("cur_price")) in (0.0, 1.0))
    metrics = {
        "wallet_id": wallet_id,
        "profile_url": profile.get("profile_url", ""),
        "wallet_classification": classification,
        "positions_visible": total,
        "active_positions_count": profile.get("active_positions_count", ""),
        "closed_positions_count": profile.get("closed_positions_count", ""),
        "fast_crypto_positions_count": len(fast_rows),
        "weather_positions_count": len(weather_rows),
        "mixed_or_other_positions_count": total - len(fast_rows) - len(weather_rows),
        "btc_updown_count": sum(1 for row in fast_rows if row.get("asset_exposure") == "BTC"),
        "eth_updown_count": sum(1 for row in fast_rows if row.get("asset_exposure") == "ETH"),
        "sol_updown_count": sum(1 for row in fast_rows if row.get("asset_exposure") == "SOL"),
        "non_crypto_count": len(non_crypto_rows),
        "fast_market_share": _fmt_float(fast_share),
        "yes_count": yes_count,
        "no_count": no_count,
        "yes_no_balance": _fmt_float(1.0 - abs(yes_count - no_count) / yes_no_total) if yes_no_total else UNAVAILABLE,
        "cheap_side_buying_share": _fmt_float(_safe_div(cheap_count, len(entry_prices))) if entry_prices else UNAVAILABLE,
        "favorite_side_buying_share": _fmt_float(_safe_div(favorite_count, len(entry_prices))) if entry_prices else UNAVAILABLE,
        "average_entry_price": _fmt_float(mean(entry_prices)) if entry_prices else UNAVAILABLE,
        "median_entry_price": _fmt_float(median(entry_prices)) if entry_prices else UNAVAILABLE,
        "entry_bucket_0_10c": buckets.get("0_10c", 0),
        "entry_bucket_10_20c": buckets.get("10_20c", 0),
        "entry_bucket_20_40c": buckets.get("20_40c", 0),
        "entry_bucket_40_60c": buckets.get("40_60c", 0),
        "entry_bucket_60_80c": buckets.get("60_80c", 0),
        "entry_bucket_80_100c": buckets.get("80_100c", 0),
        "average_position_size": _fmt_float(mean(position_sizes)) if position_sizes else UNAVAILABLE,
        "median_position_size": _fmt_float(median(position_sizes)) if position_sizes else UNAVAILABLE,
        "largest_visible_position": _fmt_float(max(position_sizes)) if position_sizes else UNAVAILABLE,
        "sizing_concentration": _fmt_float(size_concentration) if position_sizes else UNAVAILABLE,
        "repeated_asset_timeframe_markets": repeated_asset_timeframe,
        "repeated_side": repeated_side,
        "repeated_price_bucket": repeated_price_bucket,
        "repeated_cheap_side_behavior": "yes" if cheap_count >= 10 or _safe_div(cheap_count, len(entry_prices)) >= 0.25 else "no",
        "repeated_late_window_behavior": UNAVAILABLE,
        "closed_resolution_like_price_share": _fmt_float(_safe_div(resolution_like, sum(1 for row in rows if row.get("position_status") == "closed"))),
        "public_data_completeness": public_data_completeness(profile, rows),
        "likely_delay_risk": likely_delay_risk(classification, fast_share),
        "liquidity_fill_uncertainty": liquidity_fill_uncertainty(position_sizes),
        "unknown_exit_timing_risk": "high",
        "overall_copyability_score": "",
        "data_limit_notes": "first-page public snapshot only; holding time, drawdown, entry/exit linkage, late-window timing, and Binance-lag behavior unavailable",
    }
    metrics["overall_copyability_score"] = copyability_score(metrics)
    metrics["feature_vector"] = json.dumps(feature_vector(metrics), sort_keys=True)
    metrics["exposure_distribution"] = json.dumps(dict(exposures), sort_keys=True)
    return metrics


def classify_wallet(total: int, fast_share: float, weather_share: float) -> str:
    if total < 10:
        return "inactive_or_insufficient_data"
    if fast_share >= 0.60:
        return "fast_crypto_focused"
    if weather_share >= 0.60:
        return "weather_focused"
    return "mixed"


def entry_bucket(value: float) -> str:
    for label, low, high in PRICE_BUCKETS:
        if low <= value < high:
            return label
    return "outside_0_100c"


def repeated_asset_timeframe_pattern(rows: list[dict[str, str]]) -> str:
    counter = Counter()
    for row in rows:
        asset = row.get("asset_exposure") or "OTHER"
        timeframe = _timeframe(row.get("slug", ""), row.get("title", ""))
        counter[f"{asset}:{timeframe}"] += 1
    return _top_counter_label(counter)


def public_data_completeness(profile: dict[str, str], rows: list[dict[str, str]]) -> str:
    notes = (profile.get("data_availability_notes") or "").lower()
    if "truncated" in notes or len(rows) >= 50:
        return "partial_truncated_snapshot"
    if rows:
        return "partial_public_snapshot"
    return "insufficient"


def likely_delay_risk(classification: str, fast_share: float) -> str:
    if classification == "fast_crypto_focused" or fast_share >= 0.50:
        return "high"
    if classification == "weather_focused":
        return "medium"
    return "medium_high"


def liquidity_fill_uncertainty(position_sizes: list[float]) -> str:
    if not position_sizes:
        return "unknown"
    if max(position_sizes) >= 10000 or _largest_share(position_sizes) >= 0.50:
        return "high"
    if max(position_sizes) >= 1000:
        return "medium_high"
    return "medium"


def copyability_score(metrics: dict[str, Any]) -> int:
    score = 20
    if metrics["wallet_classification"] == "fast_crypto_focused":
        score += 15
    if _float(metrics["yes_no_balance"]) >= 0.70:
        score += 5
    if _float(metrics["cheap_side_buying_share"]) >= 0.20:
        score += 5
    if metrics["public_data_completeness"] == "partial_truncated_snapshot":
        score -= 10
    if metrics["likely_delay_risk"] == "high":
        score -= 10
    if metrics["liquidity_fill_uncertainty"] == "high":
        score -= 5
    score -= 10  # exit timing is unknown for every current wallet.
    return max(0, min(60, score))


def copyability_risk_row(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "wallet_id": metrics["wallet_id"],
        "wallet_classification": metrics["wallet_classification"],
        "public_data_completeness": metrics["public_data_completeness"],
        "likely_delay_risk": metrics["likely_delay_risk"],
        "liquidity_fill_uncertainty": metrics["liquidity_fill_uncertainty"],
        "unknown_exit_timing_risk": metrics["unknown_exit_timing_risk"],
        "overall_copyability_score": metrics["overall_copyability_score"],
        "risk_summary": (
            "Research-only; score is capped because complete fill history, observation delay, "
            "liquidity consumption, and exit timing are unavailable."
        ),
    }


def feature_vector(metrics: dict[str, Any]) -> list[float]:
    positions = max(1, int(metrics["positions_visible"]))
    return [
        _float(metrics["fast_market_share"]),
        int(metrics["btc_updown_count"]) / positions,
        int(metrics["eth_updown_count"]) / positions,
        int(metrics["sol_updown_count"]) / positions,
        int(metrics["non_crypto_count"]) / positions,
        _float(metrics["cheap_side_buying_share"]),
        _float(metrics["favorite_side_buying_share"]),
        _float(metrics["yes_no_balance"]),
        _float(metrics["sizing_concentration"]),
        _float(metrics["entry_bucket_0_10c"]) / positions,
        _float(metrics["entry_bucket_10_20c"]) / positions,
        _float(metrics["entry_bucket_20_40c"]) / positions,
        _float(metrics["entry_bucket_40_60c"]) / positions,
        _float(metrics["entry_bucket_60_80c"]) / positions,
        _float(metrics["entry_bucket_80_100c"]) / positions,
    ]


def similarity_matrix(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    vectors = {row["wallet_id"]: feature_vector(row) for row in metric_rows}
    wallet_ids = sorted(vectors)
    matrix = []
    for left in wallet_ids:
        out = {"wallet_id": left}
        for right in wallet_ids:
            out[right] = _fmt_float(cosine_similarity(vectors[left], vectors[right]))
        matrix.append(out)
    return matrix


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def cluster_row(metrics: dict[str, Any]) -> dict[str, Any]:
    clusters = []
    if metrics["wallet_classification"] == "fast_crypto_focused":
        clusters.append("fast_crypto_directional")
    if _float(metrics["cheap_side_buying_share"]) >= 0.20:
        clusters.append("cheap_side_buyer")
    if int(metrics["positions_visible"]) >= 75 and _float(metrics["fast_market_share"]) >= 0.50:
        clusters.append("high_volume_repeated_pattern")
    if metrics["wallet_classification"] == "weather_focused":
        clusters.append("weather_other")
    if not clusters:
        clusters.append("mixed_or_insufficient")
    return {
        "wallet_id": metrics["wallet_id"],
        "primary_cluster": clusters[0],
        "clusters": "|".join(clusters),
        "rationale": (
            f"classification={metrics['wallet_classification']}; "
            f"fast_share={metrics['fast_market_share']}; "
            f"cheap_share={metrics['cheap_side_buying_share']}; "
            f"positions={metrics['positions_visible']}"
        ),
    }


def build_report(
    metric_rows: list[dict[str, Any]],
    risk_rows: list[dict[str, Any]],
    similarity_rows: list[dict[str, Any]],
    cluster_rows: list[dict[str, Any]],
    input_dir: Path,
    output_dir: Path,
    generated_at: str,
) -> dict[str, Any]:
    strongest = max(metric_rows, key=lambda row: (int(row["fast_crypto_positions_count"]), _float(row["fast_market_share"])))
    classifications = Counter(row["wallet_classification"] for row in metric_rows)
    top_pairs = most_similar_pairs(similarity_rows)
    report = {
        "task": "Wallet Intelligence Behavior Metrics v1",
        "generated_at": generated_at,
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "wallets_analyzed": len(metric_rows),
        "strongest_fast_market_wallet": strongest["wallet_id"],
        "strongest_fast_market_wallet_fast_positions": int(strongest["fast_crypto_positions_count"]),
        "classifications": dict(classifications),
        "common_behavior_patterns": common_patterns(metric_rows, cluster_rows),
        "entry_price_patterns": entry_patterns(metric_rows),
        "yes_no_patterns": yes_no_patterns(metric_rows),
        "copyability_risks": [
            "All scores are research-only and capped because public snapshots lack full trade/fill history.",
            "Likely delay risk is high for fast crypto wallets because entry windows can be short.",
            "Liquidity/fill uncertainty is material where visible position sizes are large or concentrated.",
            "Unknown exit timing prevents claims about hold-to-resolution versus exit-before-expiry.",
        ],
        "most_similar_wallet_pairs": top_pairs,
        "recommended_next_task": "Wallet Intelligence Deep History Feasibility v1",
        "strict_boundaries": [
            "no live trading",
            "no trade copying",
            "no wallet/private-key connection",
            "no order placement",
            "no sealed holdout inspection",
            "no holdout evaluation",
            "no market capture campaign",
            "no copyability overclaim",
        ],
    }
    return report


def common_patterns(metric_rows: list[dict[str, Any]], cluster_rows: list[dict[str, Any]]) -> list[str]:
    clusters = Counter(row["primary_cluster"] for row in cluster_rows)
    fast_wallets = [row["wallet_id"] for row in metric_rows if row["wallet_classification"] == "fast_crypto_focused"]
    cheap_wallets = [row["wallet_id"] for row in metric_rows if _float(row["cheap_side_buying_share"]) >= 0.20]
    return [
        f"{len(fast_wallets)} wallets are fast-crypto focused.",
        f"Primary clusters: {dict(clusters)}.",
        f"{len(cheap_wallets)} wallets show repeated cheap-side buying at >=20% of visible entries.",
        "Repeated late-window behavior remains unavailable from this snapshot.",
    ]


def entry_patterns(metric_rows: list[dict[str, Any]]) -> dict[str, Any]:
    bucket_totals = Counter()
    averages = []
    for row in metric_rows:
        averages.append(_float(row["average_entry_price"]))
        for label, _, _ in PRICE_BUCKETS:
            bucket_totals[label] += int(row[f"entry_bucket_{label}"])
    return {
        "mean_wallet_average_entry_price": _fmt_float(mean(averages)) if averages else UNAVAILABLE,
        "aggregate_bucket_counts": dict(bucket_totals),
        "dominant_bucket": _top_counter_label(bucket_totals),
    }


def yes_no_patterns(metric_rows: list[dict[str, Any]]) -> dict[str, Any]:
    yes = sum(int(row["yes_count"]) for row in metric_rows)
    no = sum(int(row["no_count"]) for row in metric_rows)
    total = yes + no
    return {
        "yes_count": yes,
        "no_count": no,
        "yes_no_balance": _fmt_float(1.0 - abs(yes - no) / total) if total else UNAVAILABLE,
        "dominant_side": "YES" if yes > no else "NO" if no > yes else "balanced",
    }


def most_similar_pairs(similarity_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs = []
    seen = set()
    for row in similarity_rows:
        left = row["wallet_id"]
        for right, value in row.items():
            if right == "wallet_id" or left == right:
                continue
            key = tuple(sorted((left, right)))
            if key in seen:
                continue
            seen.add(key)
            pairs.append({"wallet_a": key[0], "wallet_b": key[1], "similarity": value})
    return sorted(pairs, key=lambda item: float(item["similarity"]), reverse=True)[:5]


def write_behavior_outputs(
    output_dir: Path,
    metric_rows: list[dict[str, Any]],
    similarity_rows: list[dict[str, Any]],
    cluster_rows: list[dict[str, Any]],
    risk_rows: list[dict[str, Any]],
    report: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_public = [{k: v for k, v in row.items() if k != "feature_vector"} for row in metric_rows]
    _write_csv(output_dir / "wallet_behavior_metrics.csv", metrics_public)
    _write_csv(output_dir / "wallet_similarity_matrix.csv", similarity_rows)
    _write_csv(output_dir / "wallet_clusters.csv", cluster_rows)
    _write_csv(output_dir / "copyability_risk.csv", risk_rows)
    (output_dir / "behavior_metrics_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "behavior_metrics_report.md").write_text(render_markdown_report(report, metrics_public), encoding="utf-8")


def render_markdown_report(report: dict[str, Any], metrics: list[dict[str, Any]]) -> str:
    lines = [
        "# Wallet Intelligence Behavior Metrics v1",
        "",
        f"Generated at: {report['generated_at']}",
        "",
        "This report is derived only from existing Wallet Intelligence Data Ingestion v1 outputs. It contains no live trading, order placement, wallet/private-key handling, trade copying, capture campaign, holdout evaluation, or production model training.",
        "",
        "## Summary",
        "",
        f"- Wallets analyzed: {report['wallets_analyzed']}",
        f"- Strongest fast-market wallet: `{report['strongest_fast_market_wallet']}` ({report['strongest_fast_market_wallet_fast_positions']} fast crypto positions)",
        f"- Classifications: `{json.dumps(report['classifications'], sort_keys=True)}`",
        f"- Recommended next task: {report['recommended_next_task']}",
        "",
        "## Wallet Metrics",
        "",
    ]
    for row in sorted(metrics, key=lambda item: item["wallet_id"]):
        lines.extend(
            [
                f"### {row['wallet_id']}",
                "",
                f"- Classification: {row['wallet_classification']}",
                f"- Fast market share: {row['fast_market_share']}",
                f"- BTC/ETH/SOL Up-Down counts: {row['btc_updown_count']} / {row['eth_updown_count']} / {row['sol_updown_count']}",
                f"- YES/NO counts: {row['yes_count']} / {row['no_count']} (balance {row['yes_no_balance']})",
                f"- Average/median entry: {row['average_entry_price']} / {row['median_entry_price']}",
                f"- Cheap-side share: {row['cheap_side_buying_share']}",
                f"- Favorite-side share: {row['favorite_side_buying_share']}",
                f"- Largest visible position: {row['largest_visible_position']}",
                f"- Sizing concentration: {row['sizing_concentration']}",
                f"- Repeated pattern: {row['repeated_asset_timeframe_markets']}",
                f"- Copyability score: {row['overall_copyability_score']}",
                f"- Limits: {row['data_limit_notes']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Common Patterns",
            "",
            *[f"- {item}" for item in report["common_behavior_patterns"]],
            "",
            "## Copyability Risks",
            "",
            *[f"- {item}" for item in report["copyability_risks"]],
            "",
        ]
    )
    return "\n".join(lines)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = list(rows[0].keys()) if rows else ["wallet_id"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _num(value: Any) -> float | None:
    if value in (None, "", UNAVAILABLE, "unavailable_from_public_profile_snapshot"):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _float(value: Any) -> float:
    parsed = _num(value)
    return parsed if parsed is not None else 0.0


def _fmt_float(value: float) -> str:
    if value is None or not math.isfinite(value):
        return UNAVAILABLE
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _safe_div(left: float, right: float) -> float:
    return left / right if right else 0.0


def _position_size(row: dict[str, str]) -> float | None:
    return _num(row.get("total_bought")) or _num(row.get("size")) or _num(row.get("initial_value"))


def _side(outcome: str) -> str:
    lowered = (outcome or "").strip().lower()
    if lowered in {"yes", "up"}:
        return "YES"
    if lowered in {"no", "down"}:
        return "NO"
    return "OTHER"


def _timeframe(slug: str, title: str) -> str:
    text = f"{slug} {title}".lower()
    if "15m" in text or "15-min" in text:
        return "15m"
    if "5m" in text or "5-min" in text:
        return "5m"
    if "updown" in text or "up-or-down" in text or "up or down" in text:
        return "updown_window_unknown"
    return "other_timeframe"


def _top_counter_label(counter: Counter[str]) -> str:
    if not counter:
        return UNAVAILABLE
    label, count = counter.most_common(1)[0]
    total = sum(counter.values())
    return f"{label}:{count}/{total}:{_fmt_float(_safe_div(count, total))}"


def _largest_share(values: list[float]) -> float:
    total = sum(values)
    return max(values) / total if total else 0.0
