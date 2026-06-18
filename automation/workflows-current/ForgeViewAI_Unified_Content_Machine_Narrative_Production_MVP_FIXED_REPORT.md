# ForgeViewAI Unified Content Machine MVP — Verification Report

## Deliverable

- Workflow: `automation/workflows-current/ForgeViewAI_Unified_Content_Machine_Narrative_Production_MVP_FIXED.json`
- Workflow name: `ForgeViewAI Unified Content Machine - Narrative Production`
- Import status: standalone n8n workflow JSON; disabled after import.

## Verification

- `Manual Trigger` connects to `Prepare Narrative Engine`.
- `Prepare Narrative Engine` has outgoing connections to:
  - `Build Telegram Prompt`
  - `Build Strict X Prompt`
  - `Build YouTube Shorts Prompt`
- The required Shorts Retry 1, Retry 2, Retry 3 generation, validation, and IF nodes exist.
- The true output of every Shorts IF node connects to `Format Structured Shorts Draft`.
- The false outputs form the required Retry 1 → Retry 2 → Retry 3 chain.
- Retry 3 false connects to `Fallback Previous Valid Shorts Package`, then to `Format Structured Shorts Draft`.
- `Format Structured Shorts Draft` connects directly to `Telegram - Send Shorts Draft`.
- All three `OpenAI Chat Model - Shorts Retry N` nodes use:
  - model `gpt-4.1-mini`;
  - Responses API enabled;
  - response format `text`;
  - maximum tokens `1800`;
  - temperature `0.4`;
  - timeout `120000` ms;
  - maximum retries `0`.

## Source limitation

No Content Machine workflow JSON or historical Story/Narrative Engine implementation existed in the repository, its Git history, or the supplied local project files when issue #1 was implemented. The workflow was therefore reconstructed from the issue's required graph.

The original strategy and prompts could not be modified because they were not present. `Prepare Narrative Engine`, `Build Telegram Prompt`, and `Build Strict X Prompt` are explicitly marked placeholders. The Shorts prompt contains only the minimum structured-output contract needed to execute and validate the issue's Shorts path.

## Configuration required in n8n

1. Select the same OpenAI credential on all three `OpenAI Chat Model - Shorts Retry N` nodes.
2. Select a Telegram credential on `Telegram - Send Shorts Draft`.
3. Define `FORGEVIEW_SHORTS_TELEGRAM_CHAT_ID` in the n8n environment, or replace the node expression with the numeric Telegram chat/channel ID.
4. Replace the placeholder fields in `Prepare Narrative Engine` with the existing Story/Narrative Engine output when that source becomes available.

## Manual test

1. Import the workflow JSON.
2. Configure the OpenAI and Telegram credentials and chat ID.
3. Open `Manual Trigger` and choose **Execute workflow**.
4. Confirm that one valid model response, or the deterministic fallback after three invalid responses, reaches `Telegram - Send Shorts Draft`.

