# Polymarket Research Engines

This directory is the isolated home of the ForgeViewAI Polymarket project.
It contains no Content Machine code and has no live order-execution capability.

Start here:

- [Master objective](../docs/polymarket/MASTER_OBJECTIVE.md) - the permanent
  source of truth for mission, success criteria, research gates, proven edge,
  and production readiness.
- [Project state](../docs/polymarket/PROJECT_STATE.md) - current milestone,
  measured status, blockers, and immediate next actions.
- [Next task](../docs/polymarket/NEXT_TASK.md) - exactly one active task for the
  next engineering session.
- [Decisions](../docs/polymarket/DECISIONS.md) - accepted architecture and
  research-policy choices.
- [Research backlog](../docs/polymarket/RESEARCH_BACKLOG.md) - deferred ideas,
  not active work.

Future sessions should read those five documents in that order before changing
the project. At task completion, update project state, record decisions, and
replace the completed next task with one newly recommended active task.

## Engines

- `edge_engine/`: v1 deterministic paper-trading simulator.
- `edge_engine_v2/`: v2 walk-forward and robustness validation.
- `edge_engine_v3/`: v3 public live-data capture and shadow validation.
- `edge_engine_v4/`: v4 BTC/ETH/SOL five-minute lag scanner.
- `edge_engine_v5/`: v5 long shadow capture and edge evidence system.
- `feature_engine/`: completed-window feature and labelled dataset builder.
- `dataset_quality/`: dataset quality scoring and public-only subset builder.
- `resolution_engine/`: authoritative public outcome ingestion and proxy-label
  reconciliation.
- `evidence_batch/`: capture-to-quality orchestration and milestone manifest.
- `validation_protocol/`: frozen chronological splits, purge/embargo controls,
  and sealed holdout commitments.
- `baseline_model/`: deterministic development-only probability baselines and
  validation reporting.
- `baseline_diagnostics/`: fixed development-only feature, drift, calibration,
  asset, and regime diagnostics.
- `data/`: replayable Polymarket input datasets and example sessions.
- `runs/`: generated logs, trade ledgers, reports, and captured sessions.

## Run from `D:\ForgeViewAI`

```powershell
python -m polymarket.edge_engine
python -m polymarket.edge_engine_v2 run
python -m polymarket.edge_engine_v3 capture --token-id YES_TOKEN_ID --duration 3600
python -m polymarket.edge_engine_v3 replay --session polymarket/runs/v3/latest/session
python -m polymarket.edge_engine_v4 scan --duration 300
python -m polymarket.edge_engine_v4 replay --session polymarket/runs/v4/latest/session
python -m polymarket.edge_engine_v5 capture --duration 3600
python -m polymarket.edge_engine_v5 replay --session polymarket/runs/v5/latest/session.jsonl
python -m polymarket.feature_engine build
python -m polymarket.feature_engine inspect
python -m polymarket.dataset_quality analyze
python -m polymarket.dataset_quality build-public
python -m polymarket.resolution_engine reconcile
python -m polymarket.resolution_engine replay
python -m polymarket.evidence_batch resume --session polymarket/runs/v5/latest/session.jsonl --resolution-mode replay
python -m polymarket.validation_protocol verify
python -m polymarket.baseline_model verify
python -m polymarket.baseline_diagnostics verify
```

Microstructure schema and provenance:
[`docs/polymarket/MARKET_MICROSTRUCTURE_FEATURE_CAPTURE_V1.md`](../docs/polymarket/MARKET_MICROSTRUCTURE_FEATURE_CAPTURE_V1.md).

For WebSocket capture:

```powershell
python -m pip install -e ".[live]"
```

Run all isolated Polymarket tests:

```powershell
python -m unittest discover -s tests -v
```

Architecture details are documented in
[`docs/polymarket/PROJECT_STRUCTURE.md`](../docs/polymarket/PROJECT_STRUCTURE.md).
