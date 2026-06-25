# Baseline Probability Model v1

Status: Complete - `NO_EDGE_FOUND_YET`  
Evaluation date: June 23, 2026

## Scope

This development evaluation used only the frozen 741-row train split and
153-row validation split. The 158-row final holdout remained sealed and its
outcomes were not read.

Run and verify:

```powershell
python -m polymarket.baseline_model run
python -m polymarket.baseline_model verify
```

Outputs are stored in `polymarket/models/baseline_v1/`.

## Models

- constant training class prior;
- asset-specific training class prior;
- Polymarket YES price;
- fixed-feature L2-regularized logistic regression.

The logistic model uses train-only median imputation and standardization. No
hyperparameter search, tree model, P&L optimization, or validation-driven
feature search was performed.

## Validation result

| Model | Log loss | Brier | Accuracy | ROC AUC |
|---|---:|---:|---:|---:|
| Constant prior | 0.699768 | 0.253309 | 0.4183 | 0.5000 |
| Asset prior | 0.700291 | 0.253566 | 0.4641 | 0.5000 |
| Polymarket YES price | 0.617128 | 0.216683 | 0.6275 | 0.6721 |
| Logistic regression | 0.667825 | 0.238251 | 0.5621 | 0.6462 |

Logistic regression beats both prior baselines but does not beat Polymarket
YES price on either primary metric. The deficit is present for BTC, ETH, and
SOL. Its train-to-validation deterioration is also larger than the YES-price
baseline.

## Verdict

`NO_EDGE_FOUND_YET`

The advancement rule failed. The final holdout must remain sealed. The next
research step is a pre-registered diagnosis of temporal and feature-group
failure on development data only, not another broad model search.
