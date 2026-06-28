# Polymarket Risk Management Principles

Status: Active
Version: v1
Last updated: June 28, 2026
Authority: CEO-approved risk policy for any future ForgeViewAI real-money
Polymarket system

## 1. Objective and scope

ForgeViewAI's business goal is to earn its first $10,000 on Polymarket BTC,
ETH, and SOL five-minute Up/Down markets using whichever strategy produces
reproducible evidence.

This policy applies to every future real-money trading system, including any
system derived from Repricing Research or Wallet Intelligence. It does not
authorize real-money execution. The project is currently in Capital Stage 0,
with zero real-money risk.

## 2. Capital stages

### Capital Stage 0 - Research

- real-money risk is $0;
- permitted work is research, offline testing, deterministic replay, and paper
  trading;
- no real-money execution is permitted.

### Capital Stage 1 - Proof

- begins only after successful paper-trading evidence and explicit approval;
- uses minimal real-money position size;
- initial target size is approximately $3-$5 per trade, or the platform
  minimum if higher, subject to the maximum-risk rule below;
- the goal is execution verification, not profit maximization;
- the stage must test whether real orders, fills, costs, state, and recovery
  behave consistently with paper assumptions.

If the platform minimum exceeds 1% of current trading capital, the system must
remain in paper mode unless use of the smallest allowed size receives explicit
approval.

### Capital Stage 2 - Scale

- begins only after Capital Stage 1 demonstrates stable behavior;
- position size increases gradually under predefined rules;
- scaling decisions must be evidence-based and must not be changed in response
  to emotion or isolated outcomes.

## 3. Maximum risk per trade

No single trade may risk more than 1% of current trading capital, regardless of
signal confidence. Position sizing must use the lower of the strategy's
approved size and the 1% risk ceiling. The sole exception is the platform
minimum described in Capital Stage 1, and it requires explicit approval;
without that approval, the system remains in paper mode.

## 4. Daily and session risk stops

A real-money system must stop opening new trades when any configured stop
condition triggers. Required stop categories are:

- daily loss limit;
- consecutive losing trades limit;
- critical infrastructure error;
- API or market-data failure;
- data consistency failure;
- duplicate-position risk;
- restart recovery failure;
- unexpected order or execution state.

Numeric loss and consecutive-loss thresholds may be defined only after paper
statistics are available. They must be predefined, documented, validated in
paper trading, and approved before Capital Stage 1 begins. Triggered stops fail
closed and require documented recovery criteria before new real-money entries
resume.

## 5. No discretionary manual trading

After an automated strategy is launched:

- no manual trade opening is permitted;
- no manual trade closing is permitted;
- no active parameter may be changed during trading in response to emotion;
- operational shutdown controls may stop the system, but must not become a
  discretionary manual trading path.

Every parameter change requires, in order:

1. a stated hypothesis;
2. a reproducible test;
3. paper-trading validation;
4. a documented decision.

## 6. Automation preference

Manual operating work must be minimized. The target operating model is:

- automated data collection;
- automated signal generation;
- automated paper trading;
- automated statistics;
- automated reporting;
- eventual automated real execution only after evidence and explicit approval
  support it.

Automation must preserve fail-closed behavior, auditability, deterministic
recovery, and human shutdown capability.

## 7. Strategy-agnostic capital allocation

ForgeViewAI is not committed to Repricing, Wallet Intelligence, or any other
named strategy. Engineering priority follows the fastest reproducible,
evidence-backed path toward profitable BTC, ETH, and SOL five-minute trading.

- a branch rejected by evidence may be frozen;
- a branch supported by evidence receives higher engineering priority;
- no branch receives capital because of sunk cost, preference, or narrative;
- all branches must satisfy the same capital-stage and risk controls before
  real-money deployment.

## 8. Change control

Risk limits, capital-stage gates, stop categories, and execution parameters may
change only through a documented governance decision. No research result or
paper result automatically authorizes progression to a higher capital stage.
