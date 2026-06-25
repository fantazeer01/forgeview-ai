# Live Repository Inventory: ForgeViewAI

Last updated: 2026-06-15.

Live repository:

```text
D:\ForgeViewAI
```

This inventory is documentation-only. It does not prove deployment status. File presence means an artifact exists locally; it does not prove that n8n, Telegram, bridge/tunnel, YouTube, or trading systems are active.

## Root Structure

| Path | Purpose | Classification | Codex edit policy | Commit policy | Risks |
| --- | --- | --- | --- | --- | --- |
| `.git/` | Git metadata. | runtime/system | Never edit manually. | Never commit directly. | Corrupting this breaks repository history/state. |
| `.gitignore` | Defines ignored secrets, logs, videos, cache, runtime output. | source/config-policy | Editable only in explicit Git/security docs task. | Can commit if reviewed. | Wrong rules can expose secrets or hide source files. |
| `automation/` | Mixed area: trading bot exports, bridge scripts, tunnel docs, YouTube upload helper, runtime logs/responses. | mixed source/export/runtime | Edit docs/scripts only when explicitly requested; do not edit trading JSON unless trading mode. | Commit reviewed docs/scripts/exports only; never commit logs/responses/cache by default. | Contains trading JSON, runtime response JSON, logs, executable scripts. |
| `ForgeViewAIn8n/` | Live n8n workflow export library for Content Machine and upload workflows. | source/export | Do not edit workflow JSON unless task explicitly says workflow mode. | Commit only explicit reviewed workflow exports. | Many historical versions; easy to edit old version or wrong workflow. |
| `content/config/` | Local configs for bridge, OpenAI, Telegram, video provider, YouTube. | runtime/secrets/config | Do not edit unless task explicitly says config/runtime setup. Never print contents. | Never commit real config/token/client secret files. Example files may be committable if scrubbed. | Highest secret exposure risk. |
| `ForgeViewAIDocs/` | Live documentation area. ProjectMemory lives here. | source/docs | Safe for documentation tasks. | Safe to commit explicit reviewed docs. | Docs can become stale and mislead Codex. |
| `output/archive/` | Archived backups and old `forgeview-ai-main` structure. | backup/archive/reference-only | Do not create live work here. Read only for comparison/recovery if explicitly needed. | Do not commit backup contents by default. | Contains old paths, old workflows, virtualenv/cache, possible stale configs/artifacts. |
| `ForgeViewAITrading/` | Trading area placeholder/directory. Currently no files detected in inventory. | unknown/live area | Do not edit unless task explicitly says trading mode. | Commit only explicit reviewed trading docs/exports. | Empty state may hide missing expected source. |
| `output/media/videos/` | Generated video outputs. | generated | Do not edit manually. Regenerate only in video/runtime task. | Never commit by default. | Large binary files and generated artifacts. |
| `Logs/` | Runtime/e2e logs and generated status artifacts. | runtime/generated | Read for diagnostics. Do not edit unless cleaning is explicitly requested. | Never commit by default. | May contain runtime data, API traces, generated outputs. |

## n8n Workflow Index

All files below are in:

```text
ForgeViewAIn8n/
```

Deployment status for all entries is unknown unless explicitly verified in n8n.

| Filename | Version | Purpose | Freshness | Deploy status | Safe to edit |
| --- | --- | --- | --- | --- | --- |
| `ForgeViewAI Unified Content Machine v8 - 6H.json` | v8 | 6-hour content machine line. | old | unknown | No, unless workflow mode and historical edit requested. |
| `ForgeViewAI Unified Content Machine v9 - 6H Full Pipeline.json` | v9 | Full 6-hour pipeline. | old | unknown | No, unless workflow mode and historical edit requested. |
| `ForgeViewAI Unified Content Machine v9.1 - 6H Full Pipeline.json` | v9.1 | Full 6-hour pipeline iteration. | old | unknown | No, unless workflow mode and historical edit requested. |
| `ForgeViewAI Unified Content Machine v9.1 - 6H Manual Shorts.json` | v9.1 | Manual shorts branch. | old | unknown | No, unless workflow mode and historical edit requested. |
| `ForgeViewAI Unified Content Machine v9.2 - 6H Manual Shorts.json` | v9.2 | Manual shorts branch iteration. | old | unknown | No, unless workflow mode and historical edit requested. |
| `ForgeViewAI Unified Content Machine v9.3 - 6H Manual Shorts.json` | v9.3 | Manual shorts branch iteration. | old | unknown | No, unless workflow mode and historical edit requested. |
| `ForgeViewAI Unified Content Machine v10 - Story Engine v1.json` | v10 | Story Engine v1. | old | unknown | No, unless workflow mode. |
| `ForgeViewAI Unified Content Machine v10.1 - Story Engine v1.json` | v10.1 | Story Engine v1 iteration. | old | unknown | No, unless workflow mode. |
| `ForgeViewAI Unified Content Machine v10.2 - Story Engine v2.json` | v10.2 | Story Engine v2. | old | unknown | No, unless workflow mode. |
| `ForgeViewAI Unified Content Machine v10.3 - Story Engine v3.json` | v10.3 | Story Engine v3. | old | unknown | No, unless workflow mode. |
| `ForgeViewAI Unified Content Machine v11 - AI Video Auto YouTube.json` | v11 | AI video and YouTube automation branch. | old | unknown | No, unless workflow mode. |
| `ForgeViewAI Unified Content Machine v12 - Kling Preview Mode.json` | v12 | Kling preview mode branch. | old | unknown | No, unless workflow mode. |
| `ForgeViewAI Unified Content Machine v13 - Cinematic Shorts Preview.json` | v13 | Cinematic shorts preview branch. | old | unknown | No, unless workflow mode. |
| `ForgeViewAI Unified Content Machine v14 - Structured Shorts JSON.json` | v14 | Structured Shorts JSON branch. | old | unknown | No, unless workflow mode. |
| `ForgeViewAI Unified Content Machine v14.1 - OpenAI Structured Output Fix.json` | v14.1 | Structured output fix. | recent old | unknown | No, unless workflow mode. |
| `ForgeViewAI Unified Content Machine v14.2 - Sales Routing Stability Fix.json` | v14.2 | Latest detected Content Machine, sales routing stability fix. | latest detected | unknown | No, unless workflow mode and this is confirmed target. |
| `ForgeViewAI YouTube Shorts Upload - Telegram Drafts.json` | separate upload workflow | Uploads/handles Telegram drafts for YouTube Shorts path. | active candidate | unknown | No, unless workflow mode. |

Current known branch results from ProjectMemory:

- MP4 branch status: FAIL, bridge URL not configured.
- Telegram post: PASS.
- X draft: PASS.
- Shorts draft: PASS.

## Trading Bot Export Index

### Live `automation/`

| Filename | Bot type | Version | Location status | Safe to edit | Requires verification |
| --- | --- | --- | --- | --- | --- |
| `BTC Futures Paper Bot - v22 QUALITY FILTERS.json` | Futures | v22 | live export, status unclear | No, unless trading mode. | Clarify whether this is superseded, deployed, or archival. |
| `BTC Futures Paper Bot - v24 ANTI LATE LONG.json` | Futures | v24 | latest detected live Futures export | No, unless trading mode. | Confirm whether v24 is intended current live Futures version and whether deployed. |
| `kling_preview_response.json` | Unknown/runtime response | n/a | runtime/generated response | No. | Confirm ignored and not staged. |
| `kling_preview_telegram_response.json` | Unknown/runtime response | n/a | runtime/generated response | No. | Confirm ignored and not staged. |

### Backup `output/archive/`

| Filename | Bot type | Version | Location status | Safe to edit | Requires verification |
| --- | --- | --- | --- | --- | --- |
| `BTC Bot - v88 STABILITY FIX.json` | Spot | v88 | backup-only unless confirmed live | No. | Confirm whether Spot v88 should be restored to live `automation/` or remain backup-only. |
| `BTC Futures Paper Bot - v23 RSI ANTI LATE SHORT.json` | Futures | v23 | backup-only/reference | No. | Clarify relationship to live v22 and v24. |
| `ForgeViewAI Content Machine v7 - Real Content Sources.json` | Content workflow | v7 | backup-only/reference | No. | Use only for historical comparison. |

Backup also contains an archived `forgeview-ai-main` tree with old docs, growth files, spot bot files, futures bot files, virtualenv/cache, and old exports. Treat it as archive/reference-only.

## Content / Video / Logs Index

### `content/config/`

Detected files:

- `bridge_config.example.json`
- `bridge_config.json`
- `openai_config.example.json`
- `openai_config.json`
- `telegram_config.json`
- `telegram_config.json — копия.json`
- `video_provider_config.json`
- `youtube_client_secret.json`
- `youtube_token.json`
- `youtube_upload_config.example.json`
- `youtube_upload_config.json`

Classification:

- Real `*.json` config files are runtime/secrets/config.
- `*.example.json` files are source examples only if scrubbed.

Commit policy:

- Never commit real config files, tokens, OAuth files, client secrets, or copied Telegram config.
- Example configs can be committed only after review and only if they contain no real values.

### `output/media/videos/`

Detected files:

- `short.mp4`

Classification:

- generated media.

Commit policy:

- Never commit by default.
- Commit only if the user explicitly requests a reviewed media artifact.

### `Logs/`

Detected files:

- `e2e_v14_2_real_run_20260615_220516.json`
- `previous_valid_shorts_package.json`

Classification:

- runtime/generated logs and status artifacts.

Commit policy:

- Never commit by default.
- Read for diagnostics only.
- If a log is needed as evidence, summarize it in documentation instead of committing raw runtime output.

## Security / Secrets Risk

Do not print or inspect secret values unless the user explicitly requests a secure config audit. Current inventory flags the following paths by filename risk only:

| Path | Risk |
| --- | --- |
| `content\config\bridge_config.json` | Runtime bridge config; may contain local endpoint or operational settings. |
| `content\config\openai_config.json` | Likely OpenAI API config; possible API key risk. |
| `content\config\telegram_config.json` | Likely Telegram token/chat config risk. |
| `content\config\telegram_config.json — копия.json` | Duplicate Telegram config; possible stale secret copy. |
| `content\config\video_provider_config.json` | Video provider config; possible provider key or endpoint risk. |
| `content\config\youtube_client_secret.json` | YouTube OAuth client secret risk. |
| `content\config\youtube_token.json` | YouTube OAuth token risk. |
| `content\config\youtube_upload_config.json` | Upload runtime config; possible channel or credential-related settings. |
| `content\config\bridge_config.example.json` | Example config; verify no real values before commit. |
| `content\config\openai_config.example.json` | Example config; verify no real values before commit. |
| `content\config\youtube_upload_config.example.json` | Example config; verify no real values before commit. |
| `Exports\kling_preview_response.json` | Runtime API response; may contain request/response metadata. |
| `Exports\kling_preview_telegram_response.json` | Runtime Telegram/API response; may contain chat/message metadata. |
| `Logs\e2e_v14_2_real_run_20260615_220516.json` | Runtime e2e log; may contain operational payloads. |
| `Logs\previous_valid_shorts_package.json` | Generated/runtime package; may contain generated payloads. |
| `output\archive\...` | Archive may contain stale secrets, old configs, virtualenv/cache, and old generated artifacts. Treat all backup internals as high-risk until reviewed. |

No `.env` files were identified during this inventory pass.

## Autonomous Codex Rules Update

Recommended additions or reinforcements for `CEO_DIRECTIVE.md`:

- Always consult `LIVE_REPOSITORY_INVENTORY.md` after reading ProjectMemory.
- Treat `ForgeViewAIn8n/` workflow JSON as editable only in explicit workflow mode.
- Treat `automation/` as mixed-risk; identify whether a file is source, trading export, runtime response, or script before editing.
- Treat all real files in `content/config/` as secret-bearing unless proven otherwise.

Recommended additions or reinforcements for `CURRENT_STATUS.md`:

- Link to this inventory as the repository map.
- Record that `ForgeViewAITrading/` is currently empty in this inventory pass.
- Record that no `.env` files were detected.
- Record that deployment state remains unknown for every workflow until checked in n8n.

Recommended additions or reinforcements for `NEXT_OBJECTIVES.md`:

- Next task should verify active deployed n8n workflow and bridge/tunnel URL.
- Add a follow-up task to classify which files in `automation/` are safe source vs runtime/generated.
- Add a follow-up task to verify `.gitignore` coverage with actual Git status once Git tooling is available.

## Safe Commit Guidance

Generally safe to commit after review:

- `ForgeViewAIDocs/ProjectMemory/*.md`
- scrubbed documentation in `Exports/*.md`
- scrubbed example config files only if they contain no real values

Never commit by default:

- `content/config/*.json` except scrubbed examples after review
- `output/media/videos/`
- `Logs/`
- `Exports/*_response.json`
- `Exports/*_stdout.log`
- `Exports/*_stderr.log`
- `**/__pycache__/`
- `**/*.pyc`
- `**/.venv/`
- `**/work/`
- `**/output/`
- raw backup contents from `output/archive/`

