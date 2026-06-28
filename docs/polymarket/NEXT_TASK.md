# Polymarket Next Task

Last updated: June 28, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`RESEARCH_PRINCIPLES.md`, `MASTER_OBJECTIVE.md`, `PROJECT_STATE.md`,
`DECISIONS.md`, and `REPRICING_RESEARCH_V1.md` before starting it.

## Active task: Integrate Restart-Safe Repricing Paper Core with v5 Event Stream v1

### Hypothesis under test

The proven restart-safe repricing state machine can consume the existing v5
event stream through a thin read-only adapter without changing event order,
detector decisions, frozen parameters, or recovery guarantees.

### Objective

Add the smallest local adapter that tails or replays an existing v5 JSONL
stream into `RestartSafePaperCore`. Prove deterministic resume from the stored
source cursor and identical final ledger state for uninterrupted and
interrupted fixture runs. Do not launch a public capture or continuous paper
campaign.

### Required scope

1. Add a read-only v5 JSONL adapter with stable source identity and event index.
2. Resume from the durable ledger cursor without skipping or duplicating an
   event.
3. Refuse source truncation, source replacement, malformed ordering, and
   strategy fingerprint mismatch.
4. Preserve raw-event-before-transition durability and all existing database
   uniqueness constraints.
5. Test clean replay, mid-stream restart, appended-event resume, duplicate
   delivery, malformed input, and source replacement.
6. Compare uninterrupted and restarted ledger signals, positions, trades,
   cursors, and realized paper PnL.
7. Keep all outputs separate from canonical outcome data, microstructure data,
   wallet research, and sealed holdout paths.
8. Run repricing tests and the full repository suite.

### Forbidden

- no detector or threshold changes;
- no parameter optimization;
- no public capture or continuous campaign;
- no holdout access or evaluation;
- no wallet, private key, authentication, order placement, or live trading;
- no Telegram, daily reporting, statistics dashboard, supervisor, deployment,
  or 24-hour soak work in this sprint;
- no merge into canonical training data.

### Acceptance criteria

- uninterrupted and restart-resumed fixture ingestion produce identical
  signals, positions, trades, cursors, and realized paper PnL;
- source replacement or truncation fails closed;
- repeated adapter startup is idempotent;
- detector source and frozen parameters remain unchanged;
- sealed holdout remains untouched;
- all repricing and repository tests pass;
- exactly one active successor task remains after completion.
