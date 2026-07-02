# Polymarket Next Task

Last updated: July 3, 2026
Task status: ACTIVE

This file contains exactly one active task. Read canonical project memory
before starting it.

## Active task: Implement Repricing No-Order Calibration Sandbox Enforcement v1

### Objective

Implement and validate the local fixture sandbox, proxy allowlist, kill switch,
redaction and process-boundary controls required by the no-order security review
without using credentials or contacting authenticated endpoints.

### Required scope

1. Implement a local fixture egress proxy enforcing exact method/scheme/host/path
   decisions from `NoOrderCalibrationPolicy`.
2. Prove direct/non-proxy egress, redirects, unknown routes and every
   order/cancel/auth/heartbeat route fail closed.
3. Implement fixture-only secret-provider handles and clean environment
   allowlisting without real values.
4. Implement kill-switch, parent-death/proxy-loss and redaction failure drills.
5. Produce deterministic redacted audit logs and replay validation.
6. Keep all network traffic local and run comprehensive security tests.

### Forbidden

- no real credential, wallet, private key, API secret or passphrase;
- no authenticated endpoint connection or credential provisioning;
- no real order, cancellation or heartbeat;
- no strategy, threshold, evidence-gate or production execution change;
- no sealed holdout inspection or evaluation;
- no production model training or evidence campaign.

### Acceptance criteria

- all allowed fixture requests pass only through the local proxy;
- all forbidden and bypass attempts fail closed;
- audit output contains no fixture secret values;
- kill-switch and dependency-loss drills terminate cleanly;
- relevant and full repository tests pass;
- exactly one successor task remains.
