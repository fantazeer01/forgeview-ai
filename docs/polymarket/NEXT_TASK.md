# Polymarket Next Task

Last updated: July 3, 2026
Task status: ACTIVE

This file contains exactly one active task. Read the canonical Polymarket
memory documents before starting it.

## Active task: Run Repricing Weak-Evidence Stability And Executable-Cost Stress Sprint v1

### Objective

Attempt to falsify the newly passed Weak Evidence result using the three
scientifically admitted public Repricing sessions, without changing the frozen
detector or optimizing for profitability.

### Required scope

1. Use only Balanced Batch 001, Balanced Batch 002, and the admitted clean
   fourth-soak dataset.
2. Measure chronological session/fold stability, asset and side dependence,
   signal clustering, and P&L concentration.
3. Apply predefined executable-cost stress for spread, slippage, latency, and
   available depth without tuning thresholds from outcomes.
4. Recompute expectancy, drawdown, win rate, confidence limitations, and weak
   evidence stability under each stress.
5. Conclude `SUPPORTED`, `WEAKENED`, or `REJECTED` for advancement toward
   moderate evidence.
6. Produce a compact GitHub-safe report and update project memory.

### Forbidden

- no new capture or campaign;
- no detector, threshold, target, stop, timeout, fingerprint, or evidence-gate
  change;
- no sealed holdout inspection or evaluation;
- no production model training;
- no wallet, private key, authenticated API, order placement, or live trading;
- no optimization against paper P&L.

### Acceptance criteria

- deterministic stress outputs from admitted public evidence only;
- explicit session, asset, side, clustering, and concentration results;
- conservative executable-cost assumptions are predefined and reported;
- exactly one scientific conclusion and one successor task remain;
- Repricing and full repository tests pass.
