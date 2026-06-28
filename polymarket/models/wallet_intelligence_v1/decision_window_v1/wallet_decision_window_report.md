# Wallet Decision Window Sprint v1

This is bounded research evidence, not a trading recommendation or investment advice.
No profitability, return, execution-quality, or fill claim is made.

## Observed Evidence

- Eligible prospective five-minute trades: 2
- Wallets represented: 1
- Minimum / median / mean / maximum window: 44.959000 / 65.032500 / 65.032500 / 85.106000 seconds
- At least 60 / 120 / 180 seconds: 50.00% / 0.00% / 0.00%

## Classification

- Sufficient decision window: 1
- Marginal decision window: 1
- Insufficient decision window: 0
- Thresholds: sufficient >= 60s; marginal >= 30s and < 60s; insufficient < 30s
- Justification: Sixty seconds is the pre-existing H3 project gate and equals twelve 5-second poll intervals. Thirty seconds is a conservative marginal boundary equal to six poll intervals; execution latency is deliberately not estimated.

## Timing Context

- Detector polling interval: 5 seconds
- Uncertainty: First-seen is response completion and therefore an upper-bound observation time quantized by the 5-second poll cadence; exact API publication time is unknown.

## Limitations

- The 5-second polling cadence makes first-seen time a bounded observation rather than exact API publication time.
- API publication time within each poll interval is unknown.
- The observation window lasted only five minutes.
- Only two eligible five-minute trades were observed, both from one wallet.
- Execution, decision, order-submission, fill, slippage, liquidity, and queue latency were not measured.
- The selected wallet cohort is retrospective and subject to selection bias.

## Conclusion

**INCONCLUSIVE**

The two observed windows are not uniformly incompatible with future automated copy-trading research, but the sample is too small and execution latency is unmeasured; compatibility remains inconclusive.

Recommended next hypothesis: H2/H3 Prospective Evidence Accumulation Sprint v1: collect a preregistered minimum of 30 target five-minute observations with the existing restart-safe observer before retesting actionable time.
