# Repricing No-Order Calibration Sandbox Enforcement v1

## Verdict

`SANDBOX_FIXTURE_READY_REAL_CALIBRATION_NOT_AUTHORIZED`

The fixture-only sandbox implements all application-layer controls required by
the security review without credentials, authenticated calls, wallet material,
orders, cancellations or network access.

## Implemented controls

- deny-by-default exact route policy;
- local deterministic proxy with no socket creation;
- explicit `via_proxy` requirement and direct-egress rejection;
- fixture secret handles and clean child environment-name allowlist;
- private-key/seed environment-name rejection;
- armed-file kill switch;
- parent, deadline and proxy-health watchdog checks;
- zero-open-order preflight that aborts without cancellation;
- redacted, deterministic, hash-chained audit journal;
- operator abort callback and rollback with automatic restart disabled.

## Validation

The executable fixture validation passed preflight, then allowed exactly three
post-preflight observational requests (`GET /trades`, `GET /time`, user
WebSocket connect) after the preflight `GET /data/orders`. It denied order POST,
cancel-all DELETE, heartbeat POST and an unknown route. Eight audit envelopes
replayed successfully with terminal hash
`6e6353ac8ad6522df320540f9f1ee6552585ed204e8fcbe301cc7445db170ba6`.

Dedicated tests additionally deny batch order, direct egress, parent death,
watchdog expiry and proxy loss; enforce the open-order gate without changing
the fixture order; verify kill-switch shutdown and rollback; and prove fixture
secret handles never appear in audit output.

## Safety result

- Real credentials used: 0.
- Authenticated calls: 0.
- Network calls: 0.
- Orders submitted: 0.
- Cancellations submitted: 0.
- Heartbeats submitted: 0.
- Wallet/private-key implementation: absent.
- Strategy, evidence and holdout changes: none.

## Residual boundary

This validates application and fixture enforcement, not OS firewall/process
isolation on a credential-bearing host. Real calibration remains unauthorized
until an independent authorization gate review verifies host-level direct
egress denial, process isolation, external secret-provider operations,
credential revocation ownership and the unique expiring authorization record.
