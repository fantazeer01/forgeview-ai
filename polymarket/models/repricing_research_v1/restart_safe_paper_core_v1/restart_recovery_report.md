# Restart-Safe Repricing Paper Core v1

Date: June 28, 2026

## Result

PASS. The frozen repricing paper contract now has a local, fixture-driven
SQLite execution foundation. It consumes existing raw v5 event shapes without
modifying the lag detector, detector thresholds, or the frozen research
contract.

## Durability Contract

- Raw events are committed to an append-only journal before state processing.
- Signal admission, position opening or closing, realized paper PnL, and the
  processed cursor commit in one SQLite transaction.
- Recovery replays only journal rows whose processed cursor was not committed.
- Signal, position, close, and open market/side constraints are enforced by
  database uniqueness rules.
- The frozen configuration is stored as SHA-256 fingerprint
  `d5d389be45d472628aab06b3aeeb281593e74d48b82902e12712047c91fec010`;
  a mismatch fails closed.

## Validation

Seven dedicated tests passed. They covered:

- open position restoration after process restart;
- duplicate raw input and duplicate signal suppression;
- closed positions remaining closed without duplicate PnL;
- deterministic recovery from six admission/open interruption boundaries;
- deterministic recovery from three close interruption boundaries;
- exact signal, exit, and PnL equivalence with the offline frozen simulator;
- expiry close from an existing v5 lifecycle event using the last durable quote;
- strategy fingerprint mismatch refusal.

The interruption boundaries were `after_raw_persist`,
`before_signal_admission`, `after_signal_admission`, `after_position_open`,
`after_trade_close`, `before_cursor_commit`, and `after_cursor_commit` as
applicable to open and close transitions. Repeated recovery produced one
signal, one position, at most one trade, and one realized PnL credit.

## Scope Boundaries

No capture or campaign was launched. No detector logic, frozen threshold,
holdout data, wallet integration, Telegram integration, statistics, or
operational reporting component was changed.

## Remaining Blockers

The core is not yet a continuously running paper engine. It still needs a
read-only adapter to the v5 event stream, process lifecycle supervision,
session rotation, operational telemetry, daily statistics, and a sustained
restart/soak validation. Telegram remains explicitly out of scope until the
execution path itself is validated.
