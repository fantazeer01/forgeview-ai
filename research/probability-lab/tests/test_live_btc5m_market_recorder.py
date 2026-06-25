import importlib.util
import io
import json
import ssl
import unittest
import urllib.error
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "live_btc5m_market_recorder.py"
SPEC = importlib.util.spec_from_file_location("recorder", SCRIPT)
recorder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(recorder)


def market(slug_start):
    start = datetime.fromtimestamp(slug_start, timezone.utc)
    return {
        "market_id": f"btc-updown-5m-{slug_start}",
        "condition_id": "condition",
        "start": start,
        "end": start + timedelta(seconds=300),
        "yes_token_id": "yes",
        "no_token_id": "no",
    }


class Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return self.payload


class RecorderTests(unittest.TestCase):
    def test_slug_timestamp_is_market_start(self):
        normalized = recorder.normalize_market(
            {"slug": "btc-updown-5m-1800000000", "clobTokenIds": '["yes", "no"]'}
        )
        self.assertEqual(normalized["start"].timestamp(), 1800000000)
        self.assertEqual(normalized["end"].timestamp(), 1800000300)

    def test_tracker_keeps_active_market_during_refresh_timeout(self):
        tracker = recorder.MarketTracker()
        tracker.active = market(1800000000)
        now = datetime.fromtimestamp(1800000100, timezone.utc)
        with patch.object(tracker, "_discover_current", return_value=None):
            self.assertEqual(tracker.refresh(now)["market_id"], tracker.active["market_id"])

    def test_tracker_switches_after_expiry(self):
        tracker = recorder.MarketTracker()
        old_market = market(1800000000)
        new_market = market(1800000300)
        tracker.active = old_market
        now = datetime.fromtimestamp(1800000301, timezone.utc)
        output = io.StringIO()
        with (
            patch.object(tracker, "_discover_current", return_value=new_market),
            redirect_stdout(output),
        ):
            selected = tracker.refresh(now)
        self.assertEqual(selected["market_id"], new_market["market_id"])
        self.assertIn(
            f"MARKET_SWITCH old={old_market['market_id']} new={new_market['market_id']}",
            output.getvalue(),
        )

    def test_http_json_retries_timeout_ssl_and_url_errors(self):
        errors = [
            TimeoutError("timeout"),
            ssl.SSLEOFError(8, "eof"),
            urllib.error.URLError("temporary"),
            Response({"ok": True}),
        ]
        with patch.object(recorder.urllib.request, "urlopen", side_effect=errors):
            result = recorder.http_json(
                "https://example.test",
                retries=3,
                backoff=0,
                sleep=lambda _: None,
            )
        self.assertEqual(result, {"ok": True})

    def test_output_must_be_on_d_drive(self):
        expected = r"D:\ForgeViewAI\output\research\data\recorder\capture.csv"
        self.assertEqual(str(recorder.ensure_d_drive(expected)), expected)
        with self.assertRaises(ValueError):
            recorder.ensure_d_drive(r"D:\capture.csv")
        with self.assertRaises(ValueError):
            recorder.ensure_d_drive(r"C:\capture.csv")


if __name__ == "__main__":
    unittest.main()
