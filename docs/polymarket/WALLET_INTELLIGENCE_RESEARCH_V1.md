# Polymarket Wallet Intelligence Research v1

Status: Research structure created
Date: June 24, 2026
Scope: Manual and normalized wallet-behavior research, separate from outcome prediction, repricing research, live trading, and wallet execution

## Purpose

Wallet Intelligence Research v1 studies successful Polymarket wallets to
identify repeatable behavioral patterns in fast crypto markets, especially
BTC, ETH, and SOL Up or Down markets.

The branch asks whether observed wallet behavior can inform research
hypotheses about timing, sizing, side selection, holding period, and market
selection. It does not copy trades, place orders, connect wallets, or train a
production model.

This branch is separate from:

- final UP/DOWN outcome prediction;
- Repricing Research v1;
- live trading;
- wallet execution.

## Strict Boundaries

Wallet Intelligence Research v1 must not:

- inspect sealed holdout outcomes;
- run holdout evaluation;
- implement live trading;
- connect wallets or private keys;
- copy trades automatically;
- launch capture campaigns;
- train production models;
- modify the frozen validation protocol;
- write into canonical outcome-prediction train, validation, or holdout paths;
- treat observed wallet profitability as proof of a ForgeViewAI edge.

All wallet records are research observations. They may generate hypotheses,
but they do not authorize execution.

## Research Definition

The unit of analysis is a wallet or Polymarket profile observed from public
profile and position information.

Wallet Intelligence Research v1 records:

- static wallet/profile identifiers;
- aggregate profile statistics, when publicly visible;
- position and market-type exposures;
- repeated behavioral patterns;
- timing behavior around fast crypto markets;
- manual copyability risk;
- whether behavior appears closer to repricing, final-resolution betting, or
  another pattern.

The initial implementation is a memory and schema scaffold only. It does not
fetch profile data, normalize positions, score wallets, or automate any action.

## Wallet Research Schema

Each normalized wallet research record should include:

- `wallet_id`
- `profile_url`
- `label`
- `source`
- `notes`
- `total_pnl`
- `prediction_count`
- `biggest_win`
- `active_position_count`
- `closed_position_count`
- `market_types`
- `btc_exposure`
- `eth_exposure`
- `sol_exposure`
- `yes_position_count`
- `no_position_count`
- `yes_no_distribution`
- `average_entry_price`
- `average_exit_or_resolution_price`
- `average_holding_time_seconds`
- `position_sizing_summary`
- `repeated_market_patterns`
- `late_entry_behavior`
- `cheap_side_buying_behavior`
- `hold_to_resolution_vs_exit_before_expiry`
- `drawdown_behavior`
- `copyability_score`
- `copyability_notes`

Fields may be null when public profile data is unavailable or not yet
normalized. Missing data must be explicit rather than inferred.

## Research Questions

Wallet Intelligence Research v1 should answer:

- Are profitable wallets trading repricing or final resolution?
- Do they buy cheap 10-20 cent outcomes?
- Do they hold to expiry?
- Do they enter after Binance momentum?
- Do they focus on BTC only or multi-asset BTC/ETH/SOL exposure?
- Do they have repeatable sizing rules?
- Is there a copy-trading delay risk?
- Can their behavior inform the existing repricing strategy?

## Initial Watched Wallets

The initial public profile list is stored in:

- `polymarket/wallet_intelligence/watched_wallets.example.csv`

Initial profiles:

- `https://polymarket.com/0x63ce342161250d705dc0b16df89036c8e5f9ba9a`
- `https://polymarket.com/0xde17f7144fbd0eddb2679132c10ff5e74b120988`
- `https://polymarket.com/0x1f0ebc543b2d411f66947041625c0aa1ce61cf86`
- `https://polymarket.com/@k9Q2mX4L8A7ZP3R`
- `https://polymarket.com/@0x594edB9112f526Fa6A80b8F858A6379C8A2c1C11`
- `https://polymarket.com/0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`

These are seed profiles only. No profitability or behavioral conclusion is
made until public profile and position data is collected and normalized.

## Copyability Score Definition

`copyability_score` is a research-only heuristic from 0 to 100.

It should consider:

- whether the wallet uses repeatable market types;
- whether entries are observable before most repricing has occurred;
- whether position sizes are stable enough to interpret;
- whether holding periods are long enough to reduce observation-delay risk;
- whether behavior depends on fast fills, unavailable liquidity, or private
  information;
- whether drawdowns and losses are visible enough to avoid survivorship bias.

The score is not an execution signal. A high score means the behavior is easier
to study, not safe to copy.

## Relationship to Repricing Research

Wallet behavior may inform repricing hypotheses when wallets appear to:

- enter after external BTC/ETH/SOL momentum;
- buy the underpriced side before a contract reprices;
- exit before final resolution;
- repeat similar timing behavior across many short-window markets.

Wallet behavior should remain descriptive until independently tested using the
existing repricing evidence gates. Observed wallet wins must not be merged into
repricing claims without separate, leakage-controlled evidence.

## Required Future Ingestion

The next active task is Wallet Intelligence Data Ingestion v1.

That task should collect and normalize public wallet profile and position data
for the watched-wallet list only. It must produce structured records suitable
for manual review and research analysis. It must not copy trades, place
orders, connect wallets, run holdout evaluation, launch capture campaigns, or
train production models.

## Open Source Intelligence Notes

Polymarket Open Source Intelligence Audit v1 is stored under:

- `polymarket/models/open_source_intelligence_audit_v1/`

Wallet-intelligence findings:

- `ent0n29/polybot` is the highest-priority deep-dive target because it
  includes public user-trade ingestion, Polymarket profile resolution,
  research snapshots, replication scoring, paper-vs-target-user matching,
  maker fill calibration, and BTC/ETH Up/Down target-wallet analysis.
- `MrFadiAi/Polymarket-bot` is useful as a smart-money and follow-wallet
  service-shape reference, but its private-key and order-placement examples
  are outside ForgeView's research boundary.
- `aarora4/Awesome-Prediction-Market-Tools` is useful as a source-discovery
  directory for analytics, alerts, smart-money trackers, copy-trading
  services, and data vendors.
- Copy-trading behavior must be treated as a research subject, not an action.
  Future wallet records should measure observation delay, paired-outcome
  behavior, position sizing, hold time, realized/unrealized split, and
  copyability risk before any score is assigned.

These findings do not authorize trade copying, wallet/private-key use, live
trading, capture campaigns, production model training, or holdout evaluation.

## Data Ingestion v1 Findings

Wallet Intelligence Data Ingestion v1 is complete.

Outputs:

- `polymarket/data/wallet_intelligence/v1/wallets_raw.jsonl`
- `polymarket/data/wallet_intelligence/v1/wallet_profiles.csv`
- `polymarket/data/wallet_intelligence/v1/wallet_positions.csv`
- `polymarket/data/wallet_intelligence/v1/wallet_summary.json`
- `polymarket/data/wallet_intelligence/v1/ingestion_report.md`
- `polymarket/data/wallet_intelligence/v1/ingestion_report.json`

The bounded public snapshot resolved all six seed profiles and produced six
wallet-level rows plus 460 normalized position rows at retrieval timestamp
`2026-06-24T20:00:17+00:00`.

Fast-market crypto wallets in the bounded snapshot:

- `0x63ce342161250d705dc0b16df89036c8e5f9ba9a` - 45 fast crypto positions;
- `0x1f0ebc543b2d411f66947041625c0aa1ce61cf86` - 44 fast crypto positions;
- `0xd0d6053c3c37e727402d84c14069780d360993aa` - 38 fast crypto positions,
  resolved from `https://polymarket.com/@k9Q2mX4L8A7ZP3R`;
- `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a` - 100 fast crypto positions.

Other seed-wallet profiles:

- `0x594edB9112f526Fa6A80b8F858A6379C8A2c1C11` is weather-heavy in the bounded
  snapshot, with 88 weather positions and no fast crypto positions;
- `0xde17f7144fbd0eddb2679132c10ff5e74b120988` is crypto-exposed but not
  fast Up/Down focused in the bounded snapshot.

Ingestion limits:

- public `closed-positions` snapshots are capped at the first 50 rows per
  wallet in this task;
- average holding time is unavailable without linked entry and exit events;
- drawdown behavior is unavailable from first-page position snapshots;
- late-entry behavior and Binance-Polymarket lag behavior require timestamped
  trade/fill history plus external BTC/ETH/SOL reference prices;
- copyability scores are research-only and capped by missing observation-delay,
  liquidity, queue-position, and fill-priority evidence.

The successor after ingestion was Wallet Intelligence Behavior Metrics v1. It
has now been completed and remains descriptive only. It did not copy trades,
place orders, connect wallets, launch capture campaigns, inspect sealed
holdout outcomes, run holdout evaluation, or train production models.

## Behavior Metrics v1 Findings

Wallet Intelligence Behavior Metrics v1 is complete.

Outputs:

- `polymarket/models/wallet_intelligence_v1/behavior_metrics/behavior_metrics_report.md`
- `polymarket/models/wallet_intelligence_v1/behavior_metrics/behavior_metrics_report.json`
- `polymarket/models/wallet_intelligence_v1/behavior_metrics/wallet_behavior_metrics.csv`
- `polymarket/models/wallet_intelligence_v1/behavior_metrics/wallet_similarity_matrix.csv`
- `polymarket/models/wallet_intelligence_v1/behavior_metrics/wallet_clusters.csv`
- `polymarket/models/wallet_intelligence_v1/behavior_metrics/copyability_risk.csv`

Findings from the existing ingestion snapshot only:

- wallets analyzed: 6;
- classifications: 4 fast crypto focused, 1 weather focused, 1 mixed;
- strongest fast-market wallet:
  `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`, with 100 visible BTC Up/Down
  positions and 100% fast-market share;
- aggregate side distribution: 234 YES-like / 225 NO-like, balance 0.980392;
- dominant entry bucket: `80_100c`, 111 of 460 visible positions;
- cheap-side buying at >=20% of visible entries appears in three wallets;
- most similar fast-crypto pair:
  `0x1f0ebc543b2d411f66947041625c0aa1ce61cf86` and
  `0xd0d6053c3c37e727402d84c14069780d360993aa`, similarity 0.939721.

Copyability risk remains high:

- all wallet data is a partial/truncated first-page public snapshot;
- likely delay risk is high for fast crypto wallets;
- liquidity/fill uncertainty is material, especially for large visible
  position sizes;
- exit timing, average holding time, drawdown, late-window behavior, and
  Binance-lag alignment remain unavailable;
- copyability scores are research-only and intentionally low.

Next research task: Wallet Intelligence Deep History Feasibility v1. It should
assess whether existing public sources can safely support linked entry/exit
timing and observation-delay analysis. It must not fetch new campaign data,
copy trades, place orders, connect wallets, inspect sealed holdout outcomes,
run holdout evaluation, or train production models.

## Deep History Feasibility v1 Findings

Wallet Intelligence Deep History Feasibility v1 is complete.

Outputs:

- `polymarket/models/wallet_intelligence_v1/deep_history_feasibility/deep_history_feasibility_report.md`
- `polymarket/models/wallet_intelligence_v1/deep_history_feasibility/deep_history_feasibility_report.json`
- `polymarket/models/wallet_intelligence_v1/deep_history_feasibility/endpoint_inventory.csv`
- `polymarket/models/wallet_intelligence_v1/deep_history_feasibility/wallet_feasibility_matrix.csv`
- `polymarket/models/wallet_intelligence_v1/deep_history_feasibility/bounded_probe_sample.jsonl`

Conclusion:

- public wallet deep history is feasible for bounded, read-only research;
- the best first endpoint path is
  `GET https://data-api.polymarket.com/activity?user=<wallet>&type=TRADE&limit<=500&offset=<offset>`;
- `/trades?user=<wallet>` should be used as a cross-check because endpoint
  defaults such as `takerOnly` can affect completeness;
- `/positions`, `/closed-positions`, CLOB `/prices-history`, and external
  BTC/ETH/SOL reference prices are required joins for exit timing,
  time-to-expiry, and Binance-lag analysis;
- full strategy reconstruction and copyability remain infeasible from wallet
  endpoints alone.

Bounded probe:

- one read-only probe was performed for
  `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`;
- maximum rows requested: 50;
- rows returned: 50 public `TRADE` rows;
- observed fields include timestamps, transaction hashes, condition IDs,
  token/outcome asset IDs, sides, prices, sizes, outcomes, market slugs, and
  event slugs.

Fields that can be reconstructed with joins:

- entry timestamp and entry price for BUY trade rows;
- side, outcome, market type, size, and USDC notional where present;
- partial exit timestamp and exit price from SELL, REDEEM, closed-position,
  and resolution evidence;
- partial holding time by matching wallet, condition ID, token ID, side, and
  lifecycle events;
- time-to-expiry at entry after joining market `endDate` or parsing dated
  fast-market slugs;
- Binance-lag alignment only after external BTC/ETH/SOL reference prices are
  joined to wallet trade timestamps.

Fields still unavailable or incomplete:

- private trader intent or decision rules;
- queue position, fill priority, and guaranteed liquidity at observation time;
- complete maker/taker role for every public row until `/trades` filters are
  validated;
- full exit linkage when only aggregate positions are present;
- copy-trading delay and fill certainty;
- Binance-lag conclusions from Polymarket wallet endpoints alone.

Next research task: Wallet Public Trade History Ingestion Design v1. It should
design a bounded, cached, read-only schema and ingestion plan for public
trade/activity rows, not launch a broad collection or implement execution.

## Public Trade History Ingestion Design v1

Wallet Public Trade History Ingestion Design v1 is complete.

Outputs:

- `polymarket/models/wallet_intelligence_v1/trade_history_ingestion_design/trade_history_ingestion_design.md`
- `polymarket/models/wallet_intelligence_v1/trade_history_ingestion_design/trade_history_ingestion_design.json`
- `polymarket/models/wallet_intelligence_v1/trade_history_ingestion_design/trade_history_schema.csv`
- `polymarket/models/wallet_intelligence_v1/trade_history_ingestion_design/join_plan.csv`
- `polymarket/models/wallet_intelligence_v1/trade_history_ingestion_design/ingestion_limits.json`
- `polymarket/models/wallet_intelligence_v1/trade_history_ingestion_design/validation_gate_definition.json`

Schema summary:

- the design defines 35 normalized fields for public wallet trade/activity
  rows;
- core identifiers include `wallet_id`, `profile_url`, `source_endpoint`,
  `activity_timestamp`, `transaction_hash`, `condition_id`, `token_id`,
  `asset_id`, `market_slug`, `event_slug`, `outcome`, and `side`;
- pricing fields include `price`, `size`, `notional_value`, and
  `notional_source`;
- classification fields include `market_type`, `asset_class`,
  `up_down_market`, `entry_or_exit_candidate`, `lifecycle_group_key`, and
  `data_quality_flags`;
- provenance fields include `source_fetch_timestamp`, `raw_payload_hash`,
  `raw_page_hash`, and `normalization_version`.

First future ingestion scope:

- seed wallets only from `polymarket/wallet_intelligence/watched_wallets.example.csv`;
- six-wallet maximum for the first implementation;
- primary endpoint:
  `activity?user=<wallet>&type=TRADE&limit=100&offset=<offset>`;
- maximum three primary activity pages per wallet;
- maximum 300 primary activity rows per wallet;
- maximum 1,800 primary activity rows across the first scope;
- cross-check endpoint: `/trades?user=<wallet>&limit=100&offset=0`;
- maximum one cross-check page and 100 cross-check rows per wallet;
- maximum 600 cross-check rows across the first scope;
- no market-wide scans, no authenticated requests, and no unbounded history
  ingestion.

Join plan:

- activity rows to market metadata by condition ID and market slug;
- condition IDs to market slugs across activity, trades, and position
  snapshots;
- token IDs / asset IDs to outcomes using endpoint rows and market metadata;
- trades to positions and closed positions by wallet, condition ID, token ID,
  and outcome;
- trades to CLOB `prices-history` by token ID and narrow timestamp windows;
- trades to external BTC/ETH/SOL reference snapshots by asset class and
  timestamp;
- lifecycle grouping by wallet, condition ID, token ID, outcome, side, and
  timestamp.

Validation gates:

- 100% required-field coverage for core normalized fields;
- duplicate rate no greater than 1% before dedupe and zero duplicate dedupe
  keys after dedupe;
- at least 99% timestamp parse rate;
- at least 95% market classification coverage;
- 100% fast-crypto classification coverage for recognizable BTC/ETH/SOL
  Up/Down rows;
- 100% provenance completeness;
- deterministic export hashes across two rebuilds;
- bounded-scope enforcement against `ingestion_limits.json`;
- no authenticated, execution, holdout, or campaign paths touched;
- explicit join-quality reporting without imputing unavailable fields.

Next research task: Wallet Public Trade History Ingester Fixture
Implementation v1. It should implement schema constants, fixture-based
normalizer/deduper tests, and CLI dry-run/inspect scaffolding using saved probe
fixtures only. It must not fetch broad public history yet.

## Public Trade History Ingester Fixture Implementation v1

Wallet Public Trade History Ingester Fixture Implementation v1 is complete.

Code and CLI:

- schema constants and `TradeHistoryRecord` live in
  `polymarket/wallet_intelligence/schema.py`;
- fixture normalization, hashing, deduplication, validation gates, and export
  logic live in `polymarket/wallet_intelligence/trade_history.py`;
- the fixture CLI command is:
  `python -m polymarket.wallet_intelligence trade-history-fixture`;
- tests live in `tests/polymarket/test_wallet_intelligence.py`.

Outputs:

- `polymarket/models/wallet_intelligence_v1/trade_history_ingester_fixture/fixture_ingestion_report.md`
- `polymarket/models/wallet_intelligence_v1/trade_history_ingester_fixture/fixture_ingestion_report.json`
- `polymarket/models/wallet_intelligence_v1/trade_history_ingester_fixture/normalized_trades_fixture.csv`
- `polymarket/models/wallet_intelligence_v1/trade_history_ingester_fixture/raw_trades_fixture.jsonl`
- `polymarket/models/wallet_intelligence_v1/trade_history_ingester_fixture/validation_gate_results.json`
- `polymarket/models/wallet_intelligence_v1/trade_history_ingester_fixture/reproducibility_hashes.json`

Fixture result:

- source fixture:
  `polymarket/models/wallet_intelligence_v1/deep_history_feasibility/bounded_probe_sample.jsonl`;
- wallet:
  `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`;
- fixture pages: 1;
- input rows: 50;
- normalized rows: 50;
- duplicate rows removed: 0;
- validation gates passed: 10 / 10;
- deterministic CSV repeat export: true;
- Parquet status: `not_written_no_project_parquet_dependency`;
- automated tests: 105 passing.

Implemented behavior:

- normalizes public activity `TRADE` fixture rows into the 35-field schema;
- preserves source endpoint, source fetch timestamp, raw row hash, raw page
  hash, normalization version, dedupe key, and quality flags;
- classifies BTC, ETH, and SOL Up/Down markets as `fast_crypto_up_down`;
- classifies non-crypto/weather fixture rows separately;
- computes notional value from endpoint `usdcSize` when present and from
  price times size when absent;
- deduplicates rows deterministically by wallet, endpoint, transaction hash,
  condition ID, token ID, timestamp, side, price, and size;
- enforces design limits from `ingestion_limits.json` in fixture paths;
- provides a join-quality reporting placeholder without imputing unavailable
  joins.

This implementation remains fixture-only. It does not fetch broad public
history, connect wallets, use private keys, place orders, copy trades, launch
capture campaigns, inspect sealed holdout outcomes, run holdout evaluation, or
train production models.

Next research task: Wallet Public Trade History Bounded Public Smoke v1. It
should run a separately authorized, tightly bounded, public read-only smoke
using the seed-wallet allowlist and design caps. It must stop before any broad
history ingestion or execution-adjacent behavior.

## Public Trade History Bounded Public Smoke v1

Wallet Public Trade History Bounded Public Smoke v1 is complete.

Code and CLI:

- public read-only activity trade fetch support is available through
  `PolymarketPublicClient.activity_trades`;
- the bounded smoke CLI command is:
  `python -m polymarket.wallet_intelligence trade-history-smoke`;
- normalization reuses `polymarket/wallet_intelligence/trade_history.py`.

Outputs:

- `polymarket/data/wallet_intelligence/trade_history_smoke_v1/trade_history_raw.jsonl`
- `polymarket/data/wallet_intelligence/trade_history_smoke_v1/trade_history_normalized.csv`
- `polymarket/data/wallet_intelligence/trade_history_smoke_v1/trade_history_summary.json`
- `polymarket/data/wallet_intelligence/trade_history_smoke_v1/bounded_smoke_report.md`
- `polymarket/data/wallet_intelligence/trade_history_smoke_v1/bounded_smoke_report.json`
- `polymarket/data/wallet_intelligence/trade_history_smoke_v1/validation_gate_results.json`
- `polymarket/data/wallet_intelligence/trade_history_smoke_v1/reproducibility_hashes.json`

Smoke scope:

- seed wallets attempted: 6;
- seed wallets succeeded: 6;
- public activity pages fetched: 6;
- maximum pages per wallet: 1;
- maximum rows per wallet: 100;
- total rows fetched: 600;
- total rows normalized: 600;
- duplicate rows removed: 0;
- endpoint errors: none.

Validation:

- required field coverage: passed;
- duplicate rate: passed;
- timestamp parse rate: passed;
- market classification coverage: passed;
- fast crypto classification coverage: passed;
- provenance completeness: passed;
- bounded scope compliance: passed;
- safety boundary compliance: passed;
- deterministic export: passed;
- join-quality reporting placeholder: passed;
- deterministic CSV repeat export: true;
- automated tests: 106 passing.

Observed smoke distribution:

- fast crypto rows: 367 / 600;
- BTC rows: 359;
- ETH rows: 97;
- SOL rows: 11;
- other rows: 133;
- YES-like outcomes: 249;
- NO-like outcomes: 351;
- BUY rows: 543;
- SELL rows: 57;
- price buckets:
  - `0_10c`: 201;
  - `10_20c`: 19;
  - `20_40c`: 97;
  - `40_60c`: 37;
  - `60_80c`: 106;
  - `80_100c`: 140.

Unavailable fields and limits:

- time-to-expiry and expiry timestamp are not joined yet;
- exit linkage and holding time are not reconstructed yet;
- queue position, fill priority, and liquidity-at-observation are unavailable;
- Binance/reference alignment is not joined yet;
- copyability delay remains unknown;
- no strategy intent, automatic copying, or execution claim is supported.

Next research task: Wallet Trade Lifecycle Reconstruction Design v1. It should
design grouping and validation rules for entry/exit candidates, partial exits,
holding-time estimates, and join prerequisites before any lifecycle inference
is implemented.

## Wallet Trade Lifecycle Reconstruction Fixture Prototype v1

Wallet Trade Lifecycle Reconstruction Fixture Prototype v1 is complete.

Code and CLI:

- lifecycle reconstruction logic lives in
  `polymarket/wallet_intelligence/lifecycle.py`;
- lifecycle schema fields live in `polymarket/wallet_intelligence/schema.py`;
- the fixture CLI command is:
  `python -m polymarket.wallet_intelligence trade-lifecycle-fixture`.

Outputs:

- `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture/lifecycle_positions.csv`
- `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture/lifecycle_summary.json`
- `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture/lifecycle_validation.json`
- `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture/reproducibility_hashes.json`

Scope and result:

- input: 600 normalized public smoke trade rows from
  `polymarket/data/wallet_intelligence/trade_history_smoke_v1/trade_history_normalized.csv`;
- grouping key: `wallet_id`, `condition_id`, `token_id`, and `outcome`;
- lifecycle position candidates reconstructed: 112;
- fast crypto lifecycle candidates: 75;
- asset counts: 78 BTC, 6 ETH, 2 SOL, and 26 other;
- status counts: 74 still-open candidates, 36 partial-exit candidates, 2
  bounded-history oversold candidates, and 0 full-exit candidates in the
  bounded smoke window.

Validation:

- deterministic ordering: passed;
- repeatable CSV output: passed;
- position-size conservation: passed;
- unexpected negative position groups: 0;
- bounded-history missing-prior-buy groups: 2;
- Wallet Intelligence tests: 18 passing;
- full automated suite: 112 passing.

Interpretation limits:

- oversold groups are treated as one-page bounded-history gaps, not strategy
  claims;
- no expiry joins, mark-to-market PnL, Binance/reference alignment,
  copyability-delay estimation, queue-priority modelling, broad public
  ingestion, automatic trade copying, live trading, wallet/private-key use,
  order placement, holdout inspection, or holdout evaluation was implemented;
- holding time remains unavailable until expiry/metadata and deeper history
  joins are separately designed and authorized.

Next research task: Wallet Lifecycle Reconstruction Review v1. It should
review the lifecycle candidates, quantify which groups are interpretable from
bounded public history, and decide whether a next bounded metrics task is
justified without adding execution or copy-trading logic.

## Wallet Lifecycle Reconstruction Review v1

Wallet Lifecycle Reconstruction Review v1 is complete.

Outputs:

- `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_review/lifecycle_review_report.md`
- `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_review/lifecycle_review_report.json`

Files inspected:

- `polymarket/wallet_intelligence/lifecycle.py`
- `polymarket/wallet_intelligence/schema.py`
- `polymarket/wallet_intelligence/cli.py`
- `tests/polymarket/test_wallet_intelligence.py`
- `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture/lifecycle_positions.csv`
- `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture/lifecycle_summary.json`
- `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture/lifecycle_validation.json`

Review findings:

- full-exit count is 0 because no group with both BUY and SELL rows has exact
  equality between total bought size and total sold size;
- 36 groups contain both BUY and SELL rows and remain partial exits under the
  exact-size policy;
- still-open status is correct for groups with visible BUY rows and no visible
  SELL rows, but it means still open within the bounded smoke window, not
  necessarily still open in complete wallet history;
- the two bounded-history oversold groups are SELL-only XRP Up/Down groups
  where prior buys are missing from the one-page public smoke window;
- BUY/SELL semantics are consistent with the current normalized public
  activity rows, where BUY maps to `entry_candidate` and SELL maps to
  `exit_candidate`;
- grouping by wallet, condition ID, token ID, and outcome is sufficient for
  the fixture prototype because it separates paired outcomes in the same
  market;
- deterministic ordering was adequate for the current data, and was hardened
  with dedupe/provenance tie-breakers during review.

Bounded correctness fixes:

- lifecycle group keys are now derived from explicit row fields rather than
  trusting the precomputed `lifecycle_group_key` string;
- deterministic ordering now includes `dedupe_key`, `raw_payload_hash`,
  `source_endpoint_name`, and `source_fetch_timestamp` after the existing
  timestamp, transaction hash, side, price, and size tie-breakers.

Tests:

- Wallet Intelligence tests: 19 passing;
- full automated suite: 113 passing.

Next research task: Wallet Lifecycle Metrics v1. It should compute bounded,
descriptive wallet-level lifecycle metrics from the existing lifecycle
positions only, including status counts, partial-exit frequency,
bounded-history gap rate, near-flat residual counts, asset/outcome
concentration, and wallet-level summaries. It must not launch ingestion, add
expiry joins, compute PnL, add Binance/reference alignment, estimate
copyability delay, model queue priority, add scoring, place orders, connect
wallets/private keys, inspect sealed holdout outcomes, or run holdout
evaluation.
