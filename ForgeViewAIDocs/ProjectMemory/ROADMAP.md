# ForgeViewAI Roadmap

## Strategic Direction

ForgeViewAI should develop as a Telegram-first AI automation business, using the trading bots as both real operating infrastructure and high-quality source material for lessons, content, diagnostics, and future products.

The roadmap is ordered by ROI:

1. prove demand with conversations and small paid offers;
2. publish useful content from real ForgeView lessons;
3. automate the repeated parts of the growth loop;
4. keep trading bots safe, observable, and versioned;
5. improve trading strategy only after validation infrastructure is stronger.

## Stage 1: Project Memory and Operating Clarity

Status: In progress.

Goal:

Make future work consistent across Codex sessions and prevent random task selection.

Deliverables:

- CEO directive.
- Current status.
- Decision rules.
- Roadmap.
- Next objectives.
- clear priority between sales, audience, automation, and trading.

Success criteria:

- a future session can choose the next task without re-discovering project intent;
- docs do not conflict on mission, priorities, or trading safety rules;
- trading bots and workflow JSON are not modified during documentation-only work.

## Stage 2: Manual Growth Loop

Status: Ready.

Goal:

Get real market feedback before building heavier SaaS infrastructure.

Deliverables:

- publish ready MAP offer posts from `growth/lead-system-mvp/content_queue_map.csv`;
- start 10 ForgeView Automation Map conversations;
- deliver 10 free Automation Maps manually;
- offer the $29 Automation Audit when relevant;
- track every lead, problem, map, and outcome.

Success criteria:

- 10 real workflow problems collected;
- at least 3 follow-up conversations;
- at least 1 paid Automation Audit attempt;
- repeated customer problems identified.

## Stage 3: Content Machine Execution

Status: Prepared, not deployed.

Goal:

Turn internal ForgeView work into useful public lessons.

Deliverables:

- publish content using Content Machine v2 rules;
- reuse trading bot bugs, automation mistakes, n8n lessons, Telegram lessons, and lead-system lessons;
- render short videos locally when useful;
- keep events as context, never as hooks.

Success criteria:

- posts lead with useful lessons rather than internal setup updates;
- no fake metrics, hype, or guaranteed trading profit claims;
- content creates replies, DMs, or MAP requests.

## Stage 4: Growth Automation MVP

Status: Proposed.

Goal:

Automate the highest-friction parts of the manual growth loop after the loop is proven.

Candidate workflows:

- Telegram lead intake bot for MAP requests;
- manual approval content publisher;
- lead tracker update workflow;
- follow-up reminder workflow;
- Automation Map draft generator;
- daily BTC digest workflow for useful market content.

Constraints:

- do not overbuild before conversations exist;
- keep a manual approval step for public publishing;
- do not connect growth workflows to trading state unless explicitly designed and verified.

## Stage 5: Trading Bot Stability and Imports

Status: In progress.

Goal:

Make existing trading workflows safer and easier to operate.

Deliverables:

- import Spot v88 STABILITY FIX into n8n;
- import Futures v22 EXIT SAFETY into n8n;
- verify Telegram webhooks and button commands;
- run controlled paper/testnet simulations;
- document import results and version history.

Success criteria:

- Spot failed orders do not create phantom internal positions;
- Spot close uses existing `position.qty`;
- Futures cooldowns block entries but never exits;
- Telegram controls reflect actual bot state.

## Stage 6: Bot Observability and Diagnostics

Status: Proposed.

Goal:

Make bot decisions explainable from Telegram without opening n8n.

Deliverables:

- STATUS shows long score, short score, trend, cooldown, and current block reason;
- HOLD messages explain whether pause, cooldown, low score, missing data, or quality filter blocked action;
- LAST ERROR includes timestamp, context, and latest API failure;
- news fields are surfaced consistently.

Success criteria:

- operator can understand why the bot traded or did not trade from Telegram;
- diagnostics do not change scoring, thresholds, or risk parameters.

## Stage 7: Strategy Quality Improvements

Status: Later.

Goal:

Improve trading signal quality without compromising safety.

Candidate work:

- completed candle handling decision;
- multi-timeframe aggregation alignment;
- long-side Futures quality filters;
- Spot early exit scoring;
- structured trade journal output;
- controlled simulations before threshold changes.

Constraints:

- do not change thresholds without evidence;
- do not mix safety fixes and strategy changes;
- keep every release small and versioned.

## Stage 8: Product Packaging

Status: Future.

Goal:

Turn repeated ForgeView patterns into paid offers and eventually productized services.

Candidate offers:

- ForgeView Automation Audit;
- Telegram automation setup service;
- n8n workflow template packs;
- trading bot diagnostics checklist;
- managed Telegram alert workflows;
- creator or small business automation console.

Required foundation:

- customer-safe credential handling;
- onboarding docs;
- deployment checklist;
- support process;
- pricing and packaging;
- proof from real conversations.
