# Polymarket Next Task

Last updated: July 3, 2026
Task status: ACTIVE

This file contains exactly one active task. Read canonical project memory
before starting it.

## Active task: Design Repricing Authenticated Execution Latency Measurement Protocol v1

### Objective

Design the smallest safe protocol capable of measuring signing, submission,
acknowledgement, matching, and fill latency needed to resolve whether the
validated Repricing Weak Evidence can survive the real order path.

### Required scope

1. Define timestamp provenance and synchronized-clock requirements.
2. Define signing, submission, acknowledgement, match, cancellation, and fill
   measurement boundaries without implementing or running them.
3. Define a no-order public dry-run and a separately authorized credentialed
   test boundary.
4. Define fail-closed safety, exposure limits, audit artifacts, and acceptance
   gates for sub-two-second and sub-one-second feasibility.
5. Quantify which measurements can be obtained without orders and which require
   explicit future authorization.

### Forbidden

- no wallet, private key, credential, authentication, or order connection;
- no live or paper order submission;
- no strategy, threshold, evidence-gate, or execution-logic change;
- no sealed holdout inspection or evaluation;
- no production model training or evidence campaign.

### Acceptance criteria

- complete design and safety protocol with measured/inferred boundaries;
- explicit separate-authorization gates for every credentialed action;
- no execution implementation or external side effects;
- relevant and full repository tests pass;
- exactly one successor task remains.
