# Repricing Credentialed No-Order Calibration Security Review v1

## Security decision

`NOT_AUTHORIZED_SANDBOX_ENFORCEMENT_REQUIRED`

A future credentialed no-order calibration is scientifically useful but is not
authorized by this review. Polymarket L2 credentials are capability-bearing:
they authenticate read queries but also participate in trading operations.
Intent alone is therefore insufficient. A deny-by-default application policy,
isolated process, restrictive egress proxy and independent authorization must
all pass before any real credential is provisioned.

This sprint used no credentials, private keys, authenticated endpoints,
heartbeats, orders or cancellations.

## Exact future allowlist

Only these method, scheme, host and path tuples may be considered in a later,
separately authorized calibration:

- `GET https://clob.polymarket.com/data/orders`;
- `GET https://clob.polymarket.com/trades`;
- `GET https://clob.polymarket.com/time` (public clock calibration);
- `CONNECT wss://ws-subscriptions-clob.polymarket.com/ws/user`.

Query parameters may filter and paginate observations but may not alter the
path. Redirects are disabled. DNS resolution and certificate identity must
match the allowlisted host. The authenticated user WebSocket may receive only;
subscription messages are fixed-schema and redacted before audit storage.

## Forbidden actions

All non-allowlisted requests are denied, including all `POST`, `PUT`, `PATCH`
and `DELETE` calls; `/order`, `/orders`, every cancel route, `/heartbeats`, API
credential creation/derivation, balance/allowance mutation, relayer, bridge,
wallet, signing and settlement operations. No general-purpose CLOB SDK may be
loaded into the calibration process because its order methods expand the
reachable capability surface.

Heartbeat is explicitly forbidden. Although it can protect open-order
liveness, a no-order calibration must have no open orders and gains no required
measurement from a stateful authenticated POST.

## Threat model

Primary threats are accidental method/path reuse, compromised dependencies,
redirect or DNS confusion, secret leakage through logs/exceptions/core dumps,
environment inheritance, credential derivation from a private key, an
unexpected existing open order, replayed signatures, process crash, clock
drift, operator error and Git inclusion.

The largest residual risk is that API credentials are not proven by current
project evidence to be server-side read-only scoped. Client-side enforcement
must therefore assume they could authenticate state-changing methods.

## Enforcement layers

1. Dedicated calibration entrypoint with no signer or order model imports.
2. Exact application allowlist enforced before DNS or socket creation.
3. Local egress proxy permitting only allowlisted tuples and rejecting redirects.
4. Host firewall allowing only the proxy; direct CLOB egress denied.
5. Ephemeral isolated process with no shell, child-process or filesystem write
   access outside its run directory.
6. External secret provider injects only L2 API key, secret, passphrase and
   address after all preflight gates pass.
7. Kill-switch file and parent watchdog terminate the process and revoke egress.
8. All logs pass structural redaction before serialization.
9. Post-run credential revocation/rotation occurs outside this repository.

## Kill switch and fail closed

Missing authorization ID, missing kill switch, clock drift, redirect, unknown
host/path/method, WebSocket schema change, redaction failure, open-order
detection, log write failure, proxy failure, reconnect storm or process-health
loss immediately blocks new requests and closes all connections. No retry is
allowed after a policy denial or ambiguous authentication failure.

If `GET /data/orders` reports any open order, calibration stops before timing
admission. The process may not cancel that order; an independent operator must
investigate outside the calibration.

## Audit record

Store run/authorization IDs, code commit, policy hash, allowlist hash, request
method/host/path, monotonic and UTC timestamps, duration, response class,
redacted response schema hash, clock uncertainty, reconnect reason and terminal
status. Never store credential values, raw auth headers, user-channel auth
payloads, wallet identifiers, full order/trade payloads or process environment.

## Rollback

Trigger the kill switch, terminate the isolated process, revoke proxy egress,
verify no child process remains, hash and seal redacted logs, inspect public and
read-only order state through an independent approved path, rotate/revoke L2
credentials externally, preserve the incident report and return the project to
public-only operation. The calibration process itself never places or cancels
an order during rollback.

## Evidence required before authorization

- sandbox proof that only the four tuples can reach a local fixture proxy;
- static dependency/import proof that no signer/order SDK is reachable;
- denial tests for every documented order/cancel/auth/heartbeat route;
- redaction tests across logs, exceptions, crash reports and WebSocket payloads;
- environment isolation and forbidden-name tests;
- kill-switch, parent-death, proxy-loss and clock-drift drills;
- clean Git secret scan and artifact-size review;
- independent security/risk approval with a unique expiring authorization ID;
- documented externally provisioned L2 credentials with no private key present;
- empty-open-order precondition and rollback operator assignment.

Only after all gates pass may a separate task ask whether credentialed
calibration should be authorized. This review itself grants no authorization.

## Official interface basis

- https://docs.polymarket.com/api-reference/authentication
- https://docs.polymarket.com/api-reference/trade/get-user-orders
- https://docs.polymarket.com/api-reference/trade/get-trades
- https://docs.polymarket.com/market-data/websocket/user-channel
- https://docs.polymarket.com/api-reference/data/get-server-time
