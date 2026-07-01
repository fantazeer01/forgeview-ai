# Polymarket Next Task

Last updated: July 1, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `RESEARCH_PRINCIPLES.md`, `PROJECT_STATE.md`,
`LAUNCH_BLOCKERS.md`, `ALPHA_READINESS.md`, `DECISIONS.md`, and
`REPRICING_RESEARCH_V1.md` before starting it.

## Active task: Run Fourth 24-Hour Repricing Paper Soak v1 - Clean Relaunch

### Objective

Run one fresh public-only 24-hour Repricing paper soak to validate complete
source capture, bounded terminal drain, healthy `session_completed`
consumption, exact final cursor reconciliation, and deterministic paper replay.
This duration is retained by protocol review because a valid run can move
admissible evidence from 24 hours/two sessions to 48 hours/three sessions;
6-hour and 12-hour alternatives cannot close the frozen 40-hour weak gate.
The prior attempt stopped before managed-runtime startup because a Windows
UTF-8 BOM config failed parsing. Its preserved prefix is evidence-ineligible.

### Required scope

1. Synchronize a clean `main` matching `origin/main` and run fresh machine and
   runtime preflight.
2. Parse and statically validate the complete runtime configuration before
   starting the producer; prove UTF-8 BOM compatibility.
3. Confirm active Windows sleep inhibition, watchdog/host-suspend protection,
   frozen strategy fingerprint, and `terminal_drain_seconds=60`.
4. Launch exactly one public v5 producer and one managed paper runtime for
   86,400 seconds.
5. Monitor heartbeat, completion/drain state, backlog, cursor, fatal markers,
   paper positions, and source continuity without intervention.
6. Require append-monotonic terminal events, `session_completed` as the final
   source event, healthy campaign/continuity payloads, zero remaining bytes,
   and runtime cursor equality with source EOF.
7. Run deterministic replay/export twice and reconcile signals, positions,
   trades, sides, assets, and P&L exactly.
8. Admit evidence only if every operational and source gate passes.
9. Commit only a compact GitHub-safe summary and project memory.

### Forbidden

- no additional or replacement run after failure;
- no detector, threshold, target, stop, timeout, slippage, fingerprint, or
  evidence-gate change;
- no live trading, wallet, private key, authentication, or order placement;
- no sealed holdout inspection or evaluation;
- no production model training;
- no raw run, JSONL, database, parquet, or large-log commit.

### Acceptance criteria

- complete and continuous 24-hour source capture;
- no sleep, watchdog, backlog, stale-source, or fatal failure;
- bounded terminal drain consumes healthy final `session_completed`;
- runtime cursor equals final source event and no terminal record is lost;
- exact deterministic live/offline paper reconciliation;
- Repricing and full repository tests pass;
- exactly one active successor task remains.
