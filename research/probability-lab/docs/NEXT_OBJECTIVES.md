# Next Objectives

## Immediate

Run the hardened recorder continuously and monitor collection quality.

Operational checks:

- Confirm each market rollover is logged with `MARKET_SWITCH`.
- Track complete, partial, and error row rates.
- Track effective sampling cadence during API degradation.
- Restart safely after host or network interruption.
- Keep every recorder output on `D:`.

## Data Milestones

1. Reach 30 resolved real-ask trades across the predefined v5 setups.
2. Continue collection toward 100 or more resolved trades.
3. Track missing-ask rate, partial-row rate, and effective sampling cadence.
4. Preserve exact model scalers and frozen model metadata.

## Validation Milestones

1. Re-run v6 using exact v3 preprocessing artifacts.
2. Report ROI, PnL, win rate, and drawdown by timing bucket and threshold.
3. Separate UP and DOWN performance.
4. Add fee, size, spread, latency, and slippage sensitivity.
5. Require positive performance across time windows before confirmation.

## Decision Rule

Continue research while the executable sample is small. Do not trade or
connect a wallet. Real deployment remains out of scope until real-ask edge is
confirmed on a sufficiently large out-of-sample dataset.
