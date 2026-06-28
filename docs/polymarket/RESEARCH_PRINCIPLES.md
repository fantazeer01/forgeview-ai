# Polymarket Research Principles

Status: Active
Last updated: June 28, 2026
Authority: Strategic research filter for ForgeViewAI Polymarket work

ForgeViewAI is a profit-seeking automation project, not a research project for
its own sake, not an infrastructure project, and not a general wallet analytics
product.

The governing business objective is:

> Build an automated system capable of generating sustainable profit on
> Polymarket five-minute BTC, ETH, and SOL markets and progress toward $10,000
> in cumulative realized profit.

Research questions, including public wallet activity and short-horizon
repricing, are supporting paths for finding or rejecting profitable strategies.

## Core Principles

1. Profit-First.
   Every sprint must either increase expected profitability or remove a blocker
   preventing profitable automated trading. A sprint satisfying neither
   criterion must not be pursued. Research, engineering, AI, data collection,
   and infrastructure are justified only as tools for meeting this test.

2. Evidence before engineering.
   Build only the smallest tool or artifact needed to test the current
   hypothesis. Prefer measured evidence over broader systems.

3. One profitability hypothesis or blocker per sprint.
   Every sprint must name exactly one primary profitability hypothesis or one
   blocker preventing profitable automated trading, with a measurable decision
   or completion condition.

4. Every sprint ends with a clear answer.
   Hypothesis conclusions are `supported`, `rejected`, or
   `inconclusive_with_next_blocker`. Blocker-removal conclusions are
   `removed`, `not_removed`, or `inconclusive_with_next_blocker`. Reports
   should not end with vague platform-building recommendations.

5. Infrastructure exists only to test hypotheses.
   Data ingestion, joins, metrics, and reports are justified only by expected
   information gain against a named hypothesis.

6. Eliminate hypotheses quickly.
   Negative evidence is a successful outcome when it prevents further work on
   a weak idea.

7. Prefer experiments over architecture.
   When choosing between a broad architecture task and a bounded experiment,
   choose the experiment unless the experiment is impossible without a small
   enabling tool.

8. Engineering work must justify itself through expected information gain.
   A task that cannot say what uncertainty it reduces should stay in the
   backlog.

## Core Hypotheses

### H1: Some public wallets consistently make better decisions than random.

Why it matters:

- If public wallets do not choose the resolved side more often than a random
  baseline in comparable five-minute BTC/ETH/SOL markets, wallet activity is
  unlikely to support a profitable strategy.

Evidence that confirms it:

- A predefined wallet cohort has a resolved-outcome match rate meaningfully
  above random after excluding unresolved and insufficient-evidence rows.
- The effect survives per-wallet minimum sample gates and is not explained by
  a single wallet, asset, or time period.

Evidence that rejects it:

- Resolved wallet choices are indistinguishable from random, unstable across
  wallets, or disappear after basic sample-size and asset controls.

Responsible future sprint:

- Wallet Outcome Skill Baseline Sprint v1.

### H2: Their actions become visible quickly enough.

Why it matters:

- A wallet can be skilled but unusable if public activity appears only after
  the market has already repriced or expired.

Evidence that confirms it:

- Public activity timestamps are available with enough precision to measure
  detection delay, and a material share of qualifying trades appear while the
  market still has actionable time and liquidity.

Evidence that rejects it:

- Public activity appears too late, timestamps are too coarse, or most
  qualifying actions are visible only after practical opportunity has passed.

Responsible future sprint:

- Wallet Activity Visibility Delay Sprint v1.

### H3: Enough time remains after detection to act.

Why it matters:

- Even immediately visible public actions are not useful if five-minute market
  windows leave no realistic time for decision, order placement, and fill.

Evidence that confirms it:

- Time-to-expiry at public detection remains above a predefined minimum for a
  meaningful share of candidate actions, and orderbook/liquidity snapshots
  suggest fills could be simulated conservatively.

Evidence that rejects it:

- Most candidate actions occur too close to expiry or after decisive repricing,
  leaving no defensible execution window.

Responsible future sprint:

- Wallet Detection-To-Expiry Feasibility Sprint v1.

### H4: Structural filters improve wallet selection.

Why it matters:

- If simple structural filters do not improve the candidate set, Wallet Score
  and Watchlist work adds complexity without improving research odds.

Evidence that confirms it:

- Predefined structural filters produce a wallet subset with better
  outcome-match, timeliness, or completeness characteristics than an
  unfiltered public-wallet baseline.

Evidence that rejects it:

- Structural filters fail to separate wallets, overfit tiny samples, or select
  wallets with weaker outcome or timing evidence than simple baselines.

Responsible future sprint:

- Wallet Structural Filter Lift Sprint v1.

### H5: Combining these signals can outperform random participation over time.

Why it matters:

- A strategy requires combined evidence: wallet skill, visibility, remaining
  time, liquidity, and conservative execution assumptions.

Evidence that confirms it:

- A frozen, reproducible rule using public wallet activity beats random
  participation and naive baselines over multiple time windows after
  conservative delay, spread, slippage, and liquidity assumptions.

Evidence that rejects it:

- The combined rule loses to random or naive baselines, depends on a single
  period or wallet, or fails under conservative cost and delay stress.

Responsible future sprint:

- Wallet Strategy Shadow Baseline Sprint v1.

## Task Filter

Before starting any new sprint, write down:

- the one profitability hypothesis or blocker under test;
- the expected profitability gain or blocker reduction;
- the minimum artifact needed;
- the rejection or completion condition;
- why this sprint matters for profitable automated trading.

If those fields cannot be filled in, the task is not ready.
