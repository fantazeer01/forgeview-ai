# Polymarket Next Task

Last updated: June 28, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`RESEARCH_PRINCIPLES.md`, `MASTER_OBJECTIVE.md`, `PROJECT_STATE.md`,
`DECISIONS.md`, and `WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet Autonomous Evidence Accumulator Controlled Launch v1

### Hypotheses under test

- H2: public wallet activity becomes observable quickly enough;
- H3: enough time remains after detection to support future execution
  feasibility research.

### Objective

Perform the first controlled public launch of the completed autonomous
accumulator. Verify preflight state, start the detached bounded process once,
and confirm that it completes session 2 and updates all progress artifacts
without manual intervention. Do not alter implementation or gates unless a
bounded correctness bug blocks the launch.

### Required scope

1. Confirm status is `ready`, action is `CONTINUE`, completed sessions are 1,
   and remaining budget is 59.
2. Confirm no accumulator process is already active.
3. Launch exactly one detached accumulator process through the committed
   `start` command.
4. Observe until session 2 completes or a persisted failure is reported.
5. Verify observer poll persistence, automatic session numbering, Gamma expiry
   caching where eligible trades exist, and atomic progress artifacts.
6. Confirm the process continues only when action remains `CONTINUE`; otherwise
   confirm it stopped on the recorded terminal gate.
7. Record measured session-2 evidence and runtime health without changing any
   threshold or polling parameter.

### Forbidden

- no second accumulator process;
- no Wallet Score, hypothesis, gate, endpoint, polling, or evidence-budget
  change;
- no wallet/private-key use, authentication, order placement, copy automation,
  or live trading;
- no profitability, alpha, expected-return, or investment claim;
- no sealed holdout access or evaluation;
- no unrelated repricing runtime changes.

### Acceptance criteria

- one detached process starts and session 2 is numbered automatically;
- every public poll is durable and progress artifacts update after completion;
- restart/duplicate protections remain intact;
- the process records one current action and obeys terminal stop conditions;
- all Wallet Intelligence and repository tests pass;
- exactly one active successor task remains.
