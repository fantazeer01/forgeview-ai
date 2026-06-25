# Polymarket Edge Engine v2 — Alpha Validation System

## Research question

v2 does not ask whether one paper simulation made money. It asks whether the v1
signal remains profitable across chronological windows and under deterministic
price noise, missing signals, stale signals, execution latency, and slippage.
Its verdict is research evidence, not proof of tradable alpha.

## Run

```powershell
python -m polymarket.edge_engine_v2 run
```

The default uses a deterministic offline hybrid dataset and writes a canonical
replay copy plus reports to `polymarket/runs/v2/latest/`.

Replay a saved dataset:

```powershell
python -m polymarket.edge_engine_v2 run --input polymarket/runs/v2/latest/dataset.jsonl
```

Fetch public historical prices for a Polymarket YES token:

```powershell
python -m polymarket.edge_engine_v2 fetch --token-id TOKEN_ID --output polymarket/data/polymarket_token.jsonl
python -m polymarket.edge_engine_v2 run --input polymarket/data/polymarket_token.jsonl
```

The fetcher calls the public, unauthenticated CLOB `/prices-history` endpoint.
It has no order-submission code. Since that endpoint contains prices rather than
an external fair-value signal or historical volume, v2 creates explicitly
labeled causal proxies from only current and prior observations. For serious
research, replace those proxies in the JSONL file with independently sourced,
timestamp-aligned features.

## Architecture

```text
Real CLOB history OR deterministic hybrid data
                  |
                  v
          canonical replay JSONL
                  |
                  v
       v1 EdgeScorer + normalization checks
                  |
        +---------+----------+----------+
        |                    |          |
     noise/dropout       signal lag  execution latency
        |                    |          |
        +---------+----------+----------+
                  |
        chronological walk-forward windows
                  |
                  v
      trades + P&L + drawdown + robustness verdict
```

The original v1 scorer and exact weights are imported and preserved.

## Validation experiments

Defaults:

- Six non-overlapping chronological windows.
- Price noise standard deviations: 1%, 2.5%, 5%.
- Signal dropout: 5%, 15%.
- Signal lag: 1, 2, 4 market observations.
- Execution latency: 0, 1, 3 market observations.
- Absolute adverse slippage: 10 basis points on both entry and exit.

All random perturbations use explicit seeds. Dataset fingerprints, deterministic
trade IDs, and canonical replay files make runs reproducible.

## Robustness score

```text
ROBUSTNESS_SCORE =
    30% consistency across windows
  + 25% noise/dropout resilience
  + 25% window P&L stability
  + 20% drawdown control
```

Scores are bounded to `[0, 100]`. `POTENTIAL_ALPHA` requires:

- robustness score at least 60;
- positive baseline P&L;
- at least 60% profitable walk-forward windows;
- every configured noise/dropout scenario profitable;
- every configured execution-latency scenario profitable;
- at least two thirds of signal-lag scenarios profitable.

Otherwise the verdict is `OVERFIT_OR_INCONCLUSIVE`. The thresholds are explicit
research policy, not a statistical significance test.

## Outputs

- `dataset.jsonl`: canonical offline replay data for the default run.
- `validation_report.json`: complete machine-readable results and sub-scores.
- `report.md`: concise verdict and per-window P&L.
- `windows.csv`: every scenario/window result.
- `trades.csv`: all baseline and stress-test paper trades.

The JSON report includes global and per-window P&L, P&L standard deviation
between windows, variance across stress scenarios, maximum drawdown, win rates,
the four robustness components, and the final verdict.

## Important limitations

- A proxy reference probability is not independent information and cannot prove
  alpha.
- The engine does not model order-book depth, market impact, fees, token
  resolution, survivorship bias, or correlated portfolio capital.
- Walk-forward windows validate temporal stability but do not optimize
  parameters and do not constitute a train/test statistical model.
- A positive verdict means “worth deeper research,” never “safe to trade.”
