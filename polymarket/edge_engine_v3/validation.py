from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from pathlib import Path

from polymarket.edge_engine_v2.metrics import clamp_score, coefficient_stability, max_drawdown

from .features import CausalLiveFeatureBuilder, ExternalReferenceStore
from .models import LiveTick, LiveValidationReport, ReferenceMode
from .session import LiveSessionStore, resample_ticks
from .shadow import ShadowExecutionEngine


@dataclass(frozen=True)
class LiveValidationConfig:
    model_report: Path = Path("polymarket/runs/v2/latest/validation_report.json")
    output_dir: Path = Path("polymarket/runs/v3/latest")
    reference_file: Path | None = None
    stake: float = 100.0
    slippage_bps: float = 10.0
    timeout_updates: int = 8
    minimum_trades: int = 30
    periods: int = 4


class LiveAlphaValidator:
    def __init__(self, ticks: list[LiveTick], config: LiveValidationConfig | None = None) -> None:
        if not ticks:
            raise ValueError("Live validation requires ticks")
        self.raw_ticks = sorted(ticks, key=lambda row: (row.timestamp, row.market_id))
        self.ticks = resample_ticks(self.raw_ticks)
        self.config = config or LiveValidationConfig()

    def run(self) -> LiveValidationReport:
        model = json.loads(self.config.model_report.read_text(encoding="utf-8"))
        external = ExternalReferenceStore(self.config.reference_file) if self.config.reference_file else None
        features = CausalLiveFeatureBuilder(external)
        shadow = ShadowExecutionEngine(
            self.config.stake, self.config.slippage_bps, self.config.timeout_updates
        )
        snapshots = []
        for tick in self.ticks:
            snapshot = features.build(tick)
            snapshots.append(snapshot)
            shadow.on_snapshot(snapshot)
        shadow.finalize()

        live_pnl = sum(trade.pnl for trade in shadow.trades)
        baseline = model["baseline"]
        expected_per_trade = baseline["pnl"] / max(1, baseline["trades"])
        model_expected = expected_per_trade * len(shadow.trades)
        pnl_deviation = live_pnl - model_expected
        live_win_rate = (
            sum(trade.pnl > 0 for trade in shadow.trades) / len(shadow.trades)
            if shadow.trades else 0.0
        )
        pnl_ratio = live_pnl / model_expected if model_expected > 0 else 0.0
        trade_rate_model = baseline["trades"] / model["normalization_checks"]["snapshots_checked"]
        trade_rate_live = len(shadow.trades) / max(1, len(snapshots))
        signal_drift = clamp_score(
            100.0 * min(1.0, abs(trade_rate_live - trade_rate_model) / max(0.001, trade_rate_model))
        )
        divergence = clamp_score(
            100.0 * (
                0.55 * min(1.0, abs(1.0 - pnl_ratio))
                + 0.25 * abs(live_win_rate - baseline["win_rate"])
                + 0.20 * signal_drift / 100.0
            )
        )

        period_trades = self._split_trades(shadow.trades)
        period_pnl = tuple(round(sum(trade.pnl for trade in part), 6) for part in period_trades)
        halfway = max(1, len(period_pnl) // 2)
        first = statistics.fmean(period_pnl[:halfway])
        second = statistics.fmean(period_pnl[halfway:]) if period_pnl[halfway:] else first
        decay_ratio = max(0.0, (first - second) / max(abs(first), 1.0))
        losing_recent = 1.0 if second <= 0 else 0.0
        edge_decay = clamp_score(100.0 * (0.7 * min(1.0, decay_ratio) + 0.3 * losing_recent))
        stability = coefficient_stability(list(period_pnl))
        moves = [
            abs(snapshots[index].yes_price - snapshots[index - 1].yes_price)
            for index in range(1, len(snapshots))
            if snapshots[index].market_id == snapshots[index - 1].market_id
        ]
        live_noise = statistics.fmean(moves) if moves else 0.0
        model_noise = self._model_noise(model)
        noise_ratio = live_noise / max(0.000001, model_noise)
        equity = [10_000.0]
        for trade in shadow.trades:
            equity.append(equity[-1] + trade.pnl)

        evidence = len(shadow.trades) >= self.config.minimum_trades
        caveats = []
        if features.mode is ReferenceMode.CAUSAL_PROXY:
            caveats.append("No independent live fair-value feed; reference probability is a causal price proxy.")
        if not evidence:
            caveats.append(
                f"Only {len(shadow.trades)} closed trades; at least {self.config.minimum_trades} are required."
            )

        coverage_ok = features.external_coverage >= 0.95
        if features.mode is ReferenceMode.EXTERNAL and not coverage_ok:
            caveats.append(
                f"Independent reference coverage is {features.external_coverage:.1%}; 95% is required."
            )

        if (
            evidence and features.mode is ReferenceMode.EXTERNAL and coverage_ok
            and live_pnl > 0 and divergence <= 35 and edge_decay <= 35 and stability >= 55
        ):
            verdict = "TRUE_ALPHA"
        elif live_pnl > 0 and divergence <= 65 and edge_decay <= 65:
            verdict = "WEAK_ALPHA"
        else:
            verdict = "NO_ALPHA"

        report = LiveValidationReport(
            session_fingerprint=LiveSessionStore.fingerprint(self.raw_ticks),
            session_start=self.ticks[0].timestamp,
            session_end=self.ticks[-1].timestamp,
            reference_mode=features.mode,
            external_reference_coverage=round(features.external_coverage, 6),
            snapshots=len(snapshots),
            decisions=len(shadow.decisions),
            trades=len(shadow.trades),
            live_simulated_pnl=round(live_pnl, 6),
            live_return_pct=round(live_pnl / 10_000.0, 8),
            max_drawdown=round(max_drawdown(equity), 8),
            model_expected_pnl=round(model_expected, 6),
            pnl_deviation=round(pnl_deviation, 6),
            divergence_score=divergence,
            signal_drift_score=signal_drift,
            edge_decay_score=edge_decay,
            stability_score=stability,
            noise_ratio=round(noise_ratio, 6),
            period_pnl=period_pnl,
            verdict=verdict,
            evidence_sufficient=evidence,
            caveats=tuple(caveats),
        )
        from .reporting import write_live_report
        write_live_report(report, shadow.decisions, shadow.trades, self.config.output_dir)
        return report

    def _split_trades(self, trades: list) -> list[list]:
        result = [[] for _ in range(self.config.periods)]
        if not trades:
            return result
        start, end = self.ticks[0].timestamp, self.ticks[-1].timestamp
        span = max(1.0, (end - start).total_seconds())
        for trade in trades:
            index = min(
                self.config.periods - 1,
                int(((trade.closed_at - start).total_seconds() / span) * self.config.periods),
            )
            result[index].append(trade)
        return result

    def _model_noise(self, model: dict) -> float:
        noise = [row["parameter"] for row in model.get("scenarios", []) if row["scenario"] == "noise"]
        return statistics.fmean(noise) if noise else 0.025
