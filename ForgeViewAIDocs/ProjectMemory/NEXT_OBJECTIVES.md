# Next Objectives: ForgeViewAI

## Objective 1: Launch the Manual MAP Loop

Why:

This is the highest-ROI next task because it can create conversations, customer insight, content, and a paid offer without changing code or trading bots.

Tasks:

- publish or send the ready MAP offer posts;
- track each lead manually;
- ask the 4 intake questions from `growth/lead-system-mvp/TELEGRAM_DM_WORKFLOW.md`;
- deliver a free Automation Map using `AUTOMATION_MAP_TEMPLATE.md`;
- offer the $29 Automation Audit where relevant;
- record outcomes.

Acceptance criteria:

- 10 MAP conversations started;
- 10 workflow problems logged;
- 10 free maps delivered or clearly marked incomplete;
- 3 follow-up conversations attempted;
- 1 paid Automation Audit attempt made.

## Objective 2: Create a Lead Tracking Document

Why:

The lead-system MVP currently defines the tracking fields but does not yet have a dedicated tracker.

Suggested output:

```text
growth/lead-system-mvp/LEAD_TRACKER.md
```

Fields:

- lead;
- platform;
- repeated task;
- tools used now;
- desired output;
- free MAP delivered;
- paid audit offered;
- outcome;
- next follow-up date.

Acceptance criteria:

- tracker exists;
- it supports the first 10 conversations;
- it does not require new SaaS.

## Objective 3: Publish From Content Machine v2

Why:

The prompts and content queue are ready. The next value comes from distribution, not more internal setup.

Tasks:

- choose 3 lessons from existing ForgeView work;
- generate Telegram, X, and Shorts drafts using `growth/content-machine-v2/PROMPTS.md`;
- avoid internal setup as the hook;
- use trading bot bugs, automation lessons, or lead-system lessons as proof;
- publish manually or mark drafts ready for manual publishing.

Acceptance criteria:

- 3 useful posts drafted;
- each post leads with a mistake, bug, lesson, insight, or principle;
- no fake metrics or guaranteed trading profit claims;
- each post includes a MAP call to action when relevant.

## Objective 4: Verify Spot v88 Import

Why:

Spot v88 addresses a critical state-safety issue, but import behavior still needs validation.

Tasks:

- import Spot v88 into n8n;
- confirm workflow name;
- verify Telegram webhook URL;
- run test executions with no open position and simulated open position;
- confirm failed order does not mutate `state.position`;
- confirm confirmed order commits planned position.

Acceptance criteria:

- verification report exists;
- no scoring, threshold, or risk parameter changes;
- any discovered issues are listed by severity.

## Objective 5: Create n8n Import Checklist

Why:

Workflow import is repeated and risky. A checklist reduces operational mistakes.

Suggested output:

```text
docs/N8N_IMPORT_CHECKLIST.md
```

Tasks:

- document import steps;
- include workflow name verification;
- include webhook, Telegram token, chat ID, credential, schedule, and manual execution checks;
- include state reset process;
- include post-import Telegram callback test.

Acceptance criteria:

- checklist is usable for Spot, Futures, and growth workflows;
- no workflow JSON files are changed.

## Objective 6: Add Telegram Diagnostics Without Strategy Changes

Why:

Diagnostics improve trust and speed up debugging while preserving strategy behavior.

Tasks:

- add displayed fields only in a future workflow version;
- show scores, trend, cooldown, and block reason;
- improve LAST ERROR context;
- surface news fields consistently.

Acceptance criteria:

- new versioned workflow export;
- version history updated;
- before/after message examples;
- no scoring, threshold, or risk changes.

## Highest-ROI Next Task

Start with Objective 1:

```text
Launch the manual ForgeView Automation Map loop and track the first 10 conversations.
```

Reason:

It is the fastest path to demand validation, audience signal, paid offer testing, and reusable product insight. It also does not require code, workflow, or trading bot changes.

