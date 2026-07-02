# Authenticated Execution Latency Dry-Run Benchmark v1

## Verdict

`LOCAL_HARNESS_PASS_AUTHENTICATED_EXCHANGE_NOT_MEASURED`

The harness completed 120 deterministic loopback attempts: 60 fixture fills
and 60 fixture cancellations. It replayed 1,680 lifecycle events across 120
correlations with no duplicate, predecessor, sequence, clock, redaction, or
terminal-state failure. A second independent run produced the identical
identity hash `91f195181252da87d05d6c18a620a0e38e975e546cef93ac74a12d40f5392633`.
The deterministic summary hash was
`4fe716799ef877c0e8d8601652a521b70eb4aac7874ef9dd58fbd2b276473097`.

No credential, wallet, private key, authenticated Polymarket endpoint, or real
order was used. Fixture order size was zero and network access was restricted
to `127.0.0.1`. “Signing”, “authentication”, exchange acknowledgement, user
updates, fills and cancellations are interface simulations, not exchange
measurements.

## Measured local benchmark

| Stage | Best | Median | p90 | p95 | p99 | Worst |
|---|---:|---:|---:|---:|---:|---:|
| Decision | 0.0011 ms | 0.0019 ms | 0.0024 ms | 0.0026 ms | 0.0037 ms | 0.0041 ms |
| Fixture signing | 0.1731 ms | 0.2077 ms | 0.2898 ms | 0.3091 ms | 0.3553 ms | 0.3725 ms |
| Serialization/auth stub | 0.0151 ms | 0.0173 ms | 0.0225 ms | 0.0255 ms | 0.0312 ms | 0.0443 ms |
| Local transport queue | 0.6610 ms | 0.8012 ms | 0.9867 ms | 1.0215 ms | 1.2601 ms | 1.5448 ms |
| Local sink acknowledgement | 0.1968 ms | 13.2218 ms | 13.7506 ms | 13.8470 ms | 14.0538 ms | 14.2600 ms |
| Signal to acknowledgement | 2.4588 ms | 16.2298 ms | 16.6753 ms | 16.8979 ms | 17.1493 ms | 17.2604 ms |
| Signal to first fixture transition | 14.5879 ms | 30.3126 ms | 31.0202 ms | 31.1120 ms | 31.1940 ms | 31.2168 ms |
| Signal to terminal | 31.1793 ms | 46.7695 ms | 47.5606 ms | 47.7829 ms | 47.9294 ms | 48.0068 ms |
| Fixture cancellation | 0.9244 ms | 16.6066 ms | 16.8045 ms | 16.8511 ms | 17.0661 ms | 17.2193 ms |

Windows timer granularity and fixture sleeps dominate acknowledgement and
lifecycle timing. The actual client computation is sub-millisecond at p95
apart from the loopback transport queue at 1.0215 ms.

## Modeled-budget comparison

The prior 490 ms p95 signal-to-ack and 800 ms p95 signal-to-first-match models
are neither confirmed nor rejected. This dry run validates local instrumentation
and state safety only. It cannot measure internet transmission, authenticated
CLOB processing, user-channel publication, matching, queue position or fills.

## Scientific conclusion

The local harness passes all three numerical gates, but those gate results are
engineering validation only and are ineligible as authenticated execution
admission evidence. Weak Evidence remains conditionally plausible, not proven
executable. Production readiness remains blocked on separately authorized
credentialed no-order calibration and eventual risk-approved order-path data.
