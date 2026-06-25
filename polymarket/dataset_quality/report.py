from __future__ import annotations

import json
from pathlib import Path

from .analyzer import QualityMetrics


def write_quality_report(path: Path, metrics: QualityMetrics) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(metrics.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
