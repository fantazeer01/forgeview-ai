# Continuous Repricing Paper Trading MVP v1

Date: June 28, 2026

## Result

`PASS_BOUNDED_DRY_RUN`. ForgeViewAI now has one continuously runnable,
paper-only repricing entrypoint that composes the frozen paper core, v5 JSONL
adapter, managed poll loop, process lock, startup preflight, restart policy,
heartbeat, daily summary, and unified JSONL runtime log.

This is not a completed 24-hour paper soak and does not authorize live trading.

## Entrypoint And Configuration

Entrypoint:

```text
repricing-runtime-mvp --config <runtime.json>
```

The single JSON configuration defines the v5 session, state and output
directories, poll cadence, restart limit/backoff, optional poll/runtime bounds,
and dry-run mode. Relative paths resolve against the configuration file.

Derived state and output files:

- `repricing_paper.sqlite3`;
- `repricing_runtime.lock`;
- `repricing_runtime_status.json`;
- `repricing_runtime_heartbeat.json`;
- `repricing_runtime_summary.json`;
- `repricing_runtime.log`.

## Startup Preflight

Startup fails before polling unless:

- configuration values are valid;
- no configured path references a sealed/holdout location;
- the v5 session exists and contains a complete valid event;
- state and output directories are writable;
- the SQLite paper ledger opens and recovers;
- the frozen strategy fingerprint matches;
- the OS-level single-instance lock is available.

## Supervision

- Only one process may hold the byte-range runtime lock.
- Temporary source unavailability is explicitly recoverable and retries up to
  the configured limit with backoff.
- Malformed streams, source-integrity failures, fingerprint mismatches, and
  unexpected state errors fail closed without automatic retry.
- An unclean process restart reuses the prior session ID and increments the
  restart count.
- Ctrl+C/termination requests graceful shutdown; open positions remain in the
  durable ledger and are never force-closed because the process exits.

## Operational Outputs

The heartbeat is replaced atomically at startup, each poll, failure, and stop.
It exposes runtime liveness, last event/poll/successful processing time, last
error, frozen detector state, paper-core state, event counts, signal counts,
position counts, duplicates, and strategy fingerprint.

The UTC daily summary accumulates runtime duration across midnight boundaries,
events received, valid/rejected signals, opened/closed/current paper positions,
runtime failures, and restart count. The unified JSONL log records startup,
health snapshots, recoverable/unrecoverable failures, process recovery, and
shutdown.

## Validation

Eleven dedicated MVP tests cover:

- single JSON configuration and relative paths;
- startup preflight and holdout-path refusal;
- single-instance lock exclusion and clean reuse;
- bounded full-stack status, heartbeat, summary, and log output;
- recoverable restart and daily restart/failure accounting;
- valid and rejected detector-signal daily accounting;
- unrecoverable fail-closed behavior;
- process-crash session continuity;
- exact UTC midnight duration splitting;
- CLI single-config contract.

All 39 repricing tests and all 185 repository tests pass. Detector logic,
frozen thresholds, strategy behavior, sealed holdout, wallets/private keys,
and real-money order placement remain unchanged.

## Remaining 24-Hour Blockers

- verify Windows power policy and disk reserve immediately before launch;
- define the exact v5 producer/session rotation procedure for a 24-hour run;
- add stale-event and write-latency alert thresholds;
- conduct supervised restart drills while positions are open;
- complete one continuous 24-hour public paper soak with no duplicate or lost
  transitions;
- reconcile heartbeat, daily summary, raw events, positions, and trades after
  the soak.

The next Repricing branch task should be **Run First 24-Hour Repricing Paper
Soak Preflight v1**. It must not launch the soak until explicit authorization.
