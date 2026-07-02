from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .credentialed_calibration_policy import (
    REQUIRED_ENV_NAMES,
    CalibrationPolicyError,
    NoOrderCalibrationPolicy,
    audit_record,
)


class SandboxFailClosed(RuntimeError):
    pass


@dataclass(frozen=True)
class FixtureSecretHandle:
    name: str
    handle_id: str


@dataclass(frozen=True)
class AuditEnvelope:
    sequence: int
    run_id: str
    action: str
    allowed: bool
    reason: str
    method: str
    host: str
    path: str
    metadata_sha256: str
    predecessor_sha256: str | None
    envelope_sha256: str


class KillSwitch:
    def __init__(self, path: Path) -> None:
        self.path = path

    def arm(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("ARMED\n", encoding="ascii")

    def trip(self, reason: str = "operator_abort") -> None:
        self.path.write_text(f"TRIPPED:{reason}\n", encoding="ascii")

    def require_armed(self) -> None:
        try:
            state = self.path.read_text(encoding="ascii").strip()
        except OSError as exc:
            raise SandboxFailClosed("kill switch missing") from exc
        if state != "ARMED":
            raise SandboxFailClosed("kill switch not armed")


class SandboxWatchdog:
    def __init__(
        self,
        *,
        timeout_seconds: float = 1.0,
        parent_alive: Callable[[], bool] | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.parent_alive = parent_alive or (lambda: True)
        self.last_pulse = time.monotonic()
        self.proxy_alive = True

    def pulse(self) -> None:
        self.last_pulse = time.monotonic()

    def require_healthy(self) -> None:
        if not self.parent_alive():
            raise SandboxFailClosed("parent watchdog failed")
        if not self.proxy_alive:
            raise SandboxFailClosed("proxy watchdog failed")
        if time.monotonic() - self.last_pulse > self.timeout_seconds:
            raise SandboxFailClosed("watchdog deadline exceeded")


class RedactedAuditJournal:
    def __init__(self, path: Path, run_id: str = "fixture-sandbox-v1") -> None:
        self.path = path
        self.run_id = run_id
        self.sequence = 0
        self.predecessor: str | None = None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")

    def append(self, action: str, record: dict[str, Any]) -> AuditEnvelope:
        self.sequence += 1
        content = {
            "sequence": self.sequence,
            "run_id": self.run_id,
            "action": action,
            "allowed": bool(record["allowed"]),
            "reason": str(record["reason"]),
            "method": str(record["method"]),
            "host": str(record["host"]),
            "path": str(record["path"]),
            "metadata_sha256": str(record["metadata_sha256"]),
            "predecessor_sha256": self.predecessor,
        }
        digest = hashlib.sha256(_canonical(content)).hexdigest()
        envelope = AuditEnvelope(**content, envelope_sha256=digest)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(envelope), sort_keys=True, separators=(",", ":")) + "\n")
        self.predecessor = digest
        return envelope


class FixtureSecretProvider:
    def clean_child_environment(self) -> dict[str, FixtureSecretHandle]:
        return {
            name: FixtureSecretHandle(
                name=name,
                handle_id=hashlib.sha256(f"fixture-handle:{name}".encode()).hexdigest(),
            )
            for name in sorted(REQUIRED_ENV_NAMES)
        }


class FixtureEgressProxy:
    """Local deterministic response surface. It never opens a network socket."""

    def __init__(self, policy: NoOrderCalibrationPolicy | None = None) -> None:
        self.policy = policy or NoOrderCalibrationPolicy()
        self.alive = True
        self.open_orders: list[dict[str, Any]] = []

    def request(self, method: str, url: str) -> dict[str, Any]:
        if not self.alive:
            raise SandboxFailClosed("fixture proxy unavailable")
        self.policy.require(method, url)
        if url.startswith("https://clob.polymarket.com/data/orders"):
            return {"count": len(self.open_orders), "data": list(self.open_orders)}
        if url.startswith("https://clob.polymarket.com/trades"):
            return {"count": 0, "data": []}
        if url == "https://clob.polymarket.com/time":
            return {"server_time": 1_750_000_000}
        if url == "wss://ws-subscriptions-clob.polymarket.com/ws/user":
            return {"connected": True, "mode": "fixture_receive_only"}
        raise SandboxFailClosed("allowlisted route lacks fixture implementation")


class NoOrderCalibrationSandbox:
    def __init__(
        self,
        output: Path,
        *,
        proxy: FixtureEgressProxy | None = None,
        watchdog: SandboxWatchdog | None = None,
        operator_abort: Callable[[str], None] | None = None,
    ) -> None:
        self.output = output
        self.policy = NoOrderCalibrationPolicy()
        self.proxy = proxy or FixtureEgressProxy(self.policy)
        self.watchdog = watchdog or SandboxWatchdog()
        self.kill_switch = KillSwitch(output / "kill_switch.state")
        self.audit = RedactedAuditJournal(output / "sandbox_audit.jsonl")
        self.operator_abort = operator_abort or (lambda reason: None)
        self.environment = FixtureSecretProvider().clean_child_environment()
        self.ready = False

    def preflight(self) -> dict[str, Any]:
        self.kill_switch.require_armed()
        self.watchdog.proxy_alive = self.proxy.alive
        self.watchdog.require_healthy()
        self.policy.validate_environment_names(set(self.environment))
        orders = self.request("GET", "https://clob.polymarket.com/data/orders", via_proxy=True)
        if int(orders.get("count", -1)) != 0 or orders.get("data"):
            self.abort("open_order_gate_failed")
            raise SandboxFailClosed("zero-open-order gate failed")
        self.ready = True
        return {
            "kill_switch": "PASS",
            "watchdog": "PASS",
            "environment_names": "PASS",
            "proxy_only": "PASS",
            "open_orders": 0,
            "credentials": "fixture_handles_only",
        }

    def request(
        self,
        method: str,
        url: str,
        *,
        via_proxy: bool,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.kill_switch.require_armed()
        self.watchdog.proxy_alive = self.proxy.alive
        self.watchdog.require_healthy()
        if not via_proxy:
            record = audit_record(method, url, dict(metadata or {}))
            record.update({"allowed": False, "reason": "direct_egress_denied"})
            self.audit.append("request_denied", record)
            raise SandboxFailClosed("direct egress denied")
        record = audit_record(method, url, dict(metadata or {}))
        if not record["allowed"]:
            self.audit.append("request_denied", record)
            raise SandboxFailClosed(f"route denied: {record['method']} {record['path']}")
        try:
            response = self.proxy.request(method, url)
        except (CalibrationPolicyError, SandboxFailClosed) as exc:
            self.abort("proxy_or_policy_failure")
            raise SandboxFailClosed(str(exc)) from exc
        self.audit.append("request_allowed", record)
        self.watchdog.pulse()
        return response

    def abort(self, reason: str) -> None:
        self.ready = False
        self.kill_switch.trip(reason)
        self.operator_abort(reason)

    def rollback(self, reason: str) -> dict[str, Any]:
        self.abort(reason)
        self.proxy.alive = False
        return {
            "status": "ROLLED_BACK",
            "reason": reason,
            "proxy_alive": False,
            "restart_allowed": False,
            "operator_notified": True,
        }


def replay_audit(path: Path) -> dict[str, Any]:
    predecessor = None
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        digest = row.pop("envelope_sha256")
        if row["predecessor_sha256"] != predecessor:
            return {"valid": False, "reason": "predecessor_mismatch"}
        expected = hashlib.sha256(_canonical(row)).hexdigest()
        if expected != digest:
            return {"valid": False, "reason": "hash_mismatch"}
        predecessor = digest
        count += 1
    return {"valid": True, "records": count, "terminal_hash": predecessor}


def run_fixture_validation(output: Path) -> dict[str, Any]:
    sandbox = NoOrderCalibrationSandbox(output)
    sandbox.kill_switch.arm()
    preflight = sandbox.preflight()
    allowed = [
        sandbox.request("GET", "https://clob.polymarket.com/trades", via_proxy=True),
        sandbox.request("GET", "https://clob.polymarket.com/time", via_proxy=True),
        sandbox.request("CONNECT", "wss://ws-subscriptions-clob.polymarket.com/ws/user", via_proxy=True),
    ]
    denied = 0
    for method, url in (
        ("POST", "https://clob.polymarket.com/order"),
        ("DELETE", "https://clob.polymarket.com/cancel-all"),
        ("POST", "https://clob.polymarket.com/heartbeats"),
        ("GET", "https://clob.polymarket.com/unknown"),
    ):
        try:
            sandbox.request(method, url, via_proxy=True)
        except SandboxFailClosed:
            denied += 1
    rollback = sandbox.rollback("fixture_validation_complete")
    replay = replay_audit(sandbox.audit.path)
    result = {
        "preflight": preflight,
        "allowed_fixture_requests": len(allowed),
        "forbidden_requests_denied": denied,
        "audit_replay": replay,
        "rollback": rollback,
        "credentials_used": False,
        "authenticated_calls": 0,
        "orders_submitted": 0,
        "cancellations_submitted": 0,
        "network_scope": "no_network_fixture_proxy",
        "verdict": "SANDBOX_FIXTURE_READY_REAL_CALIBRATION_NOT_AUTHORIZED",
    }
    (output / "sandbox_validation.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fixture-only no-order calibration sandbox")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(run_fixture_validation(args.output), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
