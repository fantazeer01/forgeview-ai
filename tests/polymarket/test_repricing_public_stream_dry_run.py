from __future__ import annotations

import asyncio
import tempfile
import time
import unittest
from pathlib import Path

from polymarket.repricing_research.public_stream_dry_run import (
    PublicEvent,
    PublicStreamAdapter,
    PublicStreamDryRun,
)


def event(index: int, *, age_ms: float = 100.0, token: str = "token-btc") -> PublicEvent:
    wall = time.time_ns()
    return PublicEvent(
        token_id=token,
        asset="BTC",
        event_type="price_change",
        server_timestamp_ms=int(wall / 1_000_000 - age_ms),
        received_wall_ns=wall,
        received_monotonic_ns=time.perf_counter_ns(),
        payload_hash=f"hash-{index}",
    )


async def fixture_source(count: int, *, age_ms: float = 100.0):
    for index in range(count):
        yield event(index, age_ms=age_ms)
        await asyncio.sleep(0.02)


class PublicStreamDryRunTests(unittest.TestCase):
    def test_public_event_correlates_to_local_lifecycle_and_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner = PublicStreamDryRun(Path(tmp), max_attempts=2)
            runner.adapter.sample_interval_ns = 0
            summary = asyncio.run(runner.run(fixture_source(20)))
            self.assertEqual(summary["attempts"], 2)
            self.assertEqual(summary["orders_submitted"], 0)
            self.assertTrue(summary["replay"]["valid"])
            self.assertEqual(summary["public_stream"]["transition_missing"], 0)

    def test_stale_event_is_rejected(self) -> None:
        adapter = PublicStreamAdapter(stale_after_ms=2_000, sample_interval_ms=0)
        accepted, reason = adapter.observe(event(1, age_ms=2_500))
        self.assertFalse(accepted)
        self.assertEqual(reason, "stale")
        self.assertEqual(adapter.stale, 1)

    def test_duplicate_event_is_rejected(self) -> None:
        adapter = PublicStreamAdapter(sample_interval_ms=0)
        item = event(1)
        self.assertTrue(adapter.observe(item)[0])
        self.assertEqual(adapter.observe(item), (False, "duplicate"))

    def test_reconnect_counter_is_reported(self) -> None:
        adapter = PublicStreamAdapter()
        adapter.reconnects += 1
        self.assertEqual(adapter.reconnects, 1)

    def test_backpressure_is_counted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner = PublicStreamDryRun(Path(tmp), max_attempts=20, queue_size=1, concurrency=1)
            runner.adapter.sample_interval_ns = 0
            summary = asyncio.run(runner.run(fixture_source(100)))
            self.assertGreater(summary["public_stream"]["dropped_or_backpressured"], 0)

    def test_source_contains_no_credential_or_order_capability(self) -> None:
        source = Path("polymarket/repricing_research/public_stream_dry_run.py").read_text(encoding="utf-8").lower()
        for token in ("private_key", "passphrase", "poly_api_key", "post /order"):
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
