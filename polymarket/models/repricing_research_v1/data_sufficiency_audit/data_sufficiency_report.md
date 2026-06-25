# Repricing Research v1 Data Sufficiency Audit

Status: **insufficient smoke-only evidence**

This audit uses only the existing Repricing Research v1 short replay labels. It does not inspect holdout outcomes, run holdout evaluation, train production models, implement live trading, connect wallets, or launch a campaign.

## Current Sample
- Total signals: 28
- Signals by asset: {'ETH': 8, 'BTC': 5, 'SOL': 15}
- Signals by side: {'YES': 5, 'NO': 23}
- Signals by exit reason: {'repricing_target': 16, 'stop_loss': 8, 'timeout': 4}
- Hours observed: 13.1255
- Signals per hour: 2.1333
- Win rate: 57.14%
- Expectancy after slippage: 0.014518
- P&L after slippage: 0.406500
- Max drawdown: 0.405000
- Per-signal P&L std dev: 0.094838
- Per-signal P&L variance: 0.008994
- Per-signal P&L median / q25 / q75: 0.017500 / -0.050000 / 0.040000

## Sufficiency Decision
Current data is sufficient for repricing code-path diagnostics and basic label-distribution review only. It is not sufficient for model development, shadow strategy validation, or any repricing edge claim.

## Sample Targets
| Evidence level | Signals | Hours | Sessions | Signals/asset | Signals/side | Min expectancy |
|---|---:|---:|---:|---:|---:|---:|
| weak_development_evidence | 100 | 40 | 3 | 25 | 35 | 0.005 |
| moderate_development_evidence | 300 | 120 | 6 | 75 | 100 | 0.008 |
| strong_development_evidence | 1000 | 400 | 20 | 250 | 350 | 0.010 |

## Evidence Gates
- Weak evidence: at least 100 signals, 40 observed hours, 3 independent sessions, 25 signals per asset, 35 per side, expectancy after slippage at least 0.005, and positive expectancy in at least 2 of 3 assets.
- Moderate evidence: at least 300 signals, 120 observed hours, 6 sessions, 75 signals per asset, 100 per side, expectancy at least 0.008, positive in all assets and both sides, and positive in at least 4 chronological folds.
- Strong development evidence: at least 1,000 signals, 400 observed hours, 20 sessions, 250 signals per asset, 350 per side, expectancy at least 0.010 after stress, no single asset/session above 40% of P&L, and positive in at least 80% of chronological folds.

## Recommended Next Action
Collect more repricing-focused public data only after a separate capture plan is approved. Do not adjust thresholds for edge claims, train models, or launch a campaign from this audit. The immediate successor should design a precommitted repricing evidence collection plan with explicit gates and no automatic capture.

## Holdout Status
Holdout outcomes inspected: false. Holdout evaluation run: false. Validation protocol modified: false.
