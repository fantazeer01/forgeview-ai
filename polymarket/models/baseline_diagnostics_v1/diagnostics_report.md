# Baseline Failure Diagnostics v1

Conclusion: **FEATURE_SET_INCOMPLETE**

The final holdout remained sealed and was not evaluated.

## Strongest finding

No fixed current feature group improves both log loss and Brier score over YES price in aggregate.

## Weakest area

Current features are mostly single-timestamp summaries; they omit order flow, depth, quote age, and repricing velocity.

## Fixed feature-group tests

| Group | Log loss | Brier | Delta LL vs YES | Delta Brier vs YES |
|---|---:|---:|---:|---:|
| yes_calibration | 0.632043 | 0.223510 | +0.014916 | +0.006827 |
| market_only | 0.634155 | 0.224353 | +0.017028 | +0.007671 |
| external_only | 0.676432 | 0.240243 | +0.059305 | +0.023560 |
| lag_only | 0.679738 | 0.243078 | +0.062610 | +0.026395 |
| yes_plus_external | 0.635887 | 0.224825 | +0.018759 | +0.008142 |
| yes_plus_lag | 0.635783 | 0.225521 | +0.018655 | +0.008839 |
| yes_plus_market_dynamics | 0.634217 | 0.224359 | +0.017090 | +0.007677 |
| combined_baseline | 0.667825 | 0.238251 | +0.050697 | +0.021568 |

## Decision

Build Market Microstructure Feature Capture v1 for quote depth, quote age, signed order-flow proxy, repricing velocity, and probability acceleration; collect a new independent development period before fitting one pre-registered YES-plus-microstructure logistic model.
