# Repricing Terminal Drain And Session Completion Fix v1

Verdict: `READY_FOR_FOURTH_24H_SOAK_PREFLIGHT`

## Root Cause

Third 24-Hour Repricing Paper Soak v1 exposed two coupled terminal-contract
defects. The producer appended three final `shadow_trade` summaries using each
trade's historical close timestamp after a final checkpoint timestamped
`2026-07-01T18:52:39.372316Z`. This moved the JSONL envelope backward in time.
The runtime adapter correctly rejects backward envelope timestamps.

Independently, `max_runtime_seconds` was an immediate watchdog stop. The
runtime had no bounded phase for waiting on producer finalization, draining
post-checkpoint summaries, consuming `session_completed`, or proving that its
cursor matched source EOF. It therefore stopped cleanly at cursor 741,528 while
the source finalized through 741,532.

## Prior Safeguards

The sleep, liveness, backpressure, and atomic-ledger fixes worked correctly.
The third soak had no host suspend, watchdog failure, fatal marker, backlog,
duplicate, rejected stream event, or open position. Its 175 live paper trades
reconciled exactly to replay. Those safeguards did not address producer
terminal ordering or deadline-to-completion coordination.

## Fix

- terminal `shadow_trade` envelope timestamps now use final append time;
  historical close time remains in the payload;
- production managed runtimes require `session_completed`;
- nominal runtime expiry enters a bounded 60-second `DRAINING` phase rather
  than stopping immediately;
- completion is successful only when terminal health is `complete`, source
  remaining bytes are zero, and the final event is durably committed;
- missing terminal completion fails closed as `TERMINAL_DRAIN_INCOMPLETE`;
- missing or disagreeing campaign/continuity markers fail closed as
  `SESSION_HEALTH_INCOMPLETE`;
- the MVP independently rejects any runtime that returns `STOPPED` without
  verified terminal reconciliation;
- heartbeat output exposes completion and drain state.

Regression coverage uses delayed post-deadline append, 258 terminal records,
32-event batches, exact cursor EOF, missing completion, missing health fields,
and a false clean-stop runtime. The v5 mock capture also proves append-monotonic
terminal envelopes and `session_completed` as the final event.

No new soak was launched. The frozen detector, fingerprint, thresholds,
target, stop, timeout, slippage, evidence gates, and sealed holdout boundary
are unchanged.

## Validation

- Repricing suite: 58 tests passed.
- Full repository suite: 204 tests passed.
- `git diff --check`: passed (line-ending conversion warnings only).
