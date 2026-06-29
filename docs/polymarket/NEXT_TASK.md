# Polymarket Next Task

Last updated: June 29, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `RESEARCH_PRINCIPLES.md`, `PROJECT_STATE.md`,
`LAUNCH_BLOCKERS.md`, `ALPHA_READINESS.md`, `DECISIONS.md`, and
`REPRICING_RESEARCH_V1.md` before starting it.

## Active task: Fix Repricing Runtime Backpressure And Liveness Fail-Closed v1

### Objective

Remove the runtime integrity blocker exposed by First 24-Hour Repricing Paper
Soak v1 without changing the frozen detector or launching another soak. The
runtime must consume a growing v5 JSONL stream incrementally while heartbeat,
watchdog, and bounded-shutdown controls remain independently responsive.

### Required scope

1. Replace whole-backlog-per-poll behavior with bounded incremental consumption
   that durably advances the existing source cursor.
2. Keep heartbeat and maximum-runtime enforcement responsive while backlog is
   being consumed.
3. Stop closed when heartbeat freshness, source progress, write latency, or the
   configured runtime bound fails.
4. Preserve restart-safe exactly-once signal, position, and trade behavior from
   the existing SQLite ledger.
5. Add deterministic catch-up tests from the soak-scale cursor boundary and a
   stress fixture large enough to expose processing lag.
6. Reconcile fixture live output exactly to offline adapter output with zero
   missing or duplicate signals.
7. Update Objective Alpha blocker evidence and run Repricing plus full tests.

### Forbidden

- no second soak or capture campaign;
- no detector, threshold, strategy, fingerprint, or evidence-gate change;
- no live trading, wallet, private key, authentication, or order placement;
- no sealed holdout inspection or evaluation;
- no production model training;
- no manual insertion or deletion of paper signals, positions, or trades.

### Acceptance criteria

- heartbeat remains current during bounded backlog processing;
- configured maximum runtime is enforced independently of adapter throughput;
- injected stalls and stale progress stop closed with a durable error;
- restart resumes from the committed cursor without duplicate or lost business
  state;
- live and offline fixture signals reconcile exactly;
- Repricing and full repository tests pass;
- exactly one active successor task remains.
