# Repricing WebSocket Architecture Recommendation v1

## Verdict

Retain polling as a comparison and recovery path, but use persistent public
CLOB and external-price WebSockets for any future latency-sensitive paper
execution architecture. The measured public event path is fast enough to make
sub-two-second ingestion and decision feasible in principle. It does not prove
sub-two-second order acknowledgement or fills.

## Recommended next boundary

Authorize a design-only authenticated execution latency measurement protocol.
That protocol must define signing, submission, acknowledgement, matching,
clock synchronization, queue position, and fail-closed handling before any
credentialed measurement is considered. This sprint does not authorize keys,
orders, or live trading.

## Required architecture

- persistent CLOB and external-price WebSockets;
- one in-memory event and decision loop;
- bounded asynchronous durability outside the decision critical path;
- source timestamp provenance plus NTP/PTP offset measurement;
- explicit stale-event, reconnect, and backlog guards;
- polling retained only for reconciliation and degraded-mode diagnostics;
- deployment near the exchange only after public-path reproducibility.

## Remaining bottlenecks

Authenticated signing, order transport, exchange acknowledgement, matching,
queue position, fill probability, host-to-exchange clock offset, and economic
performance after those delays remain unknown. These are now more important
than Python parsing, serialization, queueing, or detector computation.
