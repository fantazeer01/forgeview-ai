from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import ValidationReport, to_dict


def write_report(report: ValidationReport, output_dir: str | Path) -> Path:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    payload = to_dict(report)
    (destination / "validation_report.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    with (destination / "windows.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "run_id", "scenario", "parameter", "window_id", "start", "end",
            "snapshots", "trades", "pnl", "return_pct", "max_drawdown", "win_rate",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for scenario in (report.baseline, *report.scenarios):
            for window in scenario.windows:
                row = to_dict(window)
                writer.writerow({
                    "run_id": scenario.run_id,
                    "scenario": scenario.scenario,
                    "parameter": scenario.parameter,
                    **row,
                })

    with (destination / "trades.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "trade_id", "run_id", "window_id", "market_id", "side", "signal_at",
            "opened_at", "closed_at", "entry_price", "exit_price", "quantity",
            "entry_score", "exit_score", "exit_reason", "pnl", "return_pct",
            "holding_steps", "entry_delay_steps",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for scenario in (report.baseline, *report.scenarios):
            for trade in scenario.trade_log:
                writer.writerow(to_dict(trade))

    lines = [
        "# Alpha Validation Report",
        "",
        f"- Verdict: **{report.verdict}**",
        f"- Robustness score: **{report.robustness_score:.2f}/100**",
        f"- Baseline global P&L: **${report.baseline.pnl:,.2f}**",
        f"- Baseline max drawdown: **{report.baseline.max_drawdown:.2%}**",
        f"- Stress-scenario P&L variance: **{report.scenario_pnl_variance:,.2f}**",
        f"- Dataset fingerprint: `{report.dataset_fingerprint}`",
        "",
        "## Direct answers",
        "",
        f"- Survives noise: **{'YES' if report.answers['noise'] else 'NO'}**",
        f"- Survives different time periods: **{'YES' if report.answers['time_periods'] else 'NO'}**",
        f"- Survives execution delay: **{'YES' if report.answers['execution_delay'] else 'NO'}**",
        f"- Survives signal lag: **{'YES' if report.answers['signal_lag'] else 'NO'}**",
        "",
        "## Baseline P&L by walk-forward window",
        "",
        "| Window | P&L | Trades | Max drawdown | Win rate |",
        "|---:|---:|---:|---:|---:|",
    ]
    for window in report.baseline.windows:
        lines.append(
            f"| {window.window_id} | ${window.pnl:,.2f} | {window.trades} | "
            f"{window.max_drawdown:.2%} | {window.win_rate:.1%} |"
        )
    (destination / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination
