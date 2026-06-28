# Polymarket Next Task

Last updated: June 28, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `RESEARCH_PRINCIPLES.md`, `PROJECT_STATE.md`,
`DECISIONS.md`, `REPRICING_RESEARCH_V1.md`, and
`WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet Detection-To-Expiry Feasibility Sprint v1

### Hypothesis under test

H3: Enough time remains after public wallet activity is first detected to
support future strategy research.

### Evidence basis

Wallet First-Seen Detection Sprint v1 proved that prospective timing is
measurable. A bounded five-minute run detected six live crypto Up/Down trades,
including two target five-minute trades with polling-quantized first-seen
upper bounds of 15.894 and 16.041 seconds. The target sample is too small to
support or reject H2, but it is sufficient to test whether an expiry join can
produce detection-to-expiry evidence.

### Objective

Use the committed Wallet First-Seen dataset and existing public Gamma/CLOB
market metadata paths to determine whether detection-to-expiry can be measured
reliably for the two target five-minute rows.

### Required scope

1. Use the existing
   `polymarket/models/wallet_intelligence_v1/first_seen_detection_v1/wallet_first_seen_dataset.csv`.
2. Restrict the primary analysis to rows where `observation_class` is
   `new_live_window_trade` and `five_minute_market` is `true`.
3. Join market expiry using existing public read-only Gamma/CLOB metadata
   paths and stable condition, token, event, or market identifiers.
4. Compute first-observation-to-expiry seconds and report whether at least 60,
   120, and 180 seconds remained.
5. Preserve first-seen delay as a polling-quantized upper bound; do not infer
   exact server publication time.
6. Do not launch another observation run unless the committed two-row evidence
   is technically unusable for the join.
7. End with exactly one feasibility conclusion: `SUPPORTED`, `REJECTED`, or
   `INCONCLUSIVE`.
8. Do not copy trades, place orders, connect wallets/private keys, modify
   Wallet Score or Watchlist, inspect sealed holdout outcomes, run holdout
   evaluation, or claim profitability, alpha, execution quality, or trading
   suitability.
9. Run Wallet Intelligence tests and the full test suite.

### Acceptance criteria

- every measured row preserves first-seen and expiry provenance;
- historical page-churn rows are excluded;
- deterministic joins and exports are verified;
- the two-row result is labelled as feasibility evidence, not a strategy
  conclusion;
- exactly one active successor task remains after completion.
