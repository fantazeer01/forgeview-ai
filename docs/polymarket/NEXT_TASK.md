# Polymarket Next Task

Last updated: July 3, 2026
Task status: ACTIVE

This file contains exactly one active task. Read canonical project memory
before starting it.

## Active task: Integrate Repricing Latency Dry-Run Harness With Public Event Stream v1

### Objective

Feed real public CLOB and external-price WebSocket events into the validated
local-only execution latency harness to measure live signal-to-local-sink flow,
correlation, clock behavior and backpressure without credentials or orders.

### Required scope

1. Adapt public WebSocket events into the dry-run harness input contract.
2. Preserve frozen detector logic and all deterministic correlation fields.
3. Use only fixture signer/authentication and the `127.0.0.1` execution sink.
4. Measure event receipt through local acknowledgement and terminal fixture
   state, including reconnect, stale-event and backlog behavior.
5. Run one bounded public engineering validation, not an evidence campaign.
6. Compare live client-path results with the local benchmark and protocol gates.

### Forbidden

- no real credential, wallet, private key, API secret or passphrase;
- no authenticated Polymarket endpoint or real order/cancellation;
- no strategy, threshold, evidence-gate or production execution change;
- no sealed holdout inspection or evaluation;
- no production model training or evidence campaign.

### Acceptance criteria

- public events reach the loopback sink with deterministic correlation;
- bounded queues, stale guards and disconnects fail closed;
- replay and redaction gates pass with zero duplicate correlations;
- authenticated exchange admission remains explicitly not evaluated;
- relevant and full repository tests pass;
- exactly one successor task remains.
