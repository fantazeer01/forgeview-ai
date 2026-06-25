# Polymarket Dataset Quality Engine v1

## Purpose

Dataset Quality Engine v1 evaluates the Feature Engine dataset and creates a
public-market-only subset for later statistical validation. It is offline
research tooling and contains no trading, wallet, key, or order code.

## Commands

Run from `D:\ForgeViewAI`:

```powershell
python -m polymarket.dataset_quality analyze
python -m polymarket.dataset_quality build-public
```

Optional input and output locations:

```powershell
python -m polymarket.dataset_quality analyze `
  --dataset polymarket/data/training/dataset.csv `
  --output-root polymarket/data/training
```

## Metrics

The report contains:

- total, public, and mock sample counts;
- BTC, ETH, and SOL counts;
- UP and DOWN counts;
- class imbalance and minority-class percentages;
- missing cell count and percentage;
- feature completeness across the 20 modelling features;
- exact duplicate rows and duplicate market IDs;
- public-only sample count and public class balance.

Class imbalance is the absolute difference between UP and DOWN counts divided
by all labelled rows. A perfectly balanced dataset has 0% imbalance.

## Quality score

The score is deterministic and ranges from 0 to 100:

| Component | Weight |
|---|---:|
| Public sample ratio | 30% |
| Class balance | 25% |
| Overall missing-value control | 15% |
| Duplicate control | 10% |
| Feature completeness | 20% |

Class-balance points scale from zero when one class is absent to 100 when both
classes are 50%.

Training is recommended only when all conservative gates pass:

- quality score is at least 75;
- public samples are at least 80% of the dataset;
- minority class is at least 30%;
- feature completeness is at least 95%;
- duplicate rate is no greater than 1%.

## Outputs

Analysis writes:

```text
polymarket/data/training/quality_report.json
```

`build-public` additionally writes:

```text
polymarket/data/training/public_only.csv
polymarket/data/training/public_only.parquet
```

Only rows where `market_source == public` are included. Rows are not
resampled, balanced, imputed, or synthetically generated.

## Limitations

- Quality scoring measures data suitability, not predictive edge.
- Public samples still use the Feature Engine's external-reference proxy
  labels until authoritative Polymarket resolutions are captured.
- A high score cannot replace walk-forward validation or leakage review.
