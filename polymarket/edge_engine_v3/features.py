from __future__ import annotations

import bisect
import json
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path

from polymarket.edge_engine.models import MarketSnapshot

from .models import LiveTick, ReferenceMode


def _clip(value: float) -> float:
    return max(0.001, min(0.999, value))


class ExternalReferenceStore:
    """Timestamp-aligned independent probability observations."""

    def __init__(self, path: str | Path) -> None:
        self.rows: dict[str, list[tuple[datetime, float]]] = defaultdict(list)
        with Path(path).open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                self.rows[str(row["market_id"])].append((
                    datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")),
                    float(row["reference_probability"]),
                ))
        for values in self.rows.values():
            values.sort()

    def latest(self, market_id: str, timestamp: datetime) -> float | None:
        values = self.rows.get(market_id, [])
        index = bisect.bisect_right(values, (timestamp, float("inf"))) - 1
        return values[index][1] if index >= 0 else None


class CausalLiveFeatureBuilder:
    def __init__(self, external: ExternalReferenceStore | None = None) -> None:
        self.external = external
        self.ewma: dict[str, float] = {}
        self.prices: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=24))
        self.moves: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=24))
        self.external_hits = 0
        self.observations = 0

    @property
    def mode(self) -> ReferenceMode:
        return ReferenceMode.EXTERNAL if self.external else ReferenceMode.CAUSAL_PROXY

    def build(self, tick: LiveTick) -> MarketSnapshot:
        price = _clip(tick.midpoint)
        history = self.prices[tick.market_id]
        previous = history[-1] if history else price
        move = abs(price - previous)
        self.moves[tick.market_id].append(move)
        external = self.external.latest(tick.market_id, tick.timestamp) if self.external else None
        self.observations += 1
        if external is not None:
            self.external_hits += 1
        reference = external if external is not None else self.ewma.get(tick.market_id, price)
        move_history = self.moves[tick.market_id]
        baseline = sum(move_history) / max(1, len(move_history))
        volume = _clip(0.5 * move / max(0.002, baseline) + 0.5 * min(1.0, tick.trade_size / 500.0))
        momentum = _clip(0.5 + (price - previous) * 10.0)
        stability = _clip(1.0 - baseline * 20.0 - tick.spread * 2.0)
        snapshot = MarketSnapshot(
            timestamp=tick.timestamp,
            market_id=tick.market_id,
            question=f"Live Polymarket market {tick.market_id}",
            yes_price=price,
            reference_probability=_clip(reference),
            volume_spike=volume,
            momentum=momentum,
            stability=stability,
        )
        history.append(price)
        prior_ewma = self.ewma.get(tick.market_id, price)
        self.ewma[tick.market_id] = 0.12 * price + 0.88 * prior_ewma
        return snapshot

    @property
    def external_coverage(self) -> float:
        return self.external_hits / self.observations if self.observations else 0.0
