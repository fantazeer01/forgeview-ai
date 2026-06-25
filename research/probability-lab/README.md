# ForgeView Probability Lab

Research repository for evaluating predictive and executable-price edge in
Polymarket BTC 5-minute Up/Down markets.

## Current Evidence

- Predictive edge: **YES**
- Simulated profit edge: **YES**
- Real ask edge: **NOT CONFIRMED**

The current live sample is too small to validate profitability. The minimum
next milestone is 30 resolved real-ask trades; 100 or more is preferred.

## Research Rule

**Do not trade. Do not connect a wallet. Research only until real-ask
validation confirms an edge.**

## Repository Layout

- `docs/`: status, research history, and objectives
- `scripts/`: dataset, model, simulation, recorder, and validation pipelines
- `data_samples/`: small reproducibility samples only

Generated datasets, models, reports, and validation results are stored under
`D:\ForgeViewAI\output\research\`.

Large recorder CSV files and secrets must remain outside this repository.

## Pipeline

1. Build resolved BTC 5m probability datasets.
2. Train chronological baseline models.
3. Compare model probability against Polymarket probability.
4. Simulate signals under conservative execution assumptions.
5. Record live executable bids and asks.
6. Join captured asks to resolved outcomes and validate realized PnL.

## Current Next Task

Run the hardened live recorder continuously and collect at least 30 resolved
real-ask trades, with 100 or more preferred for validation.
