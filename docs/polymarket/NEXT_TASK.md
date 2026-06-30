# Polymarket Next Task

Last updated: June 30, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `RESEARCH_PRINCIPLES.md`, `PROJECT_STATE.md`,
`LAUNCH_BLOCKERS.md`, `ALPHA_READINESS.md`, `DECISIONS.md`, and
`REPRICING_RESEARCH_V1.md` before starting it.

## Active task: Diagnose Repricing Runtime Telemetry Stall After Interrupted Soak v1

### Objective

Determine why the second soak's managed runtime emitted
`TELEMETRY_STALLED` after prolonged healthy operation, while preserving the
frozen detector and the recovered run. Establish whether the watchdog detected
a genuine processing deadlock, lock contention, I/O latency, callback starvation,
or a false-positive liveness condition.

### Required scope

1. Use only the preserved second-soak runtime logs, heartbeat, safe-shutdown
   marker, SQLite ledger, and deterministic recovery outputs.
2. Reconstruct the final healthy processing interval and the exact watchdog
   transition without modifying raw session evidence.
3. Measure backlog, cursor movement, batch progress, database latency, source
   write behavior, and watchdog scheduling around the failure.
4. Add a deterministic regression fixture that reproduces the identified
   condition, or document precisely why the preserved artifacts cannot do so.
5. Implement the smallest runtime-only correction if and only if a defect is
   demonstrated; do not change strategy behavior.
6. Run all Repricing tests and the full repository suite.
7. Produce a compact GitHub-safe diagnosis and update project memory.

### Forbidden

- no new soak, campaign, capture, replay evidence run, or replacement session;
- no detector, threshold, target, stop, timeout, slippage, fingerprint, or
  evidence-gate change;
- no live trading, wallet, private key, authentication, or order placement;
- no sealed holdout inspection or evaluation;
- no production model training;
- no modification of the preserved raw second-soak session.

### Acceptance criteria

- the liveness transition has a timestamped, artifact-backed causal account;
- any runtime defect has a failing regression test before its correction;
- fail-closed behavior remains intact and cannot silently continue;
- Repricing and full repository tests pass;
- exactly one active successor task remains.
