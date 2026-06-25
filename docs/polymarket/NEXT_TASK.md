# Polymarket Next Task

Last updated: June 25, 2026  
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `PROJECT_STATE.md`, `DECISIONS.md`,
`REPRICING_RESEARCH_V1.md`, and
`WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet Lifecycle Metrics Review v1

### Objective

Review the bounded wallet-level lifecycle metrics outputs for determinism,
interpretability, and next-step readiness before any deeper-history,
scoring, or value-modelling work.

### Required scope

1. Read lifecycle metrics outputs under:
   `polymarket/models/wallet_intelligence_v1/lifecycle_metrics/`.
2. Confirm metrics use only existing lifecycle positions from:
   `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture/lifecycle_positions.csv`.
3. Review:
   - wallet-level lifecycle counts;
   - still-open / partial-exit / full-exit / oversold shares;
   - average and median visible position sizes;
   - BUY/SELL event counts;
   - average events per lifecycle;
   - SELL-only lifecycle percentage;
   - near-flat residual count and threshold documentation;
   - asset/outcome concentration;
   - fast-crypto lifecycle share.
4. Identify which metrics are safe for descriptive research and which require
   deeper history before interpretation.
5. Recommend exactly one successor task.

### Acceptance criteria

- No public ingestion is launched.
- No live trading, automatic trade copying, wallet/private-key use, order
  placement, or execution-adjacent code is implemented.
- No PnL, ROI, Sharpe, copyability, wallet scoring, wallet ranking,
  mark-to-market values, expiry joins, Binance/reference alignment,
  copyability-delay estimation, or queue-priority modelling is implemented.
- No sealed holdout outcomes are inspected.
- No holdout evaluation is run.
- No production model is trained.
- Exactly one successor task remains in this file.
