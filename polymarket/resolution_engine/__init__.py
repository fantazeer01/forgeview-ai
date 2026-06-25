"""Authoritative Polymarket outcome ingestion and reconciliation."""

from .models import MarketDescriptor, ResolutionRecord
from .resolver import GammaResolutionClient, parse_resolution

__all__ = [
    "GammaResolutionClient",
    "MarketDescriptor",
    "ResolutionRecord",
    "parse_resolution",
]
