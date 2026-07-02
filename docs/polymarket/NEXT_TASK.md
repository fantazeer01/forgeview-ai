# Polymarket Next Task

Last updated: July 3, 2026
Task status: ACTIVE

This file contains exactly one active task. Read canonical project memory
before starting it.

## Active task: Implement Repricing Authenticated Execution Latency Dry-Run Harness v1

### Objective

Implement the deterministic no-secret measurement harness defined by the
authenticated execution latency protocol, proving timestamp, correlation,
replay, redaction and fail-closed behavior without contacting authenticated
endpoints or creating orders.

### Required scope

1. Implement the canonical event envelope and deterministic event IDs.
2. Implement signer, credential-provider and order-transport interfaces with
   fixture/stub implementations only.
3. Implement a local HTTP execution sink and fixture user-channel lifecycle.
4. Measure signal, decision, sign, serialization, queue, request, response,
   acceptance, fill, cancellation and reconciliation stages.
5. Implement clock-offset monitoring, bounded retries, ambiguous-response
   reconciliation, secret redaction, append-only journaling and replay.
6. Add failure-injection tests for duplicate, timeout, partial fill, disconnect,
   clock drift, secret leakage and terminal disagreement.

### Forbidden

- no real credential, wallet, private key, API secret or passphrase;
- no authenticated Polymarket endpoint or real order/cancellation;
- no strategy, threshold, evidence-gate or production execution change;
- no sealed holdout inspection or evaluation;
- no production model training or evidence campaign.

### Acceptance criteria

- deterministic fixture replay and identical summary hashes;
- zero secret-bearing fields in journals and exports;
- duplicate and ambiguous submissions fail closed;
- no network destination except the local fixture sink;
- relevant and full repository tests pass;
- exactly one successor task remains.
