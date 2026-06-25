# Wallet Score Design v1

Generated: 2026-06-25

## Scope

Wallet Score v1 is a bounded structural prioritization score for selecting
public Polymarket wallets worth deeper Wallet Intelligence analysis. It is not
a profitability score, alpha score, execution score, copyability score, or
wallet ranking for trading.

The design uses only current structural lifecycle metrics reviewed in:

- `polymarket/models/wallet_intelligence_v1/wallet_metrics_readiness_review/wallet_metrics_readiness_review.md`

This task does not implement score computation and does not modify metric
generation.

## Purpose

Wallet Score v1 should answer one narrow question:

> Which seed wallets have enough visible, fast-market, structurally
> interpretable lifecycle activity to justify deeper public-history analysis?

The score is for research triage. A high score means "inspect this wallet
first." It does not mean the wallet is profitable, skilled, copyable, or
useful for live trading.

## Explicit Non-Goals

Wallet Score v1 must not:

- claim profitability;
- claim alpha;
- estimate ROI;
- estimate PnL;
- estimate Sharpe;
- infer realized profit;
- rank wallets by trading quality;
- estimate execution quality;
- estimate copyability;
- imply automatic trade copying;
- use mark-to-market values;
- use sealed holdout outcomes;
- use final outcome-prediction validation data.

## Forbidden Inputs

The future implementation must fail validation if any of these inputs are used
as score features:

- PnL;
- ROI;
- realized profit;
- Sharpe;
- execution quality;
- copyability;
- alpha claims;
- mark-to-market values;
- wallet ranking labels;
- final resolved win/loss outcome;
- sealed holdout labels or outputs;
- private wallet data;
- order-placement data;
- authenticated trading data.

Identifiers and provenance fields are allowed for joins and reporting only,
not as score values:

- `wallet_id`;
- `profile_url`.

## Allowed Input Metrics

Allowed score inputs are limited to readiness-approved structural metrics from
`wallet_metrics.csv`:

- `total_lifecycle_positions`;
- `fast_crypto_lifecycle_count`;
- `fast_crypto_lifecycle_share`;
- `partial_exits`;
- `percentage_still_open_positions`;
- `percentage_sell_only_lifecycles`;
- `oversold_bounded_history`;
- `average_buy_count_per_lifecycle`;
- `average_sell_count_per_lifecycle`;
- `average_events_per_lifecycle`;
- `near_flat_residual_count`;
- `dominant_asset`;
- `asset_concentration`;
- `dominant_outcome`;
- `outcome_concentration`.

Raw visible size fields remain excluded from v1 scoring because the readiness
review classified them as useful later after normalization and completeness
policy.

`full_exits` remains excluded from v1 scoring because current full-exit
interpretation needs deeper history, expiry, or redemption context.

## Score Scale

Wallet Score v1 should produce:

- `wallet_score`: integer or fixed-decimal score from 0 to 100;
- `score_band`: categorical interpretation:
  - `high_priority`: score >= 75;
  - `medium_priority`: score >= 50 and < 75;
  - `low_priority`: score >= 25 and < 50;
  - `insufficient_visible_structure`: score < 25.

These bands are research-priority labels only. They are not wallet-quality,
profitability, alpha, execution, or copyability labels.

## Component Model

The future implementation should compute a bounded additive score:

```text
wallet_score =
  coverage_component
  + fast_crypto_component
  + lifecycle_activity_component
  + event_density_component
  + specialization_component
  - bounded_history_penalty
  - still_open_penalty
  - concentration_penalty
  - near_flat_ambiguity_penalty
```

Every component must be clipped to its documented bounds before summing. The
final score must be clipped to `[0, 100]`.

## Positive Components

| Component | Max Points | Inputs | Rationale |
|---|---:|---|---|
| Coverage | 25 | `total_lifecycle_positions` | More lifecycle candidates provide more structure for deeper analysis. |
| Fast-crypto relevance | 25 | `fast_crypto_lifecycle_share`, `fast_crypto_lifecycle_count` | Wallet Intelligence is focused on BTC/ETH/SOL Up/Down markets. |
| Lifecycle activity | 15 | `partial_exits`, `average_sell_count_per_lifecycle` | Visible SELL activity and partial exits make lifecycle behavior more interpretable than BUY-only snapshots. |
| Event-density consistency | 15 | `average_events_per_lifecycle`, `average_buy_count_per_lifecycle`, `average_sell_count_per_lifecycle` | Moderate repeated activity is more useful for structural research than a single sparse event. |
| Specialization | 10 | `dominant_asset`, `asset_concentration`, `dominant_outcome`, `outcome_concentration` | Some focus is useful for hypothesis generation, provided it is not extreme enough to reduce generality. |

The positive component maximum is 90 points. Penalties can reduce the score;
they cannot make the final score negative.

### Coverage Component

Suggested deterministic mapping:

- `total_lifecycle_positions < 5`: 0 points;
- `5-9`: 8 points;
- `10-24`: 15 points;
- `25-49`: 21 points;
- `>=50`: 25 points.

This treats too-small samples as insufficient for prioritization while not
claiming larger samples are better traders.

### Fast-Crypto Relevance Component

Suggested deterministic mapping:

- share points: `20 * fast_crypto_lifecycle_share`, clipped to `[0, 20]`;
- count support:
  - `fast_crypto_lifecycle_count < 5`: 0 points;
  - `5-9`: 2 points;
  - `10-24`: 4 points;
  - `>=25`: 5 points.

Maximum: 25 points.

### Lifecycle Activity Component

Suggested deterministic mapping:

- partial-exit share:
  `partial_exits / total_lifecycle_positions`, if denominator is positive;
- partial-exit points:
  - `0`: 0 points;
  - `(0, 0.10)`: 4 points;
  - `[0.10, 0.35)`: 8 points;
  - `[0.35, 0.75]`: 12 points;
  - `>0.75`: 8 points, because extreme exit share may reflect truncated
    history rather than stable behavior;
- SELL activity support:
  - `average_sell_count_per_lifecycle > 0`: 3 points;
  - otherwise 0.

Maximum: 15 points.

### Event-Density Consistency Component

Suggested deterministic mapping:

- `average_events_per_lifecycle < 1`: 0 points;
- `[1, 2)`: 8 points;
- `[2, 8]`: 15 points;
- `(8, 20]`: 11 points;
- `>20`: 6 points.

This favors repeated but interpretable activity. Very high event density may
be useful later, but in bounded one-page public history it can also make
entry/exit interpretation harder.

### Specialization Component

Suggested deterministic mapping:

- `dominant_asset` in `BTC`, `ETH`, or `SOL`: 4 points;
- `asset_concentration`:
  - `[0.30, 0.80]`: 4 points;
  - `(0.80, 0.95]`: 3 points;
  - `>0.95`: 1 point before concentration penalties;
  - otherwise 0;
- `outcome_concentration <= 0.70`: 2 points;
- `outcome_concentration > 0.70`: 0 points before concentration penalties.

Maximum: 10 points.

This component rewards interpretable focus without treating one-sided exposure
as quality.

## Penalties

| Penalty | Max Deduction | Inputs | Rationale |
|---|---:|---|---|
| SELL-only / bounded-history risk | 20 | `percentage_sell_only_lifecycles`, `oversold_bounded_history` | SELL-only and oversold groups are signs that the bounded smoke may be missing earlier buys. |
| Excessive still-open share | 15 | `percentage_still_open_positions` | Extremely open-looking snapshots are hard to interpret without deeper history. |
| Too few lifecycle positions | 20 | `total_lifecycle_positions` | Very small visible samples should not be prioritized. |
| Excessive concentration | 10 | `asset_concentration`, `outcome_concentration` | Extreme asset/outcome concentration may reduce generality and raise overinterpretation risk. |
| Near-flat residual ambiguity | 5 | `near_flat_residual_count`, `total_lifecycle_positions` | Near-flat residuals are informative but ambiguous until a dust policy or redemption join exists. |

### SELL-Only / Bounded-History Risk Penalty

Suggested deterministic mapping:

- `percentage_sell_only_lifecycles * 20`, clipped to `[0, 15]`;
- plus `min(5, oversold_bounded_history * 2.5)`.

Maximum: 20 points.

### Excessive Still-Open Share Penalty

Suggested deterministic mapping:

- `percentage_still_open_positions <= 0.50`: 0 points;
- `(0.50, 0.75]`: 5 points;
- `(0.75, 0.90]`: 10 points;
- `>0.90`: 15 points.

High still-open share means the bounded public window gives limited exit
evidence. This is a data-interpretability penalty, not a claim that holding is
bad.

### Too Few Lifecycle Positions Penalty

Suggested deterministic mapping:

- `total_lifecycle_positions < 5`: 20 points;
- `5-9`: 10 points;
- `10-14`: 5 points;
- `>=15`: 0 points.

### Excessive Concentration Penalty

Suggested deterministic mapping:

- `asset_concentration > 0.95`: 5 points;
- `outcome_concentration > 0.75`: 5 points;
- otherwise 0.

This penalty is justified only as a generality warning. It must not imply that
concentrated wallets are worse traders.

### Near-Flat Residual Ambiguity Penalty

Suggested deterministic mapping:

- near-flat share:
  `near_flat_residual_count / total_lifecycle_positions`, if denominator is
  positive;
- `near_flat_share <= 0.05`: 0 points;
- `(0.05, 0.20]`: 2 points;
- `>0.20`: 5 points.

This penalty exists because near-flat residuals may represent dust, precision
effects, or missing completion evidence, but the project has not authorized a
dust/full-exit policy.

## Missing Metric Handling

The future implementation must:

- require `wallet_id` and all allowed structural input columns to exist;
- treat missing numeric allowed inputs as validation failures unless an
  explicit fallback is documented in the validation output;
- never impute forbidden values;
- never derive PnL, ROI, Sharpe, mark-to-market, copyability, execution, or
  alpha features from available fields;
- include per-wallet `missing_required_metric_count` in the future
  `wallet_scores.csv`.

## Output Artifacts For Future Implementation

Future implementation should produce:

- `wallet_scores.csv`;
- `wallet_scores_summary.json`;
- `wallet_score_validation.json`;
- `wallet_score_report.md`.

Recommended output directory:

- `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/`

### `wallet_scores.csv` Schema

Required columns:

- `wallet_id`;
- `profile_url`;
- `wallet_score`;
- `score_band`;
- `coverage_component`;
- `fast_crypto_component`;
- `lifecycle_activity_component`;
- `event_density_component`;
- `specialization_component`;
- `bounded_history_penalty`;
- `still_open_penalty`;
- `small_sample_penalty`;
- `concentration_penalty`;
- `near_flat_ambiguity_penalty`;
- `total_lifecycle_positions`;
- `fast_crypto_lifecycle_count`;
- `fast_crypto_lifecycle_share`;
- `partial_exits`;
- `percentage_still_open_positions`;
- `percentage_sell_only_lifecycles`;
- `oversold_bounded_history`;
- `average_events_per_lifecycle`;
- `dominant_asset`;
- `asset_concentration`;
- `dominant_outcome`;
- `outcome_concentration`;
- `missing_required_metric_count`;
- `score_version`;
- `source_metrics_sha256`.

### `wallet_scores_summary.json`

Required sections:

- task name and score version;
- source metrics path and SHA-256;
- wallets scored;
- score bounds;
- score-band counts;
- forbidden-input audit result;
- validation summary;
- not-computed list.

### `wallet_score_validation.json`

Required validation gates:

- score bounds;
- deterministic ranking/order;
- no forbidden metrics used;
- missing metric handling;
- repeatable export;
- allowed input set exact match;
- component bounds;
- penalty bounds;
- output schema completeness;
- source provenance completeness.

### `wallet_score_report.md`

Required content:

- scope and non-goals;
- forbidden inputs confirmation;
- allowed input list;
- component and penalty summary;
- validation results;
- score-band distribution;
- explicit warning that scores are structural research-priority labels only.

## Validation Gates

Future implementation must pass these gates:

| Gate | Requirement |
|---|---|
| Score bounds | Every `wallet_score` is between 0 and 100 after clipping. |
| Deterministic ranking/order | Output ordering is deterministic by `wallet_score` descending, then `fast_crypto_lifecycle_share` descending, then `total_lifecycle_positions` descending, then `wallet_id` ascending. |
| No forbidden metrics used | Implementation exposes the allowed input list and fails if forbidden names are referenced. |
| Missing metric handling | Missing required structural inputs are reported and cause validation failure unless an explicitly documented non-scoring fallback is used. |
| Repeatable export | Two exports from the same input produce identical CSV SHA-256 hashes. |
| Component bounds | Each component and penalty stays within its documented bounds. |
| Output schema completeness | All required output columns/files are present. |
| Source provenance | Source metrics path and SHA-256 are recorded in all summary/report artifacts. |

## Recommended Successor Task

`Wallet Score Fixture Implementation v1`

The next task should implement the bounded score from this design using only
the existing `wallet_metrics.csv` fixture output. It should produce the four
planned output artifacts, add focused unit tests, and run the Wallet
Intelligence and full test suites. It must not launch ingestion, change metric
generation, compute PnL/ROI/Sharpe, rank wallets for trading, estimate
copyability, join expiry or mark-to-market data, connect wallets/private keys,
place orders, inspect sealed holdout outcomes, or run holdout evaluation.
