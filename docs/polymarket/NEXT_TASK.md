# Polymarket Next Task

Last updated: June 28, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`RESEARCH_PRINCIPLES.md`, `MASTER_OBJECTIVE.md`, `PROJECT_STATE.md`,
`DECISIONS.md`, and `REPRICING_RESEARCH_V1.md` before starting it.

## Active task: Implement Restart-Safe Repricing Paper Trading Core v1

### Hypothesis under test

The frozen repricing entry and exit contract can be processed causally and
recovered after interruption without changing detector decisions, losing
state, or creating duplicate paper trades.

### Objective

Implement the smallest deterministic repricing paper core needed to prove
causal replay equivalence and restart-safe idempotency. This task is local and
fixture-driven only. It must not launch a public capture or continuous paper
campaign.

### Frozen contract

- external move threshold: 6 bps;
- repricing ratio: 0.65;
- minimum confidence: 0.45;
- accepted reasons: `qualified_external_move_not_repriced` and
  `confidence_below_threshold`;
- minimum entry time: 60 seconds;
- side: YES for UP, NO for DOWN;
- target: +0.03;
- stop: -0.03;
- timeout: 180 seconds;
- conservative slippage: 0.02;
- no overlapping position for the same market and side.

### Required scope

1. Add a separate repricing paper module that consumes existing v5 raw events
   and lag measurements without modifying `LagDetector` or v5 detector logic.
2. Implement causal frozen admission, paper entry, target, stop, timeout, and
   expiry transitions.
3. Add a SQLite state ledger using Python standard-library `sqlite3` for:
   - strategy fingerprint;
   - processed event cursor;
   - admitted signals;
   - open positions;
   - closed paper trades;
   - realized paper PnL.
4. Persist the raw event before applying any state transition.
5. Enforce unique signal and close keys plus transactional non-overlap rules.
6. On restart, verify the frozen strategy fingerprint, restore open positions,
   and replay events after the last committed cursor before accepting new
   events.
7. Prove fixture equivalence with the existing offline repricing simulator for
   the same causal event sequence.
8. Add crash injection tests before and after signal admission, position open,
   close, and cursor commit. Repeated recovery must create no lost or duplicate
   signal, position, trade, or PnL record.
9. Keep outputs separate from canonical outcome data, microstructure datasets,
   and sealed holdout paths.
10. Run repricing tests and the full repository suite.

### Forbidden

- no detector or threshold changes;
- no parameter optimization;
- no public capture or paper campaign;
- no Batch 003 or other evidence campaign;
- no holdout access or evaluation;
- no wallet, private key, authentication, order placement, or live trading;
- no Telegram integration, process supervisor, or deployment work in this
  sprint;
- no merge into canonical training data.

### Acceptance criteria

- fixture replay produces the same accepted signals, exits, and PnL as the
  offline frozen simulator;
- restart from every injected failure point is deterministic and idempotent;
- open positions survive restart without forced closure;
- duplicate and overlap constraints survive process restart;
- strategy fingerprint mismatch fails closed;
- no existing detector source or frozen parameter is modified;
- sealed holdout remains untouched;
- all repricing and repository tests pass;
- exactly one active successor task remains after completion.
