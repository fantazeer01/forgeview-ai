# Polymarket Project Structure

All paths in this document are relative to `D:\ForgeViewAI`.

## Ownership boundaries

Polymarket code and artifacts are restricted to:

- `polymarket/`
- `docs/polymarket/`
- `tests/polymarket/`

The Polymarket engines do not import from or write into Content Machine,
automation, core, state, output, or unrelated research modules.

## Components

```text
polymarket/
  edge_engine/       v1 paper simulation
  edge_engine_v2/    v2 historical alpha validation
  edge_engine_v3/    v3 live shadow validation
  edge_engine_v4/    v4 BTC/ETH/SOL five-minute lag scanner
  edge_engine_v5/    v5 long shadow capture and edge evidence
  data/              replay datasets and captured-session examples
  runs/              generated logs, reports, ledgers, and sessions
  README.md

docs/
  polymarket/
    POLYMARKET_EDGE_ENGINE.md
    POLYMARKET_EDGE_ENGINE_V2.md
    POLYMARKET_EDGE_ENGINE_V3.md
    POLYMARKET_EDGE_ENGINE_V4.md
    POLYMARKET_EDGE_ENGINE_V5.md
    PROJECT_STRUCTURE.md

tests/
  polymarket/
    test_engine.py
    test_scoring.py
    test_v2.py
    test_v3.py
    test_v4.py
    test_v5.py
```

## Engine versions

### v1 — Paper simulation

`polymarket/edge_engine/` contains market snapshots, the preserved weighted
edge score, decision rules, simulated fills, P&L tracking, and local run logs.

```powershell
python -m polymarket.edge_engine
python -m polymarket.edge_engine --input polymarket/data/sample_markets.jsonl
```

Default output: `polymarket/runs/latest/`.

### v2 — Historical alpha validation

`polymarket/edge_engine_v2/` adds deterministic replay storage, perturbation
tests, walk-forward windows, latency and slippage stress, drawdown statistics,
and a robustness verdict.

```powershell
python -m polymarket.edge_engine_v2 run
python -m polymarket.edge_engine_v2 run --input polymarket/data/sample_markets.jsonl
```

Default output: `polymarket/runs/v2/latest/`.

### v3 — Live shadow validation

`polymarket/edge_engine_v3/` reads public Polymarket market data, stores raw
events and normalized ticks, runs shadow-only decisions, supports deterministic
session replay, and reports model divergence, signal drift, and edge decay.
It contains no authenticated trading or order-submission path.

```powershell
python -m pip install -e ".[live]"
python -m polymarket.edge_engine_v3 capture --token-id YES_TOKEN_ID --duration 3600
python -m polymarket.edge_engine_v3 replay --session polymarket/runs/v3/latest/session
```

Default output: `polymarket/runs/v3/latest/`.

### v4 — Five-minute crypto lag scanner

`polymarket/edge_engine_v4/` discovers active BTC/ETH/SOL UP/DOWN markets,
compares public exchange prices with Polymarket YES prices, records lag
opportunities and skipped candidates, and passes qualified signals into the
v3 shadow engine.

```powershell
python -m polymarket.edge_engine_v4 scan --duration 300
python -m polymarket.edge_engine_v4 scan --assets BTC ETH SOL --duration 300
python -m polymarket.edge_engine_v4 replay --session polymarket/runs/v4/latest/session
```

Default output: `polymarket/runs/v4/latest/`.

### v5 — Long shadow capture and evidence

`polymarket/edge_engine_v5/` continuously rotates across five-minute crypto
markets, stores an append-only evidence session, computes coverage/performance
metrics, and applies conservative evidence verdicts.

```powershell
python -m polymarket.edge_engine_v5 capture --duration 3600
python -m polymarket.edge_engine_v5 capture --duration 21600
python -m polymarket.edge_engine_v5 replay --session polymarket/runs/v5/latest/session.jsonl
```

Default output: timestamped folders and `polymarket/runs/v5/latest/`.

## Storage

- Input and replay data: `polymarket/data/`
- v1 reports and logs: `polymarket/runs/latest/`
- v2 datasets and reports: `polymarket/runs/v2/latest/`
- v3 captures, decisions, and reports: `polymarket/runs/v3/latest/`
- v4 scanner sessions and reports: `polymarket/runs/v4/latest/`
- v5 long captures and evidence reports: `polymarket/runs/v5/`
- Documentation: `docs/polymarket/`
- Tests: `tests/polymarket/`

## Tests

From `D:\ForgeViewAI`:

```powershell
python -m unittest discover -s tests -v
```
