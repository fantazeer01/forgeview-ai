from __future__ import annotations

import random
from collections import defaultdict, deque

from polymarket.edge_engine.models import MarketSnapshot


def perturb_snapshots(
    snapshots: list[MarketSnapshot],
    seed: int,
    price_noise_std: float = 0.0,
    signal_dropout: float = 0.0,
    signal_lag_steps: int = 0,
) -> list[MarketSnapshot]:
    if price_noise_std < 0 or not 0 <= signal_dropout < 1 or signal_lag_steps < 0:
        raise ValueError("Invalid perturbation parameters")
    rng = random.Random(seed)
    histories: dict[str, deque[tuple[float, float, float, float]]] = defaultdict(
        lambda: deque(maxlen=signal_lag_steps + 1)
    )
    output: list[MarketSnapshot] = []
    for row in sorted(snapshots, key=lambda item: (item.timestamp, item.market_id)):
        noisy_price = max(0.001, min(0.999, row.yes_price + rng.gauss(0, price_noise_std)))
        current_signal = (
            row.reference_probability,
            row.volume_spike,
            row.momentum,
            row.stability,
        )
        history = histories[row.market_id]
        history.append(current_signal)
        signal = history[0] if len(history) > signal_lag_steps else current_signal
        if rng.random() < signal_dropout:
            # A missing signal becomes neutral; market prices remain observable.
            signal = (noisy_price, 0.0, 0.0, 0.5)
        output.append(
            MarketSnapshot(
                timestamp=row.timestamp,
                market_id=row.market_id,
                question=row.question,
                yes_price=round(noisy_price, 6),
                reference_probability=round(signal[0], 6),
                volume_spike=round(signal[1], 6),
                momentum=round(signal[2], 6),
                stability=round(signal[3], 6),
            )
        )
    return output
