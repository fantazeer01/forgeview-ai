# Decision Rules: Maximum ROI

## ROI Definition

For ForgeViewAI, ROI means the best combination of:

- revenue potential;
- real user conversations;
- audience growth;
- reduced manual work;
- lower operational risk;
- reusable assets for future products.

The best task is not always the most technical task. The best task is the one that most quickly moves ForgeViewAI toward a repeatable business loop while preserving trading safety.

## Priority Order

Default priority:

1. Sales and qualified conversations.
2. Audience growth through useful content.
3. Automation that makes sales, content, or operations easier.
4. Trading bot safety and observability.
5. Trading strategy improvement.

Explanation:

- Sales prove demand.
- Audience creates distribution.
- Automation increases output without adding manual load.
- Trading safety protects credibility and capital.
- Strategy changes are valuable only after the system is observable and validated.

## Task Selection Score

Score each candidate from 0 to 3:

```text
Revenue impact:
Audience impact:
Automation leverage:
Risk reduction:
Speed to ship:
Reusability:
```

Choose the highest total score.

Tie-breakers:

1. Choose the task that can create an external artifact today.
2. Choose the task that supports the first 10 real conversations.
3. Choose the task that reduces a known blocker.
4. Choose the safer task if trading behavior is involved.

## Sales vs Audience vs Automation vs Trading

Sales beats audience when:

- there is a clear offer;
- a user or lead can be contacted now;
- the task can create a paid Automation Audit, customer interview, or direct reply.

Audience beats automation when:

- content assets already exist but are not being published;
- the project needs distribution more than internal tooling;
- a useful lesson can be published from existing work.

Automation beats manual sales when:

- the same manual task is repeated often;
- the automation directly supports posting, intake, lead tracking, delivery, or follow-up;
- the MVP is small and low-cost.

Trading safety beats growth when:

- there is a risk of phantom positions, blocked exits, incorrect state, or misleading bot status;
- a bot is about to be imported, activated, or used;
- documentation says a safety fix is unverified.

Trading strategy improvement comes last unless:

- safety is already verified;
- the change is backed by simulation or backtest;
- it is isolated from safety and UX changes;
- it has clear version history and rollback path.

## Default Next Best Action

If there is no urgent bot safety issue, the default highest-ROI action is:

```text
Run the ForgeView Automation Map loop and document the first 10 conversations.
```

Supporting tasks:

- publish ready MAP posts;
- track each lead manually;
- deliver free Automation Maps;
- offer the $29 Automation Audit where relevant;
- turn each real problem into content and product insight.

## Forbidden Decision Patterns

Do not choose a task because it is technically interesting if it does not support the current business loop.

Do not change trading logic to chase performance before:

- imports are verified;
- cooldown and state safety are confirmed;
- Telegram diagnostics are trustworthy;
- trade journal or comparable records exist.

Do not build SaaS infrastructure before:

- at least 10 MAP conversations;
- at least 1 paid Automation Audit attempt;
- a repeated customer problem is visible.

