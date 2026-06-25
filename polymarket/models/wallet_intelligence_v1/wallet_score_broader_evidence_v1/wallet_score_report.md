# Wallet Score Fixture Implementation v1

Generated: 2026-06-25T21:41:10+00:00

## Scope

Wallet scores are bounded structural research-priority labels only. They do not indicate profitability, alpha, ROI, PnL, Sharpe, execution quality, copyability, or trading suitability.

## Source

- Source metrics CSV: `polymarket\models\wallet_intelligence_v1\lifecycle_metrics_broader_v1\wallet_metrics.csv`
- Source metrics SHA-256: `931a9f316fab5ab15f07d8b8a61adae5b7d19dd5b8e74fe247573af8f99fb964`
- Wallets scored: 30

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

- `high_priority`: 3
- `insufficient_visible_structure`: 2
- `low_priority`: 12
- `medium_priority`: 13

## Component And Penalty Summary

- Positive components: coverage, fast-crypto relevance, lifecycle activity, event-density consistency, and specialization.
- Penalties: SELL-only/bounded-history risk, excessive still-open share, small visible sample, excessive concentration, and near-flat residual ambiguity.

## Wallet Score Rows

- `0x4228048ea2f8f571ff2777cc32baee584c5134cb`: score=85.8974358974358974358974359, band=high_priority, positions=78, fast_crypto_share=0.7948717948717948717948717949
- `0x4a0b6dacb223f1126080048826f0271dbe31ff39`: score=84.2, band=high_priority, positions=50, fast_crypto_share=0.96
- `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`: score=75, band=high_priority, positions=89, fast_crypto_share=1
- `0x1cc53dd33c49d0a222c61ebfd2f24ba48802b199`: score=73.83333333333333333333333334, band=medium_priority, positions=60, fast_crypto_share=0.9833333333333333333333333333
- `0x3c6afcbc144b6bb110dbf8538bde2781c24a8a58`: score=69.5, band=medium_priority, positions=44, fast_crypto_share=1
- `0x4bfb3f47ad1a0b494ecaa3c1a9bfba22a4c39f3a`: score=67.31818181818181818181818182, band=medium_priority, positions=110, fast_crypto_share=1
- `0x1a39c44c2bc6b23cc715a197cc0d76574ab51bb6`: score=66, band=medium_priority, positions=132, fast_crypto_share=1
- `0x088df3b7e5c1b5c2d4b7dc760863153480cf025e`: score=63.13636363636363636363636363, band=medium_priority, positions=88, fast_crypto_share=0.6136363636363636363636363636
- `0x2e554602dbe0d9549fd5a356892f3f7ddb28c549`: score=61.85950413223140495867768595, band=medium_priority, positions=121, fast_crypto_share=0.8429752066115702479338842975
- `0x20d2309cd92b797ae7ca175ed828ed8a27fbe29d`: score=59.33333333333333333333333334, band=medium_priority, positions=21, fast_crypto_share=0.7619047619047619047619047619
- `0x54afeb88e709fbfb7e75a1ab8275ed4f0b333130`: score=59, band=medium_priority, positions=83, fast_crypto_share=1
- `0x29a55c2bf8efd1029c001477b34be47d3ca37752`: score=56.1875, band=medium_priority, positions=64, fast_crypto_share=0.890625
- `0x0e0d60ea727cb7a569ea391263cc10952d1e6e5b`: score=52, band=medium_priority, positions=60, fast_crypto_share=1
- `0x1a561cdee16a7a263231aacc9ee50447ea6cf475`: score=52, band=medium_priority, positions=54, fast_crypto_share=1
- `0x11e7740bc4f6f16f4c56bcdc8abda23f0863d3c2`: score=52, band=medium_priority, positions=53, fast_crypto_share=1
- `0x47d7dfd8b93e656d44ed173c848203e05982113a`: score=52, band=medium_priority, positions=51, fast_crypto_share=1
- `0xd0d6053c3c37e727402d84c14069780d360993aa`: score=48.3076923076923076923076923, band=low_priority, positions=13, fast_crypto_share=0.8461538461538461538461538462
- `0x01b739b360d3c2f6cc8ec84cda900d48650e2eca`: score=48, band=low_priority, positions=27, fast_crypto_share=1
- `0x4d0730b1c8b4da2444ab7a4a389a607584132b94`: score=46.2368421052631578947368421, band=low_priority, positions=152, fast_crypto_share=0.4934210526315789473684210526
- `0x25f4707c93e4bfdf26cd6c5cc46c5464691cf88e`: score=46.2, band=low_priority, positions=25, fast_crypto_share=0.96
- `0x59e9593d9ad358947577a51f2c2d32b49cff2f9d`: score=45, band=low_priority, positions=132, fast_crypto_share=1
- `0x251c1a283703beed41590b0875a8dcb8ddd1541f`: score=45, band=low_priority, positions=23, fast_crypto_share=1
- `0x3b19d4c9e38af6e6d6923039275d5cfe89bc3655`: score=44.63302752293577981651376147, band=low_priority, positions=109, fast_crypto_share=0.9816513761467889908256880734
- `0x2c3ef176341ced9b0c5456d355d58fc0832e282d`: score=38, band=low_priority, positions=200, fast_crypto_share=1
- `0x60ca7ed001bb8496c50fde95329f6a8fa756f86e`: score=37.63157894736842105263157895, band=low_priority, positions=190, fast_crypto_share=0.4315789473684210526315789474
- `0x63ce342161250d705dc0b16df89036c8e5f9ba9a`: score=37.14285714285714285714285714, band=low_priority, positions=7, fast_crypto_share=0.8571428571428571428571428571
- `0x4af813b3fc6038c55d06ce21531e9dceab093b6d`: score=37, band=low_priority, positions=16, fast_crypto_share=1
- `0x1f0ebc543b2d411f66947041625c0aa1ce61cf86`: score=33.14285714285714285714285714, band=low_priority, positions=14, fast_crypto_share=0.8571428571428571428571428571
- `0xde17f7144fbd0eddb2679132c10ff5e74b120988`: score=23, band=insufficient_visible_structure, positions=30, fast_crypto_share=0
- `0x594edb9112f526fa6a80b8f858a6379c8a2c1c11`: score=19, band=insufficient_visible_structure, positions=39, fast_crypto_share=0

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
