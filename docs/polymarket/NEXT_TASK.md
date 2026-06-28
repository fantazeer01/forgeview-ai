# Polymarket Next Task

Last updated: June 28, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`RESEARCH_PRINCIPLES.md`, `MASTER_OBJECTIVE.md`, `PROJECT_STATE.md`,
`DECISIONS.md`, and `WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet H2/H3 Gate-Bound Evidence Collection Sprint v1

### Hypotheses under test

- H2: public wallet activity becomes observable quickly enough;
- H3: enough time remains after detection to support future execution
  feasibility research.

### Objective

Collect the next bounded tranche with the existing restart-safe observer and
evaluate the frozen H2/H3 decision framework. This is evidence collection,
not new engineering and not an automatic commitment to exhaust the budget.

### Frozen collection rules

1. Observe only the four frozen H1 wallets.
2. Keep the existing public endpoint, 5-second polling, 100-row page, 300-second
   session, and 240-request session limits unchanged.
3. Preserve every poll, first-seen trade, stable identity, and Gamma expiry
   provenance through existing components.
4. Run at most 10 additional bounded sessions in this sprint.
5. Stop earlier if the cumulative eligible sample reaches 100 rows.
6. Recompute the framework after the tranche; do not alter any gate.
7. Preserve session and UTC-date diversity explicitly.

### Decision rules

- continue only if H2/H3 remain inconclusive and fewer than 60 total sessions
  have been consumed;
- graduate only if both support gates and every minimum evidence gate pass;
- freeze if either rejection gate passes;
- freeze if the 60-session total budget is exhausted without minimum evidence;
- no automatic collection-budget extension.

### Forbidden

- no Wallet Score, Watchlist, polling, endpoint, threshold, or hypothesis
  change;
- no wallet/private-key use, authentication, order placement, copy automation,
  or live trading;
- no profitability, alpha, expected-return, or investment claim;
- no execution, slippage, liquidity, fill, or queue simulation;
- no sealed holdout access or evaluation;
- no permanent or unbounded monitoring.

### Acceptance criteria

- no more than 10 bounded sessions are attempted;
- cumulative evidence and every framework gate are reported deterministically;
- H2 and H3 each receive exactly one current conclusion;
- the program receives exactly one action: `CONTINUE`,
  `GRADUATE_TO_ENGINEERING`, or `FREEZE`;
- all Wallet Intelligence and repository tests pass;
- exactly one active successor task remains.
