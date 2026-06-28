# Polymarket Next Task

Last updated: June 28, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`RESEARCH_PRINCIPLES.md`, `MASTER_OBJECTIVE.md`, `PROJECT_STATE.md`,
`DECISIONS.md`, and `WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet H2/H3 Prospective Evidence Accumulation Sprint v1

### Hypothesis under test

Public activity from the four frozen H1 wallets is observable with a
repeatable delay distribution and leaves at least 60 seconds before expiry for
a meaningful share of target five-minute BTC/ETH/SOL trades.

### Objective

Use the existing restart-safe first-seen observer to accumulate enough bounded
prospective evidence to retest H2 visibility delay and H3 decision-window
feasibility. Collect evidence only; do not change scoring, thresholds, or
execution assumptions.

### Frozen scope

1. Observe only the four frozen H1 wallets.
2. Use only the approved public unauthenticated Data API activity endpoint.
3. Preserve the 5-second polling interval, 100-row page limit, 300-second run
   limit, and 240-request run limit.
4. Stop after 30 eligible prospective BTC/ETH/SOL five-minute trades or 20
   bounded runs, whichever occurs first.
5. Persist every poll and first-seen trade through the existing transactional
   SQLite observer.
6. Join eligible rows to public Gamma expiry metadata and preserve source
   provenance.
7. Report H2 delay and H3 decision-window distributions using the frozen
   60-second sufficient and 30-second marginal boundaries.
8. Keep every run restart safe, duplicate safe, deterministic, and separately
   auditable.

### Forbidden

- no wallet/private-key connection, authentication, order placement, or live
  trading;
- no copy-trade automation;
- no Wallet Score or Watchlist change;
- no profitability, expected-return, alpha, or investment claim;
- no execution-quality, slippage, fill, liquidity, or queue estimate;
- no sealed holdout access or evaluation;
- no permanent monitoring or unbounded collection.

### Acceptance criteria

- at least 30 eligible target rows are collected, or the 20-run bound is
  reached and the shortfall is reported;
- every eligible row has stable identity, trade time, first-seen time, expiry,
  and source provenance;
- deterministic exports and duplicate/restart validation pass;
- H2 and H3 each receive exactly one evidence-backed conclusion from
  `SUPPORTED`, `REJECTED`, or `INCONCLUSIVE`;
- all Wallet Intelligence and repository tests pass;
- exactly one active successor task remains.
