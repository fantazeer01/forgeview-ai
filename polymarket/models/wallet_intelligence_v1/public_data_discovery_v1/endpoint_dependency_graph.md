# Polymarket Public Endpoint Dependency Graph v1

Status: Discovery artifact  
Date: June 26, 2026  
Scope: Public read-only Polymarket data sources for Wallet Intelligence

This graph describes how public endpoints relate to the existing Wallet
Intelligence pipeline. It does not authorize integration, trading, wallet
connection, order placement, automatic trade copying, score changes, or broad
capture.

```mermaid
flowchart TD
    A["Watched wallet list"] --> B["Data API /activity?user=&type=TRADE"]
    A --> C["Data API /trades?user="]
    A --> D["Data API /positions?user="]
    A --> E["Data API /closed-positions?user="]
    A --> F["Gamma /public-profile?address="]

    B --> G["Normalized public trade rows"]
    C --> G
    D --> H["Position and closed-position context"]
    E --> H

    G --> I["Lifecycle reconstruction"]
    H --> I
    I --> J["Lifecycle metrics"]
    J --> K["Wallet Score v1"]
    K --> L["Wallet Watchlist v1"]

    G --> M["condition_id, token_id, market_slug, event_slug"]
    H --> M

    M --> N["Gamma /markets/slug/{market_slug}"]
    M --> O["Gamma /events/slug/{event_slug}"]
    M --> P["Gamma /events?slug={event_slug}"]
    M --> Q["Gamma /markets/token/{token_id}"]
    M --> R["CLOB /clob-markets/{condition_id}"]

    N --> S["Market expiry and lifecycle metadata"]
    O --> S
    P --> S
    Q --> S
    R --> T["Token/outcome and CLOB parameter cross-check"]

    S --> U["Report-only expiry join"]
    T --> U

    M --> V["CLOB /book, /price, /midpoint, /spread"]
    M --> W["CLOB /last-trade-price"]
    M --> X["CLOB /prices-history"]
    V --> Y["Future liquidity/slippage context"]
    W --> Y
    X --> Z["Future mark-to-market context"]

    M --> AA["Data API /holders and /oi"]
    AA --> AB["Future participant/liquidity concentration context"]

    M --> AC["CLOB Market WebSocket"]
    AC --> AD["Future real-time orderbook/trade event evidence"]

    M --> AE["Polygon public logs / settlement and redemption events"]
    AE --> AF["Future settlement/redemption provenance"]
```

## Dependency Notes

- The existing normalized wallet trade rows already contain the best join
  keys: `condition_id`, `token_id`, `market_slug`, and `event_slug`.
- Gamma market/event endpoints are the best next dependency for expiry because
  they expose `endDate`, `startDate`, `closed`, `active`, event grouping, and
  resolution-source text without requiring private data.
- `GET /markets/slug/{slug}` is safer than `GET /markets?slug={slug}` for the
  next sprint because a bounded probe returned a historical fast market by
  path while the query route returned an empty array for the same slug.
- `GET /events/slug/{slug}` and `GET /events?slug={slug}` both returned the
  historical fast market event in the bounded probe; the implementation should
  preserve route provenance and compare returned event and market dates.
- CLOB `GET /clob-markets/{condition_id}` is the best CLOB cross-check for
  token and outcome mapping; it returned both historical and active/sampling
  market data in bounded probes.
- CLOB orderbook/price endpoints are useful for future liquidity or slippage
  work, but they should not be part of the expiry join sprint. They returned
  200 for a sampling market token and 404 for expired or non-orderbook tokens.
- CLOB `GET /prices-history` is useful for future mark-to-market work, but the
  probe found parameter sensitivity: `interval=max`, `interval=all`, and
  `interval=1h` returned data for a sampling token, while
  `interval=1m&fidelity=1` returned 400.
- Data API `/positions`, `/closed-positions`, `/holders`, `/oi`, `/value`, and
  `/traded` provide useful context, but they do not remove the dominant expiry
  ambiguity by themselves.
- Authenticated CLOB user/order endpoints, wallet/private-key flows, and user
  WebSocket channels remain excluded.

## Next Engineering Endpoint Set

Exactly these public read-only endpoints should be used by the next engineering
sprint:

1. `GET https://gamma-api.polymarket.com/markets/slug/{market_slug}`
2. `GET https://gamma-api.polymarket.com/events/slug/{event_slug}`
3. `GET https://gamma-api.polymarket.com/events?slug={event_slug}`
4. `GET https://gamma-api.polymarket.com/markets/token/{token_id}` as a
   fallback when slug joins fail.
5. `GET https://clob.polymarket.com/clob-markets/{condition_id}` as a
   token/outcome cross-check only.

