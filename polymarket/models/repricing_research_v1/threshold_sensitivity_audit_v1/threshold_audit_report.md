# Repricing Threshold Sensitivity Audit v1

Status: completed. This audit used only existing public sessions and existing repricing datasets. No capture was launched, no model was trained, no holdout outcomes were inspected, and the frozen validation protocol and evidence gates were not changed.

## Current Pipeline

Current capture settings are external move threshold 8 bps, repricing ratio 0.50, minimum confidence 0.65, detector expiry floor 30 seconds, and entry-time guard 60 seconds. The repricing dataset accepts `qualified_external_move_not_repriced` and `confidence_below_threshold`, requires at least 35 seconds to expiry, applies non-overlap by market and side, and records 30/60/120/180 second horizon coverage.

The persisted current repricing smoke dataset contains 28 signals at 2.1333 signals/hour, with BTC/ETH/SOL 5/8/15 and YES/NO 5/23.

## Dominant Bottleneck

The dominant detector-level removal filter is `external_move_below_threshold` with 36,465 observations, or 56.86% of candidate observations. The threshold family with the largest signal-count range overall is `horizon_filter`, because requiring full 180-second horizon coverage removes every current signal. Among entry-admission thresholds, `external_move_threshold_bps` has the largest signal-density effect.

YES scarcity is primarily caused by directional external-move distribution after strict admission filters. BTC/ETH scarcity is caused by asset-level candidate density after strict thresholds, with BTC lowest and SOL highest in the current smoke sample.

## Strata

- Conservative: 48 signals, 3.08/h, BTC/ETH/SOL 14/16/18, YES/NO 9/39, horizons 30/60/120/180 100.0%/89.6%/75.0%/0.0%, candidate retention 0.405%.
- Balanced: 61 signals, 3.92/h, BTC/ETH/SOL 17/20/24, YES/NO 14/47, horizons 30/60/120/180 100.0%/98.4%/80.3%/0.0%, candidate retention 0.577%.
- Aggressive: 124 signals, 7.97/h, BTC/ETH/SOL 28/33/63, YES/NO 44/80, horizons 30/60/120/180 100.0%/96.8%/82.3%/0.0%, candidate retention 1.168%.

## Recommendation

Recommend freezing the `balanced` collection stratum for future evidence gathering, subject to explicit authorization before any new capture. The recommendation is based on signal density, asset/side balance, and horizon coverage, not paper P&L.

Balanced parameters: external move threshold 6 bps, repricing ratio 0.65, minimum confidence 0.45, minimum dataset expiry 60 seconds, max holding 180 seconds, accepted reasons `qualified_external_move_not_repriced` and `confidence_below_threshold`.

## Safety

The audit did not optimize for historical profitability. Paper P&L was not used to choose the recommended stratum. Repricing edge claims remain prohibited until the unchanged evidence gates are met and a separate prospective or untouched repricing validation period succeeds under executable-cost assumptions.
