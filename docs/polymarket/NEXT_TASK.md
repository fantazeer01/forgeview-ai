# Polymarket Next Task

Last updated: July 3, 2026
Task status: ACTIVE

This file contains exactly one active task. Read canonical project memory
before starting it.

## Active task: Prepare Repricing Credentialed No-Order Calibration Security Review v1

### Objective

Define and validate the security boundary required for a future separately
authorized credentialed read-only latency calibration, proving that no order or
cancellation route can be reached.

### Required scope

1. Specify process isolation and an external secret-provider contract.
2. Define an allowlist limited to authenticated user WebSocket, heartbeat and
   read-only order/trade query methods where current API semantics permit.
3. Prove order POST, batch order and cancellation methods are unreachable.
4. Define header/payload redaction, memory lifetime, audit hashes and incident
   response without using real credentials.
5. Define clock synchronization, connection warm-up and measurement gates.
6. Build static/fixture security validation only if needed; do not authenticate.

### Forbidden

- no real credential, wallet, private key, API secret or passphrase;
- no authenticated endpoint connection;
- no real order, cancellation, heartbeat or credential provisioning;
- no strategy, threshold, evidence-gate or production execution change;
- no sealed holdout inspection or evaluation;
- no production model training or evidence campaign.

### Acceptance criteria

- explicit threat model and endpoint capability matrix;
- mechanically testable deny-by-default policy;
- proof that order-capable routes are absent or unreachable;
- separate future authorization gate documented;
- relevant and full repository tests pass;
- exactly one successor task remains.
