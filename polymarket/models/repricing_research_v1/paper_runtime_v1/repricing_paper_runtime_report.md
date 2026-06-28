# Managed Repricing Paper Runtime Loop v1

Date: June 28, 2026

## Result

PASS for bounded, fixture-driven paper operation. The frozen repricing paper
core can now run through a managed polling loop over an existing append-only v5
JSONL stream. It opens and closes paper positions, persists every state change,
recovers after restart, emits atomic health state, and exits gracefully.

This result does not authorize an unattended public paper campaign. Runtime
supervision, stale-feed policy, session rotation, disk/write circuit breakers,
and soak evidence remain outstanding.

## Entrypoint

Installed command:

```text
repricing-paper-runtime --session <session.jsonl> --database <paper.sqlite3> --health <health.json>
```

Bounded dry-run example:

```text
repricing-paper-runtime --session <fixture.jsonl> --database <paper.sqlite3> --health <health.json> --dry-run --max-polls 1
```

The entrypoint also supports `--poll-interval`, `--max-runtime-seconds`, and
`--max-polls`. Dry-run mode requires a poll or runtime bound.

## Runtime Contract

- Opens the existing restart-safe SQLite paper core.
- Recovers pending journal events and open positions before polling.
- Starts the v5 JSONL adapter against one source session.
- Accepts only complete, structurally valid, chronologically ordered events.
- Commits paper state through the existing event-first transactional ledger.
- Repeated source events remain idempotent after restart.
- Ctrl+C and termination signals request a graceful stop where supported.
- Shutdown finishes the current atomic operation, closes SQLite, and leaves
  open positions persisted rather than force-closing them.
- Invalid complete stream data records failed health and propagates the error.

## Health Telemetry

The health JSON is replaced atomically after startup, every completed poll,
failure, and shutdown. It contains:

- status;
- runtime start and stop timestamps;
- last poll timestamp;
- last source event timestamp;
- events received, accepted, and rejected;
- duplicate events skipped;
- positions opened and closed during the runtime;
- recovered and current open positions;
- polls completed;
- last error;
- source and database paths;
- frozen strategy fingerprint;
- dry-run flag.

`events_accepted` means newly journaled valid v5 records. `events_rejected`
counts complete stream records that fail closed validation. Detector admission
is not redefined; actual paper entries and exits are represented by the
position counters.

## Validation

Eight dedicated runtime tests passed:

- clean bounded start and stop;
- event flow into durable position and trade state;
- duplicate source replay after restart;
- open-position recovery followed by an appended close;
- failed-closed invalid stream telemetry;
- pre-requested graceful stop with a recoverable ledger;
- byte-deterministic bounded dry-run health output with a fixed clock;
- CLI bounded dry-run contract.

The combined repricing suite passed 28 tests. The complete repository suite
passed 167 tests.

No detector logic, frozen threshold, holdout artifact, Telegram integration,
wallet/private-key path, order-placement path, or real-money execution code
was changed.

## Remaining Blockers

- external single-instance supervision and restart policy;
- source session rotation and rollover validation;
- stale-feed, disk-space, write-latency, and write-failure thresholds;
- daily paper statistics and equity summaries;
- supervised restart drills and a minimum 24-hour paper soak;
- optional persisted notification outbox and disabled-by-default Telegram
  adapter remain future work.

The required repricing successor is **Repricing Paper Runtime Supervision And
Soak Sprint v1**.
