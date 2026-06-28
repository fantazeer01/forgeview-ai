# Wallet H2/H3 Remaining Evidence

## Current Position

The current recommendation is **CONTINUE**, not graduate and not freeze.

Only 2 eligible trades exist. H2 is 2/2 within 30 seconds, while H3 is 1/2
with at least 60 seconds remaining. Their 95% Wilson intervals are too wide to
exclude weak underlying rates:

- H2: 34.24%-100%;
- H3: 9.45%-90.55%.

## Remaining Minimum Evidence

- 98 additional eligible trades;
- 2 additional represented wallets;
- at least 10 eligible trades from each of 3 wallets;
- 9 additional sessions to reach the minimum session gate;
- 4 additional UTC dates;
- at least 20 rows for each of 2 represented assets;
- continued 95% timestamp and expiry completeness and 100% stable identity
  uniqueness.

The first session produced 2 eligible trades. If that rate persisted, 98 more
trades would require approximately 49 additional five-minute sessions, or 245
minutes of observation. This is a rough planning estimate from one session,
not a forecast.

## Finite Collection Rule

Evaluate progress after every 10 sessions. Stop when:

1. both H2 and H3 satisfy their support gates, then
   `GRADUATE_TO_ENGINEERING`;
2. either hypothesis satisfies its rejection gate, then `FREEZE`; or
3. 60 total bounded sessions are complete without minimum evidence, then
   `FREEZE` for insufficient observable opportunity density.

If 100 eligible rows are reached but the confidence intervals lie between the
support and rejection regions, remain `INCONCLUSIVE`. Further collection is
permitted only within the same 60-session budget; there is no automatic budget
extension.

## What Graduation Means

Graduation would authorize only a bounded engineering experiment for
execution delay, orderbook liquidity, spread, slippage, and fill feasibility.
It would not authorize trading, copying, wallet connection, or any claim about
profitability or expected return.
