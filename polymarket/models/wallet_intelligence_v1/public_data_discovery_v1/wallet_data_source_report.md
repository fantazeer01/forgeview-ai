# Polymarket Public Data Discovery Sprint v1

Status: Complete  
Date: June 26, 2026  
Branch: Wallet Intelligence Research v1  
Output directory:
`polymarket/models/wallet_intelligence_v1/public_data_discovery_v1/`

## Purpose

This sprint performed a real-world discovery pass over public Polymarket data
sources that can improve Wallet Intelligence. It focused on endpoint
accessibility, authentication, rate limits, observed behavior, join keys, and
research value. It did not implement integration, change Wallet Score, change
Wallet Watchlist, connect wallets, use private keys, place orders, copy trades,
inspect sealed holdout outcomes, or run holdout evaluation.

## Method

Evidence came from three sources:

- official Polymarket API documentation;
- existing ForgeViewAI endpoint usage and Wallet Intelligence artifacts;
- small bounded read-only probes against representative wallet, market, event,
  token, and condition identifiers from the existing 30-wallet evidence batch.

The probes were intentionally narrow. They did not crawl markets, launch
capture, or fetch unbounded wallet history.

## Public API Surface

Polymarket currently exposes three major public surfaces relevant to Wallet
Intelligence:

- Gamma API: market, event, tag, series, sports, search, comments, and public
  profile metadata.
- Data API: public user positions, closed positions, activity, trades, holders,
  open interest, value, traded counts, leaderboard, and builder analytics.
- CLOB read endpoints: orderbook, price, midpoint, spread, last trade price,
  price history, CLOB market metadata, and market lists.

Authenticated CLOB order, user order, user trade, heartbeat, and user WebSocket
paths are outside this repository's research boundary and must remain excluded.

## Bounded Probe Findings

Representative seed wallet:
`0x63ce342161250d705dc0b16df89036c8e5f9ba9a`

Representative historical fast market:

- condition ID:
  `0xe7f83f4fd9e2c1b8c5752d514e5c5761d953417037de06e6856ef066adcdf3e4`
- token ID:
  `33772256513953729867305428364575471811054395663634834290762938224302400571258`
- slug: `btc-updown-5m-1774353300`

Observed:

- Data API `/activity?user=...&type=TRADE&limit=1` returned a public trade row
  with timestamp, condition ID, type, size, USDC size, transaction hash, price,
  token asset, slug, event slug, outcome, and side-like fields.
- Data API `/trades?user=...&limit=1` returned a public trade row with side,
  asset, condition ID, size, price, timestamp, slug, event slug, outcome, and
  transaction hash.
- Data API `/positions?user=...&limit=1` returned an empty array for the seed
  wallet at probe time, confirming that current-position snapshots can be
  empty even when public trade history exists.
- Data API `/closed-positions?user=...&limit=1` returned a closed-position
  snapshot with condition ID, asset, average price, timestamp, slug, event slug,
  outcome, and `endDate`.
- Data API `/value?user=...` and `/traded?user=...` returned public aggregate
  profile values.
- Gamma `/markets/slug/btc-updown-5m-1774353300` returned the historical fast
  market and exposed `conditionId`, `slug`, `resolutionSource`, title, and
  lifecycle metadata.
- Gamma `/markets?slug=btc-updown-5m-1774353300` returned an empty array for
  the same historical slug. The next engineering sprint should therefore use
  path-by-slug first and preserve route provenance.
- Gamma `/events/slug/btc-updown-5m-1774353300` and
  `/events?slug=btc-updown-5m-1774353300` both returned the historical event.
- CLOB `/clob-markets/{condition_id}` returned token/outcome mapping for both
  historical and sampling conditions.
- CLOB orderbook/price/midpoint/spread returned 404 for the historical expired
  token and for one non-orderbook active event token, but returned 200 for a
  sampling orderbook-enabled token.
- CLOB `/last-trade-price?token_id=...` returned 200 for historical and
  sampling tokens.
- CLOB `/prices-history` returned 200 for a sampling token with
  `interval=max`, `interval=all`, and `interval=1h`, but 400 for the probed
  `interval=1m&fidelity=1` query.
- Data API `/holders` is public but returned 400 without the required market
  or token context.
- A guessed `/leaderboard` route returned 404; leaderboard use should rely on
  the documented exact route before any future use.

## Endpoint Suitability

Directly useful now:

- Gamma `/markets/slug/{market_slug}` for market-level expiry, lifecycle, and
  resolution-source metadata.
- Gamma `/events/slug/{event_slug}` and `/events?slug={event_slug}` for
  event-level fallback metadata and grouped-market checks.
- Gamma `/markets/token/{token_id}` as a fallback for token-to-market lookup
  when slug joins fail.
- CLOB `/clob-markets/{condition_id}` as a token/outcome mapping cross-check.
- Existing Data API `/activity` and `/trades` outputs as the primary wallet
  history input.

Useful later:

- Data API `/positions` and `/closed-positions` for current/closed exposure and
  possible redemption context, with PnL/value fields excluded from Wallet
  Score.
- Data API `/holders` and `/oi` for participant and open-interest context.
- CLOB `/book`, `/price`, `/midpoint`, `/spread`, `/last-trade-price`,
  `/prices-history`, and `/batch-prices-history` for liquidity, slippage, and
  mark-to-market research.
- CLOB Market WebSocket for future prospective real-time orderbook and market
  event capture.
- Polygon public logs or a public subgraph for future settlement/redemption
  provenance after a separate contract/ABI inventory.

Not suitable for this repository:

- CLOB order placement, cancellation, user order, user trade, heartbeat, and
  authenticated user WebSocket paths.
- Bridge and relayer write paths.
- Any path requiring wallet/private-key control or API credentials.

## Discovery Answer

Public data is sufficient to improve Wallet Intelligence's structural context.
The next improvement should not be another score or watchlist change. It should
join expiry metadata to the existing bounded wallet lifecycle evidence.

The strongest next endpoint path is:

1. Use existing normalized Data API wallet trade rows as input.
2. Join market metadata through Gamma `/markets/slug/{market_slug}`.
3. Join event metadata through Gamma `/events/slug/{event_slug}` and
   `/events?slug={event_slug}`.
4. Fall back to Gamma `/markets/token/{token_id}` when slug joins fail.
5. Cross-check token/outcome mapping through CLOB
   `/clob-markets/{condition_id}`.

This path directly targets the largest measured ambiguity from the previous
Wallet Intelligence evidence: 1,735 of 2,135 lifecycle candidates were still
open in bounded history.

## Remaining Unknowns

- Whether every historical fast-market slug in the 30-wallet batch resolves
  through Gamma path-by-slug.
- Whether market-level `endDate`, event-level `endDate`, and dated fast-market
  slugs agree for all sampled BTC/ETH/SOL markets.
- Whether resolved outcome can be safely parsed without creating performance
  or profitability claims.
- Whether closed-position timestamps are exit, resolution, or profile snapshot
  timestamps.
- Whether CLOB price history coverage is adequate for historical fast markets.
- Whether public on-chain settlement/redemption data can be normalized without
  hidden contract assumptions.

## Recommended Next Engineering Sprint

The next sprint should remain:

`Wallet Market Expiry Join Sprint v1`

It should use exactly these public read-only endpoints:

- `GET https://gamma-api.polymarket.com/markets/slug/{market_slug}`
- `GET https://gamma-api.polymarket.com/events/slug/{event_slug}`
- `GET https://gamma-api.polymarket.com/events?slug={event_slug}`
- `GET https://gamma-api.polymarket.com/markets/token/{token_id}` as fallback
- `GET https://clob.polymarket.com/clob-markets/{condition_id}` as
  token/outcome cross-check

It should produce report-only expiry join coverage for the existing 30-wallet
evidence batch. It must not change Wallet Score, Wallet Watchlist,
copyability classifications, thresholds, trading logic, PnL, ROI, Sharpe,
market-advantage claims, mark-to-market values, execution-quality estimates,
or sealed holdout handling.

