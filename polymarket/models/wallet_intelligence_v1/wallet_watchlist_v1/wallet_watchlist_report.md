# Wallet Watchlist v1

Generated: 2026-06-25T21:23:58+00:00

## Scope

This is a monitoring/research artifact. It is not a trading signal, not a copy-trading recommendation, and not a profitability ranking. It is based only on bounded public history and existing Wallet Score outputs.

## Source

- Source scores CSV: `polymarket\models\wallet_intelligence_v1\wallet_score_fixture\wallet_scores.csv`
- Source scores SHA-256: `52ceafde32dc6e6c4d07829e824a83c9b767bc7da4d1b3461188e6cda2e3b2ad`
- Wallets input: 6
- Wallets included: 6
- Wallets excluded: 0

## Priority Bucket Counts

- `insufficient_visible_structure`: 2
- `low_priority`: 3
- `medium_priority`: 1

## Watchlist Rows

- `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`: score=73, bucket=medium_priority, reasons=bucket_medium_priority;minimum_visibility_passed;fast_crypto_relevant;visible_partial_exit_activity;concentration_risk;near_flat_residual_ambiguity
- `0x63ce342161250d705dc0b16df89036c8e5f9ba9a`: score=42.14285714285714285714285714, bucket=low_priority, reasons=bucket_low_priority;minimum_visibility_passed;fast_crypto_relevant;visible_partial_exit_activity;small_visible_sample;near_flat_residual_ambiguity
- `0xd0d6053c3c37e727402d84c14069780d360993aa`: score=32, bucket=low_priority, reasons=bucket_low_priority;minimum_visibility_passed;fast_crypto_relevant;visible_partial_exit_activity;bounded_history_artifact_risk;small_visible_sample
- `0x1f0ebc543b2d411f66947041625c0aa1ce61cf86`: score=26, bucket=low_priority, reasons=bucket_low_priority;minimum_visibility_passed;fast_crypto_relevant;all_or_mostly_open_visibility;small_visible_sample
- `0x594edb9112f526fa6a80b8f858a6379c8a2c1c11`: score=13, bucket=insufficient_visible_structure, reasons=bucket_insufficient_visible_structure;minimum_visibility_passed;no_fast_crypto_visibility;all_or_mostly_open_visibility;concentration_risk
- `0xde17f7144fbd0eddb2679132c10ff5e74b120988`: score=6, bucket=insufficient_visible_structure, reasons=bucket_insufficient_visible_structure;minimum_visibility_passed;no_fast_crypto_visibility;all_or_mostly_open_visibility;concentration_risk;small_visible_sample

## Validation

- `deterministic_ordering`: true
- `output_schema_completeness`: true
- `reason_codes_present`: true
- `research_actions_present`: true
- `no_forbidden_metric_fields`: true
- `forbidden_metric_fields`: []
- `no_forbidden_claims`: true
- `forbidden_claim_phrases`: []
- `all_validation_passed`: true
- `repeatable_export`: true

## Explicit Non-Claims

- No profitability claims.
- No alpha claims.
- No PnL, ROI, or Sharpe metrics.
- No copy-trading recommendation.
- No mark-to-market values.
- No trading recommendation.

## Recommended Next Task

`Wallet Watchlist Review v1`
