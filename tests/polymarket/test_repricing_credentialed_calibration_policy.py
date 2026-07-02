from __future__ import annotations

import unittest

from polymarket.repricing_research.credentialed_calibration_policy import (
    FORBIDDEN_ENV_NAMES,
    REQUIRED_ENV_NAMES,
    CalibrationPolicyError,
    NoOrderCalibrationPolicy,
    audit_record,
)


class CredentialedCalibrationPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = NoOrderCalibrationPolicy()

    def test_exact_read_only_allowlist(self) -> None:
        allowed = (
            ("GET", "https://clob.polymarket.com/data/orders?market=x"),
            ("GET", "https://clob.polymarket.com/trades?after=1"),
            ("GET", "https://clob.polymarket.com/time"),
            ("CONNECT", "wss://ws-subscriptions-clob.polymarket.com/ws/user"),
        )
        for method, url in allowed:
            self.assertTrue(self.policy.authorize(method, url).allowed)

    def test_all_order_and_cancel_routes_are_denied(self) -> None:
        forbidden = (
            ("POST", "https://clob.polymarket.com/order"),
            ("POST", "https://clob.polymarket.com/orders"),
            ("DELETE", "https://clob.polymarket.com/order/abc"),
            ("DELETE", "https://clob.polymarket.com/cancel-all"),
            ("DELETE", "https://clob.polymarket.com/cancel-market-orders"),
            ("POST", "https://clob.polymarket.com/heartbeats"),
            ("POST", "https://clob.polymarket.com/auth/api-key"),
            ("GET", "https://clob.polymarket.com/auth/derive-api-key"),
        )
        for method, url in forbidden:
            self.assertFalse(self.policy.authorize(method, url).allowed)

    def test_method_host_path_and_scheme_must_match_exactly(self) -> None:
        for method, url in (
            ("POST", "https://clob.polymarket.com/trades"),
            ("GET", "http://clob.polymarket.com/trades"),
            ("GET", "https://evil.example/trades"),
            ("GET", "https://clob.polymarket.com/trades/extra"),
        ):
            with self.assertRaisesRegex(CalibrationPolicyError, "blocked"):
                self.policy.require(method, url)

    def test_environment_names_require_authorization_and_kill_switch(self) -> None:
        self.policy.validate_environment_names(set(REQUIRED_ENV_NAMES))
        with self.assertRaisesRegex(CalibrationPolicyError, "missing"):
            self.policy.validate_environment_names(set())
        with self.assertRaisesRegex(CalibrationPolicyError, "forbidden"):
            self.policy.validate_environment_names(set(REQUIRED_ENV_NAMES) | {next(iter(FORBIDDEN_ENV_NAMES))})

    def test_audit_record_redacts_all_secret_fields(self) -> None:
        record = audit_record("GET", "https://clob.polymarket.com/trades", {
            "POLY_API_KEY": "key", "passphrase": "phrase", "nested": {"signature": "sig"}, "count": 2,
        })
        serialized = str(record)
        for secret in ("key", "phrase", "sig"):
            self.assertNotIn(f"'{secret}'", serialized)
        self.assertEqual(record["metadata"]["count"], 2)
        self.assertTrue(record["allowed"])

    def test_unknown_request_fails_closed(self) -> None:
        decision = self.policy.authorize("GET", "https://clob.polymarket.com/unknown")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "deny_by_default")


if __name__ == "__main__":
    unittest.main()
