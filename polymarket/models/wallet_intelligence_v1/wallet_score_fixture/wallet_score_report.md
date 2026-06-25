# Wallet Score Fixture Implementation v1

Generated: 2026-06-25T21:05:01+00:00

## Scope

Wallet scores are bounded structural research-priority labels only. They do not indicate profitability, alpha, ROI, PnL, Sharpe, execution quality, copyability, or trading suitability.

## Source

- Source metrics CSV: `polymarket\models\wallet_intelligence_v1\lifecycle_metrics\wallet_metrics.csv`
- Source metrics SHA-256: `62cd5e79b1388dedb899b8c48da2f48526c880f3ac3b2332e2b2c6f1961deff3`
- Wallets scored: 6

## Forbidden Inputs Confirmed

- `pnl`
- `roi`
- `realized_profit`
- `realized_pnl`
- `sharpe`
- `execution_quality`
- `copyability`
- `alpha`
- `mark_to_market`
- `wallet_ranking`
- `final_resolved_win_loss`
- `sealed_holdout`
- `private_wallet`
- `order_placement`
- `authenticated_trading`

## Allowed Score Inputs

- `total_lifecycle_positions`
- `fast_crypto_lifecycle_count`
- `fast_crypto_lifecycle_share`
- `partial_exits`
- `percentage_still_open_positions`
- `percentage_sell_only_lifecycles`
- `oversold_bounded_history`
- `average_buy_count_per_lifecycle`
- `average_sell_count_per_lifecycle`
- `average_events_per_lifecycle`
- `near_flat_residual_count`
- `dominant_asset`
- `asset_concentration`
- `dominant_outcome`
- `outcome_concentration`

## Score Band Distribution

- `insufficient_visible_structure`: 2
- `low_priority`: 3
- `medium_priority`: 1

## Component And Penalty Summary

- Positive components: coverage, fast-crypto relevance, lifecycle activity, event-density consistency, and specialization.
- Penalties: SELL-only/bounded-history risk, excessive still-open share, small visible sample, excessive concentration, and near-flat residual ambiguity.

## Wallet Score Rows

- `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`: score=73, band=medium_priority, positions=57, fast_crypto_share=1
- `0x63ce342161250d705dc0b16df89036c8e5f9ba9a`: score=42.14285714285714285714285714, band=low_priority, positions=7, fast_crypto_share=0.8571428571428571428571428571
- `0xd0d6053c3c37e727402d84c14069780d360993aa`: score=32, band=low_priority, positions=8, fast_crypto_share=0.75
- `0x1f0ebc543b2d411f66947041625c0aa1ce61cf86`: score=26, band=low_priority, positions=6, fast_crypto_share=1
- `0x594edb9112f526fa6a80b8f858a6379c8a2c1c11`: score=13, band=insufficient_visible_structure, positions=23, fast_crypto_share=0
- `0xde17f7144fbd0eddb2679132c10ff5e74b120988`: score=6, band=insufficient_visible_structure, positions=11, fast_crypto_share=0

## Validation

- `score_bounds`: true
- `deterministic_score_calculation`: true
- `deterministic_ordering`: true
- `no_forbidden_metrics_used`: true
- `forbidden_inputs_used`: []
- `missing_metric_handling`: true
- `missing_source_fields`: []
- `allowed_input_set_exact_match`: true
- `component_bounds`: true
- `penalty_bounds`: true
- `output_schema_completeness`: true
- `source_provenance_completeness`: true
- `all_validation_passed`: true
- `repeatable_export`: true

## Recommended Next Task

`Wallet Score Fixture Review v1`
