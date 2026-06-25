import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "polymarket_btc5m_probability_lab_v1.csv"
OUT = ROOT / "data" / "polymarket_btc5m_probability_lab_v2_model_results.json"

BTC_FEATURES = [
    "btc_return_1m",
    "btc_return_5m",
    "btc_return_15m",
    "btc_volatility_15m",
]


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


def read_rows():
    with DATA.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = []
    for row in rows:
        out.append(
            {
                "market_id": row["market_id"],
                "timestamp": int(row["timestamp"]),
                "outcome": int(row["outcome"]),
                "market_probability": float(row["market_probability"]),
                **{k: float(row[k]) for k in BTC_FEATURES},
            }
        )
    return sorted(out, key=lambda r: r["timestamp"])


def split_chronological(rows, train_frac=0.70):
    cut = int(len(rows) * train_frac)
    return rows[:cut], rows[cut:]


def standardize(train, test, features):
    means = {}
    stds = {}
    for feature in features:
        vals = [r[feature] for r in train]
        mean = sum(vals) / len(vals)
        var = sum((x - mean) ** 2 for x in vals) / len(vals)
        std = math.sqrt(var) or 1.0
        means[feature] = mean
        stds[feature] = std

    def convert(rows):
        return [[(r[f] - means[f]) / stds[f] for f in features] for r in rows]

    return convert(train), convert(test), means, stds


def train_logistic(x, y, l2=1.0, lr=0.08, epochs=30000):
    n = len(y)
    d = len(x[0]) if x else 0
    weights = [0.0] * (d + 1)
    # Initialize intercept at base-rate logit.
    base = sum(y) / len(y)
    weights[0] = logit(base)

    for _ in range(epochs):
        grads = [0.0] * (d + 1)
        for xi, yi in zip(x, y):
            z = weights[0] + sum(w * v for w, v in zip(weights[1:], xi))
            p = sigmoid(z)
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
    acc = sum((pi >= 0.5) == bool(yi) for yi, pi in zip(y, p)) / n
    return {"brier": brier, "log_loss": log_loss, "accuracy": acc}


def calibration(y, p, bins=5):
    rows = []
    for i in range(bins):
        lo = i / bins
        hi = (i + 1) / bins
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
    x_train, x_test, means, stds = standardize(train, test, features)
    y_train = [r["outcome"] for r in train]
    y_test = [r["outcome"] for r in test]
    weights = train_logistic(x_train, y_train)
    pred_train = predict(weights, x_train)
    pred_test = predict(weights, x_test)
    return {
        "features": features,
        "weights": weights,
        "means": means,
        "stds": stds,
        "train_metrics": metrics(y_train, pred_train),
        "test_metrics": metrics(y_test, pred_test),
        "test_calibration": calibration(y_test, pred_test),
        "test_predictions": pred_test,
    }


def feature_importance(model):
    return [
        {"feature": feature, "standardized_coefficient": coef}
        for feature, coef in sorted(
            zip(model["features"], model["weights"][1:]),
            key=lambda x: abs(x[1]),
            reverse=True,
        )
    ]


def round_obj(obj):
    if isinstance(obj, float):
        return round(obj, 8)
    if isinstance(obj, list):
        return [round_obj(x) for x in obj]
    if isinstance(obj, dict):
        return {k: round_obj(v) for k, v in obj.items() if k != "test_predictions"}
    return obj


def main():
    rows = read_rows()
    train, test = split_chronological(rows)
    y_test = [r["outcome"] for r in test]

    model_a = fit_model(train, test, ["market_probability"])
    model_b = fit_model(train, test, BTC_FEATURES)
    model_c = fit_model(train, test, ["market_probability", *BTC_FEATURES])

    raw_market_pred = [r["market_probability"] for r in test]
    raw_market_metrics = metrics(y_test, raw_market_pred)
    raw_market_calibration = calibration(y_test, raw_market_pred)

    result = {
        "dataset": str(DATA),
        "rows": len(rows),
        "train_size": len(train),
        "test_size": len(test),
        "split": "chronological_70_30",
        "train_range": [train[0]["timestamp"], train[-1]["timestamp"]],
        "test_range": [test[0]["timestamp"], test[-1]["timestamp"]],
        "raw_market_probability_baseline": {
            "test_metrics": raw_market_metrics,
            "test_calibration": raw_market_calibration,
        },
        "model_a_market_probability_only": model_a,
        "model_b_btc_features_only": model_b,
        "model_c_market_plus_btc_features": model_c,
        "feature_importance": {
            "model_a": feature_importance(model_a),
            "model_b": feature_importance(model_b),
            "model_c": feature_importance(model_c),
        },
        "model_c_beats_model_a_by_brier": model_c["test_metrics"]["brier"] < model_a["test_metrics"]["brier"],
        "model_c_beats_raw_market_by_brier": model_c["test_metrics"]["brier"] < raw_market_metrics["brier"],
        "model_c_beats_model_a_by_log_loss": model_c["test_metrics"]["log_loss"] < model_a["test_metrics"]["log_loss"],
        "model_c_beats_raw_market_by_log_loss": model_c["test_metrics"]["log_loss"] < raw_market_metrics["log_loss"],
    }
    OUT.write_text(json.dumps(round_obj(result), indent=2), encoding="utf-8")
    print(json.dumps(round_obj(result), indent=2))


if __name__ == "__main__":
    main()
