# Polymarket Next Task

Last updated: June 25, 2026  
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `PROJECT_STATE.md`, `DECISIONS.md`,
`REPRICING_RESEARCH_V1.md`, and
`WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet Score Fixture Implementation v1

### Objective

Implement the first bounded structural Wallet Score fixture from the approved
Wallet Score Design v1, using existing lifecycle metrics only.

### Required scope

1. Read:
   - `polymarket/models/wallet_intelligence_v1/wallet_score_design/wallet_score_design_v1.md`;
   - `polymarket/models/wallet_intelligence_v1/wallet_metrics_readiness_review/wallet_metrics_readiness_review.md`;
   - lifecycle metrics outputs under
     `polymarket/models/wallet_intelligence_v1/lifecycle_metrics/`.
2. Implement the designed score using only existing `wallet_metrics.csv`.
3. Produce outputs under:
   `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/`.
4. Required output artifacts:
   - `wallet_scores.csv`;
   - `wallet_scores_summary.json`;
   - `wallet_score_validation.json`;
   - `wallet_score_report.md`.
5. Add deterministic validation for:
   - score bounds;
   - deterministic ranking/order;
   - no forbidden metrics used;
   - missing metric handling;
   - repeatable export;
   - component bounds;
   - penalty bounds;
   - output schema completeness;
   - source provenance completeness.
6. Add focused unit tests.
7. Run Wallet Intelligence tests and the full test suite.
8. Recommend exactly one successor task.

### Acceptance criteria

- Score implementation follows Wallet Score Design v1.
- No public ingestion is launched.
- Lifecycle metric generation is not modified unless a bounded correctness bug
  is found and documented.
- No PnL, ROI, realized profit, Sharpe, execution quality, copyability, alpha
  claims, mark-to-market values, final resolved win/loss outcomes, sealed
  holdout labels, private wallet data, order-placement data, or authenticated
  trading data is used.
- No live trading, automatic trade copying, wallet/private-key use, order
  placement, execution-adjacent code, capture campaign, production model
  training, sealed holdout inspection, or holdout evaluation is implemented.
- Exactly one successor task remains in this file.
