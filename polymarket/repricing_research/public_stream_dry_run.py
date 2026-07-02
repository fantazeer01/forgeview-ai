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
from typing import Any, AsyncIterator

from websockets.asyncio.client import connect

from polymarket.edge_engine_v4.market_discovery import PolymarketMarketDiscovery
from .authenticated_latency_harness import (
    DryRunHarness,
    LocalExecutionSink,
    LoopbackTransport,
    _stats,
    replay_journal,
)
from .websocket_latency import CLOB_WS, _timestamp_ms


@dataclass(frozen=True)
class PublicEvent:
    token_id: str
    asset: str
    event_type: str
    server_timestamp_ms: int | None
    received_wall_ns: int
    received_monotonic_ns: int
    payload_hash: str


@dataclass(frozen=True)
class CorrelationResult:
    correlation_id: str
    asset: str
    event_type: str
    event_age_ms: float | None
    source_to_signal_ms: float
    signal_to_local_ack_ms: float
    signal_to_public_transition_ms: float | None
    signal_to_terminal_ms: float
    public_transition_observed: bool
    outcome: str


class PublicStreamAdapter:
    def __init__(self, *, stale_after_ms: float = 2_000.0, sample_interval_ms: float = 250.0) -> None:
        self.stale_after_ms = stale_after_ms
        self.sample_interval_ns = int(sample_interval_ms * 1_000_000)
        self.last_received_ns: dict[str, int] = {}
        self.last_sampled_ns: dict[str, int] = {}
        self.event_gaps_ms: list[float] = []
        self.received = 0
        self.stale = 0
        self.duplicates = 0
        self.dropped = 0
        self.reconnects = 0
        self.seen: set[str] = set()

    def observe(self, event: PublicEvent) -> tuple[bool, str]:
        self.received += 1
        previous = self.last_received_ns.get(event.token_id)
        if previous is not None:
            self.event_gaps_ms.append((event.received_monotonic_ns - previous) / 1_000_000)
        self.last_received_ns[event.token_id] = event.received_monotonic_ns
        identity = hashlib.sha256(
            f"{event.token_id}:{event.server_timestamp_ms}:{event.event_type}:{event.payload_hash}".encode()
        ).hexdigest()
        if identity in self.seen:
            self.duplicates += 1
            return False, "duplicate"
        self.seen.add(identity)
        age = event_age_ms(event)
        if age is not None and age > self.stale_after_ms:
            self.stale += 1
            return False, "stale"
        last_sample = self.last_sampled_ns.get(event.token_id)
        if last_sample is not None and event.received_monotonic_ns - last_sample < self.sample_interval_ns:
            return False, "sample_interval"
        self.last_sampled_ns[event.token_id] = event.received_monotonic_ns
        return True, "accepted"


class PublicStreamDryRun:
    def __init__(self, output: Path, *, max_attempts: int = 60, queue_size: int = 256, concurrency: int = 8) -> None:
        self.output = output
        self.max_attempts = max_attempts
        self.queue_size = queue_size
        self.concurrency = concurrency
        self.adapter = PublicStreamAdapter()
        self.harness = DryRunHarness(output / "harness")
        self.waiters: dict[str, list[tuple[int, asyncio.Future[int]]]] = {}
        self.results: list[CorrelationResult] = []

    async def run(self, source: AsyncIterator[PublicEvent]) -> dict[str, Any]:
        queue: asyncio.Queue[PublicEvent | None] = asyncio.Queue(maxsize=self.queue_size)

        async def produce() -> None:
            async for event in source:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    self.adapter.dropped += 1
            await queue.put(None)

        producer = asyncio.create_task(produce())
        active: set[asyncio.Task[None]] = set()
        async with LocalExecutionSink() as sink:
            transport = LoopbackTransport(sink.port)
            while True:
                event = await queue.get()
                if event is None:
                    break
                self._complete_waiters(event)
                accepted, _ = self.adapter.observe(event)
                if not accepted or len(self.results) + len(active) >= self.max_attempts:
                    continue
                if len(active) >= self.concurrency:
                    self.adapter.dropped += 1
                    continue
                index = len(self.results) + len(active)
                task = asyncio.create_task(self._probe(index, event, transport))
                active.add(task)
                task.add_done_callback(active.discard)
            if active:
                await asyncio.gather(*active)
        await producer
        replay = replay_journal(self.harness.journal.path)
        summary = self._summary(replay)
        self.output.mkdir(parents=True, exist_ok=True)
        (self.output / "public_stream_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        self._write_correlations(self.output / "event_correlations.csv")
        return summary

    def _complete_waiters(self, event: PublicEvent) -> None:
        remaining = []
        for submitted_ns, future in self.waiters.get(event.token_id, []):
            if not future.done() and event.received_monotonic_ns >= submitted_ns:
                future.set_result(event.received_monotonic_ns)
            else:
                remaining.append((submitted_ns, future))
        self.waiters[event.token_id] = remaining

    async def _probe(self, index: int, event: PublicEvent, transport: LoopbackTransport) -> None:
        transition: asyncio.Future[int] = asyncio.get_running_loop().create_future()

        async def submitted(timestamp_ns: int) -> None:
            self.waiters.setdefault(event.token_id, []).append((timestamp_ns, transition))

        result = await self.harness.run_attempt(
            index,
            transport,
            source_metadata={
                "asset": event.asset,
                "event_type": event.event_type,
                "payload_hash": event.payload_hash,
                "server_timestamp_ms": event.server_timestamp_ms,
                "source": "public_clob_websocket",
            },
            on_submitted=submitted,
        )
        try:
            transition_ns = await asyncio.wait_for(asyncio.shield(transition), timeout=2.0)
        except asyncio.TimeoutError:
            transition_ns = None
        correlation = hashlib.sha256(f"dry-run-v1:{index}".encode()).hexdigest()
        self.results.append(CorrelationResult(
            correlation_id=correlation,
            asset=event.asset,
            event_type=event.event_type,
            event_age_ms=event_age_ms(event),
            source_to_signal_ms=(result.signal_monotonic_ns - event.received_monotonic_ns) / 1_000_000,
            signal_to_local_ack_ms=result.signal_to_ack_ms,
            signal_to_public_transition_ms=(transition_ns - result.signal_monotonic_ns) / 1_000_000 if transition_ns else None,
            signal_to_terminal_ms=result.signal_to_terminal_ms,
            public_transition_observed=transition_ns is not None,
            outcome=result.outcome,
        ))

    def _summary(self, replay: dict[str, Any]) -> dict[str, Any]:
        def values(name: str) -> list[float]:
            return [float(getattr(row, name)) for row in self.results if getattr(row, name) is not None]
        metrics = {name: _stats(values(name)) for name in (
            "event_age_ms", "source_to_signal_ms", "signal_to_local_ack_ms",
            "signal_to_public_transition_ms", "signal_to_terminal_ms",
        )}
        transitions = sum(row.public_transition_observed for row in self.results)
        return {
            "attempts": len(self.results),
            "assets": {asset: sum(row.asset == asset for row in self.results) for asset in ("BTC", "ETH", "SOL")},
            "metrics": metrics,
            "public_stream": {
                "received": self.adapter.received,
                "stale": self.adapter.stale,
                "duplicates": self.adapter.duplicates,
                "dropped_or_backpressured": self.adapter.dropped,
                "reconnects": self.adapter.reconnects,
                "event_gap_ms": _stats(self.adapter.event_gaps_ms),
                "transition_observed": transitions,
                "transition_missing": len(self.results) - transitions,
            },
            "admission_gates": {
                "local_signal_to_ack_p95_le_750ms": metrics["signal_to_local_ack_ms"]["p95"] <= 750,
                "public_transition_p95_le_1000ms": metrics["signal_to_public_transition_ms"]["p95"] <= 1000,
                "local_terminal_p95_le_1500ms": metrics["signal_to_terminal_ms"]["p95"] <= 1500,
                "authenticated_exchange_admission": "NOT_EVALUATED",
            },
            "replay": replay,
            "credentials_used": False,
            "orders_submitted": 0,
            "network_destinations": ["public_clob_websocket", "127.0.0.1_local_sink"],
            "result": "PUBLIC_TO_LOCAL_PATH_MEASURED_AUTHENTICATED_EXCHANGE_NOT_MEASURED",
        }

    def _write_correlations(self, path: Path) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(asdict(self.results[0])) if self.results else [])
            writer.writeheader()
            writer.writerows(asdict(row) for row in sorted(self.results, key=lambda row: row.correlation_id))


def event_age_ms(event: PublicEvent) -> float | None:
    if event.server_timestamp_ms is None:
        return None
    return event.received_wall_ns / 1_000_000 - event.server_timestamp_ms


class ClobPublicSource:
    def __init__(self, token_assets: dict[str, str], duration_seconds: float, adapter: PublicStreamAdapter) -> None:
        self.token_assets = token_assets
        self.duration_seconds = duration_seconds
        self.adapter = adapter

    async def events(self) -> AsyncIterator[PublicEvent]:
        deadline = time.monotonic() + self.duration_seconds
        while time.monotonic() < deadline:
            try:
                async with connect(CLOB_WS, ping_interval=10, ping_timeout=10) as websocket:
                    await websocket.send(json.dumps({
                        "assets_ids": list(self.token_assets), "type": "market", "custom_feature_enabled": True,
                    }))
                    while time.monotonic() < deadline:
                        raw = await asyncio.wait_for(websocket.recv(), timeout=min(15, max(0.1, deadline - time.monotonic())))
                        wall, monotonic = time.time_ns(), time.perf_counter_ns()
                        payload = json.loads(raw)
                        for message in payload if isinstance(payload, list) else [payload]:
                            token = str(message.get("asset_id") or "")
                            if not token and message.get("price_changes"):
                                token = str(message["price_changes"][0].get("asset_id") or "")
                            asset = self.token_assets.get(token)
                            if asset is None:
                                continue
                            yield PublicEvent(
                                token_id=token,
                                asset=asset,
                                event_type=str(message.get("event_type") or "unknown"),
                                server_timestamp_ms=_timestamp_ms(message.get("timestamp")),
                                received_wall_ns=wall,
                                received_monotonic_ns=monotonic,
                                payload_hash=hashlib.sha256(raw.encode()).hexdigest(),
                            )
            except (TimeoutError, OSError, asyncio.TimeoutError):
                self.adapter.reconnects += 1
                await asyncio.sleep(0.25)


async def run_live(duration_seconds: float, max_attempts: int, output: Path) -> dict[str, Any]:
    markets, _ = await asyncio.to_thread(PolymarketMarketDiscovery(5.0).discover, ("BTC", "ETH", "SOL"))
    selected: dict[str, Any] = {}
    for market in markets:
        selected.setdefault(market.asset, market)
    if set(selected) != {"BTC", "ETH", "SOL"}:
        raise RuntimeError("current BTC/ETH/SOL markets were not all discovered")
    token_assets = {market.yes_token_id: asset for asset, market in selected.items()}
    runner = PublicStreamDryRun(output, max_attempts=max_attempts)
    source = ClobPublicSource(token_assets, duration_seconds, runner.adapter)
    summary = await runner.run(source.events())
    summary["markets"] = {asset: market.market_id for asset, market in selected.items()}
    (output / "public_stream_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bounded public-stream to local latency dry run")
    parser.add_argument("--duration", type=float, default=90.0)
    parser.add_argument("--max-attempts", type=int, default=60)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not 10 <= args.duration <= 300 or not 1 <= args.max_attempts <= 200:
        raise ValueError("duration must be 10-300 seconds and attempts 1-200")
    summary = asyncio.run(run_live(args.duration, args.max_attempts, args.output))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
