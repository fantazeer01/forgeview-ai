from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class SessionDiagnostics:
    total_events: int
    event_types: dict[str, int]
    first_timestamp: str
    last_timestamp: str
    markets: int
    reference_snapshots: int
    polymarket_snapshots: int
    opportunity_events: int
    reference_sources: dict[str, int]
    reference_timestamp_mismatches: int
    polymarket_timestamp_mismatches: int
    snapshots_without_exact_reference: int
    has_session_completed: bool
    has_capture_checkpoint: bool
    missing_reference_reason: str
    likely_cause: str
    recommended_fix: str


def inspect_session(path: str | Path) -> SessionDiagnostics:
    source = Path(path)
    counts: Counter[str] = Counter()
    reference_sources: Counter[str] = Counter()
    markets: set[str] = set()
    reference_keys: set[tuple[str, str]] = set()
    snapshot_keys: list[tuple[str, str]] = []
    first = ""
    last = ""
    reference_mismatches = 0
    snapshot_mismatches = 0
    completed = False
    checkpoint = False

    with source.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            event = str(row["event"])
            timestamp = str(row["timestamp"])
            payload = row.get("payload", {})
            counts[event] += 1
            first = first or timestamp
            last = timestamp
            if event == "market_lifecycle":
                market_id = payload.get("market_id")
                if not market_id and payload.get("market"):
                    market_id = payload["market"].get("market_id")
                if market_id:
                    markets.add(str(market_id))
            elif event == "reference_price":
                reference_sources[str(payload.get("source", "unknown"))] += 1
                reference_keys.add((timestamp, str(payload.get("asset"))))
                if payload.get("timestamp") and str(payload["timestamp"]) != timestamp:
                    reference_mismatches += 1
            elif event == "polymarket_snapshot":
                snapshot_keys.append((timestamp, str(payload.get("asset"))))
                if payload.get("timestamp") and str(payload["timestamp"]) != timestamp:
                    snapshot_mismatches += 1
            elif event == "session_completed":
                completed = True
            elif event == "capture_checkpoint":
                checkpoint = True

    missing_exact = sum(key not in reference_keys for key in snapshot_keys)
    reference_count = counts["reference_price"]
    if reference_count == 0:
        missing_reason = "capture_did_not_save_reference_price_events"
    elif not completed and not checkpoint:
        missing_reason = (
            "reference events exist, but the interrupted legacy session has no "
            "session_completed or capture_checkpoint counters"
        )
    elif missing_exact:
        missing_reason = (
            f"{missing_exact} Polymarket snapshots have no reference event with "
            "the same event timestamp and asset"
        )
    else:
        missing_reason = "none"

    causes = []
    if not completed:
        causes.append("capture ended before session_completed")
    if reference_sources.get("mock", 0) and reference_sources.get("binance", 0):
        causes.append("capture switched from public data to mock fallback mid-session")
    if counts["opportunity"] > max(1, len(markets) * 2):
        causes.append("qualified lag was emitted repeatedly for the same market")
    likely = "; ".join(causes) or "no structural anomaly detected"
    fixes = [
        "infer counters from saved events when completion metadata is absent",
        "write periodic capture checkpoints",
        "permit at most one opportunity per market window",
    ]
    if reference_sources.get("mock", 0):
        fixes.append("do not enter mock fallback after public markets have been observed")

    return SessionDiagnostics(
        total_events=sum(counts.values()),
        event_types=dict(sorted(counts.items())),
        first_timestamp=first,
        last_timestamp=last,
        markets=len(markets),
        reference_snapshots=reference_count,
        polymarket_snapshots=counts["polymarket_snapshot"],
        opportunity_events=counts["opportunity"],
        reference_sources=dict(sorted(reference_sources.items())),
        reference_timestamp_mismatches=reference_mismatches,
        polymarket_timestamp_mismatches=snapshot_mismatches,
        snapshots_without_exact_reference=missing_exact,
        has_session_completed=completed,
        has_capture_checkpoint=checkpoint,
        missing_reference_reason=missing_reason,
        likely_cause=likely,
        recommended_fix="; ".join(fixes),
    )


def diagnostics_dict(value: SessionDiagnostics) -> dict:
    return asdict(value)
