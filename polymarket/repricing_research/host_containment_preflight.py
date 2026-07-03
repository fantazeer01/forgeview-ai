from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Mapping


PROFILE_NAMES = ("Domain", "Private", "Public")
DENY_RULE_NAME = "ForgeView Calibration Deny Direct Egress"
PROXY_RULE_NAME = "ForgeView Calibration Allow Local Proxy"
SECRET_PROVIDER_ENV_NAME = "FORGEVIEW_CALIBRATION_SECRET_PROVIDER_CONFIG"
FORBIDDEN_METADATA_KEYS = (
    "secret", "passphrase", "private_key", "seed", "credential_value", "token_value",
)


@dataclass(frozen=True)
class FirewallProfile:
    name: str
    enabled: bool
    default_outbound_action: str


@dataclass(frozen=True)
class OutboundRule:
    name: str
    enabled: bool
    action: str
    direction: str
    application: str
    remote_address: str


@dataclass(frozen=True)
class HostSnapshot:
    profiles: tuple[FirewallProfile, ...]
    outbound_rules: tuple[OutboundRule, ...]
    governance: dict[str, Any]
    environment_names: frozenset[str]
    fixture_child_pass: bool
    inspection_error: str | None = None


class ReadOnlyWindowsInspector:
    def __init__(
        self,
        *,
        runner: Callable[[list[str]], str] | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        self.runner = runner or _run_read_only_powershell
        self.environ = environ if environ is not None else os.environ

    def inspect(self, governance_path: Path | None = None) -> HostSnapshot:
        governance = _read_governance(governance_path)
        child_pass = run_fixture_child(self.environ)
        try:
            payload = json.loads(self.runner([_firewall_inspection_script()]))
            profiles = tuple(
                FirewallProfile(
                    name=str(row["Name"]),
                    enabled=bool(row["Enabled"]),
                    default_outbound_action=str(row.get("DefaultOutboundAction") or "NotConfigured"),
                )
                for row in payload.get("profiles", [])
            )
            rules = tuple(
                OutboundRule(
                    name=str(row["Name"]),
                    enabled=bool(row["Enabled"]),
                    action=str(row["Action"]),
                    direction=str(row["Direction"]),
                    application=str(row.get("Application") or ""),
                    remote_address=str(row.get("RemoteAddress") or ""),
                )
                for row in payload.get("rules", [])
            )
            error = None
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError, KeyError, TypeError) as exc:
            profiles, rules, error = (), (), type(exc).__name__
        return HostSnapshot(
            profiles=profiles,
            outbound_rules=rules,
            governance=governance,
            environment_names=frozenset(iter(self.environ)),
            fixture_child_pass=child_pass,
            inspection_error=error,
        )


def evaluate(snapshot: HostSnapshot, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    profiles = {profile.name: profile for profile in snapshot.profiles}
    rules = {rule.name: rule for rule in snapshot.outbound_rules}
    governance = snapshot.governance

    all_profiles = all(name in profiles and profiles[name].enabled for name in PROFILE_NAMES)
    deny_rule = _rule_ready(rules.get(DENY_RULE_NAME), "Block")
    proxy_rule = _rule_ready(rules.get(PROXY_RULE_NAME), "Allow", loopback=True)
    proxy = governance.get("proxy", {})
    process = governance.get("restricted_process", {})
    owners = governance.get("owners", {})
    authorization = governance.get("authorization", {})
    secret_provider = governance.get("secret_provider", {})
    drills = governance.get("host_drills", {})
    kill_switch = governance.get("kill_switch", {})
    watchdog = governance.get("watchdog", {})

    authorization_valid = _authorization_valid(authorization, now)
    provider_name_present = SECRET_PROVIDER_ENV_NAME in snapshot.environment_names
    gates = {
        "firewall_inspection": snapshot.inspection_error is None,
        "all_firewall_profiles_enabled": all_profiles,
        "deny_direct_egress_rule": deny_rule,
        "allow_local_proxy_rule": proxy_rule,
        "proxy_only_egress_ready": bool(proxy.get("configured")) and bool(proxy.get("direct_egress_denied")) and deny_rule and proxy_rule,
        "restricted_process_identity_ready": bool(process.get("configured")) and bool(process.get("child_process_denied")) and bool(process.get("shell_denied")),
        "fixture_child_clean_environment": snapshot.fixture_child_pass,
        "kill_switch_ready": bool(kill_switch.get("configured")) and bool(kill_switch.get("host_drill_passed")),
        "watchdog_ready": bool(watchdog.get("configured")) and bool(watchdog.get("host_drill_passed")),
        "rollback_owner_assigned": _assigned(owners.get("rollback")),
        "revocation_owner_assigned": _assigned(owners.get("revocation")),
        "incident_owner_assigned": _assigned(owners.get("incident")),
        "independent_approver_assigned": _assigned(owners.get("independent_approver")),
        "authorization_record_valid": authorization_valid,
        "secret_provider_metadata_present": bool(secret_provider.get("configured")) and bool(secret_provider.get("provider_id")) and provider_name_present,
        "host_failure_drills_passed": bool(drills.get("passed")) and bool(drills.get("evidence_id")),
    }
    failed = [name for name, passed in gates.items() if not passed]
    return {
        "status": "PASS" if not failed else "NOT_READY_FOR_CREDENTIALS",
        "credential_calibration_authorized": False,
        "gates": gates,
        "failed_gates": failed,
        "inspection_error": snapshot.inspection_error,
        "profiles": [asdict(profile) for profile in snapshot.profiles],
        "outbound_rules": [asdict(rule) for rule in snapshot.outbound_rules],
        "secret_values_read": False,
        "host_settings_modified": False,
    }


def run_preflight(output: Path, governance_path: Path | None = None) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    result = evaluate(ReadOnlyWindowsInspector().inspect(governance_path))
    (output / "host_preflight_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def run_fixture_child(environ: Mapping[str, str]) -> bool:
    allowed_names = ("SYSTEMROOT", "WINDIR", "TEMP", "TMP")
    clean = {name: environ[name] for name in allowed_names if name in environ}
    clean["FORGEVIEW_FIXTURE_CHILD"] = "1"
    script = (
        "import os,sys; forbidden=('PRIVATE_KEY','SEED','PASSPHRASE','API_SECRET');"
        "sys.exit(0 if os.environ.get('FORGEVIEW_FIXTURE_CHILD')=='1' and "
        "not any(any(x in k.upper() for x in forbidden) for k in os.environ) else 2)"
    )
    completed = subprocess.run(
        [sys.executable, "-I", "-c", script],
        env=clean,
        shell=False,
        capture_output=True,
        timeout=10,
        check=False,
    )
    return completed.returncode == 0 and completed.stdout == b"" and completed.stderr == b""


def proposed_firewall_plan() -> dict[str, list[str]]:
    return {
        "apply_requires_separate_approval": [
            "Enable-NetFirewallRule is intentionally not generated or executed by preflight",
            f"New-NetFirewallRule -DisplayName '{DENY_RULE_NAME}' -Direction Outbound -Action Block -Program '<REVIEWED_CALIBRATION_EXECUTABLE>'",
            f"New-NetFirewallRule -DisplayName '{PROXY_RULE_NAME}' -Direction Outbound -Action Allow -Program '<REVIEWED_CALIBRATION_EXECUTABLE>' -RemoteAddress 127.0.0.1",
        ],
        "rollback_requires_separate_approval": [
            f"Remove-NetFirewallRule -DisplayName '{PROXY_RULE_NAME}'",
            f"Remove-NetFirewallRule -DisplayName '{DENY_RULE_NAME}'",
        ],
    }


def _read_governance(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    _reject_sensitive_metadata(payload)
    return payload


def _reject_sensitive_metadata(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if any(term in str(key).lower() for term in FORBIDDEN_METADATA_KEYS):
                raise ValueError("governance metadata contains forbidden secret field")
            _reject_sensitive_metadata(item)
    elif isinstance(value, list):
        for item in value:
            _reject_sensitive_metadata(item)


def _rule_ready(rule: OutboundRule | None, action: str, loopback: bool = False) -> bool:
    if rule is None or not rule.enabled or rule.action.lower() != action.lower() or rule.direction.lower() != "outbound":
        return False
    return not loopback or rule.remote_address in {"127.0.0.1", "LocalSubnet:127.0.0.1"}


def _assigned(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value not in {"TBD", "UNASSIGNED"}


def _authorization_valid(value: dict[str, Any], now: datetime) -> bool:
    try:
        expires = datetime.fromisoformat(str(value["expires_at"]).replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError):
        return False
    return (
        _assigned(value.get("id"))
        and value.get("scope") == "credentialed_no_order_calibration"
        and expires.tzinfo is not None
        and expires > now
    )


def _firewall_inspection_script() -> str:
    return """
$profiles = @(Get-NetFirewallProfile | Select-Object Name,Enabled,DefaultOutboundAction)
$names = @('ForgeView Calibration Deny Direct Egress','ForgeView Calibration Allow Local Proxy')
$rules = @(Get-NetFirewallRule -Direction Outbound -ErrorAction SilentlyContinue |
  Where-Object { $_.DisplayName -in $names } | ForEach-Object {
    $app = Get-NetFirewallApplicationFilter -AssociatedNetFirewallRule $_ -ErrorAction SilentlyContinue
    $addr = Get-NetFirewallAddressFilter -AssociatedNetFirewallRule $_ -ErrorAction SilentlyContinue
    [PSCustomObject]@{Name=$_.DisplayName;Enabled=($_.Enabled -eq 'True');Action=[string]$_.Action;Direction=[string]$_.Direction;Application=[string]$app.Program;RemoteAddress=[string]$addr.RemoteAddress}
  })
[PSCustomObject]@{profiles=$profiles;rules=$rules} | ConvertTo-Json -Depth 5 -Compress
""".strip()


def _run_read_only_powershell(commands: list[str]) -> str:
    if len(commands) != 1:
        raise ValueError("exactly one inspection script is required")
    lowered = commands[0].lower()
    forbidden = ("set-netfirewall", "new-netfirewall", "remove-netfirewall", "enable-netfirewall", "disable-netfirewall")
    if any(token in lowered for token in forbidden):
        raise ValueError("mutation command rejected")
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", commands[0]],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    return completed.stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only no-order host containment preflight")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--governance", type=Path)
    args = parser.parse_args(argv)
    result = run_preflight(args.output, args.governance)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
