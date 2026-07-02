from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from polymarket.repricing_research.authenticated_latency_harness import (
    AmbiguousSubmissionError,
    ClockMonitor,
    DryRunHarness,
    EventJournal,
    HarnessSafetyError,
    LoopbackTransport,
    PreSendTransportError,
    _percentile,
    replay_journal,
)


class PreSendOnceTransport:
    def __init__(self, delegate):
        self.delegate = delegate
        self.calls = 0

    async def post(self, body, headers):
        self.calls += 1
        if self.calls == 1:
            raise PreSendTransportError("fixture pre-send")
        return await self.delegate.post(body, headers)


class TimeoutTransport:
    async def post(self, body, headers):
        raise asyncio.TimeoutError("fixture ambiguous timeout")


class AuthenticatedLatencyHarnessTests(unittest.TestCase):
    def test_local_harness_covers_fill_cancel_and_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary = asyncio.run(DryRunHarness(Path(tmp)).run(6))
            self.assertEqual(summary["orders_submitted"], 0)
            self.assertEqual(summary["network_scope"], "127.0.0.1_only")
            self.assertEqual(summary["outcomes"], {"fixture_cancel": 3, "fixture_fill": 3})
            self.assertTrue(summary["replay"]["valid"])
            self.assertEqual(summary["replay"]["correlations"], 6)

    def test_identity_hash_is_deterministic_across_runs(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            a = asyncio.run(DryRunHarness(Path(first)).run(4))
            b = asyncio.run(DryRunHarness(Path(second)).run(4))
            self.assertEqual(a["deterministic_identity_hash"], b["deterministic_identity_hash"])
            self.assertEqual(a["deterministic_summary_hash"], b["deterministic_summary_hash"])

    def test_clock_drift_fails_closed_before_sink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            harness = DryRunHarness(Path(tmp), clock=ClockMonitor(offset_ms=51))
            with self.assertRaisesRegex(HarnessSafetyError, "clock gate"):
                asyncio.run(harness.run(1))

    def test_secret_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            journal = EventJournal(Path(tmp) / "events.jsonl", "run", ClockMonitor())
            with self.assertRaisesRegex(HarnessSafetyError, "sensitive"):
                journal.emit("c", "i", "bad", metadata={"private_key": "never"})

    def test_replay_rejects_duplicate_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            journal = EventJournal(path, "run", ClockMonitor())
            journal.emit("c", "i", "signal_generated")
            line = path.read_text(encoding="utf-8")
            path.write_text(line + line, encoding="utf-8")
            self.assertEqual(replay_journal(path)["reason"], "duplicate_event_id")

    def test_non_loopback_transport_cannot_be_configured(self) -> None:
        with self.assertRaisesRegex(HarnessSafetyError, "not active"):
            asyncio.run(LoopbackTransport(0).post(b"{}", {}))

    def test_percentile_is_deterministic(self) -> None:
        self.assertEqual(_percentile([1.0, 2.0, 3.0, 4.0], 95), 3.85)

    def test_proven_pre_send_failure_retries_once(self) -> None:
        async def scenario():
            from polymarket.repricing_research.authenticated_latency_harness import LocalExecutionSink
            async with LocalExecutionSink() as sink:
                transport = PreSendOnceTransport(LoopbackTransport(sink.port))
                with tempfile.TemporaryDirectory() as tmp:
                    harness = DryRunHarness(Path(tmp), transport_override=transport)
                    summary = await harness.run(1)
                    return transport.calls, summary

        calls, summary = asyncio.run(scenario())
        self.assertEqual(calls, 2)
        self.assertTrue(summary["replay"]["valid"])

    def test_ambiguous_timeout_fails_closed_without_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            harness = DryRunHarness(Path(tmp), transport_override=TimeoutTransport())
            with self.assertRaisesRegex(AmbiguousSubmissionError, "without retry"):
                asyncio.run(harness.run(1))
            text = (Path(tmp) / "latency_events.jsonl").read_text(encoding="utf-8")
            self.assertEqual(text.count('"event_name":"timeout"'), 1)
            self.assertNotIn('"event_name":"retry_scheduled"', text)

    def test_journal_contains_no_auth_material(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asyncio.run(DryRunHarness(root).run(2))
            text = (root / "latency_events.jsonl").read_text(encoding="utf-8").lower()
            for token in ("private_key", "passphrase", "api_secret", "authorization"):
                self.assertNotIn(token, text)
            json.loads((root / "benchmark_summary.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
