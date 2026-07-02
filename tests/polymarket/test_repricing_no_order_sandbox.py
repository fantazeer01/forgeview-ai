from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from polymarket.repricing_research.no_order_sandbox import (
    FixtureEgressProxy,
    NoOrderCalibrationSandbox,
    SandboxFailClosed,
    SandboxWatchdog,
    replay_audit,
    run_fixture_validation,
)


class NoOrderSandboxTests(unittest.TestCase):
    def sandbox(self, root: Path, **kwargs) -> NoOrderCalibrationSandbox:
        sandbox = NoOrderCalibrationSandbox(root, **kwargs)
        sandbox.kill_switch.arm()
        return sandbox

    def test_allowed_routes_pass_only_through_proxy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = self.sandbox(Path(tmp))
            sandbox.preflight()
            self.assertEqual(sandbox.request("GET", "https://clob.polymarket.com/trades", via_proxy=True)["count"], 0)
            with self.assertRaisesRegex(SandboxFailClosed, "direct egress"):
                sandbox.request("GET", "https://clob.polymarket.com/trades", via_proxy=False)

    def test_order_cancel_heartbeat_and_unknown_routes_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = self.sandbox(Path(tmp))
            for method, url in (
                ("POST", "https://clob.polymarket.com/order"),
                ("POST", "https://clob.polymarket.com/orders"),
                ("DELETE", "https://clob.polymarket.com/cancel-all"),
                ("POST", "https://clob.polymarket.com/heartbeats"),
                ("GET", "https://clob.polymarket.com/unknown"),
            ):
                with self.assertRaisesRegex(SandboxFailClosed, "route denied"):
                    sandbox.request(method, url, via_proxy=True)

    def test_kill_switch_stops_calibration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = self.sandbox(Path(tmp))
            sandbox.kill_switch.trip("test")
            with self.assertRaisesRegex(SandboxFailClosed, "not armed"):
                sandbox.request("GET", "https://clob.polymarket.com/time", via_proxy=True)

    def test_parent_watchdog_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            watchdog = SandboxWatchdog(parent_alive=lambda: False)
            sandbox = self.sandbox(Path(tmp), watchdog=watchdog)
            with self.assertRaisesRegex(SandboxFailClosed, "parent"):
                sandbox.preflight()

    def test_watchdog_deadline_and_proxy_loss_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            watchdog = SandboxWatchdog(timeout_seconds=0.001)
            sandbox = self.sandbox(Path(tmp), watchdog=watchdog)
            time.sleep(0.02)
            with self.assertRaisesRegex(SandboxFailClosed, "deadline"):
                sandbox.preflight()
        with tempfile.TemporaryDirectory() as tmp:
            proxy = FixtureEgressProxy()
            sandbox = self.sandbox(Path(tmp), proxy=proxy)
            proxy.alive = False
            with self.assertRaisesRegex(SandboxFailClosed, "proxy"):
                sandbox.preflight()

    def test_zero_open_order_gate_is_enforced_without_cancel(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proxy = FixtureEgressProxy()
            proxy.open_orders = [{"id": "fixture-open-order"}]
            reasons: list[str] = []
            sandbox = self.sandbox(Path(tmp), proxy=proxy, operator_abort=reasons.append)
            with self.assertRaisesRegex(SandboxFailClosed, "zero-open-order"):
                sandbox.preflight()
            self.assertEqual(reasons, ["open_order_gate_failed"])
            self.assertEqual(proxy.open_orders, [{"id": "fixture-open-order"}])

    def test_fixture_secret_handles_never_appear_in_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = self.sandbox(Path(tmp))
            values = [handle.handle_id for handle in sandbox.environment.values()]
            sandbox.request("GET", "https://clob.polymarket.com/trades", via_proxy=True, metadata={
                "api_secret": values[0], "authorization": values[1], "count": 1,
            })
            text = sandbox.audit.path.read_text(encoding="utf-8")
            for value in values:
                self.assertNotIn(value, text)
            self.assertTrue(replay_audit(sandbox.audit.path)["valid"])

    def test_clean_child_environment_contains_handles_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = self.sandbox(Path(tmp))
            self.assertTrue(sandbox.environment)
            self.assertTrue(all(type(value).__name__ == "FixtureSecretHandle" for value in sandbox.environment.values()))
            self.assertFalse(any("PRIVATE_KEY" in name or "SEED" in name for name in sandbox.environment))

    def test_rollback_invokes_operator_and_disables_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            reasons: list[str] = []
            sandbox = self.sandbox(Path(tmp), operator_abort=reasons.append)
            status = sandbox.rollback("operator_test")
            self.assertEqual(status["status"], "ROLLED_BACK")
            self.assertFalse(status["restart_allowed"])
            self.assertEqual(reasons, ["operator_test"])

    def test_validation_uses_no_network_or_orders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_fixture_validation(Path(tmp))
            self.assertEqual(result["network_scope"], "no_network_fixture_proxy")
            self.assertEqual(result["authenticated_calls"], 0)
            self.assertEqual(result["orders_submitted"], 0)
            self.assertEqual(result["cancellations_submitted"], 0)
            self.assertTrue(result["audit_replay"]["valid"])


if __name__ == "__main__":
    unittest.main()
