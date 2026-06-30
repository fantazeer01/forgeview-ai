# Polymarket Next Task

Last updated: June 30, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `RESEARCH_PRINCIPLES.md`, `PROJECT_STATE.md`,
`LAUNCH_BLOCKERS.md`, `ALPHA_READINESS.md`, `DECISIONS.md`, and
`REPRICING_RESEARCH_V1.md` before starting it.

## Active task: Run Third 24-Hour Repricing Paper Soak v1

### Objective

Run one fresh, public-only 24-hour Repricing paper soak to validate bounded
ingestion, active Windows sleep inhibition, host-suspend detection, continuous
health telemetry, deterministic replay, and exact live/offline reconciliation.

### Required scope

1. Synchronize repository context and require a clean `main` matching
   `origin/main`.
2. Run fresh power, disk, process, lock, path, source, and frozen-fingerprint
   preflight.
3. Confirm the managed runtime reports `sleep_inhibitor_required=true` and
   holds `WindowsSleepInhibitor` throughout execution.
4. Launch exactly one public v5 producer and one managed paper runtime for
   86,400 seconds with the committed frozen configuration.
5. Monitor heartbeat freshness, watchdog cadence, backlog, source continuity,
   fatal markers, ledger state, and process lifetime without intervention.
6. After completion, run deterministic replay and frozen export twice, then
   require exact live/offline signal, position, and trade reconciliation.
7. Admit the run to evidence only if every operational and source gate passes.
8. Commit only a compact GitHub-safe summary and updated project memory.

### Forbidden

- no additional or replacement run after failure;
- no detector, threshold, target, stop, timeout, slippage, fingerprint, or
  evidence-gate change;
- no live trading, wallet, private key, authentication, or order placement;
- no sealed holdout inspection or evaluation;
- no production model training;
- no raw session JSONL, database, parquet, run directory, or large log commit.

### Acceptance criteria

- one complete and continuous 24-hour source session;
- no host suspend, watchdog scheduling gap, stale heartbeat, backlog overload,
  or fatal marker;
- bounded clean runtime shutdown;
- deterministic replay/export and exact live/offline reconciliation;
- Repricing and full repository tests pass;
- exactly one active successor task remains.
