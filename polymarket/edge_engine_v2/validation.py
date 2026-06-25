from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import statistics

from polymarket.edge_engine.scoring import EdgeScorer
from polymarket.edge_engine.models import MarketSnapshot

from .data import ReplayStore
from .metrics import clamp_score, coefficient_stability, downside_ratio
from .models import ValidationReport
from .perturbation import perturb_snapshots
from .reporting import write_report
from .simulator import SimulatorConfig
from .walkforward import WalkForwardEngine


@dataclass(frozen=True)
class ValidationConfig:
    seed: int = 42
    windows: int = 6
    noise_levels: tuple[float, ...] = (0.01, 0.025, 0.05)
    dropout_levels: tuple[float, ...] = (0.05, 0.15)
    signal_lags: tuple[int, ...] = (1, 2, 4)
    execution_latencies: tuple[int, ...] = (0, 1, 3)
    simulator: SimulatorConfig = SimulatorConfig()
    output_dir: Path = Path("polymarket/runs/v2/latest")


class AlphaValidationSystem:
    def __init__(self, snapshots: list[MarketSnapshot], config: ValidationConfig | None = None) -> None:
        if not snapshots:
            raise ValueError("Validation requires at least one snapshot")
        self.snapshots = sorted(snapshots, key=lambda row: (row.timestamp, row.market_id))
        self.config = config or ValidationConfig()
        self.walkforward = WalkForwardEngine(self.config.windows, self.config.simulator)

    def run(self) -> ValidationReport:
        checks = self._normalization_checks()
        baseline = self.walkforward.run(self.snapshots, "baseline", "baseline", 0.0)
        scenarios = []

        for index, noise in enumerate(self.config.noise_levels):
            data = perturb_snapshots(self.snapshots, self.config.seed + 100 + index, price_noise_std=noise)
            scenarios.append(self.walkforward.run(data, f"noise-{noise}", "noise", noise))
        for index, dropout in enumerate(self.config.dropout_levels):
            data = perturb_snapshots(self.snapshots, self.config.seed + 200 + index, signal_dropout=dropout)
            scenarios.append(self.walkforward.run(data, f"dropout-{dropout}", "dropout", dropout))
        for lag in self.config.signal_lags:
            data = perturb_snapshots(self.snapshots, self.config.seed, signal_lag_steps=lag)
            scenarios.append(self.walkforward.run(data, f"signal-lag-{lag}", "signal_lag", float(lag)))
        for latency in self.config.execution_latencies:
            scenarios.append(
                self.walkforward.run(
                    self.snapshots, f"latency-{latency}", "execution_latency",
                    float(latency), latency_steps=latency,
                )
            )

        window_pnls = [window.pnl for window in baseline.windows]
        consistency = clamp_score(baseline.windows_profitable_ratio * 100.0)
        stability = coefficient_stability(window_pnls)
        noise_runs = [row for row in scenarios if row.scenario in {"noise", "dropout"}]
        lag_runs = [row for row in scenarios if row.scenario == "signal_lag"]
        latency_runs = [row for row in scenarios if row.scenario == "execution_latency"]
        noise_resilience = clamp_score(
            100.0 * sum(downside_ratio(row.pnl, baseline.pnl) for row in noise_runs) / max(1, len(noise_runs))
        )
        drawdown_control = clamp_score(100.0 * (1.0 - min(1.0, baseline.max_drawdown / 0.20)))
        robustness = clamp_score(
            0.30 * consistency
            + 0.25 * noise_resilience
            + 0.25 * stability
            + 0.20 * drawdown_control
        )

        noise_ok = bool(noise_runs) and all(row.pnl > 0 for row in noise_runs)
        sufficient_trades = baseline.trades >= self.config.windows
        periods_ok = (
            baseline.windows_profitable_ratio >= 0.60
            and baseline.pnl > 0
            and sufficient_trades
        )
        latency_ok = bool(latency_runs) and all(row.pnl > 0 for row in latency_runs)
        lag_ok = (
            bool(lag_runs)
            and sum(row.pnl > 0 for row in lag_runs) / len(lag_runs) >= (2.0 / 3.0)
        )
        verdict = (
            "POTENTIAL_ALPHA"
            if robustness >= 60 and noise_ok and periods_ok and latency_ok and lag_ok
            else "OVERFIT_OR_INCONCLUSIVE"
        )
        report = ValidationReport(
            dataset_fingerprint=ReplayStore.fingerprint(self.snapshots),
            # Dataset time makes the complete report reproducible byte-for-byte.
            generated_at=max(row.timestamp for row in self.snapshots),
            seed=self.config.seed,
            baseline=baseline,
            scenarios=tuple(scenarios),
            consistency_score=consistency,
            noise_resilience_score=noise_resilience,
            profitability_stability_score=stability,
            drawdown_control_score=drawdown_control,
            scenario_pnl_variance=round(
                statistics.pvariance([row.pnl for row in scenarios]), 6
            ) if len(scenarios) > 1 else 0.0,
            robustness_score=robustness,
            verdict=verdict,
            answers={
                "noise": noise_ok,
                "time_periods": periods_ok,
                "execution_delay": latency_ok,
                "signal_lag": lag_ok,
            },
            normalization_checks=checks,
        )
        write_report(report, self.config.output_dir)
        return report

    def _normalization_checks(self) -> dict[str, object]:
        scorer = EdgeScorer()
        invalid = 0
        scores = []
        for row in self.snapshots:
            components = (
                row.yes_price, row.reference_probability, row.volume_spike,
                row.momentum, row.stability,
            )
            if any(not 0.0 <= value <= 1.0 for value in components):
                invalid += 1
            score = scorer.score(row).score
            scores.append(score)
            if not 0.0 <= score <= 1.0:
                invalid += 1
        if invalid:
            raise ValueError(f"Normalization validation failed for {invalid} values")
        return {
            "passed": True,
            "snapshots_checked": len(self.snapshots),
            "score_min": min(scores),
            "score_max": max(scores),
            "weight_sum": 1.0,
            "minimum_baseline_trades_required": self.config.windows,
        }
