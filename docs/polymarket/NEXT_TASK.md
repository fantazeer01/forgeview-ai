# Polymarket Next Task

Last updated: July 3, 2026
Task status: ACTIVE

This file contains exactly one active task. Read canonical project memory
before starting it.

## Active task: Implement Repricing No-Order Calibration Host Containment Preflight v1

### Objective

Implement a read-only Windows host-containment inspector and fixture isolation
launcher that can prove whether firewall, proxy, process, environment and
operator prerequisites are present without applying host changes or using
credentials.

### Required scope

1. Inspect Windows Firewall profile and process-specific outbound-rule state.
2. Validate direct-egress denial and local-proxy-only design using fixtures.
3. Implement a restricted fixture child-process launcher with an exact clean
   environment, bounded lifetime and no shell/child-process capability.
4. Generate but do not execute proposed firewall/proxy configuration and
   rollback commands for independent review.
5. Validate kill-switch, parent death, proxy loss, log failure and rollback
   drills at the fixture boundary.
6. Define operator/revocation/authorization record templates without names or
   secrets.

### Forbidden

- no firewall, registry, service, account or host-policy modification;
- no real credential, wallet, private key, API secret or passphrase;
- no authenticated endpoint connection or credential provisioning;
- no real order, cancellation or heartbeat;
- no strategy, threshold, evidence-gate or production execution change;
- no sealed holdout inspection or evaluation.

### Acceptance criteria

- deterministic host preflight with explicit pass/fail evidence;
- fixture child process cannot inherit forbidden environment names;
- proposed controls and rollback are reviewable but never executed;
- all missing governance assignments remain blockers;
- relevant and full repository tests pass;
- exactly one successor task remains.
