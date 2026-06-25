# Baseline Failure Diagnostics v1

Status: Complete  
Conclusion: `FEATURE_SET_INCOMPLETE`  
Date: June 23, 2026

## Scope

The diagnostics used only the frozen 741-row train split and 153-row
validation split. The final holdout remained sealed. No hyperparameters,
model families, P&L rules, or trading logic were optimized.

## Main result

None of the eight fixed feature-group tests improved both validation log loss
and Brier score over raw Polymarket YES price.

| Feature group | Log loss | Brier | Delta log loss vs YES |
|---|---:|---:|---:|
| YES calibration | 0.632043 | 0.223510 | +0.014916 |
| Market only | 0.634155 | 0.224353 | +0.017028 |
| External only | 0.676432 | 0.240243 | +0.059305 |
| Lag only | 0.679738 | 0.243078 | +0.062610 |
| YES + external | 0.635887 | 0.224825 | +0.018759 |
| YES + lag | 0.635783 | 0.225521 | +0.018655 |
| YES + market dynamics | 0.634217 | 0.224359 | +0.017090 |
| Combined baseline | 0.667825 | 0.238251 | +0.050697 |

Positive deltas are worse than YES price.

## Findings

- Logistic predictions beat YES price on 71 of 153 individual rows, but lose
  in aggregate because the errors on the other 82 rows are larger.
- YES price wins on both primary metrics for BTC, ETH, and SOL separately.
- YES price wins in every segment with at least 20 rows.
- The only segment win is eight medium-lag rows, which is insufficient for a
  regime-specific signal claim.
- `yes_price` and `yes_no_spread` have correlation 1.0 and duplicate the same
  information.
- `detection_delay` and `late_window_flag` correlate at 0.9797.
- Every validation feature row is in the early-window anchor, so the current
  dataset cannot test middle- or late-window behavior.
- Short-return and probability-change distributions drift materially between
  train and validation. `return_15s` changes outcome-correlation sign.
- Validation rows have complete current features, so missingness does not
  explain the failure.

## Interpretation

The current feature set contains outcome information sufficient to beat naive
class priors, but does not add stable incremental probability information over
the market's own YES price. The inputs are mostly single-time snapshots and
derived returns. They omit the market microstructure needed to identify
whether Polymarket is actively repricing or genuinely stale.

## Exactly one recommended experiment

Implement Market Microstructure Feature Capture v1 for:

- best-bid/ask depth;
- quote age;
- signed order-flow proxy;
- repricing velocity;
- probability acceleration;
- synchronized cross-asset lead/lag.

After implementation, collect a new independent development period and test
one pre-registered YES-plus-microstructure logistic model. Do not open the
existing holdout.
