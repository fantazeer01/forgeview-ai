import tempfile
import unittest
from pathlib import Path

from polymarket.repricing_research.websocket_latency import (
    LatencyRecorder,
    _distribution,
    _timestamp_ms,
    build_parser,
    summarize_records,
)


class RepricingWebSocketLatencyTests(unittest.TestCase):
    def test_distribution_is_deterministic(self) -> None:
        result = _distribution([5, 1, 3, 2, 4])
        self.assertEqual(result["min"], 1)
        self.assertEqual(result["median"], 3)
        self.assertEqual(result["p90"], 5)
        self.assertEqual(result["max"], 5)

    def test_recorder_captures_staleness_gaps_and_stage_latency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            recorder = LatencyRecorder(Path(tmp) / "journal.jsonl", stale_after_ms=100)
            first = recorder.record(source="binance_websocket", event_type="aggTrade", asset="BTC", raw="{}", received_wall_ns=2_000_000_000, received_perf_ns=1_000_000, processing_perf_ns=1_100_000, server_timestamp_ms=1_500, sequence=10)
            second = recorder.record(source="binance_websocket", event_type="aggTrade", asset="BTC", raw="{}", received_wall_ns=2_100_000_000, received_perf_ns=2_000_000, processing_perf_ns=2_200_000, server_timestamp_ms=2_000, sequence=13)
            self.assertTrue(first.stale_quote)
            self.assertEqual(second.sequence_gap, 2)
            self.assertEqual(second.inter_message_gap_ms, 100)
            summary = summarize_records(recorder.records)
            self.assertEqual(summary["sources"]["binance_websocket"]["records"], 2)

    def test_timestamp_and_bounded_cli_contract(self) -> None:
        self.assertEqual(_timestamp_ms("1757908892351"), 1757908892351)
        self.assertEqual(_timestamp_ms("1757908892"), 1757908892000)
        args = build_parser().parse_args(["--duration", "60", "--output", "out"])
        self.assertEqual(args.duration, 60)
        self.assertEqual(args.output, Path("out"))


if __name__ == "__main__":
    unittest.main()
