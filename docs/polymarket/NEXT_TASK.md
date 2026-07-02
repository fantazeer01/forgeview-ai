# Polymarket Next Task

Last updated: July 3, 2026
Task status: ACTIVE

This file contains exactly one active task. Read canonical project memory
before starting it.

## Active task: Run Repricing Execution Latency Feasibility Audit v1

### Objective

Determine whether the frozen detector can be observed, processed, and paper
executed within a measurable latency budget that preserves positive expectancy,
without changing detector behavior or optimizing thresholds.

### Required scope

1. Use only admitted Repricing sessions and existing runtime telemetry.
2. Decompose end-to-end latency into source publication, polling, detection,
   processing, persistence, and hypothetical order-transmission components.
3. Measure the available timing resolution and identify which latency terms
   are observed, bounded, inferred, or missing.
4. Compare feasible latency budgets with the cost-stress break between
   immediate/one-second and two-second executable replay.
5. Determine whether existing public capture can support a defensible latency
   claim or whether higher-frequency prospective data is required.
6. Conclude `FEASIBLE`, `NOT_FEASIBLE`, or `INSUFFICIENT_MEASUREMENT` and define
   one successor task.

### Forbidden

- no detector, threshold, target, stop, timeout, or evidence-gate change;
- no new long campaign;
- no holdout inspection or evaluation;
- no production model training;
- no wallet, private key, order placement, or live trading;
- no optimization against historical P&L.

### Acceptance criteria

- deterministic latency decomposition with explicit provenance;
- clear separation of measured versus assumed latency;
- direct comparison to the observed executable-cost break point;
- one conclusion and exactly one active successor task;
- all relevant tests pass.
