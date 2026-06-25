import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT = DATA_DIR / "polymarket_btc5m_probability_lab_v5_executable_proxy_validation.json"

SETUPS = {
    "4m": 0.10,
    "3m": 0.15,
    "2m": 0.15,
    "1m": 0.15,
    "30s": 0.15,
}
BTC_FEATURES = ["btc_return_1m", "btc_return_5m", "btc_return_15m", "btc_volatility_15m"]
FEATURES = ["market_probability", *BTC_FEATURES]


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


def read_rows(snapshot):
    path = DATA_DIR / f"polymarket_btc5m_probability_lab_v3_{snapshot}.csv"
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        out.append(
            {
                "market_id": r["market_id"],
                "timestamp": int(r["timestamp"]),
                "outcome": int(r["outcome"]),
                "market_probability": float(r["market_probability"]),
                **{k: float(r[k]) for k in BTC_FEATURES},
            }
        )
    return sorted(out, key=lambda r: r["timestamp"])


def split(rows):
    cut = int(len(rows) * 0.70)
    return rows[:cut], rows[cut:]


def standardize(train, test):
    means, stds = {}, {}
    for f in FEATURES:
        vals = [r[f] for r in train]
        mean = sum(vals) / len(vals)
        std = math.sqrt(sum((x - mean) ** 2 for x in vals) / len(vals)) or 1.0
        means[f] = mean
        stds[f] = std
    return (
        [[(r[f] - means[f]) / stds[f] for f in FEATURES] for r in train],
        [[(r[f] - means[f]) / stds[f] for f in FEATURES] for r in test],
    )


def train_logistic(x, y, l2=1.0, lr=0.08, epochs=30000):
    n = len(y)
    d = len(x[0])
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


def signal_rows(test, probs, threshold):
    rows = []
    for r, model_p in zip(test, probs):
        market_p = r["market_probability"]
        if model_p - market_p >= threshold:
            side = "UP"
            market_contract_p = market_p
            model_contract_p = model_p
            win = r["outcome"] == 1
        elif market_p - model_p >= threshold:
            side = "DOWN"
            market_contract_p = 1 - market_p
            model_contract_p = 1 - model_p
            win = r["outcome"] == 0
        else:
            continue
        edge = max(0.0, model_contract_p - market_contract_p)
        rows.append(
            {
                "side": side,
                "win": win,
                "market_contract_p": market_contract_p,
                "model_contract_p": model_contract_p,
                "edge": edge,
            }
        )
    return rows


def cost_for(row, mode):
    p = row["market_contract_p"]
    if mode == "stress":
        return min(0.99, p + 0.02 + 0.10 * p)
    if mode == "ultra":
        return min(0.99, p + 0.03 + 0.15 * p)
    if mode.startswith("consume_"):
        frac = float(mode.split("_")[1])
        return min(0.99, p + frac * row["edge"])
    raise ValueError(mode)


def max_drawdown(pnls):
    equity = 0.0
    peak = 0.0
    mdd = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        mdd = min(mdd, equity - peak)
    return mdd


def summarize(rows, mode):
    pnls = []
    costs = []
    payout = 0.0
    for r in rows:
        c = cost_for(r, mode)
        p = 1.0 if r["win"] else 0.0
        costs.append(c)
        payout += p
        pnls.append(p - c)
    cost = sum(costs)
    pnl = sum(pnls)
    n = len(rows)
    return {
        "trades": n,
        "winrate": sum(1 for r in rows if r["win"]) / n if n else 0.0,
        "cost": cost,
        "payout": payout,
        "net_pnl": pnl,
        "roi": pnl / cost if cost else 0.0,
        "max_drawdown": max_drawdown(pnls),
        "up_trades": sum(1 for r in rows if r["side"] == "UP"),
        "down_trades": sum(1 for r in rows if r["side"] == "DOWN"),
        "avg_market_contract_p": sum(r["market_contract_p"] for r in rows) / n if n else 0.0,
        "avg_model_contract_p": sum(r["model_contract_p"] for r in rows) / n if n else 0.0,
        "avg_edge": sum(r["edge"] for r in rows) / n if n else 0.0,
    }


def round_obj(obj):
    if isinstance(obj, float):
        return round(obj, 8)
    if isinstance(obj, list):
        return [round_obj(x) for x in obj]
    if isinstance(obj, dict):
        return {k: round_obj(v) for k, v in obj.items()}
    return obj


def main():
    modes = ["stress", "ultra", "consume_0.25", "consume_0.5", "consume_0.75", "consume_1.0"]
    results = {}
    best = None
    for snapshot, threshold in SETUPS.items():
        rows = read_rows(snapshot)
        train, test = split(rows)
        x_train, x_test = standardize(train, test)
        weights = train_logistic(x_train, [r["outcome"] for r in train])
        probs = predict(weights, x_test)
        signals = signal_rows(test, probs, threshold)
        setup = {"threshold": threshold, "test_size": len(test), "signals": len(signals), "modes": {}}
        for mode in modes:
            summary = summarize(signals, mode)
            setup["modes"][mode] = summary
            candidate = {"snapshot": snapshot, "threshold": threshold, "mode": mode, **summary}
            if mode in ("stress", "ultra") and (
                best is None or (candidate["roi"], candidate["net_pnl"]) > (best["roi"], best["net_pnl"])
            ):
                best = candidate
        results[snapshot] = setup

    output = {
        "real_executable_data_available": False,
        "reason": "Public CLOB endpoints expose current order books and prices-history, but not reliable recent historical ask/bid order book snapshots for these resolved June 2026 BTC 5m markets.",
        "setups": results,
        "best_realistic_proxy_setup": best,
        "edge_survives_stress": all(v["modes"]["stress"]["net_pnl"] > 0 for v in results.values()),
        "edge_survives_ultra": all(v["modes"]["ultra"]["net_pnl"] > 0 for v in results.values()),
        "edge_survives_75pct_edge_consumption": all(
            v["modes"]["consume_0.75"]["net_pnl"] > 0 for v in results.values()
        ),
        "edge_survives_100pct_edge_consumption": all(
            v["modes"]["consume_1.0"]["net_pnl"] > 0 for v in results.values()
        ),
    }
    OUT.write_text(json.dumps(round_obj(output), indent=2), encoding="utf-8")
    print(json.dumps(round_obj(output), indent=2))


if __name__ == "__main__":
    main()
