# Public-Stream Repricing Latency Dry Run v1

## Verdict

`PUBLIC_TO_LOCAL_PATH_MEASURED_AUTHENTICATED_EXCHANGE_NOT_MEASURED`

A bounded 90-second public CLOB run completed 60 correlated loopback dry-run
lifecycles: BTC 21, ETH 20 and SOL 19. The observer received 38,194 recognized
public events. It used no credentials and submitted no orders. Network access
was limited to the public CLOB WebSocket and `127.0.0.1` local sink.

The probe is an engineering timing trigger created from a sampled public event;
it is not an accepted frozen-strategy trade signal and is not evidence input.
The frozen strategy and evidence gates were unchanged.

## Latency distribution

| Metric | Best | Median | p90 | p95 | p99 | Worst |
|---|---:|---:|---:|---:|---:|---:|
| Public receipt to probe signal | 0.5801 ms | 0.8061 ms | 1.1550 ms | 2.2538 ms | 3.2713 ms | 4.1457 ms |
| Signal to local acknowledgement | 2.7719 ms | 5.0465 ms | 8.3437 ms | 9.8616 ms | 12.0794 ms | 12.6788 ms |
| Signal to next public event | 1.5844 ms | 7.3760 ms | 24.4904 ms | 36.4036 ms | 88.6001 ms | 108.4537 ms |
| Signal to fixture terminal | 3.7893 ms | 9.0107 ms | 13.9155 ms | 15.4593 ms | 20.1223 ms | 23.9113 ms |
| Reported public event age | 999.8984 ms | 1,004.3525 ms | 1,025.7676 ms | 1,065.0174 ms | 1,116.5126 ms | 1,118.0171 ms |

Absolute event age is clock contaminated by the same approximately one-second
server/local offset found in the earlier WebSocket benchmark. It is not a
one-way network measurement.

## Reliability

There were zero reconnects, zero stale events, zero queue/backpressure drops,
and all 60 correlations observed a subsequent public event. The public event
gap distribution across 38,191 gaps was 0.9327 ms median, 29.6157 ms p95,
91.5315 ms p99 and 264.8276 ms maximum. The adapter suppressed 303 duplicate
event identities.

Replay validated 900 structured lifecycle events across all 60 terminal
correlations. Raw event journals were excluded from Git; compact summary and
correlation exports are retained.

## Interpretation

Public event receipt, local correlation, fixture signing, loopback submission
and state observation fit easily inside the engineering gates. This confirms
that the public-to-local path does not consume the two-second economic budget.
It does not measure authenticated submission, exchange acceptance, matching,
queue position, fills or cancellation. Authenticated admission remains
`NOT_EVALUATED` and Weak Evidence remains conditionally executable only.
