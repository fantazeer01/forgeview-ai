# Polymarket Research Synthesis v1

## Decision

The fastest credible path to a first profitable strategy is **Wallet Intelligence**, specifically a leakage-safe chronological validation of the four wallets already classified as above-baseline on resolved fast-crypto positions. Repricing remains valuable research evidence, but it is not the primary branch because measured economics turn negative at the observed two-second entry delay plus cost. Further infrastructure and credential work is stopped until a public-only candidate survives a cost-aware paper gate.

This synthesis used only existing public research artifacts and datasets. The sealed holdout was not opened or evaluated.

## Evidence Base

- Outcome prediction: 741 train and 153 validation rows. YES price was the best model; no tested feature group improved both log loss and Brier score.
- Microstructure: 426 rows, 142 each for BTC/ETH/SOL, 19 features at 100% coverage. YES price remained best; no stable incremental feature was found.
- Repricing: 338 scientifically valid signals across 48 hours and three sessions, 71.30% win rate, +0.032405 recorded after-slippage expectancy, +10.953 P&L and 0.875 max drawdown. A 1,000-trial matched random baseline on the first 172 signals was strongly inferior (one-sided p=0.000999), but the fourth session supplied 64.82% of aggregate P&L and SOL supplied 46.37%.
- Executable-cost stress: immediate executable quote replay remained positive (+0.035944 expectancy), modeled one-second delay remained positive (+0.022508), but actual two-second entry plus 0.005 cost was negative (-0.009810 expectancy, -3.3157 P&L, 3.9548 max drawdown). Repricing is real enough to preserve and too latency-sensitive to prioritize.
- Wallet Intelligence: 5,765 normalized public activity rows, 2,135 lifecycle positions and 1,788 resolved fast-crypto positions across 28 evaluated wallets. Four wallets passed above-baseline evidence gates with 258 resolved positions and match rates from 0.714286 to 0.833333. Three wallets were below baseline, 13 consistent with baseline and eight insufficient, so indiscriminate copy-following is rejected.
- Wallet observability: only two eligible prospective five-minute trades exist. Their decision windows were 44.959 and 85.106 seconds. This is encouraging but explicitly inconclusive and not yet a copyability claim.

## Exploitable Patterns Already Present

1. **Persistent wallet heterogeneity:** four wallets clear above-baseline gates while three are significantly below. Wallet identity and specialization contain measurable information; the aggregate wallet population is not the strategy.
2. **Specialist structure:** three above-baseline wallets specialize in one asset, while one has 18 resolved positions in each of BTC, ETH and SOL with an 0.833333 match rate. Asset-conditioned wallet skill is testable immediately.
3. **Potential consensus:** multiple skilled wallets overlap in fast crypto. Agreement may reduce idiosyncratic-wallet risk, but it has not yet been measured and must remain a secondary preregistered test.
4. **Repricing signal quality:** frozen lag events are not explained by matched random timing, but their monetization requires entry materially faster than the current two-second observed path.
5. **Negative controls:** YES price absorbs tested final-outcome and standalone microstructure information. These branches should not consume near-term engineering time.

## Highest-Probability Path To First Profit

Run one existing-data-only, chronological Wallet Specialist Alpha Validation sprint. Freeze the four candidate wallets before analysis; construct non-overlapping market-time folds; compare each wallet and asset-specialist rule against YES price, random side and population-wallet baselines; prohibit same-market leakage; estimate public-observation delays and conservative entry costs; and report both standalone and consensus variants without parameter search. Advance only if skill persists out of sample, survives cost/delay assumptions and is not dominated by one wallet, asset, date or market.

This is a validation sprint, not a trading authorization. If it passes, the next stage is a bounded public-only prospective shadow run. If it fails, test the slower repricing derivative, not more wallet infrastructure.

## Portfolio Roadmap

1. **Now:** Wallet Specialist Alpha Validation using existing data only.
2. **Pass condition:** positive chronological out-of-sample value versus all preregistered baselines, stable across at least two wallets/assets or a justified specialist partition, and robust to observation delay and conservative spread/slippage.
3. **Then:** bounded prospective public shadow collection focused on validated wallets and minute-scale actionable windows.
4. **Only after shadow pass:** minimal execution feasibility work for that strategy.
5. **Fallback:** test slower 30-180 second continuation/reversion labels from existing Repricing sessions.
6. **Deferred:** credentialed calibration, host governance and sub-second Repricing execution.

## Scientific Boundaries

The wallet result is retrospective and selected from a bounded public sample. It is exposed to selection bias, incomplete history, correlated markets, publication delay and execution uncertainty. Match rate is not realized P&L. The next sprint must attempt to disprove the specialist hypothesis and may not promote a strategy based on in-sample wallet ranking.
