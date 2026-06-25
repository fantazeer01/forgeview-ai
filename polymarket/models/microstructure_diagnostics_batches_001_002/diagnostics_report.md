# Combined Microstructure Diagnostics Batches 001-002

Decision: **DATASET_STILL_TOO_SMALL_OR_UNSTABLE**

This is a development-only diagnostic over proxy labels from Batch 001 and Batch 002. It is not production model training, not holdout evaluation, and not an alpha claim.

## Combined Data
- Rows analyzed: 426
- Windows analyzed: 142
- Assets: {'BTC': 142, 'ETH': 142, 'SOL': 142}
- Outcomes: {'UP': 213, 'DOWN': 213}
- Batches: {'batch_001': 213, 'batch_002': 213}
- Labels: proxy reference-window returns only
- Microstructure feature coverage: 8094 / 8094 cells (100.0000%)
- Microstructure missing cells: 0
- Core plus microstructure missing cells: 0

## Development Baselines
Chronological 70/30 split by atomic five-minute window group.

| Model | Eval rows | Log loss | Brier | Accuracy | ROC AUC |
|---|---:|---:|---:|---:|---:|
| yes_price_only | 129 | 0.546792 | 0.182709 | 0.7287 | 0.8055 |
| microstructure_only_diagnostic_logistic | 129 | 0.677837 | 0.241526 | 0.5659 | 0.6228 |
| yes_price_plus_microstructure_diagnostic_logistic | 129 | 0.610897 | 0.210249 | 0.6589 | 0.7295 |

Best diagnostic result: `yes_price_only` with evaluation log loss 0.546792 and Brier 0.182709.
YES price beaten on development evaluation: `False`.

## Per-Asset Evaluation
| Asset | Best model | YES log loss | YES+micro log loss | YES Brier | YES+micro Brier |
|---|---|---:|---:|---:|---:|
| BTC | yes_price_only | 0.561961 | 0.676765 | 0.190687 | 0.237563 |
| ETH | yes_price_only | 0.569312 | 0.584161 | 0.191059 | 0.198099 |
| SOL | yes_price_only | 0.509104 | 0.571766 | 0.166380 | 0.195086 |

## Information Value
Possible incremental features in the combined table: none
Stable possible incremental features across both batches: none
Features helping only one batch: quote_age_seconds, time_since_quote_update_seconds, repricing_velocity, consecutive_quote_stability, cross_asset_yes_dispersion
Unstable features: book_imbalance
Redundant with YES price: none

## Redundancy Highlights
- `spread_change` / `spread_compression`: corr -1.000000
- `yes_change_frequency_30s` / `no_change_frequency_30s`: corr 1.000000
- `time_since_quote_update_seconds` / `consecutive_quote_stability`: corr 0.999998
- `spread_change` / `spread_velocity`: corr 0.999996
- `spread_velocity` / `spread_compression`: corr -0.999996

## Holdout Status
Holdout outcomes read: false. Holdout evaluation run: false. Validation protocol modified: false.
