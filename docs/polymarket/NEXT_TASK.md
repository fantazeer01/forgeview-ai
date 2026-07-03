# Polymarket Next Task

Last updated: July 4, 2026
Task status: ACTIVE

This file contains exactly one active task. Read canonical project memory
before starting it.

## Active task: Run Repricing Slower-Horizon Derivative Validation v1

### Objective

Attempt to disprove whether the preserved public Repricing evidence contains a
cost-aware continuation or reversion effect at fixed 30, 60, 120, and 180
second horizons that is less sensitive to the known two-second execution
failure. Use existing public sessions only.

### Required scope

1. Freeze the existing valid Repricing sessions, signal anchors, four forward
   horizons, cost model, and continuation/reversion definitions before reading
   derivative results.
2. Use strict chronological, session-grouped evaluation with no same-market or
   overlapping-window leakage between development and evaluation folds.
3. Evaluate each horizon as a separate preregistered hypothesis and report
   multiplicity-adjusted statistical confidence; do not select the best result
   as a new strategy after inspection.
4. Compare against matched random timing, Polymarket price movement, and zero
   net expectancy after conservative spread, slippage, fees, and latency.
5. Report sample size, expectancy, drawdown, asset/side/session concentration,
   fold stability, timing sensitivity, and missing-data exclusions.
6. Choose one portfolio result: advance one already-preregistered derivative
   to bounded prospective shadow, or permanently reject the slower Repricing
   derivative family.

### Forbidden

- no new public capture campaign;
- no credentials, authenticated endpoints, wallet/private-key logic or orders;
- no sealed holdout inspection or evaluation;
- no production model training;
- no threshold, horizon, asset, side or session selection after results;
- no reactivation of Wallet Intelligence;
- no profitability or deployment claim from retrospective evidence alone.

### Acceptance criteria

- deterministic existing-data evaluation with fixed manifests and hashes;
- strict chronological/session leakage audit;
- conservative executable-cost sensitivity and adjusted confidence reported;
- one evidence-driven portfolio decision;
- relevant and full repository tests pass;
- exactly one active successor remains.
