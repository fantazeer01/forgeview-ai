# Wallet First-Seen Detection Sprint v1

This is a bounded public-data observation experiment. It is not permanent monitoring, a trading signal, or an execution system.

## Experiment

- Observation start: 2026-06-28T14:01:59.495+00:00
- Observation end: 2026-06-28T14:06:59.493+00:00
- Observed duration: 299.998 seconds
- Wallets: 4
- Poll interval: 5.0 seconds
- Requests: 240 attempted, 240 successful, 0 failed
- Endpoint: `https://data-api.polymarket.com/activity` (public GET, no authentication)

## Observations

- Baseline unique trades: 400
- Response rows observed: 24000
- Newly observed identities: 124
- New trades detected: 6
- Target five-minute trades detected: 2
- Historical page-churn identities excluded: 118
- Measurable first-seen delays: 6
- Unknown first-seen delays: 0
- Duplicate observations: 23476
- Missed observations: 440
- Reappearances after gap: 322

## Timing

- First-seen delay minimum / median / mean / maximum: 10.932 / 15.9675 / 19.749167 / 41.529
- Five-minute delay minimum / median / mean / maximum: 15.894 / 15.9675 / 15.9675 / 16.041
- Response latency minimum / median / mean / maximum ms: 149.0 / 283.0 / 322.329167 / 1031.0
- First-seen delay is a polling-quantized upper bound, not exact server publication latency.

## API Limits

- Official Data API general limit: 1000 requests per 10 seconds
- Configured rate: 8.0 requests per 10 seconds
- Limit utilization: 0.80%
- Documentation: https://docs.polymarket.com/api-reference/rate-limits

## Can H2 Now Be Tested?

YES

The bounded observer produced measurable trade-to-first-seen upper bounds. A larger preregistered prospective sample is still required before H2 can be supported or rejected.

## Research Conclusion

H2_MEASURABLE_PROSPECTIVELY

## Recommended Next Hypothesis

H3: Wallet Detection-To-Expiry Feasibility Sprint v1 after a preregistered H2 first-seen sample is large enough.
