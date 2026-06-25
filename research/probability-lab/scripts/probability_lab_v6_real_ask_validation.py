import argparse
import csv
import glob
import json
import math
import ssl
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


SNAPSHOTS = {"4m": 240, "3m": 180, "2m": 120, "1m": 60, "30s": 30}
THRESHOLDS = [0.02, 0.05, 0.10, 0.15]
V5_SETUPS = {"4m": 0.10, "3m": 0.15, "2m": 0.15, "1m": 0.15, "30s": 0.15}
FEATURES = [
    "market_probability",
    "btc_return_1m",
    "btc_return_5m",
    "btc_return_15m",
    "btc_volatility_15m",
]
BTC_FEATURES = FEATURES[1:]
DEFAULT_GLOB = r"D:\ForgeViewAI\output\research\data\recorder\forgeview_live_btc5m*.csv"
DEFAULT_MODEL = r"D:\ForgeViewAI\output\research\data\legacy-data\polymarket_btc5m_probability_lab_v3_snapshot_model_results.json"
DEFAULT_FALLBACK = r"D:\ForgeViewAI\output\research\data\legacy-data\polymarket_btc5m_probability_lab_v1.csv"
DEFAULT_OUT = r"D:\ForgeViewAI\output\research\data\validation\forgeview_probability_lab_v6_real_ask_validation.json"
DEFAULT_TRADES = r"D:\ForgeViewAI\output\research\data\validation\forgeview_probability_lab_v6_real_ask_trades.csv"
DEFAULT_CACHE = r"D:\ForgeViewAI\state\forgeview_probability_lab_v6_outcomes.json"
WORKSPACE_ROOT = Path(r"D:\ForgeViewAI")


def workspace_path(value):
    resolved = Path(value).resolve()
    root = WORKSPACE_ROOT.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"path must stay inside {root}: {resolved}")
    return resolved


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_time(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def http_json(url, timeout=8, attempts=3):
    last = None
    context = ssl.create_default_context()
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "forgeview-research-validator/1.0", "Accept": "application/json"},
            )
            with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
                return json.loads(response.read().decode("utf-8"))
        except (
            TimeoutError,
            ssl.SSLError,
            urllib.error.URLError,
            urllib.error.HTTPError,
            ConnectionError,
            OSError,
        ) as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"{url}: {last!r}")


def load_snapshots(pattern):
    loaded = []
    files = sorted(glob.glob(pattern))
    seen = set()
    for path in files:
        with open(path, encoding="utf-8") as handle:
            for raw in csv.DictReader(handle):
                market_id = raw.get("market_id", "")
                timestamp = parse_time(raw.get("captured_at"))
                seconds = number(raw.get("seconds_to_resolution"))
                if not market_id or timestamp is None or seconds is None:
                    continue
                key = (market_id, round(timestamp, 3))
                if key in seen:
                    continue
                seen.add(key)
                row = {
                    "source_file": path,
                    "market_id": market_id,
                    "condition_id": raw.get("condition_id", ""),
                    "timestamp": timestamp,
                    "seconds_to_resolution": seconds,
                    "best_ask_yes": number(raw.get("best_ask_yes")),
                    "best_ask_no": number(raw.get("best_ask_no")),
                    "best_bid_yes": number(raw.get("best_bid_yes")),
                    "best_bid_no": number(raw.get("best_bid_no")),
                    **{feature: number(raw.get(feature)) for feature in BTC_FEATURES},
                }
                yes_mid = midpoint(row["best_bid_yes"], row["best_ask_yes"])
                no_mid = midpoint(row["best_bid_no"], row["best_ask_no"])
                if yes_mid is not None:
                    row["market_probability"] = yes_mid
                elif no_mid is not None:
                    row["market_probability"] = 1.0 - no_mid
                else:
                    row["market_probability"] = number(raw.get("market_probability"))
                loaded.append(row)
    loaded.sort(key=lambda row: row["timestamp"])
    return files, loaded


def midpoint(bid, ask):
    if bid is not None and ask is not None:
        return (bid + ask) / 2.0
    return ask if ask is not None else bid


def choose_bucket_rows(rows, tolerance=45):
    by_market = defaultdict(list)
    for row in rows:
        if all(row.get(feature) is not None for feature in FEATURES):
            by_market[row["market_id"]].append(row)
    selected = {name: [] for name in SNAPSHOTS}
    for market_rows in by_market.values():
        for name, target in SNAPSHOTS.items():
            candidates = [row for row in market_rows if abs(row["seconds_to_resolution"] - target) <= tolerance]
            if candidates:
                selected[name].append(
                    min(candidates, key=lambda row: (abs(row["seconds_to_resolution"] - target), row["timestamp"]))
                )
    return selected


def load_outcomes(path):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def resolve_outcomes(rows, cache_path):
    cache = load_outcomes(cache_path)
    errors = {}
    market_rows = {}
    for row in rows:
        if row["market_id"] not in market_rows or (not market_rows[row["market_id"]]["condition_id"] and row["condition_id"]):
            market_rows[row["market_id"]] = row
    for market_id, row in market_rows.items():
        if cache.get(market_id, {}).get("outcome") in ("UP", "DOWN"):
            continue
        condition_id = row["condition_id"]
        if not condition_id:
            errors[market_id] = "missing condition_id"
            continue
        try:
            data = http_json(f"https://clob.polymarket.com/markets/{condition_id}")
            if not data.get("closed"):
                errors[market_id] = "market not resolved"
                continue
            winner = None
            for token in data.get("tokens") or []:
                if token.get("winner"):
                    winner = str(token.get("outcome", "")).upper()
                    break
            if winner not in ("UP", "DOWN"):
                errors[market_id] = "winning outcome unavailable"
                continue
            cache[market_id] = {
                "outcome": winner,
                "condition_id": condition_id,
                "resolved_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            errors[market_id] = str(exc)
    cache_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    return cache, errors


def scaler_from_csv(path):
    with path.open(encoding="utf-8") as handle:
        rows = sorted(list(csv.DictReader(handle)), key=lambda row: parse_time(row["timestamp"]) or 0)
    train = rows[: int(len(rows) * 0.70)]
    means, stds = {}, {}
    for feature in FEATURES:
        values = [float(row[feature]) for row in train]
        means[feature] = sum(values) / len(values)
        stds[feature] = math.sqrt(sum((value - means[feature]) ** 2 for value in values) / len(values)) or 1.0
    return means, stds, len(train)


def load_models(model_path, fallback_path):
    report = json.loads(model_path.read_text(encoding="utf-8"))
    fallback_means, fallback_stds, fallback_n = scaler_from_csv(fallback_path)
    models = {}
    for snapshot, result in report["snapshots"].items():
        model = result["model_d_market_plus_btc_features"]
        dataset_path = Path(result.get("dataset_path", ""))
        if dataset_path.exists():
            means, stds, train_n = scaler_from_csv(dataset_path)
            scaler_source = str(dataset_path)
            exact_scaler = True
        else:
            means, stds, train_n = fallback_means, fallback_stds, fallback_n
            scaler_source = str(fallback_path)
            exact_scaler = False
        models[snapshot] = {
            "weights": model["weights"],
            "means": means,
            "stds": stds,
            "train_n": train_n,
            "scaler_source": scaler_source,
            "exact_scaler": exact_scaler,
        }
    return models


def sigmoid(value):
    if value >= 0:
        exp_value = math.exp(-value)
        return 1.0 / (1.0 + exp_value)
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def model_probability(row, model):
    values = [(row[feature] - model["means"][feature]) / model["stds"][feature] for feature in FEATURES]
    return sigmoid(model["weights"][0] + sum(weight * value for weight, value in zip(model["weights"][1:], values)))


def trade_for(row, probability, threshold, outcome):
    market_probability = row["market_probability"]
    if probability - market_probability >= threshold:
        side, ask = "UP", row["best_ask_yes"]
    elif market_probability - probability >= threshold:
        side, ask = "DOWN", row["best_ask_no"]
    else:
        return None
    if ask is None or not 0 < ask < 1:
        return {"skip": "captured ask unavailable", "side": side}
    win = side == outcome
    payout = 1.0 if win else 0.0
    return {
        "skip": "",
        "market_id": row["market_id"],
        "timestamp": row["timestamp"],
        "seconds_to_resolution": row["seconds_to_resolution"],
        "side": side,
        "outcome": outcome,
        "win": win,
        "market_probability_up": market_probability,
        "model_probability_up": probability,
        "execution_ask": ask,
        "cost": ask,
        "payout": payout,
        "net_pnl": payout - ask,
    }


def max_drawdown(trades):
    equity = peak = 0.0
    drawdown = 0.0
    for trade in sorted(trades, key=lambda row: row["timestamp"]):
        equity += trade["net_pnl"]
        peak = max(peak, equity)
        drawdown = min(drawdown, equity - peak)
    return drawdown


def summarize(trades, signals, skipped):
    cost = sum(row["cost"] for row in trades)
    payout = sum(row["payout"] for row in trades)
    pnl = payout - cost
    return {
        "signals": signals,
        "trades": len(trades),
        "skipped_missing_ask": skipped,
        "wins": sum(row["win"] for row in trades),
        "winrate": sum(row["win"] for row in trades) / len(trades) if trades else None,
        "cost": cost,
        "payout": payout,
        "net_pnl": pnl,
        "roi": pnl / cost if cost else None,
        "max_drawdown": max_drawdown(trades),
        "up_trades": sum(row["side"] == "UP" for row in trades),
        "down_trades": sum(row["side"] == "DOWN" for row in trades),
    }


def round_values(value):
    if isinstance(value, float):
        return round(value, 8)
    if isinstance(value, dict):
        return {key: round_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [round_values(item) for item in value]
    return value


def write_trades(path, trades):
    fields = [
        "snapshot",
        "threshold",
        "market_id",
        "timestamp",
        "seconds_to_resolution",
        "side",
        "outcome",
        "win",
        "market_probability_up",
        "model_probability_up",
        "execution_ask",
        "cost",
        "payout",
        "net_pnl",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in trades])


def main():
    parser = argparse.ArgumentParser(description="Research-only validation using captured executable asks.")
    parser.add_argument("--input-glob", default=DEFAULT_GLOB)
    parser.add_argument("--model-report", default=DEFAULT_MODEL)
    parser.add_argument("--scaler-fallback", default=DEFAULT_FALLBACK)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--trades-out", default=DEFAULT_TRADES)
    parser.add_argument("--outcome-cache", default=DEFAULT_CACHE)
    parser.add_argument("--bucket-tolerance", type=float, default=45)
    parser.add_argument("--min-confirmation-trades", type=int, default=30)
    args = parser.parse_args()

    files, rows = load_snapshots(args.input_glob)
    selected = choose_bucket_rows(rows, args.bucket_tolerance)
    cache_path = workspace_path(args.outcome_cache)
    outcomes, resolution_errors = resolve_outcomes(rows, cache_path)
    models = load_models(workspace_path(args.model_report), workspace_path(args.scaler_fallback))
    results, all_trades, best = {}, [], None

    for snapshot in SNAPSHOTS:
        bucket_rows = selected[snapshot]
        resolved_rows = [row for row in bucket_rows if outcomes.get(row["market_id"], {}).get("outcome")]
        thresholds = {}
        for threshold in THRESHOLDS:
            trades, signals, skipped = [], 0, 0
            for row in resolved_rows:
                probability = model_probability(row, models[snapshot])
                trade = trade_for(row, probability, threshold, outcomes[row["market_id"]]["outcome"])
                if trade is None:
                    continue
                signals += 1
                if trade.get("skip"):
                    skipped += 1
                    continue
                trade.update({"snapshot": snapshot, "threshold": threshold})
                trades.append(trade)
                all_trades.append(trade)
            summary = summarize(trades, signals, skipped)
            thresholds[f"{int(threshold * 100)}pct"] = summary
            candidate = {"snapshot": snapshot, "threshold": threshold, **summary}
            if summary["trades"] and (
                best is None or (summary["roi"], summary["net_pnl"], summary["trades"]) >
                (best["roi"], best["net_pnl"], best["trades"])
            ):
                best = candidate
        results[snapshot] = {
            "target_seconds_before_resolution": SNAPSHOTS[snapshot],
            "captured_markets_in_bucket": len(bucket_rows),
            "resolved_markets_in_bucket": len(resolved_rows),
            "v5_threshold": V5_SETUPS[snapshot],
            "v5_real_ask_result": thresholds[f"{int(V5_SETUPS[snapshot] * 100)}pct"],
            "thresholds": thresholds,
        }

    enough_data = bool(best and best["trades"] >= args.min_confirmation_trades)
    confirmed = bool(enough_data and best["net_pnl"] > 0 and best["roi"] > 0 and all(m["exact_scaler"] for m in models.values()))
    output = {
        "research_only": True,
        "input_files": files,
        "recorder_rows_loaded": len(rows),
        "unique_markets_loaded": len({row["market_id"] for row in rows}),
        "resolved_markets": len(outcomes),
        "resolution_errors": resolution_errors,
        "snapshot_tolerance_seconds": args.bucket_tolerance,
        "model": "v3 Model D frozen coefficients",
        "scaler_exact": all(model["exact_scaler"] for model in models.values()),
        "scaler_sources": {name: model["scaler_source"] for name, model in models.items()},
        "results": results,
        "best_setup": best,
        "minimum_confirmation_trades": args.min_confirmation_trades,
        "real_edge_confirmed": confirmed,
        "decision": "continue" if confirmed else "refine",
        "limitations": [
            "The deleted v3 snapshot CSVs were unavailable, so the archived v1 training distribution was used to scale frozen v3 coefficients."
            if not all(model["exact_scaler"] for model in models.values()) else "",
            "A positive setup is not confirmed unless it has the minimum trade count and exact model scaling.",
            "One contract per signal; captured ask is treated as fully executable with no additional fee or size/slippage adjustment.",
        ],
    }
    output["limitations"] = [item for item in output["limitations"] if item]
    write_trades(workspace_path(args.trades_out), all_trades)
    workspace_path(args.out).write_text(json.dumps(round_values(output), indent=2), encoding="utf-8")
    print(json.dumps(round_values(output), indent=2))


if __name__ == "__main__":
    main()
