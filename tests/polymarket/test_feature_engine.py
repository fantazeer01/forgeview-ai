from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from polymarket.feature_engine.cli import main
from polymarket.feature_engine.config import FeatureConfig
from polymarket.feature_engine.dataset_builder import DatasetBuilder
from polymarket.feature_engine.features import change, simple_return
from polymarket.feature_engine.schema import (
    FEATURE_COLUMNS, MICROSTRUCTURE_FEATURE_COLUMNS,
)


class FeatureEngineTests(unittest.TestCase):
    def test_microstructure_features_are_asof_and_legacy_rows_remain_eligible(self) -> None:
        with _workspace_temp() as folder:
            root = Path(folder)
            session = root / "runs" / "session-a" / "session.jsonl"
            _write_session(session)
            start = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
            events = [
                _event(start + timedelta(seconds=55), "microstructure_snapshot", {
                    "schema_version": 1, "market_id": "btc-window", "asset": "BTC",
                    "quote_age_seconds": 0.2,
                    "time_since_last_quote_update_seconds": 5.0,
                    "repricing_velocity": 0.001,
                    "repricing_acceleration": 0.0001,
                    "yes_change_frequency_30s": 0.1,
                    "no_change_frequency_30s": 0.1,
                    "consecutive_quote_stability": 2,
                    "bid_ask_spread": 0.02, "spread_change": -0.01,
                    "spread_velocity": -0.002, "spread_compression": 0.01,
                    "yes_bid_size": 100, "yes_ask_size": 80,
                    "total_bid_depth": 500, "total_ask_depth": 400,
                    "book_imbalance": 1 / 9, "refresh_latency_seconds": 0.05,
                    "cross_asset_yes_dispersion": 0.03,
                    "cross_asset_relative_yes": 0.01,
                }),
                _event(start + timedelta(seconds=65), "microstructure_snapshot", {
                    "schema_version": 1, "market_id": "btc-window", "asset": "BTC",
                    "repricing_velocity": 999.0, "bid_ask_spread": 999.0,
                }),
            ]
            with session.open("a", encoding="utf-8") as handle:
                for event in events:
                    handle.write(json.dumps(event) + "\n")
            result = DatasetBuilder(FeatureConfig(
                runs_root=root / "runs",
                output_root=root / "training",
                allow_proxy_labels=True,
            )).build()
            btc = next(row for row in result.rows if row.asset == "BTC")
            eth = next(row for row in result.rows if row.asset == "ETH")
            self.assertEqual(btc.repricing_velocity, 0.001)
            self.assertEqual(btc.bid_ask_spread, 0.02)
            self.assertIsNone(eth.repricing_velocity)
            self.assertEqual(len(result.rows), 2)
            self.assertEqual(
                result.summary["microstructure"]["rows_with_any_microstructure"], 1
            )
            self.assertTrue(
                set(MICROSTRUCTURE_FEATURE_COLUMNS) <= set(FEATURE_COLUMNS)
            )

    def test_completed_markets_build_one_row_each(self) -> None:
        with _workspace_temp() as folder:
            root = Path(folder)
            runs = root / "runs"
            output = root / "training"
            _write_session(runs / "session-a" / "session.jsonl")
            result = DatasetBuilder(FeatureConfig(
                runs_root=runs, output_root=output, allow_proxy_labels=True
            )).build()

            self.assertEqual(len(result.rows), 2)
            self.assertEqual({row.asset for row in result.rows}, {"BTC", "ETH"})
            self.assertEqual(
                {row.asset: row.outcome for row in result.rows},
                {"BTC": 1, "ETH": 0},
            )
            self.assertTrue(all(row.market_age_seconds == 60 for row in result.rows))
            self.assertTrue(all(row.seconds_to_expiry == 240 for row in result.rows))
            self.assertTrue(all(row.label_source == "reference_window_return" for row in result.rows))

    def test_exports_csv_real_parquet_and_summary(self) -> None:
        with _workspace_temp() as folder:
            root = Path(folder)
            runs = root / "runs"
            output = root / "training"
            _write_session(runs / "session-a" / "session.jsonl")
            result = DatasetBuilder(FeatureConfig(
                runs_root=runs, output_root=output, allow_proxy_labels=True
            )).build()

            self.assertEqual(result.parquet_path.read_bytes()[:4], b"PAR1")
            self.assertEqual(result.parquet_path.read_bytes()[-4:], b"PAR1")
            with result.csv_path.open(encoding="utf-8") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 2)
            summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["total_samples"], 2)
            self.assertEqual(summary["feature_count"], len(FEATURE_COLUMNS))
            self.assertEqual(summary["class_balance"], {"DOWN": 1, "UP": 1})
            self.assertIn("outcome", summary["correlation_matrix"])

    def test_incomplete_and_unlabelled_windows_are_excluded(self) -> None:
        with _workspace_temp() as folder:
            root = Path(folder)
            session = root / "runs" / "session-a" / "session.jsonl"
            _write_session(session, stop_seconds=120)
            result = DatasetBuilder(
                FeatureConfig(
                    runs_root=root / "runs",
                    output_root=root / "training",
                    allow_proxy_labels=True,
                )
            ).build()
            self.assertEqual(result.rows, [])
            self.assertGreater(
                result.summary["skipped_windows"].get("incomplete_window", 0), 0
            )

    def test_cli_build_and_inspect(self) -> None:
        with _workspace_temp() as folder:
            root = Path(folder)
            runs = root / "runs"
            output = root / "training"
            _write_session(runs / "session-a" / "session.jsonl")
            self.assertEqual(main([
                "build", "--runs-root", str(runs), "--output-root", str(output),
                "--allow-proxy-labels",
            ]), 0)
            self.assertEqual(main([
                "inspect", "--runs-root", str(runs), "--output-root", str(output)
            ]), 0)

    def test_authoritative_label_is_preferred_over_proxy(self) -> None:
        from polymarket.resolution_engine.models import ResolutionRecord
        from polymarket.resolution_engine.storage import write_resolutions

        with _workspace_temp() as folder:
            root = Path(folder)
            runs = root / "runs"
            output = root / "training"
            resolutions = root / "resolutions.jsonl"
            _write_session(runs / "session-a" / "session.jsonl")
            timestamp = datetime(2026, 1, 1, 12, 5, tzinfo=timezone.utc)
            write_resolutions(resolutions, [ResolutionRecord(
                market_id="btc-window",
                asset="BTC",
                question="Bitcoin Up or Down",
                slug="btc-updown-5m-1767268800",
                outcome=0,
                outcome_name="DOWN",
                resolution_timestamp=timestamp,
                resolution_source="test-authoritative",
                retrieval_timestamp=timestamp,
                status="resolved",
                reason="",
            )])
            result = DatasetBuilder(FeatureConfig(
                runs_root=runs,
                output_root=output,
                resolutions_path=resolutions,
                allow_proxy_labels=False,
            )).build()
            self.assertEqual(len(result.rows), 1)
            self.assertEqual(result.rows[0].market_id, "btc-window")
            self.assertEqual(result.rows[0].outcome, 0)
            self.assertEqual(
                result.rows[0].label_source, "polymarket_gamma_resolved"
            )

    def test_asof_features_reject_stale_and_future_observations(self) -> None:
        anchor = datetime(2026, 1, 1, 12, 1, tzinfo=timezone.utc)
        series = [
            (anchor - timedelta(seconds=50), 100.0),
            (anchor - timedelta(seconds=10), 101.0),
            (anchor - timedelta(seconds=5), 101.0),
            (anchor + timedelta(seconds=1), 999.0),
        ]
        self.assertIsNone(simple_return(
            series, anchor, 30, max_age_seconds=10
        ))
        self.assertAlmostEqual(
            simple_return(series, anchor, 5, max_age_seconds=10),
            0.0,
        )
        self.assertEqual(
            change(series, anchor, 5, max_age_seconds=10),
            0.0,
        )

    def test_first_seen_detection_delay_is_recovered(self) -> None:
        with _workspace_temp() as folder:
            root = Path(folder)
            runs = root / "runs"
            output = root / "training"
            session = runs / "session-a" / "session.jsonl"
            _write_session(session)
            lines = [
                json.loads(line)
                for line in session.read_text(encoding="utf-8").splitlines()
            ]
            lines = [
                line for line in lines
                if line["event"] != "lifecycle_tracking"
            ]
            session.write_text(
                "\n".join(json.dumps(line) for line in lines) + "\n",
                encoding="utf-8",
            )
            result = DatasetBuilder(FeatureConfig(
                runs_root=runs,
                output_root=output,
                allow_proxy_labels=True,
            )).build()
            self.assertEqual(len(result.rows), 2)
            self.assertTrue(all(row.detection_delay == 0 for row in result.rows))
            diagnostics = json.loads(
                (output / "missingness_diagnostics.json").read_text()
            )
            self.assertEqual(
                diagnostics["recovery"]["detection_delay_derived_from_first_seen"],
                2,
            )

    def test_completeness_policy_excludes_sparse_rows(self) -> None:
        from dataclasses import replace
        from polymarket.feature_engine.dataset_builder import _missingness

        row = _complete_row()
        sparse = replace(
            row,
            market_id="sparse",
            return_5s=None,
            return_15s=None,
            return_30s=None,
        )
        self.assertEqual(_missingness([row])["feature_completeness_percentage"], 100.0)
        self.assertEqual(
            _missingness([sparse])["missing_feature_cells"], 3
        )


def _write_session(path: Path, stop_seconds: int = 300) -> None:
    path.parent.mkdir(parents=True)
    start = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(seconds=300)
    markets = {
        "BTC": {
            "market_id": "btc-window",
            "asset": "BTC",
            "question": "Bitcoin Up or Down",
            "window_start": start.isoformat(),
            "window_end": end.isoformat(),
            "yes_token_id": "btc-yes",
            "no_token_id": "btc-no",
            "liquidity": 10_000,
            "volume": 20_000,
            "active": True,
            "closed": False,
        },
        "ETH": {
            "market_id": "eth-window",
            "asset": "ETH",
            "question": "Ethereum Up or Down",
            "window_start": start.isoformat(),
            "window_end": end.isoformat(),
            "yes_token_id": "eth-yes",
            "no_token_id": "eth-no",
            "liquidity": 10_000,
            "volume": 20_000,
            "active": True,
            "closed": False,
        },
    }
    events = []
    for asset, market in markets.items():
        events.append(_event(start, "market_lifecycle", {
            "previous": "discovered", "current": "discovered", "market": market
        }))
        events.append(_event(start, "lifecycle_tracking", {
            "event": "detected",
            "market_id": market["market_id"],
            "asset": asset,
            "seconds_after_open_when_detected": 5.0,
        }))
    for seconds in range(0, stop_seconds + 1, 5):
        timestamp = start + timedelta(seconds=seconds)
        for asset, base, direction in (("BTC", 100.0, 1), ("ETH", 200.0, -1)):
            price = base + direction * seconds * 0.01
            yes = 0.5 + direction * seconds * 0.0002
            market_id = markets[asset]["market_id"]
            events.append(_event(timestamp, "reference_price", {
                "asset": asset, "price": price, "source": "test",
                "timestamp": timestamp.isoformat(),
            }))
            events.append(_event(timestamp, "polymarket_snapshot", {
                "asset": asset,
                "market_id": market_id,
                "timestamp": timestamp.isoformat(),
                "yes_price": yes,
                "no_price": 1 - yes,
                "yes_bid": yes - 0.01,
                "yes_ask": yes + 0.01,
                "liquidity": 10_000,
                "seconds_to_expiry": 300 - seconds,
            }))
            events.append(_event(timestamp, "lag_measurement", {
                "market_id": market_id,
                "measurement": {
                    "lag_score": 0.6,
                    "confidence": 0.7,
                    "direction": "UP" if direction > 0 else "DOWN",
                },
            }))
    with path.open("w", encoding="utf-8") as handle:
        for event in sorted(events, key=lambda item: item["timestamp"]):
            handle.write(json.dumps(event) + "\n")


def _event(timestamp: datetime, event: str, payload: dict) -> dict:
    return {"event": event, "timestamp": timestamp.isoformat(), "payload": payload}


def _complete_row():
    from polymarket.feature_engine.schema import TrainingRow

    return TrainingRow(
        market_id="complete",
        asset="BTC",
        market_source="public",
        window_start="2026-01-01T12:00:00+00:00",
        window_end="2026-01-01T12:05:00+00:00",
        feature_timestamp="2026-01-01T12:01:00+00:00",
        market_age_seconds=60.0,
        seconds_to_expiry=240.0,
        return_5s=0.1,
        return_15s=0.1,
        return_30s=0.1,
        return_60s=0.1,
        momentum_short=0.0,
        momentum_medium=0.0,
        volatility_30s=0.1,
        volatility_60s=0.1,
        yes_price=0.5,
        no_price=0.5,
        yes_no_spread=0.0,
        probability_change_15s=0.0,
        probability_change_30s=0.0,
        lag_score=0.0,
        confidence_score=0.0,
        detection_delay=0.0,
        early_window_flag=1,
        late_window_flag=0,
        outcome=1,
        resolution_timestamp="2026-01-01T12:05:00+00:00",
        label_source="polymarket_gamma_resolved",
        source_session="test/session.jsonl",
    )


def _workspace_temp() -> tempfile.TemporaryDirectory:
    return tempfile.TemporaryDirectory(dir=Path("tests/polymarket"))


if __name__ == "__main__":
    unittest.main()
