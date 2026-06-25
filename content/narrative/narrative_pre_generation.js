// Paste at the start of the existing pre-generation Code node.
// It adds item.json.narrative_context and does not rename downstream fields.

const SEASON_ID = 'S1';
const SEASON_THEME =
  'Does a real trading edge exist in Polymarket BTC 5m markets or is it a data illusion?';

function nextEpisodeId(current) {
  const match = /^S1E(\d+)$/.exec(String(current || ''));
  if (!match) throw new Error(`Invalid narrative episode_id: ${current}`);
  return `S1E${String(Number(match[1]) + 1).padStart(2, '0')}`;
}

function requireQuestion(value, field) {
  const text = String(value || '').trim();
  if (!text.endsWith('?')) throw new Error(`${field} must end with a question`);
  return text;
}

const memory = $getWorkflowStaticData('global');
if (!memory.forgeviewNarrative) {
  memory.forgeviewNarrative = {
    episode_id: 'S1E00',
    season_id: SEASON_ID,
    season_theme: SEASON_THEME,
    belief_state:
      'An apparent predictive edge exists, but real executable profitability has not been confirmed.',
    open_loop:
      'Will the apparent edge survive enough real captured buying prices to separate profit from data illusion?',
    contradiction_chain: [
      'Predictive improvement did not prove executable profit.',
      'Simulated profit relied on prices that were not captured live.',
      'The first real-price result was positive but used only two trades.',
    ],
    last_result: 'Real ask edge remains not confirmed.',
    next_trigger: 'Generate the next episode from the current open loop.',
    continuation_required: true,
  };
}

const state = memory.forgeviewNarrative;
if (state.season_id !== SEASON_ID || state.season_theme !== SEASON_THEME) {
  throw new Error('Narrative season reset or theme change rejected');
}
requireQuestion(state.open_loop, 'stored open_loop');
if (state.continuation_required !== true) {
  throw new Error('continuation_required must remain true');
}

return $input.all().map((item) => {
  const event = item.json.research_event || item.json.event || {};
  const eventName = String(event.research_event || event.name || '').trim();
  const result = String(event.result || event.last_result || '').trim();
  const contradiction = String(event.contradiction || '').trim();
  if (!eventName || !result || !contradiction) {
    throw new Error('research_event.name, result, and contradiction are required');
  }

  item.json.narrative_context = {
    season_id: SEASON_ID,
    season_theme: SEASON_THEME,
    episode_id: nextEpisodeId(state.episode_id),
    depends_on_episode: state.episode_id,
    previous_belief_state: state.belief_state,
    previous_open_loop: state.open_loop,
    previous_result: state.last_result,
    contradiction_chain: [...state.contradiction_chain, contradiction],
    current_research_event: eventName,
    current_result: result,
    required_contradiction: contradiction,
    attention_structure: {
      hook: 'Open with the contradiction in the first two seconds.',
      breakdown: 'Show the system failure or insight shift.',
      partial_resolution: 'Resolve only part of the previous open loop.',
      open_loop_question: 'End with a new unresolved question.',
    },
    generation_rules: {
      must_depend_on_previous_episode: true,
      must_update_belief_state: true,
      must_create_new_open_loop: true,
      must_end_with_question: true,
      may_resolve_core_season_question: false,
      continuation_required: true,
    },
    continuation_required: true,
  };
  return item;
});

