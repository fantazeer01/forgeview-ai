# Wallet Metrics Readiness Review v1

Generated: 2026-06-25

## Scope

This review evaluates the currently available Wallet Intelligence lifecycle
metrics for readiness to support a first Wallet Score design. It does not add
new metrics, implement scoring, infer PnL, rank wallets, estimate copyability,
join expiry data, join mark-to-market prices, align Binance/reference data, or
expand public ingestion.

Reviewed inputs:

- `polymarket/models/wallet_intelligence_v1/lifecycle_metrics/wallet_metrics.csv`
- `polymarket/models/wallet_intelligence_v1/lifecycle_metrics/wallet_metrics_summary.json`
- `polymarket/models/wallet_intelligence_v1/lifecycle_metrics/wallet_metrics_report.md`
- `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture/lifecycle_positions.csv`

## Executive Finding

The current outputs are sufficient to design Wallet Score v1 as a bounded
structural readiness score only. They can support coverage, fast-crypto focus,
visible lifecycle behavior, exit-activity structure, bounded-history risk, and
asset/outcome concentration. They are not sufficient for performance scoring,
profitability scoring, copyability scoring, execution-quality scoring, or
claims about durable wallet skill.

The first Wallet Score design should therefore use current metrics as
descriptive inputs and explicit data-quality gates. It should not treat the
score as alpha, ROI, copy-trading suitability, or execution guidance.

## Current Metrics Reviewed

Aggregate state from the latest metrics run:

- wallets analyzed: 6;
- lifecycle positions analyzed: 112;
- still-open candidates: 74;
- partial-exit candidates: 36;
- full-exit candidates: 0;
- bounded-history oversold candidates: 2;
- visible BUY / SELL trade counts: 543 / 57;
- SELL-only lifecycles: 2;
- near-flat residual groups: 10 at the documented 0.1-share review-only
  threshold;
- validation gates: passed;
- deterministic CSV repeat export: passed.

## Metric Readiness Matrix

| Metric | Classification | Wallet Score Design Use |
|---|---|---|
| `wallet_id` | Not useful | Identifier only; use for grouping, not score value. |
| `profile_url` | Not useful | Provenance/inspection metadata only. |
| `total_lifecycle_positions` | Ready for Wallet Score | Minimum coverage and sample-size gate. |
| `still_open_positions` | Ready for Wallet Score | Structural status count; bounded-window caveat required. |
| `partial_exits` | Ready for Wallet Score | Visible exit-activity signal. |
| `full_exits` | Needs additional data | Current exact-count metric is measurable, but the zero count should not be interpreted until deeper history, expiry, or redemption context exists. |
| `oversold_bounded_history` | Ready for Wallet Score | Data-completeness risk and bounded-history warning. |
| `average_position_size` | Useful later | Visible share-size proxy; avoid score weight until normalization and completeness policy are designed. |
| `median_position_size` | Useful later | More robust visible size proxy; useful after score normalization design. |
| `average_buy_count_per_lifecycle` | Ready for Wallet Score | Structural activity intensity signal. |
| `average_sell_count_per_lifecycle` | Ready for Wallet Score | Structural exit-activity signal. |
| `average_events_per_lifecycle` | Ready for Wallet Score | Lifecycle complexity / activity density signal. |
| `percentage_still_open_positions` | Ready for Wallet Score | Bounded-window status share; use with explicit limitation. |
| `percentage_sell_only_lifecycles` | Ready for Wallet Score | Bounded-history gap risk and missing-prior-buy warning. |
| `buy_trade_count` | Ready for Wallet Score | Activity coverage input. |
| `sell_trade_count` | Ready for Wallet Score | Exit-activity coverage input. |
| `total_visible_bought_size` | Useful later | Raw visible size exposure; do not use directly without scale normalization. |
| `total_visible_sold_size` | Useful later | Raw visible exit size; do not use directly without scale normalization. |
| `remaining_visible_size` | Useful later | Residual visible size proxy; requires bounded-history caveat. |
| `oversold_visible_size` | Useful later | Magnitude of bounded-history oversold gaps; useful as risk context after normalization. |
| `near_flat_residual_count` | Ready for Wallet Score | Structural review signal for possible near-closure behavior; must remain separate from full-exit policy. |
| `fast_crypto_lifecycle_count` | Ready for Wallet Score | Fast-market coverage input. |
| `fast_crypto_lifecycle_share` | Ready for Wallet Score | Core focus signal for BTC/ETH/SOL Up/Down relevance. |
| `dominant_asset` | Ready for Wallet Score | Focus descriptor; categorical input, not quality by itself. |
| `asset_concentration` | Ready for Wallet Score | Specialization/diversification signal. |
| `dominant_outcome` | Ready for Wallet Score | Side/outcome preference descriptor. |
| `outcome_concentration` | Ready for Wallet Score | Outcome concentration signal. |

## Currently Measurable

The current lifecycle outputs can measure only bounded structural behavior:

- lifecycle candidate counts by wallet;
- visible status counts: still-open, partial-exit, full-exit exact match, and
  bounded-history oversold;
- BUY/SELL event counts and per-lifecycle event density;
- SELL-only lifecycle share;
- near-flat residual group count under the review-only 0.1-share threshold;
- fast BTC/ETH/SOL Up/Down lifecycle count and share;
- dominant asset, asset concentration, dominant outcome, and outcome
  concentration;
- visible raw size summaries, with the limitation that they are not PnL,
  not notional edge, and not complete wallet exposure.

## Measurable After Expiry Joins

Expiry and market metadata joins would unlock:

- time-to-expiry at entry and exit;
- expiry-window buckets;
- held-to-expiry versus exited-before-expiry evidence;
- resolved/won/lost outcome context;
- better distinction between true still-open positions and positions closed
  outside the bounded activity window;
- full-exit or resolution/REDEEM context that the current public smoke window
  cannot infer.

## Measurable After Mark-to-Market

Mark-to-market joins would unlock:

- unrealized position value;
- realized and unrealized PnL candidates;
- drawdown and adverse excursion;
- position-value concentration;
- volatility of visible wallet exposure;
- ROI-like or risk-adjusted metrics, if later authorized and validated.

## Measurable After Copyability Modelling

Copyability modelling would require separate design and data:

- observation delay from public activity availability;
- market liquidity and fill uncertainty at the copied timestamp;
- likely slippage;
- queue/fill priority risk;
- degradation from delayed entry;
- exit timing uncertainty;
- a copyability score or penalty model.

None of these are currently supported by lifecycle metrics alone.

## Missing Capabilities Before Wallet Score

Wallet Score Design v1 can proceed, but only if it stays structural. The
following capabilities are missing before any performance or copyability score
can be implemented:

- expiry and resolution joins;
- deeper trade-history coverage beyond the bounded one-page smoke;
- deterministic treatment for redemptions, dust, and near-flat residuals;
- mark-to-market price reconstruction;
- reference-price alignment for Binance-lag analysis;
- liquidity/fill/slippage modelling;
- copyability-delay measurement;
- missing-data and wallet-coverage policy;
- score normalization and monotonicity policy;
- explicit policy for excluding identifiers and profile URLs from score
  computation.

## Minimum Metric Set For Wallet Score Design v1

The minimum current metric set recommended for Wallet Score Design v1 is:

- `total_lifecycle_positions`;
- `fast_crypto_lifecycle_share`;
- `fast_crypto_lifecycle_count`;
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

These inputs support a descriptive structural score design around coverage,
fast-market relevance, visible lifecycle activity, and bounded-data risk. Raw
size fields should be deferred or used only as non-scoring descriptors until a
normalization policy is reviewed.

## Recommended Successor Task

`Wallet Score Design v1`

The next task should design, but not implement, the first structural Wallet
Score specification. It should define score objectives, allowed inputs,
excluded inputs, missing-data policy, normalization rules, data-quality gates,
output schema, and validation criteria using only readiness-approved lifecycle
metrics. It must not implement scoring, rank wallets, compute PnL/ROI/Sharpe,
estimate copyability, add mark-to-market joins, add expiry joins, launch
ingestion, connect wallets/private keys, place orders, inspect sealed holdout
outcomes, or run holdout evaluation.
