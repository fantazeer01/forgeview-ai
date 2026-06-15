# Next Objectives: ForgeViewAI

## Priority 1: Complete Live Repo Inventory/Status Update

Why:

Project memory previously described the archived `forgeview-ai-main` structure. The live repository is `D:\ForgeViewAI`, with different live paths and newer workflow exports.

Tasks:

- verify all live top-level directories;
- document active vs backup/reference-only areas;
- create or update a live workflow index;
- create or update a live trading export index;
- confirm which files are generated/runtime outputs;
- update `CURRENT_STATUS.md` after any new verified facts.

Acceptance criteria:

- `D:\ForgeViewAI` is documented as the live repo;
- `ForgeViewAIBackup/` is documented as backup/reference-only;
- Content Machine v14.2 is documented as latest detected workflow;
- Futures v24 is documented as latest detected Futures export;
- Spot v88 is documented as backup-only unless confirmed live.

## Priority 2: Verify Active Deployed n8n Workflow

Why:

The repository contains many workflow exports, but active deployment cannot be inferred from files alone.

Tasks:

- identify active n8n workflow name/version;
- verify whether v14.2 is deployed or only exported;
- verify Telegram webhook status;
- verify bridge/tunnel URL status;
- verify YouTube upload credential/status without exposing secrets;
- document deployed workflow status.

Acceptance criteria:

- active n8n workflow is known or explicitly marked inactive/unknown after attempted verification;
- Telegram webhook status is known;
- bridge/tunnel URL is known or documented as missing;
- YouTube upload status is known without committing secrets.

## Priority 3: Connect GitHub Push Safely

Why:

The live repo has `.git`, but current Codex PowerShell environment could not find `git`. Safe commit/push requires verified Git tooling and careful staging.

Tasks:

- make Git command available or use an approved GitHub workflow/tool;
- run `git status`;
- identify tracked/untracked sensitive files;
- verify `.gitignore` is protecting local config, logs, videos, generated outputs, cache, and virtualenvs;
- prepare exact safe staging commands for explicit reviewed files only.

Acceptance criteria:

- `git status` can be checked;
- no secrets are staged;
- no videos/logs/generated files are staged by default;
- push happens only after explicit user request.

## Priority 4: Resume Sales/Content Loop

Why:

Once live runtime status is clear, ForgeViewAI should return to publishing useful content and generating conversations.

Tasks:

- use the latest Content Machine line, not old `growth/content-machine-v2` paths;
- publish or prepare Telegram posts;
- prepare X drafts;
- prepare Shorts drafts;
- keep MP4/video branch optional until bridge URL is configured;
- include clear sales or conversation CTA when relevant.

Acceptance criteria:

- Telegram post path remains PASS;
- X draft path remains PASS;
- Shorts draft path remains PASS;
- MP4 branch is fixed or clearly documented as blocked;
- content does not claim fake metrics or guaranteed trading profit.

## Priority 5: Clarify Trading Export Status

Why:

Trading export state is currently ambiguous across live `Exports/` and `ForgeViewAIBackup/`.

Tasks:

- confirm whether `BTC Futures Paper Bot - v24 ANTI LATE LONG.json` is current intended live Futures version;
- clarify status of Futures v22/v23 by filename and release intent;
- confirm whether Spot v88 should be restored to live exports or remain backup-only;
- avoid trading edits unless the task explicitly says trading mode.

Acceptance criteria:

- latest intended Futures version is known;
- Spot live status is known;
- backup-only exports are not confused with live exports.

## Operating Reminder

- Work from `D:\ForgeViewAI`.
- Read ProjectMemory first.
- Do not edit workflow JSON unless task explicitly says workflow mode.
- Do not edit trading bots unless task explicitly says trading mode.
- Do not treat `ForgeViewAIBackup/` as live source.
- Do not commit tokens, real config files, videos, logs, generated frames, or runtime outputs.
- After substantial work, update `CURRENT_STATUS.md` and this file if priorities changed.

