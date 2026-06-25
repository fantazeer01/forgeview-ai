# Polymarket Next Task

Last updated: June 26, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `PROJECT_STATE.md`, `DECISIONS.md`,
`REPRICING_RESEARCH_V1.md`, and
`WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet Score Fixture Review v1

### Objective

Review the first bounded structural Wallet Score fixture for correctness,
determinism, validation coverage, and interpretation safety before any score
expansion or deeper-history use.

### Required scope

1. Read:
   - `polymarket/models/wallet_intelligence_v1/wallet_score_design/wallet_score_design_v1.md`;
   - `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_scores.csv`;
   - `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_scores_summary.json`;
   - `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_score_validation.json`;
   - `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_score_report.md`;
   - `polymarket/wallet_intelligence/wallet_score.py`;
   - `tests/polymarket/test_wallet_intelligence.py`.
2. Confirm the implementation uses only approved structural metrics.
3. Confirm forbidden inputs are absent from score calculation.
4. Review component and penalty behavior against Wallet Score Design v1.
5. Review deterministic ordering and repeatable export.
6. Review interpretation language to ensure it does not imply profitability,
   alpha, execution quality, copyability, or wallet recommendations.
7. If bounded correctness bugs are found, fix only those bugs.
8. Recommend exactly one successor task.

### Acceptance criteria

- No public ingestion is launched.
- No new score inputs are added.
- No metric generation changes are made unless required for a bounded
  correctness bug and documented.
- No PnL, ROI, realized profit, Sharpe, execution quality, copyability, alpha
  claims, mark-to-market values, final resolved win/loss outcomes, sealed
  holdout labels, private wallet data, order-placement data, or authenticated
  trading data is used.
- No live trading, automatic trade copying, wallet/private-key use, order
  placement, execution-adjacent code, capture campaign, production model
  training, sealed holdout inspection, or holdout evaluation is implemented.
- Wallet Intelligence tests and the full test suite are run.
- Exactly one successor task remains in this file.
