# Polymarket Executable Structural Mispricing Triage v1

## Decision

**B. Freeze structural mispricing and recommend a new direction.**

No directly executable structural opportunity exists in the current public
asset. Across 60 scheduled hours, five complete and continuous sessions,
320,736 raw snapshots and 280,284 valid fresh deduplicated quote states, there
were zero crossed books, zero locked books and zero positive near-expiry
structural states.

## Frozen Evidence And Costs

- Sessions: Microstructure Batches 001-002, Balanced Repricing Batches 001-002,
  and the valid fourth 24-hour paper soak.
- Exclusions: interrupted/failed sessions, duplicate `latest` files, stale
  quotes over five seconds, nonpositive size and invalid prices.
- Execution: actual YES bid/ask and visible top-level size, 250-share order cap,
  50% fill cap and 0.01 total cost from the existing severe stress protocol.
- Latency: episodes are reported at immediate, two-second and five-second
  persistence; serially repeated identical quote states are deduplicated.
- Holdout: sealed and not inspected.

## Dataset

| Metric | Result |
|---|---:|
| Scheduled public hours | 60.0 |
| Completed continuous sessions | 5 |
| Markets | 2,175 |
| Raw snapshots | 320,736 |
| Deduplicated quote states | 280,804 |
| Valid fresh states | 280,284 |
| Stale states | 520 |
| Invalid states | 0 |
| BTC / ETH / SOL states | 94,329 / 92,766 / 93,709 |
| Median spread | 0.010000 |
| p95 spread | 0.020000 |
| Minimum / maximum spread | 0.001000 / 0.880000 |

## Candidate Ranking

1. **Crossed or inverted YES book:** directly testable, zero qualifying states,
   zero capacity and zero 2s/5s episodes.
2. **Complete-set acquisition:** not independently testable because NO bid/ask
   and depth were not captured. Algebraic complement gives a best theoretical
   margin of -0.011000 and mean -0.021816 after cost.
3. **Complete-set liquidation:** same missing independent NO book and same
   strictly negative theoretical margins.
4. **Locked book:** zero states; even a lock would be -0.010000 after cost.
5. **Stale bid/ask inconsistency:** 520 stale states existed, but none was
   crossed; all fail the quote-age gate regardless.
6. **Temporary wide-spread capture:** 7,534 states in 6,312 episodes across
   1,799 markets. Frequency was 125.5667 states/hour and 105.2 episodes/hour.
   Only 533 episodes persisted two seconds and 102 persisted five seconds.
   Best marketable margin was -0.040000 and mean -0.066406. Passive capture
   requires two unobserved queue fills and is not directly executable evidence.
7. **Near-expiry distortion:** 15,573 fresh states within 30 seconds of expiry,
   zero crossed states; best theoretical margin -0.011000.
8. **Multi-outcome inconsistency:** not applicable. Captured markets are binary
   and contain no independently synchronized multi-outcome books.
9. **Executable bid/ask anomaly:** zero fresh crossed states.
10. **Liquidity-aware arbitrage-like setup:** zero positive states and zero
    profitable conservative capacity.

## Book-Semantics Limitation

The historical schema stores an independent YES order book only. `NO ask = 1 -
YES bid` and `NO bid = 1 - YES ask` are algebraic values, not independently
captured NO-token quotes and depths. Consequently, a complete-set margin from
this schema is exactly `-YES spread` before cost. It cannot establish
simultaneous two-token execution or multi-outcome arbitrage.

## Conclusion

Structural mispricing is frozen for the current asset. There is no positive
marketable expectancy, no profitable visible capacity and no latency-persistent
crossed condition. Wide spreads are observable but are compensation offered to
passive liquidity providers, not arbitrage available to a marketable order.

The fastest evidence-based successor is a separate passive-liquidity feasibility
triage: test whether hypothetical maker fills in the existing wide-spread states
survive adverse selection, inventory exposure, queue uncertainty and costs.
This does not reopen structural arbitrage and does not authorize orders.
