# Polymarket Next Task

Last updated: July 4, 2026
Task status: ACTIVE

This file contains exactly one active task. Read canonical project memory
before starting it.

## Active task: Run Wallet Specialist Alpha Chronological Validation v1

### Objective

Attempt to disprove whether the four already identified above-baseline wallets
contain stable, actionable directional information on fast-crypto Polymarket
markets using only existing public datasets.

### Required scope

1. Freeze the four candidate wallet IDs and their observed asset specialties
   before evaluation; do not discover or substitute wallets on test folds.
2. Build market-grouped chronological folds with no same-market or future-row
   leakage between train and evaluation periods.
3. Compare preregistered wallet-specialist signals against random side,
   population-wallet and contemporaneous YES-price baselines.
4. Report sample size, match rate, calibration/value metrics where valid,
   concentration by wallet/asset/date/market, and uncertainty intervals.
5. Stress public observation delay, spread/slippage and missed-entry assumptions
   without optimizing thresholds for historical P&L.
6. Evaluate wallet consensus and asset-specialist partitions only as clearly
   labeled secondary hypotheses with multiplicity limitations.
7. Choose exactly one result: `SUPPORTED_FOR_PROSPECTIVE_SHADOW`,
   `INCONCLUSIVE`, or `REJECTED`.

### Forbidden

- no new capture campaign, credentials, wallet/private-key logic or orders;
- no sealed holdout inspection or evaluation;
- no production model training;
- no wallet reselection, parameter search or evaluation-fold optimization;
- no claim that outcome alignment equals realized or executable profit.

### Acceptance criteria

- deterministic, replayable existing-data analysis;
- leakage and selection-bias audit included;
- conservative execution sensitivity reported;
- one successor selected from measured evidence;
- relevant and full repository tests pass;
- exactly one active successor remains.
