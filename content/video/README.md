# Video Rendering Module

Asynchronous scene rendering for `execution_bundle.json`.

## Providers

- `mock` is the safe default. It creates one ready-for-upload request manifest
  per scene and performs no external generation.
- `kling` calls KlingAI Open Platform text-to-video.

Official API references:

- https://kling.ai/document-api/apiReference/model/textToVideo
- https://kling.ai/document-api/apiReference/commonInfo

## Environment

```text
KLING_API_TOKEN=...
KLING_API_BASE=https://api-singapore.klingai.com
KLING_MODEL=kling-v2-6
KLING_CALLBACK_URL=https://your-n8n/webhook/kling-callback
```

All runtime paths are locked to:

```text
D:\ForgeViewAI
```

Do not commit tokens.

## Mock Submission

```powershell
python D:\ForgeViewAI\core\render_engine.py submit `
  --bundle D:\ForgeViewAI\output\content\shorts\execution_bundle.json `
  --out D:\ForgeViewAI\output\media\outputs\execution_bundle.rendering.json `
  --provider mock
```

This returns immediately. Text publishing does not wait.

## Kling Submission

```powershell
python D:\ForgeViewAI\core\render_engine.py submit `
  --bundle D:\ForgeViewAI\output\content\shorts\execution_bundle.json `
  --out D:\ForgeViewAI\output\media\outputs\execution_bundle.rendering.json `
  --provider kling
```

## Poll Once

```powershell
python D:\ForgeViewAI\core\render_engine.py poll `
  --bundle D:\ForgeViewAI\output\media\outputs\execution_bundle.rendering.json `
  --out D:\ForgeViewAI\output\media\outputs\execution_bundle.polled.json
```

Schedule repeated polling in n8n. The Python command performs one status check
and exits; it never blocks in a polling loop.

## Pipeline Order

```text
Telegram publish
X publish
video submit (asynchronous)
wait / scheduled poll branch
video upload or Telegram delivery
```
