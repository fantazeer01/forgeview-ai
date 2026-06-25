import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core.render_engine import (
    build_kling_payload,
    poll_execution_bundle,
    poll_render_status,
    return_video_url,
    submit_execution_bundle,
    trigger_video_render,
)


SCENE = {
    "id": "scene_1",
    "start": 0,
    "end": 10,
    "location": "quantitative research lab",
    "character_action": "analyst watches a market counter",
    "camera": "slow dolly",
    "lighting": "cold cyan",
    "beats": [
        {
            "time": 0,
            "system_state": "scan begins",
            "action": "counter rises",
            "screen_content": ["MARKETS FOUND: 001"],
        }
    ],
    "glitch": "one frame tear",
    "emotional_progression": "hope to unease",
}


class RenderEngineTests(unittest.TestCase):
    def setUp(self):
        base = Path(r"D:\ForgeViewAI\output\tests")
        base.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path(tempfile.mkdtemp(prefix="render_", dir=base))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_build_payload(self):
        payload = build_kling_payload(SCENE)
        self.assertEqual(payload["aspect_ratio"], "9:16")
        self.assertEqual(payload["duration"], "10")
        self.assertIn("MARKETS FOUND: 001", payload["prompt"])
        self.assertEqual(payload["external_task_id"], "scene_1")

    def test_mock_trigger_and_status(self):
        payload = build_kling_payload(SCENE)
        job = trigger_video_render(payload, "mock", self.temp_dir)
        status = poll_render_status(job["job_id"], "mock", self.temp_dir)
        self.assertEqual(status["status"], "ready_for_upload")
        self.assertEqual(return_video_url(job["job_id"], "mock", self.temp_dir), "")

    def test_submit_is_async_and_preserves_bundle(self):
        bundle = {"bundle_version": "1.0", "scenes": [SCENE, dict(SCENE, id="scene_2")]}
        updated = submit_execution_bundle(bundle, "mock", self.temp_dir)
        self.assertEqual(updated["bundle_version"], "1.0")
        self.assertEqual(len(updated["video_render"]["job_ids"]), 2)
        self.assertTrue(updated["video_render"]["async"])
        self.assertFalse(updated["video_render"]["text_publishing_blocked"])
        self.assertEqual(updated["video_render"]["status"], "triggered")

    def test_poll_bundle_ready_for_upload(self):
        bundle = submit_execution_bundle({"scenes": [SCENE]}, "mock", self.temp_dir)
        polled = poll_execution_bundle(bundle, "mock", self.temp_dir)
        self.assertEqual(polled["video_render"]["status"], "ready_for_upload")

    def test_mock_manifest_is_json(self):
        job = trigger_video_render(build_kling_payload(SCENE), "mock", self.temp_dir)
        path = self.temp_dir / f"{job['job_id']}.json"
        self.assertEqual(json.loads(path.read_text())["job_id"], job["job_id"])


if __name__ == "__main__":
    unittest.main()
