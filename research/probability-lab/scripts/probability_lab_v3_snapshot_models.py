import csv
import json
import math
import ssl
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT = DATA_DIR / "polymarket_btc5m_probability_lab_v3_snapshot_model_results.json"

START_TS = int(datetime(2026, 6, 14, tzinfo=timezone.utc).timestamp())
END_TS = int(datetime(2026, 6, 17, tzinfo=timezone.utc).timestamp())
SNAPSHOTS = {
    "4m": 240,
    "3m": 180,
    "2m": 120,
    "1m": 60,
    "30s": 30,
}
BTC_FEATURES = [
    "btc_return_1m",
    "btc_return_5m",
    "btc_return_15m",
    "btc_volatility_15m",
]

CTX = ssl.create_default_context()


def http_json(url, timeout=35, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json",
                    "Connection": "close",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as exc:
            last = exc
            time.sleep(0.25 * (i + 1))
    raise last


def fetch_market(start_ts):
    slug = f"btc-updown-5m-{start_ts}"
    qs = urllib.parse.urlencode({"closed": "true", "limit": 1, "slug": slug})
    data = http_json(f"https://gamma-api.polymarket.com/markets?{qs}")
    rows = data if isinstance(data, list) else data.get("value") or data.get("data") or []
    if not rows:
        return None
    market = rows[0]
    if market.get("slug") != slug:
        return None
    token_ids = json.loads(market.get("clobTokenIds") or "[]")
    outcomes = json.loads(market.get("outcomes") or "[]")
    condition_id = market.get("conditionId") or market.get("condition_id")
    if len(token_ids) != 2 or len(outcomes) != 2 or not condition_id or "Up" not in outcomes:
        return None
    return {
        "market_id": slug,
        "condition_id": condition_id,
        "open_timestamp": start_ts,
        "resolution_timestamp": start_ts + 300,
        "token_ids": [str(x) for x in token_ids],
        "outcomes": outcomes,
    }


def resolve_market(market):
    data = http_json(f"https://clob.polymarket.com/markets/{market['condition_id']}")
    tokens = data.get("tokens") or []
    winners = {str(t.get("token_id")): bool(t.get("winner")) for t in tokens}
    if not data.get("closed") or not winners:
        return None
    final_outcome = None
    for token_id, outcome in zip(market["token_ids"], market["outcomes"]):
        if winners.get(token_id):
            final_outcome = outcome
            break
    if final_outcome not in ("Up", "Down"):
        return None
    market = dict(market)
    market["up_token"] = market["token_ids"][market["outcomes"].index("Up")]
    market["final_outcome"] = final_outcome
    market["outcome"] = 1 if final_outcome == "Up" else 0
    return market


def price_history(token_id, start_ts, end_ts):
    qs = urllib.parse.urlencode({"market": token_id, "startTs": start_ts, "endTs": end_ts})
    data = http_json(f"https://clob.polymarket.com/prices-history?{qs}", tries=3)
    return data.get("history") or []


def fetch_market_history(market):
    hist = price_history(market["up_token"], market["open_timestamp"], market["resolution_timestamp"])
    points = [
        (int(p.get("t") or 0), float(p.get("p") or 0))
        for p in hist
        if 0 < float(p.get("p") or 0) < 1
    ]
    return market["market_id"], points


def snapshot_probability(points, resolution_ts, seconds_before):
    if not points:
        return None
    target_ts = resolution_ts - seconds_before
    before = [p for p in points if p[0] <= target_ts]
    return max(before, key=lambda x: x[0]) if before else min(points, key=lambda x: abs(x[0] - target_ts))


def fetch_binance_klines(start_ts, end_ts):
    closes = {}
    cursor = (start_ts - 3600) * 1000
    end_ms = (end_ts + 300) * 1000
    while cursor < end_ms:
        qs = urllib.parse.urlencode(
            {
                "symbol": "BTCUSDT",
                "interval": "1m",
                "startTime": cursor,
                "endTime": end_ms,
                "limit": 1000,
            }
        )
        rows = http_json(f"https://api.binance.com/api/v3/klines?{qs}", timeout=35)
        if not rows:
            break
        for row in rows:
            closes[int(row[0] // 1000)] = float(row[4])
        cursor = int(rows[-1][0]) + 60_000
        time.sleep(0.05)
    return closes


def close_at_or_before(closes, ts):
    minute_ts = ts - (ts % 60)
    for candidate in range(minute_ts, minute_ts - 600, -60):
        if candidate in closes:
            return closes[candidate]
    return None


def ret(closes, ts, minutes):
    now = close_at_or_before(closes, ts)
    then = close_at_or_before(closes, ts - minutes * 60)
    if now is None or then is None or then == 0:
        return None
    return (now / then) - 1


def realized_vol_15m(closes, ts):
    vals = []
    for i in range(15, 0, -1):
        p0 = close_at_or_before(closes, ts - i * 60)
        p1 = close_at_or_before(closes, ts - (i - 1) * 60)
        if p0 and p1 and p0 > 0:
            vals.append(math.log(p1 / p0))
    if len(vals) < 5:
        return None
    mean = sum(vals) / len(vals)
    return math.sqrt(sum((x - mean) ** 2 for x in vals) / len(vals))


def sigmoid(z):
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def logit(p):
    eps = 1e-6
    p = min(1 - eps, max(eps, p))
    return math.log(p / (1 - p))


def standardize(train, test, features):
    means, stds = {}, {}
    for feature in features:
        vals = [r[feature] for r in train]
        mean = sum(vals) / len(vals)
        std = math.sqrt(sum((x - mean) ** 2 for x in vals) / len(vals)) or 1.0
        means[feature] = mean
        stds[feature] = std

    def convert(rows):
        return [[(r[f] - means[f]) / stds[f] for f in features] for r in rows]

    return convert(train), convert(test), means, stds


def train_logistic(x, y, l2=1.0, lr=0.08, epochs=30000):
    n = len(y)
    d = len(x[0]) if x else 0
    weights = [0.0] * (d + 1)
    weights[0] = logit(sum(y) / len(y))
    for _ in range(epochs):
        grads = [0.0] * (d + 1)
        for xi, yi in zip(x, y):
            p = sigmoid(weights[0] + sum(w * v for w, v in zip(weights[1:], xi)))
            err = p - yi
            grads[0] += err
            for j, v in enumerate(xi, start=1):
                grads[j] += err * v
        grads[0] /= n
        for j in range(1, d + 1):
            grads[j] = grads[j] / n + (l2 / n) * weights[j]
        for j in range(d + 1):
            weights[j] -= lr * grads[j]
    return weights


def predict(weights, x):
    return [sigmoid(weights[0] + sum(w * v for w, v in zip(weights[1:], xi))) for xi in x]


def metrics(y, p):
    eps = 1e-12
    n = len(y)
    brier = sum((pi - yi) ** 2 for yi, pi in zip(y, p)) / n
    log_loss = -sum(
        yi * math.log(max(eps, min(1 - eps, pi)))
        + (1 - yi) * math.log(max(eps, min(1 - eps, 1 - pi)))
        for yi, pi in zip(y, p)
    ) / n
    accuracy = sum((pi >= 0.5) == bool(yi) for yi, pi in zip(y, p)) / n
    return {"brier": brier, "log_loss": log_loss, "accuracy": accuracy}


def calibration(y, p, bins=5):
    rows = []
    for i in range(bins):
        lo, hi = i / bins, (i + 1) / bins
        idx = [j for j, pi in enumerate(p) if lo <= pi < hi or (i == bins - 1 and pi == 1.0)]
        if not idx:
            continue
        avg_pred = sum(p[j] for j in idx) / len(idx)
        actual = sum(y[j] for j in idx) / len(idx)
        rows.append(
            {
                "bucket": f"{lo:.1f}-{hi:.1f}",
                "n": len(idx),
                "avg_pred": avg_pred,
                "actual": actual,
                "gap_actual_minus_pred": actual - avg_pred,
            }
        )
    return rows


def fit_model(train, test, features):
    x_train, x_test, _, _ = standardize(train, test, features)
    y_train = [r["outcome"] for r in train]
    y_test = [r["outcome"] for r in test]
    weights = train_logistic(x_train, y_train)
    pred = predict(weights, x_test)
    return {
        "features": features,
        "weights": weights,
        "test_metrics": metrics(y_test, pred),
        "test_calibration": calibration(y_test, pred),
        "feature_importance": [
            {"feature": f, "standardized_coefficient": c}
            for f, c in sorted(zip(features, weights[1:]), key=lambda x: abs(x[1]), reverse=True)
        ],
    }


def split(rows):
    rows = sorted(rows, key=lambda r: r["timestamp"])
    cut = int(len(rows) * 0.70)
    return rows[:cut], rows[cut:]


def build_datasets(markets, histories, closes):
    datasets = {name: [] for name in SNAPSHOTS}
    for market in markets:
        points = histories.get(market["market_id"]) or []
        for name, seconds_before in SNAPSHOTS.items():
            snap = snapshot_probability(points, market["resolution_timestamp"], seconds_before)
            if not snap:
                continue
            ts, probability = snap
            btc_price = close_at_or_before(closes, ts)
            features = {
                "btc_return_1m": ret(closes, ts, 1),
                "btc_return_5m": ret(closes, ts, 5),
                "btc_return_15m": ret(closes, ts, 15),
                "btc_volatility_15m": realized_vol_15m(closes, ts),
            }
            if btc_price is None or any(v is None for v in features.values()):
                continue
            datasets[name].append(
                {
                    "market_id": market["market_id"],
                    "timestamp": ts,
                    "market_probability": probability,
                    "btc_price": btc_price,
                    "outcome": market["outcome"],
                    **features,
                }
            )
    return datasets


def write_dataset(name, rows):
    path = DATA_DIR / f"polymarket_btc5m_probability_lab_v3_{name}.csv"
    fields = [
        "market_id",
        "timestamp",
        "market_probability",
        "btc_price",
        "btc_return_1m",
        "btc_return_5m",
        "btc_return_15m",
        "btc_volatility_15m",
        "outcome",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def round_obj(obj):
    if isinstance(obj, float):
        return round(obj, 8)
    if isinstance(obj, list):
        return [round_obj(x) for x in obj]
    if isinstance(obj, dict):
        return {k: round_obj(v) for k, v in obj.items()}
    return obj


def evaluate_dataset(rows):
    train, test = split(rows)
    y_test = [r["outcome"] for r in test]
    raw_pred = [r["market_probability"] for r in test]
    model_b = fit_model(train, test, ["market_probability"])
    model_c = fit_model(train, test, BTC_FEATURES)
    model_d = fit_model(train, test, ["market_probability", *BTC_FEATURES])
    raw = {"test_metrics": metrics(y_test, raw_pred), "test_calibration": calibration(y_test, raw_pred)}
    return {
        "sample_size": len(rows),
        "train_size": len(train),
        "test_size": len(test),
        "model_a_raw_market_probability": raw,
        "model_b_market_probability_logistic": model_b,
        "model_c_btc_features_only": model_c,
        "model_d_market_plus_btc_features": model_d,
        "model_d_beats_raw_market_brier": model_d["test_metrics"]["brier"] < raw["test_metrics"]["brier"],
        "model_d_beats_raw_market_log_loss": model_d["test_metrics"]["log_loss"] < raw["test_metrics"]["log_loss"],
        "model_d_beats_market": (
            model_d["test_metrics"]["brier"] < raw["test_metrics"]["brier"]
            and model_d["test_metrics"]["log_loss"] < raw["test_metrics"]["log_loss"]
        ),
    }


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    starts = list(range(START_TS, END_TS, 300))
    print(f"Planned markets: {len(starts)}", flush=True)
    with ThreadPoolExecutor(max_workers=24) as ex:
        markets = [m for m in ex.map(fetch_market, starts) if m]
    print(f"Markets found: {len(markets)}", flush=True)
    with ThreadPoolExecutor(max_workers=24) as ex:
        resolved = [m for m in ex.map(resolve_market, markets) if m]
    resolved.sort(key=lambda m: m["open_timestamp"])
    print(f"Markets resolved: {len(resolved)}", flush=True)
    closes = fetch_binance_klines(START_TS, END_TS)
    print(f"BTC candles: {len(closes)}", flush=True)
    histories = {}
    with ThreadPoolExecutor(max_workers=32) as ex:
        futures = [ex.submit(fetch_market_history, m) for m in resolved]
        for i, future in enumerate(as_completed(futures), 1):
            market_id, points = future.result()
            histories[market_id] = points
            if i % 200 == 0:
                print(f"Histories fetched: {i}", flush=True)
    datasets = build_datasets(resolved, histories, closes)
    results = {
        "window": {
            "start_utc": datetime.fromtimestamp(START_TS, timezone.utc).isoformat(),
            "end_utc": datetime.fromtimestamp(END_TS, timezone.utc).isoformat(),
            "resolved_markets": len(resolved),
        },
        "snapshots": {},
    }
    for name, rows in datasets.items():
        path = write_dataset(name, rows)
        print(f"Training {name}: rows={len(rows)}", flush=True)
        snapshot_result = evaluate_dataset(rows)
        snapshot_result["dataset_path"] = str(path)
        results["snapshots"][name] = snapshot_result
    OUT.write_text(json.dumps(round_obj(results), indent=2), encoding="utf-8")
    print(json.dumps(round_obj(results), indent=2))


if __name__ == "__main__":
    main()
