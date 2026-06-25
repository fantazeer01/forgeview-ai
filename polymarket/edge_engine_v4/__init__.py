"""BTC/ETH/SOL five-minute Polymarket lag scanner."""

from .config import ScannerConfig
from .scanner import CryptoLagScanner

__all__ = ["CryptoLagScanner", "ScannerConfig"]
__version__ = "4.0.0"
