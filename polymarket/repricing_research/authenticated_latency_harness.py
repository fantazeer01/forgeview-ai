from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol


PROTOCOL_VERSION = "authenticated_execution_latency_v1"
SENSITIVE_TERMS = ("private_key", "seed", "passphrase", "api_secret", "authorization")


class HarnessSafetyError(RuntimeError):
    pass


class AmbiguousSubmissionError(RuntimeError):
    pass


class PreSendTransportError(RuntimeError):
    pass


class Signer(Protocol):
    def sign(self, payload: bytes) -> str: ...


class CredentialProvider(Protocol):
    def headers(self, payload: bytes) -> dict[str, str]: ...


class Transport(Protocol):
    async def post(self, body: bytes, headers: dict[str, str]) -> tuple[dict[str, Any], int, int]: ...


@dataclass(frozen=True)
class EventEnvelope:
    protocol_version: str
    run_id: str
    event_id: str
    correlation_id: str
    order_intent_id: str
    event_name: str
    sequence: int
    attempt: int
    utc_ns: int
    monotonic_ns: int
    clock_offset_ms: float
    clock_uncertainty_ms: float
    predecessor_event_id: str | None
    payload_sha256: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class AttemptResult:
    correlation_id: str
    outcome: str
    retry_count: int
    signal_to_ack_ms: float
    signal_to_first_transition_ms: float
    signal_to_terminal_ms: float
    decision_ms: float
    signing_ms: float
    serialization_ms: float
    queue_ms: float
    transport_ack_ms: float
    exchange_fixture_ms: float
    cancellation_ms: float | None


class FixtureSigner:
    """Deterministic non-cryptographic boundary probe; never handles a key."""

    def sign(self, payload: bytes) -> str:
        return hashlib.sha256(b"fixture-signature-v1\0" + payload).hexdigest()


class FixtureCredentialProvider:
    """Produces harmless local-sink headers, never exchange credentials."""

    def headers(self, payload: bytes) -> dict[str, str]:
        digest = hashlib.sha256(b"fixture-l2-v1\0" + payload).hexdigest()
        return {"X-ForgeView-Fixture-Auth": digest, "Content-Type": "application/json"}


class ClockMonitor:
    def __init__(self, offset_ms: float = 0.0, uncertainty_ms: float = 0.5) -> None:
        self.offset_ms = offset_ms
        self.uncertainty_ms = uncertainty_ms

    def validate(self) -> None:
        if abs(self.offset_ms) > 50 or self.uncertainty_ms > 50:
            raise HarnessSafetyError("clock gate failed")


class EventJournal:
    def __init__(self, path: Path, run_id: str, clock: ClockMonitor) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")
        self.run_id = run_id
        self.clock = clock
        self.events: list[EventEnvelope] = []
        self.last_by_correlation: dict[str, str] = {}
        self.sequence_by_correlation: dict[str, int] = {}

    def emit(
        self,
        correlation_id: str,
        order_intent_id: str,
        event_name: str,
        *,
        attempt: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> EventEnvelope:
        metadata = metadata or {}
        _assert_redacted(metadata)
        sequence = self.sequence_by_correlation.get(correlation_id, 0) + 1
        payload = _canonical({"event_name": event_name, "metadata": metadata})
        payload_hash = hashlib.sha256(payload).hexdigest()
        identity = _canonical({
            "protocol_version": PROTOCOL_VERSION,
            "run_id": self.run_id,
            "correlation_id": correlation_id,
            "event_name": event_name,
            "sequence": sequence,
            "attempt": attempt,
            "payload_sha256": payload_hash,
        })
        event = EventEnvelope(
            protocol_version=PROTOCOL_VERSION,
            run_id=self.run_id,
            event_id=hashlib.sha256(identity).hexdigest(),
            correlation_id=correlation_id,
            order_intent_id=order_intent_id,
            event_name=event_name,
            sequence=sequence,
            attempt=attempt,
            utc_ns=time.time_ns(),
            monotonic_ns=time.perf_counter_ns(),
            clock_offset_ms=self.clock.offset_ms,
            clock_uncertainty_ms=self.clock.uncertainty_ms,
            predecessor_event_id=self.last_by_correlation.get(correlation_id),
            payload_sha256=payload_hash,
            metadata=metadata,
        )
        line = json.dumps(asdict(event), sort_keys=True, separators=(",", ":"))
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        self.events.append(event)
        self.last_by_correlation[correlation_id] = event.event_id
        self.sequence_by_correlation[correlation_id] = sequence
        return event


class LocalExecutionSink:
    def __init__(self) -> None:
        self.server: asyncio.AbstractServer | None = None
        self.port = 0

    async def __aenter__(self) -> "LocalExecutionSink":
        self.server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        self.port = int(self.server.sockets[0].getsockname()[1])
        return self

    async def __aexit__(self, *_: object) -> None:
        assert self.server is not None
        self.server.close()
        await self.server.wait_closed()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            head = await reader.readuntil(b"\r\n\r\n")
            length = 0
            for line in head.decode("ascii").split("\r\n"):
                if line.lower().startswith("content-length:"):
                    length = int(line.split(":", 1)[1].strip())
            body = await reader.readexactly(length)
            request = json.loads(body)
            await asyncio.sleep(float(request.get("fixture_delay_ms", 1)) / 1000)
            response = _canonical({
                "success": True,
                "status": "live",
                "orderID": hashlib.sha256(str(request["intent"]["intent_id"]).encode()).hexdigest(),
            })
            writer.write(
                b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                + f"Content-Length: {len(response)}\r\nConnection: close\r\n\r\n".encode()
                + response
            )
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()


class LoopbackTransport:
    def __init__(self, port: int) -> None:
        self.port = port

    async def post(self, body: bytes, headers: dict[str, str]) -> tuple[dict[str, Any], int, int]:
        if self.port <= 0:
            raise HarnessSafetyError("loopback sink is not active")
        reader, writer = await asyncio.open_connection("127.0.0.1", self.port)
        lines = [
            "POST /fixture-order HTTP/1.1",
            "Host: 127.0.0.1",
            f"Content-Length: {len(body)}",
            *[f"{key}: {value}" for key, value in sorted(headers.items())],
            "Connection: close",
            "",
            "",
        ]
        writer.write("\r\n".join(lines).encode("ascii") + body)
        await writer.drain()
        sent_ns = time.perf_counter_ns()
        head = await reader.readuntil(b"\r\n\r\n")
        first_byte_ns = time.perf_counter_ns()
        length = 0
        for line in head.decode("ascii").split("\r\n"):
            if line.lower().startswith("content-length:"):
                length = int(line.split(":", 1)[1].strip())
        response = json.loads(await reader.readexactly(length))
        writer.close()
        await writer.wait_closed()
        return response, sent_ns, first_byte_ns


class DryRunHarness:
    def __init__(
        self,
        output: Path,
        *,
        signer: Signer | None = None,
        credentials: CredentialProvider | None = None,
        clock: ClockMonitor | None = None,
        transport_override: Transport | None = None,
    ) -> None:
        self.output = output
        self.signer = signer or FixtureSigner()
        self.credentials = credentials or FixtureCredentialProvider()
        self.clock = clock or ClockMonitor()
        self.transport_override = transport_override
        self.run_id = "dry-run-v1"
        self.journal = EventJournal(output / "latency_events.jsonl", self.run_id, self.clock)

    async def run(self, attempts: int = 120) -> dict[str, Any]:
        if attempts < 1 or attempts > 1000:
            raise ValueError("attempts must be between 1 and 1000")
        self.clock.validate()
        async with LocalExecutionSink() as sink:
            transport = self.transport_override or LoopbackTransport(sink.port)
            results = [await self._attempt(i, transport) for i in range(attempts)]
        replay = replay_journal(self.journal.path)
        if not replay["valid"]:
            raise HarnessSafetyError("journal replay failed")
        summary = summarize(results)
        deterministic_summary = {
            "attempts": attempts,
            "identity_hash": replay["identity_hash"],
            "events": replay["events"],
            "outcomes": summary["outcomes"],
            "protocol_version": PROTOCOL_VERSION,
        }
        summary.update({
            "protocol_version": PROTOCOL_VERSION,
            "attempts": attempts,
            "authentication_mode": "fixture_stub_only",
            "network_scope": "127.0.0.1_only",
            "credentials_used": False,
            "orders_submitted": 0,
            "exchange_latency_measured": False,
            "replay": replay,
            "deterministic_identity_hash": replay["identity_hash"],
            "deterministic_summary_hash": hashlib.sha256(_canonical(deterministic_summary)).hexdigest(),
        })
        self.output.mkdir(parents=True, exist_ok=True)
        (self.output / "benchmark_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        _write_results(self.output / "attempt_latencies.csv", results)
        return summary

    async def _attempt(self, index: int, transport: Transport) -> AttemptResult:
        correlation = hashlib.sha256(f"dry-run-v1:{index}".encode()).hexdigest()
        intent_id = hashlib.sha256(f"intent:{correlation}".encode()).hexdigest()
        self.journal.emit(correlation, intent_id, "signal_generated")
        signal_ns = time.perf_counter_ns()
        decision_start = time.perf_counter_ns()
        intent = {
            "intent_id": intent_id,
            "asset": ("BTC", "ETH", "SOL")[index % 3],
            "side": ("YES", "NO")[index % 2],
            "price": "0.50",
            "size": "0",
            "fixture_delay_ms": 1 + index % 4,
            "economically_meaningful": False,
        }
        decision_ns = time.perf_counter_ns()
        self.journal.emit(correlation, intent_id, "decision_completed")
        payload = _canonical(intent)
        sign_start = time.perf_counter_ns()
        self.journal.emit(correlation, intent_id, "sign_start")
        signature = self.signer.sign(payload)
        sign_end = time.perf_counter_ns()
        self.journal.emit(correlation, intent_id, "sign_complete", metadata={"signature_hash": hashlib.sha256(signature.encode()).hexdigest()})
        serialize_start = time.perf_counter_ns()
        body = _canonical({"intent": intent, "fixture_signature": signature})
        headers = self.credentials.headers(body)
        serialize_end = time.perf_counter_ns()
        self.journal.emit(correlation, intent_id, "serialize_complete", metadata={"body_hash": hashlib.sha256(body).hexdigest()})
        queued_ns = time.perf_counter_ns()
        self.journal.emit(correlation, intent_id, "request_queued")
        retry_count = 0
        try:
            response, sent_ns, first_byte_ns = await transport.post(body, headers)
        except PreSendTransportError:
            retry_count = 1
            self.journal.emit(correlation, intent_id, "retry_scheduled", attempt=1, metadata={"reason": "proven_pre_send_failure"})
            response, sent_ns, first_byte_ns = await transport.post(body, headers)
        except (asyncio.TimeoutError, TimeoutError) as exc:
            self.journal.emit(correlation, intent_id, "timeout", metadata={"classification": "ambiguous_after_submission"})
            self.journal.emit(correlation, intent_id, "terminal", metadata={"outcome": "failed_closed"})
            raise AmbiguousSubmissionError("ambiguous submission failed closed without retry") from exc
        complete_ns = time.perf_counter_ns()
        self.journal.emit(correlation, intent_id, "request_sent")
        self.journal.emit(correlation, intent_id, "response_first_byte")
        self.journal.emit(correlation, intent_id, "response_complete")
        order_hash = hashlib.sha256(response["orderID"].encode()).hexdigest()
        self.journal.emit(correlation, intent_id, "order_accepted", metadata={"order_id_hash": order_hash, "source": "local_fixture"})
        ack_ns = time.perf_counter_ns()
        await asyncio.sleep((1 + index % 3) / 1000)
        transition_ns = time.perf_counter_ns()
        if index % 2 == 0:
            self.journal.emit(correlation, intent_id, "user_order_event", metadata={"type": "UPDATE", "source": "fixture"})
            self.journal.emit(correlation, intent_id, "partial_fill", metadata={"matched": "0.5"})
            await asyncio.sleep(0.001)
            self.journal.emit(correlation, intent_id, "complete_fill", metadata={"matched": "1.0"})
            terminal_ns = time.perf_counter_ns()
            outcome = "fixture_fill"
            cancellation_ms = None
        else:
            cancel_start = time.perf_counter_ns()
            self.journal.emit(correlation, intent_id, "cancel_intent")
            await asyncio.sleep(0.001)
            self.journal.emit(correlation, intent_id, "cancel_ack", metadata={"source": "fixture"})
            self.journal.emit(correlation, intent_id, "cancel_observed", metadata={"source": "fixture"})
            terminal_ns = time.perf_counter_ns()
            outcome = "fixture_cancel"
            cancellation_ms = (terminal_ns - cancel_start) / 1_000_000
        self.journal.emit(correlation, intent_id, "terminal", metadata={"outcome": outcome})
        return AttemptResult(
            correlation_id=correlation,
            outcome=outcome,
            retry_count=retry_count,
            signal_to_ack_ms=(ack_ns - signal_ns) / 1_000_000,
            signal_to_first_transition_ms=(transition_ns - signal_ns) / 1_000_000,
            signal_to_terminal_ms=(terminal_ns - signal_ns) / 1_000_000,
            decision_ms=(decision_ns - decision_start) / 1_000_000,
            signing_ms=(sign_end - sign_start) / 1_000_000,
            serialization_ms=(serialize_end - serialize_start) / 1_000_000,
            queue_ms=(sent_ns - queued_ns) / 1_000_000,
            transport_ack_ms=(first_byte_ns - sent_ns) / 1_000_000,
            exchange_fixture_ms=(transition_ns - complete_ns) / 1_000_000,
            cancellation_ms=cancellation_ms,
        )


def replay_journal(path: Path) -> dict[str, Any]:
    seen: set[str] = set()
    last: dict[str, tuple[str, int, int]] = {}
    identities: list[str] = []
    terminal = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        _assert_redacted(row.get("metadata", {}))
        event_id = row["event_id"]
        correlation = row["correlation_id"]
        if event_id in seen:
            return {"valid": False, "reason": "duplicate_event_id"}
        previous = last.get(correlation)
        if previous:
            if row["predecessor_event_id"] != previous[0]:
                return {"valid": False, "reason": "predecessor_mismatch"}
            if row["sequence"] != previous[1] + 1 or row["monotonic_ns"] < previous[2]:
                return {"valid": False, "reason": "sequence_or_time_regression"}
        elif row["predecessor_event_id"] is not None or row["sequence"] != 1:
            return {"valid": False, "reason": "invalid_first_event"}
        seen.add(event_id)
        identities.append(event_id)
        last[correlation] = (event_id, row["sequence"], row["monotonic_ns"])
        terminal += row["event_name"] == "terminal"
    identity_hash = hashlib.sha256("\n".join(identities).encode()).hexdigest()
    return {"valid": terminal == len(last), "events": len(seen), "correlations": len(last), "terminal": terminal, "identity_hash": identity_hash}


def summarize(results: list[AttemptResult]) -> dict[str, Any]:
    metrics = {}
    for field in (
        "signal_to_ack_ms", "signal_to_first_transition_ms", "signal_to_terminal_ms",
        "decision_ms", "signing_ms", "serialization_ms", "queue_ms",
        "transport_ack_ms", "exchange_fixture_ms", "cancellation_ms",
    ):
        values = [float(getattr(row, field)) for row in results if getattr(row, field) is not None]
        metrics[field] = _stats(values)
    return {
        "metrics": metrics,
        "outcomes": {name: sum(row.outcome == name for row in results) for name in sorted({row.outcome for row in results})},
        "admission_gates": {
            "signal_to_ack_p95_le_750ms": metrics["signal_to_ack_ms"]["p95"] <= 750,
            "first_transition_p95_le_1000ms": metrics["signal_to_first_transition_ms"]["p95"] <= 1000,
            "terminal_p95_le_1500ms": metrics["signal_to_terminal_ms"]["p95"] <= 1500,
            "scope": "local_dry_run_only_not_authenticated_exchange_admission",
        },
    }


def _stats(values: list[float]) -> dict[str, float | int]:
    ordered = sorted(values)
    if not ordered:
        return {"count": 0, "min": 0.0, "mean": 0.0, "median": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}
    return {
        "count": len(ordered), "min": ordered[0], "mean": sum(ordered) / len(ordered),
        "median": _percentile(ordered, 50), "p90": _percentile(ordered, 90),
        "p95": _percentile(ordered, 95), "p99": _percentile(ordered, 99), "max": ordered[-1],
    }


def _percentile(ordered: list[float], percentile: float) -> float:
    position = (len(ordered) - 1) * percentile / 100
    low, high = math.floor(position), math.ceil(position)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _assert_redacted(value: Any) -> None:
    text = json.dumps(value, sort_keys=True).lower()
    if any(term in text for term in SENSITIVE_TERMS):
        raise HarnessSafetyError("sensitive field rejected")


def _write_results(path: Path, results: list[AttemptResult]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(results[0])))
        writer.writeheader()
        writer.writerows(asdict(row) for row in results)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local-only authenticated latency dry-run harness")
    parser.add_argument("--attempts", type=int, default=120)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = asyncio.run(DryRunHarness(args.output).run(args.attempts))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
