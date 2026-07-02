# Implementation Roadmap

## Stage 1: no-secret deterministic harness

Implement event schema validation, canonical hashing, signer and transport
interfaces, fixture user-channel events, local HTTP sink, replay, redaction,
clock monitor, timeout/retry state machine, and failure injection. No external
authenticated calls. Exit gate: deterministic replay and zero secret-bearing
fields.

## Stage 2: public dry run

Connect the harness to existing public WebSockets and a local execution sink.
Measure warm-up, event correlation, queue bounds, clock discipline and summary
exports under live public load. Exit gate: p95 local critical path below 10 ms,
no duplicates, no unresolved state, and full reconnect recovery.

## Stage 3: security and risk review

Review secret-provider interface, process isolation, redaction, network allow
list, exposure limits, heartbeat cancellation, kill switch, audit retention,
geographic eligibility and incident procedure. This review can reject or defer
credentialed work.

## Stage 4: separately authorized authenticated no-order calibration

Measure user-channel subscription, heartbeat, L2 HMAC, and read-only endpoints
with isolated credentials. Exit gate: clock and correlation integrity plus no
order-capable method reachable from the calibration command.

## Stage 5: separately authorized minimum-risk measurement

Only under Capital Stage and Trading License approval, execute the precommitted
small fixed matrix. Collect at least 100 attempts over three sessions. Replay
measured latency distributions through frozen evidence without tuning.

## Estimated effort

- Stage 1: 2-3 engineering days.
- Stage 2: 1-2 engineering days plus bounded observation.
- Stage 3: 1-2 review days.
- Stage 4: 1 engineering day after authorization and credential provisioning.
- Stage 5: 3 sessions plus analysis; duration depends on eligible signals.

No stage automatically authorizes the next.
