# Baseline Probability Model v1 - Development Validation

Verdict: **NO_EDGE_FOUND_YET**
Best validation model: **yes_price**

The final holdout remained sealed and was not evaluated.

| Model | Log loss | Brier | Accuracy | AUC |
|---|---:|---:|---:|---:|
| constant_prior | 0.699768 | 0.253309 | 0.4183 | 0.5 |
| asset_prior | 0.700291 | 0.253566 | 0.4641 | 0.5 |
| yes_price | 0.617128 | 0.216683 | 0.6275 | 0.6720505618 |
| logistic_regression | 0.667825 | 0.238251 | 0.5621 | 0.6462429775 |

## Advancement

Passes frozen rule: **False**

## Next research action

Do not open the holdout. Diagnose temporal and per-asset validation failures, then pre-register one targeted feature ablation or collect a new independent development period.
