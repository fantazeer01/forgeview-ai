# Polymarket Next Task

Last updated: July 1, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `RESEARCH_PRINCIPLES.md`, `PROJECT_STATE.md`,
`LAUNCH_BLOCKERS.md`, `ALPHA_READINESS.md`, `DECISIONS.md`, and
`REPRICING_RESEARCH_V1.md` before starting it.

## Active task: Fix Repricing Terminal Drain And Session Completion Reconciliation v1

### Objective

Ensure the managed Repricing runtime drains every terminal source event,
consumes and validates `session_completed`, and stops only after exact source
cursor reconciliation, without changing frozen strategy behavior.

### Required scope

1. Use the preserved third-soak tail and ledger to reproduce the four-event
   terminal shortfall in a deterministic fixture.
2. Correct v5 terminal export ordering so appended summary events cannot move
   backward in stream timestamp.
3. Add a bounded terminal-drain phase after the source producer completes and
   before the managed runtime declares `STOPPED`.
4. Require runtime cursor equality with the final complete source event and
   explicit runtime consumption of `session_completed`.
5. Preserve fail-closed behavior when terminal campaign or continuity health
   is incomplete.
6. Add tests for historical terminal rows, deadline/source completion races,
   terminal cursor reconciliation, and incomplete terminal health.
7. Run all Repricing tests and the full repository suite, then update project
   memory with a compact GitHub-safe report.

### Forbidden

- no fourth soak, capture campaign, or replacement run;
- no detector, threshold, target, stop, timeout, slippage, fingerprint, or
  evidence-gate change;
- no live trading, wallet, private key, authentication, or order placement;
- no sealed holdout inspection or evaluation;
- no production model training;
- no modification of preserved raw soak sessions.

### Acceptance criteria

- the preserved terminal shortfall is reproduced before the fix;
- terminal summary events remain stream-monotonic or carry a separate event
  time while their envelope timestamp stays append-monotonic;
- bounded runtime shutdown drains through `session_completed` and validates
  source health;
- cursor equals the final source event with no duplicate paper state;
- Repricing and full repository tests pass;
- exactly one active successor task remains.
