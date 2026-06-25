# Polymarket Edge Engine v1

## Purpose

This is a local research simulator, not a production trading system. It does not
connect to an exchange, submit orders, custody funds, or estimate a genuine
forecast probability. Mock and local-file data are supported so a complete run
requires no external service.

## Architecture

```text
MarketDataProvider
        |
        v
EdgeScorer -> DecisionEngine -> PaperExecutionEngine -> PnLTracker
                                      |
                                      v
                           JSONL / CSV run artifacts
```

Modules:

- `polymarket/edge_engine/data.py`: snapshot interface, deterministic mock feed, JSONL feed.
- `polymarket/edge_engine/scoring.py`: EDGE_SCORE and component breakdown.
- `polymarket/edge_engine/decision.py`: entry, convergence, score, and timeout rules.
- `polymarket/edge_engine/execution.py`: simulated YES/NO fills and position lifecycle.
- `polymarket/edge_engine/pnl.py`: realized/unrealized P&L, equity, wins, and losses.
- `polymarket/edge_engine/logging.py`: console output and durable run artifacts.
- `polymarket/edge_engine/engine.py`: event loop orchestration.
- `polymarket/edge_engine/cli.py`: one-command entry point.

## EDGE_SCORE

All components are normalized to `[0, 1]`.

```text
EDGE_SCORE =
    0.4 * price_lag
  + 0.3 * volume_spike
  + 0.2 * momentum
  + 0.1 * stability
```

`price_lag = min(1, abs(reference_probability - yes_price) * 2)`.
The factor of two maps a 50-point probability discrepancy to the maximum
normalized lag. The other three components are supplied by the data layer.

The engine buys YES when the reference probability is above the market YES
price and buys NO when it is below.

## Rules

- Open when `score > 0.7`.
- Close when `score < 0.3`.
- Close on convergence when the market/reference gap is at most `0.03`.
- Close after three subsequent updates by default.
- At end of finite input, mark and liquidate remaining positions unless
  `--keep-open` is supplied.
- Only one position per market can be open.

Thresholds, stake, timeout, slippage, output directory, and starting cash are
configurable CLI arguments.

## Run

Python 3.11 or later is required. No third-party package is required.

```powershell
python -m polymarket.edge_engine
python -m polymarket.edge_engine --input polymarket/data/sample_markets.jsonl
python -m polymarket.edge_engine --stake 250 --slippage-bps 5 --timeout 6
```

Optional editable installation:

```powershell
python -m pip install -e .
edge-engine
```

## Output

Each run writes:

- `events.jsonl`: every scored decision and position lifecycle event.
- `equity.csv`: realized/unrealized P&L and equity after every snapshot.
- `trades.csv`: complete closed-trade ledger.
- `summary.json`: final portfolio statistics.

By default these are recreated under `polymarket/runs/latest/`.

## Local JSONL schema

One JSON object per line:

```json
{
  "timestamp": "2026-01-01T12:00:00Z",
  "market_id": "fed-cut",
  "question": "Will the Fed cut rates by September?",
  "yes_price": 0.28,
  "reference_probability": 0.76,
  "volume_spike": 0.92,
  "momentum": 0.86,
  "stability": 0.90
}
```

## Research limitations

The simulator assumes binary contracts where `NO = 1 - YES`. It does not model
order-book depth, partial fills, fees, latency, resolution risk, correlated
exposure, capital limits across simultaneous entries, or live probability
estimation. Slippage can be configured, but the default is zero to make the
sample deterministic.
