# Polymarket Next Task

Last updated: June 26, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `PROJECT_STATE.md`, `DECISIONS.md`,
`REPRICING_RESEARCH_V1.md`, and
`WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet Market Expiry Join Sprint v1

### Objective

Implement the highest-priority missing Wallet Intelligence information layer
identified by Wallet Intelligence Information Gain Sprint v1: public market
expiry joins for the existing bounded wallet trade and lifecycle evidence.

This task should add report-only expiry context. It must not change Wallet
Score, Wallet Watchlist, copyability classifications, or any trading boundary.

### Required scope

1. Read:
   - `polymarket/models/wallet_intelligence_v1/information_gain_sprint_v1/wallet_information_gain_report.md`;
   - `polymarket/models/wallet_intelligence_v1/information_gain_sprint_v1/wallet_research_roadmap.md`;
   - `polymarket/models/wallet_intelligence_v1/wallet_copyability_feasibility_v1/wallet_copyability_report.md`;
   - `polymarket/models/wallet_intelligence_v1/wallet_copyability_feasibility_v1/wallet_copyability_summary.json`;
   - `polymarket/data/wallet_intelligence/trade_history_broader_v1/trade_history_summary.json`;
   - `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_broader_v1/lifecycle_positions.csv`;
   - `docs/polymarket/WALLET_INTELLIGENCE_RESEARCH_V1.md`.
2. Use existing bounded Wallet Intelligence artifacts as the primary input.
3. Join only public read-only market expiry metadata. Inventory endpoint paths
   that can map:
   - condition IDs;
   - token IDs / asset IDs;
   - market slugs;
   - event slugs;
   - expiry timestamps.
4. If public probing is needed, keep it narrowly bounded and read-only:
   - no more than 30 markets/events sampled from existing evidence;
   - no recursive crawling;
   - no broad market capture;
   - no authenticated requests.
5. Produce measured expiry join coverage for the existing 30-wallet evidence
   batch:
   - market metadata coverage;
   - expiry timestamp coverage;
   - condition ID / token ID mapping coverage;
   - unresolved or ambiguous market counts.
6. Report which fields become measurable after joins:
   - time-to-expiry at entry;
   - held-through-expiry candidate;
   - late-window entry behavior;
   - lifecycle status refinement if safe and report-only.
7. Report fields that remain unavailable:
   - resolved outcomes;
   - observation delay;
   - slippage and fill certainty;
   - queue position;
   - full unbounded history;
   - private intent;
   - external BTC/ETH/SOL reference alignment.
8. Do not modify Wallet Score formula, thresholds, Wallet Watchlist logic, or
   copyability classifications.
9. Do not compute ROI, PnL, Sharpe, market advantage, execution quality,
   trading rankings, or trading recommendations.

### Outputs

Produce deterministic artifacts under:

`polymarket/models/wallet_intelligence_v1/market_expiry_join_v1/`

Include:

- `market_expiry_join_report.md`
- `market_expiry_join_summary.json`
- `expiry_join_endpoint_inventory.csv`
- `expiry_join_coverage_by_wallet.csv`
- `expiry_join_coverage_by_market.csv`
- `bounded_probe_sample.jsonl` if a public probe is performed

### Acceptance criteria

- Wallet Intelligence tests and the full test suite are run.
- Exactly one active successor task remains in this file.
- No live monitoring, live trading, automatic trade copying, wallet/private-key
  use, order placement, production model training, sealed holdout inspection,
  holdout evaluation, broad scraping, or capture campaign is implemented.
- No resolved-outcome scoring, profitability, market-advantage, copy-outcome,
  return, execution-quality, or trading-suitability claim is introduced.
