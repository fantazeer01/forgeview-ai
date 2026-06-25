# Polymarket Next Task

Last updated: June 25, 2026  
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `PROJECT_STATE.md`, `DECISIONS.md`,
`REPRICING_RESEARCH_V1.md`, and
`WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet Lifecycle Reconstruction Review v1

### Objective

Review the deterministic lifecycle reconstruction fixture outputs and decide
which wallet lifecycle fields can be interpreted safely from bounded public
trade history.

### Required scope

1. Read the lifecycle prototype outputs under:
   `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture/`.
2. Confirm the prototype used only existing normalized public smoke history
   from:
   `polymarket/data/wallet_intelligence/trade_history_smoke_v1/`.
3. Review lifecycle status groups:
   - still-open candidates;
   - partial-exit candidates;
   - full-exit candidates if present;
   - bounded-history oversold candidates.
4. Quantify which lifecycle candidates are interpretable from the bounded
   one-page smoke and which require deeper history.
5. Identify whether a future bounded metrics task is justified for:
   - entry/exit candidate counts;
   - partial-exit frequency;
   - bounded-history gap rate;
   - asset/outcome lifecycle concentration;
   - wallet-level lifecycle pattern summaries.
6. Keep all conclusions descriptive and non-executable.
7. Recommend exactly one successor task.

### Acceptance criteria

- No public ingestion is launched.
- No live trading, automatic trade copying, wallet/private-key use, order
  placement, or execution-adjacent code is implemented.
- No expiry joins, mark-to-market PnL, Binance/reference alignment,
  copyability-delay estimation, or queue-priority modelling is implemented.
- No sealed holdout outcomes are inspected.
- No holdout evaluation is run.
- No production model is trained.
- Exactly one successor task remains in this file.
