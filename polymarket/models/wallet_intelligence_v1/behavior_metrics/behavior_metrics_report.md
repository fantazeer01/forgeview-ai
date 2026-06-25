# Wallet Intelligence Behavior Metrics v1

Generated at: 2026-06-24T20:12:02+00:00

This report is derived only from existing Wallet Intelligence Data Ingestion v1 outputs. It contains no live trading, order placement, wallet/private-key handling, trade copying, capture campaign, holdout evaluation, or production model training.

## Summary

- Wallets analyzed: 6
- Strongest fast-market wallet: `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a` (100 fast crypto positions)
- Classifications: `{"fast_crypto_focused": 4, "mixed": 1, "weather_focused": 1}`
- Recommended next task: Wallet Intelligence Deep History Feasibility v1

## Wallet Metrics

### 0x1f0ebc543b2d411f66947041625c0aa1ce61cf86

- Classification: fast_crypto_focused
- Fast market share: 0.77193
- BTC/ETH/SOL Up-Down counts: 17 / 15 / 12
- YES/NO counts: 26 / 31 (balance 0.912281)
- Average/median entry: 0.510345 / 0.572583
- Cheap-side share: 0.210526
- Favorite-side share: 0.45614
- Largest visible position: 10227.2932
- Sizing concentration: 0.074746
- Repeated pattern: ETH:updown_window_unknown:9/57:0.157895
- Copyability score: 10
- Limits: first-page public snapshot only; holding time, drawdown, entry/exit linkage, late-window timing, and Binance-lag behavior unavailable

### 0x594edB9112f526Fa6A80b8F858A6379C8A2c1C11

- Classification: weather_focused
- Fast market share: 0
- BTC/ETH/SOL Up-Down counts: 0 / 0 / 0
- YES/NO counts: 65 / 34 (balance 0.686869)
- Average/median entry: 0.333585 / 0.0115
- Cheap-side share: 0.63
- Favorite-side share: 0.33
- Largest visible position: 28034.57
- Sizing concentration: 0.077774
- Repeated pattern: OTHER:other_timeframe:100/100:1
- Copyability score: 0
- Limits: first-page public snapshot only; holding time, drawdown, entry/exit linkage, late-window timing, and Binance-lag behavior unavailable

### 0x63ce342161250d705dc0b16df89036c8e5f9ba9a

- Classification: fast_crypto_focused
- Fast market share: 0.9
- BTC/ETH/SOL Up-Down counts: 21 / 20 / 4
- YES/NO counts: 24 / 26 (balance 0.96)
- Average/median entry: 0.43435 / 0.420023
- Cheap-side share: 0.08
- Favorite-side share: 0.22
- Largest visible position: 175204.817091
- Sizing concentration: 0.678923
- Repeated pattern: ETH:5m:16/50:0.32
- Copyability score: 5
- Limits: first-page public snapshot only; holding time, drawdown, entry/exit linkage, late-window timing, and Binance-lag behavior unavailable

### 0xd0d6053c3c37e727402d84c14069780d360993aa

- Classification: fast_crypto_focused
- Fast market share: 0.716981
- BTC/ETH/SOL Up-Down counts: 21 / 8 / 9
- YES/NO counts: 24 / 29 (balance 0.90566)
- Average/median entry: 0.492986 / 0.51
- Cheap-side share: 0.018868
- Favorite-side share: 0.245283
- Largest visible position: 10461.924697
- Sizing concentration: 0.16663
- Repeated pattern: OTHER:5m:13/53:0.245283
- Copyability score: 5
- Limits: first-page public snapshot only; holding time, drawdown, entry/exit linkage, late-window timing, and Binance-lag behavior unavailable

### 0xde17f7144fbd0eddb2679132c10ff5e74b120988

- Classification: mixed
- Fast market share: 0
- BTC/ETH/SOL Up-Down counts: 0 / 0 / 0
- YES/NO counts: 48 / 52 (balance 0.96)
- Average/median entry: 0.407346 / 0.314591
- Cheap-side share: 0.41
- Favorite-side share: 0.32
- Largest visible position: 148040.0069
- Sizing concentration: 0.068329
- Repeated pattern: BTC:other_timeframe:100/100:1
- Copyability score: 5
- Limits: first-page public snapshot only; holding time, drawdown, entry/exit linkage, late-window timing, and Binance-lag behavior unavailable

### 0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a

- Classification: fast_crypto_focused
- Fast market share: 1
- BTC/ETH/SOL Up-Down counts: 100 / 0 / 0
- YES/NO counts: 47 / 53 (balance 0.94)
- Average/median entry: 0.632224 / 0.79516
- Cheap-side share: 0.18
- Favorite-side share: 0.55
- Largest visible position: 479.934414
- Sizing concentration: 0.031279
- Repeated pattern: BTC:15m:52/100:0.52
- Copyability score: 10
- Limits: first-page public snapshot only; holding time, drawdown, entry/exit linkage, late-window timing, and Binance-lag behavior unavailable

## Common Patterns

- 4 wallets are fast-crypto focused.
- Primary clusters: {'fast_crypto_directional': 4, 'cheap_side_buyer': 2}.
- 3 wallets show repeated cheap-side buying at >=20% of visible entries.
- Repeated late-window behavior remains unavailable from this snapshot.

## Copyability Risks

- All scores are research-only and capped because public snapshots lack full trade/fill history.
- Likely delay risk is high for fast crypto wallets because entry windows can be short.
- Liquidity/fill uncertainty is material where visible position sizes are large or concentrated.
- Unknown exit timing prevents claims about hold-to-resolution versus exit-before-expiry.
