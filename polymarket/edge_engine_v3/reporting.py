from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import LiveValidationReport, ShadowDecision, ShadowTrade, to_dict


def write_live_report(
    report: LiveValidationReport,
    decisions: list[ShadowDecision],
    trades: list[ShadowTrade],
    output_dir: str | Path,
) -> None:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "live_validation_report.json").write_text(
        json.dumps(to_dict(report), indent=2), encoding="utf-8"
    )
    _csv(destination / "decisions.csv", decisions)
    _csv(destination / "shadow_trades.csv", trades)
    lines = [
        "# Real-Market Alpha Validation",
        "",
        f"- Verdict: **{report.verdict}**",
        f"- Reference mode: **{report.reference_mode.value}**",
        f"- Independent-reference coverage: **{report.external_reference_coverage:.1%}**",
        f"- Live simulated P&L: **${report.live_simulated_pnl:,.2f}**",
        f"- Model expected P&L: **${report.model_expected_pnl:,.2f}**",
        f"- Model/live divergence: **{report.divergence_score:.2f}/100** (lower is better)",
        f"- Signal drift: **{report.signal_drift_score:.2f}/100** (lower is better)",
        f"- Edge decay: **{report.edge_decay_score:.2f}/100** (lower is better)",
        f"- Stability: **{report.stability_score:.2f}/100** (higher is better)",
        f"- Evidence sufficient: **{'YES' if report.evidence_sufficient else 'NO'}**",
        "",
        "## Period P&L",
        "",
    ]
    lines.extend(f"- Period {index}: ${pnl:+,.2f}" for index, pnl in enumerate(report.period_pnl, 1))
    if report.caveats:
        lines.extend(["", "## Caveats", ""])
        lines.extend(f"- {item}" for item in report.caveats)
    (destination / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _csv(path: Path, rows: list) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    data = [to_dict(row) for row in rows]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)
