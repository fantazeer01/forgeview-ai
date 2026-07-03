# Repricing Slower-Horizon Derivative Validation v1

## Verdict

**NO-GO: freeze Repricing permanently.**

No preregistered continuation or mean-reversion derivative passed every gate.
Continuation point estimates were positive at 30, 60, 120 and 180 seconds,
but every market-clustered confidence interval included zero and every result
failed concentration or matched-random requirements. Mean reversion was
negative at every horizon and in every session.

## Frozen Method

- Inputs: the same 338 valid anchors from Balanced Batches 001-002 and the
  fourth canonical paper soak.
- Horizons: 30, 60, 120 and 180 seconds.
- Directions: detector-side continuation and exact opposite-side mean
  reversion.
- Entry: first executable ask at or after signal plus two seconds.
- Exit: first executable bid at or after signal plus the fixed horizon.
- Cost: actual ask-to-bid spread plus the existing 0.005 transaction-cost
  stress; snapshots more than five seconds late are excluded.
- Expiry: any signal whose fixed horizon exceeds entry time-to-expiry is
  excluded; no position is valued after expiry.
- Confidence: deterministic market-cluster bootstrap, eight-way Bonferroni
  intervals, Holm-adjusted matched-random-timing tests.
- No horizon, side, asset, session, threshold or cost was optimized after
  results.

## Results

| Horizon | Direction | N | Win rate | Expectancy | P&L | Drawdown | Cluster 95% CI | Holm random p |
|---:|---|---:|---:|---:|---:|---:|---|---:|
| 30s | continuation | 336 | 52.38% | +0.019601 | +6.586 | 2.790 | [-0.006194, +0.044912] | 0.015984 |
| 30s | mean reversion | 336 | 34.23% | -0.056146 | -18.865 | 19.505 | [-0.082361, -0.030745] | 1.000000 |
| 60s | continuation | 334 | 53.29% | +0.035171 | +11.747 | 3.085 | [-0.004706, +0.075111] | 0.034965 |
| 60s | mean reversion | 334 | 37.13% | -0.071653 | -23.932 | 25.259 | [-0.111290, -0.031846] | 1.000000 |
| 120s | continuation | 269 | 56.51% | +0.038394 | +10.328 | 3.922 | [-0.026077, +0.101316] | 0.983017 |
| 120s | mean reversion | 269 | 40.89% | -0.076056 | -20.459 | 23.339 | [-0.139628, -0.009691] | 1.000000 |
| 180s | continuation | 198 | 56.06% | +0.028768 | +5.696 | 3.200 | [-0.042475, +0.099614] | 1.000000 |
| 180s | mean reversion | 198 | 41.41% | -0.066227 | -13.113 | 15.375 | [-0.136561, +0.005020] | 0.983017 |

## Stability

All continuation horizons were positive in each of the three sessions, but
cross-asset stability failed. SOL expectancy was -0.001243 at 30 seconds,
+0.001906 at 60 seconds, -0.003333 at 120 seconds and -0.049676 at 180
seconds. BTC supplied 93.44% of 30-second positive P&L. The largest-session
shares were 55.50%, 51.25%, 43.43% and 68.64%, all above the 40% gate.

The 30-second and 60-second detector anchors beat matched random timing, but
their cluster and multiplicity-adjusted intervals include zero and their P&L
is concentrated. At 120 and 180 seconds, matched random timing was as good as
or better than detector timing. Thus increasing the horizon reduces the
specific information attributable to the frozen detector rather than proving
a slower executable edge.

## Scientific Conclusion

The observed continuation point estimates have analytical value but cannot be
advanced under the preregistered binary rule. The result is compatible with a
short-lived market drift plus broad market-time effects, not a robust,
executable derivative of the frozen detector. Repricing is permanently frozen;
its artifacts remain preserved as research history and negative controls.

The sealed holdout was not inspected or evaluated. No data was collected, no
strategy parameter changed, and no production model or execution capability
was introduced.
