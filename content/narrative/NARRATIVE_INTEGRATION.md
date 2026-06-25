# n8n Narrative Integration Patch

This patch preserves the existing workflow topology and all downstream field
names.

## Placement

1. Add the contents of `narrative_pre_generation.js` to the beginning of the
   existing Code node that prepares the OpenAI request.
2. Include `{{$json.narrative_context}}` in the existing OpenAI prompt input.
3. Require the generated object to return:
   - `episode_id`
   - `narrative_hook`
   - `breakdown`
   - `partial_resolution`
   - `belief_state`
   - `open_loop`
   - `last_result`
   - `next_trigger`
4. Add the contents of `narrative_post_generation.js` to the end of the
   existing parsing/normalization Code node.

No Telegram, X, scenes, Kling prompts, rendering, polling, or publishing
fields are renamed.

## Execution Order

```text
existing trigger
  -> existing input normalization + narrative_pre_generation.js
  -> existing OpenAI generation using narrative_context
  -> existing parse node + narrative_post_generation.js
  -> existing Telegram / X branches
  -> asynchronous D:\ForgeViewAI\core\render_engine.py submission
  -> existing wait / poll / Telegram video delivery branch
```

The state is stored in n8n workflow static data under:

```text
forgeviewNarrative
```

This works only for active workflow executions. Manual test executions may not
persist static data consistently across n8n versions.

## OpenAI Prompt Addition

Append this block to the current generation prompt:

```text
SERIALIZED NARRATIVE CONTEXT
{{ JSON.stringify($json.narrative_context) }}

You must depend on the previous open loop, partially resolve it, evolve the
belief state, add the required contradiction, and end with a new unresolved
question. Never fully resolve the season theme.
```

## Output Compatibility

Existing required channel fields remain unchanged:

- `telegram_post`
- `x_post`
- `scenes_json`
- `kling_prompts`
- video request and result fields

Narrative fields are additive.

Video submission must run after Telegram and X publishing. It returns job IDs
immediately and must not be placed inline before either text channel.
