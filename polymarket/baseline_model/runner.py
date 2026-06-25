from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .logistic import LogisticModel, fit_logistic
from .metrics import clip_probability, probability_metrics


NUMERIC_FEATURES = (
    "return_5s", "return_15s", "return_30s", "return_60s",
    "momentum_short", "momentum_medium",
    "volatility_30s", "volatility_60s",
    "yes_price", "yes_no_spread",
    "probability_change_15s", "probability_change_30s",
    "lag_score", "confidence_score",
    "detection_delay", "early_window_flag", "late_window_flag",
)
ASSET_FEATURES = ("asset_ETH", "asset_SOL")
MODEL_FEATURES = ("intercept",) + NUMERIC_FEATURES + ASSET_FEATURES
MODEL_NAMES = (
    "constant_prior", "asset_prior", "yes_price", "logistic_regression",
)


@dataclass(frozen=True)
class BaselineConfig:
    protocol_root: Path = Path("polymarket/data/validation_protocol/v1")
    output_root: Path = Path("polymarket/models/baseline_v1")
    l2_penalty: float = 1.0
    max_iterations: int = 100
    tolerance: float = 1e-9
    calibration_bins: int = 10


class BaselineRunner:
    def __init__(self, config: BaselineConfig | None = None) -> None:
        self.config = config or BaselineConfig()

    def run(self) -> dict[str, Any]:
        manifest = _read_json(self.config.protocol_root / "protocol_manifest.json")
        _verify_authorized_inputs(self.config.protocol_root, manifest)
        train = _read_rows(self.config.protocol_root / "train.csv")
        validation = _read_rows(self.config.protocol_root / "validation.csv")
        _validate_rows(train, validation)

        preprocessing = _fit_preprocessing(train)
        train_matrix = _matrix(train, preprocessing)
        validation_matrix = _matrix(validation, preprocessing)
        train_outcomes = [_outcome(row) for row in train]
        validation_outcomes = [_outcome(row) for row in validation]
        logistic = fit_logistic(
            train_matrix,
            train_outcomes,
            l2_penalty=self.config.l2_penalty,
            max_iterations=self.config.max_iterations,
            tolerance=self.config.tolerance,
        )
        prior = sum(train_outcomes) / len(train_outcomes)
        asset_priors = _asset_priors(train, prior)
        predictions = {
            "train": _predictions(
                train, logistic, train_matrix, prior, asset_priors
            ),
            "validation": _predictions(
                validation, logistic, validation_matrix, prior, asset_priors
            ),
        }
        metrics = {
            split: _evaluate(rows, values)
            for split, rows, values in (
                ("train", train, predictions["train"]),
                ("validation", validation, predictions["validation"]),
            )
        }
        gap = {
            model: {
                metric: round(
                    metrics["validation"]["overall"][model][metric]
                    - metrics["train"]["overall"][model][metric],
                    10,
                )
                for metric in ("log_loss", "brier_score", "accuracy")
            }
            for model in MODEL_NAMES
        }
        advancement = _advancement(metrics["validation"])
        verdict = (
            "ADVANCE_CANDIDATE"
            if advancement["passes"]
            else "NO_EDGE_FOUND_YET"
        )
        best = min(
            MODEL_NAMES,
            key=lambda name: (
                metrics["validation"]["overall"][name]["log_loss"],
                metrics["validation"]["overall"][name]["brier_score"],
                name,
            ),
        )
        output = self.config.output_root
        output.mkdir(parents=True, exist_ok=True)
        _write_predictions(
            output / "predictions_validation.csv",
            validation,
            predictions["validation"],
        )
        _write_feature_importance(
            output / "feature_importance.csv", logistic
        )
        training_config = {
            "protocol_id": manifest["protocol_id"],
            "authorized_inputs": ["train.csv", "validation.csv", "protocol_manifest.json"],
            "prohibited_input": "sealed holdout labels",
            "numeric_features": list(NUMERIC_FEATURES),
            "asset_features": list(ASSET_FEATURES),
            "missing_value_policy": "training median",
            "scaling_policy": "training mean and population standard deviation",
            "logistic_l2_penalty": self.config.l2_penalty,
            "logistic_max_iterations": self.config.max_iterations,
            "logistic_tolerance": self.config.tolerance,
            "threshold": 0.5,
            "model_search": "none",
            "optional_tree_model": "not evaluated; dependency-free fixed baseline scope",
        }
        _write_json(output / "training_config.json", training_config)
        report = {
            "schema_version": 1,
            "status": "completed",
            "verdict": verdict,
            "best_model": best,
            "data": {
                "train_rows": len(train),
                "validation_rows": len(validation),
                "train_first_window": train[0]["window_start"],
                "train_last_window": train[-1]["window_start"],
                "validation_first_window": validation[0]["window_start"],
                "validation_last_window": validation[-1]["window_start"],
            },
            "holdout": {
                "sealed": True,
                "outcomes_read": False,
                "label_commitment_sha256": manifest["holdout"][
                    "label_commitment_sha256"
                ],
            },
            "models_evaluated": list(MODEL_NAMES),
            "metrics": metrics,
            "train_validation_gap": gap,
            "advancement": advancement,
            "logistic_model": {
                "converged": logistic.converged,
                "iterations": logistic.iterations,
                "coefficients": {
                    name: round(value, 12)
                    for name, value in zip(MODEL_FEATURES, logistic.coefficients)
                },
                "preprocessing": preprocessing,
            },
            "next_research_action": (
                "Freeze the development candidate and its assumptions for a "
                "separately authorized holdout evaluation."
                if advancement["passes"] else
                "Do not open the holdout. Diagnose temporal and per-asset "
                "validation failures, then pre-register one targeted feature "
                "ablation or collect a new independent development period."
            ),
        }
        _write_json(output / "validation_report.json", report)
        _write_markdown(output / "validation_report.md", report)
        _write_model_cards(output, report, training_config)
        hashes = self._hashes(manifest)
        _write_json(output / "reproducibility_hashes.json", hashes)
        return report

    def inspect(self) -> dict[str, Any]:
        return _read_json(self.config.output_root / "validation_report.json")

    def verify(self) -> dict[str, Any]:
        report = self.inspect()
        hashes = _read_json(
            self.config.output_root / "reproducibility_hashes.json"
        )
        manifest = _read_json(self.config.protocol_root / "protocol_manifest.json")
        _verify_authorized_inputs(self.config.protocol_root, manifest)
        for name, expected in hashes["outputs"].items():
            path = self.config.output_root / name
            if _sha256(path) != expected:
                raise ValueError(f"output hash mismatch: {name}")
        if hashes["inputs"]["train.csv"] != _sha256(
            self.config.protocol_root / "train.csv"
        ):
            raise ValueError("train input hash mismatch")
        if hashes["inputs"]["validation.csv"] != _sha256(
            self.config.protocol_root / "validation.csv"
        ):
            raise ValueError("validation input hash mismatch")
        return report

    def _hashes(self, manifest: dict[str, Any]) -> dict[str, Any]:
        output_names = (
            "training_config.json", "validation_report.json",
            "validation_report.md", "predictions_validation.csv",
            "feature_importance.csv", "MODEL_CARD.md",
            "model_cards/constant_prior.md",
            "model_cards/asset_prior.md",
            "model_cards/yes_price.md",
            "model_cards/logistic_regression.md",
        )
        return {
            "inputs": {
                "train.csv": _sha256(self.config.protocol_root / "train.csv"),
                "validation.csv": _sha256(
                    self.config.protocol_root / "validation.csv"
                ),
                "protocol_manifest.json": _sha256(
                    self.config.protocol_root / "protocol_manifest.json"
                ),
            },
            "sealed_holdout_commitment_from_manifest": manifest["holdout"][
                "label_commitment_sha256"
            ],
            "outputs": {
                name: _sha256(self.config.output_root / name)
                for name in output_names
            },
        }


def _fit_preprocessing(rows: list[dict[str, str]]) -> dict[str, Any]:
    output = {}
    for feature in NUMERIC_FEATURES:
        values = [
            float(row[feature]) for row in rows
            if row.get(feature, "") not in ("", None)
        ]
        if not values:
            median = mean = 0.0
            scale = 1.0
        else:
            median = statistics.median(values)
            filled = [
                float(row[feature]) if row.get(feature, "") not in ("", None)
                else median for row in rows
            ]
            mean = sum(filled) / len(filled)
            scale = math.sqrt(
                sum((value - mean) ** 2 for value in filled) / len(filled)
            )
            if scale < 1e-12:
                scale = 1.0
        output[feature] = {
            "median": round(median, 15),
            "mean": round(mean, 15),
            "scale": round(scale, 15),
        }
    return output


def _matrix(
    rows: list[dict[str, str]], preprocessing: dict[str, Any]
) -> list[list[float]]:
    matrix = []
    for row in rows:
        values = [1.0]
        for feature in NUMERIC_FEATURES:
            config = preprocessing[feature]
            raw = row.get(feature, "")
            value = float(raw) if raw not in ("", None) else config["median"]
            values.append((value - config["mean"]) / config["scale"])
        values.extend([
            float(row["asset"] == "ETH"),
            float(row["asset"] == "SOL"),
        ])
        matrix.append(values)
    return matrix


def _predictions(rows, logistic, matrix, prior, asset_priors):
    logistic_values = logistic.predict(matrix)
    return [
        {
            "constant_prior": clip_probability(prior),
            "asset_prior": clip_probability(asset_priors[row["asset"]]),
            "yes_price": clip_probability(float(row["yes_price"])),
            "logistic_regression": clip_probability(logistic_value),
        }
        for row, logistic_value in zip(rows, logistic_values)
    ]


def _evaluate(rows, predictions):
    outcomes = [_outcome(row) for row in rows]
    overall = {
        model: probability_metrics(
            outcomes, [row[model] for row in predictions]
        )
        for model in MODEL_NAMES
    }
    by_asset = {}
    for asset in ("BTC", "ETH", "SOL"):
        indexes = [
            index for index, row in enumerate(rows) if row["asset"] == asset
        ]
        by_asset[asset] = {
            model: probability_metrics(
                [outcomes[index] for index in indexes],
                [predictions[index][model] for index in indexes],
            )
            for model in MODEL_NAMES
        }
    period = {}
    windows = sorted({row["window_start"] for row in rows})
    window_rank = {window: index for index, window in enumerate(windows)}
    for bucket in range(3):
        indexes = [
            index for index, row in enumerate(rows)
            if min(2, window_rank[row["window_start"]] * 3 // len(windows))
            == bucket
        ]
        period[f"period_{bucket + 1}"] = {
            "first_window": min(rows[index]["window_start"] for index in indexes),
            "last_window": max(rows[index]["window_start"] for index in indexes),
            "metrics": {
                model: probability_metrics(
                    [outcomes[index] for index in indexes],
                    [predictions[index][model] for index in indexes],
                )
                for model in MODEL_NAMES
            },
        }
    return {"overall": overall, "by_asset": by_asset, "by_period": period}


def _advancement(validation_metrics):
    overall = validation_metrics["overall"]
    candidate = overall["logistic_regression"]
    comparisons = {}
    for baseline in ("constant_prior", "asset_prior", "yes_price"):
        base = overall[baseline]
        comparisons[baseline] = {
            "beats_log_loss": candidate["log_loss"] < base["log_loss"],
            "beats_brier_score": candidate["brier_score"] < base["brier_score"],
            "log_loss_relative_improvement": round(
                (base["log_loss"] - candidate["log_loss"]) / base["log_loss"],
                10,
            ),
            "brier_relative_improvement": round(
                (base["brier_score"] - candidate["brier_score"])
                / base["brier_score"],
                10,
            ),
        }
    beats_all = all(
        row["beats_log_loss"] and row["beats_brier_score"]
        for row in comparisons.values()
    )
    versus_yes = comparisons["yes_price"]
    protocol_metric_rule = (
        max(
            versus_yes["log_loss_relative_improvement"],
            versus_yes["brier_relative_improvement"],
        ) >= 0.01
        and min(
            versus_yes["log_loss_relative_improvement"],
            versus_yes["brier_relative_improvement"],
        ) >= -0.005
    )
    asset_wins = []
    for asset, metrics in validation_metrics["by_asset"].items():
        candidate_asset = metrics["logistic_regression"]
        yes_asset = metrics["yes_price"]
        if (
            candidate_asset["log_loss"] < yes_asset["log_loss"]
            and candidate_asset["brier_score"] < yes_asset["brier_score"]
        ):
            asset_wins.append(asset)
    return {
        "passes": beats_all and protocol_metric_rule and len(asset_wins) >= 2,
        "candidate": "logistic_regression",
        "comparisons": comparisons,
        "beats_all_required_baselines_on_both_primary_metrics": beats_all,
        "protocol_yes_price_improvement_rule": protocol_metric_rule,
        "assets_beating_yes_price_on_both_primary_metrics": asset_wins,
        "minimum_assets_required": 2,
    }


def _asset_priors(rows, fallback):
    output = {}
    for asset in ("BTC", "ETH", "SOL"):
        values = [_outcome(row) for row in rows if row["asset"] == asset]
        output[asset] = sum(values) / len(values) if values else fallback
    return output


def _validate_rows(train, validation):
    if not train or not validation:
        raise ValueError("train and validation rows are required")
    train_ids = {row["market_id"] for row in train}
    validation_ids = {row["market_id"] for row in validation}
    if train_ids & validation_ids:
        raise ValueError("train and validation market IDs overlap")
    if max(row["window_start"] for row in train) >= min(
        row["window_start"] for row in validation
    ):
        raise ValueError("train must end before validation begins")
    for row in train + validation:
        if row["market_source"] != "public":
            raise ValueError("public data required")
        if row["label_source"] != "polymarket_gamma_resolved":
            raise ValueError("authoritative labels required")


def _verify_authorized_inputs(root, manifest):
    for name in ("train.csv", "validation.csv"):
        path = root / name
        expected = manifest["artifacts"][name]["sha256"]
        if _sha256(path) != expected:
            raise ValueError(f"frozen input hash mismatch: {name}")


def _outcome(row):
    return int(row["outcome"])


def _write_predictions(path, rows, predictions):
    columns = (
        "market_id", "asset", "window_start", "outcome",
        "constant_prior", "asset_prior", "yes_price",
        "logistic_regression",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row, values in zip(rows, predictions):
            writer.writerow({
                "market_id": row["market_id"],
                "asset": row["asset"],
                "window_start": row["window_start"],
                "outcome": row["outcome"],
                **{name: f"{values[name]:.12f}" for name in MODEL_NAMES},
            })


def _write_feature_importance(path, model):
    values = list(zip(MODEL_FEATURES, model.coefficients))
    values.sort(key=lambda item: (-abs(item[1]), item[0]))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("feature", "coefficient", "absolute_coefficient"),
            lineterminator="\n",
        )
        writer.writeheader()
        for name, value in values:
            writer.writerow({
                "feature": name,
                "coefficient": f"{value:.12f}",
                "absolute_coefficient": f"{abs(value):.12f}",
            })


def _write_markdown(path, report):
    metrics = report["metrics"]["validation"]["overall"]
    lines = [
        "# Baseline Probability Model v1 - Development Validation",
        "",
        f"Verdict: **{report['verdict']}**",
        f"Best validation model: **{report['best_model']}**",
        "",
        "The final holdout remained sealed and was not evaluated.",
        "",
        "| Model | Log loss | Brier | Accuracy | AUC |",
        "|---|---:|---:|---:|---:|",
    ]
    for model in MODEL_NAMES:
        row = metrics[model]
        lines.append(
            f"| {model} | {row['log_loss']:.6f} | "
            f"{row['brier_score']:.6f} | {row['accuracy']:.4f} | "
            f"{row['roc_auc'] if row['roc_auc'] is not None else 'N/A'} |"
        )
    lines += [
        "",
        "## Advancement",
        "",
        f"Passes frozen rule: **{report['advancement']['passes']}**",
        "",
        "## Next research action",
        "",
        report["next_research_action"],
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_model_cards(output, report, config):
    metrics = report["metrics"]["validation"]["overall"]
    lines = [
        "# Baseline Model Cards",
        "",
        "Scope: development train/validation evaluation only.",
        "Holdout outcomes were not read.",
        "",
    ]
    descriptions = {
        "constant_prior": "Constant probability equal to train UP frequency.",
        "asset_prior": "Per-asset train UP frequency.",
        "yes_price": "Polymarket YES quote at feature time; no fitting.",
        "logistic_regression": (
            "L2-regularized interpretable logistic regression with fixed "
            "features and train-only median/scaling."
        ),
    }
    for model in MODEL_NAMES:
        row = metrics[model]
        lines += [
            f"## {model}",
            "",
            descriptions[model],
            "",
            f"- Validation log loss: {row['log_loss']}",
            f"- Validation Brier score: {row['brier_score']}",
            f"- Validation accuracy: {row['accuracy']}",
            f"- Validation ROC AUC: {row['roc_auc']}",
            "",
        ]
    lines += [
        "## Limitations",
        "",
        "- One fixed development period; no final holdout result.",
        "- No P&L optimization or execution-cost conclusion.",
        "- No alpha or production-readiness claim.",
        "",
    ]
    (output / "MODEL_CARD.md").write_text("\n".join(lines), encoding="utf-8")
    cards = output / "model_cards"
    cards.mkdir(exist_ok=True)
    for model in MODEL_NAMES:
        row = metrics[model]
        card = [
            f"# Model Card: {model}",
            "",
            descriptions[model],
            "",
            "## Authorized scope",
            "",
            "Development train/validation evaluation only. The sealed holdout "
            "was not read.",
            "",
            "## Validation metrics",
            "",
            f"- Log loss: {row['log_loss']}",
            f"- Brier score: {row['brier_score']}",
            f"- Accuracy: {row['accuracy']}",
            f"- ROC AUC: {row['roc_auc']}",
            f"- Calibration error: {row['calibration_error']}",
            "",
            "## Limitations",
            "",
            "- No final holdout evidence.",
            "- No execution-cost or P&L optimization.",
            "- No proven-edge or production-readiness claim.",
            "",
        ]
        (cards / f"{model}.md").write_text(
            "\n".join(card), encoding="utf-8"
        )


def _read_rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, value):
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
