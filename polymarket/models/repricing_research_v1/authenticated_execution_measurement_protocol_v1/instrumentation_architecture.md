# Instrumentation Architecture

## Components

1. **Public event observer**: existing CLOB and external WebSockets, unchanged.
2. **Frozen decision observer**: emits immutable signal and decision timestamps.
3. **Execution probe interface**: accepts an immutable order intent; dry-run
   implementations only until a later authorization.
4. **Signer boundary**: opaque `sign(intent) -> signed_payload` interface. The
   measurement layer sees duration and payload hash, never secret material.
5. **Warm asynchronous transport**: persistent HTTP/TLS connection, bounded
   one-attempt queue, explicit first-byte/last-byte timestamps.
6. **Authenticated user observer**: future isolated adapter for order and trade
   lifecycle events; credentials injected by an external provider.
7. **Public book observer**: records possible first appearance and depth change.
8. **Reconciler**: joins REST response, user events, order query and trades by
   deterministic hashes; ambiguous states fail closed.
9. **Append-only journal**: asynchronous durability after critical timestamps,
   hash chained and replay validated.
10. **Summary exporter**: emits only aggregate, redacted, Git-safe artifacts.

## Security boundary

The measurement package depends on a signer and credential-provider interface,
not their implementation. Production source must never contain seed phrases,
private keys, API secrets, passphrases, raw authorization headers, signed order
bodies, or wallet addresses in Git-safe output. Redaction occurs before the
journal boundary and is covered by tests.

## Latency attribution

- receive to decision: local monotonic measurement;
- signing: `sign_complete - sign_start`;
- serialization: `serialize_complete - serialize_start`;
- local queue: `request_sent - request_queued`, split from socket wait;
- network/server acknowledgement: REST first-byte and complete RTT; one-way
  split remains unknown without server processing timestamps;
- acceptance: response completion to user-channel placement event;
- first match: signal generation to documented `matchtime`, clock-corrected,
  and independently to local user-event receipt;
- settlement: `MINED`/`CONFIRMED`, reported separately from fill economics;
- cancellation: cancel intent through REST acknowledgement and observed
  cancellation; both are required.

## Connection policy

Warm the public WebSockets, authenticated user WebSocket, DNS, TLS and HTTP
pool before an eligible attempt. Record cold-start separately. Keep transport
and signing asynchronous, but preserve one deterministic order per signal.
Bound every queue; queue overflow rejects the signal before signing.

## Failure policy

Unknown order state, clock drift, stale public data, user-channel disconnect,
journal failure, duplicate correlation ID, transport backlog or reconciliation
disagreement disables new attempts and starts bounded reconciliation. Heartbeat
loss must cancel open orders under the official exchange mechanism.
