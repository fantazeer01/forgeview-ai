# Polymarket Next Task

Last updated: June 26, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `PROJECT_STATE.md`, `DECISIONS.md`,
`REPRICING_RESEARCH_V1.md`, and
`WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet Score Broader Evidence Batch Implementation v1

### Objective

Implement the bounded public read-only Wallet Score broader evidence batch
defined in Wallet Score Broader Evidence Collection Design v1.

### Required scope

1. Read:
   - `polymarket/models/wallet_intelligence_v1/wallet_score_design/wallet_score_design_v1.md`;
   - `polymarket/models/wallet_intelligence_v1/wallet_score_fixture_review/wallet_score_fixture_review_report.md`;
   - `polymarket/models/wallet_intelligence_v1/wallet_score_broader_evidence_design/broader_evidence_plan.md`;
   - `docs/polymarket/WALLET_INTELLIGENCE_RESEARCH_V1.md`.
2. Add a broader wallet manifest template at
   `polymarket/wallet_intelligence/watched_wallets_broader_v1.example.csv`.
3. Implement or wire a bounded public read-only batch path that can process
   the broader wallet manifest while enforcing the design limits.
4. Preserve the existing Wallet Score v1 allowed inputs and thresholds.
5. Produce expected artifacts under the paths specified in the design:
   - `polymarket/data/wallet_intelligence/trade_history_broader_v1/`;
   - `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_broader_v1/`;
   - `polymarket/models/wallet_intelligence_v1/lifecycle_metrics_broader_v1/`;
   - `polymarket/models/wallet_intelligence_v1/wallet_score_broader_evidence_v1/`.
6. Run validation gates:
   - score bounds;
   - deterministic ordering;
   - no forbidden inputs;
   - missing metric handling;
   - wallet-source provenance;
   - bounded-scope compliance;
   - interpretation-safety language.
7. Summarize score distribution against the healthy and suspicious behavior
   criteria from the design.
8. Recommend exactly one successor task.

### Acceptance criteria

- Public ingestion, if used, is bounded to the design limits:
  - maximum wallets: 30;
  - maximum primary activity pages per wallet: 2;
  - maximum primary activity rows per wallet: 200;
  - maximum primary activity rows overall: 6,000;
  - maximum cross-check pages per wallet: 1;
  - maximum cross-check rows per wallet: 100;
  - maximum cross-check rows overall: 3,000;
  - maximum retries per page: 2.
- No new score inputs are added.
- No threshold or penalty change is made.
- No metric generation change is made except path parameterization needed to
  write the broader evidence artifacts.
- No PnL, ROI, realized profit, Sharpe, execution quality, copyability, alpha
  claims, mark-to-market values, final resolved win/loss outcomes, sealed
  holdout labels, private wallet data, order-placement data, or authenticated
  trading data is used.
- No live trading, automatic trade copying, wallet/private-key use, order
  placement, execution-adjacent code, capture campaign, production model
  training, sealed holdout inspection, or holdout evaluation is implemented.
- Wallet Intelligence tests and the full test suite are run.
- Exactly one successor task remains in this file.
