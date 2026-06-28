# Wallet H2/H3 Decision Framework v1

## Purpose

This framework prevents indefinite evidence collection. It decides whether
Wallet Intelligence should continue bounded research, graduate to the next
engineering question, or freeze the copy-trading branch. It does not change
H2, H3, Wallet Score, polling, or the observer.

## Primary Measures

- **H2 success:** an eligible BTC/ETH/SOL five-minute wallet trade is first
  observed no more than 30 seconds after its public trade timestamp.
- **H3 success:** an eligible trade has at least 60 seconds remaining from
  first observation to Gamma-verified market expiry.
- First observation is response completion from the frozen 5-second polling
  system. It is a conservative, polling-quantized observation time, not an
  exact API publication timestamp.

## Minimum Evidence Gate

No `SUPPORTED` or `REJECTED` conclusion is permitted until all requirements
pass:

| Requirement | Minimum |
|---|---:|
| Eligible prospective five-minute trades | 100 |
| Distinct frozen H1 wallets represented | 3 |
| Eligible trades per represented wallet | 10 |
| Largest wallet share | no more than 60% |
| Independent bounded observation sessions | 10 |
| Distinct UTC dates | 5 |
| Assets represented | 2 |
| Eligible trades per represented asset | 20 |
| Trade and first-seen timestamp completeness | at least 95% |
| Gamma expiry join completeness | at least 95% |
| Stable identity uniqueness | 100% |
| Successful public request rate | at least 95% |

The 100-trade floor limits the worst-case normal-approximation margin for a
proportion to about 9.8 percentage points at 95% confidence. Diversity gates
prevent a single wallet, asset, session, or date from deciding the result.

## Confidence Rule

Primary proportions use two-sided 95% Wilson score intervals. Point estimates
alone never support or reject a hypothesis. H2 and H3 are evaluated
separately; graduation requires both to be supported.

## Quantitative Outcomes

### H2

- `SUPPORTED`: minimum evidence passes, at least 80% of eligible trades are
  observed within 30 seconds, and the 95% Wilson lower bound is at least 70%.
- `REJECTED`: minimum evidence passes, no more than 50% are observed within 30
  seconds, and the 95% Wilson upper bound is at most 60%.
- `INCONCLUSIVE`: minimum evidence fails, the interval overlaps the support or
  rejection gap, or the point estimate lies between the two decision regions.

At 100 observations, 80/100 has a Wilson interval of approximately
71.12%-86.66%, while 50/100 has an interval of approximately 40.38%-59.62%.

### H3

- `SUPPORTED`: minimum evidence passes, at least 70% of eligible trades retain
  60 seconds, and the 95% Wilson lower bound is at least 60%.
- `REJECTED`: minimum evidence passes, no more than 30% retain 60 seconds, and
  the 95% Wilson upper bound is at most 40%.
- `INCONCLUSIVE`: minimum evidence fails, the interval overlaps the support or
  rejection gap, or the point estimate lies between the two decision regions.

At 100 observations, 70/100 has a Wilson interval of approximately
60.42%-78.11%, while 30/100 has an interval of approximately 21.89%-39.58%.

The existing 30-second marginal and 60-second sufficient classifications
remain descriptive. They are not execution-quality estimates.

## Program Action

- `CONTINUE`: H2 or H3 is inconclusive, minimum evidence is incomplete, and
  the collection budget remains.
- `GRADUATE_TO_ENGINEERING`: both H2 and H3 are supported and every minimum
  evidence gate passes. Graduation authorizes only a bounded liquidity,
  slippage, and execution-delay feasibility experiment. It does not authorize
  trading or imply profitability.
- `FREEZE`: either H2 or H3 is rejected, or 60 total bounded five-minute
  sessions are completed without satisfying the minimum evidence gate. Freeze
  means stop wallet-copy engineering until materially new public data becomes
  available.

Evaluate after every 10 completed sessions and immediately when 100 eligible
trades are reached. Stop collection as soon as `GRADUATE_TO_ENGINEERING` or
`FREEZE` is triggered.

## Current Automatic Evaluation

- Eligible trades: 2 of 100.
- Distinct wallets: 1 of 3; both rows came from one wallet.
- Sessions: 1 of 10.
- Distinct UTC dates: 1 of 5.
- Assets: BTC and SOL, one row each; neither reaches 20.
- H2 successes: 2 of 2, 100%; 95% Wilson interval 34.24%-100%.
- H3 successes: 1 of 2, 50%; 95% Wilson interval 9.45%-90.55%.
- H2: `INCONCLUSIVE`.
- H3: `INCONCLUSIVE`.
- Program action: `CONTINUE`.

The current intervals include both weak and strong underlying rates. The two
rows demonstrate measurability, not a decision.
