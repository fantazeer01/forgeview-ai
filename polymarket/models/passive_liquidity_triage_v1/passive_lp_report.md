# Polymarket Passive Liquidity Provision Existing-Data Feasibility Triage v1

## Decision

**B. Freeze passive liquidity provision and recommend a new direction.**

Every preregistered passive policy had negative inferred executable expectancy,
an entirely negative market-cluster confidence interval, substantial one-sided
inventory exposure and drawdown. No policy deserves prospective shadow
validation.

## Frozen Method

- Evidence: the same five complete public sessions and 6,312 wide-spread
  episodes frozen by Structural Mispricing Triage v1.
- Posted quotes: observed top-of-book YES bid and ask at the first fresh state
  of each wide-spread episode.
- Fill proxy: bid depletion when a later fresh best bid moved below the posted
  bid; ask depletion when a later best ask moved above the posted ask.
- Queue penalty: expected filled quantity is 37.5% of visible capped size,
  combining the existing severe 50% fill cap with 25% miss risk.
- Capacity: maximum 125 expected shares per side from a 250-share order cap.
- Costs: 0.005 per filled leg.
- Quote ages: no older than two seconds at placement.
- Cancellation: fills remain exposed through fixed quote life plus two-second
  cancellation latency; unmatched inventory is crossed out at the next fresh
  executable quote.
- Quote lives: fixed 2, 5, 15 and 30 seconds; 15-second BTC/ETH/SOL segments and
  a fixed near-expiry 5-second policy were also evaluated without selection.

The proxy is deliberately adverse-selection-aware. It does not prove a trade
occurred or reveal queue position. Results are feasibility estimates, not fills.

## Policy Results

| Policy | Attempts | Queue-adjusted fill probability | One-sided / triggered | Expectancy / attempt | Expectancy / filled share | P&L | Drawdown | Cluster 95% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| All assets 2s | 358 | 31.95% | 90.16% | -0.795748 | -0.049861 | -284.878 | 284.878 | [-0.999936, -0.599292] |
| All assets 5s | 352 | 34.84% | 85.63% | -0.944989 | -0.050904 | -332.636 | 332.636 | [-1.178291, -0.736462] |
| All assets 15s | 323 | 37.04% | 65.83% | -1.244880 | -0.049286 | -402.096 | 402.096 | [-1.576661, -0.933519] |
| All assets 30s | 304 | 37.38% | 56.11% | -1.507288 | -0.055591 | -458.216 | 458.216 | [-1.980584, -1.085750] |
| BTC 15s | 116 | 37.50% | 57.76% | -1.965998 | -0.052300 | -228.056 | 228.056 | [-2.723011, -1.264662] |
| ETH 15s | 50 | 37.50% | 62.00% | -1.253864 | -0.052430 | -62.693 | 64.636 | [-2.120706, -0.380665] |
| SOL 15s | 157 | 36.54% | 73.20% | -0.709218 | -0.042789 | -111.347 | 113.380 | [-0.977226, -0.452753] |
| Near-expiry 5s | 49 | 35.97% | 76.60% | -1.159151 | -0.063551 | -56.798 | 60.127 | [-1.748998, -0.587268] |

## Best Candidate

The least-negative policy was **SOL 15s**. It generated 157 eligible quote
attempts (2.6167/hour), 153 depletion triggers, 41 two-sided proxies and 112
one-sided proxies. Queue-adjusted expected capacity was 43.3709 shares/hour.
Its -0.042789 probability-point loss per expected filled share and confidence
interval wholly below zero reject advancement.

## Risks And Stability

- One-sided fills dominate every policy and turn spread into directional
  inventory at precisely the moment the quote moves adversely.
- Longer quote life increases two-sided completion but worsens absolute loss
  and drawdown; cancellation latency leaves the quote exposed during movement.
- BTC was worst at 15 seconds; SOL was least negative; no asset had positive
  aggregate expectancy.
- Near-expiry quoting was worse than the broad 5-second policy.
- The proxy cannot observe trades, queue rank, cancellations ahead, fee/rebate
  eligibility or real maker acknowledgement. Those unknowns cannot rescue a
  result whose conservative point estimate and confidence interval are negative.

## Portfolio Comparison

Wallet specialist execution, Repricing at observed delay, structural
marketable execution and passive liquidity are all negative after their
respective conservative execution assumptions. Passive LP does not dominate
the frozen alternatives and introduces inventory, queue and cancellation risk.

## Conclusion

Passive liquidity provision is permanently frozen. The current narrow research
universe has now rejected outcome prediction, Wallet Intelligence, Repricing,
structural arbitrage and passive LP. The next task should decide whether to
pivot beyond five-minute BTC/ETH/SOL markets or stop the Polymarket program,
rather than invent another variant inside an exhausted asset.

No credentials, orders, new capture, model training or holdout access occurred.
