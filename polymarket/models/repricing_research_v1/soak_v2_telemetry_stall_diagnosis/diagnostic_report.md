# Repricing Soak v2 Telemetry Stall Diagnosis

Verdict: `ROOT_CAUSE_CONFIRMED_HOST_SUSPEND`

## Root Cause

The second soak did not encounter ingestion backpressure or a SQLite deadlock.
Windows entered S3 sleep through an Application API at
`2026-06-30T17:52:16.060434Z` and resumed at
`2026-06-30T18:07:06.226392Z`. The Power-Troubleshooter recorded a
890.165958-second low-power interval and power-button wake. Kernel-Power Event
42 identifies the sleep reason as `Application API`; the machine did not
reboot.

The source checkpoint before sleep was event index 685145 at
`2026-06-30T17:52:16.146150Z`. Runtime health logs stop after that committed
batch and resume 900.159992 seconds later. The source itself contains an
891.868253-second checkpoint gap. On resume, the independent watchdog observed
that processing had made no progress for longer than its 30-second threshold,
wrote the durable fail-closed marker, and stopped the paper runtime. The public
producer later continued, which is why the immutable session contains events
beyond the durable paper cursor.

## Previous Safeguards

The previous fix was partially working, not bypassed:

- bounded batches prevented unbounded consume-to-EOF behavior;
- the backlog remained far below the 64 MiB ceiling;
- the ledger stopped at a complete atomic batch with SQLite integrity `ok`;
- all 84 paper signals, positions, and trades reconciled to deterministic
  offline export;
- the watchdog wrote a durable marker and prevented silent continuation.

Two operational gaps remained. Static preflight verified AC sleep and
hibernate timers were zero, but the canonical managed runtime did not activate
the repository's existing `WindowsSleepInhibitor`. A direct Application API
sleep can occur independently of timer settings. Also, the watchdog used the
generic `TELEMETRY_STALLED` code even when the watchdog thread itself had not
been scheduled across a whole-host sleep interval.

## Fix

- `ContinuousRepricingPaperMVP` now holds `WindowsSleepInhibitor` for the full
  single-instance managed runtime lifetime.
- Runtime preflight reports that the sleep inhibitor is required.
- The watchdog tracks its own scheduling cadence. A gap at least five times
  the processing-stall threshold fails closed as `HOST_SUSPEND_DETECTED`;
  ordinary active-batch stalls remain `TELEMETRY_STALLED`.
- Host suspension does not become recoverable and does not permit silent
  continuation. The frozen detector, strategy fingerprint, thresholds,
  target, stop, timeout, and slippage are unchanged.

## Evidence And Launch Status

The interrupted soak remains descriptive only and contributes nothing to
frozen evidence. Another 24-hour paper soak is allowed only as the next
explicit task after a fresh preflight, with the sleep inhibitor active and no
manual or application-triggered suspend. `ALPHA-B001`, `ALPHA-B003`,
`ALPHA-B004`, `ALPHA-B006`, and `ALPHA-B007` remain in progress;
`ALPHA-B008` remains blocked.

Validation passes: 26 focused runtime tests, 53 Repricing tests, and 199 full
repository tests.
