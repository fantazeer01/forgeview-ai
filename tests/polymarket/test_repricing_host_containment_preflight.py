from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from polymarket.repricing_research.host_containment_preflight import (
    DENY_RULE_NAME,
    PROXY_RULE_NAME,
    SECRET_PROVIDER_ENV_NAME,
    FirewallProfile,
    HostSnapshot,
    OutboundRule,
    ReadOnlyWindowsInspector,
    _firewall_inspection_script,
    _read_governance,
    evaluate,
    proposed_firewall_plan,
)


NOW = datetime(2026, 7, 3, tzinfo=UTC)


def full_snapshot(**changes) -> HostSnapshot:
    governance = {
        "proxy": {"configured": True, "direct_egress_denied": True},
        "restricted_process": {"configured": True, "child_process_denied": True, "shell_denied": True},
        "kill_switch": {"configured": True, "host_drill_passed": True},
        "watchdog": {"configured": True, "host_drill_passed": True},
        "owners": {"rollback": "role-r", "revocation": "role-v", "incident": "role-i", "independent_approver": "role-a"},
        "authorization": {"id": "auth-fixture", "scope": "credentialed_no_order_calibration", "expires_at": (NOW + timedelta(hours=1)).isoformat()},
        "secret_provider": {"configured": True, "provider_id": "provider-fixture"},
        "host_drills": {"passed": True, "evidence_id": "drill-fixture"},
    }
    snapshot = HostSnapshot(
        profiles=tuple(FirewallProfile(name, True, "Block") for name in ("Domain", "Private", "Public")),
        outbound_rules=(
            OutboundRule(DENY_RULE_NAME, True, "Block", "Outbound", "C:/fixture/python.exe", "Any"),
            OutboundRule(PROXY_RULE_NAME, True, "Allow", "Outbound", "C:/fixture/python.exe", "127.0.0.1"),
        ),
        governance=governance,
        environment_names=frozenset({SECRET_PROVIDER_ENV_NAME}),
        fixture_child_pass=True,
    )
    values = snapshot.__dict__ | changes
    return HostSnapshot(**values)


class HostContainmentPreflightTests(unittest.TestCase):
    def test_full_pass_fixture(self) -> None:
        result = evaluate(full_snapshot(), NOW)
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["credential_calibration_authorized"])

    def test_all_firewall_profiles_disabled(self) -> None:
        profiles = tuple(FirewallProfile(name, False, "NotConfigured") for name in ("Domain", "Private", "Public"))
        result = evaluate(full_snapshot(profiles=profiles), NOW)
        self.assertIn("all_firewall_profiles_enabled", result["failed_gates"])

    def test_partial_firewall_enablement_fails(self) -> None:
        profiles = (
            FirewallProfile("Domain", True, "Block"), FirewallProfile("Private", True, "Block"), FirewallProfile("Public", False, "Block")
        )
        self.assertEqual(evaluate(full_snapshot(profiles=profiles), NOW)["status"], "NOT_READY_FOR_CREDENTIALS")

    def test_missing_scoped_outbound_rules_fails(self) -> None:
        result = evaluate(full_snapshot(outbound_rules=()), NOW)
        self.assertIn("deny_direct_egress_rule", result["failed_gates"])
        self.assertIn("allow_local_proxy_rule", result["failed_gates"])

    def test_missing_owner_records_fail(self) -> None:
        snapshot = full_snapshot()
        governance = snapshot.governance | {"owners": {}}
        failed = evaluate(full_snapshot(governance=governance), NOW)["failed_gates"]
        self.assertIn("rollback_owner_assigned", failed)
        self.assertIn("revocation_owner_assigned", failed)

    def test_missing_or_expired_authorization_fails(self) -> None:
        snapshot = full_snapshot()
        governance = snapshot.governance | {"authorization": {}}
        self.assertIn("authorization_record_valid", evaluate(full_snapshot(governance=governance), NOW)["failed_gates"])
        expired = {"id": "x", "scope": "credentialed_no_order_calibration", "expires_at": (NOW - timedelta(seconds=1)).isoformat()}
        governance = snapshot.governance | {"authorization": expired}
        self.assertIn("authorization_record_valid", evaluate(full_snapshot(governance=governance), NOW)["failed_gates"])

    def test_missing_secret_provider_config_fails_without_reading_values(self) -> None:
        snapshot = full_snapshot(environment_names=frozenset())
        self.assertIn("secret_provider_metadata_present", evaluate(snapshot, NOW)["failed_gates"])

    def test_inspector_only_iterates_environment_names(self) -> None:
        class NamesOnly(dict):
            def __getitem__(self, key):
                if key == SECRET_PROVIDER_ENV_NAME:
                    raise AssertionError("secret provider value read")
                return super().__getitem__(key)
        environment = NamesOnly({SECRET_PROVIDER_ENV_NAME: "must-not-read", "SYSTEMROOT": "C:/Windows"})
        payload = json.dumps({"profiles": [], "rules": []})
        inspector = ReadOnlyWindowsInspector(runner=lambda commands: payload, environ=environment)
        snapshot = inspector.inspect()
        self.assertIn(SECRET_PROVIDER_ENV_NAME, snapshot.environment_names)

    def test_inspection_script_contains_no_mutation_commands(self) -> None:
        script = _firewall_inspection_script().lower()
        for token in ("set-netfirewall", "new-netfirewall", "remove-netfirewall", "enable-netfirewall", "disable-netfirewall"):
            self.assertNotIn(token, script)
        self.assertIn("get-netfirewallprofile", script)

    def test_governance_rejects_secret_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "governance.json"
            path.write_text(json.dumps({"secret_provider": {"secret": "no"}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "forbidden secret"):
                _read_governance(path)

    def test_proposed_firewall_commands_are_data_not_executed(self) -> None:
        plan = proposed_firewall_plan()
        self.assertIn("New-NetFirewallRule", plan["apply_requires_separate_approval"][1])
        self.assertIn("Remove-NetFirewallRule", plan["rollback_requires_separate_approval"][0])


if __name__ == "__main__":
    unittest.main()
