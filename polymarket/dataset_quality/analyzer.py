from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

from polymarket.feature_engine.schema import (
    CORE_FEATURE_COLUMNS, MICROSTRUCTURE_FEATURE_COLUMNS,
)


@dataclass(frozen=True)
class QualityMetrics:
    total_samples: int
    public_samples: int
    mock_samples: int
    asset_counts: dict[str, int]
    up_count: int
    down_count: int
    class_imbalance_percentage: float
    minority_class_percentage: float
    missing_values: int
    missing_values_percentage: float
    feature_completeness_percentage: float
    duplicate_rows: int
    duplicate_rate_percentage: float
    duplicate_market_ids: int
    public_only_sample_count: int
    public_class_balance: dict[str, int]
    dataset_quality_score: float
    score_components: dict[str, float]
    training_recommended: bool
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


class DatasetQualityAnalyzer:
    def __init__(
        self,
        dataset_path: Path = Path("polymarket/data/training/dataset.csv"),
    ) -> None:
        self.dataset_path = dataset_path

    def load_rows(self) -> tuple[list[str], list[dict[str, str]]]:
        if not self.dataset_path.exists():
            raise FileNotFoundError(
                f"Training dataset not found: {self.dataset_path}"
            )
        with self.dataset_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise ValueError("Training dataset has no header")
            rows = list(reader)
            return list(reader.fieldnames), rows

    def analyze(self) -> QualityMetrics:
        columns, rows = self.load_rows()
        total = len(rows)
        public = [row for row in rows if row.get("market_source") == "public"]
        mock = [row for row in rows if row.get("market_source") == "mock"]
        assets = {
            asset: sum(row.get("asset") == asset for row in rows)
            for asset in ("BTC", "ETH", "SOL")
        }
        up = sum(row.get("outcome") == "1" for row in rows)
        down = sum(row.get("outcome") == "0" for row in rows)
        labelled = up + down
        imbalance = abs(up - down) / labelled * 100 if labelled else 100.0
        minority = min(up, down) / labelled * 100 if labelled else 0.0

        quality_columns = [
            column for column in columns
            if column not in MICROSTRUCTURE_FEATURE_COLUMNS
        ]
        missing = sum(
            _missing(row.get(column))
            for row in rows for column in quality_columns
        )
        total_cells = total * len(quality_columns)
        missing_pct = missing / total_cells * 100 if total_cells else 100.0
        available_features = [
            feature for feature in CORE_FEATURE_COLUMNS if feature in columns
        ]
        feature_cells = total * len(available_features)
        missing_features = sum(
            _missing(row.get(feature))
            for row in rows
            for feature in available_features
        )
        completeness = (
            (feature_cells - missing_features) / feature_cells * 100
            if feature_cells else 0.0
        )

        signatures = [tuple(row.get(column, "") for column in columns) for row in rows]
        duplicate_rows = total - len(set(signatures))
        duplicate_rate = duplicate_rows / total * 100 if total else 100.0
        market_ids = [row.get("market_id", "") for row in rows]
        duplicate_market_ids = total - len(set(market_ids)) if total else 0

        public_up = sum(row.get("outcome") == "1" for row in public)
        public_down = sum(row.get("outcome") == "0" for row in public)
        public_ratio = len(public) / total if total else 0.0
        balance_score = min(100.0, minority / 50.0 * 100.0)
        components = {
            "public_sample_ratio": round(public_ratio * 100, 4),
            "class_balance": round(balance_score, 4),
            "missing_value_control": round(max(0.0, 100.0 - missing_pct), 4),
            "duplicate_control": round(max(0.0, 100.0 - duplicate_rate), 4),
            "feature_completeness": round(completeness, 4),
        }
        score = round(
            components["public_sample_ratio"] * 0.30
            + components["class_balance"] * 0.25
            + components["missing_value_control"] * 0.15
            + components["duplicate_control"] * 0.10
            + components["feature_completeness"] * 0.20,
            2,
        )
        failures = []
        if total == 0:
            failures.append("dataset is empty")
        if public_ratio < 0.80:
            failures.append("public sample ratio is below 80%")
        if minority < 30.0:
            failures.append("minority class share is below 30%")
        if completeness < 95.0:
            failures.append("feature completeness is below 95%")
        if duplicate_rate > 1.0:
            failures.append("duplicate rate exceeds 1%")
        if score < 75.0:
            failures.append("quality score is below 75")
        recommended = not failures
        reason = (
            "Dataset meets the v1 training quality gates."
            if recommended
            else "Training not recommended: " + "; ".join(failures) + "."
        )
        return QualityMetrics(
            total_samples=total,
            public_samples=len(public),
            mock_samples=len(mock),
            asset_counts=assets,
            up_count=up,
            down_count=down,
            class_imbalance_percentage=round(imbalance, 4),
            minority_class_percentage=round(minority, 4),
            missing_values=missing,
            missing_values_percentage=round(missing_pct, 4),
            feature_completeness_percentage=round(completeness, 4),
            duplicate_rows=duplicate_rows,
            duplicate_rate_percentage=round(duplicate_rate, 4),
            duplicate_market_ids=duplicate_market_ids,
            public_only_sample_count=len(public),
            public_class_balance={"UP": public_up, "DOWN": public_down},
            dataset_quality_score=score,
            score_components=components,
            training_recommended=recommended,
            reason=reason,
        )


def _missing(value: str | None) -> bool:
    return value is None or not value.strip()
