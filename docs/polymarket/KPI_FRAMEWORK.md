# ForgeViewAI Polymarket KPI Framework

Status: Active
Version: v1
Last updated: June 28, 2026
Authority: Canonical definition of the ForgeViewAI Polymarket project dashboard

## 1. Purpose and scope

This document defines how ForgeViewAI project health is measured. It defines
dashboard fields and reporting semantics only. It does not implement a
dashboard, create numeric targets, alter strategy or detector logic, change
frozen parameters, or authorize trading.

The framework is strategy agnostic. Repricing, Wallet Intelligence, and every
future strategy must use the same KPI groups and field meanings.

## 2. Canonical dashboard

The canonical project dashboard contains five KPI groups:

1. Research Health;
2. Strategy Health;
3. Trading Quality;
4. Infrastructure Health;
5. Business Progress.

Every dashboard snapshot must identify its observation time, evidence cutoff,
source artifacts, and whether each value is measured, unavailable, or not yet
applicable. Missing values must remain explicit and must not be guessed.

## 3. Research Health

Research Health tracks the state of project hypotheses:

- **active hypotheses**: hypotheses currently authorized for evidence
  collection or evaluation;
- **supported hypotheses**: hypotheses whose predefined support conditions
  have passed;
- **rejected hypotheses**: hypotheses whose predefined rejection conditions
  have passed;
- **inconclusive hypotheses**: evaluated hypotheses that have not met support
  or rejection conditions and retain an explicit blocker or evidence need.

Counts must be traceable to the governing hypothesis and its latest documented
decision. A hypothesis may have only one current status in a dashboard
snapshot.

## 4. Strategy Health

Strategy Health is reported separately for every strategy and tracks:

- **current stage**: the strategy's current research, paper, proof, scale, or
  paused lifecycle state under approved governance;
- **paper readiness**: whether the strategy is not ready, ready for bounded
  paper work, actively paper trading, or has completed its required paper
  evidence;
- **real-money readiness**: whether real trading is blocked, evidence-gate
  eligible, awaiting approval, approved for a specific license, or paused;
- **last evidence review**: the timestamp and decision reference for the most
  recent formal evidence review.

Readiness fields report authorization state, not confidence or predicted
profit. Strategies must not be combined into one readiness value.

## 5. Trading Quality

Trading Quality tracks, separately by strategy and execution mode:

- **expectancy**;
- **drawdown**;
- **trade count**;
- **paper/live status**.

Every value must identify its measurement window, cost assumptions, and source
evidence. Paper and live results must remain separated. This framework defines
no numeric target or pass threshold.

## 6. Infrastructure Health

Infrastructure Health tracks:

- **uptime**: observed runtime availability over the reported window;
- **restart reliability**: restart attempts, successful recoveries, and
  unresolved recovery failures;
- **duplicate protection**: current protection status and any duplicate-event,
  position, or execution incidents;
- **integrity checks**: latest status of data, state, fingerprint, lineage, and
  reconciliation checks that apply to the system;
- **API health**: availability, errors, stale data, and unresolved source
  failures for required external APIs.

An unresolved integrity failure must remain visible and must not be averaged
away by otherwise healthy infrastructure metrics.

## 7. Business Progress

Business Progress tracks:

- **current capital stage** under `RISK_MANAGEMENT.md`;
- **current trading license level** under `CAPITAL_SCALING.md`;
- **active strategy** receiving the current evidence or engineering priority;
- **next required milestone** that must pass before business progress can
  advance.

Business Progress reports the current governed state. It must not imply that a
future license, capital allocation, or real-money transition is authorized.

## 8. Reporting rules

- use the same KPI definitions for every strategy;
- preserve paper/live, asset, strategy, and evidence-window boundaries;
- link every measured value to reproducible source evidence;
- show unavailable, stale, blocked, paused, and not-applicable states
  explicitly;
- retain the latest formal review reference for readiness and stage changes;
- do not infer health from missing data;
- do not define or change numeric targets in dashboard presentation;
- do not let aggregate metrics hide a mandatory evidence, integrity, risk, or
  shutdown failure.

## 9. Relationship to governance

`PROJECT_STATE.md` remains the project memory and current narrative state.
`DECISIONS.md` remains the durable decision log. `EVIDENCE_GATES.md`,
`RISK_MANAGEMENT.md`, `CAPITAL_SCALING.md`, and
`STRATEGY_SHUTDOWN_POLICY.md` remain authoritative for promotion, capital,
license, and shutdown decisions. The KPI framework reports those decisions; it
does not replace or override them.
