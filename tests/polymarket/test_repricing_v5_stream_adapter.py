from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from polymarket.repricing_research import (
    FrozenPaperConfig,
    RestartSafePaperCore,
    V5JsonlPaperAdapter,
    V5StreamValidationError,
)


class RepricingV5StreamAdapterTests(unittest.TestCase):
    def test_converts_v5_events_and_preserves_audit_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session, self._winning_events()[:2])
            with RestartSafePaperCore(root / "paper.sqlite3") as core:
                result = V5JsonlPaperAdapter(session, core).sync()
                signal = core.signals()[0]
                source = core.stream_source(result.source_id)

                self.assertEqual(result.ingested_events, 2)
                self.assertEqual(len(core.open_positions()), 1)
                self.assertEqual(signal["source_id"], result.source_id)
                self.assertEqual(signal["event_index"], 1)
                self.assertEqual(source["source_path"], str(session.resolve()))
                core.verify_source_event(result.source_id, 1, self._winning_events()[1])

    def test_duplicate_delivery_does_not_duplicate_position(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            database = root / "paper.sqlite3"
            self._write(session, self._winning_events()[:2])
            with RestartSafePaperCore(database) as core:
                V5JsonlPaperAdapter(session, core).sync()
                repeated = V5JsonlPaperAdapter(session, core).sync()
                self.assertEqual(repeated.verified_events, 2)
                self.assertEqual(repeated.ingested_events, 0)
                self.assertEqual(len(core.signals()), 1)
                self.assertEqual(len(core.positions()), 1)

    def test_restart_restores_open_then_processes_appended_close(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            database = root / "paper.sqlite3"
            events = self._winning_events()
            self._write(session, events[:2])
            with RestartSafePaperCore(database) as core:
                V5JsonlPaperAdapter(session, core).sync()
                self.assertEqual(len(core.open_positions()), 1)

            self._append(session, events[2:])
            with RestartSafePaperCore(database) as recovered:
                result = V5JsonlPaperAdapter(session, recovered).sync()
                self.assertEqual(result.verified_events, 2)
                self.assertEqual(result.ingested_events, 1)
                self.assertEqual(len(recovered.open_positions()), 0)
                self.assertEqual(len(recovered.trades()), 1)

    def test_restart_after_close_never_reopens_position(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            database = root / "paper.sqlite3"
            self._write(session, self._winning_events())
            with RestartSafePaperCore(database) as core:
                V5JsonlPaperAdapter(session, core).sync()
                expected = core.validation_snapshot()
            with RestartSafePaperCore(database) as recovered:
                V5JsonlPaperAdapter(session, recovered).sync()
                self.assertEqual(recovered.validation_snapshot(), expected)
                self.assertEqual(len(recovered.trades()), 1)

    def test_partial_line_is_deferred_and_complete_invalid_event_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            partial = root / "partial.jsonl"
            partial.write_bytes(b'{"event":"polymarket_snapshot"')
            with RestartSafePaperCore(root / "partial.sqlite3") as core:
                result = V5JsonlPaperAdapter(partial, core).sync()
                self.assertGreater(result.deferred_trailing_bytes, 0)
                self.assertEqual(result.ingested_events, 0)

            invalid = root / "invalid.jsonl"
            invalid.write_text('{"event":"lag_measurement"}\n', encoding="utf-8")
            with RestartSafePaperCore(root / "invalid.sqlite3") as core:
                with self.assertRaises(V5StreamValidationError):
                    V5JsonlPaperAdapter(invalid, core).sync()

    def test_frozen_side_timeout_and_slippage_contract_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            database = root / "paper.sqlite3"
            events = [
                self._snapshot("2026-01-01T00:00:00+00:00", 0.50, 240),
                self._signal("2026-01-01T00:00:00+00:00", "DOWN"),
                self._snapshot("2026-01-01T00:03:00+00:00", 0.50, 60),
            ]
            self._write(session, events)
            with RestartSafePaperCore(database) as core:
                V5JsonlPaperAdapter(session, core).sync()
                trade = core.trades()[0]
                self.assertEqual(core.config, FrozenPaperConfig())
                self.assertEqual(trade["side"], "NO")
                self.assertEqual(trade["exit_reason"], "timeout")
                self.assertAlmostEqual(trade["pnl_before_slippage"], 0.0)
                self.assertAlmostEqual(trade["pnl_after_slippage"], -0.02)

    def test_out_of_order_and_non_finite_market_events_fail_closed(self) -> None:
        with self.subTest("out_of_order"), tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session, [
                self._snapshot("2026-01-01T00:01:00+00:00", 0.50, 240),
                self._snapshot("2026-01-01T00:00:59+00:00", 0.50, 239),
            ])
            with RestartSafePaperCore(root / "paper.sqlite3") as core:
                with self.assertRaises(V5StreamValidationError):
                    V5JsonlPaperAdapter(session, core).sync()

        with self.subTest("non_finite"), tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            self._write(session, [
                self._snapshot("2026-01-01T00:00:00+00:00", float("nan"), 240)
            ])
            with RestartSafePaperCore(root / "paper.sqlite3") as core:
                with self.assertRaises(V5StreamValidationError):
                    V5JsonlPaperAdapter(session, core).sync()

    def test_source_replacement_and_truncation_fail_closed(self) -> None:
        with self.subTest("replacement"), tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            database = root / "paper.sqlite3"
            events = self._winning_events()
            self._write(session, events)
            with RestartSafePaperCore(database) as core:
                V5JsonlPaperAdapter(session, core).sync()
            changed = list(events)
            changed[0] = self._snapshot("2026-01-01T00:00:00+00:00", 0.49, 240)
            self._write(session, changed)
            with RestartSafePaperCore(database) as recovered:
                with self.assertRaises(V5StreamValidationError):
                    V5JsonlPaperAdapter(session, recovered).sync()

        with self.subTest("truncation"), tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            database = root / "paper.sqlite3"
            events = self._winning_events()
            self._write(session, events)
            with RestartSafePaperCore(database) as core:
                V5JsonlPaperAdapter(session, core).sync()
            self._write(session, events[:2])
            with RestartSafePaperCore(database) as recovered:
                with self.assertRaises(V5StreamValidationError):
                    V5JsonlPaperAdapter(session, recovered).sync()

    def test_interrupted_and_uninterrupted_ingestion_are_equivalent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "session.jsonl"
            events = self._winning_events()
            self._write(session, events[:2])
            interrupted_db = root / "interrupted.sqlite3"
            with RestartSafePaperCore(interrupted_db) as core:
                V5JsonlPaperAdapter(session, core).sync()
            self._append(session, events[2:])
            with RestartSafePaperCore(interrupted_db) as core:
                V5JsonlPaperAdapter(session, core).sync()
                interrupted = self._business_state(core)

            with RestartSafePaperCore(root / "uninterrupted.sqlite3") as core:
                V5JsonlPaperAdapter(session, core).sync()
                uninterrupted = self._business_state(core)
            self.assertEqual(interrupted, uninterrupted)

    @staticmethod
    def _business_state(core: RestartSafePaperCore) -> dict[str, object]:
        return {
            "signals": core.signals(),
            "positions": core.positions(),
            "trades": core.trades(),
            "validation": core.validation_snapshot(),
        }

    @classmethod
    def _winning_events(cls) -> list[dict[str, object]]:
        return [
            cls._snapshot("2026-01-01T00:00:00+00:00", 0.50, 240),
            cls._signal("2026-01-01T00:00:00+00:00", "UP"),
            cls._snapshot("2026-01-01T00:00:30+00:00", 0.54, 210),
        ]

    @staticmethod
    def _snapshot(timestamp: str, yes_price: float, expiry: float) -> dict[str, object]:
        return {
            "event": "polymarket_snapshot",
            "timestamp": timestamp,
            "payload": {
                "asset": "BTC",
                "market_id": "m1",
                "yes_price": yes_price,
                "no_price": 1.0 - yes_price,
                "seconds_to_expiry": expiry,
            },
        }

    @staticmethod
    def _signal(timestamp: str, direction: str) -> dict[str, object]:
        return {
            "event": "lag_measurement",
            "timestamp": timestamp,
            "payload": {
                "market_id": "m1",
                "measurement": {
                    "confidence": 0.45,
                    "direction": direction,
                    "external_price_change": 0.001,
                    "lag_score": 0.65,
                    "polymarket_yes_price_change": 0.0,
                    "qualified": False,
                    "reason": "confidence_below_threshold",
                },
            },
        }

    @staticmethod
    def _write(path: Path, events: list[dict[str, object]]) -> None:
        path.write_text(
            "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
            encoding="utf-8",
        )

    @staticmethod
    def _append(path: Path, events: list[dict[str, object]]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event, sort_keys=True) + "\n")


if __name__ == "__main__":
    unittest.main()
