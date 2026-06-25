# Repricing-Focused Public Evidence Collection Plan v1

Status: completed plan only. No capture campaign was launched.

## Current Evidence

The current Repricing Research v1 smoke sample contains 28 paper signals over 13.1255 observed hours, or 2.1333 signals/hour. The aggregate result remains positive but insufficient: 57.14% win rate, +0.0145 after-slippage expectancy per signal, +0.4065 after-slippage P&L, and 0.4050 max drawdown.

Signal balance is the main bottleneck: BTC / ETH / SOL counts are 5 / 8 / 15, while YES / NO counts are 5 / 23. The branch remains `INSUFFICIENT_SMOKE_ONLY`.

## Bottlenecks

The two existing schema-v1 sessions produced 63,891 lag measurements, but only 87 confidence-below-threshold lag events and zero fully qualified lag events. The paper simulator then compressed those candidates to 28 entries because it avoids overlapping positions per market and side.

Reason distribution:

- external move below threshold: 37,843 (59.23%);
- Polymarket already repriced: 19,565 (30.62%);
- near expiry insufficient time: 6,396 (10.01%);
- confidence below threshold: 87 (0.14%);
- qualified external move not repriced: 0.

The restrictive filters are useful for purity but too slow for evidence collection. YES-side scarcity is the binding weak-evidence constraint at current rates.

## Signal Rate Estimates

- Current strict baseline: 2.13 signals/hour.
- Complete market-lifecycle capture with unchanged replay rules: about 3.0 signals/hour.
- Precommitted threshold-sweep stratum after freezing density and balance rules: about 4.5 signals/hour.
- Separate short-horizon near-expiry stratum: about 6.0 signals/hour, but it must remain tagged separately.
- Additional longer expiry horizons: about 1.5 incremental signals/hour until measured.

These are planning estimates, not edge claims.

## Evidence Roadmap

| Level | Target | Count-only 12h sessions | Balance-adjusted 12h sessions | Binding current constraint |
| --- | ---: | ---: | ---: | --- |
| Weak | 100 | 4 | 8 | YES_side_balance |
| Moderate | 300 | 12 | 22 | YES_side_balance |
| Strong development | 1000 | 40 | 77 | YES_side_balance |

The fastest statistically sound route is to run a no-capture threshold sensitivity audit first, then collect independent 12-hour public-only repricing-focused sessions using frozen entry strata and strict replay/continuity gates.

## Recommended Strategy

1. Run `Run Repricing Threshold Sensitivity Audit v1` on existing public sessions only.
2. Freeze one baseline-compatible lag threshold stratum selected for signal density and asset/side balance, not P&L.
3. Collect independent 12-hour public-only BTC/ETH/SOL sessions only after that successor task is complete and explicitly authorized.
4. Stop at weak evidence only when all weak gates pass: at least 100 signals, 40 observed hours, 3 sessions, 25 per asset, 35 per side, expectancy after slippage >= 0.005, and continuity/replay gates pass.
5. Continue to moderate and strong only if chronological, asset, and side stability remain positive under stress.

## Safety

This plan did not inspect sealed holdout outcomes, run holdout evaluation, train production models, implement live trading, connect wallets, launch a campaign, merge data into canonical outcome-training paths, or modify the validation protocol.
