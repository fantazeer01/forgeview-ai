# Polymarket Next Task

Last updated: July 4, 2026
Task status: ACTIVE

This file contains exactly one active task. Read canonical project memory
before starting it.

## Active task: Run Polymarket Passive Liquidity Provision Existing-Data Feasibility Triage v1

### Objective

Determine whether the frequent wide-spread states already observed can support
a conservative passive-liquidity hypothesis after maker-fill uncertainty,
adverse selection, inventory risk and costs, without treating displayed spread
as earned profit.

### Required scope

1. Use only the five completed public sessions frozen by Structural Mispricing
   Triage v1; do not collect new data.
2. Predefine passive YES bid and ask placement at observed top-of-book prices
   and conservative touch/cross fill proxies using subsequent public quotes.
3. Model one-sided fills, two-sided completion, queue uncertainty, missed fills,
   inventory timeout, adverse selection at 2/5/15/30 seconds and 0.01 costs.
4. Report opportunities, inferred fill rates, net expectancy, capacity,
   drawdown, asset/session concentration and sensitivity to fill assumptions.
5. Reject any result that requires assuming both displayed sides fill or uses
   midpoint value as executable P&L.
6. Choose exactly one outcome: advance one fixed passive policy to prospective
   public shadow, or freeze passive liquidity provision.

### Forbidden

- no new capture, credentials, wallet/private-key logic, orders or execution;
- no sealed holdout inspection or evaluation;
- no production model training;
- no reactivation of Wallet Intelligence, Repricing or structural arbitrage;
- no threshold or policy optimization after observing results.

### Acceptance criteria

- deterministic quote-sequence replay with explicit fill-proxy limitations;
- conservative one-sided inventory and adverse-selection accounting;
- no displayed-spread-equals-profit assumption;
- one evidence-driven successor remains;
- relevant and full repository tests pass;
- exactly one active task remains.
