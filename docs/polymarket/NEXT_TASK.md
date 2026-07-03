# Polymarket Next Task

Last updated: July 4, 2026
Task status: ACTIVE

This file contains exactly one active task. Read canonical project memory
before starting it.

## Active task: Run Polymarket Executable Structural Mispricing Triage v1

### Objective

Determine whether existing public quote sessions contain directly executable,
non-directional structural mispricing with a shorter path to profit than the
permanently frozen Wallet, Repricing, outcome-prediction and standalone
microstructure branches.

### Required scope

1. Use existing public sessions only; inventory synchronized YES/NO executable
   bids, asks and visible depth.
2. Preregister and test complete-set acquisition (`YES ask + NO ask < 1`),
   complete-set liquidation (`YES bid + NO bid > 1`) and internally crossed or
   locked quote conditions after conservative fees, latency and fill limits.
3. Deduplicate serial quote states and report duration, recurrence, available
   size, asset/session concentration and executable net margin.
4. Separate genuine simultaneous quotes from stale, asynchronous, incomplete
   or mechanically invalid observations.
5. Compare opportunity density and cost robustness without parameter search.
6. Choose exactly one outcome: advance one frozen structural hypothesis to a
   bounded prospective public shadow, or reject structural mispricing from the
   current asset.

### Forbidden

- no new capture, credentials, wallet/private-key logic, orders or execution;
- no sealed holdout inspection or evaluation;
- no production model training;
- no reactivation of Wallet Intelligence or Repricing;
- no threshold selection based on observed profitability.

### Acceptance criteria

- deterministic existing-data inventory and quote-integrity audit;
- actual executable prices and visible size used;
- conservative costs and latency explicitly applied;
- one evidence-driven successor remains;
- relevant and full repository tests pass;
- exactly one active task remains.
