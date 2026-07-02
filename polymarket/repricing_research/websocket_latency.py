from __future__ import annotations

import argparse
import asyncio
import csv
import json
import math
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from websockets.asyncio.client import connect

from polymarket.edge_engine_v4.market_discovery import PolymarketMarketDiscovery


CLOB_WS = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
BINANCE_WS = (
    "wss://data-stream.binance.vision/stream?streams="
    "btcusdt@aggTrade/ethusdt@aggTrade/solusdt@aggTrade"
)
CLOB_BOOK = "https://clob.polymarket.com/book"


@dataclass(frozen=True)
class LatencyRecord:
    source: str
    event_type: str
    asset: str
    server_timestamp_ms: int | None
    receive_timestamp_ns: int
    processing_timestamp_ns: int
    decision_timestamp_ns: int
    serialization_complete_ns: int
    journal_complete_ns: int
    network_latency_ms: float | None
    queue_latency_ms: float
    parse_latency_ms: float
    decision_latency_ms: float
    serialization_latency_ms: float
    journal_latency_ms: float
    event_loop_latency_ms: float
    quote_age_ms: float | None
    inter_message_gap_ms: float | None
    stale_quote: bool
    sequence_gap: int


class LatencyRecorder:
    def __init__(self, raw_path: Path, stale_after_ms: float = 2_000.0) -> None:
        self.raw_path = raw_path
        self.raw_path.parent.mkdir(parents=True, exist_ok=True)
        self.stale_after_ms = stale_after_ms
        self.records: list[LatencyRecord] = []
        self.last_receive_ns: dict[str, int] = {}
        self.last_sequence: dict[str, int] = {}

    def record(
        self,
        *,
        source: str,
        event_type: str,
        asset: str,
        raw: str,
        received_wall_ns: int,
        received_perf_ns: int,
        processing_perf_ns: int,
        server_timestamp_ms: int | None,
        sequence: int | None = None,
    ) -> LatencyRecord:
        parsed_at = time.perf_counter_ns()
        _decision_probe(raw)
        decision_at = time.perf_counter_ns()
        previous_receive = self.last_receive_ns.get(source)
        inter_message = (
            (received_wall_ns - previous_receive) / 1_000_000.0
            if previous_receive is not None else None
        )
        self.last_receive_ns[source] = received_wall_ns
        sequence_gap = 0
        sequence_key = f"{source}:{asset}"
        if sequence is not None:
            previous_sequence = self.last_sequence.get(sequence_key)
            if previous_sequence is not None and sequence > previous_sequence + 1:
                sequence_gap = sequence - previous_sequence - 1
            self.last_sequence[sequence_key] = sequence
        network_latency = (
            received_wall_ns / 1_000_000.0 - server_timestamp_ms
            if server_timestamp_ms is not None else None
        )
        serialized = {
            "source": source,
            "event_type": event_type,
            "asset": asset,
            "server_timestamp_ms": server_timestamp_ms,
            "receive_timestamp_ns": received_wall_ns,
        }
        encoded = json.dumps(serialized, sort_keys=True, separators=(",", ":"))
        serialization_at = time.perf_counter_ns()
        with self.raw_path.open("a", encoding="utf-8") as handle:
            handle.write(encoded + "\n")
            handle.flush()
        journal_at = time.perf_counter_ns()
        quote_age = network_latency
        record = LatencyRecord(
            source=source,
            event_type=event_type,
            asset=asset,
            server_timestamp_ms=server_timestamp_ms,
            receive_timestamp_ns=received_wall_ns,
            processing_timestamp_ns=received_wall_ns + (processing_perf_ns - received_perf_ns),
            decision_timestamp_ns=received_wall_ns + (decision_at - received_perf_ns),
            serialization_complete_ns=received_wall_ns + (serialization_at - received_perf_ns),
            journal_complete_ns=received_wall_ns + (journal_at - received_perf_ns),
            network_latency_ms=network_latency,
            queue_latency_ms=(processing_perf_ns - received_perf_ns) / 1_000_000.0,
            parse_latency_ms=(parsed_at - processing_perf_ns) / 1_000_000.0,
            decision_latency_ms=(decision_at - parsed_at) / 1_000_000.0,
            serialization_latency_ms=(serialization_at - decision_at) / 1_000_000.0,
            journal_latency_ms=(journal_at - serialization_at) / 1_000_000.0,
            event_loop_latency_ms=(processing_perf_ns - received_perf_ns) / 1_000_000.0,
            quote_age_ms=quote_age,
            inter_message_gap_ms=inter_message,
            stale_quote=quote_age is not None and quote_age > self.stale_after_ms,
            sequence_gap=sequence_gap,
        )
        self.records.append(record)
        return record


async def run_bounded(duration_seconds: float, output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    raw_path = output / "latency_journal.jsonl"
    raw_path.write_text("", encoding="utf-8")
    recorder = LatencyRecorder(raw_path)
    markets, _ = await asyncio.to_thread(
        PolymarketMarketDiscovery(5.0).discover,
        ("BTC", "ETH", "SOL"),
    )
    selected = {}
    for market in markets:
        selected.setdefault(market.asset, market)
    if set(selected) != {"BTC", "ETH", "SOL"}:
        raise RuntimeError("current BTC/ETH/SOL markets were not all discovered")
    token_assets = {market.yes_token_id: asset for asset, market in selected.items()}
    deadline = time.monotonic() + duration_seconds
    counters = {
        "clob_reconnects": 0,
        "binance_reconnects": 0,
        "clob_messages_without_sequence": 0,
        "poll_errors": 0,
    }
    await asyncio.gather(
        _clob_observer(token_assets, recorder, counters, deadline),
        _binance_observer(recorder, counters, deadline),
        _polling_observer(token_assets, recorder, counters, deadline),
    )
    _write_records(output / "latency_records.csv", recorder.records)
    summary = summarize_records(recorder.records)
    summary.update({
        "duration_seconds": duration_seconds,
        "markets": {asset: market.market_id for asset, market in selected.items()},
        "counters": counters,
        "clock_assumption": "server and local UTC clocks are comparable; no NTP offset correction was available",
        "clob_packet_loss": "not_measurable_no_sequence_number",
        "binance_sequence_gap": "aggregate-trade ID gaps are diagnostic, not proof of packet loss",
        "authentication_used": False,
        "orders_submitted": 0,
    })
    (output / "latency_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


async def _clob_observer(token_assets, recorder, counters, deadline) -> None:
    while time.monotonic() < deadline:
        try:
            async with connect(CLOB_WS, ping_interval=10, ping_timeout=10) as websocket:
                await websocket.send(json.dumps({
                    "assets_ids": list(token_assets),
                    "type": "market",
                    "custom_feature_enabled": True,
                }))
                while time.monotonic() < deadline:
                    raw = await asyncio.wait_for(websocket.recv(), timeout=min(15, max(0.1, deadline - time.monotonic())))
                    received_wall = time.time_ns()
                    received_perf = time.perf_counter_ns()
                    processing = time.perf_counter_ns()
                    payload = json.loads(raw)
                    messages = payload if isinstance(payload, list) else [payload]
                    for message in messages:
                        token = str(message.get("asset_id") or "")
                        timestamp = _timestamp_ms(message.get("timestamp"))
                        recorder.record(
                            source="clob_websocket", event_type=str(message.get("event_type") or "unknown"),
                            asset=token_assets.get(token, "UNKNOWN"), raw=raw,
                            received_wall_ns=received_wall, received_perf_ns=received_perf,
                            processing_perf_ns=processing, server_timestamp_ms=timestamp,
                        )
                        counters["clob_messages_without_sequence"] += 1
        except (TimeoutError, OSError, asyncio.TimeoutError):
            counters["clob_reconnects"] += 1
            await asyncio.sleep(0.25)


async def _binance_observer(recorder, counters, deadline) -> None:
    while time.monotonic() < deadline:
        try:
            async with connect(BINANCE_WS, ping_interval=10, ping_timeout=10) as websocket:
                while time.monotonic() < deadline:
                    raw = await asyncio.wait_for(websocket.recv(), timeout=min(15, max(0.1, deadline - time.monotonic())))
                    received_wall = time.time_ns()
                    received_perf = time.perf_counter_ns()
                    processing = time.perf_counter_ns()
                    envelope = json.loads(raw)
                    message = envelope.get("data", envelope)
                    symbol = str(message.get("s") or "")
                    recorder.record(
                        source="binance_websocket", event_type=str(message.get("e") or "aggTrade"),
                        asset=symbol.replace("USDT", ""), raw=raw,
                        received_wall_ns=received_wall, received_perf_ns=received_perf,
                        processing_perf_ns=processing,
                        server_timestamp_ms=_timestamp_ms(message.get("E") or message.get("T")),
                        sequence=int(message["a"]) if "a" in message else None,
                    )
        except (TimeoutError, OSError, asyncio.TimeoutError):
            counters["binance_reconnects"] += 1
            await asyncio.sleep(0.25)


async def _polling_observer(token_assets, recorder, counters, deadline) -> None:
    while time.monotonic() < deadline:
        started = time.monotonic()
        for token, asset in token_assets.items():
            try:
                raw, received_wall, received_perf = await asyncio.to_thread(_fetch_book, token)
                processing = time.perf_counter_ns()
                message = json.loads(raw)
                recorder.record(
                    source="clob_polling", event_type="book", asset=asset, raw=raw,
                    received_wall_ns=received_wall, received_perf_ns=received_perf,
                    processing_perf_ns=processing,
                    server_timestamp_ms=_timestamp_ms(message.get("timestamp")),
                )
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                counters["poll_errors"] += 1
        await asyncio.sleep(max(0.0, 2.0 - (time.monotonic() - started)))


def _fetch_book(token: str) -> tuple[str, int, int]:
    query = urllib.parse.urlencode({"token_id": token})
    request = urllib.request.Request(
        f"{CLOB_BOOK}?{query}", headers={"User-Agent": "forgeview-latency-instrument/1.0"}
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        raw = response.read().decode("utf-8")
    return raw, time.time_ns(), time.perf_counter_ns()


def summarize_records(records: list[LatencyRecord]) -> dict[str, Any]:
    output = {"total_records": len(records), "sources": {}}
    for source in sorted({record.source for record in records}):
        selected = [record for record in records if record.source == source]
        metrics = {}
        for field in (
            "network_latency_ms", "queue_latency_ms", "parse_latency_ms",
            "decision_latency_ms", "serialization_latency_ms", "journal_latency_ms",
            "event_loop_latency_ms", "quote_age_ms", "inter_message_gap_ms",
        ):
            values = [float(getattr(record, field)) for record in selected if getattr(record, field) is not None and math.isfinite(float(getattr(record, field)))]
            metrics[field] = _distribution(values)
        output["sources"][source] = {
            "records": len(selected),
            "stale_quotes": sum(record.stale_quote for record in selected),
            "sequence_gaps": sum(record.sequence_gap for record in selected),
            "metrics": metrics,
        }
    return output


def _distribution(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {key: None for key in ("count", "min", "mean", "median", "p90", "p95", "p99", "max")}
    ordered = sorted(values)
    def percentile(value: float) -> float:
        return ordered[min(len(ordered) - 1, max(0, math.ceil(value * len(ordered)) - 1))]
    return {
        "count": len(ordered), "min": ordered[0], "mean": sum(ordered) / len(ordered),
        "median": percentile(0.5), "p90": percentile(0.9), "p95": percentile(0.95),
        "p99": percentile(0.99), "max": ordered[-1],
    }


def _timestamp_ms(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return None
    return number * 1_000 if number < 10_000_000_000 else number


def _decision_probe(raw: str) -> int:
    # Side-effect-free deterministic work representative of the frozen scalar detector.
    seed = len(raw)
    return ((seed * 31) ^ (seed >> 2)) & 0xFFFFFFFF


def _write_records(path: Path, records: list[LatencyRecord]) -> None:
    fields = list(asdict(records[0])) if records else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bounded public WebSocket latency instrumentation")
    parser.add_argument("--duration", type=float, default=120.0)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not 1 <= args.duration <= 900:
        raise ValueError("duration must be between 1 and 900 seconds")
    summary = asyncio.run(run_bounded(args.duration, args.output))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
