from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import ResolutionRecord


def write_raw(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def read_raw(path: Path) -> dict[str, dict[str, Any] | None]:
    if not path.exists():
        raise FileNotFoundError(f"Resolution fixture not found: {path}")
    rows: dict[str, dict[str, Any] | None] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            rows[str(item["market_id"])] = item.get("event")
    return rows


def read_raw_retrieval_times(path: Path) -> dict[str, datetime]:
    rows = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            timestamp = item.get("retrieval_timestamp")
            if timestamp:
                rows[str(item["market_id"])] = datetime.fromisoformat(timestamp)
    return rows


def write_resolutions(path: Path, rows: list[ResolutionRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            payload = asdict(row)
            payload["resolution_timestamp"] = (
                row.resolution_timestamp.isoformat()
                if row.resolution_timestamp else None
            )
            payload["retrieval_timestamp"] = row.retrieval_timestamp.isoformat()
            handle.write(json.dumps(payload, sort_keys=True) + "\n")


def read_resolutions(path: Path) -> dict[str, ResolutionRecord]:
    if not path.exists():
        return {}
    result = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            row = ResolutionRecord(
                market_id=str(payload["market_id"]),
                asset=str(payload["asset"]),
                question=str(payload.get("question", "")),
                slug=str(payload["slug"]),
                outcome=(
                    int(payload["outcome"])
                    if payload.get("outcome") is not None else None
                ),
                outcome_name=str(payload.get("outcome_name", "")),
                resolution_timestamp=_dt(payload.get("resolution_timestamp")),
                resolution_source=str(payload.get("resolution_source", "")),
                retrieval_timestamp=_dt(payload["retrieval_timestamp"]),
                status=str(payload["status"]),
                reason=str(payload.get("reason", "")),
            )
            result[row.market_id] = row
    return result


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
