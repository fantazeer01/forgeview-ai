# Wallet Lifecycle Metrics v1

Generated: 2026-06-25T20:48:58+00:00

## Scope

Metrics are computed from existing lifecycle positions only. No PnL, ROI, Sharpe, copyability, wallet scoring, wallet ranking, mark-to-market values, expiry joins, reference alignment, queue modelling, order placement, wallet/private-key use, holdout inspection, or holdout evaluation was added.

## Aggregate

- Wallets analyzed: 6
- Lifecycle positions: 112
- BUY trades visible: 543
- SELL trades visible: 57
- Near-flat residual threshold: 0.1 shares
- Near-flat residual count: 10

## Status Counts

- `oversold_bounded_history`: 2
- `partial_exit`: 36
- `still_open`: 74

## Wallet Rows

- `0x1f0ebc543b2d411f66947041625c0aa1ce61cf86`: positions=6, still_open=6, partial=0, full=0, oversold=0
- `0x594edb9112f526fa6a80b8f858a6379c8a2c1c11`: positions=23, still_open=23, partial=0, full=0, oversold=0
- `0x63ce342161250d705dc0b16df89036c8e5f9ba9a`: positions=7, still_open=5, partial=2, full=0, oversold=0
- `0xd0d6053c3c37e727402d84c14069780d360993aa`: positions=8, still_open=5, partial=1, full=0, oversold=2
- `0xde17f7144fbd0eddb2679132c10ff5e74b120988`: positions=11, still_open=11, partial=0, full=0, oversold=0
- `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`: positions=57, still_open=24, partial=33, full=0, oversold=0

## Validation

- `wallet_coverage`: true
- `input_position_count_matches`: true
- `status_count_conservation`: true
- `buy_trade_count_matches`: true
- `sell_trade_count_matches`: true
- `share_fields_in_range`: true
- `decimal_metric_fields_parse`: true
- `forbidden_metric_fields_absent`: true
- `forbidden_metric_fields`: []
- `deterministic_wallet_ordering`: true
- `all_validation_passed`: true
- `deterministic_csv_repeat_export`: true

## Recommended Next Task

`Wallet Lifecycle Metrics Review v1`
