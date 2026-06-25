# Wallet Public Trade History Broader Evidence v1

Generated: 2026-06-25T21:41:10+00:00

## Scope

Public read-only wallet activity rows were fetched within the approved broader-evidence limits. Cross-check `/trades` rows were stored separately and were not merged into lifecycle reconstruction.

## Summary

- Wallets attempted: 30
- Wallets with primary rows: 30
- Primary pages fetched: 60
- Primary rows fetched: 5771
- Primary rows normalized: 5765
- Cross-check pages fetched: 30
- Cross-check rows fetched: 3000
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
- `cross_check_bounded_scope`: passed

## Reproducibility Hashes

- `trade_history_raw_jsonl_sha256`: `d8408a7e43cf806488d954cc4460161e286c215434b5bc36c3df7bb35d808823`
- `trade_history_cross_check_raw_jsonl_sha256`: `ea7de2c4396fa4c7d231bd4450aaa8340bb354a2d17dfd22ab1649a9d480ef64`
- `trade_history_normalized_csv_sha256`: `40d395b65a964535ddefccd7fdc0642e5cfc90bba36cba3a2c92b03e9a07b062`
- `trade_history_summary_json_sha256`: `87f59c9591c70d5c5f92dab6a88547aed87d5710c0ca4d0b2e9e73f2c2c6f2df`
- `broader_ingestion_report_json_sha256`: `87f59c9591c70d5c5f92dab6a88547aed87d5710c0ca4d0b2e9e73f2c2c6f2df`
- `validation_gate_results_json_sha256`: `5b264698c57bb4c25b6eff8bcbd88b542cdea1e0da7fe9ef3d5477f2021b95fa`
- `csv_repeat_export_hash_match`: `True`

## Safety Boundary

No wallet/private-key use, order placement, automatic trade copying, live monitoring, capture campaign, production model training, sealed holdout inspection, or holdout evaluation was performed.
