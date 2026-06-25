import csv
import json
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
