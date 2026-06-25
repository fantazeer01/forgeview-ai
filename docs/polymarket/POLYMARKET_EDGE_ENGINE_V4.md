# Polymarket Edge Engine v4 — Five-Minute Crypto Lag Scanner

## Purpose

v4 scans BTC, ETH, and SOL five-minute UP/DOWN markets for short-lived
repricing lag. It does not predict crypto direction from scratch. It compares
an external spot-price move with the contemporaneous Polymarket YES
probability move and records cases where Polymarket has not moved enough.

The engine is shadow-only. It has no private keys, wallet integration,
authentication, or order-placement code.

## Architecture

```text
Gamma market discovery
        |
        v
validated 5-minute BTC/ETH/SOL markets
        |
        +---- CLOB public YES order book
        |
        +---- Binance public spot price
                 |
                 +---- Coinbase Exchange fallback
                 |
                 +---- deterministic mock fallback
        |
        v
lag detector -> opportunity -> v3 shadow adapter -> reports/replay
```

## Commands

From `D:\ForgeViewAI`:

```powershell
python -m polymarket.edge_engine_v4 scan --duration 300
python -m polymarket.edge_engine_v4 scan --assets BTC ETH SOL --duration 300
python -m polymarket.edge_engine_v4 replay --session polymarket/runs/v4/latest/session
```

Deterministic offline scan:

```powershell
python -m polymarket.edge_engine_v4 scan --mock --duration 6 --poll-interval 1
```

Public discovery/reference failures automatically use the deterministic mock
fallback unless `--no-mock-fallback` is supplied.

## Discovery rules

Discovery uses strict asset aliases (`BTC`/Bitcoin, `ETH`/Ethereum,
`SOL`/Solana), never arbitrary substrings. A candidate must:

- be active and not closed;
- have a window between 240 and 360 seconds;
- represent UP/DOWN or YES/NO binary outcomes;
- expose both CLOB token IDs;
- map to exactly one supported asset.

Rejected candidates and scan-level rejections are written to
`skipped_markets.csv` with explicit reasons.

## Lag measurement

For each market:

- `external_price_change` is return since the first reference observation.
- `polymarket_yes_price_change` is the YES midpoint change since first quote.
- direction is UP, DOWN, or NONE from the external move threshold.
- expected probability movement scales with external basis-point movement.
- `lag_score` combines external move strength and unpriced residual.
- confidence adds spread quality to lag score and move strength.

Signals are rejected when external movement is too small, Polymarket already
repriced, liquidity is too low, expiry is too close, or confidence is weak.

## v3 integration

Qualified opportunities pass through a narrow adapter into v3's
`ShadowExecutionEngine`. The adapter creates normalized research snapshots;
it never submits an order. v3 decisions and shadow trades are saved alongside
the scanner report.

## Storage and replay

Default output: `polymarket/runs/v4/latest/`.

```text
opportunities.csv
skipped_markets.csv
reference_prices.jsonl
polymarket_snapshots.jsonl
shadow_decisions.csv
shadow_trades.csv
report.md
summary.json
session/
  markets.json
  reference_prices.jsonl
  polymarket_snapshots.jsonl
```

Replay reads only the three canonical files in `session/`, making results
deterministic.

## Public data sources

- Polymarket Gamma API: active events and nested markets.
- Polymarket CLOB API: public YES-token order books.
- Binance market-data-only REST: BTCUSDT, ETHUSDT, SOLUSDT.
- Coinbase Exchange public ticker: fallback BTC-USD, ETH-USD, SOL-USD.

## Limitations

- Spot exchange moves are a proxy for the resolution source used by each
  Polymarket market; basis differences may exist.
- REST polling can miss sub-second moves.
- Order-book depth and market impact are not modeled by the v4 detector.
- Mock fallback demonstrates mechanics, not real alpha.
