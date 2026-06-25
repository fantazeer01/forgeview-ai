# Polymarket Next Task

Last updated: June 26, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `PROJECT_STATE.md`, `DECISIONS.md`,
`REPRICING_RESEARCH_V1.md`, and
`WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet Score Broader Evidence Collection Design v1

### Objective

Design a bounded, public, read-only evidence expansion plan for applying the
existing Wallet Score v1 to a broader wallet sample before any broader
ingestion or score threshold change.

### Required scope

1. Read:
   - `polymarket/models/wallet_intelligence_v1/wallet_score_design/wallet_score_design_v1.md`;
   - `polymarket/models/wallet_intelligence_v1/wallet_score_fixture_review/wallet_score_fixture_review_report.md`;
   - `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_scores.csv`;
   - `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_scores_summary.json`;
   - `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_score_validation.json`;
   - `docs/polymarket/WALLET_INTELLIGENCE_RESEARCH_V1.md`.
2. Define the purpose of broader evidence collection for Wallet Score v1.
3. Define wallet selection criteria for a larger public sample without turning
   the score into a ranking, recommendation, or trading-quality measure.
4. Define public read-only data limits, including maximum wallets, pages per
   wallet, rows per wallet, retry limits, and rate-limit posture.
5. Define required provenance and reproducibility requirements.
6. Define validation gates for applying the existing score to the broader
   sample:
   - score bounds;
   - deterministic ordering;
   - no forbidden inputs;
   - missing metric handling;
   - wallet-source provenance;
   - bounded-scope compliance;
   - interpretation-safety language.
7. Define review criteria for deciding whether the current thresholds remain
   acceptable after broader evidence collection.
8. Produce a design artifact under
   `polymarket/models/wallet_intelligence_v1/wallet_score_broader_evidence_design/`.
9. Recommend exactly one successor task.

### Acceptance criteria

- No public ingestion is launched.
- No new score inputs are added.
- No threshold or penalty change is made.
- No metric generation change is made.
- No PnL, ROI, realized profit, Sharpe, execution quality, copyability, alpha
  claims, mark-to-market values, final resolved win/loss outcomes, sealed
  holdout labels, private wallet data, order-placement data, or authenticated
  trading data is used.
- No live trading, automatic trade copying, wallet/private-key use, order
  placement, execution-adjacent code, capture campaign, production model
  training, sealed holdout inspection, or holdout evaluation is implemented.
- Wallet Intelligence tests and the full test suite are run.
- Exactly one successor task remains in this file.
