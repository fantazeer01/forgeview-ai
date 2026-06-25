# ForgeViewAI

ForgeViewAI is organized into isolated ownership domains:

- `core/`: system engines and shared utilities
- `content/`: narrative, publishing, and video-generation source
- `research/`: Polymarket research and trading-system source
- `state/`: persistent memory and runtime logs only
- `automation/`: importable n8n workflows and execution triggers only
- `output/`: generated media, datasets, reports, jobs, and artifacts
- `polymarket/`: self-contained Polymarket simulation and validation engines
- `docs/polymarket/`: Polymarket-only architecture and operating documentation
- `tests/polymarket/`: Polymarket-only automated tests

Runtime code must write generated files to `output/` and persistent memory to
`state/`. Source domains do not import from one another; each executable is
invoked through its public file or workflow boundary.

Polymarket is an explicit isolated product area and writes only beneath
`polymarket/data/` and `polymarket/runs/`. See
[`docs/polymarket/PROJECT_STRUCTURE.md`](docs/polymarket/PROJECT_STRUCTURE.md).

Polymarket project direction and current status:

- [Master objective](docs/polymarket/MASTER_OBJECTIVE.md) - permanent mission,
  success gates, architecture, and definitions of proven edge and production
  readiness.
- [Project state](docs/polymarket/PROJECT_STATE.md) - current stage, blockers,
  active milestone, and next actions.
- [Next task](docs/polymarket/NEXT_TASK.md) - the single active engineering
  priority and its acceptance criteria.
- [Decisions](docs/polymarket/DECISIONS.md) - durable architecture and research
  policy decisions.
- [Research backlog](docs/polymarket/RESEARCH_BACKLOG.md) - future ideas that
  are not currently authorized work.
- [Resolution Engine v1](docs/polymarket/RESOLUTION_ENGINE_V1.md) -
  authoritative outcome ingestion and proxy-label reconciliation.
- [Public Evidence Batch v1](docs/polymarket/PUBLIC_EVIDENCE_BATCH_V1.md) -
  fail-closed capture-to-quality orchestration and milestone progress.
- [Time-Ordered Holdout Protocol v1](docs/polymarket/TIME_ORDERED_HOLDOUT_PROTOCOL_V1.md) -
  frozen chronological splits, leakage controls, and final-holdout policy.
- [Baseline Probability Model v1](docs/polymarket/BASELINE_PROBABILITY_MODEL_V1.md) -
  development-only baseline results and `NO_EDGE_FOUND_YET` verdict.
- [Baseline Failure Diagnostics v1](docs/polymarket/BASELINE_FAILURE_DIAGNOSTICS_V1.md) -
  fixed diagnostic evidence and the `FEATURE_SET_INCOMPLETE` conclusion.
- [Market Microstructure Feature Capture v1](docs/polymarket/MARKET_MICROSTRUCTURE_FEATURE_CAPTURE_V1.md) -
  public CLOB schema, as-of features, provenance, and coverage status.

Polymarket quick start:

```powershell
python -m polymarket.edge_engine
python -m polymarket.edge_engine_v2 run
python -m polymarket.edge_engine_v3 replay --session polymarket/runs/v3/latest/session
python -m polymarket.edge_engine_v4 scan --duration 300
python -m polymarket.edge_engine_v5 capture --duration 3600
python -m polymarket.feature_engine build
python -m polymarket.dataset_quality analyze
python -m polymarket.resolution_engine reconcile
python -m polymarket.validation_protocol verify
python -m polymarket.baseline_model verify
python -m polymarket.baseline_diagnostics verify
```
