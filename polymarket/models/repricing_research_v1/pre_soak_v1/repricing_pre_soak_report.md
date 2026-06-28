# Repricing Pre-Soak Consolidation v1

Verdict: `READY_FOR_24H_SOAK`

Verified: June 28, 2026

## Machine Preflight

- Windows AC sleep timeout: 0 seconds;
- Windows AC hibernate timeout: 0 seconds;
- overnight power status: safe;
- free disk: 35,648,344,064 bytes;
- required disk floor: 2,147,483,648 bytes;
- measured marker write latency: 0.694 ms;
- write-latency ceiling: 500 ms;
- stale-event ceiling: 30 seconds;
- source root rotation: enabled;
- selected existing public source:
  `repricing_balanced_v1_batch_002/20260625_200724/session.jsonl`.

## Gates

- power_safe: PASS
- disk_reserve_pass: PASS
- preflight_write_latency_pass: PASS
- session_rotation_pass: PASS
- stale_event_guard_pass: PASS
- write_latency_guard_pass: PASS
- restart_with_open_position_pass: PASS
- restart_during_processing_pass: PASS
- restart_after_graceful_shutdown_pass: PASS

## Validation

- latest-session resolution excludes the copied `latest` directory and selects
  the newest timestamped v5 session;
- runtime rotation moved from one source session to the next while preserving
  one position and one close;
- stale source time failed closed;
- write latency above the configured ceiling failed closed;
- restart with an open position preserved exactly one position;
- interruption after position creation recovered deterministically;
- graceful shutdown preserved the open position and the next run closed it;
- Repricing tests: 45 passed;
- full repository tests: 191 passed.

## Remaining Blockers

- None before an explicitly authorized 24-hour soak.

No soak was launched. Detector logic, thresholds, strategy, holdout,
and live-trading boundaries remain unchanged.
