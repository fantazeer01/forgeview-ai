# CEO Directive: ForgeViewAI

## Live Repository

The live ForgeViewAI Git repository is:

```text
D:\ForgeViewAI
```

All autonomous Codex work must treat this repository as the source of truth unless the user explicitly says otherwise.

`output/archive/` is backup and reference-only. It is not the live source. Do not create new work there, do not treat files inside it as current, and do not copy from it into live areas unless the user explicitly requests a recovery or comparison task.

## Mission

ForgeViewAI exists to turn real operational work into practical AI-first automation products.

The project compounds through:

- AI-assisted content and video automation;
- Telegram-first publishing and sales workflows;
- safer trading workflow research and diagnostics;
- small paid automation offers that can become repeatable products.

ForgeViewAI is not a hype project, a fake-metric growth project, or a promise of guaranteed trading profit. It is an operator system: build useful workflows, verify them, document them, publish useful lessons, and turn repeated patterns into products.

## Project Priorities

Default priority order:

1. Revenue, qualified conversations, and usable offers.
2. Audience growth through useful lessons and working content pipelines.
3. Automation that reduces repeated manual work.
4. Workflow reliability, runtime observability, and deployment clarity.
5. Trading bot safety and diagnostics.
6. Trading strategy experimentation only after safety and validation.

Trading systems matter, but they must not consume all project energy before the business loop and live content engine are operational.

## Task Selection Rules

Prefer tasks that:

- clarify the live repository state;
- improve or verify deployed n8n/content workflows;
- create publishable content or sales material;
- generate real conversations with potential users;
- reduce manual operating load;
- improve bot safety, diagnostics, or verification without changing strategy;
- produce reusable documentation, templates, prompts, reports, or checklists.

Avoid tasks that:

- edit files in `output/archive/` as if they are live;
- change workflow JSON unless the task explicitly says workflow mode;
- change trading bots unless the task explicitly says trading mode;
- change trading thresholds without simulation or backtest evidence;
- mix safety fixes and strategy changes in one release;
- optimize internal structure without operational or commercial value;
- add hidden complexity to n8n workflows.

## AI-First Strategy

AI should act as an operating layer for:

- content transformation from real project events into useful lessons;
- Telegram posts, X drafts, shorts drafts, and sales routing;
- automation maps, audits, prompts, and checklists;
- workflow diagnostics and operator summaries;
- project memory and task selection;
- rapid prototypes where results can be inspected.

AI must not:

- invent fake performance metrics;
- make guaranteed profit claims;
- hide unverified trading risk;
- replace verification of workflow behavior;
- publish content with no practical takeaway;
- expose tokens, client secrets, or private config values.

Core loop:

```text
Real work -> verified lesson -> content -> conversation -> small offer -> repeatable automation product
```

## Budget Constraints

- Prefer existing local tools, n8n, Telegram, simple files, and current APIs.
- Do not buy new SaaS tools until a low-cost MVP proves demand.
- Treat paid AI/image/video generation as optional unless it directly supports a revenue or publishing experiment.
- Keep workflow versions small enough to inspect manually.
- Protect attention budget: one session should usually deliver one concrete artifact.

## Security And Commit Policy

- Never commit tokens.
- Never commit real config files, client secrets, OAuth tokens, or private credential files.
- Never commit generated videos, runtime logs, generated frames, cache files, `__pycache__`, `.venv`, or temporary outputs.
- Respect `.gitignore`.
- Only commit explicit reviewed files.
- Do not run `git add`, `git commit`, or `git push` unless the user explicitly requests that action.

## Autonomous Codex Operating Rules

- Always read `ForgeViewAIDocs/ProjectMemory/` first.
- Never treat `output/archive/` as live source.
- Never edit trading bots unless the task explicitly says trading mode.
- Never edit n8n workflow JSON unless the task explicitly says workflow mode.
- Never edit runtime secrets or real config files.
- After each substantial task, update `CURRENT_STATUS.md` and `NEXT_OBJECTIVES.md` if project state or next priorities changed.
- If live deployment status is unknown, say unknown; do not infer.

## Non-Negotiable Trading Rules

- Never let entry cooldowns block exits.
- Never commit position state before execution confirmation.
- Keep paper, testnet, and production behavior separate.
- Do not change scoring thresholds without a documented validation reason.
- Do not mix safety, strategy, and UX changes in one bot release.
- Treat every bot JSON export as a deployable artifact.

