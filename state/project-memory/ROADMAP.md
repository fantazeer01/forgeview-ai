# ForgeViewAI Roadmap

## Strategic Direction

ForgeViewAI should develop as a Telegram-first AI automation and content operations business, supported by n8n workflows, local bridge/runtime tools, and carefully documented trading workflow research.

Live repository:

```text
D:\ForgeViewAI
```

`output/archive/` is backup/reference-only and is not a live development area.

## Roadmap Order

1. Make live repo and deployment status accurate.
2. Verify active n8n workflow and runtime integrations.
3. Restore safe GitHub push/commit workflow.
4. Resume sales/content loop.
5. Improve content/video automation reliability.
6. Clarify and verify trading exports.
7. Package repeatable offers and products.

## Stage 1: Live Repository Memory And Inventory

Status: In progress.

Goal:

Make ProjectMemory match the actual live repository, not the archived `forgeview-ai-main` structure.

Deliverables:

- live repo path documented as `D:\ForgeViewAI`;
- live repository structure documented;
- `output/archive/` marked backup/reference-only;
- workflow index updated to Content Machine v14.2;
- trading export index updated to Futures v24 and Spot v88 unknown/backup-only;
- runtime unknowns listed;
- security and commit policy documented.

Success criteria:

- Codex no longer creates or updates old `growth/`, `spot-bot/`, or root `docs/` paths as live paths;
- future tasks can identify live docs, workflow exports, content configs, videos, logs, and backup areas;
- no code, workflow JSON, or trading bots are changed during memory-only work.

## Stage 2: Verify Active Deployment State

Status: Next.

Goal:

Determine what is actually deployed and active, because file presence is not enough.

Required checks:

- active n8n workflow unknown;
- Telegram webhook status unknown;
- bridge/tunnel URL unknown;
- YouTube upload credentials/status unknown;
- deployed workflow unknown.

Success criteria:

- one document records active workflow name/version;
- Telegram webhook and posting path are verified or clearly marked inactive;
- bridge/tunnel URL is configured or the MP4 branch remains documented as blocked;
- YouTube upload status is verified without exposing secrets.

## Stage 3: GitHub And Commit Safety

Status: Blocked by local tooling until Git access is available.

Goal:

Make it safe to commit and push explicit reviewed documentation/workflow changes.

Known issue:

- `git` was not available in the current PowerShell environment during prior checks.

Deliverables:

- confirm Git command availability;
- run `git status`;
- identify tracked/untracked sensitive files;
- stage only explicit reviewed files;
- never stage secrets, videos, logs, generated frames, cache, or runtime outputs.

Success criteria:

- Git status is known;
- safe commit scope can be named exactly;
- push is performed only when explicitly requested.

## Stage 4: Sales And Content Loop

Status: Resume after live runtime state is clear.

Goal:

Use the working content machine and Telegram-first distribution to create attention, conversations, and offers.

Deliverables:

- publish useful Telegram posts;
- create X drafts;
- create Shorts drafts;
- route useful lessons into sales conversations;
- revive or recreate the Automation Map / Automation Audit loop in live paths if still needed.

Current detected output status:

- Telegram post: PASS.
- X draft: PASS.
- Shorts draft: PASS.
- MP4 branch: FAIL, bridge URL not configured.

Success criteria:

- content output is published or ready for manual approval;
- sales CTA is clear;
- runtime failures are logged and do not block text-only content.

## Stage 5: Content Machine Reliability

Status: Proposed.

Goal:

Improve reliability of the latest workflow line without randomly editing old versions.

Latest detected workflow:

```text
ForgeViewAIn8n\ForgeViewAI Unified Content Machine v14.2 - Sales Routing Stability Fix.json
```

Candidate work:

- verify v14.2 deployed vs merely exported;
- fix bridge URL configuration for MP4 path;
- clarify manual vs automatic YouTube upload;
- document expected config files without exposing secrets;
- add operator checklist for running content generation safely.

Constraints:

- do not edit workflow JSON unless the task explicitly says workflow mode;
- do not commit real config/client secret/token files;
- do not commit generated videos/logs by default.

## Stage 6: Trading Export Clarification

Status: Proposed.

Goal:

Clarify which trading exports are live, archived, or backup-only.

Detected live exports:

- `Exports\BTC Futures Paper Bot - v24 ANTI LATE LONG.json`
- `Exports\BTC Futures Paper Bot - v22 QUALITY FILTERS.json`

Detected backup/reference exports:

- Spot v88 in `output/archive/`;
- Futures v23 in `output/archive/`.

Required decisions:

- confirm whether Futures v24 is the current intended live version;
- clarify what happened to v22/v23 naming and status;
- confirm whether Spot v88 should be restored to live `automation/` or remain backup-only.

Constraints:

- do not edit trading bots unless the task explicitly says trading mode;
- do not change strategy thresholds without validation evidence.

## Stage 7: Product Packaging

Status: Future.

Goal:

Turn repeated ForgeViewAI patterns into paid offers and eventually productized services.

Candidate offers:

- ForgeView Automation Audit;
- Telegram content automation setup;
- n8n workflow template packs;
- YouTube Shorts automation setup;
- trading bot diagnostics checklist;
- managed Telegram alert workflows.

Required foundation:

- verified active workflows;
- safe credential handling;
- deployment checklist;
- support process;
- pricing and packaging;
- proof from real conversations.

