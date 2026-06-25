# Polymarket Next Task

Last updated: June 25, 2026  
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `PROJECT_STATE.md`, `DECISIONS.md`, and
`REPRICING_RESEARCH_V1.md` before starting it.

## Active task: Run Balanced Repricing Evidence Collection Batch 002

### Objective

Collect the second independent 12-hour public-only balanced repricing evidence
batch using the unchanged frozen balanced stratum. Batch 001 was positive and
complete, but weak development evidence is not yet reached because the branch
still needs at least 40 observed hours and at least 3 independent sessions.

### Required scope

1. Re-read Batch 001 results under:
   - `polymarket/models/repricing_research_v1/balanced_collection_batch_001/`;
   - `polymarket/data/repricing_research_balanced_batch_001/`.
2. Before launch, re-run preflight:
   - correct project root `D:\ForgeViewAI`;
   - Windows AC sleep / hibernate disabled;
   - no competing `python -m polymarket.edge_engine_v5 capture` process;
   - no stale lock;
   - at least 1 GB free disk space;
   - output paths remain separate from canonical outcome-prediction datasets,
     microstructure development datasets, validation data, and sealed holdout;
   - mock fallback disabled;
   - no wallet/private-key requirement.
3. Launch exactly one Batch 002 campaign with the frozen balanced stratum:
   - assets: BTC, ETH, SOL;
   - duration: 43,200 seconds;
   - poll interval: 2 seconds;
   - discovery interval: 5 seconds;
   - no mock fallback;
   - external move threshold: 6 bps;
   - repricing ratio: 0.65;
   - minimum confidence: 0.45;
   - minimum entry seconds: 60;
   - output root: `polymarket/runs/repricing_balanced_v1_batch_002/`.
4. After completion, process only the completed Batch 002 session:
   - verify `session_completed`;
   - verify campaign completeness;
   - verify observation continuity;
   - run v5 replay;
   - build the repricing dataset with 60-second minimum expiry and accepted
     reasons `qualified_external_move_not_repriced` and
     `confidence_below_threshold`;
   - verify deterministic export by hashing repeated output;
   - report signal count, BTC / ETH / SOL counts, YES / NO counts, horizon
     coverage, continuity, replay status, deterministic export status, and
     cumulative Batch 001 + Batch 002 evidence status.
5. Recommend exactly one successor task.

### Acceptance criteria

- Exactly one Batch 002 campaign is launched.
- No Batch 003 or second campaign is launched.
- No holdout outcomes are opened.
- No holdout evaluation is run.
- No production model is trained.
- No validation protocol is modified.
- No wallet, private key, authenticated order placement, live trading, or real
  execution capability is implemented.
- Frozen balanced stratum parameters remain unchanged.

### Stop condition

If preflight safety fails, do not launch. Report the failing gate and leave
Batch 002 unstarted.
