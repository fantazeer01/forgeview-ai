# Polymarket Next Task

Last updated: July 3, 2026
Task status: ACTIVE

This file contains exactly one active task. Read canonical project memory
before starting it.

## Active task: Run Repricing No-Order Calibration Independent Authorization Gate Review v1

### Objective

Independently determine whether host-level and procedural controls are
sufficient to authorize a future bounded credentialed no-order calibration.
This task does not provision or use credentials.

### Required scope

1. Verify the fixture sandbox evidence and exact policy hashes.
2. Review Windows process isolation and direct-egress firewall/proxy design.
3. Verify external secret-provider, clean-environment and revocation procedures.
4. Verify kill-switch, watchdog, rollback operator and incident ownership.
5. Verify unique expiring authorization-record requirements and run bounds.
6. Issue exactly one verdict: `AUTHORIZED_FOR_SEPARATE_BOUNDED_CALIBRATION`
   or `NOT_AUTHORIZED`, listing every unmet gate.

### Forbidden

- no real credential, wallet, private key, API secret or passphrase;
- no authenticated endpoint connection or credential provisioning;
- no real order, cancellation or heartbeat;
- no strategy, threshold, evidence-gate or production execution change;
- no sealed holdout inspection or evaluation;
- no production model training or evidence campaign.

### Acceptance criteria

- independent gate-by-gate review with evidence references;
- host and procedural gaps explicitly classified;
- verdict does not itself execute calibration;
- relevant and full repository tests pass;
- exactly one successor task remains.
