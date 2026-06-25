from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from polymarket.edge_engine_v3.models import ShadowDecision, ShadowTrade

from .opportunity import (
    CryptoMarket,
    Opportunity,
    PolymarketSnapshot,
    ReferencePrice,
    SkippedMarket,
    to_dict,
)


class SessionStore:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.session_dir = self.output_dir / "session"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.markets_path = self.session_dir / "markets.json"
        self.references_path = self.session_dir / "reference_prices.jsonl"
        self.polymarket_path = self.session_dir / "polymarket_snapshots.jsonl"
        self.references_path.write_text("", encoding="utf-8")
        self.polymarket_path.write_text("", encoding="utf-8")

    def write_markets(self, markets: list[CryptoMarket]) -> None:
        self.markets_path.write_text(
            json.dumps(to_dict(markets), indent=2), encoding="utf-8"
        )

    def append_reference(self, row: ReferencePrice) -> None:
        self._append(self.references_path, row)

    def append_polymarket(self, row: PolymarketSnapshot) -> None:
        self._append(self.polymarket_path, row)

    @staticmethod
    def _append(path: Path, row) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(to_dict(row), sort_keys=True, separators=(",", ":")) + "\n")

    @staticmethod
    def load(session_dir: str | Path) -> tuple[list[CryptoMarket], list[ReferencePrice], list[PolymarketSnapshot]]:
        source = Path(session_dir)
        markets = [
            CryptoMarket(
                **{
                    **row,
                    "window_start": datetime.fromisoformat(row["window_start"]),
                    "window_end": datetime.fromisoformat(row["window_end"]),
                }
            )
            for row in json.loads((source / "markets.json").read_text(encoding="utf-8"))
        ]
        references = [
            ReferencePrice(
                datetime.fromisoformat(row["timestamp"]),
                row["asset"], float(row["price"]), row["source"],
            )
            for row in _read_jsonl(source / "reference_prices.jsonl")
        ]
        snapshots = [
            PolymarketSnapshot(
                timestamp=datetime.fromisoformat(row["timestamp"]),
                market_id=row["market_id"],
                asset=row["asset"],
                yes_price=float(row["yes_price"]),
                no_price=float(row["no_price"]),
                yes_bid=float(row["yes_bid"]),
                yes_ask=float(row["yes_ask"]),
                liquidity=float(row["liquidity"]),
                seconds_to_expiry=float(row["seconds_to_expiry"]),
            )
            for row in _read_jsonl(source / "polymarket_snapshots.jsonl")
        ]
        if not markets or not references or not snapshots:
            raise ValueError(f"Incomplete v4 session: {source}")
        return markets, references, snapshots


def write_reports(
    output_dir: str | Path,
    markets: list[CryptoMarket],
    opportunities: list[Opportunity],
    skipped: list[SkippedMarket],
    decisions: list[ShadowDecision],
    trades: list[ShadowTrade],
    mock_mode: bool,
    fallback_reason: str,
    preserve_session: bool = False,
) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    _write_csv(output / "opportunities.csv", opportunities)
    _write_csv(output / "skipped_markets.csv", skipped)
    _write_csv(output / "shadow_decisions.csv", decisions)
    _write_csv(output / "shadow_trades.csv", trades)
    if not preserve_session:
        # Convenient report-root copies; canonical replay inputs remain in session/.
        for name in ("reference_prices.jsonl", "polymarket_snapshots.jsonl"):
            source = output / "session" / name
            (output / name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    pnl = round(sum(row.pnl for row in trades), 6)
    by_asset = {
        asset: sum(row.asset == asset for row in opportunities)
        for asset in sorted({market.asset for market in markets})
    }
    summary = {
        "mode": "mock" if mock_mode else "public",
        "fallback_reason": fallback_reason,
        "markets": len(markets),
        "opportunities": len(opportunities),
        "skipped_decisions": len(skipped),
        "shadow_decisions": len(decisions),
        "shadow_trades": len(trades),
        "shadow_pnl": pnl,
        "opportunities_by_asset": by_asset,
        "no_trading_guarantee": True,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = [
        "# Polymarket Edge Engine v4 Scan",
        "",
        f"- Mode: **{summary['mode']}**",
        f"- Markets scanned: **{summary['markets']}**",
        f"- Opportunities: **{summary['opportunities']}**",
        f"- Skipped decisions: **{summary['skipped_decisions']}**",
        f"- v3 shadow decisions: **{summary['shadow_decisions']}**",
        f"- Shadow P&L: **${summary['shadow_pnl']:+,.2f}**",
        f"- Real orders submitted: **0**",
    ]
    if fallback_reason:
        lines.append(f"- Fallback reason: `{fallback_reason}`")
    lines.extend(["", "## Opportunities by asset", ""])
    lines.extend(f"- {asset}: {count}" for asset, count in by_asset.items())
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def _write_csv(path: Path, rows: list) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    data = [to_dict(row) for row in rows]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)


def _read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]
