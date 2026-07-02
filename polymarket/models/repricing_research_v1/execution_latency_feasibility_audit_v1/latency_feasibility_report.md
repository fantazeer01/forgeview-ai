# Repricing Execution Latency Feasibility Audit v1

Conclusion: `INSUFFICIENT_MEASUREMENT`

## Executive Finding

The current REST-polling architecture cannot reliably execute within two
seconds and cannot execute within one second. On 338 admitted signals, the
quote was already 1.771s old in the best case, 2.653s at median, 7.137s at p95,
and 49.065s at maximum before the one-second paper-runtime poll or any order
submission.

The current end-to-end lower bound is approximately 1.914s best case, 3.333s
median, 8.435s p95, and 56.925s at the observed worst tail. These are lower
bounds because authenticated signing, POST `/order`, exchange acknowledgement,
matching, and queue delay were not measured and remain forbidden without an
authorized execution phase.

## Measured Components

- Canonical source checkpoint cadence: 1.998s median, 2.009s p95.
- CLOB cold HTTPS read: 178ms median, 346ms p95, 6.857s maximum outlier.
- Binance REST ticker: 1.169s median, 1.217s p95 from this Home PC.
- Frozen detector decision: 0.0043ms median.
- JSON encode plus decode: about 0.0054ms median.
- Restart-safe SQLite commit: 0.859ms median, 1.147ms p95.
- Runtime stream poll: configured 0-1s phase delay, approximately 0.5s median.

Python computation and serialization are negligible. Polling cadence,
asynchronous next-cycle feed consumption, stale public quotes, network jitter,
and unmeasured order/match processing dominate.

## Feasibility

Sub-two-second execution is not reliable in the current architecture; even the
observed minimum quote age consumes nearly the entire budget. Sub-one-second
execution is impossible because the minimum admitted quote age alone exceeds
one second.

Polymarket officially exposes public real-time market WebSockets and recommends
WebSockets instead of polling for live order books. Its matching engine is in
`eu-west-2`, with an `eu-west-1` non-georestricted region and optional direct
co-location. These facts make a redesigned event-driven path technically
capable of lower latency, but they do not prove authenticated execution speed.

## Architecture Options

1. Faster REST polling in one process could reduce median latency to roughly
   0.8-1.5s, but HTTP jitter makes p95 sub-two-second performance doubtful.
2. Persistent external and CLOB WebSockets, one event loop, in-memory detector,
   asynchronous durability, and persistent order transport could plausibly
   reach 0.3-0.8s median from a stable host, with estimated p95 1.0-2.5s.
3. Event-driven deployment near `eu-west-2` could plausibly reach 0.1-0.35s
   median and 0.3-1.0s p95, but requires separately authorized authenticated
   measurement and still cannot guarantee queue fills.
4. Less latency-sensitive strategies with a 5-30s survival horizon avoid making
   infrastructure speed the central source of edge.

## Recommendation

Engineering improvements alone may make sub-two-second transport plausible,
but cannot make this strategy production-ready on current evidence. The edge
is negative at two-second executable replay, and order/match latency remains
unknown. Run one bounded public WebSocket instrumentation sprint with no
orders; continue this branch only if measured event-to-decision p95 leaves a
credible order/match budget. In parallel, prioritize less latency-sensitive
research.

Official references: [WebSocket overview](https://docs.polymarket.com/market-data/websocket/overview),
[market channel](https://docs.polymarket.com/market-data/websocket/market-channel),
[trading architecture](https://docs.polymarket.com/trading/overview),
[orderbook guidance](https://docs.polymarket.com/trading/orderbook), and
[rate limits](https://docs.polymarket.com/api-reference/rate-limits).

Validation: 62 Repricing tests and 208 full repository tests pass. No order,
credential, wallet, holdout, model training, or evidence run was used.
