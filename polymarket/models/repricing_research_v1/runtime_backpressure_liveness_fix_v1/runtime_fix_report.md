# Repricing Runtime Backpressure And Liveness Fix v1

Verdict: `READY_FOR_SECOND_24H_SOAK_PREFLIGHT`

## Failure Diagnosis

The first soak heartbeat stopped at `2026-06-28T21:04:31.905461+00:00`,
12,310.53587 seconds after runtime start. The source capture continued emitting
checkpoints until `2026-06-29T11:43:08.054053+00:00` and completed at
`2026-06-29T18:15:42.387630+00:00`. The paper ledger also continued advancing
without current telemetry, reaching source event 351,230.

`V5JsonlPaperAdapter.sync()` consumed until EOF, but the source file was growing.
Each event also paid two `SQLite synchronous=FULL` commits: one to journal the
raw row and one to apply it and advance the cursor. The adapter therefore fell
behind and did not return to the managed loop. Heartbeat writes, stale checks,
and maximum-runtime checks existed only outside `sync()`, so none could stop or
report the unhealthy in-flight operation.

## Runtime Fix

- source reads are capped at 1,000 events per batch and one MiB per JSONL line;
- each bounded batch journals, applies, and advances the cursor in one atomic
  transaction rather than two durable commits per event;
- a 64 MiB uncommitted-backlog ceiling stops closed on overload;
- progress callbacks run inside the transaction, allowing watchdog failure to
  roll back the full in-flight batch;
- an independent watchdog enforces a 30-second processing-progress ceiling and
  the configured runtime deadline;
- heartbeat diagnostics include progress time, batch count, backlog bytes,
  batch-limit state, watchdog state, fatal code, and safe-shutdown marker path;
- liveness, overload, invalid source, and incomplete terminal session health
  produce a durable `FAILED_CLOSED` marker and no silent continuation;
- a terminal `session_completed` event cannot pass when campaign completeness
  or observation continuity is unhealthy;
- restart verification remains bounded and exactly-once from the durable
  source cursor.

The frozen detector, target, stop, timeout, slippage, admission reasons,
strategy fingerprint, evidence gates, and holdout policy are unchanged.

## Validation

- simulated telemetry stall: pass;
- backpressure overload: pass;
- durable fail-closed shutdown marker: pass;
- 5,000-event healthy bounded path: pass;
- 5,000-event committed-prefix restart plus 100-event catch-up: pass;
- incomplete terminal session health rejection: pass;
- preserved-soak 10,000-event bounded replay: 0.479278 seconds, 20,864.72
  events/second, 10 batches, no watchdog trip;
- Repricing tests: 51 passed;
- full repository tests: 197 passed.

No capture or soak was launched. A second 24-hour paper soak is allowed only as
the next explicit task and only after a fresh green preflight.
