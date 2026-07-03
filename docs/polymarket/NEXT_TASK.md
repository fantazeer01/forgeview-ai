# Polymarket Next Task

Last updated: July 3, 2026
Task status: ACTIVE

This file contains exactly one active task. Read canonical project memory
before starting it.

## Active task: Prepare Repricing Host Containment Remediation And Governance Package v1

### Objective

Prepare an exact, reviewable Windows containment and governance change package
that could satisfy the failed preflight gates after separate approval. Do not
apply host changes and do not use credentials.

### Required scope

1. Resolve the exact calibration executable, local proxy endpoint and rule
   precedence required for proxy-only egress.
2. Produce reviewed firewall apply, verification and rollback scripts in
   non-executing dry-run form.
3. Specify restricted process identity, filesystem, shell and child-process
   controls for Windows.
4. Define kill-switch/watchdog host drill procedures.
5. Finalize non-secret owner, revocation, incident, provider and expiring
   authorization record schemas.
6. Produce a change-impact and rollback review for explicit approval.

### Forbidden

- no firewall, registry, service, account or host-policy modification;
- no execution of generated remediation commands;
- no real credential, wallet, private key, API secret or passphrase;
- no authenticated endpoint connection or credential provisioning;
- no real order, cancellation or heartbeat;
- no strategy, evidence-gate or holdout change.

### Acceptance criteria

- exact commands are inert artifacts and separately reviewable;
- rollback precedes apply and covers unrelated-host impact;
- governance templates contain no identities or secrets;
- package states the explicit approval required before execution;
- relevant and full repository tests pass;
- exactly one successor task remains.
