# Repricing Paper Trading MVP Launch Plan

## Smallest Safe Architecture

```text
Existing public v5 feeds and LagDetector (unchanged)
                         |
                         v
              append raw event before action
                         |
                         v
          Frozen Repricing Admission Consumer
       reasons + expiry + side + overlap only
                         |
                         v
             SQLite Paper State Ledger
 signals | open positions | trades | cursor
                         |
              +----------+----------+
              |                     |
              v                     v
      Target/Stop/Timeout       Telemetry Outbox
         State Machine          file + Telegram
              |                     |
              +----------+----------+
                         v
             UTC Daily Research Summary
```

SQLite is the smallest appropriate state layer because it is in the Python
standard library and provides transactions, uniqueness constraints, restart
recovery, and atomic cursors without adding a service dependency. Raw JSONL
remains the immutable replay source.

## Frozen Contract

The MVP must fail startup if its strategy fingerprint differs from:

- external move threshold: 6 bps;
- repricing ratio: 0.65;
- minimum confidence: 0.45;
- minimum entry time: 60 seconds;
- accepted reasons: `qualified_external_move_not_repriced` and
  `confidence_below_threshold`;
- side: YES for UP, NO for DOWN;
- target: +0.03;
- stop: -0.03;
- timeout: 180 seconds;
- conservative slippage: 0.02;
- no overlapping position for the same market and side.

## Delivery Sequence

### Phase 1: Causal Core, 2.75 Days

- Create the separate repricing paper state machine.
- Consume existing lag measurements without changing `LagDetector`.
- Implement frozen admission, entry, target, stop, timeout, and expiry.
- Persist signals, positions, closes, PnL, and strategy fingerprint.

Exit gate: deterministic event fixtures produce the same rows as offline
repricing replay for equivalent causal data.

### Phase 2: Persistence and Recovery, 3.25 Days

- Add SQLite schema, transactions, event cursor, and unique constraints.
- Restore open positions after restart.
- Replay unprocessed raw events before accepting new events.
- Add single-instance lock and daily session rotation without forced closes.

Exit gate: injected crashes before and after each state transition produce no
lost or duplicate signal, position, close, or PnL record.

### Phase 3: Operations, 1.75 Days

- Add UTC daily statistics and equity snapshots.
- Add heartbeat, stale-feed, exception, disk, and write-latency telemetry.
- Add optional outbound-only Telegram notifications with environment-based
  secrets, retry limits, and a persisted outbox.
- Add Windows supervised launch with bounded restart backoff and sleep
  inhibition.

Exit gate: notification failure never blocks trading-state persistence, and
the supervisor cannot start a second process.

### Phase 4: Validation and Soak, 2.00 Days

- Add fixture replay equivalence, restart, duplicate, stale-feed, outage,
  Telegram-failure, and date-rollover tests.
- Run the full repository suite.
- Run a minimum 24-hour public-only paper soak with no mock fallback.

Exit gate: 100% checkpoint coverage target, no gap above 300 seconds, no lost
or duplicate transitions, successful restart recovery, deterministic daily
exports, and no holdout access.

## Effort and Earliest MVP

- component estimate: 9.75 engineer-days;
- planning range: 9-11 engineer-days for one engineer;
- earliest continuously running MVP: end of engineer-day 10 if no external
  blocker occurs;
- earliest initial readiness evidence: day 11 after one complete 24-hour soak;
- prudent calendar estimate: 11-15 calendar days.

## Launch Decision

Launch is **not authorized now**. The next sprint should implement only the
restart-safe causal paper core and prove replay equivalence. Telegram,
supervision, and the public soak remain subsequent gates; no threshold or
detector change is part of this plan.
