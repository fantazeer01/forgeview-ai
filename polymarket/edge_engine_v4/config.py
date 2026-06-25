from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SUPPORTED_ASSETS = ("BTC", "ETH", "SOL")


@dataclass(frozen=True)
class ScannerConfig:
    assets: tuple[str, ...] = SUPPORTED_ASSETS
    duration_seconds: float = 300.0
    poll_interval_seconds: float = 2.0
    min_liquidity: float = 500.0
    min_seconds_to_expiry: float = 20.0
    external_move_threshold_bps: float = 4.0
    repricing_ratio: float = 0.65
    min_confidence: float = 0.55
    output_dir: Path = Path("polymarket/runs/v4/latest")
    mock: bool = False
    allow_mock_fallback: bool = True
    request_timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        invalid = set(self.assets) - set(SUPPORTED_ASSETS)
        if invalid:
            raise ValueError(f"Unsupported assets: {sorted(invalid)}")
        if self.duration_seconds <= 0 or self.poll_interval_seconds <= 0:
            raise ValueError("Duration and poll interval must be positive")
        if self.min_liquidity < 0:
            raise ValueError("Minimum liquidity cannot be negative")
