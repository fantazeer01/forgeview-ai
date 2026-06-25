# Wallet Public Trade History Ingestion Design v1

Generated: 2026-06-24T20:35:38.024305+00:00

## Conclusion

The future wallet trade-history ingester should be bounded, cache-first, read-only, and seed-wallet only. The first implementation should normalize public activity `TRADE` rows, cross-check a small `/trades` sample, and preserve raw provenance before attempting lifecycle reconstruction. This design does not run ingestion and does not authorize execution or copy-trading.

## First Scope

- Seed wallets only: 6 wallets from `polymarket/wallet_intelligence/watched_wallets.example.csv`.
- Primary endpoint: `activity?user=<wallet>&type=TRADE&limit=100&offset=<offset>`.
- Primary cap: 3 pages or 300 activity rows per wallet.
- Cross-check endpoint: `/trades?user=<wallet>&limit=100&offset=0`.
- Cross-check cap: 1 page or 100 rows per wallet.
- Max first-scope activity rows: 1,800; max cross-check rows: 600.
- Minimum delay: 2 seconds between pages for a wallet and 1 second between global requests.
- Retries: at most 2 per page with 5 second then 15 second backoff.

## Schema Summary

- `wallet_id` (string, required): normalized wallet/proxy address. Source: source profile allowlist or row.proxyWallet.
- `profile_url` (string, required): Polymarket profile URL from seed list. Source: watched_wallets.example.csv / wallet_profiles.csv.
- `source_endpoint` (string, required): full public endpoint URL used for the raw row. Source: fetch manifest.
- `source_endpoint_name` (enum, required): activity or trades endpoint label. Source: fetch manifest.
- `activity_type` (enum, required): Polymarket activity type. Source: row.type.
- `activity_timestamp` (integer, required): public activity/trade timestamp in Unix seconds. Source: row.timestamp.
- `activity_datetime_utc` (datetime, required): UTC ISO timestamp derived from activity_timestamp. Source: derived.
- `transaction_hash` (string, required): public transaction hash for provenance and dedupe. Source: row.transactionHash.
- `condition_id` (string, required): Polymarket condition ID / market resolution key. Source: row.conditionId.
- `token_id` (string, required): outcome token / CLOB asset identifier. Source: row.asset.
- `asset_id` (string, required): alias for token_id used by CLOB prices-history. Source: row.asset.
- `market_slug` (string, required): market slug for classification and metadata joins. Source: row.slug.
- `event_slug` (string, recommended): event slug when present. Source: row.eventSlug.
- `market_title` (string, recommended): human-readable market title. Source: row.title.
- `outcome` (string, required): outcome label, typically Up/Down/Yes/No. Source: row.outcome.
- `outcome_index` (integer, recommended): outcome index from Polymarket. Source: row.outcomeIndex.
- `side` (enum, required): trade side from endpoint perspective. Source: row.side.
- `price` (decimal, required): contract price at row timestamp. Source: row.price.
- `size` (decimal, required): token/share size. Source: row.size.
- `notional_value` (decimal, recommended): USDC notional if supplied or deterministically computed. Source: row.usdcSize or price*size.
- `notional_source` (enum, required): notional provenance. Source: derived.
- `market_type` (enum, required): normalized market family. Source: derived from slug/title.
- `asset_class` (enum, required): underlying asset classification. Source: derived from slug/title.
- `up_down_market` (boolean, required): whether market is an Up/Down market. Source: derived from slug/title/outcome.
- `time_to_expiry_seconds` (integer, optional): expiry minus activity timestamp. Source: join market metadata/endDate or slug epoch.
- `expiry_timestamp` (integer, optional): market expiry/end timestamp. Source: market metadata or slug parse.
- `expiry_source` (enum, required): how expiry was obtained. Source: derived.
- `entry_or_exit_candidate` (enum, required): lifecycle role candidate. Source: derived from side/type.
- `lifecycle_group_key` (string, required): key for grouping lifecycle rows. Source: derived.
- `dedupe_key` (string, required): stable row dedupe key. Source: derived.
- `source_fetch_timestamp` (datetime, required): UTC timestamp of raw endpoint fetch. Source: fetch manifest.
- `raw_payload_hash` (string, required): SHA-256 hash of canonical raw row JSON. Source: derived.
- `raw_page_hash` (string, required): SHA-256 hash of raw page payload. Source: derived.
- `normalization_version` (string, required): normalizer version. Source: pipeline constant.
- `data_quality_flags` (string, required): semicolon-separated explicit quality flags. Source: derived.

## Architecture

- load seed wallet allowlist.
- fetch bounded activity TRADE pages with cache-first lookup.
- write raw page JSONL and fetch manifest before normalization.
- normalize rows to wallet_trade_history schema.
- cross-check first bounded /trades page per wallet.
- join existing positions/closed positions snapshots where available.
- join market metadata/endDate for observed markets only.
- optionally join narrow CLOB prices-history windows and external BTC/ETH/SOL reference snapshots in later bounded task.
- export deterministic CSV and Parquet where local dependencies allow.
- write quality report and hashes.

Raw JSONL pages and a fetch manifest are the source of truth. Normalized CSV and optional Parquet exports must be deterministic rebuild products. Every row carries endpoint provenance, fetch timestamp, raw row hash, raw page hash, normalization version, and data-quality flags.

## Join Plan

- **activity_to_market_metadata**: join `activity.condition_id, activity.market_slug` to positions/closed_positions/Gamma market metadata using `condition_id primary; slug fallback`. Purpose: Adds expiry/endDate, market title, outcome token map, active/closed status. Guardrail: Quarantine conflicting condition_id->slug mappings; preserve both raw values.
- **condition_to_slug**: join `condition_id` to activity rows, trades rows, positions rows using `condition_id`. Purpose: Validates that activity and aggregate snapshots refer to same market. Guardrail: Do not infer a missing condition_id from title alone.
- **token_to_outcome**: join `token_id / asset_id` to activity/trades rows and market metadata token maps using `token_id plus condition_id`. Purpose: Confirms Up/Down/YES/NO outcome label and outcome index. Guardrail: If endpoint outcome conflicts with metadata, mark conflict and keep raw endpoint label.
- **trades_to_positions**: join `wallet_id, condition_id, token_id, outcome` to positions and closed_positions snapshots using `wallet+condition+token/outcome`. Purpose: Cross-checks aggregate average entry, realized PnL, current/closed status. Guardrail: Aggregate positions do not prove individual fills; use as validation only.
- **trades_to_price_history**: join `token_id, activity_timestamp` to CLOB prices-history using `token_id plus narrow timestamp window`. Purpose: Adds Polymarket token price path before/after wallet activity for repricing context. Guardrail: Query only small windows around known activity rows in future implementation.
- **trades_to_binance_reference**: join `asset_class, activity_timestamp` to external BTC/ETH/SOL reference price snapshots using `asset_class plus timestamp nearest at-or-before`. Purpose: Adds external return windows around entry for Binance-lag analysis. Guardrail: Wallet endpoints alone cannot prove lag; require as-of reference snapshots.
- **lifecycle_rows**: join `wallet_id, condition_id, token_id, outcome, side, timestamp` to normalized trade_history rows using `group by lifecycle_group_key ordered by timestamp`. Purpose: Supports entry/exit candidate grouping, partial exits, approximate hold time. Guardrail: Do not collapse unmatched rows into copyability claims.

## Validation Gates

- `required_field_coverage`: 100% for wallet_id, source_endpoint, activity_timestamp, transaction_hash, condition_id, token_id, side, price, size, source_fetch_timestamp, raw_payload_hash. Action: fail normalized export; quarantine bad rows.
- `duplicate_rate`: <= 1% duplicate dedupe_key rows before dedupe and 0 duplicate dedupe_key rows after dedupe. Action: fail report and inspect endpoint/page overlap.
- `timestamp_parse_rate`: >= 99% parseable activity_timestamp to UTC datetime. Action: fail export if required timestamps cannot be parsed.
- `market_classification_coverage`: >= 95% market_type not unknown for normalized rows. Action: warn below 98%; fail below 95%.
- `fast_crypto_classification_coverage`: 100% classification for rows whose slug/title contains BTC, ETH, SOL, Up, Down, or updown. Action: fail classification report.
- `provenance_completeness`: 100% rows have source_endpoint, source_fetch_timestamp, raw_payload_hash, raw_page_hash, normalization_version. Action: fail export.
- `deterministic_export`: two rebuilds from raw JSONL produce identical CSV hash and identical JSON report hash. Action: fail handoff.
- `bounded_scope`: wallet count, rows per wallet, pages per wallet, retries, and endpoint names remain within ingestion_limits.json. Action: abort fetch before writing normalized outputs.
- `safety_boundary`: no authenticated requests, wallet/private-key code, order endpoints, capture campaigns, holdout files, or live execution paths touched. Action: abort task and record violation.
- `join_quality_reporting`: report coverage for market metadata, closed/current positions, price-history, and Binance/reference joins; do not impute missing joins. Action: warn and retain explicit unavailable flags.

## Safety Rules

- public read-only endpoints only.
- no wallet connection or private keys.
- no order placement.
- no automatic trade copying.
- no market capture campaigns.
- no sealed holdout inspection.
- no holdout evaluation.
- no production model training.
- no unbounded history ingestion.
- seed-wallet allowlist only in first implementation.

## Expected Future Output Paths

- `future_output_root`: `polymarket/data/wallet_intelligence/trade_history_v1/`
- `raw_jsonl`: `raw/activity_pages.jsonl and raw/trades_cross_check_pages.jsonl`
- `fetch_manifest`: `fetch_manifest.json`
- `normalized_csv`: `wallet_trade_history.csv`
- `normalized_parquet`: `wallet_trade_history.parquet if pyarrow/pandas support is available locally; otherwise record unavailable`
- `lifecycle_csv`: `wallet_trade_lifecycle_candidates.csv`
- `quality_report_json`: `trade_history_ingestion_report.json`
- `quality_report_md`: `trade_history_ingestion_report.md`

## Recommended Next Task

`Wallet Public Trade History Ingester Fixture Implementation v1`

That task should implement schema constants, fixture-based normalizer/deduper tests, and CLI dry-run/inspect scaffolding using saved probe fixtures only. It should not fetch broad wallet history yet.
