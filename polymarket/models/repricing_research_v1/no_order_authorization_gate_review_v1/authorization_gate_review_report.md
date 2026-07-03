# Repricing No-Order Calibration Independent Authorization Gate Review v1

## Decision

`NOT_AUTHORIZED`

Credentialed no-order calibration may not proceed. The application policy and
fixture sandbox are sound, but mandatory host-containment and governance gates
are absent. This sprint used no credentials, authenticated calls, wallet
material, orders, cancellations or holdout data.

## Evidence reviewed

- deny-by-default policy and exact route tests;
- allowed/forbidden action matrix;
- fixture sandbox implementation and 259-test validation baseline;
- secret redaction and clean-environment rules;
- zero-open-order gate;
- kill switch, watchdog and rollback hooks;
- hash-chained fixture audit replay;
- Windows Firewall profiles and matching outbound rules;
- repository evidence for process isolation, external secret operations,
  revocation ownership and expiring authorization.

Policy hashes reviewed:

- `credentialed_calibration_policy.py`:
  `01340ff1385740c903cfe74d4ccf232cb3b52723a61e982dc23844f158a75072`;
- `no_order_sandbox.py`:
  `3018664ef3ac1e6e51278d9f6e6f42616eaff16fff5a7dcd4f1e16bd712cf2c6`;
- calibration gate definition:
  `204ff05a3a2e132b7880db375c9c4bdad44dce1bc09533baca4c580dad51a7d5`;
- sandbox readiness status:
  `7e70e4a14bf8c2450fb9cf9e5f6b17b3d0f145ce0d102479b041d58041edea4c`.

## Passed gates

- exact deny-by-default application allowlist;
- fixture-only proxy and direct-egress abstraction denial;
- forbidden order/cancel/auth/heartbeat route tests;
- fixture secret handles and structural redaction;
- zero-open-order abort without cancellation;
- kill-switch, parent/deadline/proxy watchdog fixtures;
- deterministic audit replay and operator rollback hook;
- clean repository manifest and no calibration credential environment names.

## Blocking findings

### Host network containment

All Windows Firewall profiles reported `Enabled=False` and outbound policy
`NotConfigured`. No outbound rule matching ForgeView, Polymarket, Repricing or
Calibration was present. The fixture `via_proxy` flag is not OS-level direct
egress denial and cannot contain a compromised process.

### Process isolation

No implemented AppContainer, Windows Sandbox, restricted token, Job Object,
dedicated service account or equivalent calibration process boundary was found.
The current Python process can use normal host capabilities.

### Secret-provider operations

The protocol describes external injection, but no approved provider, operator
procedure, scoped access policy, expiry, retrieval audit or dry-run operational
evidence exists. The absence of calibration environment variables is correct
for this review but does not satisfy future provisioning readiness.

### Authorization and ownership

No unique expiring authorization record exists. No independent security/risk
approver, rollback operator, credential revocation owner or incident owner is
assigned. Documentation of a role is not evidence of an assigned person and
accepted run window.

### Host drills

Kill-switch, watchdog, proxy-loss and rollback behavior pass fixtures only.
No host-level firewall bypass, parent death, process escape, proxy termination,
credential revocation or post-incident reconciliation drill has been recorded.

## Preconditions for reconsideration

1. Enable and verify an appropriate Windows Firewall profile without disrupting
   unrelated host operations.
2. Install explicit deny-direct-egress rules for the calibration process and
   permit only a dedicated local proxy.
3. Implement restricted process identity/Job Object or stronger isolation and
   prove child-process and shell denial.
4. Select and approve an external L2 secret provider; document retrieval,
   expiry, access audit and revocation without private-key presence.
5. Assign independent approver, rollback operator, revocation owner and
   incident owner.
6. Create a unique, expiring, scope-bound authorization record for a future
   task; this review is not that authorization.
7. Run host-level bypass, kill-switch, proxy-loss, parent-death, log-failure and
   rollback drills using fixture handles only.
8. Re-run secret scan, policy hashes, environment checks and zero-open-order
   fixture gate after host controls are installed.

Only a new independent gate review may change the decision. Passing that review
would authorize a separate bounded calibration task, not execute it.
