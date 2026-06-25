# Wallet Score Broader Evidence Collection Design v1

Generated: 2026-06-26

## Scope

This design defines a bounded, reproducible, public read-only evidence batch
for evaluating Wallet Score v1 behavior beyond the current six-wallet fixture.
It does not implement collection, launch ingestion, add score inputs, change
thresholds, compute PnL/ROI/Sharpe, infer copyability, join mark-to-market
values, connect wallets, place orders, inspect sealed holdout outcomes, or run
holdout evaluation.

Wallet Score v1 remains a structural research-priority score only. It is not a
profitability score, alpha score, copyability score, execution-quality score,
trading recommendation, or wallet ranking for capital deployment.

## Design Inputs

- `polymarket/models/wallet_intelligence_v1/wallet_score_design/wallet_score_design_v1.md`
- `polymarket/models/wallet_intelligence_v1/wallet_score_fixture_review/wallet_score_fixture_review_report.md`
- `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_scores.csv`
- `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_scores_summary.json`
- `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_score_validation.json`
- `docs/polymarket/WALLET_INTELLIGENCE_RESEARCH_V1.md`

## Purpose

The broader evidence batch should answer a narrow structural question:

> Does Wallet Score v1 produce a useful, non-degenerate research-priority
> distribution when applied to more public wallets under the same bounded
> structural rules?

The batch is meant to evaluate score behavior, not wallet quality. It should
help decide whether the existing score bands and penalties are stable enough
for future Wallet Intelligence review or whether a later design review is
needed before any deeper-history work.

## Target Sample Size

Target sample: 30 public wallets.

Composition:

- 6 existing seed wallets;
- up to 12 additional fast BTC/ETH/SOL Up/Down oriented wallets;
- up to 6 active non-fast-crypto or mixed-market wallets;
- up to 6 lower-activity or insufficient-data control wallets.

Rationale:

- 30 wallets gives five times the current fixture size while remaining small
  enough for manual provenance review.
- The sample can reveal whether all scores collapse into one bucket, whether
  high-priority inflation appears, or whether insufficient-data rates dominate.
- The size keeps the first broader public batch bounded: at most 60 primary
  activity pages and 6,000 primary activity rows before dedupe.
- A 30-wallet sample is not large enough to support claims about population
  profitability, alpha, copyability, or wallet quality, and the artifacts must
  say so.

## Wallet Selection Criteria

Wallets may be included when they meet all base criteria:

- public Polymarket profile or wallet URL is available;
- profile can be represented by a stable `wallet_id` and `profile_url`;
- source of inclusion is recorded;
- no private, paid, authenticated, or key-based access is required;
- inclusion does not depend on sealed holdout data or ForgeView validation
  outcomes.

Preferred wallet categories:

- visible BTC/ETH/SOL Up/Down activity;
- repeated short-window crypto market participation;
- mixed market activity useful as a control;
- weather or non-crypto activity useful as a negative fast-crypto control;
- lower-activity wallets useful for insufficient-data behavior checks.

Selection must not use:

- PnL as a score input;
- ROI, realized profit, Sharpe, or mark-to-market values;
- copyability or smart-money labels as score features;
- private wallets, private keys, authenticated trading data, or order data;
- final resolved win/loss labels from sealed holdout artifacts.

Allowed source tags:

- `existing_seed`;
- `manual_public_profile`;
- `oss_reference_public_profile`;
- `polymarket_public_profile`;
- `control_wallet`.

Every selected wallet should carry a `selection_reason` such as
`fast_crypto_candidate`, `mixed_control`, `weather_control`,
`low_activity_control`, or `profile_resolution_check`.

## Safety And Data Limits

The first broader evidence implementation should use public read-only
endpoints only.

Primary activity endpoint:

- `activity?user=<wallet>&type=TRADE&limit=100&offset=<offset>`

Limits:

- maximum wallets: 30;
- maximum primary activity pages per wallet: 2;
- maximum primary activity rows per wallet: 200;
- maximum primary activity rows overall: 6,000;
- maximum cross-check `/trades?user=<wallet>` pages per wallet: 1;
- maximum cross-check rows per wallet: 100;
- maximum cross-check rows overall: 3,000;
- maximum retries per page: 2;
- minimum delay between wallet requests: 1 second;
- stop the batch on repeated endpoint errors rather than escalating request
  rate;
- no market-wide scans;
- no recursive profile crawling;
- no automatic follow-wallet expansion;
- no authenticated requests.

The implementation should support a dry-run manifest mode that validates the
wallet list and planned request count without fetching public rows.

## Expected Artifact Paths

Design artifact:

- `polymarket/models/wallet_intelligence_v1/wallet_score_broader_evidence_design/broader_evidence_plan.md`

Future input manifest:

- `polymarket/wallet_intelligence/watched_wallets_broader_v1.example.csv`

Future raw and normalized batch outputs:

- `polymarket/data/wallet_intelligence/trade_history_broader_v1/trade_history_raw.jsonl`
- `polymarket/data/wallet_intelligence/trade_history_broader_v1/trade_history_normalized.csv`
- `polymarket/data/wallet_intelligence/trade_history_broader_v1/trade_history_summary.json`
- `polymarket/data/wallet_intelligence/trade_history_broader_v1/broader_ingestion_report.md`
- `polymarket/data/wallet_intelligence/trade_history_broader_v1/broader_ingestion_report.json`
- `polymarket/data/wallet_intelligence/trade_history_broader_v1/validation_gate_results.json`
- `polymarket/data/wallet_intelligence/trade_history_broader_v1/reproducibility_hashes.json`

Future lifecycle and metrics outputs:

- `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_broader_v1/lifecycle_positions.csv`
- `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_broader_v1/lifecycle_summary.json`
- `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_broader_v1/lifecycle_validation.json`
- `polymarket/models/wallet_intelligence_v1/lifecycle_metrics_broader_v1/wallet_metrics.csv`
- `polymarket/models/wallet_intelligence_v1/lifecycle_metrics_broader_v1/wallet_metrics_summary.json`
- `polymarket/models/wallet_intelligence_v1/lifecycle_metrics_broader_v1/wallet_metrics_report.md`

Future score outputs:

- `polymarket/models/wallet_intelligence_v1/wallet_score_broader_evidence_v1/wallet_scores.csv`
- `polymarket/models/wallet_intelligence_v1/wallet_score_broader_evidence_v1/wallet_scores_summary.json`
- `polymarket/models/wallet_intelligence_v1/wallet_score_broader_evidence_v1/wallet_score_validation.json`
- `polymarket/models/wallet_intelligence_v1/wallet_score_broader_evidence_v1/wallet_score_report.md`
- `polymarket/models/wallet_intelligence_v1/wallet_score_broader_evidence_v1/score_behavior_review.md`

## Validation Gates

### Collection Gates

- wallet count is greater than 6 and no more than 30;
- every wallet has `wallet_id`, `profile_url`, `source`, and
  `selection_reason`;
- total planned requests remain within documented limits;
- all endpoints are public read-only;
- zero authenticated, wallet, private-key, order-placement, or execution paths
  are used;
- source URLs, fetch timestamps, endpoint names, page offsets, and raw hashes
  are recorded;
- dedupe keys are deterministic;
- repeated export hashes match.

### Normalization Gates

- required trade-history fields are present for every normalized row;
- timestamp parse rate is at least 99%;
- market classification coverage is at least 95%;
- recognizable BTC/ETH/SOL Up/Down rows receive complete fast-crypto
  classification;
- duplicate dedupe keys are zero after dedupe;
- unavailable fields are explicit, not guessed.

### Lifecycle And Metrics Gates

- lifecycle grouping uses `wallet_id`, `condition_id`, `token_id`, and
  `outcome`;
- position-size conservation passes;
- unexpected negative visible position size is zero;
- bounded-history oversold groups are recorded as data-limit artifacts;
- metric rows cover every wallet with at least one normalized trade row;
- metrics use structural fields only;
- no PnL, ROI, Sharpe, copyability, mark-to-market, execution quality, or
  ranking fields are generated.

### Score Gates

- score bounds remain 0 to 100;
- deterministic ordering remains score descending, fast-crypto share
  descending, lifecycle-position count descending, then `wallet_id` ascending;
- allowed score inputs exactly match Wallet Score Design v1;
- forbidden inputs used list is empty;
- missing metric handling is explicit and validation-gated;
- component and penalty bounds pass;
- score report language preserves structural research-priority interpretation;
- repeat export hash matches.

## Healthy Wallet Score Behavior

Healthy behavior in the broader evidence batch would include:

- non-degenerate score distribution across at least three score bands;
- deterministic outputs and stable ordering across repeated exports;
- insufficient-data rate between 10% and 45%;
- `high_priority` share no greater than 20%;
- at least some separation between fast-crypto-oriented wallets and control
  wallets;
- bounded-history penalties appearing where SELL-only or oversold artifacts
  are visible;
- no wallet receiving a high score primarily from one fragile artifact;
- validation gates passing without score-input changes.

These are behavior checks for the score design, not performance claims.

## Suspicious Wallet Score Behavior

Suspicious behavior requiring review before further use would include:

- more than 70% of wallets landing in the same score band;
- more than 20% of wallets landing in `high_priority`;
- more than 60% of wallets landing in `insufficient_visible_structure`;
- high-priority scores driven by tiny samples, all-open positions, or
  bounded-history oversold artifacts;
- unstable ordering across repeat exports;
- score changes caused by unavailable fields being guessed or silently filled;
- fast-crypto controls and non-crypto controls receiving indistinguishable
  score patterns without a clear structural reason;
- validation passing while forbidden fields appear in score inputs or reports.

## Review Criteria After Future Implementation

A future review should decide:

- whether current Wallet Score v1 thresholds remain acceptable;
- whether the insufficient-data rate is compatible with the public-history
  limits;
- whether the `high_priority` threshold is conservative enough;
- whether penalties are protecting against bounded-history artifacts;
- whether any additional design review is required before deeper-history
  joins;
- whether future work should continue with the same score, freeze the score
  for a larger public batch, or return to design.

The review must not use profitability, alpha, copyability, execution quality,
live trading, or sealed holdout outcomes as criteria.

## Recommended Successor Task

`Wallet Score Broader Evidence Batch Implementation v1`

The next task should implement the bounded public read-only broader evidence
batch using the existing wallet trade-history, lifecycle, metrics, and score
layers where possible. It should add the broader wallet manifest, enforce the
limits in this design, produce the expected artifacts, run validation gates,
and run the Wallet Intelligence and full test suites.

It must not add score inputs, change thresholds, compute PnL/ROI/Sharpe,
infer copyability, make trading recommendations, connect wallets/private keys,
place orders, inspect sealed holdout outcomes, run holdout evaluation, launch
capture campaigns, or train production models.
