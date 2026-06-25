# Narrative Serialization Addendum

Apply this after the current Content Machine V4 instructions.

```text
The episode is not standalone.

Use narrative_context as mandatory prior state.

The season question is:
"Does a real trading edge exist in Polymarket BTC 5m markets or is it a data illusion?"

Required episode transition:
1. Hook: introduce the supplied contradiction immediately.
2. Breakdown: show the failure or insight shift caused by the current event.
3. Partial resolution: answer part of previous_open_loop, never all of it.
4. Belief update: belief_state must change.
5. New open loop: end with a new unresolved question.

Return these additive fields:
- episode_id
- narrative_hook
- breakdown
- partial_resolution
- belief_state
- open_loop
- last_result
- next_trigger

Rules:
- episode_id must equal narrative_context.episode_id.
- The episode must explicitly depend on narrative_context.previous_open_loop.
- open_loop must differ from previous_open_loop and end with a question.
- Never answer the core season question conclusively.
- continuation_required is always true.
- Telegram, X, scenes, and Kling outputs must all express the same narrative
  transition.
```

