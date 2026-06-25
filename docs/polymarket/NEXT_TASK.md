# Polymarket Next Task

Last updated: June 26, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `PROJECT_STATE.md`, `DECISIONS.md`,
`REPRICING_RESEARCH_V1.md`, and
`WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet Watchlist Broader Evidence Batch v1

### Objective

Apply the reviewed Wallet Watchlist v1 artifact pattern to a bounded broader
evidence batch while preserving the existing Wallet Score formula, score
thresholds, public read-only limits, deterministic exports, and all
non-trading safety boundaries.

### Required scope

1. Read:
   - `polymarket/models/wallet_intelligence_v1/wallet_watchlist_review/wallet_watchlist_review_report.md`;
   - `polymarket/models/wallet_intelligence_v1/wallet_score_broader_evidence_design/broader_evidence_plan.md`;
   - `docs/polymarket/WALLET_INTELLIGENCE_RESEARCH_V1.md`.
2. Use the reviewed Wallet Watchlist v1 schema and report pattern:
   - wallet ID;
   - score;
   - priority bucket;
   - reason codes;
   - structural strengths;
   - structural risks;
   - recommended next research action.
3. Use existing Wallet Score v1 formula and thresholds only.
4. Do not add scoring inputs or change score penalties.
5. Keep the batch bounded by the approved broader-evidence limits:
   - maximum wallets: 30;
   - maximum primary activity pages per wallet: 2;
   - maximum primary activity rows per wallet: 200;
   - maximum primary activity rows overall: 6,000;
   - maximum `/trades` cross-check pages per wallet: 1;
   - maximum cross-check rows per wallet: 100;
   - maximum cross-check rows overall: 3,000;
   - maximum retries per page: 2.
6. Produce deterministic broader-batch watchlist artifacts under a separate
   output path.
7. Validate:
   - deterministic ordering;
   - reason codes present;
   - strengths/risks/actions present;
   - no forbidden claims;
   - no forbidden metrics;
   - repeatable export;
   - bounded-scope compliance.
8. Summarize distribution and validation without interpreting profitability,
   alpha, copyability, execution quality, or trading suitability.

### Acceptance criteria

- Wallet Intelligence tests and the full test suite are run.
- No live monitoring, live trading, automatic trade copying, wallet/private-key
  use, order placement, capture campaign, production model training, sealed
  holdout inspection, or holdout evaluation is implemented.
- No PnL, ROI, Sharpe, alpha, copyability, execution-quality,
  mark-to-market, or trading-recommendation claim is introduced.
- Exactly one successor task remains in this file.
