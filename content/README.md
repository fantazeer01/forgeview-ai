# ForgeView Content Machine v3

Prompt-layer upgrade for the existing content pipeline.

No n8n workflow architecture is changed.

- Probability Lab is the primary source.
- Telegram remains enabled.
- X drafts remain enabled.
- Shorts generation remains enabled.
- Publishing remains unchanged.
- Shorts keep the existing seven-scene JSON compatibility fields.
- Serialized state now drives every channel before generation.

Domain locations:

- `D:\ForgeViewAI\content\prompts`: narrative and Shorts prompts
- `D:\ForgeViewAI\content\narrative`: n8n narrative execution code
- `D:\ForgeViewAI\content\publishing`: Telegram, YouTube, and bridge logic
- `D:\ForgeViewAI\content\video`: Shorts generation source
- `D:\ForgeViewAI\core`: narrative and rendering engines
- `D:\ForgeViewAI\state`: episode memory and runtime logs
- `D:\ForgeViewAI\automation`: importable n8n workflows and triggers
- `D:\ForgeViewAI\output`: generated bundles, media, and render jobs

## Narrative Engine

The season never resets:

> Does a real trading edge exist in Polymarket BTC 5m markets or is it a data
> illusion?

Every episode must consume the previous `open_loop`, evolve `belief_state`,
append a contradiction, and create a new unresolved question.

Run the Python validation layer:

```powershell
python -m unittest discover -s D:\ForgeViewAI\core\tests -v
```

Prepare a transition:

```powershell
python D:\ForgeViewAI\core\narrative_engine.py prepare `
  --event D:\ForgeViewAI\state\examples\research_event.example.json `
  --out D:\ForgeViewAI\output\content\prepared_episode.json
```

Commit a validated episode:

```powershell
python D:\ForgeViewAI\core\narrative_engine.py commit `
  --prepared D:\ForgeViewAI\output\content\prepared_episode.json `
  --generated D:\ForgeViewAI\state\examples\generated_episode.example.json
```

## Async Video Rendering

Text channels publish first. Video rendering is then submitted as a separate
asynchronous branch:

```powershell
python D:\ForgeViewAI\core\render_engine.py submit `
  --bundle D:\ForgeViewAI\output\content\shorts\execution_bundle.json `
  --out D:\ForgeViewAI\output\media\outputs\execution_bundle.rendering.json `
  --provider mock
```

Use `--provider kling` only after configuring `KLING_API_TOKEN`.
