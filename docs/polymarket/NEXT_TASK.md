# Polymarket Next Task

Last updated: June 25, 2026  
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `PROJECT_STATE.md`, `DECISIONS.md`,
`REPRICING_RESEARCH_V1.md`, and
`WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet Score Design v1

### Objective

Design the first Wallet Score specification using only
readiness-approved structural Wallet Intelligence lifecycle metrics.

This is a design task only. Do not implement scoring.

### Required scope

1. Read:
   - `polymarket/models/wallet_intelligence_v1/wallet_metrics_readiness_review/wallet_metrics_readiness_review.md`;
   - lifecycle metrics outputs under
     `polymarket/models/wallet_intelligence_v1/lifecycle_metrics/`;
   - lifecycle reconstruction outputs under
     `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture/`.
2. Define the Wallet Score v1 objective and explicit non-goals.
3. Define allowed score inputs from readiness-approved metrics only, unless a
   new metric is clearly justified as strictly required for design.
4. Define excluded inputs, including identifiers, profile URLs, PnL, ROI,
   Sharpe, mark-to-market values, expiry/resolution outcomes, copyability,
   wallet ranking, and execution-quality evidence.
5. Define missing-data handling and minimum data-quality gates.
6. Define normalization and monotonicity policy for each allowed input.
7. Define output schema for a future score implementation.
8. Define deterministic validation criteria for any future implementation.
9. Recommend exactly one successor task.

### Acceptance criteria

- Produce a design artifact for Wallet Score v1.
- Do not implement score computation.
- Do not rank wallets.
- Do not create additional metric families unless the design proves they are
  strictly required.
- Do not compute PnL, ROI, Sharpe, copyability, wallet ranking,
  mark-to-market values, expiry joins, Binance/reference alignment,
  copyability-delay estimation, or queue-priority modelling.
- Do not launch public ingestion, broad history collection, capture campaigns,
  or production model training.
- Do not implement live trading, automatic trade copying, wallet/private-key
  use, order placement, or execution-adjacent code.
- Do not inspect sealed holdout outcomes.
- Do not run holdout evaluation.
- Exactly one successor task remains in this file.
