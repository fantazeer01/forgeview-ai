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
- **Latest evidence:** The second soak preserved exact live/offline
  reconciliation but was interrupted by a Windows S3 sleep initiated through
  an Application API. The MVP now holds an active sleep inhibitor and reports
  host scheduling gaps separately; a fresh uninterrupted soak remains required
  for exit.
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
- **Latest evidence:** Single-instance ownership and fail-closed shutdown held
  during the second soak. The watchdog stopped on resume from an approximately
  890-second host sleep, but the cause was previously mislabeled. Active sleep
  inhibition and distinct host-suspend classification now require unattended
  validation.
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
- **Latest evidence:** Daily output was generated, but stopped with the stale
  heartbeat and did not reconcile the complete source or the 13-signal live
  shortfall.
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
- **Latest evidence:** The second-soak heartbeat paused with the entire host
  during S3 sleep and failed closed on resume. The runtime now distinguishes
  watchdog scheduling gaps from ingestion stalls and holds an active Windows
  sleep inhibitor; a fresh soak must verify sustained health.
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
