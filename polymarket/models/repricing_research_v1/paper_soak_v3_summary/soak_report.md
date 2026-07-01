# Third 24-Hour Repricing Paper Soak v1

Verdict: `FAILED_TERMINAL_DRAIN_RECONCILIATION`

Preflight passed with a clean synchronized repository, 416 GB free disk,
safe AC power settings, an active Windows `SYSTEM` sleep-inhibition request,
no competing runtime, and frozen strategy fingerprint
`d5d389be45d472628aab06b3aeeb281593e74d48b82902e12712047c91fec010`.
Exactly one public producer and one managed paper runtime ran. Windows recorded
no sleep or resume transition during the run.

The source capture completed its full 86,400-second monotonic duration. It
emitted `session_completed`, 43,200 / 43,200 checkpoints, 100% checkpoint
coverage, a 2.105269-second maximum gap, no gap over ten seconds, no fatal
capture error, and campaign/continuity statuses `complete` / `continuous`.
The public session contains 741,533 valid records and no malformed row.

The managed runtime stopped cleanly after 86,398.257341 wall-clock seconds,
with no watchdog trip, host-suspend detection, fatal marker, restart, rejected
stream event, backlog, duplicate, or open position. Its durable SQLite ledger
passes integrity and contains 175 signals, 175 positions, and 175 closed trades.
These paper records reconcile exactly to deterministic offline export by count,
asset, side, and after-slippage P&L.

Operational integrity nevertheless fails at terminal drain. The runtime cursor
stopped at event index 741,528 while the source ends at 741,532. The four
unconsumed records are three terminal `shadow_trade` rows followed by
`session_completed`. The shadow rows were appended after the final checkpoint
with historical timestamps earlier than that checkpoint, violating the stream
adapter's monotonic timestamp contract. The runtime therefore did not consume
or enforce terminal source health itself.

The deterministic descriptive result is 175 signals: BTC / ETH / SOL 33 / 39
/ 103; YES / NO 82 / 93; 120 wins; 68.571429% win rate; +0.0371228571
after-slippage expectancy; +6.4965 after-slippage P&L; and 0.77 maximum
drawdown. Exits were 120 repricing targets, 22 stop losses, and 33 timeouts.

Because operational integrity failed, the run is excluded from frozen evidence
despite complete source continuity and positive reproducible performance.
Scientifically valid evidence remains 172 signals, 24.000000389 hours, and two
independent sessions. Weak evidence remains below gate because 40 observed
hours and three valid sessions are required. The sealed holdout was not
inspected and no strategy parameter changed. All 53 Repricing tests and all 199
repository tests pass.
