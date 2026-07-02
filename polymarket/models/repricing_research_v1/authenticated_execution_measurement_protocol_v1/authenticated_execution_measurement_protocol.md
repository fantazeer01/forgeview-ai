# Authenticated Execution Measurement Protocol v1

## Purpose and boundary

This protocol measures the complete Repricing execution path without changing
the frozen detector or evidence gates. This document is a design artifact. It
does not authorize credentials, private keys, wallets, orders, or capital.

The economic reference points are frozen: immediate executable replay was
+0.035944 expectancy, modeled one-second delay was +0.022508, and actual
two-second replay plus 0.005 cost was -0.009810. Two seconds is therefore a
failure boundary, not an engineering target.

## Measurement phases

### Phase 0: deterministic no-secret dry run

Use recorded public events, a deterministic signer stub, a local HTTP sink,
and fixture user-channel messages. Validate event IDs, clocks, timestamps,
state transitions, retries, timeouts, redaction, hashes, and replay. No network
request may reach an authenticated endpoint.

### Phase 1: public transport calibration

Maintain warm public CLOB and external-price WebSockets. Measure local event
receipt through decision, public REST round trips, DNS/TLS warm-up, connection
reuse, clock offset, jitter, reconnects, and durable logging. No credentials or
orders are permitted.

### Phase 2: separately authorized credentialed no-order calibration

Only after explicit risk and security approval, use isolated test credentials
to measure L2 header generation, authenticated user-WebSocket subscription,
heartbeat acknowledgement, and read-only order/trade queries. Do not create or
cancel orders. Secrets remain in an external secret provider and never enter
logs, fixtures, command lines, source, or Git.

### Phase 3: separately authorized minimum-risk order-path measurement

This phase is not authorized by this sprint. If later approved under the
project risk policy, use precommitted markets, minimum permitted size, hard
daily/order limits, a kill switch, heartbeat cancellation, and an independent
operator. Measure a small fixed matrix of marketable FAK/FOK and passive
post-only orders. Do not tune from results.

## Canonical event contract

Every envelope is append-only and contains:

- `protocol_version`, `run_id`, `event_id`, `correlation_id`;
- `order_intent_id`, redacted `order_id_hash`, redacted `trade_id_hash`;
- `market_id`, `asset_id`, asset, side, order type, price and size;
- `event_name`, monotonic nanoseconds, UTC nanoseconds, clock-offset estimate;
- source timestamp and normalized UTC nanoseconds where available;
- predecessor event ID and payload SHA-256;
- transport attempt, timeout class, retry reason and terminal status;
- process, host and build identity without secrets.

Event IDs are SHA-256 hashes of protocol version, run ID, correlation ID,
event name, attempt number and canonical payload hash. JSON uses UTF-8, sorted
keys, compact separators, decimal strings for prices/sizes, and UTC nanoseconds.
Replay rejects duplicate IDs, missing predecessors, backward monotonic time,
unknown states, unredacted secret fields, and terminal-state disagreement.

## Timestamp points

1. `source_event_published`: exchange/source time when supplied.
2. `source_event_received`: first local byte/message completion.
3. `signal_generated`: frozen detector emits the signal.
4. `decision_completed`: immutable order intent is produced.
5. `sign_start` and `sign_complete`: EIP-712 order signing boundary.
6. `serialize_start` and `serialize_complete`: final wire body boundary.
7. `request_queued` and `request_sent`: transport queue and last-byte sent.
8. `response_first_byte` and `response_complete`: REST acknowledgement.
9. `order_accepted`: response reports `live`, `matched`, or `delayed`.
10. `book_appearance`: correlated public book event first shows the order,
    where uniquely observable; otherwise record `NOT_IDENTIFIABLE`.
11. `user_order_event`: authenticated placement/update/cancellation received.
12. `trade_matched`, `trade_mined`, `trade_confirmed`, `trade_failed`.
13. `partial_fill` and `complete_fill`: cumulative matched size transitions.
14. `cancel_intent`, `cancel_sent`, `cancel_ack`, `cancel_observed`.
15. `timeout`, `retry_scheduled`, `reconciled`, `terminal`.

Local durations use one monotonic clock. Cross-host/source attribution uses UTC
only after offset correction. Never subtract unrelated unsynchronized clocks.

## Correlation and lifecycle rules

- One immutable `correlation_id` spans signal, order intent, request, REST
  response, user-channel order events, trades, cancellation and reconciliation.
- Correlate REST `orderID`, user-channel order `id`, trade `taker_order_id` and
  maker-order `order_id`; store only hashes in Git-safe summaries.
- A REST success is acknowledgement, not fill proof.
- `matched` is the execution event for latency economics; `MINED` and
  `CONFIRMED` measure settlement, not decision-to-fill latency.
- Partial fills are cumulative increases in `size_matched`; complete fill is
  cumulative matched size equal to original size.
- First public book appearance is measurable only for an identifiable passive
  price/size/order transition. Ambiguous attribution must remain unknown.
- Queue position is never inferred as exact. Record ahead-size bounds at
  acceptance, subsequent depth/trade changes, and an uncertainty interval.

## Timeouts and retries

- No automatic retry of an order POST after an ambiguous timeout. Reconcile by
  deterministic order hash and authenticated order query first.
- Retry only transport failures proven to occur before any bytes were sent, or
  explicit exchange responses declared retryable by the frozen protocol.
- Use bounded exponential backoff with jitter recorded from a precommitted seed.
- `401`, malformed signatures, stale clocks, invariant failures and unknown
  acknowledgements fail closed.
- `425`, `429`, `500` and `503` are recorded separately; no retry may cross the
  signal timeout or create a second order intent.
- Cancellation timeout triggers query and user-channel reconciliation, never a
  blind replacement order.

## Clock requirements

- NTP discipline is mandatory; measure offset and uncertainty before, during
  and after every run using CLOB `/time` plus at least two independent NTP
  sources.
- Clock offset uncertainty must be <=5 ms median and <=20 ms p95. A sample
  outside 50 ms pauses measurement and marks cross-clock latency ineligible.
- Record UTC and monotonic timestamps together at every local boundary.
- Normalize documented second timestamps without inventing sub-second
  precision; preserve the original value and unit.
- Server timestamps measure publication/state time only where semantics are
  documented. REST RTT and local stage durations remain valid without one-way
  attribution.

## Scientific acceptance gates

At least 100 fixed-protocol attempts across three independent sessions are
required for a latency feasibility conclusion, with at least 20 per asset and
20 per side where the authorized matrix supports them. Report best, median,
p90, p95, p99 and maximum for every stage, plus timeout, retry, rejection,
partial-fill, full-fill and cancellation rates.

The architecture passes the latency feasibility gate only when:

- signal-to-order-ack p95 <=750 ms;
- signal-to-first-match p95 <=1,000 ms for marketable attempts;
- signal-to-terminal-fill-or-cancel p95 <=1,500 ms;
- zero duplicate orders and zero unreconciled ambiguous submissions;
- clock, correlation, replay and redaction gates all pass;
- expectancy replay using the measured latency distribution remains positive
  after frozen spread, slippage and cost assumptions in every admitted session.

Any signal-to-first-match observation >=2,000 ms fails the relevant attempt.
The whole result is inconclusive, not passed, when fills are too sparse or
queue attribution is unresolved.

## Official interface basis

The design follows the current official CLOB contract: L1 EIP-712 order
signing plus L2 HMAC request authentication, `POST /order`, authenticated user
WebSocket order/trade updates, trade states `MATCHED`, `MINED`, `CONFIRMED`,
`RETRYING`, and `FAILED`, and the public `/time` endpoint. Sources:

- https://docs.polymarket.com/api-reference/authentication
- https://docs.polymarket.com/api-reference/trade/post-a-new-order
- https://docs.polymarket.com/market-data/websocket/user-channel
- https://docs.polymarket.com/trading/orders/overview
- https://docs.polymarket.com/api-reference/data/get-server-time
- https://docs.polymarket.com/api-reference/trade/send-heartbeat
