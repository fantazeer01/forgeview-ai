# Evidence Gates for Real Trading

Status: Active
Version: v1
Last updated: June 28, 2026
Authority: CEO-approved process for authorization of ForgeViewAI's first
real-money Polymarket trade

## 1. Purpose and scope

This document defines the mandatory process that must be completed before any
ForgeViewAI strategy may execute its first real-money trade. It defines process
only and introduces no new numeric thresholds.

The process applies equally to:

- Repricing;
- Wallet Intelligence;
- any future Polymarket strategy.

It does not authorize real-money execution, alter strategy or detector logic,
change frozen parameters, or tune any threshold.

## 2. Governing rule

No real-money trading is permitted until every predefined mandatory evidence
gate for the candidate strategy has passed. Paper trading must always precede
real trading.

The strategy must remain at Trading License Level 1 or below until this process
is complete. Passing the process makes a strategy eligible for CEO review; it
does not itself authorize promotion to Level 2.

## 3. Gate definition

Before evaluation begins, the candidate strategy's mandatory gate set must be
predefined, documented, and tied to reproducible evidence. Evidence gates may
include, but are not limited to:

- sufficient paper-trade sample;
- positive expectancy;
- acceptable drawdown;
- infrastructure stability;
- deterministic recovery;
- zero unresolved integrity failures;
- reproducible exports;
- successful long-duration runs;
- successful restart tests.

Numeric thresholds may be used only when they already exist in approved
project policy or are defined later through the documented governance process.
This document does not create any numeric threshold.

## 4. Evaluation process

Evidence gates must be evaluated automatically where possible. Each mandatory
gate must have a durable result linked to its source evidence. Any gate that
cannot be evaluated automatically must have an explicit, documented review
result rather than an informal judgment.

A mandatory gate is not satisfied merely because evidence is unavailable,
incomplete, stale, or ambiguous. Until it has passed, it continues to block
real-money promotion.

## 5. Failure behavior

Failure of any mandatory evidence gate blocks promotion to real trading. A
failed, unresolved, or unevaluated mandatory gate cannot be waived by operator
discretion, recent paper performance, strategy confidence, or urgency to reach
the profit target.

The candidate remains in paper trading until the failure is corrected and the
gate is evaluated again from reproducible evidence under the approved process.

## 6. CEO approval boundary

Documented CEO approval is required after every mandatory evidence gate has
passed and before the first real-money transition. CEO approval can never
override a failed, unresolved, or unevaluated mandatory gate.

The required sequence is:

1. paper trading;
2. predefined gate evaluation;
3. every mandatory gate passes;
4. documented CEO approval;
5. separately authorized Level 2 micro real trading.

No later step may be performed early or used to bypass an earlier step.

## 7. Relationship to other policies

`RISK_MANAGEMENT.md` remains authoritative for capital risk, stops, and change
control. `CAPITAL_SCALING.md` remains authoritative for Trading License Levels,
promotion, and demotion. This document defines the evidence prerequisite for
the first transition from Level 1 paper trading to Level 2 micro real trading.
