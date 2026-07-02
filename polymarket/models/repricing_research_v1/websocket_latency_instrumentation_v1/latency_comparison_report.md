# Repricing Public WebSocket Latency Instrumentation v1

## Executive conclusion

A 180-second simultaneous public benchmark observed 137,107 CLOB WebSocket
messages, 179 CLOB REST polling observations, and 974 Binance WebSocket trades.
No authentication or orders were used. Public WebSockets remove the polling
cadence bottleneck: CLOB inter-message gap p95 fell from 5,150.8863 ms to
6.7460 ms, a 5,144.1403 ms reduction.

The local WebSocket path is not the limiting component. Its p95 queue, parse,
decision, serialization, and journal times were 0.0003, 0.0298, 0.0016,
0.0207, and 0.2632 ms. Sub-two-second public ingestion and decision is
therefore feasible in principle. End-to-end execution remains unproven because
authenticated submission, acknowledgement, matching, queue position, and
fills were outside this sprint.

## Polling versus WebSocket

| Metric | Polling | WebSocket | Difference |
|---|---:|---:|---:|
| Mean inter-message gap | 1,025.7355 ms | 1.2867 ms | -1,024.4488 ms |
| Median inter-message gap | 180.7862 ms | 0.5095 ms | -180.2767 ms |
| p95 inter-message gap | 5,150.8863 ms | 6.7460 ms | -5,144.1403 ms |
| Mean queue latency | 1.1073 ms | 0.0002 ms | -1.1071 ms |
| p95 decision latency | 0.0022 ms | 0.0016 ms | -0.0006 ms |
| Mean reported quote age | 1,008.0786 ms | 996.2131 ms | -11.8656 ms |

Absolute quote age and one-way network latency are clock contaminated. Both
simultaneous CLOB paths showed an approximately one-second local-versus-server
offset, and no NTP offset correction was available. The same-host relative
mean quote-age improvement is 11.8656 ms. Against the prior admitted-signal
polling mean of 3,473.7308 ms, the observed WebSocket value is 2,477.5178 ms
lower, but that cross-run comparison is descriptive rather than causal.

## Reconnect, loss, and stale handling

The bounded run recorded one CLOB and two Binance reconnect-cycle exits; these
include normal deadline timeout accounting. There were 16 REST poll errors.
CLOB public messages expose no usable sequence number, so packet loss cannot
be proven from this feed. Binance aggregate-trade ID gaps totaled 174, but
aggregate IDs may advance for events not delivered by the selected combined
stream and are diagnostic only. No quote exceeded the two-second stale guard.

## Economic interpretation

The prior executable replay was +0.035944 at immediate entry, +0.022508 under
modeled one-second delay, and -0.009810 at two seconds plus 0.005 cost. The
WebSocket benchmark demonstrates that public event receipt and local decision
need not consume that two-second window. It does not measure the remaining
order path, so expected executable expectancy cannot be recomputed as observed
evidence. A positive result is plausible below one second, but remains an
inference and not a production-edge claim.

## Feasibility

- Sub-two-second public event-to-decision: supported by measurement.
- Sub-two-second end-to-end execution: plausible, not validated.
- Sub-one-second public event-to-decision: supported apart from clock-offset
  uncertainty in one-way event age.
- Sub-one-second end-to-end execution: unproven.
- Weak Evidence executable in principle: conditionally yes; execution proof
  requires a separately authorized order-path measurement protocol.

Frozen strategy, evidence gates, sealed holdout, production model, wallet
research, and execution logic were unchanged.
