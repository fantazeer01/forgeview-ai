# Polymarket Next Task

Last updated: June 25, 2026  
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `PROJECT_STATE.md`, `DECISIONS.md`,
`REPRICING_RESEARCH_V1.md`, and
`WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet Lifecycle Metrics v1

### Objective

Compute bounded, descriptive wallet-level lifecycle metrics from the existing
wallet lifecycle reconstruction fixture outputs only.

### Required scope

1. Read the lifecycle review outputs under:
   `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_review/`.
2. Use existing lifecycle positions from:
   `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture/lifecycle_positions.csv`.
3. Compute wallet-level metrics:
   - lifecycle position count;
   - still-open count and share;
   - partial-exit count and share;
   - full-exit count and share;
   - bounded-history oversold count and share;
   - BUY and SELL trade counts;
   - total visible bought size;
   - total visible sold size;
   - remaining visible size;
   - oversold visible size;
   - near-flat residual count using an explicitly documented review-only
     threshold;
   - asset and outcome concentration;
   - fast-crypto lifecycle share.
4. Produce outputs under:
   `polymarket/models/wallet_intelligence_v1/lifecycle_metrics/`.
5. Include:
   - `wallet_lifecycle_metrics.csv`;
   - `lifecycle_metrics_summary.json`;
   - `lifecycle_metrics_report.md`.
6. Keep all metrics descriptive and non-executable.
7. Recommend exactly one successor task.

### Acceptance criteria

- Existing lifecycle fixture outputs are the only data source.
- No public ingestion is launched.
- No live trading, automatic trade copying, wallet/private-key use, order
  placement, or execution-adjacent code is implemented.
- No expiry joins, mark-to-market PnL, Binance/reference alignment,
  copyability-delay estimation, queue-priority modelling, or scoring is
  implemented.
- No sealed holdout outcomes are inspected.
- No holdout evaluation is run.
- No production model is trained.
- Exactly one successor task remains in this file.
