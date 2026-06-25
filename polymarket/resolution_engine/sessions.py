from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import MarketDescriptor


def collect_markets(runs_root: Path) -> list[MarketDescriptor]:
    markets: dict[str, MarketDescriptor] = {}
    for path in sorted(runs_root.glob("*/session.jsonl")):
        if path.parent.name == "latest":
            continue
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                    if event.get("event") != "market_lifecycle":
                        continue
                    payload = event.get("payload", {}).get("market", {})
                    market_id = str(payload["market_id"])
                    asset = str(payload["asset"])
                    if market_id.startswith("mock-") or asset not in {"BTC", "ETH", "SOL"}:
                        continue
                    markets[market_id] = MarketDescriptor(
                        market_id=market_id,
                        asset=asset,
                        question=str(payload.get("question", "")),
                        window_start=_dt(payload["window_start"]),
                        window_end=_dt(payload["window_end"]),
                    )
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    continue
    return sorted(
        markets.values(),
        key=lambda row: (row.window_start, row.asset, row.market_id),
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
