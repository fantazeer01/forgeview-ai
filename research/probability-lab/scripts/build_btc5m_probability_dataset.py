import csv
import json
import math
import ssl
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "polymarket_btc5m_probability_lab_v1.csv"
REPORT = ROOT / "data" / "polymarket_btc5m_probability_lab_v1_report.json"

# Recent resolved window. Keep this modest to avoid hammering public endpoints.
START_TS = int(datetime(2026, 6, 14, tzinfo=timezone.utc).timestamp())
END_TS = int(datetime(2026, 6, 17, tzinfo=timezone.utc).timestamp())
SNAPSHOT_SECONDS_BEFORE_RESOLUTION = 60

CTX = ssl.create_default_context()


def http_json(url, timeout=35, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json",
                    "Connection": "close",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as exc:
            last = exc
            time.sleep(0.3 * (i + 1))
    raise last


def fetch_market(start_ts):
    slug = f"btc-updown-5m-{start_ts}"
    qs = urllib.parse.urlencode({"closed": "true", "limit": 1, "slug": slug})
    data = http_json(f"https://gamma-api.polymarket.com/markets?{qs}")
    rows = data if isinstance(data, list) else data.get("value") or data.get("data") or []
    if not rows:
        return None
    market = rows[0]
    if market.get("slug") != slug:
        return None
    token_ids = json.loads(market.get("clobTokenIds") or "[]")
    outcomes = json.loads(market.get("outcomes") or "[]")
    condition_id = market.get("conditionId") or market.get("condition_id")
    if len(token_ids) != 2 or len(outcomes) != 2 or not condition_id:
        return None
    return {
        "market_id": slug,
        "condition_id": condition_id,
        "open_timestamp": start_ts,
        "resolution_timestamp": start_ts + 300,
        "token_ids": [str(x) for x in token_ids],
        "outcomes": outcomes,
    }


def resolve_market(market):
    data = http_json(f"https://clob.polymarket.com/markets/{market['condition_id']}")
    tokens = data.get("tokens") or []
    winners = {str(t.get("token_id")): bool(t.get("winner")) for t in tokens}
    if not data.get("closed") or not winners:
        return None
    final_outcome = None
    for token_id, outcome in zip(market["token_ids"], market["outcomes"]):
        if winners.get(token_id):
            final_outcome = outcome
            break
    if final_outcome not in ("Up", "Down"):
        return None
    market = dict(market)
    market["final_outcome"] = final_outcome
    market["outcome"] = 1 if final_outcome == "Up" else 0
    return market


def price_history(token_id, start_ts, end_ts):
    qs = urllib.parse.urlencode({"market": token_id, "startTs": start_ts, "endTs": end_ts})
    data = http_json(f"https://clob.polymarket.com/prices-history?{qs}", tries=3)
    return data.get("history") or []


def snapshot_probability(market):
    target_ts = market["resolution_timestamp"] - SNAPSHOT_SECONDS_BEFORE_RESOLUTION
    up_token = market["token_ids"][market["outcomes"].index("Up")]
    hist = price_history(up_token, market["open_timestamp"], market["resolution_timestamp"])
    points = [
        (int(p.get("t") or 0), float(p.get("p") or 0))
        for p in hist
        if 0 < float(p.get("p") or 0) < 1
    ]
    if not points:
        return None
    # One snapshot per market: closest available point at or before target; fallback to nearest.
    before = [p for p in points if p[0] <= target_ts]
    ts, prob = max(before, key=lambda x: x[0]) if before else min(points, key=lambda x: abs(x[0] - target_ts))
    return ts, prob


def fetch_binance_klines(start_ts, end_ts):
    # Binance timestamps are milliseconds. Pull a little padding for 15m features.
    closes = {}
    cursor = (start_ts - 3600) * 1000
    end_ms = (end_ts + 300) * 1000
    while cursor < end_ms:
        qs = urllib.parse.urlencode(
            {
                "symbol": "BTCUSDT",
                "interval": "1m",
                "startTime": cursor,
                "endTime": end_ms,
                "limit": 1000,
            }
        )
        url = f"https://api.binance.com/api/v3/klines?{qs}"
        rows = http_json(url, timeout=35)
        if not rows:
            break
        for row in rows:
            open_ts = int(row[0] // 1000)
            closes[open_ts] = float(row[4])
        last_open_ms = int(rows[-1][0])
        next_cursor = last_open_ms + 60_000
        if next_cursor <= cursor:
            break
        cursor = next_cursor
        time.sleep(0.05)
    return closes


def close_at_or_before(closes, ts):
    minute_ts = ts - (ts % 60)
    for candidate in range(minute_ts, minute_ts - 600, -60):
        if candidate in closes:
            return closes[candidate]
    return None


def ret(closes, ts, minutes):
    now = close_at_or_before(closes, ts)
    then = close_at_or_before(closes, ts - minutes * 60)
    if now is None or then is None or then == 0:
        return None
    return (now / then) - 1


def realized_vol_15m(closes, ts):
    vals = []
    for i in range(15, 0, -1):
        p0 = close_at_or_before(closes, ts - i * 60)
        p1 = close_at_or_before(closes, ts - (i - 1) * 60)
        if p0 and p1 and p0 > 0:
            vals.append(math.log(p1 / p0))
    if len(vals) < 5:
        return None
    mean = sum(vals) / len(vals)
    variance = sum((x - mean) ** 2 for x in vals) / len(vals)
    return math.sqrt(variance)


def fmt(value):
    if value is None:
        return ""
    return f"{value:.10f}" if isinstance(value, float) else value


def main():
    starts = list(range(START_TS, END_TS, 300))
    print(f"Planned markets: {len(starts)}", flush=True)

    with ThreadPoolExecutor(max_workers=24) as ex:
        markets = [m for m in ex.map(fetch_market, starts) if m]
    print(f"Markets found: {len(markets)}", flush=True)

    resolved = []
    with ThreadPoolExecutor(max_workers=24) as ex:
        for future in as_completed([ex.submit(resolve_market, m) for m in markets]):
            market = future.result()
            if market:
                resolved.append(market)
    resolved.sort(key=lambda m: m["open_timestamp"])
    print(f"Markets resolved: {len(resolved)}", flush=True)

    closes = fetch_binance_klines(START_TS, END_TS)
    print(f"BTC 1m candles: {len(closes)}", flush=True)

    records = []
    missing_probability = 0
    missing_btc = 0
    snapshots = {}
    with ThreadPoolExecutor(max_workers=32) as ex:
        futures = {ex.submit(snapshot_probability, market): market for market in resolved}
        for future in as_completed(futures):
            snapshots[futures[future]["market_id"]] = future.result()

    for market in resolved:
        snap = snapshots.get(market["market_id"])
        if not snap:
            missing_probability += 1
            continue
        timestamp, probability = snap
        btc_price = close_at_or_before(closes, timestamp)
        if btc_price is None:
            missing_btc += 1
            continue
        records.append(
            {
                "market_id": market["market_id"],
                "timestamp": timestamp,
                "open_timestamp": market["open_timestamp"],
                "resolution_timestamp": market["resolution_timestamp"],
                "market_probability": probability,
                "btc_price": btc_price,
                "btc_return_1m": ret(closes, timestamp, 1),
                "btc_return_5m": ret(closes, timestamp, 5),
                "btc_return_15m": ret(closes, timestamp, 15),
                "btc_volatility_15m": realized_vol_15m(closes, timestamp),
                "final_outcome": market["final_outcome"],
                "outcome": market["outcome"],
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "market_id",
        "timestamp",
        "open_timestamp",
        "resolution_timestamp",
        "market_probability",
        "btc_price",
        "btc_return_1m",
        "btc_return_5m",
        "btc_return_15m",
        "btc_volatility_15m",
        "final_outcome",
        "outcome",
    ]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in records:
            writer.writerow({k: fmt(row[k]) for k in fields})

    report = {
        "dataset_path": str(OUT),
        "planned_markets": len(starts),
        "markets_found": len(markets),
        "markets_resolved": len(resolved),
        "dataset_size": len(records),
        "missing_probability_snapshot": missing_probability,
        "missing_btc_price": missing_btc,
        "start_utc": datetime.fromtimestamp(START_TS, timezone.utc).isoformat(),
        "end_utc": datetime.fromtimestamp(END_TS, timezone.utc).isoformat(),
        "snapshot_seconds_before_resolution": SNAPSHOT_SECONDS_BEFORE_RESOLUTION,
        "features": fields,
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
