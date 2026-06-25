# Current Status: ForgeViewAI

Last updated: 2026-06-15.

## Source Of Truth

Live Git repository:

```text
D:\ForgeViewAI
```

Project memory location:

```text
D:\ForgeViewAI\ForgeViewAIDocs\ProjectMemory
```

`output/archive/` is backup and reference-only. It is not the live source.

## Live Repository Structure

```text
D:\ForgeViewAI
  Exports/
  ForgeViewAIn8n/
  content/config/
  ForgeViewAIDocs/
  output/archive/
  output/media/videos/
  Logs/
  .gitignore
```

Directory roles:

- `automation/`: exported workflow files, bridge scripts, tunnel docs, upload scripts, and runtime helper files.
- `ForgeViewAIn8n/`: live n8n workflow export library for ForgeViewAI content/video automation.
- `content/config/`: local config area for OpenAI, Telegram, YouTube, bridge, and provider settings. Treat real config files as private.
- `ForgeViewAIDocs/`: live documentation area, including ProjectMemory.
- `output/archive/`: backup/reference-only archive. Do not treat as live source.
- `output/media/videos/`: generated video outputs. Do not commit generated media unless explicitly reviewed and requested.
- `Logs/`: runtime/e2e logs and generated status artifacts. Do not commit by default.

## Actual Workflow Index

Latest detected Content Machine workflow:

```text
ForgeViewAIn8n\ForgeViewAI Unified Content Machine v14.2 - Sales Routing Stability Fix.json
```

Detected workflow lineage includes v8 through v14.2 plus:

```text
ForgeViewAIn8n\ForgeViewAI YouTube Shorts Upload - Telegram Drafts.json
```

Current branch/status notes from repository audit:

- MP4 branch status: FAIL, bridge URL not configured.
- Telegram post: PASS.
- X draft: PASS.
- Shorts draft: PASS.

Runtime artifact detected:

```text
Logs\e2e_v14_2_real_run_20260615_220516.json
```

## Trading Export Index

Latest detected Futures export:

```text
Exports\BTC Futures Paper Bot - v24 ANTI LATE LONG.json
```

Other detected live Futures export:

```text
Exports\BTC Futures Paper Bot - v22 QUALITY FILTERS.json
```

Clarification needed:

- Futures v22/v23 status must be clarified by filename and actual release intent.
- Existing memory previously referenced `v22 EXIT SAFETY`, but live filename says `v22 QUALITY FILTERS`.
- Futures v23 was detected in backup, not live exports.

Spot status:

- Spot v88 was detected in `output/archive/`, not in live `automation/`.
- Spot v88 is backup-only unless confirmed live by the user or by a future inventory task.
- Do not assume Spot v88 is deployed or live.

## Content And Video State

The old `growth/content-machine-v2` path belongs to the archived `forgeview-ai-main` structure and should not be treated as live.

Live content/video automation is now centered around:

- `ForgeViewAIn8n/` workflow exports;
- `content/config/` local configs;
- `Exports/forgeview_local_bridge.py`;
- `Exports/upload_short_to_youtube.py`;
- `output/media/videos/short.mp4`;
- `Logs/` e2e outputs.

The latest live Content Machine is v14.2, not v2.

## Runtime Unknowns

The following are currently unknown and must be verified before claiming deployment readiness:

- active n8n workflow unknown;
- Telegram webhook status unknown;
- bridge/tunnel URL unknown;
- YouTube upload credentials/status unknown;
- deployed workflow unknown.

Do not infer these from file presence alone.

## Git And Tooling State

The live repo has a `.git` directory at:

```text
D:\ForgeViewAI\.git
```

In the current Codex PowerShell environment, `git` was not available through `git` or `where.exe git` during prior checks. Git status, branch, remote, commit, and push state therefore remain unverified from this environment.

## Security And Generated Files

`.gitignore` excludes local secrets, config files, generated media, logs, runtime responses, cache files, virtualenvs, and work/output directories.

Never commit:

- real token/config/client secret files;
- generated videos;
- logs;
- generated frames;
- runtime API responses;
- cache or virtualenv artifacts.

Only commit explicit reviewed files.

## Known Problems

- Project memory was originally written from an older `forgeview-ai-main` structure and has now been updated to live repo structure.
- Active deployed n8n workflow is unknown.
- Bridge/tunnel URL is not configured for the MP4 branch.
- YouTube upload credential/status is unknown.
- Telegram webhook status is unknown.
- Futures v22/v23 naming/status needs clarification.
- Spot v88 is backup-only unless confirmed live.
- Git status cannot currently be checked from this environment because `git` is unavailable.

