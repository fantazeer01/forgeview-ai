# Wallet Intelligence Information Gain Sprint v1

Generated: June 26, 2026

## Purpose

This sprint ranks missing information layers by research value per engineering effort for Wallet Intelligence. It does not implement a new layer, modify Wallet Score, modify Wallet Watchlist, redesign the pipeline, place orders, connect wallets, copy trades, inspect sealed holdout outcomes, or run holdout evaluation.

## Evidence Base

Observed facts from Wallet Copyability Feasibility Sprint v1:

- 30 wallets were selected and classified.
- 5,765 public primary activity rows were normalized.
- 3,000 `/trades` cross-check rows were fetched.
- 2,135 lifecycle candidates were reconstructed.
- Lifecycle statuses were 1,735 still-open, 296 partial exits, 80 full exits, and 24 bounded-history oversold candidates.
- 4,897 normalized rows were fast crypto rows.
- Asset row counts were 4,073 BTC, 778 ETH, 282 SOL, and 632 other.
- Wallet Score separated the batch into 3 `high_priority`, 13 `medium_priority`, 12 `low_priority`, and 2 `insufficient_visible_structure` wallets.
- Copyability research classified 11 wallets as `monitor_candidate`, 17 as `needs_more_history`, 2 as `insufficient_signal`, and 0 as `exclude_for_now`.
- The previous sprint explicitly identified realized outcome joins, expiry joins, complete unbounded history, entry-to-exit holding time, observation delay, slippage, liquidity/fill uncertainty, queue position, maker/taker completeness, and BTC/ETH/SOL reference alignment as unknown.

Engineering judgment used in this sprint:

- A layer gets higher priority when it removes uncertainty already visible in the 30-wallet evidence.
- A layer gets higher priority when it improves multiple downstream artifacts without requiring a scoring change.
- A layer gets lower priority when it depends on unproven endpoint availability, market microstructure reconstruction, or hidden execution assumptions.
- The next week should favor a layer that is bounded, reproducible, and directly improves lifecycle interpretation before any scoring or ranking expansion.

Unknown assumptions:

- Public market metadata coverage for the current 2,135 lifecycle candidates has not yet been measured.
- Public resolved outcome coverage for old fast crypto markets has not yet been measured in this wallet branch.
- Deeper pagination may be incomplete or filtered by public endpoint defaults.
- Historical order book depth at exact wallet trade timestamps may not be recoverable from public endpoints.
- Public observation delay is not necessarily equal to a real observer's discovery delay.

## Highest Information Gain

The highest expected information gain is **Market expiry**.

Why:

- The previous sprint had 1,735 still-open lifecycle candidates, so expiry context attacks the largest visible ambiguity directly.
- Expiry makes time-to-expiry measurable without needing profitability, mark-to-market, or execution assumptions.
- Expiry can distinguish a position that is still open because the market is unresolved from a position that is only still open because the bounded history lacks the later exit.
- Expiry improves Lifecycle, Metrics, Wallet Score interpretability, Watchlist reasons, Copyability confidence, and future Ranking readiness without changing the score formula.
- Engineering effort is medium, risk is low, and public market metadata should be more reproducible than liquidity, queue, or delay models.

## Candidate Layer Findings

### 1. Market Expiry

What becomes measurable:

- time-to-expiry at entry;
- entry timing bucket relative to market close;
- held-through-expiry candidates;
- whether an all-open visible lifecycle is structurally plausible or just missing a later exit;
- late-window behavior.

Which uncertainty disappears:

- expiry timing;
- part of hold-to-resolution versus exit-before-expiry ambiguity;
- whether entries happen early, mid-window, or near settlement.

False positives made impossible:

- treating an all-open lifecycle as interesting when all rows are simply pre-expiry and incomplete;
- treating visible partial exits as meaningful without knowing whether they occurred near expiry.

False negatives made detectable:

- wallets that look low-signal structurally but repeatedly enter close to expiry;
- wallets that look all-open but are actually still unresolved at observation time.

Impact:

- Lifecycle: very high;
- Metrics: very high;
- Wallet Score: high interpretability, no formula change required;
- Watchlist: high reason-code quality;
- Copyability: high confidence improvement;
- Ranking: useful later after outcome and execution context;
- Confidence: very high.

### 2. Resolved Market Outcome

What becomes measurable:

- resolved side;
- terminal outcome context;
- whether visible bought side eventually aligned with final settlement.

Which uncertainty disappears:

- final outcome ambiguity;
- some false positives where strong structure is on the wrong resolved side;
- some false negatives where weaker structure repeatedly aligns with final resolution.

False positives made impossible:

- structural monitor candidates whose visible side repeatedly resolves against them can be flagged for deeper review.

False negatives made detectable:

- wallets with modest structure but consistent final-side alignment can be surfaced for later review.

Impact:

- Lifecycle: medium;
- Metrics: high;
- Wallet Score: should remain excluded until a new design explicitly allows outcome context;
- Watchlist: high as report-only evidence;
- Copyability: high;
- Ranking: high later, but not yet;
- Confidence: high.

Important boundary:

- Resolved outcome must not be treated as PnL, ROI, future-return evidence, market advantage, or trading guidance.

### 3. Full Historical Wallet Activity

What becomes measurable:

- complete visible trade sequence per wallet;
- earlier buys before bounded SELL rows;
- later sells after bounded BUY rows;
- more accurate lifecycle open/partial/full/oversold status;
- longer repeated-pattern evidence.

Which uncertainty disappears:

- bounded-history artifacts;
- many SELL-only and still-open ambiguities;
- sample-size fragility for low-history wallets.

False positives made impossible:

- wallets that score well only because the first two pages omit exits or losses of structure.

False negatives made detectable:

- wallets whose bounded first pages are sparse but deeper pages reveal repeatable fast-crypto behavior.

Impact:

- Lifecycle: very high;
- Metrics: very high;
- Wallet Score: high after rerun with same formula;
- Watchlist: high;
- Copyability: high;
- Ranking: high later;
- Confidence: high.

Cost:

- high, because safe pagination, caching, endpoint filter validation, and reproducibility controls are required.

### 4. Mark-To-Market Valuation

What becomes measurable:

- rough current value of visible open positions;
- unresolved exposure context;
- whether open positions are near terminal or ambiguous.

Which uncertainty disappears:

- current open-position valuation only.

False positives made impossible:

- some all-open positions that are effectively terminal could be separated from genuinely uncertain open positions.

False negatives made detectable:

- wallets with structurally open positions that are close to terminal value.

Impact:

- Lifecycle: medium;
- Metrics: medium;
- Wallet Score: not allowed without redesign;
- Watchlist: medium as report-only context;
- Copyability: medium;
- Ranking: useful later;
- Confidence: medium.

Risk:

- mark-to-market can easily be mistaken for performance; it should wait until expiry/outcome context exists.

### 5. Reference Asset Alignment

What becomes measurable:

- BTC/ETH/SOL price movement before and after wallet entries;
- whether entries follow external momentum;
- whether wallet activity resembles repricing behavior.

Which uncertainty disappears:

- Binance/reference lag alignment;
- whether fast-crypto exposure is actually external-move reactive.

False positives made impossible:

- wallets that look fast-crypto focused but do not enter around meaningful external asset movement.

False negatives made detectable:

- wallets with modest lifecycle structure but strong external-move timing.

Impact:

- Lifecycle: low;
- Metrics: medium;
- Wallet Score: no direct change;
- Watchlist: high research context;
- Copyability: high;
- Ranking: useful later;
- Confidence: high for repricing linkage.

Dependency:

- best after expiry/outcome context, because entries need market-time context.

### 6. Execution Delay Modelling

What becomes measurable:

- assumed follower observation delay;
- time between public trade row timestamp and hypothetical reaction;
- sensitivity of candidate behavior to delay windows.

Which uncertainty disappears:

- only part of copy-delay uncertainty.

False positives made impossible:

- wallets whose visible behavior requires reacting faster than a public observer can plausibly react.

False negatives made detectable:

- slower patterns that remain observable after delay.

Impact:

- Lifecycle: low;
- Metrics: low;
- Wallet Score: not allowed now;
- Watchlist: medium;
- Copyability: high later;
- Ranking: high later;
- Confidence: medium.

Risk:

- high hidden-assumption risk without a measured public observation stream and liquidity context.

### 7. Liquidity / Slippage Estimation

What becomes measurable:

- rough fill feasibility;
- order book depth around trade timestamps;
- whether copied size would likely move price.

Which uncertainty disappears:

- part of fill uncertainty and slippage risk.

False positives made impossible:

- wallets whose visible trades occur in markets too thin to study as copy candidates.

False negatives made detectable:

- wallets trading repeatable liquid markets with structurally modest scores.

Impact:

- Lifecycle: low;
- Metrics: medium;
- Wallet Score: not allowed now;
- Watchlist: medium;
- Copyability: high later;
- Ranking: high later;
- Confidence: high for execution realism.

Cost:

- high, because historical book reconstruction or CLOB price-history joins are required.

### 8. Queue Position / Fill Uncertainty

What becomes measurable:

- possibly maker/taker role and queue priority, if public data supports it.

Which uncertainty disappears:

- fill-priority ambiguity only if historical book state is reconstructable.

False positives made impossible:

- wallets that depend on queue priority unavailable to a follower.

False negatives made detectable:

- wallets whose trades are marketable and less queue-dependent.

Impact:

- Lifecycle: low;
- Metrics: low;
- Wallet Score: not allowed now;
- Watchlist: low;
- Copyability: high only much later;
- Ranking: high only much later;
- Confidence: medium later.

Risk:

- very high; current evidence does not show that this is reliably reconstructable.

### 9. Additional Public Endpoints

What becomes measurable:

- cross-endpoint field completeness;
- closed-position context;
- value/traded aggregates;
- prices-history availability;
- metadata gaps not available from activity rows.

Which uncertainty disappears:

- whether current endpoint choice is filtering or omitting needed fields.

False positives made impossible:

- candidates caused by one endpoint's pagination or filtering artifact.

False negatives made detectable:

- wallets with missing activity rows but useful closed-position or position records elsewhere.

Impact:

- Lifecycle: high;
- Metrics: high;
- Wallet Score: medium through better inputs;
- Watchlist: high;
- Copyability: medium;
- Ranking: medium later;
- Confidence: high.

Risk:

- endpoint schemas and filters must be measured carefully before broad use.

### 10. Other Public Data Source: Explorer / On-Chain Settlement Metadata

What becomes measurable:

- transaction-level settlement provenance;
- possible redemption timing;
- external verification of hashes;
- condition/token provenance.

Which uncertainty disappears:

- some provenance uncertainty.

False positives made impossible:

- records with mismatched or unverifiable transaction provenance.

False negatives made detectable:

- wallets whose public API rows are sparse but transaction hashes expose settlement context.

Impact:

- Lifecycle: medium;
- Metrics: low;
- Wallet Score: no immediate change;
- Watchlist: low;
- Copyability: medium later;
- Ranking: low now;
- Confidence: medium.

Risk:

- high engineering cost and possible indexer complexity; not first-week material.

## Information Gain Matrix Summary

The CSV matrix ranks each layer by engineering effort, research value, implementation risk, data reliability, expected impact, and priority. The top five are:

1. Market expiry
2. Resolved market outcome
3. Full historical wallet activity
4. Additional public endpoints
5. Reference asset alignment

## Best One-Week Capability

If only one additional capability can be implemented during the next week, it should be:

**Wallet Market Expiry Join Sprint v1**

Support:

- Expiry directly addresses the largest measured structural ambiguity: 1,735 of 2,135 lifecycle candidates are still-open.
- Expiry improves existing lifecycle status interpretation without changing Wallet Score, Wallet Watchlist, or the pipeline.
- Expiry provides time-to-expiry and late-window behavior, which are central to distinguishing final-resolution behavior from short-window repricing behavior.
- Expiry has a better cost/value ratio than full historical pagination, liquidity, slippage, queue modelling, or execution-delay modelling.
- Expiry is less likely than resolved outcomes or mark-to-market values to be misread as a performance claim.

## Validation

Observed facts:

- All numerical support in this report comes from the previous bounded copyability sprint artifacts.
- No public endpoints were queried in this sprint.
- No new data layer was implemented.
- Wallet Score and Wallet Watchlist were not changed.

Engineering judgement:

- Market expiry has the best next-week cost/value ratio.
- Resolved outcome is nearly as valuable but should follow or be paired only after expiry semantics are measured.
- Full history is valuable but too expensive to be the first next-week capability.

Unknown assumptions:

- Actual market metadata join coverage is not measured yet.
- Some old market slugs or condition IDs may not resolve through public metadata endpoints.
- Outcome and expiry endpoint coverage may differ by market age and market type.

## Non-Claims

This sprint does not claim profitability, market advantage, successful copying, future returns, execution quality, or trading suitability. It is a research prioritization artifact only.
