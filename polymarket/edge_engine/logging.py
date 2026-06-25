from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

from .models import ClosedTrade, serializable


def configure_logger(verbose: bool = False) -> logging.Logger:
    logger = logging.getLogger("edge_engine")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%H:%M:%S"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


class RunLogger:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.output_dir / "events.jsonl"
        self.equity_path = self.output_dir / "equity.csv"
        self.trades_path = self.output_dir / "trades.csv"

        self.events_path.write_text("", encoding="utf-8")
        with self.equity_path.open("w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(
                ["timestamp", "realized_pnl", "unrealized_pnl", "total_pnl", "ending_equity", "open_positions"]
            )

    def event(self, event_type: str, payload: dict[str, Any]) -> None:
        row = {"event": event_type, **serializable(payload)}
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, separators=(",", ":")) + "\n")

    def equity(self, timestamp: Any, summary: dict[str, Any]) -> None:
        with self.equity_path.open("a", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(
                [
                    serializable(timestamp),
                    summary["realized_pnl"],
                    summary["unrealized_pnl"],
                    summary["total_pnl"],
                    summary["ending_equity"],
                    summary["open_positions"],
                ]
            )

    def write_trades(self, trades: list[ClosedTrade]) -> None:
        fields = [
            "trade_id", "market_id", "question", "side", "quantity", "entry_price",
            "exit_price", "entry_score", "exit_score", "opened_at", "closed_at",
            "exit_reason", "pnl", "return_pct", "holding_steps",
        ]
        with self.trades_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for trade in trades:
                writer.writerow(serializable(trade))

    def write_summary(self, summary: dict[str, Any]) -> None:
        (self.output_dir / "summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
