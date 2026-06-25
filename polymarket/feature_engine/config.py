from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FeatureConfig:
    runs_root: Path = Path("polymarket/runs/v5")
    output_root: Path = Path("polymarket/data/training")
    resolutions_path: Path = Path("polymarket/data/resolutions/resolutions.jsonl")
    allow_proxy_labels: bool = False
    feature_anchor_seconds: float = 60.0
    boundary_tolerance_seconds: float = 15.0
    early_window_seconds: float = 15.0
    late_window_seconds: float = 60.0
    asof_max_age_seconds: float = 15.0
    max_missing_features_per_row: int = 2

    def __post_init__(self) -> None:
        if self.feature_anchor_seconds < 0:
            raise ValueError("feature_anchor_seconds cannot be negative")
        if self.boundary_tolerance_seconds < 0:
            raise ValueError("boundary_tolerance_seconds cannot be negative")
        if self.asof_max_age_seconds < 0:
            raise ValueError("asof_max_age_seconds cannot be negative")
        if self.max_missing_features_per_row < 0:
            raise ValueError("max_missing_features_per_row cannot be negative")
