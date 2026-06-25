# Wallet Lifecycle Metrics v1

Generated: 2026-06-25T21:41:10+00:00

## Scope

Metrics are computed from existing lifecycle positions only. No PnL, ROI, Sharpe, copyability, wallet scoring, wallet ranking, mark-to-market values, expiry joins, reference alignment, queue modelling, order placement, wallet/private-key use, holdout inspection, or holdout evaluation was added.

## Aggregate

- Wallets analyzed: 30
- Lifecycle positions: 2135
- BUY trades visible: 5063
- SELL trades visible: 702
- Near-flat residual threshold: 0.1 shares
- Near-flat residual count: 125

## Status Counts

- `full_exit`: 80
- `oversold_bounded_history`: 24
- `partial_exit`: 296
- `still_open`: 1735

## Wallet Rows

- `0x01b739b360d3c2f6cc8ec84cda900d48650e2eca`: positions=27, still_open=27, partial=0, full=0, oversold=0
- `0x088df3b7e5c1b5c2d4b7dc760863153480cf025e`: positions=88, still_open=65, partial=17, full=1, oversold=5
- `0x0e0d60ea727cb7a569ea391263cc10952d1e6e5b`: positions=60, still_open=60, partial=0, full=0, oversold=0
- `0x11e7740bc4f6f16f4c56bcdc8abda23f0863d3c2`: positions=53, still_open=53, partial=0, full=0, oversold=0
- `0x1a39c44c2bc6b23cc715a197cc0d76574ab51bb6`: positions=132, still_open=98, partial=31, full=3, oversold=0
- `0x1a561cdee16a7a263231aacc9ee50447ea6cf475`: positions=54, still_open=54, partial=0, full=0, oversold=0
- `0x1cc53dd33c49d0a222c61ebfd2f24ba48802b199`: positions=60, still_open=14, partial=42, full=3, oversold=1
- `0x1f0ebc543b2d411f66947041625c0aa1ce61cf86`: positions=14, still_open=14, partial=0, full=0, oversold=0
- `0x20d2309cd92b797ae7ca175ed828ed8a27fbe29d`: positions=21, still_open=3, partial=10, full=0, oversold=8
- `0x251c1a283703beed41590b0875a8dcb8ddd1541f`: positions=23, still_open=23, partial=0, full=0, oversold=0
- `0x25f4707c93e4bfdf26cd6c5cc46c5464691cf88e`: positions=25, still_open=25, partial=0, full=0, oversold=0
- `0x29a55c2bf8efd1029c001477b34be47d3ca37752`: positions=64, still_open=54, partial=3, full=3, oversold=4
- `0x2c3ef176341ced9b0c5456d355d58fc0832e282d`: positions=200, still_open=200, partial=0, full=0, oversold=0
- `0x2e554602dbe0d9549fd5a356892f3f7ddb28c549`: positions=121, still_open=92, partial=10, full=19, oversold=0
- `0x3b19d4c9e38af6e6d6923039275d5cfe89bc3655`: positions=109, still_open=109, partial=0, full=0, oversold=0
- `0x3c6afcbc144b6bb110dbf8538bde2781c24a8a58`: positions=44, still_open=9, partial=12, full=22, oversold=1
- `0x4228048ea2f8f571ff2777cc32baee584c5134cb`: positions=78, still_open=29, partial=34, full=15, oversold=0
- `0x47d7dfd8b93e656d44ed173c848203e05982113a`: positions=51, still_open=51, partial=0, full=0, oversold=0
- `0x4a0b6dacb223f1126080048826f0271dbe31ff39`: positions=50, still_open=20, partial=30, full=0, oversold=0
- `0x4af813b3fc6038c55d06ce21531e9dceab093b6d`: positions=16, still_open=16, partial=0, full=0, oversold=0
- `0x4bfb3f47ad1a0b494ecaa3c1a9bfba22a4c39f3a`: positions=110, still_open=50, partial=47, full=12, oversold=1
- `0x4d0730b1c8b4da2444ab7a4a389a607584132b94`: positions=152, still_open=136, partial=13, full=2, oversold=1
- `0x54afeb88e709fbfb7e75a1ab8275ed4f0b333130`: positions=83, still_open=81, partial=2, full=0, oversold=0
- `0x594edb9112f526fa6a80b8f858a6379c8a2c1c11`: positions=39, still_open=39, partial=0, full=0, oversold=0
- `0x59e9593d9ad358947577a51f2c2d32b49cff2f9d`: positions=132, still_open=132, partial=0, full=0, oversold=0
- `0x60ca7ed001bb8496c50fde95329f6a8fa756f86e`: positions=190, still_open=190, partial=0, full=0, oversold=0
- `0x63ce342161250d705dc0b16df89036c8e5f9ba9a`: positions=7, still_open=5, partial=2, full=0, oversold=0
- `0xd0d6053c3c37e727402d84c14069780d360993aa`: positions=13, still_open=8, partial=2, full=0, oversold=3
- `0xde17f7144fbd0eddb2679132c10ff5e74b120988`: positions=30, still_open=30, partial=0, full=0, oversold=0
- `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`: positions=89, still_open=48, partial=41, full=0, oversold=0

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
