import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT = DATA_DIR / "polymarket_btc5m_probability_lab_v4_trading_simulation.json"

SNAPSHOTS = ["4m", "3m", "2m", "1m", "30s"]
THRESHOLDS = [0.02, 0.05, 0.10, 0.15]
BTC_FEATURES = [
    "btc_return_1m",
    "btc_return_5m",
    "btc_return_15m",
    "btc_volatility_15m",
]
MODEL_D_FEATURES = ["market_probability", *BTC_FEATURES]


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


def read_dataset(snapshot):
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
    return sorted(out, key=lambda x: x["timestamp"])


def split(rows):
    cut = int(len(rows) * 0.70)
    return rows[:cut], rows[cut:]


def standardize(train, test, features):
    means, stds = {}, {}
    for f in features:
        vals = [r[f] for r in train]
        mean = sum(vals) / len(vals)
        std = math.sqrt(sum((x - mean) ** 2 for x in vals) / len(vals)) or 1.0
        means[f] = mean
        stds[f] = std

    def transform(rows):
        return [[(r[f] - means[f]) / stds[f] for f in features] for r in rows]

    return transform(train), transform(test)


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


def execution_price(contract_probability, mode):
    if mode == "base":
        return min(0.99, contract_probability + 0.01 + 0.05 * contract_probability)
    if mode == "stress":
        return min(0.99, contract_probability + 0.02 + 0.10 * contract_probability)
    return contract_probability


def max_drawdown(pnls):
    equity = 0.0
    peak = 0.0
    mdd = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        mdd = min(mdd, equity - peak)
    return mdd


def simulate(test_rows, model_probs, threshold):
    trades = []
    for row, model_p in zip(test_rows, model_probs):
        market_p = row["market_probability"]
        edge_up = model_p - market_p
        edge_down = market_p - model_p
        if edge_up >= threshold:
            side = "UP"
            contract_probability = market_p
            win = row["outcome"] == 1
        elif edge_down >= threshold:
            side = "DOWN"
            contract_probability = 1 - market_p
            win = row["outcome"] == 0
        else:
            continue
        base_cost = execution_price(contract_probability, "base")
        stress_cost = execution_price(contract_probability, "stress")
        gross_cost = contract_probability
        payout = 1.0 if win else 0.0
        trades.append(
            {
                "timestamp": row["timestamp"],
                "market_id": row["market_id"],
                "side": side,
                "win": win,
                "contract_probability": contract_probability,
                "model_probability_up": model_p,
                "market_probability_up": market_p,
                "gross_pnl": payout - gross_cost,
                "base_pnl": payout - base_cost,
                "stress_pnl": payout - stress_cost,
                "gross_cost": gross_cost,
                "base_cost": base_cost,
                "stress_cost": stress_cost,
                "payout": payout,
            }
        )
    return trades


def summarize(trades):
    n = len(trades)
    wins = sum(1 for t in trades if t["win"])
    gross_cost = sum(t["gross_cost"] for t in trades)
    base_cost = sum(t["base_cost"] for t in trades)
    stress_cost = sum(t["stress_cost"] for t in trades)
    payout = sum(t["payout"] for t in trades)
    gross_pnl = sum(t["gross_pnl"] for t in trades)
    base_pnl = sum(t["base_pnl"] for t in trades)
    stress_pnl = sum(t["stress_pnl"] for t in trades)
    return {
        "trades": n,
        "winrate": wins / n if n else 0.0,
        "cost_gross": gross_cost,
        "cost_base": base_cost,
        "cost_stress": stress_cost,
        "payout": payout,
        "gross_pnl": gross_pnl,
        "net_pnl_base": base_pnl,
        "net_pnl_stress": stress_pnl,
        "roi_base": base_pnl / base_cost if base_cost else 0.0,
        "roi_stress": stress_pnl / stress_cost if stress_cost else 0.0,
        "max_drawdown_base": max_drawdown([t["base_pnl"] for t in trades]),
        "max_drawdown_stress": max_drawdown([t["stress_pnl"] for t in trades]),
        "up_trades": sum(1 for t in trades if t["side"] == "UP"),
        "down_trades": sum(1 for t in trades if t["side"] == "DOWN"),
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
    results = {}
    best = None
    for snapshot in SNAPSHOTS:
        rows = read_dataset(snapshot)
        train, test = split(rows)
        x_train, x_test = standardize(train, test, MODEL_D_FEATURES)
        y_train = [r["outcome"] for r in train]
        weights = train_logistic(x_train, y_train)
        model_probs = predict(weights, x_test)
        snapshot_results = {}
        for threshold in THRESHOLDS:
            trades = simulate(test, model_probs, threshold)
            summary = summarize(trades)
            key = f"{int(threshold * 100)}pct"
            snapshot_results[key] = summary
            if summary["trades"] > 0:
                candidate = {
                    "snapshot": snapshot,
                    "threshold": key,
                    **summary,
                }
                if best is None or (
                    candidate["roi_base"],
                    candidate["net_pnl_base"],
                    candidate["trades"],
                ) > (
                    best["roi_base"],
                    best["net_pnl_base"],
                    best["trades"],
                ):
                    best = candidate
        results[snapshot] = {
            "test_size": len(test),
            "thresholds": snapshot_results,
        }

    robust = bool(best and best["net_pnl_stress"] > 0 and best["roi_stress"] > 0)
    output = {
        "model": "Model D logistic: market_probability + BTC features",
        "split": "chronological_70_30; simulation uses test split only",
        "unit_size": "1 contract per signal",
        "execution_assumptions": {
            "base": "contract_probability + 1c + 5% of contract_probability",
            "stress": "contract_probability + 2c + 10% of contract_probability",
        },
        "results": results,
        "best_setup_by_base_roi": best,
        "profit_edge_confirmed": bool(best and best["net_pnl_base"] > 0 and best["roi_base"] > 0),
        "robust_under_stress": robust,
    }
    OUT.write_text(json.dumps(round_obj(output), indent=2), encoding="utf-8")
    print(json.dumps(round_obj(output), indent=2))


if __name__ == "__main__":
    main()
