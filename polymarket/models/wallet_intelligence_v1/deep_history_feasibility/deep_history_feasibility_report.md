# Wallet Intelligence Deep History Feasibility v1

Generated: 2026-06-24T20:26:14.816094+00:00

## Executive conclusion

Deeper public wallet history is feasible for bounded research, but only as a public activity/trade timeline plus joins. It is not enough to reconstruct a complete private strategy or safely infer copyability. The safest first path is the public Data API activity endpoint filtered to `type=TRADE`, cross-checked against the Data API trades endpoint and aggregate positions/closed positions.

## Best endpoint path

- Primary: `GET https://data-api.polymarket.com/activity?user=<wallet>&type=TRADE&limit<=500&offset=<offset>`
- Cross-check: `GET https://data-api.polymarket.com/trades?user=<wallet>&limit<=500&offset=<offset>`
- Joins: `/positions`, `/closed-positions`, CLOB `/prices-history`, and external BTC/ETH/SOL reference prices for Binance-lag analysis.

## Bounded probe

- Wallet: `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`
- Rows returned: 50
- Type counts: {'TRADE': 50}
- Side counts: {'SELL': 21, 'BUY': 29}
- Unique markets/slugs: 27
- Fields observed: `asset, bio, conditionId, eventSlug, icon, name, outcome, outcomeIndex, price, profileImage, profileImageOptimized, proxyWallet, pseudonym, side, size, slug, timestamp, title, transactionHash, type, usdcSize`

## Endpoint feasibility summary

- **Data API activity**: activity timeline feasible with bounded pagination. entry timestamp/price/side/size feasible for trade rows; exit and holding time partial after lifecycle linking
- **Data API trades**: trade/fill timeline likely feasible; takerOnly defaults require explicit handling. trade rows can cross-check activity; maker/taker completeness must be validated before claims
- **Data API current positions**: profile/current snapshot only. aggregate exposure and average entry feasible; individual timing unavailable
- **Data API closed positions**: closed-position snapshot feasible; docs list limit max 50 per call. exit/resolution evidence partial; exact exit sequence needs activity/trades join
- **Data API accounting snapshot**: accounting snapshot/cross-check feasible, not a primary fill timeline. may validate balances/equity but not enough alone for entry/exit reconstruction
- **CLOB prices-history**: market price timeline feasible for token IDs/outcome assets. supports time-to-expiry, late-entry, and price-context joins; does not identify wallet fills
- **Data API market positions**: holder context only. not needed for wallet timeline unless validating a specific market

## Reconstructable fields

- `entry_timestamp`: feasible from BUY trade/activity timestamps
- `exit_timestamp`: partial from SELL/REDEEM rows and closed-position joins
- `entry_price`: feasible from BUY price
- `exit_or_resolution_price`: partial from SELL price, closed curPrice, and resolution/redeem evidence
- `holding_time`: partial after wallet+conditionId+asset lifecycle matching
- `side`: feasible from side/outcome/outcomeIndex
- `size`: feasible from size/usdcSize
- `market_type`: feasible from slug/title/eventSlug pattern parsing
- `time_to_expiry_at_entry`: feasible after joining endDate or parsing dated fast-market slugs
- `held_to_resolution`: partial from REDEEM/closed position/endDate evidence
- `binance_lag_alignment`: feasible only after joining external Binance/reference price series to wallet trade timestamps

## Unavailable or incomplete fields

- private trader intent and decision rules
- guaranteed order-book queue position or fill priority
- complete maker/taker role for every public row until /trades filters are validated
- full exit linkage when only aggregate positions are present
- copy-trading delay/fill certainty
- Binance-lag inference from Polymarket wallet endpoints alone

## Seed wallet feasibility

| wallet | saved trade rows | expected row count | feasibility |
|---|---:|---:|---|
| `0x63ce342161250d705dc0b16df89036c8e5f9ba9a` | 0 | 10000 | profile_snapshot_only |
| `0xde17f7144fbd0eddb2679132c10ff5e74b120988` | 0 | 1168 | profile_snapshot_only |
| `0x1f0ebc543b2d411f66947041625c0aa1ce61cf86` | 0 | 10000 | profile_snapshot_only |
| `0xd0d6053c3c37e727402d84c14069780d360993aa` | 0 | 10000 | profile_snapshot_only |
| `0x594edB9112f526Fa6A80b8F858A6379C8A2c1C11` | 0 | 8182 | profile_snapshot_only |
| `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a` | 0 | 658 | trade_fill_history_feasible_best_seed_wallet |

## Safety boundary

This task used read-only public endpoints and one bounded probe only. It does not authorize live trading, wallet connection, order placement, automatic trade copying, capture campaigns, holdout access, or production model training.

## Recommended next task

`Wallet Public Trade History Ingestion Design v1`
