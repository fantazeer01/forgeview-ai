from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import ResolutionRecord


def reconcile(
    records: list[ResolutionRecord],
    proxy_dataset: Path,
    output_root: Path,
) -> dict:
    proxies = _proxy_labels(proxy_dataset)
    details = []
    counts = {
        "total_markets": len(records),
        "resolved": 0,
        "matched": 0,
        "mismatched": 0,
        "unresolved": 0,
        "missing": 0,
        "ambiguous": 0,
        "cancelled": 0,
        "malformed": 0,
        "no_proxy": 0,
    }
    for record in records:
        status = record.status
        proxy = proxies.get(record.market_id)
        reconciliation = status
        if record.resolved:
            counts["resolved"] += 1
            if proxy is None:
                reconciliation = "no_proxy"
                counts["no_proxy"] += 1
            elif proxy == record.outcome:
                reconciliation = "matched"
                counts["matched"] += 1
            else:
                reconciliation = "mismatched"
                counts["mismatched"] += 1
        elif status in counts:
            counts[status] += 1
        details.append({
            "market_id": record.market_id,
            "asset": record.asset,
            "authoritative_outcome": record.outcome,
            "proxy_outcome": proxy,
            "reconciliation_status": reconciliation,
            "resolution_status": record.status,
            "reason": record.reason,
        })
    report = {
        **counts,
        "authoritative_coverage_percentage": round(
            counts["resolved"] / len(records) * 100, 4
        ) if records else 0.0,
        "agreement_percentage": round(
            counts["matched"] / (counts["matched"] + counts["mismatched"]) * 100,
            4,
        ) if counts["matched"] + counts["mismatched"] else 0.0,
        "details": details,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "reconciliation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    return report


def _proxy_labels(path: Path) -> dict[str, int]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        return {
            str(row["market_id"]): int(row["outcome"])
            for row in csv.DictReader(handle)
            if row.get("market_id") and row.get("outcome") in {"0", "1"}
        }
