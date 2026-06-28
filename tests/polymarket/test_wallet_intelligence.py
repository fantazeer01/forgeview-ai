import csv
import hashlib
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from polymarket.wallet_intelligence.client import PublicResponse
from polymarket.wallet_intelligence.behavior_metrics import compute_behavior_metrics
from polymarket.wallet_intelligence.ingestion import (
    classify_exposure,
    classify_market_type,
    ingest_wallets,
)
from polymarket.wallet_intelligence.schema import TRADE_HISTORY_FIELDS
from polymarket.wallet_intelligence.trade_history import (
    build_dedupe_key,
    classify_trade_market,
    enforce_fixture_limits,
    normalize_fixture_pages,
    normalize_trade_row,
    raw_page_hash,
    raw_payload_hash,
    run_bounded_public_smoke,
    run_fixture_ingestion,
)
from polymarket.wallet_intelligence.lifecycle import (
    lifecycle_group_key,
    reconstruct_lifecycle_positions,
    run_lifecycle_fixture_reconstruction,
)
from polymarket.wallet_intelligence.lifecycle_metrics import (
    compute_wallet_lifecycle_metrics,
    run_lifecycle_metrics,
)
from polymarket.wallet_intelligence.wallet_score import (
    ALLOWED_SCORE_INPUTS,
    compute_wallet_scores,
    run_wallet_score_fixture,
)
from polymarket.wallet_intelligence.wallet_watchlist import (
    compute_wallet_watchlist,
    run_wallet_watchlist,
)
from polymarket.wallet_intelligence.copyability_sprint import (
    build_copyability_research,
    validate_copyability_research,
)
from polymarket.wallet_intelligence.market_outcome import (
    fetch_market_metadata,
    join_lifecycle_outcomes,
    run_market_outcome_resolution_sprint,
    validate_market_outcome_joins,
)
from polymarket.wallet_intelligence.outcome_skill import (
    build_wallet_outcome_skill_baseline,
    run_wallet_outcome_skill_baseline,
    validate_wallet_outcome_skill,
)
from polymarket.wallet_intelligence.visibility_delay import (
    build_wallet_visibility_delay,
    run_wallet_visibility_delay_sprint,
    validate_wallet_visibility_delay,
)
from polymarket.wallet_intelligence.first_seen import (
    STRONGEST_H1_WALLETS,
    analyze_first_seen_snapshots,
    run_first_seen_from_snapshots,
)
from polymarket.wallet_intelligence.first_seen_prospective import (
    ProspectiveFirstSeenStore,
    prepare_prospective_experiment,
    render_dataset,
    validate_restart_and_duplicates,
)
from polymarket.wallet_intelligence.decision_window import (
    build_decision_windows,
    classify_decision_window,
    run_wallet_decision_window_sprint,
)
from polymarket.wallet_intelligence.evidence_accumulator import (
    EvidenceAccumulatorStore,
    background_command,
    build_accumulated_evidence,
    evaluate_h2_h3_gates,
    prepare_accumulator_progress,
    run_autonomous_accumulator,
)


class FakeClient:
    def __init__(self):
        self.pages = {
            "https://polymarket.com/@alias": """
            <html><script id="__NEXT_DATA__" type="application/json">
            {"props":{"pageProps":{"profile":{"username":"alias","proxyWallet":"0x1111111111111111111111111111111111111111"}}}}
            </script></html>
            """
        }

    def get_text(self, url):
        return PublicResponse(url=url, status_code=200, payload=self.pages[url])

    def positions(self, user, limit=50):
        payload = []
        if user == "0x1111111111111111111111111111111111111111":
            payload = [
                {
                    "title": "Ethereum Up or Down - June 24, 1:00PM-1:15PM ET",
                    "slug": "eth-updown-15m-fixture",
                    "eventSlug": "eth-updown-15m-fixture",
                    "outcome": "Down",
                    "avgPrice": 0.18,
                    "curPrice": 0.22,
                    "totalBought": 50,
                    "cashPnl": 2,
                    "endDate": "2026-06-24T17:15:00Z",
                }
            ]
        return PublicResponse(url=f"https://data-api.polymarket.com/positions?user={user}", status_code=200, payload=payload)

    def closed_positions(self, user, limit=50, offset=0):
        payload = []
        if user == "0x0000000000000000000000000000000000000001":
            payload = [
                {
                    "title": "Bitcoin Up or Down - June 24, 1:00PM-1:15PM ET",
                    "slug": "btc-updown-15m-fixture",
                    "eventSlug": "btc-updown-15m-fixture",
                    "outcome": "Up",
                    "avgPrice": 0.12,
                    "curPrice": 1,
                    "totalBought": 100,
                    "realizedPnl": 88,
                    "timestamp": 1782314100,
                    "endDate": "2026-06-24T17:15:00Z",
                },
                {
                    "title": "Will it rain in New York on June 24?",
                    "slug": "rain-new-york-fixture",
                    "eventSlug": "rain-new-york-fixture",
                    "outcome": "No",
                    "avgPrice": 0.65,
                    "curPrice": 0,
                    "totalBought": 20,
                    "realizedPnl": -20,
                    "timestamp": 1782314100,
                    "endDate": "2026-06-24T23:59:00Z",
                },
            ]
        return PublicResponse(url=f"https://data-api.polymarket.com/closed-positions?user={user}", status_code=200, payload=payload)

    def activity(self, user, limit=50):
        return PublicResponse(url=f"https://data-api.polymarket.com/activity?user={user}", status_code=200, payload=[])

    def value(self, user):
        return PublicResponse(url=f"https://data-api.polymarket.com/value?user={user}", status_code=200, payload=[{"user": user, "value": 0}])

    def traded(self, user):
        return PublicResponse(url=f"https://data-api.polymarket.com/traded?user={user}", status_code=200, payload={"user": user, "traded": 12})


class WalletIntelligenceIngestionTests(unittest.TestCase):
    def test_market_classification(self):
        self.assertEqual(classify_market_type("Bitcoin Up or Down", "btc-updown-15m"), "fast_crypto")
        self.assertEqual(classify_market_type("Will it rain?", "rain-nyc"), "weather")
        self.assertEqual(classify_exposure("Solana Up or Down", "sol-updown-15m"), "SOL")

    def test_ingest_wallets_writes_normalized_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "watched.csv"
            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["wallet_id", "profile_url", "label", "source", "notes"])
                writer.writeheader()
                writer.writerow(
                    {
                        "wallet_id": "0x0000000000000000000000000000000000000001",
                        "profile_url": "https://polymarket.com/0x0000000000000000000000000000000000000001",
                        "label": "fixture",
                        "source": "test",
                        "notes": "direct wallet",
                    }
                )
                writer.writerow(
                    {
                        "wallet_id": "@alias",
                        "profile_url": "https://polymarket.com/@alias",
                        "label": "fixture",
                        "source": "test",
                        "notes": "alias wallet",
                    }
                )
            output_dir = root / "out"
            summary = ingest_wallets(
                input_path,
                output_dir,
                client=FakeClient(),
                retrieved_at="2026-06-24T00:00:00+00:00",
            )

            self.assertEqual(summary["wallets_attempted"], 2)
            self.assertEqual(summary["wallets_resolved"], 2)
            self.assertIn("0x0000000000000000000000000000000000000001", summary["fast_market_crypto_wallets"])
            self.assertTrue((output_dir / "wallets_raw.jsonl").exists())
            self.assertTrue((output_dir / "wallet_profiles.csv").exists())
            self.assertTrue((output_dir / "wallet_positions.csv").exists())
            self.assertTrue((output_dir / "ingestion_report.md").exists())

            with (output_dir / "wallet_profiles.csv").open("r", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["closed_positions_count"], "2")
            self.assertIn("average_holding_time", rows[0]["data_availability_notes"])
            persisted = json.loads((output_dir / "wallet_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(persisted["recommended_next_task"], "Wallet Intelligence Behavior Metrics v1")

    def test_behavior_metrics_from_existing_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "input"
            output_dir = root / "metrics"
            input_dir.mkdir()
            with (input_dir / "wallet_profiles.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "wallet_id",
                        "profile_url",
                        "active_positions_count",
                        "closed_positions_count",
                        "data_availability_notes",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "wallet_id": "0xaaa",
                        "profile_url": "https://polymarket.com/0xaaa",
                        "active_positions_count": "0",
                        "closed_positions_count": "3",
                        "data_availability_notes": "closed_positions may be truncated at public snapshot limit 50",
                    }
                )
                writer.writerow(
                    {
                        "wallet_id": "0xbbb",
                        "profile_url": "https://polymarket.com/0xbbb",
                        "active_positions_count": "0",
                        "closed_positions_count": "3",
                        "data_availability_notes": "",
                    }
                )
            fields = [
                "wallet_id",
                "profile_url",
                "position_status",
                "title",
                "slug",
                "outcome",
                "avg_price",
                "cur_price",
                "total_bought",
                "market_type",
                "asset_exposure",
            ]
            with (input_dir / "wallet_positions.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                fast_fixture_rows = [
                    ("BTC", "0.12", "Up"),
                    ("ETH", "0.18", "Down"),
                    ("SOL", "0.35", "Up"),
                    ("BTC", "0.12", "Up"),
                    ("ETH", "0.18", "Down"),
                    ("SOL", "0.35", "Up"),
                    ("BTC", "0.12", "Up"),
                    ("ETH", "0.18", "Down"),
                    ("SOL", "0.35", "Up"),
                    ("BTC", "0.12", "Up"),
                ]
                for asset, price, outcome in fast_fixture_rows:
                    writer.writerow(
                        {
                            "wallet_id": "0xaaa",
                            "profile_url": "https://polymarket.com/0xaaa",
                            "position_status": "closed",
                            "title": f"{asset} Up or Down",
                            "slug": f"{asset.lower()}-updown-15m",
                            "outcome": outcome,
                            "avg_price": price,
                            "cur_price": "1",
                            "total_bought": "100",
                            "market_type": "fast_crypto",
                            "asset_exposure": asset,
                        }
                    )
                for price in ("0.45", "0.55", "0.65", "0.45", "0.55", "0.65", "0.45", "0.55", "0.65", "0.45"):
                    writer.writerow(
                        {
                            "wallet_id": "0xbbb",
                            "profile_url": "https://polymarket.com/0xbbb",
                            "position_status": "closed",
                            "title": "Will it rain?",
                            "slug": "rain-fixture",
                            "outcome": "No",
                            "avg_price": price,
                            "cur_price": "0",
                            "total_bought": "10",
                            "market_type": "weather",
                            "asset_exposure": "OTHER",
                        }
                    )

            report = compute_behavior_metrics(input_dir, output_dir, generated_at="2026-06-24T00:00:00+00:00")
            self.assertEqual(report["wallets_analyzed"], 2)
            self.assertEqual(report["strongest_fast_market_wallet"], "0xaaa")
            self.assertTrue((output_dir / "wallet_behavior_metrics.csv").exists())
            self.assertTrue((output_dir / "wallet_similarity_matrix.csv").exists())
            with (output_dir / "wallet_behavior_metrics.csv").open("r", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["wallet_classification"], "fast_crypto_focused")
            self.assertEqual(rows[0]["entry_bucket_10_20c"], "7")
            self.assertEqual(rows[1]["wallet_classification"], "weather_focused")


class WalletTradeHistoryFixtureTests(unittest.TestCase):
    def _row(self, **overrides):
        row = {
            "proxyWallet": "0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a",
            "timestamp": 1771327653,
            "conditionId": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "type": "TRADE",
            "size": 102.13265,
            "usdcSize": 100.09,
            "transactionHash": "0x1111111111111111111111111111111111111111111111111111111111111111",
            "price": 0.98,
            "asset": "12345678901234567890",
            "side": "BUY",
            "outcomeIndex": 1,
            "title": "Bitcoin Up or Down - Fixture",
            "slug": "btc-updown-15m-1771326900",
            "eventSlug": "btc-updown-15m-1771326900",
            "outcome": "Down",
        }
        row.update(overrides)
        return row

    def test_trade_history_schema_has_35_fields(self):
        self.assertEqual(len(TRADE_HISTORY_FIELDS), 35)
        self.assertIn("raw_payload_hash", TRADE_HISTORY_FIELDS)
        self.assertIn("dedupe_key", TRADE_HISTORY_FIELDS)

    def test_normalizes_normal_trade_row(self):
        raw = self._row()
        page_hash = raw_page_hash([raw])
        record = normalize_trade_row(
            raw,
            wallet_id="0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a",
            profile_url="https://polymarket.com/0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a",
            source_endpoint="https://data-api.polymarket.com/activity?fixture",
            source_endpoint_name="activity_primary",
            source_fetch_timestamp="2026-06-24T00:00:00+00:00",
            page_hash=page_hash,
        )
        self.assertEqual(record.market_type, "fast_crypto_up_down")
        self.assertEqual(record.asset_class, "BTC")
        self.assertEqual(record.up_down_market, "true")
        self.assertEqual(record.entry_or_exit_candidate, "entry_candidate")
        self.assertEqual(record.raw_payload_hash, raw_payload_hash(raw))
        self.assertEqual(record.raw_page_hash, page_hash)
        self.assertTrue(record.activity_datetime_utc.endswith("+00:00"))

    def test_missing_optional_fields_are_flagged_and_computed(self):
        raw = self._row(eventSlug="", usdcSize=None)
        record = normalize_trade_row(
            raw,
            wallet_id="0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a",
            profile_url="https://polymarket.com/wallet",
            source_endpoint="endpoint",
            source_endpoint_name="activity_primary",
            source_fetch_timestamp="2026-06-24T00:00:00+00:00",
            page_hash=raw_page_hash([raw]),
        )
        self.assertEqual(record.notional_source, "computed_price_times_size")
        self.assertIn("missing_event_slug", record.data_quality_flags)
        self.assertIn("computed_notional", record.data_quality_flags)

    def test_duplicate_trade_row_is_removed(self):
        raw = self._row()
        pages = [
            {
                "wallet_id": "0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a",
                "profile_url": "https://polymarket.com/wallet",
                "source_endpoint": "endpoint",
                "source_endpoint_name": "activity_primary",
                "source_fetch_timestamp": "2026-06-24T00:00:00+00:00",
                "rows": [raw, dict(raw)],
            }
        ]
        records, metadata = normalize_fixture_pages(pages)
        self.assertEqual(len(records), 1)
        self.assertEqual(metadata["duplicate_rows_removed"], 1)
        self.assertEqual(records[0].dedupe_key, build_dedupe_key(records[0].__dict__))

    def test_eth_sol_and_non_crypto_classification(self):
        self.assertEqual(classify_trade_market("Ethereum Up or Down", "eth-updown-15m"), ("fast_crypto_up_down", "ETH", True))
        self.assertEqual(classify_trade_market("Solana Up or Down", "sol-updown-15m"), ("fast_crypto_up_down", "SOL", True))
        self.assertEqual(classify_trade_market("Will it rain?", "rain-new-york"), ("weather", "other", False))

    def test_bounded_pagination_enforcement(self):
        limits = {
            "first_ingestion_scope": {
                "max_wallets": 1,
                "max_rows_per_wallet_primary_activity": 1,
                "max_pages_per_wallet_primary_activity": 1,
                "max_total_activity_rows": 1,
            }
        }
        violations = enforce_fixture_limits(
            wallet_count=2,
            rows_by_wallet={"0x1": 2},
            pages_by_wallet={"0x1": 2},
            limits=limits,
        )
        self.assertIn("wallet_count_exceeds_limit", violations)
        self.assertIn("total_activity_rows_exceeds_limit", violations)
        self.assertIn("rows_exceed_limit:0x1", violations)
        self.assertIn("pages_exceed_limit:0x1", violations)

    def test_fixture_ingestion_writes_deterministic_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = root / "fixture.jsonl"
            rows = [
                self._row(),
                self._row(
                    transactionHash="0x2222222222222222222222222222222222222222222222222222222222222222",
                    title="Ethereum Up or Down - Fixture",
                    slug="eth-updown-15m-1771326900",
                    eventSlug="eth-updown-15m-1771326900",
                    asset="22345678901234567890",
                ),
                self._row(
                    transactionHash="0x3333333333333333333333333333333333333333333333333333333333333333",
                    title="Solana Up or Down - Fixture",
                    slug="sol-updown-15m-1771326900",
                    eventSlug="sol-updown-15m-1771326900",
                    asset="32345678901234567890",
                ),
                self._row(
                    transactionHash="0x4444444444444444444444444444444444444444444444444444444444444444",
                    title="Will it rain in New York?",
                    slug="rain-new-york-fixture",
                    eventSlug="rain-new-york-fixture",
                    asset="42345678901234567890",
                    outcome="No",
                ),
            ]
            fixture.write_text(
                json.dumps(
                    {
                        "wallet_id": "0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a",
                        "profile_url": "https://polymarket.com/wallet",
                        "url": "https://data-api.polymarket.com/activity?fixture",
                        "source_fetch_timestamp": "2026-06-24T00:00:00+00:00",
                        "payload": rows,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            limits = root / "limits.json"
            limits.write_text(
                json.dumps(
                    {
                        "first_ingestion_scope": {
                            "max_wallets": 6,
                            "max_rows_per_wallet_primary_activity": 300,
                            "max_pages_per_wallet_primary_activity": 3,
                            "max_total_activity_rows": 1800,
                        }
                    }
                ),
                encoding="utf-8",
            )
            output = root / "out"
            report = run_fixture_ingestion(
                fixture,
                output,
                limits_path=limits,
                generated_at="2026-06-24T00:00:00+00:00",
            )
            self.assertTrue(report["validation_gates_passed"])
            self.assertEqual(report["normalized_rows"], 4)
            self.assertTrue((output / "raw_trades_fixture.jsonl").exists())
            self.assertTrue((output / "normalized_trades_fixture.csv").exists())
            self.assertTrue((output / "fixture_ingestion_report.md").exists())
            hashes = json.loads((output / "reproducibility_hashes.json").read_text(encoding="utf-8"))
            self.assertTrue(hashes["csv_repeat_export_hash_match"])
            second = run_fixture_ingestion(
                fixture,
                output,
                limits_path=limits,
                generated_at="2026-06-24T00:00:00+00:00",
            )
            hashes_second = json.loads((output / "reproducibility_hashes.json").read_text(encoding="utf-8"))
            self.assertEqual(report["normalized_rows"], second["normalized_rows"])
            self.assertEqual(
                hashes["normalized_trades_fixture_csv_sha256"],
                hashes_second["normalized_trades_fixture_csv_sha256"],
            )

    def test_safety_no_execution_methods_on_trade_history_module(self):
        import polymarket.wallet_intelligence.trade_history as trade_history

        names = dir(trade_history)
        forbidden_fragments = ("private_key", "place_order", "copy_trade", "execute_trade", "wallet_connect")
        for fragment in forbidden_fragments:
            self.assertFalse(any(fragment in name.lower() for name in names))

    def test_bounded_public_smoke_with_mocked_client(self):
        class FakeSmokeClient:
            def __init__(self, base_row):
                self.calls = []
                self.base_row = base_row

            def activity_trades(self, user, limit=100, offset=0):
                self.calls.append((user, limit, offset))
                payload = [
                    self.base_row,
                    {
                        **self.base_row,
                        "transactionHash": "0x5555555555555555555555555555555555555555555555555555555555555555",
                        "title": "Ethereum Up or Down - Fixture",
                        "slug": "eth-updown-15m-1771326900",
                        "eventSlug": "eth-updown-15m-1771326900",
                        "asset": "52345678901234567890",
                    },
                ]
                return PublicResponse(
                    url=f"https://data-api.polymarket.com/activity?user={user}&type=TRADE&limit={limit}&offset={offset}",
                    status_code=200,
                    payload=payload,
                )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watched = root / "watched.csv"
            profiles = root / "profiles.csv"
            with watched.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["wallet_id", "profile_url", "label", "source", "notes"])
                writer.writeheader()
                writer.writerow(
                    {
                        "wallet_id": "0x0000000000000000000000000000000000000001",
                        "profile_url": "https://polymarket.com/0x0000000000000000000000000000000000000001",
                        "label": "seed",
                        "source": "test",
                        "notes": "",
                    }
                )
                writer.writerow(
                    {
                        "wallet_id": "0x0000000000000000000000000000000000000002",
                        "profile_url": "https://polymarket.com/0x0000000000000000000000000000000000000002",
                        "label": "seed",
                        "source": "test",
                        "notes": "",
                    }
                )
            with profiles.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["wallet_id", "profile_url"])
                writer.writeheader()
                writer.writerow(
                    {
                        "wallet_id": "0x0000000000000000000000000000000000000001",
                        "profile_url": "https://polymarket.com/0x0000000000000000000000000000000000000001",
                    }
                )
                writer.writerow(
                    {
                        "wallet_id": "0x0000000000000000000000000000000000000002",
                        "profile_url": "https://polymarket.com/0x0000000000000000000000000000000000000002",
                    }
                )
            limits = root / "limits.json"
            limits.write_text(
                json.dumps(
                    {
                        "first_ingestion_scope": {
                            "max_wallets": 6,
                            "page_size": 100,
                            "max_rows_per_wallet_primary_activity": 300,
                            "max_pages_per_wallet_primary_activity": 3,
                            "max_total_activity_rows": 1800,
                        }
                    }
                ),
                encoding="utf-8",
            )
            client = FakeSmokeClient(self._row())
            output = root / "smoke"
            report = run_bounded_public_smoke(
                client=client,
                watched_wallets_path=watched,
                wallet_profiles_path=profiles,
                output_dir=output,
                limits_path=limits,
                max_wallets=2,
                page_size=100,
                max_pages_per_wallet=1,
                generated_at="2026-06-24T00:00:00+00:00",
            )
            self.assertEqual(len(client.calls), 2)
            self.assertEqual(report["wallets_attempted"], 2)
            self.assertEqual(report["wallets_succeeded"], 2)
            self.assertEqual(report["rows_fetched"], 4)
            self.assertEqual(report["rows_normalized"], 4)
            self.assertTrue(report["validation_gates_passed"])
            self.assertTrue((output / "trade_history_raw.jsonl").exists())
            self.assertTrue((output / "trade_history_normalized.csv").exists())
            self.assertTrue((output / "bounded_smoke_report.md").exists())


class WalletLifecycleReconstructionTests(unittest.TestCase):
    def _trade(self, **overrides):
        row = {
            "wallet_id": "0xwallet",
            "profile_url": "https://polymarket.com/0xwallet",
            "source_endpoint": "fixture",
            "source_endpoint_name": "activity_primary",
            "activity_type": "TRADE",
            "activity_timestamp": "1771327000",
            "activity_datetime_utc": "2026-02-17T10:36:40+00:00",
            "transaction_hash": "0xaaa",
            "condition_id": "0xcond",
            "token_id": "123",
            "asset_id": "123",
            "market_slug": "btc-updown-15m-fixture",
            "event_slug": "btc-updown-15m-fixture",
            "market_title": "Bitcoin Up or Down - Fixture",
            "outcome": "Up",
            "outcome_index": "0",
            "side": "BUY",
            "price": "0.2",
            "size": "10",
            "notional_value": "2",
            "notional_source": "computed_price_times_size",
            "market_type": "fast_crypto_up_down",
            "asset_class": "BTC",
            "up_down_market": "true",
            "time_to_expiry_seconds": "",
            "expiry_timestamp": "",
            "expiry_source": "unavailable",
            "entry_or_exit_candidate": "entry_candidate",
            "lifecycle_group_key": "0xwallet|0xcond|123|Up",
            "dedupe_key": "dedupe",
            "source_fetch_timestamp": "2026-06-24T00:00:00+00:00",
            "raw_payload_hash": "hash",
            "raw_page_hash": "page",
            "normalization_version": "wallet_trade_history_v1",
            "data_quality_flags": "none",
        }
        row.update(overrides)
        return row

    def test_reconstructs_still_open_position(self):
        positions, summary = reconstruct_lifecycle_positions([self._trade()])
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0].status, "still_open")
        self.assertEqual(positions[0].remaining_size, "10")
        self.assertTrue(summary["validation"]["position_size_conservation"])

    def test_reconstructs_partial_and_full_exits(self):
        partial_rows = [
            self._trade(size="10", price="0.2", transaction_hash="0x001"),
            self._trade(
                side="SELL",
                size="4",
                price="0.7",
                transaction_hash="0x002",
                activity_timestamp="1771327100",
                entry_or_exit_candidate="exit_candidate",
            ),
        ]
        positions, _ = reconstruct_lifecycle_positions(partial_rows)
        self.assertEqual(positions[0].status, "partial_exit")
        self.assertEqual(positions[0].remaining_size, "6")
        self.assertEqual(positions[0].weighted_average_exit_price, "0.7")

        full_rows = [
            self._trade(size="10", transaction_hash="0x003"),
            self._trade(
                side="SELL",
                size="10",
                price="0.9",
                transaction_hash="0x004",
                activity_timestamp="1771327200",
                entry_or_exit_candidate="exit_candidate",
            ),
        ]
        positions, _ = reconstruct_lifecycle_positions(full_rows)
        self.assertEqual(positions[0].status, "full_exit")
        self.assertEqual(positions[0].remaining_size, "0")

    def test_negative_position_is_flagged_as_bounded_history_gap(self):
        positions, summary = reconstruct_lifecycle_positions(
            [
                self._trade(
                    side="SELL",
                    size="5",
                    transaction_hash="0x005",
                    entry_or_exit_candidate="exit_candidate",
                )
            ]
        )
        self.assertEqual(positions[0].status, "oversold_bounded_history")
        self.assertEqual(positions[0].negative_position_detected, "true")
        self.assertTrue(summary["validation"]["no_unexpected_negative_position_size"])
        self.assertEqual(len(summary["validation"]["bounded_history_negative_position_groups"]), 1)

    def test_reconstruction_is_deterministically_ordered_and_repeatable(self):
        rows = [
            self._trade(
                wallet_id="0xbbb",
                lifecycle_group_key="0xbbb|0xcond|123|Up",
                transaction_hash="0xbbb",
            ),
            self._trade(
                wallet_id="0xaaa",
                lifecycle_group_key="0xaaa|0xcond|123|Up",
                transaction_hash="0xaaa",
            ),
        ]
        first_positions, first_summary = reconstruct_lifecycle_positions(rows)
        second_positions, second_summary = reconstruct_lifecycle_positions(list(reversed(rows)))
        self.assertEqual([p.lifecycle_group_key for p in first_positions], ["0xaaa|0xcond|123|Up", "0xbbb|0xcond|123|Up"])
        self.assertEqual([p.lifecycle_group_key for p in first_positions], [p.lifecycle_group_key for p in second_positions])
        self.assertEqual(first_summary["validation"], second_summary["validation"])

    def test_lifecycle_group_key_is_computed_from_explicit_fields(self):
        row = self._trade(
            wallet_id="0xABC",
            condition_id="0xDEF",
            token_id="456",
            outcome="Down",
            lifecycle_group_key="stale|wrong|key|Up",
        )
        positions, _ = reconstruct_lifecycle_positions([row])
        self.assertEqual(lifecycle_group_key(row), "0xabc|0xdef|456|Down")
        self.assertEqual(positions[0].lifecycle_group_key, "0xabc|0xdef|456|Down")

    def test_lifecycle_fixture_cli_outputs_are_repeatable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_csv = root / "trade_history.csv"
            with input_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=TRADE_HISTORY_FIELDS)
                writer.writeheader()
                writer.writerow(self._trade())
                writer.writerow(
                    self._trade(
                        side="SELL",
                        size="10",
                        price="0.8",
                        transaction_hash="0x006",
                        activity_timestamp="1771327300",
                        entry_or_exit_candidate="exit_candidate",
                    )
                )
            output = root / "lifecycle"
            first = run_lifecycle_fixture_reconstruction(
                input_csv,
                output,
                generated_at="2026-06-24T00:00:00+00:00",
            )
            second = run_lifecycle_fixture_reconstruction(
                input_csv,
                output,
                generated_at="2026-06-24T00:00:00+00:00",
            )
            self.assertEqual(first["lifecycle_positions"], 1)
            self.assertTrue(first["validation"]["repeatable_output"])
            self.assertEqual(
                first["reproducibility_hashes"]["lifecycle_positions_csv_sha256"],
                second["reproducibility_hashes"]["lifecycle_positions_csv_sha256"],
            )
            self.assertTrue((output / "lifecycle_positions.csv").exists())
            self.assertTrue((output / "lifecycle_summary.json").exists())

    def test_lifecycle_module_has_no_execution_methods(self):
        import polymarket.wallet_intelligence.lifecycle as lifecycle

        names = dir(lifecycle)
        forbidden_fragments = ("private_key", "place_order", "copy_trade", "execute_trade", "wallet_connect")
        for fragment in forbidden_fragments:
            self.assertFalse(any(fragment in name.lower() for name in names))


class WalletLifecycleMetricsTests(unittest.TestCase):
    def _position(self, **overrides):
        row = {
            "wallet_id": "0xwallet",
            "profile_url": "https://polymarket.com/0xwallet",
            "condition_id": "0xcond",
            "token_id": "123",
            "outcome": "Up",
            "lifecycle_group_key": "0xwallet|0xcond|123|Up",
            "market_slug": "btc-updown-15m-fixture",
            "event_slug": "btc-updown-15m-fixture",
            "market_title": "Bitcoin Up or Down - Fixture",
            "market_type": "fast_crypto_up_down",
            "asset_class": "BTC",
            "up_down_market": "true",
            "first_activity_timestamp": "1771327000",
            "first_activity_datetime_utc": "2026-02-17T10:36:40+00:00",
            "last_activity_timestamp": "1771327000",
            "last_activity_datetime_utc": "2026-02-17T10:36:40+00:00",
            "buy_trade_count": "1",
            "sell_trade_count": "0",
            "total_bought_size": "10",
            "total_sold_size": "0",
            "remaining_size": "10",
            "oversold_size": "0",
            "weighted_average_entry_price": "0.2",
            "weighted_average_exit_price": "",
            "status": "still_open",
            "negative_position_detected": "false",
            "negative_position_reason": "",
            "position_size_conserved": "true",
            "transaction_hashes": "0xaaa",
            "data_quality_flags": "none",
        }
        row.update(overrides)
        return row

    def test_computes_structural_wallet_metrics(self):
        rows = [
            self._position(total_bought_size="10", remaining_size="10", buy_trade_count="1"),
            self._position(
                lifecycle_group_key="0xwallet|0xcond|456|Down",
                token_id="456",
                outcome="Down",
                status="partial_exit",
                buy_trade_count="2",
                sell_trade_count="1",
                total_bought_size="5",
                total_sold_size="4.95",
                remaining_size="0.05",
            ),
            self._position(
                wallet_id="0xother",
                profile_url="https://polymarket.com/0xother",
                lifecycle_group_key="0xother|0xcond|789|Up",
                status="oversold_bounded_history",
                buy_trade_count="0",
                sell_trade_count="1",
                total_bought_size="0",
                total_sold_size="3",
                remaining_size="0",
                oversold_size="3",
            ),
        ]
        metrics, summary = compute_wallet_lifecycle_metrics(rows)
        self.assertEqual(summary["wallets_analyzed"], 2)
        self.assertTrue(summary["validation"]["all_validation_passed"])
        first = metrics[0]
        self.assertEqual(first["wallet_id"], "0xother")
        self.assertEqual(first["percentage_sell_only_lifecycles"], "1")
        second = metrics[1]
        self.assertEqual(second["total_lifecycle_positions"], "2")
        self.assertEqual(second["still_open_positions"], "1")
        self.assertEqual(second["partial_exits"], "1")
        self.assertEqual(second["near_flat_residual_count"], "1")
        self.assertEqual(second["average_events_per_lifecycle"], "2")

    def test_lifecycle_metrics_writes_deterministic_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_csv = root / "lifecycle_positions.csv"
            with input_csv.open("w", encoding="utf-8", newline="") as handle:
                fieldnames = list(self._position().keys())
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(self._position())
                writer.writerow(
                    self._position(
                        lifecycle_group_key="0xwallet|0xcond|456|Down",
                        token_id="456",
                        outcome="Down",
                        status="full_exit",
                        buy_trade_count="1",
                        sell_trade_count="1",
                        total_bought_size="7",
                        total_sold_size="7",
                        remaining_size="0",
                    )
                )
            output = root / "metrics"
            first = run_lifecycle_metrics(
                input_csv,
                output,
                generated_at="2026-06-24T00:00:00+00:00",
            )
            second = run_lifecycle_metrics(
                input_csv,
                output,
                generated_at="2026-06-24T00:00:00+00:00",
            )
            self.assertTrue(first["validation"]["all_validation_passed"])
            self.assertTrue(first["validation"]["deterministic_csv_repeat_export"])
            self.assertEqual(
                first["reproducibility_hashes"]["wallet_metrics_csv_sha256"],
                second["reproducibility_hashes"]["wallet_metrics_csv_sha256"],
            )
            self.assertTrue((output / "wallet_metrics.csv").exists())
            self.assertTrue((output / "wallet_metrics_summary.json").exists())
            self.assertTrue((output / "wallet_metrics_report.md").exists())

    def test_lifecycle_metrics_module_has_no_execution_or_scoring_methods(self):
        import polymarket.wallet_intelligence.lifecycle_metrics as lifecycle_metrics

        names = dir(lifecycle_metrics)
        forbidden_fragments = (
            "private_key",
            "place_order",
            "copy_trade",
            "execute_trade",
            "wallet_connect",
            "sharpe",
            "roi",
        )
        for fragment in forbidden_fragments:
            self.assertFalse(any(fragment in name.lower() for name in names))


class WalletScoreFixtureTests(unittest.TestCase):
    def _metric(self, **overrides):
        row = {
            "wallet_id": "0xwallet",
            "profile_url": "https://polymarket.com/0xwallet",
            "total_lifecycle_positions": "50",
            "still_open_positions": "20",
            "partial_exits": "25",
            "full_exits": "0",
            "oversold_bounded_history": "0",
            "average_position_size": "100",
            "median_position_size": "100",
            "average_buy_count_per_lifecycle": "1.2",
            "average_sell_count_per_lifecycle": "0.6",
            "average_events_per_lifecycle": "1.8",
            "percentage_still_open_positions": "0.4",
            "percentage_sell_only_lifecycles": "0",
            "buy_trade_count": "60",
            "sell_trade_count": "30",
            "total_visible_bought_size": "5000",
            "total_visible_sold_size": "3000",
            "remaining_visible_size": "2000",
            "oversold_visible_size": "0",
            "near_flat_residual_count": "1",
            "fast_crypto_lifecycle_count": "50",
            "fast_crypto_lifecycle_share": "1",
            "dominant_asset": "BTC",
            "asset_concentration": "0.8",
            "dominant_outcome": "Down",
            "outcome_concentration": "0.6",
        }
        row.update(overrides)
        return row

    def test_computes_bounded_structural_scores_only(self):
        rows = [
            self._metric(),
            self._metric(
                wallet_id="0xsmall",
                total_lifecycle_positions="6",
                fast_crypto_lifecycle_count="6",
                fast_crypto_lifecycle_share="1",
                partial_exits="0",
                average_sell_count_per_lifecycle="0",
                average_events_per_lifecycle="20",
                percentage_still_open_positions="1",
                oversold_bounded_history="0",
                near_flat_residual_count="0",
            ),
        ]
        scores, summary = compute_wallet_scores(rows, source_metrics_sha256="hash")
        self.assertTrue(summary["validation"]["all_validation_passed"])
        self.assertEqual(scores[0]["wallet_id"], "0xwallet")
        self.assertEqual(scores[0]["wallet_score"], "83")
        self.assertEqual(scores[0]["score_band"], "high_priority")
        self.assertEqual(scores[1]["small_sample_penalty"], "10")
        self.assertEqual(scores[1]["still_open_penalty"], "15")
        self.assertEqual(summary["forbidden_input_audit"]["forbidden_inputs_used"], [])
        self.assertEqual(sorted(summary["forbidden_input_audit"]["allowed_score_inputs"]), sorted(ALLOWED_SCORE_INPUTS))

    def test_missing_required_metric_fails_validation_without_guessing(self):
        row = self._metric()
        del row["fast_crypto_lifecycle_share"]
        scores, summary = compute_wallet_scores([row], source_metrics_sha256="hash")
        self.assertEqual(scores[0]["missing_required_metric_count"], "1")
        self.assertFalse(summary["validation"]["missing_metric_handling"])
        self.assertFalse(summary["validation"]["all_validation_passed"])
        self.assertIn("fast_crypto_lifecycle_share", summary["validation"]["missing_source_fields"])

    def test_wallet_score_fixture_writes_deterministic_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_csv = root / "wallet_metrics.csv"
            rows = [
                self._metric(wallet_id="0xbbb"),
                self._metric(wallet_id="0xaaa", total_lifecycle_positions="10", fast_crypto_lifecycle_count="0", fast_crypto_lifecycle_share="0"),
            ]
            with input_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)
            output = root / "score"
            first = run_wallet_score_fixture(
                input_csv,
                output,
                generated_at="2026-06-26T00:00:00+00:00",
            )
            second = run_wallet_score_fixture(
                input_csv,
                output,
                generated_at="2026-06-26T00:00:00+00:00",
            )
            self.assertTrue(first["validation"]["all_validation_passed"])
            self.assertTrue(first["validation"]["repeatable_export"])
            self.assertEqual(
                first["reproducibility_hashes"]["wallet_scores_csv_sha256"],
                second["reproducibility_hashes"]["wallet_scores_csv_sha256"],
            )
            self.assertTrue((output / "wallet_scores.csv").exists())
            self.assertTrue((output / "wallet_scores_summary.json").exists())
            self.assertTrue((output / "wallet_score_validation.json").exists())
            self.assertTrue((output / "wallet_score_report.md").exists())
            with (output / "wallet_scores.csv").open("r", encoding="utf-8") as handle:
                score_rows = list(csv.DictReader(handle))
            self.assertEqual(score_rows[0]["wallet_id"], "0xbbb")
            self.assertEqual(score_rows[0]["source_metrics_sha256"], first["source_metrics_sha256"])

    def test_wallet_score_module_has_no_execution_or_forbidden_metric_methods(self):
        import polymarket.wallet_intelligence.wallet_score as wallet_score

        names = dir(wallet_score)
        forbidden_fragments = (
            "private_key",
            "place_order",
            "copy_trade",
            "execute_trade",
            "wallet_connect",
            "sharpe_ratio",
            "compute_pnl",
            "compute_roi",
        )
        for fragment in forbidden_fragments:
            self.assertFalse(any(fragment in name.lower() for name in names))


class WalletWatchlistTests(unittest.TestCase):
    def _score(self, **overrides):
        row = {
            "wallet_id": "0xwallet",
            "profile_url": "https://polymarket.com/0xwallet",
            "wallet_score": "73",
            "score_band": "medium_priority",
            "score_version": "wallet_score_v1_structural_fixture",
            "total_lifecycle_positions": "40",
            "missing_required_metric_count": "0",
            "fast_crypto_lifecycle_share": "1",
            "partial_exits": "12",
            "percentage_still_open_positions": "0.5",
            "bounded_history_penalty": "0",
            "oversold_bounded_history": "0",
            "concentration_penalty": "4",
            "small_sample_penalty": "0",
            "near_flat_ambiguity_penalty": "2",
            "event_density_component": "8",
            "specialization_component": "8",
        }
        row.update(overrides)
        return row

    def test_watchlist_uses_score_outputs_and_minimum_visibility(self):
        rows = [
            self._score(wallet_id="0xbbb", wallet_score="73", score_band="medium_priority"),
            self._score(
                wallet_id="0xaaa",
                wallet_score="44",
                score_band="low_priority",
                total_lifecycle_positions="12",
                partial_exits="0",
                fast_crypto_lifecycle_share="0",
            ),
            self._score(
                wallet_id="0xsmall",
                wallet_score="10",
                score_band="insufficient_visible_structure",
                total_lifecycle_positions="4",
            ),
        ]
        watchlist, summary = compute_wallet_watchlist(rows, source_scores_sha256="score-hash")
        self.assertEqual([row["wallet_id"] for row in watchlist], ["0xbbb", "0xaaa"])
        self.assertEqual(summary["wallets_included"], 2)
        self.assertEqual(summary["wallets_excluded"], 1)
        self.assertTrue(summary["validation"]["reason_codes_present"])
        self.assertTrue(summary["validation"]["no_forbidden_metric_fields"])
        self.assertTrue(summary["validation"]["no_forbidden_claims"])
        self.assertIn("fast_crypto_relevant", watchlist[0]["reason_codes"])
        self.assertIn("no_fast_crypto_visibility", watchlist[1]["reason_codes"])

    def test_watchlist_export_is_repeatable_and_report_has_disclaimers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_csv = root / "wallet_scores.csv"
            rows = [
                self._score(wallet_id="0xbbb", wallet_score="73", score_band="medium_priority"),
                self._score(wallet_id="0xaaa", wallet_score="44", score_band="low_priority"),
            ]
            with input_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)
            output = root / "watchlist"
            first = run_wallet_watchlist(
                input_csv,
                output,
                generated_at="2026-06-26T00:00:00+00:00",
            )
            second = run_wallet_watchlist(
                input_csv,
                output,
                generated_at="2026-06-26T00:00:00+00:00",
            )
            self.assertTrue(first["validation"]["all_validation_passed"])
            self.assertTrue(first["validation"]["repeatable_export"])
            self.assertEqual(
                first["reproducibility_hashes"]["wallet_watchlist_csv_sha256"],
                second["reproducibility_hashes"]["wallet_watchlist_csv_sha256"],
            )
            self.assertTrue((output / "wallet_watchlist.csv").exists())
            self.assertTrue((output / "wallet_watchlist_summary.json").exists())
            self.assertTrue((output / "wallet_watchlist_report.md").exists())
            report = (output / "wallet_watchlist_report.md").read_text(encoding="utf-8")
            self.assertIn("monitoring/research artifact", report)
            self.assertIn("not a trading signal", report)
            self.assertIn("not a copy-trading recommendation", report)
            self.assertIn("based only on bounded public history", report)
            self.assertIn("strengths:", report)
            self.assertIn("risks:", report)
            self.assertIn("next research action:", report)
            self.assertIn("include in research watchlist", report)

    def test_wallet_watchlist_module_has_no_execution_or_forbidden_metric_methods(self):
        import polymarket.wallet_intelligence.wallet_watchlist as wallet_watchlist

        names = dir(wallet_watchlist)
        forbidden_fragments = (
            "private_key",
            "place_order",
            "copy_trade",
            "execute_trade",
            "wallet_connect",
            "compute_pnl",
            "compute_roi",
            "sharpe_ratio",
            "mark_to_market",
        )
        for fragment in forbidden_fragments:
            self.assertFalse(any(fragment in name.lower() for name in names))


class WalletCopyabilitySprintTests(unittest.TestCase):
    def test_copyability_research_classifies_wallets_with_reason_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scores_path = root / "wallet_scores.csv"
            watchlist_path = root / "wallet_watchlist.csv"
            metrics_path = root / "wallet_metrics.csv"
            score_rows = [
                {
                    "wallet_id": "0xaaa",
                    "profile_url": "https://polymarket.com/0xaaa",
                    "wallet_score": "74",
                    "score_band": "medium_priority",
                    "total_lifecycle_positions": "30",
                    "fast_crypto_lifecycle_share": "1",
                    "partial_exits": "10",
                    "percentage_still_open_positions": "0.5",
                    "oversold_bounded_history": "0",
                    "coverage_component": "20",
                    "fast_crypto_component": "25",
                    "lifecycle_activity_component": "15",
                    "event_density_component": "9",
                    "specialization_component": "7",
                    "bounded_history_penalty": "0",
                    "still_open_penalty": "0",
                    "small_sample_penalty": "0",
                    "concentration_penalty": "2",
                    "near_flat_ambiguity_penalty": "0",
                },
                {
                    "wallet_id": "0xbbb",
                    "profile_url": "https://polymarket.com/0xbbb",
                    "wallet_score": "40",
                    "score_band": "low_priority",
                    "total_lifecycle_positions": "8",
                    "fast_crypto_lifecycle_share": "0",
                    "partial_exits": "0",
                    "percentage_still_open_positions": "1",
                    "oversold_bounded_history": "1",
                    "coverage_component": "8",
                    "fast_crypto_component": "0",
                    "lifecycle_activity_component": "2",
                    "event_density_component": "0",
                    "specialization_component": "1",
                    "bounded_history_penalty": "5",
                    "still_open_penalty": "15",
                    "small_sample_penalty": "5",
                    "concentration_penalty": "0",
                    "near_flat_ambiguity_penalty": "0",
                },
                {
                    "wallet_id": "0xccc",
                    "profile_url": "https://polymarket.com/0xccc",
                    "wallet_score": "10",
                    "score_band": "insufficient_visible_structure",
                    "total_lifecycle_positions": "2",
                    "fast_crypto_lifecycle_share": "0",
                    "partial_exits": "0",
                    "percentage_still_open_positions": "1",
                    "oversold_bounded_history": "0",
                    "coverage_component": "2",
                    "fast_crypto_component": "0",
                    "lifecycle_activity_component": "0",
                    "event_density_component": "0",
                    "specialization_component": "0",
                    "bounded_history_penalty": "0",
                    "still_open_penalty": "15",
                    "small_sample_penalty": "10",
                    "concentration_penalty": "0",
                    "near_flat_ambiguity_penalty": "0",
                },
            ]
            watchlist_rows = [
                {
                    "wallet_id": "0xaaa",
                    "reason_codes": "enough_visible_structure; fast_crypto_relevant",
                    "structural_strengths": "visible fast-crypto lifecycle coverage",
                    "structural_risks": "bounded public history only",
                },
                {
                    "wallet_id": "0xbbb",
                    "reason_codes": "minimum_visible_structure",
                    "structural_strengths": "some lifecycle coverage",
                    "structural_risks": "mostly open visible state",
                },
            ]
            for path, rows in ((scores_path, score_rows), (metrics_path, score_rows)):
                with path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                    writer.writeheader()
                    writer.writerows(rows)
            with watchlist_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(watchlist_rows[0].keys()))
                writer.writeheader()
                writer.writerows(watchlist_rows)

            rows, summary = build_copyability_research(
                scores_path=scores_path,
                watchlist_path=watchlist_path,
                metrics_path=metrics_path,
                ingestion_summary={"primary_rows_normalized": 40, "cross_check_rows_fetched": 10, "rows_by_wallet": {"0xaaa": 30}},
                discovery_summary={"wallets_selected": 3},
                generated_at="2026-06-26T00:00:00+00:00",
            )

            self.assertTrue(summary["validation"]["all_validation_passed"])
            self.assertEqual([row["recommendation"] for row in rows], ["monitor_candidate", "needs_more_history", "exclude_for_now"])
            self.assertEqual(summary["analysis"]["A_monitor_candidate_count"], 1)
            self.assertEqual(summary["analysis"]["B_exclude_for_now_count"], 1)
            self.assertTrue(validate_copyability_research(rows)["no_forbidden_claims"])
            self.assertIn("realized outcome joins", rows[0]["missing_evidence"])


class FakeMarketMetadataClient:
    def get_market_by_slug(self, slug):
        if slug == "resolved-up":
            return {
                "id": "m1",
                "conditionId": "0xaaa",
                "slug": slug,
                "endDate": "2026-06-25T19:00:00Z",
                "closed": True,
                "outcomes": '["Up", "Down"]',
                "outcomePrices": '["1", "0"]',
                "umaResolutionStatus": "resolved",
                "automaticallyResolved": True,
                "closedTime": "2026-06-25 19:00:20+00",
            }
        if slug == "unresolved":
            return {
                "id": "m2",
                "conditionId": "0xbbb",
                "slug": slug,
                "endDate": "2026-06-26T19:00:00Z",
                "closed": False,
                "outcomes": '["Up", "Down"]',
                "outcomePrices": '["0.5", "0.5"]',
            }
        if slug == "conflict":
            return {
                "id": "m3",
                "conditionId": "0xnotccc",
                "slug": slug,
                "closed": True,
                "outcomes": '["Yes", "No"]',
                "outcomePrices": '["1", "0"]',
                "umaResolutionStatus": "resolved",
            }
        return None

    def get_event_by_slug(self, slug):
        return {"id": f"event-{slug}", "slug": slug, "markets": []}

    def get_events_query_by_slug(self, slug):
        return None

    def get_market_by_token(self, token_id):
        return None

    def get_clob_market(self, condition_id):
        tokens = {
            "0xaaa": [{"t": "token-up", "o": "Up"}, {"t": "token-down", "o": "Down"}],
            "0xbbb": [{"t": "token-up-b", "o": "Up"}],
            "0xccc": [{"t": "token-yes", "o": "Yes"}],
        }
        return {"t": tokens.get(condition_id, [])}


class WalletMarketOutcomeResolutionTests(unittest.TestCase):
    def _lifecycle(self, **overrides):
        row = {
            "wallet_id": "0xwallet",
            "profile_url": "https://polymarket.com/0xwallet",
            "condition_id": "0xaaa",
            "token_id": "token-up",
            "outcome": "Up",
            "lifecycle_group_key": "0xwallet|0xaaa|token-up|Up",
            "market_slug": "resolved-up",
            "event_slug": "resolved-up",
            "market_title": "Bitcoin Up or Down",
            "market_type": "fast_crypto_up_down",
            "asset_class": "BTC",
            "up_down_market": "true",
            "first_activity_timestamp": "1",
            "first_activity_datetime_utc": "2026-06-25T18:45:00+00:00",
            "last_activity_timestamp": "2",
            "last_activity_datetime_utc": "2026-06-25T18:46:00+00:00",
            "status": "still_open",
        }
        row.update(overrides)
        return row

    def test_market_outcome_join_classifies_resolved_and_unresolved_rows(self):
        rows = [
            self._lifecycle(),
            self._lifecycle(
                condition_id="0xaaa",
                token_id="token-down",
                outcome="Down",
                lifecycle_group_key="0xwallet|0xaaa|token-down|Down",
            ),
            self._lifecycle(
                condition_id="0xbbb",
                token_id="token-up-b",
                outcome="Up",
                lifecycle_group_key="0xwallet|0xbbb|token-up-b|Up",
                market_slug="unresolved",
                event_slug="unresolved",
            ),
        ]
        metadata = fetch_market_metadata(rows, FakeMarketMetadataClient())
        joined = join_lifecycle_outcomes(rows, metadata)
        status_by_key = {(row.condition_id, row.outcome): row.lifecycle_resolution_status for row in joined}
        self.assertEqual(status_by_key[("0xaaa", "Up")], "matched_outcome")
        self.assertEqual(status_by_key[("0xaaa", "Down")], "unmatched_outcome")
        self.assertIn("unresolved_market", [row.lifecycle_resolution_status for row in joined])
        self.assertEqual([row for row in joined if row.condition_id == "0xaaa" and row.outcome == "Up"][0].join_confidence, "high")
        validation = validate_market_outcome_joins(joined)
        self.assertTrue(validation["deterministic_ordering"])
        self.assertTrue(validation["all_rows_have_confidence_labels"])
        self.assertTrue(validation["unresolved_handling_present"])
        self.assertTrue(validation["no_forbidden_metric_fields"])

    def test_market_outcome_join_flags_conflicting_metadata(self):
        rows = [
            self._lifecycle(
                condition_id="0xccc",
                token_id="token-yes",
                outcome="Yes",
                lifecycle_group_key="0xwallet|0xccc|token-yes|Yes",
                market_slug="conflict",
                event_slug="conflict",
            )
        ]
        metadata = fetch_market_metadata(rows, FakeMarketMetadataClient())
        joined = join_lifecycle_outcomes(rows, metadata)
        self.assertEqual(joined[0].join_status, "conflicting_metadata")
        self.assertEqual(joined[0].lifecycle_resolution_status, "insufficient_evidence")

    def test_market_outcome_sprint_writes_repeatable_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_csv = root / "lifecycle_positions.csv"
            rows = [self._lifecycle()]
            with input_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            output_dir = root / "outcome"
            first = run_market_outcome_resolution_sprint(
                input_csv,
                output_dir,
                client=FakeMarketMetadataClient(),
                generated_at="2026-06-26T00:00:00+00:00",
            )
            second = run_market_outcome_resolution_sprint(
                input_csv,
                output_dir,
                client=FakeMarketMetadataClient(),
                generated_at="2026-06-26T00:00:00+00:00",
            )
            self.assertEqual(first["lifecycle_positions_evaluated"], 1)
            self.assertTrue(first["validation"]["repeatable_export"])
            self.assertEqual(
                first["reproducibility_hashes"]["market_outcome_join_csv_sha256"],
                second["reproducibility_hashes"]["market_outcome_join_csv_sha256"],
            )
            self.assertTrue((output_dir / "market_outcome_join.csv").exists())
            self.assertTrue((output_dir / "market_outcome_join_summary.json").exists())
            self.assertTrue((output_dir / "market_outcome_join_report.md").exists())
            report = (output_dir / "market_outcome_join_report.md").read_text(encoding="utf-8")
            self.assertIn("not a trading signal", report)
            self.assertIn("not a copy-trading recommendation", report)


class WalletOutcomeSkillBaselineTests(unittest.TestCase):
    def _outcome_rows(self, wallet_id, matched, unmatched, *, asset="BTC"):
        rows = []
        for index in range(matched + unmatched):
            status = "matched_outcome" if index < matched else "unmatched_outcome"
            outcome = "Up" if status == "matched_outcome" else "Down"
            rows.append(
                {
                    "wallet_id": wallet_id,
                    "profile_url": f"https://polymarket.com/{wallet_id}",
                    "condition_id": f"0x{wallet_id[-3:]}{index}",
                    "token_id": f"token-{wallet_id}-{index}",
                    "outcome": outcome,
                    "lifecycle_group_key": f"{wallet_id}|{index}|{outcome}",
                    "market_slug": f"btc-updown-{index}",
                    "event_slug": f"btc-updown-{index}",
                    "market_title": "Bitcoin Up or Down",
                    "market_type": "fast_crypto_up_down",
                    "asset_class": asset,
                    "up_down_market": "true",
                    "first_activity_timestamp": str(index),
                    "first_activity_datetime_utc": "2026-06-25T18:45:00+00:00",
                    "last_activity_timestamp": str(index + 1),
                    "last_activity_datetime_utc": "2026-06-25T18:46:00+00:00",
                    "lifecycle_status": "still_open",
                    "market_id": str(index),
                    "event_id": "",
                    "expiry_timestamp": "2026-06-25T19:00:00Z",
                    "resolution_timestamp": "2026-06-25 19:00:20+00",
                    "resolved_status": "resolved",
                    "winning_outcome": "Up",
                    "outcome_prices": '{"Down": 0.0, "Up": 1.0}',
                    "lifecycle_resolution_status": status,
                    "join_confidence": "high",
                    "join_status": "joined",
                    "join_reason": "resolved_terminal_outcome",
                    "metadata_sources": "gamma_markets_slug",
                    "condition_id_match": "true",
                    "token_outcome_cross_check": "unavailable",
                    "conflicting_metadata": "false",
                }
            )
        return rows

    def test_outcome_skill_classifies_above_below_and_insufficient_wallets(self):
        outcome_rows = (
            self._outcome_rows("0xabove", 35, 5)
            + self._outcome_rows("0xbelow", 5, 35)
            + self._outcome_rows("0xsmall", 4, 4)
        )
        score_rows = [{"wallet_id": "0xabove", "wallet_score": "80", "score_band": "high_priority"}]
        watchlist_rows = [{"wallet_id": "0xabove", "priority_bucket": "high_priority", "reason_codes": "fixture"}]

        rows, summary = build_wallet_outcome_skill_baseline(
            outcome_rows,
            score_rows=score_rows,
            watchlist_rows=watchlist_rows,
            generated_at="2026-06-26T00:00:00+00:00",
        )

        by_wallet = {row["wallet_id"]: row for row in rows}
        self.assertEqual(by_wallet["0xabove"]["evidence_classification"], "above_baseline_evidence")
        self.assertEqual(by_wallet["0xbelow"]["evidence_classification"], "below_baseline_evidence")
        self.assertEqual(by_wallet["0xsmall"]["evidence_classification"], "insufficient_evidence")
        self.assertEqual(summary["final_conclusion"], "INCONCLUSIVE")
        self.assertTrue(summary["validation"]["all_tested_rows_are_resolved_binary_fast_crypto"])
        self.assertTrue(validate_wallet_outcome_skill(rows, outcome_rows, outcome_rows)["no_forbidden_metric_fields"])

    def test_outcome_skill_sprint_writes_repeatable_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_csv = root / "market_outcome_join.csv"
            score_csv = root / "wallet_scores.csv"
            watchlist_csv = root / "wallet_watchlist.csv"
            output_dir = root / "skill"
            outcome_rows = (
                self._outcome_rows("0xabove", 35, 5)
                + self._outcome_rows("0xbelow", 5, 35)
                + self._outcome_rows("0xsmall", 4, 4)
            )
            with input_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(outcome_rows[0].keys()))
                writer.writeheader()
                writer.writerows(outcome_rows)
            with score_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["wallet_id", "wallet_score", "score_band"])
                writer.writeheader()
                writer.writerow({"wallet_id": "0xabove", "wallet_score": "80", "score_band": "high_priority"})
            with watchlist_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["wallet_id", "priority_bucket", "reason_codes"])
                writer.writeheader()
                writer.writerow({"wallet_id": "0xabove", "priority_bucket": "high_priority", "reason_codes": "fixture"})

            first = run_wallet_outcome_skill_baseline(
                input_csv,
                output_dir,
                score_csv=score_csv,
                watchlist_csv=watchlist_csv,
                generated_at="2026-06-26T00:00:00+00:00",
            )
            second = run_wallet_outcome_skill_baseline(
                input_csv,
                output_dir,
                score_csv=score_csv,
                watchlist_csv=watchlist_csv,
                generated_at="2026-06-26T00:00:00+00:00",
            )

            self.assertEqual(first["wallet_count"], 3)
            self.assertTrue(first["validation"]["repeatable_export"])
            self.assertEqual(
                first["reproducibility_hashes"]["wallet_skill_baseline_csv_sha256"],
                second["reproducibility_hashes"]["wallet_skill_baseline_csv_sha256"],
            )
            self.assertTrue((output_dir / "wallet_skill_baseline.csv").exists())
            self.assertTrue((output_dir / "wallet_skill_summary.json").exists())
            self.assertTrue((output_dir / "wallet_skill_report.md").exists())


class WalletActivityVisibilityDelayTests(unittest.TestCase):
    def _skill(self, wallet_id, classification):
        return {
            "wallet_id": wallet_id,
            "profile_url": f"https://polymarket.com/{wallet_id}",
            "evidence_classification": classification,
        }

    def _trade(self, wallet_id, timestamp, *, publication_timestamp=""):
        return {
            "wallet_id": wallet_id,
            "profile_url": f"https://polymarket.com/{wallet_id}",
            "source_endpoint": "https://data-api.polymarket.com/activity",
            "source_endpoint_name": "activity_primary",
            "activity_type": "TRADE",
            "activity_timestamp": str(timestamp),
            "activity_datetime_utc": "",
            "publication_timestamp": publication_timestamp,
            "transaction_hash": f"0xtx-{wallet_id}-{timestamp}",
            "condition_id": f"0xcondition-{timestamp}",
            "token_id": f"token-{timestamp}",
            "asset_id": f"token-{timestamp}",
            "market_slug": f"btc-updown-{timestamp}",
            "event_slug": f"btc-updown-{timestamp}",
            "outcome": "Up",
            "side": "BUY",
            "price": "0.5",
            "size": "10",
            "market_type": "fast_crypto_up_down",
            "asset_class": "BTC",
            "up_down_market": "true",
            "source_fetch_timestamp": "2026-06-25T19:00:00+00:00",
            "dedupe_key": f"dedupe-{wallet_id}-{timestamp}",
        }

    def _fixtures(self):
        skills = [
            self._skill("0xabove", "above_baseline_evidence"),
            self._skill("0xbase", "sample_size_consistent_with_baseline"),
            self._skill("0xbelow", "below_baseline_evidence"),
            self._skill("0xsmall", "insufficient_evidence"),
        ]
        trades = [
            self._trade("0xabove", 1782413100),
            self._trade("0xbase", 1782413200, publication_timestamp="1782413205"),
            self._trade("0xbelow", 1782413300),
            self._trade("0xsmall", 1782413400),
        ]
        return skills, trades

    def test_visibility_delay_keeps_publication_and_fetch_time_distinct(self):
        skills, trades = self._fixtures()
        rows, summary = build_wallet_visibility_delay(skills, trades)
        by_wallet = {row["wallet_id"]: row for row in rows}
        self.assertEqual(len(rows), 3)
        self.assertEqual(by_wallet["0xabove"]["delay_measurement_status"], "unknown_missing_publication_timestamp")
        self.assertEqual(by_wallet["0xabove"]["measurable_publication_delay_seconds"], "")
        self.assertTrue(by_wallet["0xabove"]["retrospective_retrieval_lag_seconds"])
        self.assertEqual(by_wallet["0xbase"]["measurable_publication_delay_seconds"], "5.000000")
        self.assertEqual(summary["measured_publication_delay_seconds"]["count"], 1)
        self.assertEqual(summary["timestamp_completeness"]["unknown_timing_count"], 2)
        self.assertEqual(summary["final_conclusion"], "INCONCLUSIVE")

    def test_visibility_delay_validation_confirms_groups_and_ordering(self):
        skills, trades = self._fixtures()
        rows, _ = build_wallet_visibility_delay(skills, list(reversed(trades)))
        metadata = {
            row["wallet_id"]: {
                "wallet_group": row["wallet_group"],
                "wallet_group_label": row["wallet_group_label"],
            }
            for row in rows
        }
        validation = validate_wallet_visibility_delay(rows, metadata)
        self.assertTrue(validation["deterministic_ordering"])
        self.assertTrue(validation["event_sequences_consecutive"])
        self.assertTrue(validation["no_publication_fetch_substitution"])
        self.assertTrue(validation["evidence_groups_present"])

    def test_visibility_delay_sprint_writes_repeatable_outputs(self):
        skills, trades = self._fixtures()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_csv = root / "skill.csv"
            trade_csv = root / "trades.csv"
            output_dir = root / "visibility"
            with skill_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(skills[0].keys()))
                writer.writeheader()
                writer.writerows(skills)
            with trade_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
                writer.writeheader()
                writer.writerows(trades)
            first = run_wallet_visibility_delay_sprint(skill_csv, trade_csv, output_dir)
            hashes = dict(first["reproducibility_hashes"])
            first_exports = {
                path.name: path.read_bytes() for path in output_dir.iterdir() if path.is_file()
            }
            second = run_wallet_visibility_delay_sprint(skill_csv, trade_csv, output_dir)
            self.assertEqual(hashes, second["reproducibility_hashes"])
            self.assertEqual(
                first_exports,
                {path.name: path.read_bytes() for path in output_dir.iterdir() if path.is_file()},
            )
            self.assertTrue(second["validation"]["repeatable_export"])
            self.assertTrue((output_dir / "wallet_visibility_delay.csv").exists())
            self.assertTrue((output_dir / "wallet_visibility_delay_summary.json").exists())
            self.assertTrue((output_dir / "wallet_visibility_delay_report.md").exists())


class WalletFirstSeenDetectionTests(unittest.TestCase):
    def _trade(self, timestamp, transaction_hash):
        return {
            "timestamp": timestamp,
            "transactionHash": transaction_hash,
            "conditionId": "0xcondition",
            "asset": "token-up",
            "slug": "btc-updown-5m-fixture",
            "eventSlug": "btc-updown-5m-fixture",
            "title": "Bitcoin Up or Down",
            "outcome": "Up",
            "side": "BUY",
            "price": 0.55,
            "size": 10,
        }

    def _snapshot(self, cycle, wallet, received, rows, *, status=200):
        return {
            "poll_cycle": cycle,
            "poll_started_at_utc": received,
            "wallet_id": wallet,
            "request_started_at_utc": received,
            "response_received_at_utc": received,
            "status_code": status,
            "source_endpoint": "https://data-api.polymarket.com/activity?type=TRADE",
            "rows": rows,
            "error": "" if status == 200 else "fixture failure",
        }

    def _snapshots(self):
        wallet = STRONGEST_H1_WALLETS[0]
        baseline = self._trade(1782413100, "0xbaseline")
        new_trade = self._trade(1782413104, "0xnew")
        return [
            self._snapshot(1, wallet, "2026-06-25T18:45:01+00:00", [baseline]),
            self._snapshot(2, wallet, "2026-06-25T18:45:06+00:00", [new_trade, baseline]),
            self._snapshot(3, wallet, "2026-06-25T18:45:11+00:00", [new_trade, baseline]),
        ]

    def test_first_seen_excludes_baseline_and_measures_new_trade(self):
        rows, summary = analyze_first_seen_snapshots(
            self._snapshots(),
            wallets=STRONGEST_H1_WALLETS,
            experiment_started_at="2026-06-25T18:45:00+00:00",
            experiment_completed_at="2026-06-25T18:45:15+00:00",
            configured_duration_seconds=15,
            poll_interval_seconds=5,
            page_limit=100,
            max_requests=12,
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["transaction_hash"], "0xnew")
        self.assertEqual(rows[0]["first_seen_delay_seconds"], "2.000000")
        self.assertEqual(rows[0]["delay_measurement_status"], "measured_upper_bound")
        self.assertEqual(summary["baseline_unique_trades"], 1)
        self.assertEqual(summary["duplicate_observations"], 3)
        self.assertTrue(summary["can_h2_now_be_tested"])
        self.assertEqual(summary["research_conclusion"], "H2_MEASURABLE_PROSPECTIVELY")

    def test_first_seen_reports_failed_requests_and_missing_wallet_baselines(self):
        snapshots = self._snapshots() + [
            self._snapshot(
                1,
                STRONGEST_H1_WALLETS[1],
                "2026-06-25T18:45:02+00:00",
                [],
                status=503,
            )
        ]
        _, summary = analyze_first_seen_snapshots(
            snapshots,
            wallets=STRONGEST_H1_WALLETS,
            experiment_started_at="2026-06-25T18:45:00+00:00",
            experiment_completed_at="2026-06-25T18:45:15+00:00",
            configured_duration_seconds=15,
            poll_interval_seconds=5,
            page_limit=100,
            max_requests=12,
        )
        self.assertEqual(summary["requests_failed"], 1)
        self.assertFalse(summary["api_consistency"]["all_wallet_baselines_established"])
        self.assertEqual(len(summary["api_consistency"]["request_failures"]), 1)

    def test_first_seen_snapshot_export_is_repeatable(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "first-seen"
            kwargs = {
                "output_dir": output,
                "wallets": STRONGEST_H1_WALLETS,
                "experiment_started_at": "2026-06-25T18:45:00+00:00",
                "experiment_completed_at": "2026-06-25T18:45:15+00:00",
                "configured_duration_seconds": 15,
                "poll_interval_seconds": 5,
                "page_limit": 100,
                "max_requests": 12,
            }
            first = run_first_seen_from_snapshots(self._snapshots(), **kwargs)
            first_exports = {path.name: path.read_bytes() for path in output.iterdir()}
            second = run_first_seen_from_snapshots(list(reversed(self._snapshots())), **kwargs)
            second_exports = {path.name: path.read_bytes() for path in output.iterdir()}
            self.assertEqual(first_exports, second_exports)
            self.assertTrue(second["validation"]["deterministic_csv_render"])
            self.assertTrue(second["validation"]["deterministic_report_render"])
            self.assertTrue(second["validation"]["public_read_only_endpoint_only"])
            self.assertEqual(first["reproducibility_hashes"], second["reproducibility_hashes"])


class WalletFirstSeenProspectiveTests(unittest.TestCase):
    def test_restart_and_duplicate_fixture_passes(self):
        validation = validate_restart_and_duplicates()
        self.assertTrue(all(validation.values()))

    def test_active_run_resumes_without_resetting_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "observer.sqlite3"
            with ProspectiveFirstSeenStore(path) as store:
                first = store.start_or_resume_run(
                    started_at_utc="2026-06-28T12:00:00.000+00:00",
                    duration_seconds=300,
                    poll_interval_seconds=5,
                    page_limit=100,
                    max_requests=240,
                )
            with ProspectiveFirstSeenStore(path) as store:
                resumed = store.start_or_resume_run(
                    started_at_utc="2026-06-28T12:02:00.000+00:00",
                    duration_seconds=60,
                    poll_interval_seconds=10,
                    page_limit=10,
                    max_requests=10,
                )
                self.assertEqual(first["run_id"], resumed["run_id"])
                self.assertEqual(resumed["deadline_at_utc"], "2026-06-28T12:05:00.000+00:00")
                self.assertEqual(resumed["max_requests"], 240)

    def test_expired_run_closes_and_starts_new_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "observer.sqlite3"
            with ProspectiveFirstSeenStore(path) as store:
                first = store.start_or_resume_run(
                    started_at_utc="2026-06-28T12:00:00.000+00:00",
                    duration_seconds=300,
                    poll_interval_seconds=5,
                    page_limit=100,
                    max_requests=240,
                )
                second = store.start_or_resume_run(
                    started_at_utc="2026-06-28T13:00:00.000+00:00",
                    duration_seconds=60,
                    poll_interval_seconds=10,
                    page_limit=10,
                    max_requests=10,
                )
                self.assertNotEqual(first["run_id"], second["run_id"])
                self.assertEqual(second["deadline_at_utc"], "2026-06-28T13:01:00.000+00:00")
                first_status = store.connection.execute(
                    "SELECT status FROM runs WHERE run_id=?", (first["run_id"],)
                ).fetchone()[0]
                self.assertEqual(first_status, "complete")

    def test_prepare_writes_empty_deterministic_research_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "data" / "observer.sqlite3"
            output = root / "models"
            first = prepare_prospective_experiment(db_path=db, output_dir=output)
            first_files = {path.name: path.read_bytes() for path in output.iterdir()}
            second = prepare_prospective_experiment(db_path=db, output_dir=output)
            second_files = {path.name: path.read_bytes() for path in output.iterdir()}
            self.assertEqual(first_files, second_files)
            self.assertFalse(first["h2_evaluated"])
            self.assertTrue(second["all_validation_passed"])
            self.assertEqual(render_dataset([]), (output / "wallet_first_seen_dataset.csv").read_text(encoding="utf-8"))
            self.assertTrue((output / "wallet_first_seen_validation.json").exists())
            self.assertTrue((output / "wallet_first_seen_design_report.md").exists())


class WalletDecisionWindowTests(unittest.TestCase):
    @staticmethod
    def _rows():
        return [
            {
                "wallet_id": "0xwallet",
                "observation_class": "new_live_window_trade",
                "first_observation_timestamp_utc": "2026-06-28T14:03:34.894+00:00",
                "trade_datetime_utc": "2026-06-28T14:03:19.000+00:00",
                "trade_timestamp": "1782655399",
                "first_seen_delay_seconds": "15.894000",
                "poll_interval_seconds": "5.000000",
                "market_slug": "sol-updown-5m-1782655200",
                "condition_id": "0x5c5809ee85b49a9b63716f7cf6f47d42df09a0df1ccbc350dfda9209fea277f4",
                "token_id": "token-sol",
                "transaction_hash": "0xtx-sol",
                "trade_identity": "trade-sol",
                "asset_class": "SOL",
                "five_minute_market": "true",
            },
            {
                "wallet_id": "0xwallet",
                "observation_class": "new_live_window_trade",
                "first_observation_timestamp_utc": "2026-06-28T14:04:15.041+00:00",
                "trade_datetime_utc": "2026-06-28T14:03:59.000+00:00",
                "trade_timestamp": "1782655439",
                "first_seen_delay_seconds": "16.041000",
                "poll_interval_seconds": "5.000000",
                "market_slug": "btc-updown-5m-1782655200",
                "condition_id": "0x2fece38d8afd7a75c250cb52406e22841c40fad48190ba431f212bdecdab7067",
                "token_id": "token-btc",
                "transaction_hash": "0xtx-btc",
                "trade_identity": "trade-btc",
                "asset_class": "BTC",
                "five_minute_market": "true",
            },
            {
                "wallet_id": "0xwallet",
                "observation_class": "historical_page_churn",
                "first_observation_timestamp_utc": "2026-06-28T14:04:00.000+00:00",
                "market_slug": "btc-updown-5m-1782655200",
                "five_minute_market": "true",
            },
        ]

    def test_classifies_frozen_decision_window_thresholds(self):
        self.assertEqual(classify_decision_window(60), "sufficient_decision_window")
        self.assertEqual(classify_decision_window(30), "marginal_decision_window")
        self.assertEqual(classify_decision_window(29.999), "insufficient_decision_window")

    def test_builds_only_prospective_five_minute_windows(self):
        rows, exclusions = build_decision_windows(self._rows())
        self.assertEqual([row["decision_window_seconds"] for row in rows], ["85.106000", "44.959000"])
        self.assertEqual(
            [row["decision_window_classification"] for row in rows],
            ["sufficient_decision_window", "marginal_decision_window"],
        )
        self.assertEqual(exclusions["non_prospective_or_page_churn"], 1)
        self.assertTrue(all(row["expiry_join_confidence"] == "high" for row in rows))

    def test_sprint_outputs_are_repeatable_and_inconclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_csv = root / "first_seen.csv"
            fields = sorted({key for row in self._rows() for key in row})
            with input_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(self._rows())
            output = root / "output"
            first = run_wallet_decision_window_sprint(input_csv, output)
            first_files = {path.name: path.read_bytes() for path in output.iterdir()}
            second = run_wallet_decision_window_sprint(input_csv, output)
            second_files = {path.name: path.read_bytes() for path in output.iterdir()}
            self.assertEqual(first_files, second_files)
            self.assertEqual(first["research_conclusion"], "INCONCLUSIVE")
            self.assertEqual(first["classification_counts"]["sufficient_decision_window"], 1)
            self.assertTrue(second["validation"]["all_validation_passed"])
            self.assertEqual(
                second["reproducibility_hashes"]["wallet_decision_window_report_md_sha256"],
                hashlib.sha256((output / "wallet_decision_window_report.md").read_bytes()).hexdigest(),
            )


class WalletAutonomousEvidenceAccumulatorTests(unittest.TestCase):
    def test_session_numbering_is_persistent_and_restart_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "accumulator.sqlite3"
            with EvidenceAccumulatorStore(path) as store:
                first = store.reserve_session("2026-06-28T15:00:00.000+00:00")
            with EvidenceAccumulatorStore(path) as store:
                resumed = store.reserve_session("2026-06-28T15:01:00.000+00:00")
                self.assertEqual(first["session_number"], 2)
                self.assertEqual(resumed["session_number"], 2)
                store.complete_session(
                    2,
                    completed_at_utc="2026-06-28T15:05:00.000+00:00",
                    observer_run_id="run-2",
                    eligible_trades=2,
                    action="CONTINUE",
                )
                third = store.reserve_session("2026-06-28T15:10:00.000+00:00")
                self.assertEqual(third["session_number"], 3)

    @staticmethod
    def _gate_rows(h2_successes, h3_successes):
        rows = []
        wallets = ["0xa", "0xb", "0xc"]
        assets = ["BTC", "ETH"]
        for index in range(100):
            rows.append(
                {
                    "trade_identity": f"trade-{index:03d}",
                    "wallet_id": wallets[index % 3],
                    "asset_class": assets[index % 2],
                    "market_slug": f"btc-updown-5m-{index}",
                    "first_seen": f"2026-06-{20 + index % 5:02d}T12:00:00.000+00:00",
                    "delay_seconds": 20.0 if index < h2_successes else 40.0,
                    "window_seconds": 80.0 if index < h3_successes else 20.0,
                    "gamma_verified_expiry": True,
                }
            )
        return rows

    def test_support_reject_and_budget_stop_are_frozen(self):
        requests = {"successful": 1000, "failed": 0}
        supported = evaluate_h2_h3_gates(self._gate_rows(80, 70), session_count=10, request_counts=requests)
        self.assertEqual(supported["h2"]["conclusion"], "SUPPORTED")
        self.assertEqual(supported["h3"]["conclusion"], "SUPPORTED")
        self.assertEqual(supported["action"], "GRADUATE_TO_ENGINEERING")

        rejected = evaluate_h2_h3_gates(self._gate_rows(50, 70), session_count=10, request_counts=requests)
        self.assertEqual(rejected["h2"]["conclusion"], "REJECTED")
        self.assertEqual(rejected["action"], "FREEZE")

        underpowered = evaluate_h2_h3_gates(self._gate_rows(79, 69)[:20], session_count=60, request_counts=requests)
        self.assertEqual(underpowered["stop_reason"], "SESSION_BUDGET_EXHAUSTED")
        self.assertEqual(underpowered["action"], "FREEZE")

    def test_current_progress_is_repeatable_and_does_not_poll(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            accumulator_db = root / "accumulator.sqlite3"
            observer_db = root / "observer.sqlite3"
            output = root / "output"
            first = prepare_accumulator_progress(
                accumulator_db=accumulator_db,
                observer_db=observer_db,
                output_dir=output,
            )
            first_files = {path.name: path.read_bytes() for path in output.iterdir()}
            second = prepare_accumulator_progress(
                accumulator_db=accumulator_db,
                observer_db=observer_db,
                output_dir=output,
            )
            second_files = {path.name: path.read_bytes() for path in output.iterdir()}
            self.assertEqual(first_files, second_files)
            self.assertEqual(
                set(first_files),
                {"wallet_progress.json", "wallet_progress_report.md", "wallet_gate_status.json"},
            )
            self.assertEqual(first["evidence"]["eligible_trades"], 2)
            self.assertEqual(first["sessions"]["completed"], 1)
            self.assertEqual(first["sessions"]["remaining"], 59)
            self.assertEqual(second["action"], "CONTINUE")

    def test_autonomous_loop_stops_at_session_sixty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            accumulator_db = root / "accumulator.sqlite3"
            observer_db = root / "observer.sqlite3"
            output = root / "output"
            with EvidenceAccumulatorStore(accumulator_db) as store:
                with store.connection:
                    store.connection.executemany(
                        """INSERT INTO accumulator_sessions
                        (session_number, status, started_at_utc, completed_at_utc)
                        VALUES (?, 'complete', ?, ?)""",
                        [
                            (
                                number,
                                f"2026-06-28T{number % 24:02d}:00:00.000+00:00",
                                f"2026-06-28T{number % 24:02d}:05:00.000+00:00",
                            )
                            for number in range(2, 60)
                        ],
                    )
            calls = []

            def runner(**kwargs):
                calls.append(kwargs)
                return {}

            result = run_autonomous_accumulator(
                activity_client=object(),
                metadata_client=object(),
                accumulator_db=accumulator_db,
                observer_db=observer_db,
                output_dir=output,
                session_runner=runner,
                now=lambda: datetime.fromisoformat("2026-06-29T12:00:00+00:00"),
            )
            self.assertEqual(len(calls), 1)
            self.assertEqual(result["sessions"]["completed"], 60)
            self.assertEqual(result["action"], "FREEZE")
            self.assertEqual(result["stop_reason"], "SESSION_BUDGET_EXHAUSTED")
            self.assertEqual(result["automation_status"], "stopped")

    def test_background_command_runs_frozen_accumulator(self):
        command = background_command(Path("a.sqlite3"), Path("o.sqlite3"), Path("output"))
        self.assertIn("wallet-evidence-accumulator", command)
        self.assertIn("run", command)
        self.assertNotIn("--poll-interval", command)


if __name__ == "__main__":
    unittest.main()
