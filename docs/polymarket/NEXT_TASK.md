# Polymarket Next Task

Last updated: June 28, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `RESEARCH_PRINCIPLES.md`, `PROJECT_STATE.md`,
`DECISIONS.md`, and `WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet Autonomous Evidence Accumulator Canonical Background Run v1

### Objective

Start the operationally validated accumulator once against canonical local
Wallet evidence state and allow it to collect autonomously until the frozen
H2/H3 framework stops it. This is bounded evidence collection, not new
engineering.

### Required scope

1. Verify canonical status is `ready`, action is `CONTINUE`, evidence is 2
   trades, completed sessions are 1, and remaining budget is 59.
2. Confirm no canonical accumulator PID is active.
3. Launch exactly one detached process with canonical 300-second sessions, the
   frozen 5-second polling interval, and no launch-only session cap.
4. Write mutable runtime progress under ignored
   `output/wallet_autonomous_canonical_v1/` paths; do not continuously rewrite
   tracked model artifacts.
5. Preserve the canonical accumulator and observer SQLite databases under the
   existing ignored data path.
6. Verify session 2 starts automatically and all poll payloads remain durable.
7. Leave the process running only while action is `CONTINUE`; it must stop
   automatically on SUPPORT, REJECT, or session 60.
8. Snapshot terminal or explicitly requested checkpoint evidence into tracked
   artifacts only after a coherent session boundary.

### Forbidden

- no second accumulator process;
- no development duration or launch-only session cap;
- no change to hypotheses, gates, polling, wallets, endpoints, evidence
  budget, Wallet Score, or Watchlist;
- no wallet/private-key use, authentication, order placement, copy automation,
  or live trading;
- no profitability, alpha, expected-return, or investment claim;
- no sealed holdout access or evaluation;
- no unrelated repricing changes.

### Acceptance criteria

- one canonical detached process starts;
- session 2 is allocated automatically and persisted;
- runtime status reports canonical configuration and durable poll progress;
- duplicate/restart protections remain intact;
- exactly one action is current and terminal conditions remain automatic;
- Wallet Intelligence and full repository tests pass;
- exactly one active successor task remains.
