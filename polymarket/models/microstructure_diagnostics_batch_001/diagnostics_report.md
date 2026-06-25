# Microstructure Diagnostics Batch 001

Decision: **DATASET_TOO_SMALL_OR_UNSTABLE**

This is a development-only diagnostic over Batch 001 proxy labels. It is not a production model, not holdout evaluation, and not an alpha claim.

## Data

- Rows analyzed: 213
- Assets: {'BTC': 71, 'ETH': 71, 'SOL': 71}
- Labels: 213 proxy, 0 authoritative
- Microstructure feature coverage: 213 / 213 complete rows
- Microstructure missing cells: 0 / 4047
- Raw required microstructure coverage floor: 100.00%

## Development Baselines

Chronological 70/30 split within Batch 001 only.

| Model | Eval rows | Log loss | Brier | Accuracy | ROC AUC |
|---|---:|---:|---:|---:|---:|
| yes_price_only | 64 | 0.568340 | 0.192367 | 0.6875 | 0.7882 |
| microstructure_only_diagnostic_logistic | 64 | 0.628730 | 0.220724 | 0.6250 | 0.7395 |
| yes_price_plus_microstructure_diagnostic_logistic | 64 | 0.594523 | 0.203701 | 0.7188 | 0.7672 |

Best diagnostic result: `yes_price_only` with evaluation log loss 0.568340 and Brier 0.192367.
YES price beaten on development evaluation: `False`.

## Information Value

Possible incremental features after residualizing against YES price:
- `cross_asset_yes_dispersion`: partial corr 0.132849, corr YES -0.063885

Redundant with YES price:
- `book_imbalance`: corr YES 0.845073

Unstable features:
- None exceeded the fixed one-standard-deviation half-sample shift threshold.

## Redundancy Highlights

- `yes_change_frequency_30s` / `no_change_frequency_30s`: corr 1.000000
- `spread_change` / `spread_compression`: corr -1.000000
- `time_since_quote_update_seconds` / `consecutive_quote_stability`: corr 0.999998
- `spread_change` / `spread_velocity`: corr 0.999997
- `spread_velocity` / `spread_compression`: corr -0.999997
- `bid_ask_spread` / `spread_velocity`: corr 0.945438
- `bid_ask_spread` / `spread_change`: corr 0.945052
- `bid_ask_spread` / `spread_compression`: corr -0.945052
- `quote_age_seconds` / `consecutive_quote_stability`: corr 0.912116
- `quote_age_seconds` / `time_since_quote_update_seconds`: corr 0.912101

## Holdout Status

Holdout outcomes read: false. Holdout evaluation run: false. Validation protocol modified: false.
