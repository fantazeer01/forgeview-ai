# Polymarket Next Task

Last updated: June 26, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `PROJECT_STATE.md`, `DECISIONS.md`,
`REPRICING_RESEARCH_V1.md`, and
`WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet Watchlist Review v1

### Objective

Review the first Wallet Watchlist v1 artifact for correctness, interpretation
safety, and readiness as a monitoring/research handoff before any broader
evidence collection or ranking work resumes.

### Required scope

1. Inspect:
   - `polymarket/wallet_intelligence/wallet_watchlist.py`;
   - `polymarket/wallet_intelligence/cli.py`;
   - `tests/polymarket/test_wallet_intelligence.py`;
   - `polymarket/models/wallet_intelligence_v1/wallet_watchlist_v1/wallet_watchlist.csv`;
   - `polymarket/models/wallet_intelligence_v1/wallet_watchlist_v1/wallet_watchlist_summary.json`;
   - `polymarket/models/wallet_intelligence_v1/wallet_watchlist_v1/wallet_watchlist_report.md`;
   - `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_scores.csv`.
2. Verify that Wallet Watchlist v1 uses existing Wallet Score outputs only.
3. Verify that the score formula and score thresholds were not changed.
4. Confirm that every included wallet has:
   - `wallet_id`;
   - score;
   - priority bucket;
   - reason codes;
   - structural strengths;
   - structural risks;
   - recommended next research action.
5. Confirm that wallets failing minimum visibility requirements are excluded
   and that the current included/excluded counts are correct.
6. Verify report language clearly says the artifact is:
   - a monitoring/research artifact;
   - not a trading signal;
   - not a copy-trading recommendation;
   - based only on bounded public history.
7. Verify validation gates:
   - deterministic ordering;
   - reason codes present;
   - no forbidden claims;
   - no forbidden metrics;
   - repeatable export.
8. Do not add score inputs, change thresholds, rank wallets for trading,
   compute PnL/ROI/Sharpe, estimate copyability, add mark-to-market values,
   inspect sealed holdout outcomes, or run holdout evaluation.
9. If bounded correctness or interpretation-safety bugs are found, fix only
   those issues.
10. Produce a concise review note or report with:
   - confirmed invariants;
   - watchlist behavior observations;
   - inclusion/exclusion assessment;
   - known limitations;
   - recommended successor task.

### Acceptance criteria

- Wallet Intelligence tests and the full test suite are run.
- The watchlist remains a research monitoring artifact only.
- No profitability, alpha, copyability, execution-quality, or trading
  recommendation claims are introduced.
- Exactly one successor task remains in this file.
