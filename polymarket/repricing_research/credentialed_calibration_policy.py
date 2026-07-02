from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit


class CalibrationPolicyError(RuntimeError):
    pass


ALLOWED_REQUESTS = frozenset({
    ("GET", "https", "clob.polymarket.com", "/data/orders"),
    ("GET", "https", "clob.polymarket.com", "/trades"),
    ("GET", "https", "clob.polymarket.com", "/time"),
    ("CONNECT", "wss", "ws-subscriptions-clob.polymarket.com", "/ws/user"),
})

FORBIDDEN_ENV_NAMES = frozenset({
    "PRIVATE_KEY", "POLYMARKET_PRIVATE_KEY", "WALLET_PRIVATE_KEY", "SEED_PHRASE",
})

REQUIRED_ENV_NAMES = frozenset({
    "FORGEVIEW_CALIBRATION_API_KEY",
    "FORGEVIEW_CALIBRATION_API_SECRET",
    "FORGEVIEW_CALIBRATION_PASSPHRASE",
    "FORGEVIEW_CALIBRATION_ADDRESS",
    "FORGEVIEW_CALIBRATION_AUTHORIZATION_ID",
    "FORGEVIEW_CALIBRATION_KILL_SWITCH_PATH",
})

SENSITIVE_NAMES = (
    "api_key", "api_secret", "passphrase", "signature", "authorization",
    "poly_api_key", "poly_passphrase", "poly_signature", "private_key", "seed",
)


@dataclass(frozen=True)
class RequestDecision:
    allowed: bool
    reason: str
    method: str
    host: str
    path: str


class NoOrderCalibrationPolicy:
    """Deny-by-default policy for a future separately authorized calibration."""

    def authorize(self, method: str, url: str) -> RequestDecision:
        normalized_method = method.upper().strip()
        parsed = urlsplit(url)
        key = (normalized_method, parsed.scheme.lower(), (parsed.hostname or "").lower(), parsed.path)
        allowed = key in ALLOWED_REQUESTS
        return RequestDecision(
            allowed=allowed,
            reason="exact_allowlist_match" if allowed else "deny_by_default",
            method=normalized_method,
            host=key[2],
            path=parsed.path,
        )

    def require(self, method: str, url: str) -> None:
        decision = self.authorize(method, url)
        if not decision.allowed:
            raise CalibrationPolicyError(
                f"request blocked: {decision.method} {decision.host}{decision.path}"
            )

    def validate_environment_names(self, names: set[str]) -> None:
        forbidden = sorted(names & FORBIDDEN_ENV_NAMES)
        missing = sorted(REQUIRED_ENV_NAMES - names)
        if forbidden:
            raise CalibrationPolicyError(f"forbidden environment names: {forbidden}")
        if missing:
            raise CalibrationPolicyError(f"missing required environment names: {missing}")


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        output = {}
        for key, item in value.items():
            normalized = str(key).lower()
            output[key] = "[REDACTED]" if any(term in normalized for term in SENSITIVE_NAMES) else redact(item)
        return output
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    return value


def audit_record(method: str, url: str, metadata: dict[str, Any]) -> dict[str, Any]:
    policy = NoOrderCalibrationPolicy()
    decision = policy.authorize(method, url)
    sanitized = redact(metadata)
    canonical = json.dumps(sanitized, sort_keys=True, separators=(",", ":"))
    return {
        "allowed": decision.allowed,
        "reason": decision.reason,
        "method": decision.method,
        "host": decision.host,
        "path": decision.path,
        "metadata": sanitized,
        "metadata_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
    }
