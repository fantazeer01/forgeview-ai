# Time-Ordered Holdout and Baseline Validation Protocol v1

Status: Frozen  
Effective date: June 23, 2026

## Purpose

This protocol fixes the experiment design before any probability model is
fitted. It prevents temporal leakage, preserves a one-time untouched holdout,
and precommits the baseline comparisons and acceptance rules.

## Command

```powershell
python -m polymarket.validation_protocol freeze
python -m polymarket.validation_protocol inspect
python -m polymarket.validation_protocol verify
```

The default source is
`polymarket/data/training/public_only.csv`. Frozen artifacts are written to
`polymarket/data/validation_protocol/v1/`.

## Eligibility

Every source row must:

- be public;
- use the authoritative `polymarket_gamma_resolved` label;
- have a unique market ID;
- belong to an exact five-minute window;
- have its feature timestamp inside that window.

Rows are ordered by window start, asset, and market ID. All assets sharing a
window start form one atomic group and can never cross a split boundary.

## Chronological split

Raw target proportions are:

- train: first 70% of window groups;
- validation: next 15%;
- untouched holdout: final 15%.

At each raw boundary, the final window before the boundary is purged and the
first window after it is embargoed. These four excluded window groups remain
traceable in `excluded_boundary_rows.csv`. This creates a ten-minute separation
between the last usable group on one side and the first usable group on the
other while ensuring every source row is assigned exactly once.

## Holdout isolation

Train and validation CSV files contain labels. Holdout data is split into:

- `holdout_features.csv`, which contains no outcome, resolution timestamp, or
  label source;
- `sealed_holdout_labels.csv`, whose SHA-256 commitment is recorded in the
  manifest.

The development loader returns train and validation only. Holdout labels may
be opened once for final evaluation after the candidate, preprocessing,
thresholds, and stress assumptions have been frozen. Reusing the holdout for
selection invalidates the experiment.

## Baselines

The minimum comparison set is:

1. Training-split unconditional UP frequency.
2. Polymarket YES probability at the feature timestamp.
3. Existing deterministic lag score with any transformation fitted on train
   only.
4. Interpretable regularized logistic regression with preprocessing fitted on
   train only.

No model is fitted by the protocol builder.

## Metrics

Primary metrics:

- log loss;
- Brier score.

Secondary diagnostics:

- calibration error;
- balanced accuracy;
- ROC AUC;
- precision and recall;
- attribution by asset and chronological period.

## Precommitted decision rules

A candidate may advance from validation only when:

- it beats unconditional frequency on both primary metrics;
- it improves at least one primary metric versus Polymarket by at least 1%;
- the other primary metric is not worse than Polymarket by more than 0.5%;
- directional benefit appears in at least two assets.

Final holdout edge evidence requires the frozen candidate to:

- beat both unconditional and Polymarket baselines on both primary metrics;
- improve both primary metrics versus Polymarket by at least 1%;
- benefit at least two assets;
- avoid deriving more than 40% of simulated net P&L from one asset;
- remain positive under the predefined cost and latency stresses.

Failure is reported as `NO_VALIDATED_EDGE`; the holdout may not be recycled.

## Artifacts

- `protocol_manifest.json`
- `train.csv`
- `validation.csv`
- `holdout_features.csv`
- `sealed_holdout_labels.csv`
- `excluded_boundary_rows.csv`
- `split_assignments.csv`

The manifest records source and artifact hashes, exact row/window counts,
boundary timestamps, exclusions, baselines, metrics, and acceptance rules.
