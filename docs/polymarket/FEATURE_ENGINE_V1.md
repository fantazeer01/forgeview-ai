# Polymarket Feature Engine v1

## Purpose

Feature Engine v1 converts completed BTC, ETH, and SOL five-minute market
sessions from Edge Engine v5 into a deterministic historical modelling
dataset. It is an offline research component: it contains no execution,
wallet, private-key, or order-placement code.

## Commands

Run from `D:\ForgeViewAI`:

```powershell
python -m polymarket.feature_engine build
python -m polymarket.feature_engine inspect
```

Optional paths and feature timing:

```powershell
python -m polymarket.feature_engine build `
  --runs-root polymarket/runs/v5 `
  --output-root polymarket/data/training `
  --feature-anchor-seconds 60 `
  --boundary-tolerance-seconds 15
```

Public completeness controls:

```powershell
--asof-max-age-seconds 15
--max-missing-features-per-row 2
```

As-of lookups use only observations at or before the feature timestamp and
reject values older than 15 seconds relative to the requested lookback point.
Rows with more than two unavailable modelling features are excluded rather
than filled with zeros, means, future values, or synthetic observations.

## Observation and label policy

Each row represents one completed five-minute market. Feature values are
anchored at the first saved Polymarket snapshot at or after 60 seconds from
window open. This leaves approximately four minutes between feature
observation and resolution and prevents end-of-window information leakage.

Feature Engine now prefers Resolution Engine's saved authoritative Polymarket
outcome. By default, a window without an authoritative outcome is excluded.

For pipeline testing only, `--allow-proxy-labels` enables the saved external
reference feed:

- `UP = 1` when the closing reference price is greater than or equal to the
  opening reference price;
- `DOWN = 0` otherwise;
- both boundary observations must be within 15 seconds of the market boundary;
- the proxy label provenance is stored as `reference_window_return`;
- authoritative labels are stored as `polymarket_gamma_resolved`.

Windows without a permitted label, complete lifecycle, or anchor
snapshot are excluded and counted by reason in `feature_summary.json`.

## Dataset schema

Identifiers and timing:

- `market_id`, `asset`, `market_source` (`public` or `mock`)
- `window_start`, `window_end`, `feature_timestamp`
- `market_age_seconds`, `seconds_to_expiry`

External-price features:

- `return_5s`, `return_15s`, `return_30s`, `return_60s`
- `momentum_short`: five-second return minus fifteen-second return
- `momentum_medium`: fifteen-second return minus sixty-second return
- `volatility_30s`, `volatility_60s`: population standard deviation of
  consecutive log returns

Polymarket and lag features:

- `yes_price`, `no_price`
- `yes_no_spread`: signed YES price minus NO price
- `probability_change_15s`, `probability_change_30s`
- `lag_score`, `confidence_score`

Lifecycle features:

- `detection_delay`
- `early_window_flag`: detection delay no greater than 15 seconds
- `late_window_flag`: detection delay greater than 60 seconds

For sessions created before explicit lifecycle tracking, `detection_delay` is
recovered from the earliest saved market-discovery event relative to window
open. A market discovered before opening receives a delay of zero.

Labels and provenance:

- `outcome`
- `resolution_timestamp`
- `label_source`
- `source_session`

## Outputs

Files are written to `polymarket/data/training/`:

```text
dataset.csv
dataset.parquet
feature_summary.json
missingness_diagnostics.json
```

The summary contains sample and feature counts, per-column missing values,
asset counts, UP/DOWN balance, a pairwise Pearson correlation matrix, label
policy, source-session count, and excluded-window reasons.

The missingness diagnostics report completeness before and after filtering,
missing cells by feature and session, recovered detection delays, and every
excluded row with its exact missing-feature list.

`dataset.parquet` is standards-compliant, uncompressed Parquet written without
a mandatory third-party dependency.

## Limitations

- Proxy labels can disagree with Polymarket's Chainlink-based settlement and
  must not be used unless explicitly enabled.
- REST polling cadence limits the precision of short lookback features.
- Sparse sessions can produce missing volatility or return values.
- Correlations are descriptive only and do not establish predictive power.

## Completeness repair result

The June 19, 2026 authoritative rebuild recovered detection delay for all 91
candidate rows from saved first-seen evidence. Applying the 15-second as-of
age limit and maximum-two-missing-features policy excluded 29 sparse rows.

The resulting clean dataset contains 62 public rows with 98.71% feature
completeness. Sixteen feature cells remain missing and are explicitly recorded;
no values were imputed.
