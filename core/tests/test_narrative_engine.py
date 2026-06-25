import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core.narrative_engine import (
    DEFAULT_STATE_PATH,
    EpisodeState,
    NarrativeError,
    StateStore,
    commit_episode,
    extend_execution_bundle,
    prepare_episode,
)


EVENT = {
    "research_event": "Prediction comparison",
    "result": "The model beat market probability at five tested moments.",
    "contradiction": "The market was expected to contain every useful clue, but the model improved it.",
}

GENERATED = {
    "episode_id": "S1E01",
    "narrative_hook": "The market predicted first. The model still won.",
    "breakdown": "The model faced later markets it had never seen.",
    "partial_resolution": "Prediction improved across all five tests.",
    "belief_state": "A predictive edge is plausible, but real profit remains unknown.",
    "open_loop": "Will the prediction edge survive real buying prices?",
    "last_result": "Prediction improved, but profit was not tested.",
}


class NarrativeEngineTests(unittest.TestCase):
    def setUp(self):
        base = Path(r"D:\ForgeViewAI\output\tests")
        base.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path(tempfile.mkdtemp(prefix="narrative_", dir=base))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_prepare_depends_on_previous_episode(self):
        state = EpisodeState()
        prepared = prepare_episode(state, EVENT)
        self.assertEqual(prepared["episode_id"], "S1E01")
        self.assertEqual(prepared["depends_on_episode"], "S1E00")
        self.assertEqual(prepared["previous_open_loop"], state.open_loop)
        self.assertTrue(prepared["continuation_required"])

    def test_commit_advances_belief_and_open_loop(self):
        state = EpisodeState()
        prepared = prepare_episode(state, EVENT)
        updated = commit_episode(state, prepared, GENERATED)
        self.assertEqual(updated.episode_id, "S1E01")
        self.assertEqual(updated.open_loop, GENERATED["open_loop"])
        self.assertEqual(updated.belief_state, GENERATED["belief_state"])
        self.assertIn(EVENT["contradiction"], updated.contradiction_chain)

    def test_commit_rejects_standalone_episode(self):
        state = EpisodeState()
        prepared = prepare_episode(state, EVENT)
        invalid = dict(GENERATED, open_loop=state.open_loop)
        with self.assertRaises(NarrativeError):
            commit_episode(state, prepared, invalid)

    def test_state_store_round_trip(self):
        store = StateStore(self.temp_dir / "state.json")
        state = EpisodeState()
        store.save(state)
        self.assertEqual(store.load(), state)

    def test_bundle_extension_preserves_existing_fields(self):
        bundle = {"bundle_version": "1.0", "scenes": [{"id": "scene_1"}]}
        state = EpisodeState()
        extended = extend_execution_bundle(bundle, state, "Conflict hook")
        self.assertEqual(extended["scenes"], bundle["scenes"])
        self.assertEqual(extended["season_id"], "S1")
        self.assertTrue(extended["continuation_required"])

    def test_state_json_is_valid(self):
        path = DEFAULT_STATE_PATH
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(raw["season_id"], "S1")
        self.assertTrue(raw["open_loop"].endswith("?"))


if __name__ == "__main__":
    unittest.main()
