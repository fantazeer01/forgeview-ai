# Polymarket Next Task

Last updated: June 29, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `RESEARCH_PRINCIPLES.md`, `PROJECT_STATE.md`,
`LAUNCH_BLOCKERS.md`, `ALPHA_READINESS.md`, `DECISIONS.md`, and
`REPRICING_RESEARCH_V1.md` before starting it.

## Active task: Run Second 24-Hour Repricing Paper Soak v1

### Objective

Validate the fixed bounded-ingestion and liveness controls in one unattended,
public-only 24-hour Repricing paper soak without changing the frozen strategy.
This is an operational validation run, not an evidence-parameter experiment.

### Required scope

1. Synchronize repository context and run the full existing preflight.
2. Confirm safe AC power, sufficient disk, no competing producer/runtime, no
   stale lock, writable paths, and the frozen strategy fingerprint.
3. Launch exactly one public v5 producer and one paper runtime for 86,400
   seconds with the committed batch, backlog, heartbeat, watchdog, deadline,
   and session-health settings.
4. Preserve raw run data outside GitHub and monitor heartbeat freshness,
   backlog bytes, cursor progress, fatal marker, positions, and trades.
5. Require complete source continuity, bounded runtime shutdown, zero fatal
   marker, and exact live-versus-offline signal reconciliation.
6. Replay and export deterministically after completion, but do not admit the
   session to scientific evidence unless every operational and source gate
   passes.
7. Commit only a compact GitHub-safe summary and updated project memory.

### Forbidden

- no detector, threshold, strategy, fingerprint, slippage, or evidence-gate
  change;
- no second concurrent soak or replacement run after failure;
- no live trading, wallet, private key, authentication, or order placement;
- no sealed holdout inspection or evaluation;
- no production model training;
- no raw session JSONL, run directory, database, parquet, or large log commit.

### Acceptance criteria

- preflight passes before launch;
- one 24-hour source session is complete and continuous;
- heartbeat remains current and backlog stays within the committed ceiling;
- runtime stops within its configured bound without manual termination;
- safe-shutdown marker is absent and fatal error code remains empty;
- live signals, positions, and trades reconcile exactly to deterministic replay;
- Repricing and full repository tests pass;
- exactly one active successor task remains.
