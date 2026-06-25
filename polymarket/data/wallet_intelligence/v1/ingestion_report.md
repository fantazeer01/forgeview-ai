# Wallet Intelligence Data Ingestion v1

Retrieved at: 2026-06-24T20:00:17+00:00

This report uses public Polymarket profile/data endpoints only. It contains no wallet/private-key, order-placement, live-trading, trade-copying, holdout-evaluation, or capture-campaign capability.

## Summary

- Wallets attempted: 6
- Wallets resolved to public addresses: 6
- Wallets with visible positions: 6
- Normalized position rows: 460
- Fast-market crypto wallets: 0x63ce342161250d705dc0b16df89036c8e5f9ba9a, 0x1f0ebc543b2d411f66947041625c0aa1ce61cf86, 0xd0d6053c3c37e727402d84c14069780d360993aa, 0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a
- Weather/other wallets: 0x594edB9112f526Fa6A80b8F858A6379C8A2c1C11
- Enough visible data for strategy inference: 0x63ce342161250d705dc0b16df89036c8e5f9ba9a, 0xde17f7144fbd0eddb2679132c10ff5e74b120988, 0x1f0ebc543b2d411f66947041625c0aa1ce61cf86, 0xd0d6053c3c37e727402d84c14069780d360993aa, 0x594edB9112f526Fa6A80b8F858A6379C8A2c1C11, 0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a
- Research-only copyable wallets: 0x63ce342161250d705dc0b16df89036c8e5f9ba9a, 0x1f0ebc543b2d411f66947041625c0aa1ce61cf86, 0xd0d6053c3c37e727402d84c14069780d360993aa, 0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a

## Data Availability By Wallet

### 0x63ce342161250d705dc0b16df89036c8e5f9ba9a

- Profile URL: https://polymarket.com/0x63ce342161250d705dc0b16df89036c8e5f9ba9a
- Resolved wallet address: 0x63ce342161250d705dc0b16df89036c8e5f9ba9a
- Active positions: 0
- Closed positions: 50
- Fast crypto positions: 45
- Market types: `{"fast_crypto": 45, "other": 5}`
- Copyability score: 35
- Notes: wallet_resolution=seed_wallet_id; average_holding_time and drawdown unavailable from positions/closed-positions snapshots; late-entry behavior requires deeper trade/activity history; closed_positions may be truncated at public snapshot limit 50

### 0xde17f7144fbd0eddb2679132c10ff5e74b120988

- Profile URL: https://polymarket.com/0xde17f7144fbd0eddb2679132c10ff5e74b120988
- Resolved wallet address: 0xde17f7144fbd0eddb2679132c10ff5e74b120988
- Active positions: 50
- Closed positions: 50
- Fast crypto positions: 0
- Market types: `{"crypto_other": 100}`
- Copyability score: 5
- Notes: wallet_resolution=seed_wallet_id; average_holding_time and drawdown unavailable from positions/closed-positions snapshots; late-entry behavior requires deeper trade/activity history; closed_positions may be truncated at public snapshot limit 50

### 0x1f0ebc543b2d411f66947041625c0aa1ce61cf86

- Profile URL: https://polymarket.com/0x1f0ebc543b2d411f66947041625c0aa1ce61cf86
- Resolved wallet address: 0x1f0ebc543b2d411f66947041625c0aa1ce61cf86
- Active positions: 7
- Closed positions: 50
- Fast crypto positions: 44
- Market types: `{"fast_crypto": 44, "other": 13}`
- Copyability score: 35
- Notes: wallet_resolution=seed_wallet_id; average_holding_time and drawdown unavailable from positions/closed-positions snapshots; late-entry behavior requires deeper trade/activity history; closed_positions may be truncated at public snapshot limit 50

### 0xd0d6053c3c37e727402d84c14069780d360993aa

- Profile URL: https://polymarket.com/@k9Q2mX4L8A7ZP3R
- Resolved wallet address: 0xd0d6053c3c37e727402d84c14069780d360993aa
- Active positions: 3
- Closed positions: 50
- Fast crypto positions: 38
- Market types: `{"fast_crypto": 38, "other": 15}`
- Copyability score: 35
- Notes: wallet_resolution=profile_page_embedded_address; average_holding_time and drawdown unavailable from positions/closed-positions snapshots; late-entry behavior requires deeper trade/activity history; closed_positions may be truncated at public snapshot limit 50

### 0x594edB9112f526Fa6A80b8F858A6379C8A2c1C11

- Profile URL: https://polymarket.com/@0x594edB9112f526Fa6A80b8F858A6379C8A2c1C11
- Resolved wallet address: 0x594edB9112f526Fa6A80b8F858A6379C8A2c1C11
- Active positions: 50
- Closed positions: 50
- Fast crypto positions: 0
- Market types: `{"other": 12, "weather": 88}`
- Copyability score: 15
- Notes: wallet_resolution=seed_wallet_id; average_holding_time and drawdown unavailable from positions/closed-positions snapshots; late-entry behavior requires deeper trade/activity history; closed_positions may be truncated at public snapshot limit 50

### 0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a

- Profile URL: https://polymarket.com/0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a
- Resolved wallet address: 0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a
- Active positions: 50
- Closed positions: 50
- Fast crypto positions: 100
- Market types: `{"fast_crypto": 100}`
- Copyability score: 35
- Notes: wallet_resolution=seed_wallet_id; average_holding_time and drawdown unavailable from positions/closed-positions snapshots; late-entry behavior requires deeper trade/activity history; closed_positions may be truncated at public snapshot limit 50

## Biggest Data Gaps

- Full trade/fill history is not captured by first-page public profile snapshots.
- Average holding time is unavailable without linked entry and exit timestamps.
- Late-entry and Binance-lag behavior require timestamped trade history plus external price series.
- Copyability cannot be treated as executable because observation delay, liquidity, and fill priority are unknown.

## Recommended Next Task

Wallet Intelligence Behavior Metrics v1
