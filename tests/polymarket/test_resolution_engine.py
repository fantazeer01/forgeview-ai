from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from polymarket.resolution_engine.cli import main
from polymarket.resolution_engine.models import MarketDescriptor
from polymarket.resolution_engine.resolver import parse_resolution


class ResolutionEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.start = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        self.market = MarketDescriptor(
            market_id="condition-1",
            asset="BTC",
            question="Bitcoin Up or Down",
            window_start=self.start,
            window_end=datetime(2026, 1, 1, 12, 5, tzinfo=timezone.utc),
        )

    def test_strict_resolved_up_parser(self) -> None:
        record = parse_resolution(
            self.market,
            _event("condition-1", ["1", "0"]),
            self.start,
        )
        self.assertTrue(record.resolved)
        self.assertEqual(record.outcome, 1)
        self.assertEqual(record.outcome_name, "UP")

    def test_unresolved_and_ambiguous_are_rejected(self) -> None:
        unresolved = _event("condition-1", ["0.7", "0.3"])
        unresolved["markets"][0]["closed"] = False
        self.assertEqual(
            parse_resolution(self.market, unresolved, self.start).status,
            "unresolved",
        )
        ambiguous = parse_resolution(
            self.market, _event("condition-1", ["0.5", "0.5"]), self.start
        )
        self.assertEqual(ambiguous.status, "ambiguous")
        self.assertIsNone(ambiguous.outcome)

    def test_condition_id_must_match(self) -> None:
        record = parse_resolution(
            self.market, _event("different-condition", ["1", "0"]), self.start
        )
        self.assertEqual(record.status, "missing")
        self.assertEqual(record.reason, "condition_id_not_found")

    def test_fixture_reconciliation_and_replay_are_deterministic(self) -> None:
        with _workspace_temp() as folder:
            root = Path(folder)
            runs = root / "runs"
            output = root / "resolutions"
            fixture = root / "fixture.jsonl"
            dataset = root / "dataset.csv"
            _write_session(runs / "session" / "session.jsonl")
            fixture.write_text(json.dumps({
                "market_id": "condition-1",
                "slug": "btc-updown-5m-1767268800",
                "retrieval_timestamp": self.start.isoformat(),
                "event": _event("condition-1", ["1", "0"]),
            }) + "\n", encoding="utf-8")
            with dataset.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=["market_id", "outcome"]
                )
                writer.writeheader()
                writer.writerow({"market_id": "condition-1", "outcome": 0})

            args = [
                "reconcile", "--runs-root", str(runs),
                "--output-root", str(output),
                "--proxy-dataset", str(dataset),
                "--fixture", str(fixture),
            ]
            self.assertEqual(main(args), 0)
            first = (output / "reconciliation_report.json").read_text()
            first_resolutions = (output / "resolutions.jsonl").read_text()
            self.assertEqual(main([
                "replay", "--runs-root", str(runs),
                "--output-root", str(output),
                "--proxy-dataset", str(dataset),
                "--fixture", str(fixture),
            ]), 0)
            second = (output / "reconciliation_report.json").read_text()
            self.assertEqual(first, second)
            self.assertEqual(
                first_resolutions, (output / "resolutions.jsonl").read_text()
            )
            report = json.loads(second)
            self.assertEqual(report["mismatched"], 1)
            self.assertEqual(report["resolved"], 1)


def _event(condition_id: str, prices: list[str]) -> dict:
    return {
        "slug": "btc-updown-5m-1767268800",
        "resolutionSource": "https://data.chain.link/streams/btc-usd",
        "markets": [{
            "conditionId": condition_id,
            "closed": True,
            "umaResolutionStatus": "resolved",
            "outcomes": json.dumps(["Up", "Down"]),
            "outcomePrices": json.dumps(prices),
            "closedTime": "2026-01-01 12:05:30+00",
        }],
    }


def _write_session(path: Path) -> None:
    path.parent.mkdir(parents=True)
    market = {
        "market_id": "condition-1",
        "asset": "BTC",
        "question": "Bitcoin Up or Down",
        "window_start": "2026-01-01T12:00:00+00:00",
        "window_end": "2026-01-01T12:05:00+00:00",
    }
    path.write_text(json.dumps({
        "event": "market_lifecycle",
        "timestamp": "2026-01-01T12:00:00+00:00",
        "payload": {"current": "discovered", "market": market},
    }) + "\n", encoding="utf-8")


def _workspace_temp() -> tempfile.TemporaryDirectory:
    return tempfile.TemporaryDirectory(dir=Path("tests/polymarket"))


if __name__ == "__main__":
    unittest.main()
