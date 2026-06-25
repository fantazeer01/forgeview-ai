# Baseline Model Cards

Scope: development train/validation evaluation only.
Holdout outcomes were not read.

## constant_prior

Constant probability equal to train UP frequency.

- Validation log loss: 0.6997678936
- Validation Brier score: 0.2533088175
- Validation accuracy: 0.4183006536
- Validation ROC AUC: 0.5

## asset_prior

Per-asset train UP frequency.

- Validation log loss: 0.7002913821
- Validation Brier score: 0.2535657112
- Validation accuracy: 0.4640522876
- Validation ROC AUC: 0.5

## yes_price

Polymarket YES quote at feature time; no fitting.

- Validation log loss: 0.6171276489
- Validation Brier score: 0.2166825163
- Validation accuracy: 0.6274509804
- Validation ROC AUC: 0.6720505618

## logistic_regression

L2-regularized interpretable logistic regression with fixed features and train-only median/scaling.

- Validation log loss: 0.6678251082
- Validation Brier score: 0.2382507646
- Validation accuracy: 0.5620915033
- Validation ROC AUC: 0.6462429775

## Limitations

- One fixed development period; no final holdout result.
- No P&L optimization or execution-cost conclusion.
- No alpha or production-readiness claim.
