# ForgeViewAI Launch Blockers

Status: Active
Last updated: June 29, 2026
Authority: Canonical operational planning tool for Phase 1

## Objective Alpha

> The first fully autonomous paper trade from signal generation through result
> recording without human intervention.

This register contains everything currently preventing Objective Alpha. Every
future engineering sprint must reference the blocker it removes or reduces.

## Status and severity

Allowed status values are `OPEN`, `IN_PROGRESS`, `BLOCKED`, and `RESOLVED`.
Blocking severity is `Critical`, `Major`, or `Minor`. A blocker remains in the
register after resolution so the exit evidence and dependency history remain
auditable.

## ALPHA-B001: Continuous autonomous engine

- **Title:** Continuous autonomous engine
- **Description:** One unattended runtime must continuously connect market
  input, signal generation, paper position lifecycle, and result persistence.
- **Owner:** Shared
- **Current status:** IN_PROGRESS
- **Blocking severity:** Critical
- **Exit condition:** A bounded unattended run completes the full runtime loop
  without human action, duplicate state, or an unhandled integrity failure.
- **Latest evidence:** The third soak ran for 24 hours with complete source
  continuity and exact paper reconciliation, but the runtime stopped four
  terminal records before `session_completed`. Terminal drain and source-health
  reconciliation now pass delayed, multi-batch fixtures. A fourth-soak attempt
  aborted before managed-runtime startup because PowerShell BOM config parsing
  failed; that Windows launch defect is fixed and one clean soak remains
  required for exit.
- **Dependencies:** None.

## ALPHA-B002: Automated paper execution

- **Title:** Automated paper execution
- **Description:** Qualified signals must create, manage, close, and record
  paper trades through the approved strategy semantics without manual action.
- **Owner:** Repricing
- **Current status:** RESOLVED
- **Blocking severity:** Critical
- **Exit condition:** A qualifying live-input signal produces one complete,
  auditable paper trade and recorded result under frozen strategy behavior.
- **Exit evidence:** The first Repricing soak persisted 60 unique public-input
  signals as 60 positions and 60 closed trades with no duplicate business keys
  and no manual intervention.
- **Dependencies:** ALPHA-B001.

## ALPHA-B003: Restart-safe recovery

- **Title:** Restart-safe recovery
- **Description:** Runtime interruption must not lose, duplicate, reopen, or
  corrupt paper positions, events, trades, or result state.
- **Owner:** Repricing
- **Current status:** IN_PROGRESS
- **Blocking severity:** Critical
- **Exit condition:** End-to-end restart evidence proves deterministic recovery
  with an active paper position and preserves exactly-once business state.
- **Dependencies:** ALPHA-B001, ALPHA-B002.

## ALPHA-B004: Supervisor process

- **Title:** Supervisor process
- **Description:** The autonomous runtime requires single-instance lifecycle
  control, bounded restart behavior, graceful shutdown, and fail-closed stops.
- **Owner:** Infrastructure
- **Current status:** IN_PROGRESS
- **Blocking severity:** Critical
- **Exit condition:** Supervised operation starts once, rejects a competing
  instance, recovers only approved transient failures, and stops closed on
  integrity failures.
- **Latest evidence:** Third-soak single-instance ownership, active sleep
  inhibition, watchdog health, and bounded shutdown passed. The supervisor
  now rejects false clean stops and requires bounded terminal drain; unattended
  validation remains required.
- **Dependencies:** ALPHA-B001, ALPHA-B003.

## ALPHA-B005: Telegram live alerts

- **Title:** Telegram live alerts
- **Description:** Material paper-trading events, health failures, and shutdown
  conditions require automated outbound operator notification.
- **Owner:** Infrastructure
- **Current status:** OPEN
- **Blocking severity:** Major
- **Exit condition:** A paper signal, paper close, critical health failure, and
  shutdown state each produce a durable, deduplicated Telegram alert without
  affecting strategy state.
- **Dependencies:** ALPHA-B004, ALPHA-B007.

## ALPHA-B006: Daily automatic reporting

- **Title:** Daily automatic reporting
- **Description:** Paper activity and operating health must be summarized
  automatically at a stable UTC boundary without manual report assembly.
- **Owner:** Shared
- **Current status:** IN_PROGRESS
- **Blocking severity:** Major
- **Exit condition:** A completed operating day produces one deterministic,
  reconciled report covering paper trades, results, runtime, and failures.
- **Latest evidence:** Third-soak daily output remained current and paper
  results reconciled, but the runtime did not consume terminal source health.
  Completion and cursor state are now explicit; a fresh soak must prove final
  report reconciliation.
- **Dependencies:** ALPHA-B002, ALPHA-B007.

## ALPHA-B007: Production health monitoring

- **Title:** Production health monitoring
- **Description:** The runtime must expose current heartbeat, source freshness,
  API health, integrity status, restart state, and duplicate-protection state.
- **Owner:** Infrastructure
- **Current status:** IN_PROGRESS
- **Blocking severity:** Critical
- **Exit condition:** Health evidence remains current during unattended
  operation and every critical stale, integrity, API, restart, or duplicate
  condition is visible and fail-closed.
- **Latest evidence:** Third-soak heartbeat and host-suspend protection remained
  healthy for 24 hours. Production health still lacks proof that the runtime
  consumes and reports final `session_completed` health before stopping. The
  new completion/drain fields pass fixtures but need live validation.
- **Dependencies:** ALPHA-B004.

## ALPHA-B008: End-to-end Objective Alpha evidence

- **Title:** End-to-end Objective Alpha evidence
- **Description:** Component readiness must be demonstrated as one integrated,
  fully autonomous paper-trading cycle rather than inferred from isolated
  tests.
- **Owner:** Shared
- **Current status:** BLOCKED
- **Blocking severity:** Critical
- **Exit condition:** One reproducible signal-to-result paper trade completes
  without human intervention and all event, position, trade, result, report,
  alert, and health evidence reconciles.
- **Dependencies:** ALPHA-B001, ALPHA-B002, ALPHA-B003, ALPHA-B004,
  ALPHA-B005, ALPHA-B006, ALPHA-B007.

## Planning rule

`LAUNCH_BLOCKERS.md` is the primary operational planning tool for Phase 1. A
sprint that does not reduce a blocker or increase evidence-based confidence
toward Objective Alpha requires explicit CEO justification before it starts.
