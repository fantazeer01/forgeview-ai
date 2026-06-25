# Balanced Repricing Evidence Collection Preflight v1

Status: preflight complete. No evidence campaign was launched.

## Result

Operational preflight result: `READY_FOR_AUTHORIZED_LAUNCH`. Campaign launch authorized by this task: `False`.

Warnings:

- No operational blockers detected, but this task does not authorize launch.

## Balanced Stratum

- external move threshold: 6 bps
- repricing ratio: 0.65
- minimum confidence: 0.45
- minimum dataset expiry: 60 seconds
- max holding window: 180 seconds
- accepted reasons: `qualified_external_move_not_repriced`, `confidence_below_threshold`
- expected density: 3.9184 signals/hour

## Run Plan

- duration: 12 hours / 43,200 seconds
- poll interval: 2 seconds
- discovery interval: 5 seconds
- expected checkpoints: 21,600
- estimated signals: 47.02
- estimated total artifact size: about 205 MB, with at least 1 GB free space required
- output root: `polymarket/runs/repricing_balanced_v1/`
- model output root after processing: `polymarket/models/repricing_research_v1/balanced_collection_batch_001/`
- dedicated data copy path after processing: `polymarket/data/repricing_research_balanced_batch_001/`

## Launch Command

This command is recorded for a future authorized task only. It was not executed.

```powershell
python -m polymarket.edge_engine_v5 capture --assets BTC ETH SOL --duration 43200 --poll-interval 2 --discovery-interval 5 --output-root polymarket/runs/repricing_balanced_v1 --no-mock-fallback --min-completed-windows 1 --min-shadow-trades 1 --min-entry-seconds 60 --external-move-threshold-bps 6 --repricing-ratio 0.65 --min-confidence 0.45
```

## Validation Gates

- campaign completeness: `session_completed` present and completeness status `complete`
- observation continuity: at least 95% checkpoint coverage, expected 21,600 checkpoints, no gap over 300 seconds, no fatal capture errors
- replay compatibility: `edge_engine_v5 replay` exits successfully
- deterministic export: repricing dataset export runs twice and hashes match
- signal count: expected 47.02 signals in one 12-hour session; weak evidence still requires 100 total signals
- asset balance: monitor BTC / ETH / SOL; weak gate remains at least 25 per asset
- side balance: monitor YES / NO; weak gate remains at least 35 per side

## Safety

The preflight did not inspect sealed holdout outcomes, run holdout evaluation, implement live trading, connect wallets or private keys, launch capture, train production models, or change the frozen balanced stratum based on P&L.
