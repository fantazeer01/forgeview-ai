# Polymarket Next Task

Last updated: July 3, 2026
Task status: ACTIVE

This file contains exactly one active task. Read canonical project memory
before starting it.

## Active task: Implement Repricing Public WebSocket Latency Instrumentation v1

### Objective

Measure public market-event publication-to-receipt and event-to-decision
latency with persistent WebSockets, without orders, authentication, strategy
changes, or evidence claims.

### Required scope

1. Implement a bounded public CLOB market WebSocket observer and compatible
   external BTC/ETH/SOL streaming timestamp observer.
2. Record server event timestamp, local receive timestamp, parse completion,
   frozen detector completion, and durable-journal completion separately.
3. Measure minimum, median, p95, p99, and maximum latency, disconnects,
   sequence gaps, clock assumptions, and event age.
4. Run only a short bounded engineering validation, not an evidence campaign.
5. Compare measured event-to-decision p95 with the remaining order/match budget
   under the two-second economic break point.
6. Conclude whether authenticated execution feasibility deserves a separately
   authorized design or the branch should be deprioritized.

### Forbidden

- no trading strategy, threshold, or evidence-gate change;
- no long evidence run;
- no wallet, private key, authentication, order submission, or live trading;
- no sealed holdout inspection or evaluation;
- no production model training.

### Acceptance criteria

- bounded deterministic output schema and timestamp provenance;
- explicit measured versus inferred latency fields;
- no credentials or execution methods in the module;
- relevant and full repository tests pass;
- exactly one successor task remains.
