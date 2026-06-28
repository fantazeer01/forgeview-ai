# v5 Paper Core Integration v1

Date: June 28, 2026

## Result

PASS. Existing v5 `session.jsonl` events can now be incrementally consumed by
the restart-safe frozen repricing paper core. The adapter passes canonical v5
events through unchanged after structural and ordering validation; it does not
recompute, alter, or optimize detector decisions.

## Integration Contract

- A stable source ID is the SHA-256 of the normalized absolute session path.
- The source path, first canonical event hash, and first event timestamp are
  persisted in the SQLite ledger.
- Complete UTF-8 JSONL records are ingested in zero-based source order.
- A trailing partial record is deferred until its newline arrives.
- Complete malformed records, timezone-naive timestamps, missing required v5
  fields, unsupported assets, and timestamp regressions fail closed.
- On restart, every committed source event is checked against the raw journal
  before appended events are accepted.
- Source replacement, committed-prefix mutation, and truncation before the
  durable cursor fail closed.
- Duplicate delivery is idempotent through source event and signal uniqueness.

## Frozen Strategy Preservation

The adapter retains the existing strategy fingerprint and paper-core rules:

- accepted detector reasons are unchanged;
- UP maps to YES and DOWN maps to NO;
- minimum entry time is 60 seconds;
- target and stop are 0.03 contract-price points;
- timeout is 180 seconds;
- conservative slippage is 0.02 per paper signal;
- no overlapping open position is allowed for the same market and side;
- target, stop, timeout, and lifecycle expiry transitions remain causal.

## Audit Lineage

Every admitted signal stores its source ID and source event index. The source
table resolves that ID to the absolute JSONL path and immutable first-event
identity. The raw journal retains the canonical source event, and positions
and trades link back to the admitted signal. This provides the path:

`position/trade -> signal -> source ID/event index -> raw event/source path`.

## Validation

Nine dedicated adapter tests passed, covering event conversion and lineage,
duplicate delivery, restart with an open position, restart after close,
partial and invalid records, frozen side/timeout/slippage behavior, source
replacement and truncation refusal, and equivalence between interrupted and
uninterrupted ingestion. Non-finite market values and timestamp regression
also fail closed.

The combined repricing suite passed 20 tests. The complete repository suite
passed 159 tests.

No detector source, frozen threshold, holdout artifact, wallet/private-key
path, Telegram integration, or real-money execution code was changed.

## Remaining Blockers

The integration is callable and append-resumable, but it is not yet a managed
24/7 process. Remaining blockers are a single-instance runtime loop, graceful
shutdown, feed/session rotation, heartbeat and stale-feed telemetry, disk and
write-failure controls, daily statistics, and a supervised soak test. No
continuous campaign is authorized by this sprint.
