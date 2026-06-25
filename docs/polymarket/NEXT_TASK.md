# Polymarket Next Task

Last updated: June 26, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `PROJECT_STATE.md`, `DECISIONS.md`,
`REPRICING_RESEARCH_V1.md`, and
`WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet Outcome-Aware Metrics Sprint v1

### Objective

Compute the first bounded descriptive outcome-aware Wallet Intelligence metrics
from the completed public market outcome join.

This task should summarize observed `matched_outcome`, `unmatched_outcome`,
`unresolved_market`, and `insufficient_evidence` classifications. It must not
claim wallet profitability, copyability, market advantage, or execution
quality.

### Required scope

1. Read:
   - `polymarket/models/wallet_intelligence_v1/market_outcome_resolution_v1/market_outcome_join.csv`;
   - `polymarket/models/wallet_intelligence_v1/market_outcome_resolution_v1/market_outcome_join_summary.json`;
   - `polymarket/models/wallet_intelligence_v1/wallet_copyability_feasibility_v1/wallet_copyability_summary.json`;
   - `polymarket/models/wallet_intelligence_v1/lifecycle_metrics_broader_v1/wallet_metrics.csv`;
   - `polymarket/models/wallet_intelligence_v1/wallet_score_broader_v1/wallet_scores.csv` if present;
   - `docs/polymarket/WALLET_INTELLIGENCE_RESEARCH_V1.md`;
   - `docs/polymarket/DECISIONS.md`.
2. Use `market_outcome_join.csv` as the primary source.
3. Compute only descriptive outcome-aware metrics, including:
   - lifecycle positions evaluated;
   - matched outcome count and share;
   - unmatched outcome count and share;
   - unresolved market count and share;
   - insufficient evidence count and share;
   - resolved-outcome coverage;
   - join confidence distribution;
   - per-wallet outcome classification counts;
   - per-wallet unresolved/insufficient evidence counts;
   - per-wallet outcome-data confidence labels.
4. Preserve explicit distinction between observed facts and unknowns.
5. Do not compute:
   - PnL;
   - ROI;
   - realized profit;
   - Sharpe;
   - expected value;
   - mark-to-market value;
   - execution quality;
   - trading suitability;
   - copyability score;
   - Wallet Score changes;
   - Wallet Watchlist changes;
   - wallet rankings for trading.
6. Do not connect wallets, use private keys, place orders, copy trades,
   implement live monitoring, launch capture campaigns, inspect sealed holdout
   outcomes, run holdout evaluation, or train production models.
7. Add deterministic validation:
   - all rows classified;
   - every wallet has confidence labels;
   - shares sum within tolerance;
   - deterministic ordering;
   - repeatable export;
   - no forbidden metrics or claims.
8. Add focused tests.
9. Run Wallet Intelligence tests and the full test suite.

### Outputs

Produce deterministic artifacts under:

`polymarket/models/wallet_intelligence_v1/outcome_aware_metrics_v1/`

Include:

- `outcome_aware_wallet_metrics.csv`
- `outcome_aware_metrics_summary.json`
- `outcome_aware_metrics_validation.json`
- `outcome_aware_metrics_report.md`

### Acceptance criteria

- Artifacts are deterministic and repeatable.
- Metrics are descriptive and outcome-aware, but not performance-aware.
- Wallet Score and Wallet Watchlist logic remain unchanged.
- Wallet Intelligence tests and the full test suite are run.
- Exactly one active successor task remains in this file after completion.
