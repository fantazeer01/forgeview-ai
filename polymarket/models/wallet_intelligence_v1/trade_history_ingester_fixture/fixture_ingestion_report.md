# Wallet Public Trade History Ingester Fixture Implementation v1

Generated: 2026-06-24T20:45:39+00:00

## Summary

- Fixture pages: 1
- Input rows: 50
- Normalized rows: 50
- Duplicate rows removed: 0
- Schema fields: 35
- Parquet status: not_written_no_project_parquet_dependency
- Validation gates passed: true

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

## Reproducibility Hashes

- `raw_trades_fixture_jsonl_sha256`: `705afb668d34515616942304ef4085d98768c0e1d30d34ae3538c2dc658a515d`
- `normalized_trades_fixture_csv_sha256`: `2e0ebdfda8b2909ab5622caf9d8c94ee5a78c96fa94de6a36abfe7f315ec2897`
- `fixture_ingestion_report_json_sha256`: `1a971bd59123f80f9265f8734b620e08928186291ff7d41e030a735adb102cd5`
- `validation_gate_results_json_sha256`: `5ba85a83d043a5f9324ad82507fd8eada672406ca0d75ca934c31e3235c34d63`
- `csv_repeat_export_hash_match`: `True`

## Safety Boundary

This fixture implementation normalizes saved fixture data only. It does not perform network ingestion, connect wallets, use private keys, place orders, copy trades, launch capture campaigns, inspect sealed holdout outcomes, run holdout evaluation, or train production models.

## Recommended Next Task

`Wallet Public Trade History Bounded Public Smoke v1`
