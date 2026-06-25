# Polymarket Next Task

Last updated: June 26, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `RESEARCH_PRINCIPLES.md`, `PROJECT_STATE.md`,
`DECISIONS.md`, `REPRICING_RESEARCH_V1.md`, and
`WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet Outcome Skill Baseline Sprint v1

### Hypothesis under test

H1: Some public wallets consistently make better decisions than random.

### Objective

Use existing public wallet lifecycle and market outcome join artifacts to test
whether visible wallet outcome choices beat a predefined random baseline in
five-minute BTC, ETH, and SOL Polymarket markets.

This is a hypothesis test, not a general metrics layer. The sprint must end
with one answer: `supported`, `rejected`, or
`inconclusive_with_next_blocker`.

### Required scope

1. Read:
   - `docs/polymarket/RESEARCH_PRINCIPLES.md`;
   - `docs/polymarket/MASTER_OBJECTIVE.md`;
   - `docs/polymarket/PROJECT_STATE.md`;
   - `docs/polymarket/DECISIONS.md`;
   - `docs/polymarket/WALLET_INTELLIGENCE_RESEARCH_V1.md`;
   - `polymarket/models/wallet_intelligence_v1/market_outcome_resolution_v1/market_outcome_join.csv`;
   - `polymarket/models/wallet_intelligence_v1/market_outcome_resolution_v1/market_outcome_join_summary.json`;
   - `polymarket/models/wallet_intelligence_v1/wallet_copyability_feasibility_v1/wallet_copyability_summary.json`.
2. Use `market_outcome_join.csv` as the primary source.
3. Restrict the main test set to:
   - public wallet lifecycle rows;
   - BTC, ETH, and SOL fast Up/Down markets;
   - resolved rows with `matched_outcome` or `unmatched_outcome`;
   - no sealed holdout data and no canonical outcome-prediction holdout paths.
4. Define baselines before measuring:
   - random 50/50 side baseline for binary Up/Down rows;
   - naive aggregate side-frequency baseline if appropriate;
   - any minimum per-wallet sample gate used for interpretation.
5. Compute descriptive hypothesis-test evidence:
   - aggregate matched-outcome rate;
   - per-wallet matched-outcome rate;
   - sample size by wallet;
   - asset breakdown for BTC, ETH, and SOL;
   - simple confidence interval or binomial-style uncertainty measure if
     available without adding heavy dependencies;
   - whether any observed effect survives minimum sample gates.
6. Clearly separate:
   - observed resolved-side match evidence;
   - unknown profitability;
   - unknown execution feasibility;
   - unknown visibility delay;
   - unknown slippage/liquidity;
   - unknown complete-history bias.
7. Do not compute or claim:
   - PnL;
   - ROI;
   - realized profit;
   - Sharpe;
   - expected value;
   - alpha;
   - market advantage;
   - copyability success;
   - execution quality;
   - trading suitability;
   - trading recommendations.
8. Do not modify Wallet Score, Wallet Watchlist, strategy thresholds, live
   systems, wallet/private-key handling, order placement, capture campaigns,
   production models, sealed holdout artifacts, or holdout evaluation.
9. Add deterministic validation:
   - all tested rows are resolved binary fast-crypto rows;
   - per-wallet sample counts reconcile to aggregate counts;
   - baseline definitions are present;
   - deterministic ordering;
   - repeatable export;
   - no forbidden metrics or claims.
10. Add focused tests and run Wallet Intelligence tests plus the full test
    suite.

### Outputs

Produce deterministic artifacts under:

`polymarket/models/wallet_intelligence_v1/outcome_skill_baseline_v1/`

Include:

- `wallet_outcome_skill_baseline.csv`
- `wallet_outcome_skill_summary.json`
- `wallet_outcome_skill_validation.json`
- `wallet_outcome_skill_report.md`

### Acceptance criteria

- The sprint answers H1 as `supported`, `rejected`, or
  `inconclusive_with_next_blocker`.
- If H1 is not supported, the next task must stop or sharply narrow wallet
  strategy research rather than add more data infrastructure.
- If H1 is supported, the next task should test H2 or H3 directly.
- Wallet Intelligence tests and the full test suite are run.
- Exactly one active successor task remains in this file after completion.
