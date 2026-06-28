# Polymarket Capital Scaling and Trading License Levels

Status: Active
Version: v1
Last updated: June 28, 2026
Authority: CEO-approved capital scaling policy for every future ForgeViewAI
Polymarket strategy

## 1. Objective and scope

ForgeViewAI's goal is to earn its first $10,000 on Polymarket BTC, ETH, and
SOL five-minute Up/Down markets using whichever strategy produces reproducible
evidence.

Capital scaling must be automatic, conservative, evidence-based, and free from
emotional or discretionary overrides. This policy applies to Repricing, Wallet
Intelligence, and every future strategy. It defines authorization levels only;
it does not authorize real-money execution or change any current strategy,
detector, or frozen parameter.

## 2. Relationship to capital stages

Trading License Levels refine the broader Capital Stages in
`RISK_MANAGEMENT.md`:

| Capital stage | Trading License Levels |
|---|---|
| Capital Stage 0 - Research | Levels 0-1 |
| Capital Stage 1 - Proof | Level 2 |
| Capital Stage 2 - Scale | Levels 3-5 |

No license level may bypass the risk controls, 1% default per-trade cap, stop
conditions, or change-control requirements in `RISK_MANAGEMENT.md`.

## 3. Trading License Levels

### Level 0 - Research

- real capital: $0;
- offline research only;
- paper execution is not required;
- no real-money execution.

### Level 1 - Paper Trading

- real capital: $0;
- automated paper trades only;
- required before any real-money license level;
- paper results must provide the evidence used to define promotion thresholds.

### Level 2 - Micro Real Trading

- approximate position size: $3-$5 per trade, or the platform minimum if
  higher;
- purpose: verify real execution behavior, not maximize profit;
- must respect the 1% per-trade risk cap where possible;
- a platform-minimum exception above 1% requires explicit approval under
  `RISK_MANAGEMENT.md`.

### Level 3 - Small Real Trading

- approximate position size: $10 per trade;
- allowed only after Level 2 demonstrates stable behavior;
- remains subject to all promotion, demotion, and stop rules.

### Level 4 - Controlled Real Trading

- approximate position size: $25 per trade;
- allowed only after stable positive real-trade evidence;
- remains subject to all promotion, demotion, and stop rules.

### Level 5 - Normal Real Trading

- approximate position size: $50 per trade;
- allowed only after substantial evidence and a low infrastructure error rate;
- remains subject to all promotion, demotion, and stop rules.

Future higher levels require a new documented CEO decision. They are not
implicitly authorized by success at Level 5.

## 4. Promotion rules

Promotion is automatic only after every predefined evidence gate for the next
level is satisfied. Promotion gates must include at least:

- a minimum number of completed trades;
- positive expectancy;
- acceptable drawdown;
- no critical infrastructure failures;
- no duplicate-position incidents;
- no restart recovery failures;
- stable execution behavior.

Specific numeric thresholds may be defined only after relevant paper-trading
statistics are available. They must be predefined, documented, and validated
before use. The first transition from Level 1 to Level 2 additionally requires
documented CEO approval. Evidence satisfaction permits promotion; it does not
require promotion when a separate risk review rejects the transition.

## 5. Demotion and pause rules

The system must automatically reduce its license level or pause new trading
when quality degrades. Triggers include:

- daily loss limit reached;
- consecutive losing trade limit reached;
- expectancy turning negative over a predefined window;
- drawdown exceeding the allowed range;
- infrastructure integrity failure;
- API or data reliability failure;
- unexpected execution behavior;
- manual emergency stop.

The demotion target, pause behavior, open-position handling, and recovery gates
must be predefined before a real-money level is authorized. A manual emergency
stop pauses the automated system; it does not authorize discretionary manual
trade opening or closing.

## 6. No emotional scaling

Position size must never increase because of:

- a feeling of confidence;
- a recent lucky streak;
- impatience;
- a desire to reach $10,000 faster;
- a manual override without a documented decision.

Every scaling change must follow the evidence gates and change-control process.

## 7. Strategy-agnostic application

A strategy earns capital allocation only through evidence. The same license
ladder and risk gates apply to:

- Repricing;
- Wallet Intelligence;
- any future Polymarket strategy.

No strategy receives a higher level because of sunk cost, preference, or prior
engineering investment.

## 8. Current authorization

Real-money authorization remains absent. Levels 0 and 1 carry $0 real capital;
Levels 2-5 require future evidence, completed gates, and the approvals defined
above. Recording this policy does not promote any strategy.
