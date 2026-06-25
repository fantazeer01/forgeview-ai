# Decision Rules: Maximum ROI

## Source Of Truth

Make decisions from the live repository:

```text
D:\ForgeViewAI
```

Never treat `output/archive/` as live source. Use it only for recovery, comparison, or historical reference when explicitly requested.

## ROI Definition

For ForgeViewAI, ROI means the best combination of:

- revenue potential;
- real user conversations;
- audience growth;
- working content automation;
- reduced manual work;
- lower operational risk;
- reusable assets for future products.

The best task is not always the most technical task. The best task is the one that most quickly moves ForgeViewAI toward a repeatable business loop while preserving workflow and trading safety.

## Priority Order

Default priority:

1. Clarify live repo, runtime, and deployment state when unknowns block safe work.
2. Sales, qualified conversations, and offers.
3. Audience growth through useful content.
4. Automation that makes sales, content, and operations easier.
5. Workflow reliability and observability.
6. Trading bot safety and diagnostics.
7. Trading strategy improvement.

## Current High-ROI Context

The latest detected Content Machine is:

```text
ForgeViewAIn8n\ForgeViewAI Unified Content Machine v14.2 - Sales Routing Stability Fix.json
```

Known branch results:

- MP4 branch status: FAIL, bridge URL not configured.
- Telegram post: PASS.
- X draft: PASS.
- Shorts draft: PASS.

Therefore, before expanding the content machine, prefer tasks that verify deployment/runtime state and fix the blocked MP4/bridge path only when the user explicitly requests workflow/runtime work.

## Task Selection Score

Score each candidate from 0 to 3:

```text
Live-state clarity:
Revenue impact:
Audience impact:
Automation leverage:
Risk reduction:
Speed to ship:
Reusability:
```

Choose the highest total score.

Tie-breakers:

1. Choose the task that removes a live deployment unknown.
2. Choose the task that can create an external artifact today.
3. Choose the task that supports real sales or audience feedback.
4. Choose the safer task if workflow JSON or trading behavior is involved.

## Sales vs Audience vs Automation vs Trading

Sales beats audience when:

- there is a clear offer;
- a user or lead can be contacted now;
- the task can create a paid Automation Audit, customer interview, or direct reply.

Audience beats automation when:

- content outputs are already generated but not published;
- the project needs distribution more than new tooling;
- a useful lesson can be published from existing work.

Automation beats manual sales when:

- the same manual task is repeated often;
- the automation directly supports posting, intake, lead tracking, delivery, upload, or follow-up;
- the MVP is small and low-cost.

Workflow reliability beats expansion when:

- active n8n workflow is unknown;
- webhook status is unknown;
- bridge/tunnel URL is unknown;
- YouTube upload status is unknown;
- deployment cannot be verified from files alone.

Trading safety beats growth when:

- a bot is about to be imported, activated, or used;
- there is risk of phantom positions, blocked exits, incorrect state, or misleading status;
- the task explicitly says trading mode.

Trading strategy improvement comes last unless:

- safety is already verified;
- the change is backed by simulation or backtest;
- it is isolated from safety and UX changes;
- it has clear version history and rollback path.

## Forbidden Decision Patterns

Do not:

- create new live work under `output/archive/`;
- follow old `growth/`, `spot-bot/`, or `docs/` paths unless intentionally inspecting backup archives;
- edit workflow JSON unless the task explicitly says workflow mode;
- edit trading bots unless the task explicitly says trading mode;
- commit real config files, tokens, videos, logs, generated frames, or runtime outputs;
- build SaaS infrastructure before live workflow status and sales loop are clear.

## Default Next Best Action

If no more specific task is given, the default next action is:

```text
Complete live repo inventory/status update, then verify active deployed n8n workflow.
```

Only after those are clear should Codex resume the sales/content loop.

