# Polymarket Next Task

Last updated: June 29, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `RESEARCH_PRINCIPLES.md`, `PROJECT_STATE.md`,
`LAUNCH_BLOCKERS.md`, `ALPHA_READINESS.md`, `DECISIONS.md`, and
`REPRICING_RESEARCH_V1.md` before starting it.

## Active task: Run First 24-Hour Repricing Paper Soak v1

### Objective

Run the preflight-approved Repricing paper runtime for one bounded 24-hour
period and determine whether it can sustain an unattended, restart-safe,
fully auditable paper signal-to-result path. This task directly tests
`ALPHA-B001`, `ALPHA-B002`, `ALPHA-B003`, `ALPHA-B004`, `ALPHA-B006`, and
`ALPHA-B007` on the path to Objective Alpha.

### Required scope

1. Re-run the existing pre-soak readiness checks and launch only if every gate
   remains green.
2. Use the frozen Repricing strategy fingerprint and current continuous paper
   runtime without changing detector logic, thresholds, or strategy behavior.
3. Run paper-only for 24 hours against public v5 session input with automatic
   latest-session rotation, stale-event protection, health monitoring, and
   the existing restart budget.
4. Preserve runtime state, heartbeat, logs, daily summaries, paper positions,
   and paper trades durably throughout the soak.
5. Reconcile raw accepted events, runtime health, summaries, positions, trades,
   failures, restarts, continuity, and duplicate or lost transitions.
6. Record whether a complete autonomous paper signal-to-result cycle occurred
   and which Objective Alpha blockers gained exit evidence.
7. Run Repricing tests and the full repository suite after the bounded soak.

### Forbidden

- no live trading, authenticated trading endpoint, wallet, or private key;
- no order placement or real-money capital;
- no detector, threshold, strategy, fingerprint, or risk-policy change;
- no sealed holdout inspection or evaluation;
- no Wallet Intelligence evidence-method change;
- no manual paper trade insertion or discretionary signal intervention.

### Acceptance criteria

- the preflight remains `READY_FOR_24H_SOAK` before launch;
- one bounded 24-hour paper soak completes or stops closed for a documented
  integrity reason;
- runtime state and health remain durable and restart-safe;
- every accepted source event and paper state transition reconciles with no
  unexplained duplicate or loss;
- any completed paper trade is traceable from source event through result;
- tests pass;
- project state, launch blockers, Alpha readiness, decisions when needed, and
  this file are updated with exactly one successor task.
