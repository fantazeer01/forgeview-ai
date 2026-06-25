# Polymarket Next Task

Last updated: June 26, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `RESEARCH_PRINCIPLES.md`, `PROJECT_STATE.md`,
`DECISIONS.md`, `REPRICING_RESEARCH_V1.md`, and
`WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet Activity Visibility Delay Sprint v1

### Hypothesis under test

H2: Public wallet actions become visible quickly enough.

### Objective

Use existing public wallet trade-history, lifecycle, and outcome-skill
artifacts to test whether the four H1 above-baseline wallets have activity
timestamps that appear early enough to support future strategy research.

This is a falsification sprint. Assume H2 is false unless public activity
timestamps show that candidate wallet actions are visible with enough time
remaining to be studied further.

### Required scope

1. Read:
   - `docs/polymarket/RESEARCH_PRINCIPLES.md`;
   - `docs/polymarket/MASTER_OBJECTIVE.md`;
   - `docs/polymarket/PROJECT_STATE.md`;
   - `docs/polymarket/DECISIONS.md`;
   - `docs/polymarket/WALLET_INTELLIGENCE_RESEARCH_V1.md`;
   - `polymarket/models/wallet_intelligence_v1/outcome_skill_baseline_v1/wallet_skill_baseline.csv`;
   - `polymarket/models/wallet_intelligence_v1/outcome_skill_baseline_v1/wallet_skill_summary.json`;
   - `polymarket/data/wallet_intelligence/trade_history_broader_v1/trade_history_normalized.csv`;
   - `polymarket/models/wallet_intelligence_v1/market_outcome_resolution_v1/market_outcome_join.csv`.
2. Restrict the main analysis to H1 above-baseline wallets:
   - `0x088df3b7e5c1b5c2d4b7dc760863153480cf025e`;
   - `0x1cc53dd33c49d0a222c61ebfd2f24ba48802b199`;
   - `0x29a55c2bf8efd1029c001477b34be47d3ca37752`;
   - `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`.
3. Use existing artifacts only unless a missing field makes H2 impossible to
   evaluate. Do not launch broad ingestion, capture, crawling, or live
   monitoring.
4. Compute visibility-delay evidence:
   - first visible wallet activity timestamp per lifecycle candidate;
   - market expiry timestamp when available;
   - time from first visible activity to expiry;
   - share of candidate actions visible with at least 60, 120, and 180 seconds
     remaining;
   - unresolved or missing timestamp fraction;
   - per-wallet sample counts.
5. Clearly separate:
   - observed timestamp evidence;
   - unknown public feed latency;
   - unknown human/automation reaction time;
   - unknown fill feasibility;
   - unknown slippage/liquidity;
   - unknown complete-history bias.
6. Do not compute or claim:
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
7. Do not modify Wallet Score, Wallet Watchlist, strategy thresholds, live
   systems, wallet/private-key handling, order placement, capture campaigns,
   production models, sealed holdout artifacts, or holdout evaluation.
8. End with exactly one conclusion for H2:
   - `SUPPORTED`;
   - `REJECTED`;
   - `INCONCLUSIVE`.
9. Run Wallet Intelligence tests and the full test suite.

### Outputs

Produce deterministic artifacts under:

`polymarket/models/wallet_intelligence_v1/activity_visibility_delay_v1/`

Include:

- `wallet_activity_visibility_delay.csv`
- `wallet_activity_visibility_summary.json`
- `wallet_activity_visibility_report.md`

### Acceptance criteria

- The sprint answers H2 as `SUPPORTED`, `REJECTED`, or `INCONCLUSIVE`.
- If H2 is rejected, the next task must stop or sharply narrow public-wallet
  strategy research.
- If H2 is supported or inconclusive with useful remaining evidence, the next
  task should test H3 directly.
- Exactly one active successor task remains in this file after completion.
