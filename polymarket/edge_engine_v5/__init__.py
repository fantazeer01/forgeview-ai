"""Long-running shadow capture and edge evidence system."""

from .config import CaptureConfig
from .long_capture import LongShadowCapture

__all__ = ["CaptureConfig", "LongShadowCapture"]
__version__ = "5.0.0"
