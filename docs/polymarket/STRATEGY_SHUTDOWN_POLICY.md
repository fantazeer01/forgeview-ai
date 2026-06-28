# Polymarket Strategy Shutdown Policy

Status: Active
Version: v1
Last updated: June 28, 2026
Authority: CEO-approved shutdown and pause policy for every future ForgeViewAI
trading strategy

## 1. Purpose and scope

This document defines when ForgeViewAI must automatically stop or pause a
strategy. It applies equally to:

- Repricing;
- Wallet Intelligence;
- any future Polymarket strategy.

This policy defines governance only. It does not implement execution, alter
detector or strategy logic, change frozen parameters, or tune thresholds.

## 2. Continuous permission to trade

No strategy is permanent. Every strategy must continuously re-earn permission
to trade by maintaining its approved evidence, risk, execution, and integrity
conditions.

Past promotion, historical profitability, or current license level does not
grant indefinite trading permission. If a mandatory condition ceases to hold,
the strategy must pause automatically.

## 3. Automatic pause conditions

Automatic pause conditions include:

- mandatory evidence gates no longer satisfied;
- sustained negative expectancy;
- drawdown exceeding predefined limits;
- abnormal execution behavior;
- infrastructure integrity failures;
- repeated restart failures;
- API instability;
- duplicate execution risk;
- corrupted data;
- missing critical market data.

Existing approved thresholds remain unchanged. This document creates no new
numeric threshold.

## 4. Emergency stop

Every future trading system must support an immediate global trading stop. The
global stop must prevent further automated trading activity and invoke the
system's predefined safe shutdown behavior.

Emergency-stop authority is a risk control, not permission for discretionary
manual trade opening, closing, or strategy modification.

## 5. State after shutdown

A paused real-money strategy returns to **Trading License Level 1 - Paper
Trading**. It may collect new automated paper evidence but may not place a
real-money trade.

The strategy remains in paper trading until new reproducible evidence supports
promotion again under `EVIDENCE_GATES.md`, `CAPITAL_SCALING.md`, and
`RISK_MANAGEMENT.md`.

## 6. Resumption policy

No strategy may resume real-money trading automatically after a shutdown. A
documented review is required. The review must identify the shutdown cause,
confirm corrective evidence, verify that every applicable mandatory gate has
passed again, and record the resulting decision.

Resumption must follow the normal promotion and approval process. A previous
license or approval cannot bypass the new review.

## 7. Strategy-agnostic enforcement

Shutdown decisions are strategy agnostic. Repricing, Wallet Intelligence, and
future strategies receive no exception because of profitability history,
engineering investment, confidence, or proximity to the $10,000 objective.

## 8. Long-term principle

Capital preservation is more important than continuous trading. ForgeViewAI
prefers missing opportunities over accepting uncontrolled risk.
