from __future__ import annotations

from dataclasses import replace

from polymarket.edge_engine.models import MarketSnapshot

from .metrics import max_drawdown, safe_stdev
from .models import ScenarioResult
from .simulator import SimulatorConfig, WindowSimulator


class WalkForwardEngine:
    def __init__(self, windows: int, simulator_config: SimulatorConfig) -> None:
        if windows < 2:
            raise ValueError("walk-forward testing requires at least 2 windows")
        self.windows = windows
        self.simulator_config = simulator_config

    def split(self, snapshots: list[MarketSnapshot]) -> list[list[MarketSnapshot]]:
        timestamps = sorted({row.timestamp for row in snapshots})
        if len(timestamps) < self.windows:
            raise ValueError("Not enough timestamps for requested walk-forward windows")
        buckets: list[list[MarketSnapshot]] = []
        for index in range(self.windows):
            start = index * len(timestamps) // self.windows
            end = (index + 1) * len(timestamps) // self.windows
            selected = set(timestamps[start:end])
            buckets.append([row for row in snapshots if row.timestamp in selected])
        return buckets

    def run(
        self,
        snapshots: list[MarketSnapshot],
        run_id: str,
        scenario: str,
        parameter: float,
        latency_steps: int | None = None,
    ) -> ScenarioResult:
        config = self.simulator_config
        if latency_steps is not None:
            config = replace(config, latency_steps=latency_steps)
        simulator = WindowSimulator(config)
        window_results = []
        trades = []
        for window_id, window in enumerate(self.split(snapshots), 1):
            result, window_trades = simulator.run(window, run_id, window_id)
            window_results.append(result)
            trades.extend(window_trades)
        pnls = [window.pnl for window in window_results]
        wins = sum(trade.pnl > 0 for trade in trades)
        cumulative = [config.initial_cash]
        for pnl in pnls:
            cumulative.append(cumulative[-1] + pnl)
        return ScenarioResult(
            run_id=run_id,
            scenario=scenario,
            parameter=parameter,
            pnl=round(sum(pnls), 6),
            max_drawdown=round(max(max(row.max_drawdown for row in window_results), max_drawdown(cumulative)), 8),
            trades=len(trades),
            win_rate=round(wins / len(trades), 6) if trades else 0.0,
            windows_profitable_ratio=round(sum(pnl > 0 for pnl in pnls) / len(pnls), 6),
            window_pnl_stdev=round(safe_stdev(pnls), 6),
            windows=tuple(window_results),
            trade_log=tuple(trades),
        )
