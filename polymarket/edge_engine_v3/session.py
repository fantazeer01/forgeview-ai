from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from .models import LiveTick, to_dict


class LiveSessionStore:
    def __init__(self, directory: str | Path, reset: bool = True) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.raw_path = self.directory / "raw_events.jsonl"
        self.ticks_path = self.directory / "ticks.jsonl"
        if reset:
            self.raw_path.write_text("", encoding="utf-8")
            self.ticks_path.write_text("", encoding="utf-8")

    def append(self, raw: str, tick: LiveTick) -> None:
        with self.raw_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"raw": raw}, separators=(",", ":")) + "\n")
        with self.ticks_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(to_dict(tick), sort_keys=True, separators=(",", ":")) + "\n")

    @staticmethod
    def load_ticks(path: str | Path) -> list[LiveTick]:
        source = Path(path)
        if source.is_dir():
            source = source / "ticks.jsonl"
        ticks = []
        with source.open("r", encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                    ticks.append(LiveTick(
                        timestamp=datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")),
                        token_id=str(row["token_id"]),
                        market_id=str(row["market_id"]),
                        best_bid=float(row["best_bid"]),
                        best_ask=float(row["best_ask"]),
                        last_trade=float(row["last_trade"]) if row.get("last_trade") is not None else None,
                        trade_size=float(row.get("trade_size", 0)),
                        source_event=str(row.get("source_event", "replay")),
                    ))
                except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                    raise ValueError(f"Invalid live session row {source}:{number}: {exc}") from exc
        if not ticks:
            raise ValueError(f"Live session has no ticks: {source}")
        return sorted(ticks, key=lambda row: (row.timestamp, row.market_id))

    @staticmethod
    def fingerprint(ticks: list[LiveTick]) -> str:
        digest = hashlib.sha256()
        for tick in ticks:
            digest.update(json.dumps(to_dict(tick), sort_keys=True, separators=(",", ":")).encode())
            digest.update(b"\n")
        return digest.hexdigest()


def resample_ticks(ticks: list[LiveTick], seconds: int = 1) -> list[LiveTick]:
    """Keep the first actionable quote per market/time bucket."""
    if seconds < 1:
        raise ValueError("sample interval must be at least one second")
    selected: dict[tuple[str, int], LiveTick] = {}
    for tick in sorted(ticks, key=lambda row: (row.timestamp, row.market_id)):
        bucket = int(tick.timestamp.timestamp()) // seconds
        selected.setdefault((tick.market_id, bucket), tick)
    return sorted(selected.values(), key=lambda row: (row.timestamp, row.market_id))
