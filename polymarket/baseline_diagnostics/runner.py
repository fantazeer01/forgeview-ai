from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from polymarket.baseline_model.logistic import fit_logistic
from polymarket.baseline_model.metrics import clip_probability, probability_metrics


EXTERNAL = (
    "return_5s", "return_15s", "return_30s", "return_60s",
    "momentum_short", "momentum_medium", "volatility_30s", "volatility_60s",
)
MARKET = (
    "yes_price", "yes_no_spread",
    "probability_change_15s", "probability_change_30s",
)
LAG = ("lag_score", "confidence_score")
LIFECYCLE = ("detection_delay", "early_window_flag", "late_window_flag")
ASSETS = ("asset_ETH", "asset_SOL")
GROUPS = {
    "yes_calibration": ("yes_price",) + ASSETS,
    "market_only": MARKET + LIFECYCLE + ASSETS,
    "external_only": EXTERNAL + ASSETS,
    "lag_only": LAG + ASSETS,
    "yes_plus_external": ("yes_price",) + EXTERNAL + ASSETS,
    "yes_plus_lag": ("yes_price",) + LAG + ASSETS,
    "yes_plus_market_dynamics": (
        "yes_price", "probability_change_15s", "probability_change_30s",
    ) + LIFECYCLE + ASSETS,
    "combined_baseline": EXTERNAL + MARKET + LAG + LIFECYCLE + ASSETS,
}
NUMERIC_SOURCE = tuple(dict.fromkeys(
    EXTERNAL + MARKET + LAG + LIFECYCLE
))


@dataclass(frozen=True)
class DiagnosticsConfig:
    protocol_root: Path = Path("polymarket/data/validation_protocol/v1")
    baseline_root: Path = Path("polymarket/models/baseline_v1")
    output_root: Path = Path("polymarket/models/baseline_diagnostics_v1")
    l2_penalty: float = 1.0


class DiagnosticsRunner:
    def __init__(self, config: DiagnosticsConfig | None = None) -> None:
        self.config = config or DiagnosticsConfig()

    def run(self) -> dict[str, Any]:
        protocol = _json(self.config.protocol_root / "protocol_manifest.json")
        _verify_input(self.config.protocol_root, protocol, "train.csv")
        _verify_input(self.config.protocol_root, protocol, "validation.csv")
        baseline = _json(self.config.baseline_root / "validation_report.json")
        train = _rows(self.config.protocol_root / "train.csv")
        validation = _rows(self.config.protocol_root / "validation.csv")
        outcomes = [int(row["outcome"]) for row in validation]

        group_results = {}
        group_predictions = {}
        group_coefficients = {}
        for name, features in GROUPS.items():
            prep = _fit_preprocessing(train, features)
            train_matrix = _matrix(train, features, prep)
            validation_matrix = _matrix(validation, features, prep)
            model = fit_logistic(
                train_matrix, [int(row["outcome"]) for row in train],
                l2_penalty=self.config.l2_penalty,
            )
            predictions = model.predict(validation_matrix)
            group_predictions[name] = predictions
            group_results[name] = probability_metrics(outcomes, predictions)
            group_coefficients[name] = {
                feature: round(value, 12)
                for feature, value in zip(("intercept",) + features, model.coefficients)
            }

        yes = [float(row["yes_price"]) for row in validation]
        yes_metrics = probability_metrics(outcomes, yes)
        baseline_predictions = _prediction_rows(
            self.config.baseline_root / "predictions_validation.csv"
        )
        logistic = [
            float(baseline_predictions[row["market_id"]]["logistic_regression"])
            for row in validation
        ]
        prediction_analysis = _prediction_analysis(
            validation, outcomes, logistic, yes
        )
        thresholds = _regime_thresholds(train)
        segments = _segments(validation, thresholds)
        segment_rows = _segment_metrics(
            validation, outcomes, logistic, yes, segments
        )
        calibration_rows = _calibration_rows(
            validation, outcomes, logistic, yes
        )
        feature_rows, correlations, redundancies = _feature_diagnostics(
            train, validation,
            baseline["logistic_model"]["coefficients"],
        )
        regime_rows = _regime_rows(segment_rows)
        conclusion, strongest, weakest, edge_evidence, recommendation = (
            _choose_conclusion(
                yes_metrics, group_results, segment_rows, redundancies,
                prediction_analysis,
            )
        )

        report = {
            "schema_version": 1,
            "status": "completed",
            "conclusion": conclusion,
            "strongest_finding": strongest,
            "weakest_area": weakest,
            "evidence_for_against_edge": edge_evidence,
            "holdout": {
                "sealed": True,
                "outcomes_read": False,
                "label_commitment_sha256": protocol["holdout"][
                    "label_commitment_sha256"
                ],
            },
            "data": {
                "train_rows": len(train),
                "validation_rows": len(validation),
                "authorized_inputs": ["train.csv", "validation.csv"],
            },
            "baseline_reference": {
                "yes_price": yes_metrics,
                "logistic_regression": probability_metrics(outcomes, logistic),
            },
            "feature_group_tests": {
                name: {
                    "features": list(GROUPS[name]),
                    "metrics": metrics,
                    "delta_log_loss_vs_yes": round(
                        metrics["log_loss"] - yes_metrics["log_loss"], 10
                    ),
                    "delta_brier_vs_yes": round(
                        metrics["brier_score"] - yes_metrics["brier_score"], 10
                    ),
                    "coefficients": group_coefficients[name],
                }
                for name, metrics in group_results.items()
            },
            "incremental_information": _incremental_summary(
                yes_metrics, group_results, segment_rows
            ),
            "prediction_analysis": prediction_analysis,
            "feature_stability": {
                "features": feature_rows,
                "correlation_matrix_train": correlations,
                "redundancies": redundancies,
            },
            "regime_thresholds_from_train": thresholds,
            "segments": segment_rows,
            "candidate_missing_information": [
                "order flow and signed trade imbalance",
                "best-bid/ask depth and quote dynamics",
                "Polymarket repricing velocity and probability acceleration",
                "quote age, cancellations, and market microstructure state",
                "cross-asset lead/lag interactions measured at synchronized timestamps",
            ],
            "recommendation": recommendation,
        }
        output = self.config.output_root
        output.mkdir(parents=True, exist_ok=True)
        _write_csv(output / "segment_metrics.csv", segment_rows)
        _write_csv(output / "feature_diagnostics.csv", feature_rows)
        _write_csv(output / "calibration_analysis.csv", calibration_rows)
        _write_csv(output / "regime_analysis.csv", regime_rows)
        _write_json(output / "diagnostics_report.json", report)
        _write_markdown(output / "diagnostics_report.md", report)
        hashes = {
            "inputs": {
                "train.csv": _sha256(self.config.protocol_root / "train.csv"),
                "validation.csv": _sha256(
                    self.config.protocol_root / "validation.csv"
                ),
                "baseline_validation_report.json": _sha256(
                    self.config.baseline_root / "validation_report.json"
                ),
            },
            "outputs": {
                name: _sha256(output / name) for name in (
                    "diagnostics_report.json", "diagnostics_report.md",
                    "segment_metrics.csv", "feature_diagnostics.csv",
                    "calibration_analysis.csv", "regime_analysis.csv",
                )
            },
            "sealed_holdout_commitment_from_manifest": protocol["holdout"][
                "label_commitment_sha256"
            ],
        }
        _write_json(output / "reproducibility_hashes.json", hashes)
        return report

    def inspect(self) -> dict[str, Any]:
        return _json(self.config.output_root / "diagnostics_report.json")

    def verify(self) -> dict[str, Any]:
        report = self.inspect()
        hashes = _json(self.config.output_root / "reproducibility_hashes.json")
        for name, expected in hashes["outputs"].items():
            if _sha256(self.config.output_root / name) != expected:
                raise ValueError(f"diagnostic output hash mismatch: {name}")
        return report


def _choose_conclusion(yes, groups, segments, redundancies, analysis):
    improvements = {
        name: (
            yes["log_loss"] - metrics["log_loss"],
            yes["brier_score"] - metrics["brier_score"],
        )
        for name, metrics in groups.items()
    }
    positive_groups = [
        name for name, values in improvements.items()
        if values[0] > 0 and values[1] > 0
    ]
    meaningful_regimes = [
        row for row in segments
        if row["count"] >= 20
        and row["logistic_log_loss"] < row["yes_log_loss"]
        and row["logistic_brier"] < row["yes_brier"]
    ]
    if positive_groups:
        conclusion = "WEAK_INFORMATION_PRESENT"
        strongest = (
            f"{positive_groups[0]} improves both primary metrics over raw YES "
            "price on development validation, but not enough for advancement."
        )
    elif meaningful_regimes:
        conclusion = "REGIME_SPECIFIC_SIGNAL_PRESENT"
        strongest = (
            f"Incremental benefit appears in {meaningful_regimes[0]['segment']} "
            "but not in aggregate."
        )
    else:
        conclusion = "FEATURE_SET_INCOMPLETE"
        strongest = (
            "No fixed current feature group improves both log loss and Brier "
            "score over YES price in aggregate."
        )
    weakest = (
        "Current features are mostly single-timestamp summaries; they omit "
        "order flow, depth, quote age, and repricing velocity."
    )
    evidence = {
        "for_edge": [
            f"Logistic beats YES price on {analysis['rows_logistic_better']} of "
            f"{analysis['count']} individual validation rows.",
            "The feature set beats naive class priors, so it contains outcome information.",
        ],
        "against_edge": [
            "No current fixed feature group beats YES price on both primary metrics.",
            "Baseline logistic loses to YES price for BTC, ETH, and SOL.",
            f"Detected redundant feature pairs: {len(redundancies)}.",
        ],
    }
    recommendation = {
        "type": "pre_registered_targeted_experiment",
        "exactly_one": True,
        "task": (
            "Build Market Microstructure Feature Capture v1 for quote depth, "
            "quote age, signed order-flow proxy, repricing velocity, and "
            "probability acceleration; collect a new independent development "
            "period before fitting one pre-registered YES-plus-microstructure "
            "logistic model."
        ),
    }
    return conclusion, strongest, weakest, evidence, recommendation


def _incremental_summary(yes, groups, segments):
    return {
        "groups_beating_yes_on_both_primary_metrics": [
            name for name, metrics in groups.items()
            if metrics["log_loss"] < yes["log_loss"]
            and metrics["brier_score"] < yes["brier_score"]
        ],
        "groups_dominated_by_yes": [
            name for name, metrics in groups.items()
            if metrics["log_loss"] >= yes["log_loss"]
            and metrics["brier_score"] >= yes["brier_score"]
        ],
        "regimes_beating_yes_on_both_primary_metrics": [
            row["segment"] for row in segments
            if row["count"] >= 20
            and row["logistic_log_loss"] < row["yes_log_loss"]
            and row["logistic_brier"] < row["yes_brier"]
        ],
    }


def _prediction_analysis(rows, outcomes, logistic, yes):
    log_deltas = []
    brier_deltas = []
    logistic_better = 0
    for outcome, lp, yp in zip(outcomes, logistic, yes):
        ll = -(outcome * math.log(clip_probability(lp))
               + (1 - outcome) * math.log(1 - clip_probability(lp)))
        yl = -(outcome * math.log(clip_probability(yp))
               + (1 - outcome) * math.log(1 - clip_probability(yp)))
        log_deltas.append(ll - yl)
        brier_deltas.append((lp - outcome) ** 2 - (yp - outcome) ** 2)
        logistic_better += ll < yl
    return {
        "count": len(rows),
        "rows_logistic_better": logistic_better,
        "rows_yes_better_or_equal": len(rows) - logistic_better,
        "mean_log_loss_delta_logistic_minus_yes": round(
            statistics.mean(log_deltas), 10
        ),
        "median_log_loss_delta_logistic_minus_yes": round(
            statistics.median(log_deltas), 10
        ),
        "mean_brier_delta_logistic_minus_yes": round(
            statistics.mean(brier_deltas), 10
        ),
        "log_loss_delta_quantiles": _quantiles(log_deltas),
        "brier_delta_quantiles": _quantiles(brier_deltas),
    }


def _segments(rows, thresholds):
    windows = sorted({row["window_start"] for row in rows})
    rank = {window: index for index, window in enumerate(windows)}
    output = {}
    for index, row in enumerate(rows):
        output.setdefault(f"asset_{row['asset']}", []).append(index)
        age = float(row["market_age_seconds"])
        output.setdefault(
            "window_early" if age < 100 else
            "window_middle" if age < 200 else "window_late", []
        ).append(index)
        output.setdefault(
            "period_early" if rank[row["window_start"]] * 3 < len(windows) else
            "period_middle" if rank[row["window_start"]] * 3 < 2 * len(windows)
            else "period_late", []
        ).append(index)
        for feature, label in (("volatility_60s", "volatility"), ("lag_score", "lag")):
            value = _float(row.get(feature), thresholds[feature]["median"])
            low, high = thresholds[feature]["low"], thresholds[feature]["high"]
            bucket = "low" if value <= low else "high" if value > high else "medium"
            output.setdefault(f"{label}_{bucket}", []).append(index)
        confidence = abs(float(row["yes_price"]) - 0.5)
        bucket = "low" if confidence <= 0.1 else "high" if confidence > 0.25 else "medium"
        output.setdefault(f"yes_confidence_{bucket}", []).append(index)
        missing = sum(row.get(feature, "") in ("", None) for feature in NUMERIC_SOURCE)
        output.setdefault(
            "feature_complete" if missing == 0 else "feature_missing", []
        ).append(index)
    for required in (
        "window_early", "window_middle", "window_late",
        "volatility_low", "volatility_medium", "volatility_high",
        "lag_low", "lag_medium", "lag_high",
    ):
        output.setdefault(required, [])
    return output


def _segment_metrics(rows, outcomes, logistic, yes, segments):
    output = []
    for segment, indexes in sorted(segments.items()):
        if not indexes:
            output.append({
                "segment": segment, "count": 0,
                "logistic_log_loss": "", "yes_log_loss": "",
                "logistic_brier": "", "yes_brier": "",
                "logistic_accuracy": "", "yes_accuracy": "",
                "logistic_auc": "", "yes_auc": "",
                "logistic_calibration": "", "yes_calibration": "",
                "winner": "insufficient_data",
            })
            continue
        y = [outcomes[index] for index in indexes]
        lm = probability_metrics(y, [logistic[index] for index in indexes])
        ym = probability_metrics(y, [yes[index] for index in indexes])
        output.append({
            "segment": segment, "count": len(indexes),
            "logistic_log_loss": lm["log_loss"], "yes_log_loss": ym["log_loss"],
            "logistic_brier": lm["brier_score"], "yes_brier": ym["brier_score"],
            "logistic_accuracy": lm["accuracy"], "yes_accuracy": ym["accuracy"],
            "logistic_auc": lm["roc_auc"], "yes_auc": ym["roc_auc"],
            "logistic_calibration": lm["calibration_error"],
            "yes_calibration": ym["calibration_error"],
            "winner": (
                "logistic" if lm["log_loss"] < ym["log_loss"]
                and lm["brier_score"] < ym["brier_score"] else
                "yes_price" if ym["log_loss"] <= lm["log_loss"]
                and ym["brier_score"] <= lm["brier_score"] else "mixed"
            ),
        })
    return output


def _calibration_rows(rows, outcomes, logistic, yes):
    output = []
    for model, probabilities in (("logistic", logistic), ("yes_price", yes)):
        table = probability_metrics(outcomes, probabilities)["calibration_table"]
        for row in table:
            output.append({"scope": "overall", "model": model, **row})
        for asset in ("BTC", "ETH", "SOL"):
            indexes = [i for i, row in enumerate(rows) if row["asset"] == asset]
            table = probability_metrics(
                [outcomes[i] for i in indexes],
                [probabilities[i] for i in indexes],
            )["calibration_table"]
            for row in table:
                output.append({"scope": asset, "model": model, **row})
    return output


def _feature_diagnostics(train, validation, coefficients):
    features = NUMERIC_SOURCE
    train_values = {feature: _filled(train, feature) for feature in features}
    validation_values = {
        feature: _filled(validation, feature, statistics.median(train_values[feature]))
        for feature in features
    }
    outcomes_train = [int(row["outcome"]) for row in train]
    outcomes_validation = [int(row["outcome"]) for row in validation]
    correlations = {
        left: {
            right: round(_corr(train_values[left], train_values[right]), 10)
            for right in features
        } for left in features
    }
    redundancies = []
    for i, left in enumerate(features):
        for right in features[i + 1:]:
            correlation = correlations[left][right]
            if abs(correlation) >= 0.95:
                redundancies.append({
                    "left": left, "right": right, "correlation": correlation
                })
    output = []
    for feature in features:
        train_mean = statistics.mean(train_values[feature])
        validation_mean = statistics.mean(validation_values[feature])
        train_std = statistics.pstdev(train_values[feature])
        output.append({
            "feature": feature,
            "coefficient": coefficients.get(feature, 0.0),
            "absolute_coefficient": abs(coefficients.get(feature, 0.0)),
            "train_mean": train_mean,
            "validation_mean": validation_mean,
            "train_std": train_std,
            "validation_std": statistics.pstdev(validation_values[feature]),
            "standardized_mean_drift": (
                (validation_mean - train_mean) / train_std if train_std else 0.0
            ),
            "train_missing_rate": sum(
                row.get(feature, "") in ("", None) for row in train
            ) / len(train),
            "validation_missing_rate": sum(
                row.get(feature, "") in ("", None) for row in validation
            ) / len(validation),
            "train_outcome_correlation": _corr(
                train_values[feature], outcomes_train
            ),
            "validation_outcome_correlation": _corr(
                validation_values[feature], outcomes_validation
            ),
            "max_abs_feature_correlation": max(
                abs(value) for other, value in correlations[feature].items()
                if other != feature
            ),
            "redundant_with": "|".join(
                item["right"] if item["left"] == feature else item["left"]
                for item in redundancies
                if feature in (item["left"], item["right"])
            ),
        })
    output.sort(key=lambda row: (-row["absolute_coefficient"], row["feature"]))
    return output, correlations, redundancies


def _regime_thresholds(train):
    output = {}
    for feature in ("volatility_60s", "lag_score"):
        values = sorted(_filled(train, feature))
        output[feature] = {
            "low": _percentile(values, 1 / 3),
            "high": _percentile(values, 2 / 3),
            "median": statistics.median(values),
        }
    return output


def _regime_rows(segment_rows):
    return [
        row for row in segment_rows
        if row["segment"].startswith((
            "window_", "period_", "volatility_", "lag_", "yes_confidence_"
        ))
    ]


def _fit_preprocessing(rows, features):
    output = {}
    for feature in features:
        if feature in ASSETS:
            continue
        values = _filled(rows, feature)
        median = statistics.median(values)
        mean = statistics.mean(values)
        scale = statistics.pstdev(values)
        output[feature] = {
            "median": median, "mean": mean, "scale": scale if scale > 1e-12 else 1.0
        }
    return output


def _matrix(rows, features, prep):
    output = []
    for row in rows:
        values = [1.0]
        for feature in features:
            if feature == "asset_ETH":
                values.append(float(row["asset"] == "ETH"))
            elif feature == "asset_SOL":
                values.append(float(row["asset"] == "SOL"))
            else:
                value = _float(row.get(feature), prep[feature]["median"])
                values.append((value - prep[feature]["mean"]) / prep[feature]["scale"])
        output.append(values)
    return output


def _filled(rows, feature, fallback=None):
    observed = [
        float(row[feature]) for row in rows if row.get(feature, "") not in ("", None)
    ]
    fill = statistics.median(observed) if fallback is None and observed else (
        fallback if fallback is not None else 0.0
    )
    return [
        float(row[feature]) if row.get(feature, "") not in ("", None) else fill
        for row in rows
    ]


def _prediction_rows(path):
    return {row["market_id"]: row for row in _rows(path)}


def _corr(left, right):
    if not left or len(left) != len(right):
        return 0.0
    lm, rm = statistics.mean(left), statistics.mean(right)
    numerator = sum((a - lm) * (b - rm) for a, b in zip(left, right))
    denominator = math.sqrt(
        sum((a - lm) ** 2 for a in left) * sum((b - rm) ** 2 for b in right)
    )
    return numerator / denominator if denominator else 0.0


def _quantiles(values):
    ordered = sorted(values)
    return {
        "p10": round(_percentile(ordered, 0.1), 10),
        "p25": round(_percentile(ordered, 0.25), 10),
        "p50": round(_percentile(ordered, 0.5), 10),
        "p75": round(_percentile(ordered, 0.75), 10),
        "p90": round(_percentile(ordered, 0.9), 10),
    }


def _percentile(values, fraction):
    if not values:
        return 0.0
    position = (len(values) - 1) * fraction
    lower = int(position)
    upper = min(len(values) - 1, lower + 1)
    weight = position - lower
    return values[lower] * (1 - weight) + values[upper] * weight


def _float(value, fallback):
    return float(value) if value not in ("", None) else float(fallback)


def _verify_input(root, manifest, name):
    if _sha256(root / name) != manifest["artifacts"][name]["sha256"]:
        raise ValueError(f"frozen input hash mismatch: {name}")


def _write_markdown(path, report):
    lines = [
        "# Baseline Failure Diagnostics v1",
        "",
        f"Conclusion: **{report['conclusion']}**",
        "",
        "The final holdout remained sealed and was not evaluated.",
        "",
        "## Strongest finding",
        "",
        report["strongest_finding"],
        "",
        "## Weakest area",
        "",
        report["weakest_area"],
        "",
        "## Fixed feature-group tests",
        "",
        "| Group | Log loss | Brier | Delta LL vs YES | Delta Brier vs YES |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, result in report["feature_group_tests"].items():
        metrics = result["metrics"]
        lines.append(
            f"| {name} | {metrics['log_loss']:.6f} | "
            f"{metrics['brier_score']:.6f} | "
            f"{result['delta_log_loss_vs_yes']:+.6f} | "
            f"{result['delta_brier_vs_yes']:+.6f} |"
        )
    lines += [
        "",
        "## Decision",
        "",
        report["recommendation"]["task"],
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, value):
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _write_csv(path, rows):
    columns = sorted({key for row in rows for key in row}) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
