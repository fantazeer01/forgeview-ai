# Model Card: logistic_regression

L2-regularized interpretable logistic regression with fixed features and train-only median/scaling.

## Authorized scope

Development train/validation evaluation only. The sealed holdout was not read.

## Validation metrics

- Log loss: 0.6678251082
- Brier score: 0.2382507646
- Accuracy: 0.5620915033
- ROC AUC: 0.6462429775
- Calibration error: 0.1515844667

## Limitations

- No final holdout evidence.
- No execution-cost or P&L optimization.
- No proven-edge or production-readiness claim.
