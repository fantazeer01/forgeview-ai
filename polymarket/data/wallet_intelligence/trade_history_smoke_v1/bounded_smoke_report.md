# Wallet Public Trade History Bounded Public Smoke v1

Generated: 2026-06-24T20:54:32+00:00

## Summary

- Wallets attempted: 6
- Wallets succeeded: 6
- Pages fetched: 6
- Rows fetched: 600
- Rows normalized: 600
- Duplicate rows removed: 0
- Validation gates passed: true
- Deterministic CSV repeat export: true
- Parquet status: not_written_no_project_parquet_dependency

## Fast Crypto Counts

- Fast crypto rows: 367
- BTC rows: 359
- ETH rows: 97
- SOL rows: 11
- Other rows: 133

## YES/NO And Side Counts

- YES-like outcomes: 249
- NO-like outcomes: 351
- Other outcomes: 0
- BUY rows: 543
- SELL rows: 57

## Price Buckets

- `0_10c`: 201
- `10_20c`: 19
- `20_40c`: 97
- `40_60c`: 37
- `60_80c`: 106
- `80_100c`: 140
- `unavailable`: 0

## Endpoint Errors

- none

## Validation Gates

- `required_field_coverage`: passed
- `duplicate_rate`: passed
- `timestamp_parse_rate`: passed
- `market_classification_coverage`: passed
- `fast_crypto_classification_coverage`: passed
- `provenance_completeness`: passed
- `bounded_scope_compliance`: passed
- `safety_boundary_compliance`: passed
- `deterministic_export`: passed
- `join_quality_reporting_placeholder`: passed

## Fields Unavailable

- time_to_expiry_seconds
- expiry_timestamp
- exit linkage
- holding time
- queue position
- fill priority
- Binance/reference alignment
- copyability delay

## Reproducibility Hashes

- `trade_history_raw_jsonl_sha256`: `92866a7325298d26c88c07139af63f14e50b2c18a2a935fa0cc872972212a525`
- `trade_history_normalized_csv_sha256`: `242dbab56c9d1391ada6b43306e2a124aea2e5a3cf03f9d6fd7b1339e38b808d`
- `trade_history_summary_json_sha256`: `94b28a7ce0479fe7a028c01718d296d9680ac658065781bccb4872477dd910aa`
- `bounded_smoke_report_json_sha256`: `94b28a7ce0479fe7a028c01718d296d9680ac658065781bccb4872477dd910aa`
- `validation_gate_results_json_sha256`: `ee877cec57e82f84c6f28b348b298dcc363d2c90ef3f31a0a0822b78315e68b9`
- `csv_repeat_export_hash_match`: `True`

## Safety Boundary

This smoke used bounded public read-only Data API activity TRADE pages for seed wallets only. It did not connect wallets, use private keys, place orders, copy trades, launch capture campaigns, inspect sealed holdout outcomes, run holdout evaluation, or train production models.

## Recommended Next Task

`Wallet Trade Lifecycle Reconstruction Design v1`
