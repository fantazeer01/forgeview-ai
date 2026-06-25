from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from polymarket.edge_engine_v4.config import SUPPORTED_ASSETS


@dataclass(frozen=True)
class CaptureConfig:
    assets: tuple[str, ...] = SUPPORTED_ASSETS
    duration_seconds: float = 3_600.0
    poll_interval_seconds: float = 2.0
    discovery_interval_seconds: float = 30.0
    near_expiry_seconds: float = 30.0
    min_entry_seconds_remaining: float = 60.0
    min_liquidity: float = 500.0
    external_move_threshold_bps: float = 8.0
    repricing_ratio: float = 0.50
    min_confidence: float = 0.65
    min_completed_windows: int = 30
    min_shadow_trades: int = 20
    min_reference_coverage: float = 0.95
    max_data_gap: float = 0.10
    max_drawdown: float = 0.05
    max_edge_decay: float = 0.50
    max_latency_sensitivity: float = 0.50
    output_root: Path = Path("polymarket/runs/v5")
    mock: bool = False
    allow_mock_fallback: bool = True
    lifecycle_only: bool = False
    request_timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        invalid = set(self.assets) - set(SUPPORTED_ASSETS)
        if invalid:
            raise ValueError(f"Unsupported assets: {sorted(invalid)}")
        if self.duration_seconds <= 0 or self.poll_interval_seconds <= 0:
            raise ValueError("Duration and poll interval must be positive")
        if self.discovery_interval_seconds <= 0:
            raise ValueError("Discovery interval must be positive")
        if self.min_completed_windows < 1 or self.min_shadow_trades < 1:
            raise ValueError("Evidence minimums must be positive")
        if self.external_move_threshold_bps <= 0:
            raise ValueError("External move threshold must be positive")
        if self.min_entry_seconds_remaining < 0:
            raise ValueError("Minimum entry time remaining cannot be negative")
        for name in (
            "min_reference_coverage", "max_data_gap", "max_drawdown",
            "max_edge_decay", "max_latency_sensitivity",
        ):
            if not 0 <= getattr(self, name) <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if not 0 <= self.repricing_ratio <= 1 or not 0 <= self.min_confidence <= 1:
            raise ValueError("Repricing ratio and confidence must be between 0 and 1")
