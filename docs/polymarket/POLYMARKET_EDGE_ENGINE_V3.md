# Polymarket Edge Engine v3 — Real-Market Shadow Validation

## Purpose

v3 is the read-only validation layer between historical research and any future
deployment decision. It captures public Polymarket quotes, runs the unchanged
v1 score and decision rules in shadow mode, logs every decision, compares the
session with the frozen v2 baseline, and detects signal drift and edge decay.

There is no wallet, private key, authenticated trading client, or order method.

## Install and capture

The WebSocket client is an optional dependency:

```powershell
python -m pip install -e ".[live]"
python -m polymarket.edge_engine_v3 capture --token-id YES_TOKEN_ID --duration 3600
```

The public REST order-book fallback needs no extra package:

```powershell
python -m polymarket.edge_engine_v3 capture --token-id YES_TOKEN_ID --duration 300 --transport poll
```

Official feed:

- `wss://ws-subscriptions-clob.polymarket.com/ws/market`
- subscription type `market`, using Polymarket token IDs
- supported events include books, price changes, trades, and best bid/ask

## Replay

Every normalized quote and raw feed event is stored. Replay is deterministic:

```powershell
python -m polymarket.edge_engine_v3 replay --session polymarket/runs/v3/latest/session
```

All raw events are retained. Strategy decisions use the first quote in each
one-second market bucket so bursts of duplicate book events cannot accelerate
update-based exits.

An offline example is included:

```powershell
python -m polymarket.edge_engine_v3 replay --session polymarket/data/v3_example_session.jsonl
```

## Independent reference probabilities

The v2 score requires a `reference_probability`. Polymarket market data does not
provide an independent fair probability. Without another timestamp-aligned
source, v3 constructs a causal EWMA proxy from past prices and marks the report
as `causal_proxy`.

That mode can never produce `TRUE_ALPHA`, because market price predicting later
market price is not independent alpha evidence.

For genuine final validation, provide JSONL observations:

```json
{"timestamp":"2026-01-01T12:00:00Z","market_id":"0xcondition","reference_probability":0.64}
```

Then run:

```powershell
python -m polymarket.edge_engine_v3 replay \
  --session polymarket/runs/v3/latest/session \
  --reference-file polymarket/data/independent_probabilities.jsonl
```

Only observations at or before each market tick are used.

## Metrics

- Live simulated P&L and maximum drawdown.
- Model expected P&L and live/model P&L deviation.
- Divergence score: P&L, win-rate, and trade-rate departure from v2.
- Signal drift score: live signal frequency departure from v2.
- Edge decay score: deterioration between early and late session periods.
- Stability score: dispersion of P&L across chronological periods.
- Noise ratio: live price movement relative to v2 noise-test magnitudes.

For divergence, drift, and decay, lower is better. For stability, higher is
better.

## Verdict policy

`TRUE_ALPHA` requires all of:

- an independent external reference feed;
- at least 95% timestamp/market coverage from that reference feed;
- at least 30 closed shadow trades by default;
- positive live simulated P&L;
- divergence no greater than 35;
- edge decay no greater than 35;
- stability at least 55.

`WEAK_ALPHA` means positive but incomplete or materially divergent evidence.
`NO_ALPHA` means the observed session does not support the historical edge.

The minimum trade count is configurable, but lowering it weakens the evidence.
