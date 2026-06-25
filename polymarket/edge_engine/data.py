from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol

from .models import MarketSnapshot


class MarketDataProvider(Protocol):
    def snapshots(self) -> Iterator[MarketSnapshot]:
        """Yield market snapshots in chronological order."""


class IterableMarketDataProvider:
    def __init__(self, snapshots: Iterable[MarketSnapshot]) -> None:
        self._snapshots = snapshots

    def snapshots(self) -> Iterator[MarketSnapshot]:
        yield from self._snapshots


class JsonLinesMarketDataProvider:
    """Loads snapshots from a local JSON Lines file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def snapshots(self) -> Iterator[MarketSnapshot]:
        if not self.path.exists():
            raise FileNotFoundError(f"Market data file not found: {self.path}")

        parsed: list[MarketSnapshot] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                    timestamp = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
                    parsed.append(
                        MarketSnapshot(
                            timestamp=timestamp,
                            market_id=str(row["market_id"]),
                            question=str(row.get("question", row["market_id"])),
                            yes_price=float(row["yes_price"]),
                            reference_probability=float(row["reference_probability"]),
                            volume_spike=float(row["volume_spike"]),
                            momentum=float(row["momentum"]),
                            stability=float(row["stability"]),
                        )
                    )
                except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                    raise ValueError(f"Invalid snapshot at {self.path}:{line_number}: {exc}") from exc

        yield from sorted(parsed, key=lambda item: item.timestamp)


class MockMarketDataProvider:
    """A deterministic scenario covering convergence, score, and timeout exits."""

    def snapshots(self) -> Iterator[MarketSnapshot]:
        start = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        scenarios = [
            (
                "fed-cut",
                "Will the Fed cut rates by September?",
                [
                    (0.28, 0.76, 0.92, 0.86, 0.90),
                    (0.39, 0.75, 0.75, 0.70, 0.88),
                    (0.62, 0.73, 0.55, 0.45, 0.85),
                    (0.71, 0.72, 0.60, 0.50, 0.82),
                ],
            ),
            (
                "mars-launch",
                "Will a Mars mission launch this year?",
                [
                    (0.74, 0.24, 0.95, 0.90, 0.86),
                    (0.67, 0.25, 0.76, 0.72, 0.84),
                    (0.61, 0.26, 0.00, 0.00, 0.00),
                    (0.58, 0.27, 0.15, 0.12, 0.78),
                ],
            ),
            (
                "budget-bill",
                "Will the budget bill pass this month?",
                [
                    (0.22, 0.70, 0.90, 0.88, 0.92),
                    (0.25, 0.70, 0.88, 0.84, 0.90),
                    (0.29, 0.69, 0.82, 0.76, 0.88),
                    (0.34, 0.68, 0.76, 0.70, 0.86),
                ],
            ),
        ]

        for step in range(4):
            timestamp = start + timedelta(minutes=5 * step)
            for market_id, question, rows in scenarios:
                yes, reference, volume, momentum, stability = rows[step]
                yield MarketSnapshot(
                    timestamp=timestamp,
                    market_id=market_id,
                    question=question,
                    yes_price=yes,
                    reference_probability=reference,
                    volume_spike=volume,
                    momentum=momentum,
                    stability=stability,
                )
