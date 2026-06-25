from __future__ import annotations

import hashlib
import json
import math
import random
import urllib.parse
import urllib.request
from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from pathlib import Path

from polymarket.edge_engine.models import MarketSnapshot


def _clip(value: float, lower: float = 0.001, upper: float = 0.999) -> float:
    return max(lower, min(upper, value))


class ReplayStore:
    """Canonical JSONL storage with deterministic ordering and fingerprinting."""

    @staticmethod
    def save(snapshots: Iterable[MarketSnapshot], path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        ordered = sorted(snapshots, key=lambda row: (row.timestamp, row.market_id))
        with destination.open("w", encoding="utf-8") as handle:
            for row in ordered:
                payload = {
                    "timestamp": row.timestamp.isoformat(),
                    "market_id": row.market_id,
                    "question": row.question,
                    "yes_price": row.yes_price,
                    "reference_probability": row.reference_probability,
                    "volume_spike": row.volume_spike,
                    "momentum": row.momentum,
                    "stability": row.stability,
                }
                handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
        return destination

    @staticmethod
    def load(path: str | Path) -> list[MarketSnapshot]:
        source = Path(path)
        rows: list[MarketSnapshot] = []
        with source.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    rows.append(
                        MarketSnapshot(
                            timestamp=datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")),
                            market_id=str(item["market_id"]),
                            question=str(item.get("question", item["market_id"])),
                            yes_price=float(item["yes_price"]),
                            reference_probability=float(item["reference_probability"]),
                            volume_spike=float(item["volume_spike"]),
                            momentum=float(item["momentum"]),
                            stability=float(item["stability"]),
                        )
                    )
                except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                    raise ValueError(f"Invalid replay row {source}:{line_number}: {exc}") from exc
        if not rows:
            raise ValueError(f"Replay dataset is empty: {source}")
        return sorted(rows, key=lambda row: (row.timestamp, row.market_id))

    @staticmethod
    def fingerprint(snapshots: Iterable[MarketSnapshot]) -> str:
        digest = hashlib.sha256()
        for row in sorted(snapshots, key=lambda item: (item.timestamp, item.market_id)):
            digest.update(
                (
                    f"{row.timestamp.isoformat()}|{row.market_id}|{row.yes_price:.8f}|"
                    f"{row.reference_probability:.8f}|{row.volume_spike:.8f}|"
                    f"{row.momentum:.8f}|{row.stability:.8f}\n"
                ).encode()
            )
        return digest.hexdigest()


class HybridProxyData:
    """Deterministic market-like series with regime changes, lag, and noise."""

    def __init__(self, seed: int = 42, markets: int = 5, steps: int = 240) -> None:
        self.seed = seed
        self.markets = markets
        self.steps = steps

    def generate(self) -> list[MarketSnapshot]:
        rng = random.Random(self.seed)
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        state = []
        for market in range(self.markets):
            fair = 0.25 + 0.12 * market
            state.append({"fair": fair, "price": _clip(fair + rng.gauss(0, 0.025)), "prev": fair})

        rows: list[MarketSnapshot] = []
        for step in range(self.steps):
            regime = 1.0 if (step // 60) % 2 == 0 else -0.65
            for market, item in enumerate(state):
                cyclical = 0.012 * math.sin(step / (8.0 + market))
                shock = 0.0
                if step % (31 + market * 3) == 5:
                    shock = regime * (0.22 + 0.008 * market)
                item["fair"] = _clip(
                    item["fair"] + cyclical * 0.12 + shock + rng.gauss(0, 0.006),
                    0.08,
                    0.92,
                )
                prior_price = item["price"]
                # Market partially catches up to the latent/reference probability.
                item["price"] = _clip(
                    prior_price + 0.16 * (item["fair"] - prior_price) + rng.gauss(0, 0.012),
                    0.03,
                    0.97,
                )
                dislocation = abs(item["fair"] - item["price"])
                price_move = abs(item["price"] - prior_price)
                volume = _clip(0.35 + dislocation * 5.5 + price_move * 4.0, 0.0, 1.0)
                momentum = _clip(0.35 + dislocation * 5.0, 0.0, 1.0)
                stability = _clip(1.0 - abs(rng.gauss(0, 0.12)) - price_move * 2.0, 0.0, 1.0)
                rows.append(
                    MarketSnapshot(
                        timestamp=start + timedelta(hours=step),
                        market_id=f"hybrid-{market + 1}",
                        question=f"Hybrid research market {market + 1}",
                        yes_price=round(item["price"], 6),
                        reference_probability=round(item["fair"], 6),
                        volume_spike=round(volume, 6),
                        momentum=round(momentum, 6),
                        stability=round(stability, 6),
                    )
                )
                item["prev"] = prior_price
        return rows


class PolymarketHistoryClient:
    """Read-only public CLOB history client. No credentials and no trading methods."""

    BASE_URL = "https://clob.polymarket.com/prices-history"

    def fetch(
        self,
        token_id: str,
        interval: str = "max",
        fidelity: int = 60,
        start_ts: int | None = None,
        end_ts: int | None = None,
        timeout: int = 20,
    ) -> list[tuple[datetime, float]]:
        params: dict[str, str | int] = {
            "market": token_id,
            "interval": interval,
            "fidelity": fidelity,
        }
        if start_ts is not None:
            params["startTs"] = start_ts
        if end_ts is not None:
            params["endTs"] = end_ts
        request = urllib.request.Request(
            f"{self.BASE_URL}?{urllib.parse.urlencode(params)}",
            headers={"User-Agent": "polymarket-edge-engine-v2/2.0"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        history = payload.get("history", [])
        rows = [
            (datetime.fromtimestamp(float(item["t"]), tz=timezone.utc), float(item["p"]))
            for item in history
        ]
        if not rows:
            raise ValueError("Polymarket returned no price history for this token")
        return sorted(rows)


def prices_to_causal_proxy(
    history: list[tuple[datetime, float]],
    market_id: str,
    question: str = "Polymarket historical token",
) -> list[MarketSnapshot]:
    """Build causal v1 inputs using only current/past prices; no future leakage."""
    if len(history) < 8:
        raise ValueError("At least 8 historical price observations are required")
    alpha = 0.12
    ewma = history[0][1]
    recent_moves: list[float] = []
    rows: list[MarketSnapshot] = []
    for index, (timestamp, price) in enumerate(history):
        price = _clip(price)
        previous = history[index - 1][1] if index else price
        move = abs(price - previous)
        recent_moves.append(move)
        recent_moves = recent_moves[-12:]
        baseline_move = sum(recent_moves[:-1]) / max(1, len(recent_moves) - 1)
        volume_proxy = _clip(move / max(0.005, baseline_move * 2.0), 0.0, 1.0)
        momentum = _clip(0.5 + (price - previous) * 8.0, 0.0, 1.0)
        mean_move = sum(recent_moves) / len(recent_moves)
        stability = _clip(1.0 - mean_move * 10.0, 0.0, 1.0)
        rows.append(
            MarketSnapshot(
                timestamp=timestamp,
                market_id=market_id,
                question=question,
                yes_price=price,
                reference_probability=_clip(ewma),
                volume_spike=volume_proxy,
                momentum=momentum,
                stability=stability,
            )
        )
        ewma = alpha * price + (1.0 - alpha) * ewma
    return rows


def group_by_timestamp(snapshots: Iterable[MarketSnapshot]) -> list[list[MarketSnapshot]]:
    grouped: dict[datetime, list[MarketSnapshot]] = defaultdict(list)
    for row in snapshots:
        grouped[row.timestamp].append(row)
    return [sorted(grouped[key], key=lambda item: item.market_id) for key in sorted(grouped)]
