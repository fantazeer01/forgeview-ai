from __future__ import annotations

import csv
import json
import shutil
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from polymarket.edge_engine_v3.models import ShadowTrade
from polymarket.edge_engine_v4.opportunity import Opportunity, SkippedMarket, to_dict

from .evidence import EvidenceVerdict
from .market_rotation import TrackedMarket
from .metrics import EvidenceMetrics
from .market_lifecycle import LifecycleEvent


class EventStore:
    def __init__(self, session_dir: str | Path, reset: bool = True) -> None:
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.session_dir / "session.jsonl"
        if reset:
            self.path.write_text("", encoding="utf-8")

    def append(self, event_type: str, timestamp: datetime, payload: Any) -> None:
        row = {
            "event": event_type,
            "timestamp": timestamp.isoformat(),
            "payload": to_dict(payload),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")

    @staticmethod
    def read(path: str | Path) -> list[dict[str, Any]]:
        source = Path(path)
        with source.open("r", encoding="utf-8") as handle:
            rows = [json.loads(line) for line in handle if line.strip()]
        if not rows:
            raise ValueError(f"Empty v5 session: {source}")
        return rows


def write_evidence_artifacts(
    session_dir: str | Path,
    tracked_markets: list[TrackedMarket],
    opportunities: list[Opportunity],
    trades: list[ShadowTrade],
    skipped: list[SkippedMarket],
    metrics: EvidenceMetrics,
    verdict: EvidenceVerdict,
    mode: str,
    fallback_reason: str,
    lifecycle_events: list[LifecycleEvent] | None = None,
    lifecycle_summary: dict[str, float | int] | None = None,
    campaign_completeness: dict[str, Any] | None = None,
    discovery_failures: list[dict[str, Any]] | None = None,
    observation_continuity: dict[str, Any] | None = None,
    microstructure_coverage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output = Path(session_dir)
    output.mkdir(parents=True, exist_ok=True)
    market_rows = []
    for tracked in sorted(
        tracked_markets,
        key=lambda row: (row.market.window_start, row.market.asset, row.market.market_id),
    ):
        market_rows.append({
            **to_dict(tracked.market),
            "lifecycle": tracked.lifecycle.value,
            "discovered_at": tracked.discovered_at.isoformat(),
            "updated_at": tracked.updated_at.isoformat(),
            "snapshots": tracked.snapshots,
            "opportunities": tracked.opportunities,
            "skip_reason": tracked.skip_reason,
        })
    _write_csv(output / "markets.csv", market_rows)
    _write_csv(output / "opportunities.csv", [to_dict(row) for row in opportunities])
    _write_csv(output / "trades.csv", [to_dict(row) for row in trades])
    _write_csv(output / "skipped_markets.csv", [to_dict(row) for row in skipped])
    _write_csv(
        output / "lifecycle_events.csv",
        [to_dict(row) for row in (lifecycle_events or [])],
    )
    (output / "lifecycle_summary.json").write_text(
        json.dumps(lifecycle_summary or {}, indent=2), encoding="utf-8"
    )

    report = {
        "mode": mode,
        "fallback_reason": fallback_reason,
        "verdict": verdict.value,
        "metrics": asdict(metrics),
        "campaign_completeness": campaign_completeness or {},
        "observation_continuity": observation_continuity or {},
        "discovery_failures": discovery_failures or [],
        "microstructure_coverage": microstructure_coverage or {},
        "no_trading_guarantee": True,
    }
    (output / "evidence_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    lines = [
        "# Polymarket Edge Engine v5 Evidence Report",
        "",
        f"- Verdict: **{verdict.value}**",
        f"- Mode: **{mode}**",
        f"- Completed windows: **{metrics.completed_market_windows}**",
        f"- Opportunities: **{metrics.opportunities_detected}**",
        f"- Shadow trades: **{metrics.shadow_trades}**",
        f"- Simulated P&L after slippage: **${metrics.simulated_pnl:+,.2f}**",
        f"- Win rate: **{metrics.win_rate:.1%}**",
        f"- Max drawdown: **{metrics.max_drawdown:.2%}**",
        f"- Edge decay: **{metrics.edge_decay:.1%}**",
        f"- Latency sensitivity: **{metrics.latency_sensitivity:.1%}**",
        f"- Reference coverage: **{metrics.reference_coverage_percentage:.2f}%**",
        f"- Data gaps: **{metrics.data_gap_percentage:.2f}%**",
        (
            "- Campaign completeness: "
            f"**{(campaign_completeness or {}).get('status', 'unknown')}**"
        ),
        (
            "- Temporal coverage: "
            f"**{(campaign_completeness or {}).get('coverage_percentage', 0.0):.2f}%**"
        ),
        f"- Discovery failures: **{len(discovery_failures or [])}**",
        (
            "- Microstructure events: "
            f"**{(microstructure_coverage or {}).get('events', 0)}**"
        ),
        (
            "- Checkpoint coverage: "
            f"**{(observation_continuity or {}).get('checkpoint_coverage_percentage', 0.0):.2f}%**"
        ),
        (
            "- Maximum checkpoint gap: "
            f"**{(observation_continuity or {}).get('max_checkpoint_gap_seconds', 0.0):.3f}s**"
        ),
        f"- Real orders submitted: **0**",
    ]
    rejection_reasons = (campaign_completeness or {}).get(
        "rejection_reasons", []
    )
    if rejection_reasons:
        lines.append(
            "- Campaign rejection reason: `"
            + ";".join(rejection_reasons)
            + "`"
        )
    if fallback_reason:
        lines.append(f"- Fallback reason: `{fallback_reason}`")
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def update_latest(session_dir: str | Path, output_root: str | Path) -> Path:
    source = Path(session_dir).resolve()
    root = Path(output_root).resolve()
    latest = root / "latest"
    if source == latest:
        return latest
    if latest.exists():
        shutil.rmtree(latest)
    shutil.copytree(source, latest)
    return latest


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
