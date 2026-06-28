# Balanced Repricing Random Baseline Sprint v1

## Predefined Baseline

- Trials: 1,000
- Seed: 20260628
- Sample size per trial: 172
- Observed hours: 24.000000
- Matching: exact batch, asset, side, and 60-second expiry-bucket counts.
- Entry timing: uniform random eligible public snapshot.
- Paper rules: 180-second timeout, 0.03 target, 0.03 stop, 0.02 slippage,
  and no overlapping same-market/same-side position.

## Detector Versus Random

| Metric | Detector | Random mean | Random 95% interval | Difference |
|---|---:|---:|---:|---:|
| Win rate | 0.639535 | 0.478692 | 0.406977 to 0.546512 | +0.160843 |
| Expectancy after slippage | 0.022401 | -0.019607 | -0.029563 to -0.011226 | +0.042008 |
| Maximum drawdown | 0.875000 | 3.495447 | 2.097862 to 5.165125 | -2.620447 |
| Signals/hour | 7.166667 | 7.166667 | 7.166667 to 7.166667 | +0.000000 |

One-sided Monte Carlo exceedance probabilities:

- random expectancy at least detector: 0.000999;
- random win rate at least detector: 0.000999.

## Invalidation Search

- Selection Bias: not eliminated; detector and baseline use development sessions
- Survivorship Bias: reduced by sampling all eligible observed markets, not eliminated outside captured sessions
- Detector Bias: tested only against random timing with matched distributions
- Sampling Bias: possible from uniform snapshot weighting and serial correlation
- Market Regime: not testable with two adjacent sessions
- Small Sample Effects: material with 172 signals and two sessions

## Confidence Limitations

- Only two independent 12-hour sessions and 172 detector signals are available.
- Snapshot observations are serially correlated within five-minute markets.
- The baseline reuses the same two observed market regimes and cannot test regime persistence.
- Uniform snapshot sampling is one defensible random-timing definition, not the only possible random baseline.
- Midpoint-like public prices do not establish executable fills, queue position, depth consumption, or fees.
- Signal density is matched by design and therefore is a control variable, not an independent advantage test.
- Detector datasets were selected by frozen rules on development sessions and remain exposed to development selection bias.

## Conclusion

**SUPPORTED**

The conclusion follows the decision rule declared in
`random_baseline_summary.json`. It is development evidence only. The sealed
holdout was not inspected, frozen detector settings were unchanged, and no
production, execution, parameter-tuning, or additional-capture authorization
follows from this sprint.
