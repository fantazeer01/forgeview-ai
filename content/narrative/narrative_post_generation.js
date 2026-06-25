// Paste at the end of the existing parse/normalization Code node.
// It validates and persists narrative state while preserving every output field.

const SEASON_ID = 'S1';
const SEASON_THEME =
  'Does a real trading edge exist in Polymarket BTC 5m markets or is it a data illusion?';
const memory = $getWorkflowStaticData('global');
const stored = memory.forgeviewNarrative;
if (!stored) throw new Error('Narrative state was not prepared');

function requiredText(object, field) {
  const value = String(object[field] || '').trim();
  if (!value) throw new Error(`Generated episode missing ${field}`);
  return value;
}

return $input.all().map((item) => {
  const generated = item.json;
  const context = generated.narrative_context;
  if (!context) throw new Error('narrative_context missing before channel generation');
  if (context.depends_on_episode !== stored.episode_id) {
    throw new Error('Stale narrative state: another episode already advanced');
  }

  const episodeId = requiredText(generated, 'episode_id');
  const beliefState = requiredText(generated, 'belief_state');
  const openLoop = requiredText(generated, 'open_loop');
  const lastResult = requiredText(generated, 'last_result');
  requiredText(generated, 'narrative_hook');
  requiredText(generated, 'breakdown');
  requiredText(generated, 'partial_resolution');

  if (episodeId !== context.episode_id) {
    throw new Error('Generated episode_id does not match narrative transition');
  }
  if (!openLoop.endsWith('?')) {
    throw new Error('New open_loop must end with a question');
  }
  if (openLoop === context.previous_open_loop) {
    throw new Error('Episode must create a new open_loop');
  }
  if (beliefState === context.previous_belief_state) {
    throw new Error('Episode must evolve belief_state');
  }

  const contradictionChain = [...stored.contradiction_chain];
  if (!contradictionChain.includes(context.required_contradiction)) {
    contradictionChain.push(context.required_contradiction);
  }

  memory.forgeviewNarrative = {
    episode_id: episodeId,
    season_id: SEASON_ID,
    season_theme: SEASON_THEME,
    belief_state: beliefState,
    open_loop: openLoop,
    contradiction_chain: contradictionChain,
    last_result: lastResult,
    next_trigger:
      String(generated.next_trigger || '').trim() || `Investigate: ${openLoop}`,
    continuation_required: true,
    updated_at: new Date().toISOString(),
  };

  // These fields feed Telegram, X, scenes, and Kling without changing them.
  item.json.season_id = SEASON_ID;
  item.json.contradiction_chain = contradictionChain;
  item.json.continuation_required = true;
  return item;
});

