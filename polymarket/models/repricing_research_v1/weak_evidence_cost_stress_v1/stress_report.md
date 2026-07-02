# Repricing Weak-Evidence Stability And Executable-Cost Stress Sprint v1

Conclusion: `WEAKENED`

## Scope

The sprint used only the 338 signals from Balanced Batches 001-002 and the
admitted clean fourth soak. Entry spread and visible side size were recovered
as-of from each immutable source session with 100% coverage. No detector,
threshold, evidence gate, holdout, model, or wallet logic changed.

## Stability

Recorded conservative results remain positive in all three sessions, all
assets, and both sides: +0.032405 expectancy, +10.9530 P&L, and 0.8750 max
drawdown. However, 64.82% of P&L comes from the fourth-soak session and 46.37%
from SOL, both above the project's 40% concentration target. Only three
independent sessions are available.

## Cost Stress

One-factor stress shows:

- half-spread: +0.023673 expectancy;
- additional 0.005 transaction cost: +0.027405;
- deterministic 10% missed fills plus visible-size/75% fill cap: +0.006651;
- modeled 0.5-second delay: +0.028061;
- modeled 1-second delay: +0.022508;
- modeled 2-second delay: +0.007211, but only 2/3 sessions positive;
- quote-age penalty alone: +0.001565, below the frozen +0.005 weak floor;
- combined moderate execution: -0.015614, -5.2777 P&L, 5.2777 drawdown,
  with all sessions, assets, and sides negative.

Severe and extreme combined stress remain negative at -0.022041 and -0.034664
expectancy.

## Actual Quote Replay

Actual as-of bid/ask replay is the stronger result:

- immediate executable quote: +0.035944 expectancy, +12.1490 P&L, all three
  sessions positive;
- 2-second entry plus 0.005 cost: -0.009810 expectancy, -3.3157 P&L,
  3.9548 drawdown, all sessions negative, nominal 95% interval
  [-0.018432, -0.001188];
- 5-second/100-share visible-size replay: -0.001156 expectancy;
- 5-second/250-share replay: -0.001396 expectancy.

At two seconds, BTC remains slightly positive (+0.003171) while ETH and SOL
are negative; both YES and NO are negative. High external-move signals remain
slightly positive but contain only 12 observations. No segment supports a
production claim.

## Assessment

Weak Evidence does not remain stable under executable-cost stress. Spread,
small transaction charges, and fill impairment are survivable in isolation.
Latency and stale-quote exposure are the dominant break. The public 2-second
snapshot cadence cannot establish sub-second queue position, fill probability,
market impact, or exact fee treatment, so the result weakens rather than fully
rejects the repricing hypothesis.

The strategy does not advance to production-candidate status. The next
scientific question is whether an executable end-to-end latency budget below
the observed break point is feasible and measurable without changing the
detector.

Validation: deterministic repeat hashes match; 62 Repricing tests and 208 full
repository tests pass. The sealed holdout was not inspected.
