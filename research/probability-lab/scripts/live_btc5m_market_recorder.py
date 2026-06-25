import argparse
import csv
import json
import math
import random
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
BINANCE = "https://api.binance.com"
COINBASE = "https://api.coinbase.com"
DEFAULT_OUT = Path(r"D:\ForgeViewAI\output\research\data\recorder\forgeview_live_btc5m_orderbook_snapshots.csv")
WORKSPACE_ROOT = Path(r"D:\ForgeViewAI")
USER_AGENT = "forgeview-research-recorder/2.0"
MARKET_SECONDS = 300

FIELDS = [
    "captured_at",
    "market_id",
    "condition_id",
    "market_start_timestamp",
    "market_resolution_timestamp",
    "seconds_to_resolution",
    "yes_token_id",
    "no_token_id",
    "best_ask_yes",
    "best_ask_no",
    "best_bid_yes",
    "best_bid_no",
    "market_probability",
    "btc_price",
    "btc_return_1m",
    "btc_return_5m",
    "btc_return_15m",
    "btc_volatility_15m",
    "source_status",
    "error",
]


def utc_now():
    return datetime.now(timezone.utc)


def log_error(component, error):
    print(f"ERROR component={component} error={error}", flush=True)


def http_json(url, timeout=5.0, retries=2, backoff=0.5, sleep=time.sleep):
    last_error = None
    for attempt in range(retries + 1):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json",
                    "Connection": "close",
                },
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (
            TimeoutError,
            ssl.SSLError,
            urllib.error.URLError,
            ConnectionError,
            OSError,
        ) as error:
            last_error = error
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code not in (408, 425, 429, 500, 502, 503, 504):
                break

        if attempt < retries:
            delay = backoff * (2**attempt) + random.uniform(0, backoff * 0.2)
            log_error("http_retry", f"attempt={attempt + 1} delay={delay:.2f}s url={url} cause={last_error!r}")
            sleep(delay)

    raise RuntimeError(f"http_json failed url={url} error={last_error!r}")


def parse_timestamp(value):
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def list_value(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


def response_rows(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("markets", "events", "data", "value"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def token_ids(market):
    ids = list_value(market.get("clobTokenIds") or market.get("clob_token_ids"))
    if len(ids) >= 2:
        return str(ids[0]), str(ids[1])
    tokens = list_value(market.get("tokens"))
    if len(tokens) >= 2 and isinstance(tokens[0], dict):
        return (
            str(tokens[0].get("token_id") or tokens[0].get("id") or ""),
            str(tokens[1].get("token_id") or tokens[1].get("id") or ""),
        )
    return "", ""


def normalize_market(market):
    if not isinstance(market, dict):
        return None
    slug = market.get("slug") or market.get("marketSlug")
    if not slug or not slug.startswith("btc-updown-5m-"):
        return None
    try:
        slug_start = int(slug.rsplit("-", 1)[-1])
    except ValueError:
        return None

    start = parse_timestamp(
        market.get("startDate")
        or market.get("startDateIso")
        or market.get("start_time")
    )
    end = parse_timestamp(
        market.get("endDate")
        or market.get("endDateIso")
        or market.get("end_time")
        or market.get("resolutionTime")
    )
    start = start or datetime.fromtimestamp(slug_start, timezone.utc)
    end = end or datetime.fromtimestamp(slug_start + MARKET_SECONDS, timezone.utc)
    yes_token, no_token = token_ids(market)
    return {
        "market_id": slug,
        "condition_id": market.get("conditionId") or market.get("condition_id") or "",
        "start": start,
        "end": end,
        "yes_token_id": yes_token,
        "no_token_id": no_token,
    }


def market_slug(timestamp):
    start = timestamp - (timestamp % MARKET_SECONDS)
    return f"btc-updown-5m-{start}"


def market_from_slug(slug):
    query = urllib.parse.urlencode({"limit": 1, "slug": slug})
    for item in response_rows(http_json(f"{GAMMA}/markets?{query}")):
        normalized = normalize_market(item)
        if normalized and normalized["market_id"] == slug:
            return normalized
    return None


def series_markets():
    query = urllib.parse.urlencode({"slug": "btc-up-or-down-5m"})
    found = []
    for series in response_rows(http_json(f"{GAMMA}/series?{query}")):
        for event in list_value(series.get("events")):
            for raw_market in list_value(event.get("markets")):
                market = normalize_market(raw_market)
                if market:
                    found.append(market)
    return found


class MarketTracker:
    def __init__(self):
        self.active = None

    def _is_active(self, market, now):
        return bool(market and market["start"] <= now < market["end"])

    def _discover_current(self, now):
        slug = market_slug(int(now.timestamp()))
        try:
            return market_from_slug(slug)
        except Exception as error:
            log_error("market_current", f"slug={slug} cause={error}")
            return None

    def _discover_fallback(self, now):
        candidates = []
        next_start = int(now.timestamp()) - (int(now.timestamp()) % MARKET_SECONDS) + MARKET_SECONDS
        try:
            next_market = market_from_slug(f"btc-updown-5m-{next_start}")
            if next_market:
                candidates.append(next_market)
        except Exception as error:
            log_error("market_next", error)
        try:
            candidates.extend(series_markets())
        except Exception as error:
            log_error("market_series", error)

        current = [market for market in candidates if self._is_active(market, now)]
        if current:
            return min(current, key=lambda market: market["end"])
        future = [market for market in candidates if market["start"] > now]
        return min(future, key=lambda market: market["start"]) if future else None

    def refresh(self, now):
        discovered = self._discover_current(now)
        if self._is_active(discovered, now):
            selected = discovered
        elif self._is_active(self.active, now):
            log_error("market_refresh", f"keeping_active={self.active['market_id']}")
            selected = self.active
        else:
            selected = self._discover_fallback(now)

        if selected and (not self.active or selected["market_id"] != self.active["market_id"]):
            old = self.active["market_id"] if self.active else ""
            print(f"MARKET_SWITCH old={old} new={selected['market_id']}", flush=True)
        self.active = selected
        return selected


def order_book(token_id):
    if not token_id:
        raise RuntimeError("missing token id")
    query = urllib.parse.urlencode({"token_id": token_id})
    return http_json(f"{CLOB}/book?{query}", timeout=4, retries=2)


def best_price(levels, highest=False):
    prices = []
    for level in levels or []:
        try:
            prices.append(float(level.get("price") if isinstance(level, dict) else level[0]))
        except (TypeError, ValueError, IndexError):
            continue
    if not prices:
        return ""
    return max(prices) if highest else min(prices)


def safe_bid_ask(side, token_id):
    try:
        book = order_book(token_id)
        return best_price(book.get("bids"), highest=True), best_price(book.get("asks")), ""
    except Exception as error:
        message = f"{side}_book={error}"
        log_error(f"{side}_book", error)
        return "", "", message


def calculate_btc_features(closes):
    price = closes[-1]

    def simple_return(minutes):
        if len(closes) <= minutes or not closes[-1 - minutes]:
            return ""
        return (price / closes[-1 - minutes]) - 1

    returns = [
        (closes[index] / closes[index - 1]) - 1
        for index in range(max(1, len(closes) - 14), len(closes))
    ]
    mean = sum(returns) / len(returns)
    volatility = math.sqrt(sum((value - mean) ** 2 for value in returns) / len(returns))
    return price, simple_return(1), simple_return(5), simple_return(15), volatility


def btc_features():
    errors = []
    try:
        query = urllib.parse.urlencode({"symbol": "BTCUSDT", "interval": "1m", "limit": 32})
        rows = http_json(f"{BINANCE}/api/v3/klines?{query}", timeout=4, retries=1)
        return (*calculate_btc_features([float(row[4]) for row in rows]), "")
    except Exception as error:
        errors.append(f"btc_binance={error}")
        log_error("btc_binance", error)

    try:
        query = urllib.parse.urlencode({"granularity": "ONE_MINUTE", "limit": 32})
        data = http_json(
            f"{COINBASE}/api/v3/brokerage/market/products/BTC-USD/candles?{query}",
            timeout=4,
            retries=1,
        )
        candles = sorted(data.get("candles", []), key=lambda candle: int(candle["start"]))
        return (*calculate_btc_features([float(candle["close"]) for candle in candles]), "; ".join(errors))
    except Exception as error:
        errors.append(f"btc_coinbase_candles={error}")
        log_error("btc_coinbase_candles", error)

    try:
        data = http_json(f"{COINBASE}/v2/prices/BTC-USD/spot", timeout=4, retries=1)
        return float(data["data"]["amount"]), "", "", "", "", "; ".join(errors)
    except Exception as error:
        errors.append(f"btc_coinbase_spot={error}")
        log_error("btc_coinbase_spot", error)
        return "", "", "", "", "", "; ".join(errors)


def empty_row(status, error):
    row = {field: "" for field in FIELDS}
    row.update(
        {
            "captured_at": utc_now().isoformat(),
            "source_status": status,
            "error": str(error)[:2000],
        }
    )
    return row


def capture_once(tracker, captured_at=None):
    captured_at = captured_at or utc_now()
    try:
        market = tracker.refresh(captured_at)
        if not market:
            return empty_row("ERROR", "no BTC 5m market found")

        seconds = max(0, int((market["end"] - captured_at).total_seconds()))
        yes_bid, yes_ask, yes_error = safe_bid_ask("yes", market["yes_token_id"])
        no_bid, no_ask, no_error = safe_bid_ask("no", market["no_token_id"])
        btc_price, return_1m, return_5m, return_15m, volatility, btc_error = btc_features()
        errors = "; ".join(error for error in (yes_error, no_error, btc_error) if error)
        probability = (yes_bid + yes_ask) / 2 if yes_bid != "" and yes_ask != "" else yes_ask or yes_bid
        return {
            "captured_at": captured_at.isoformat(),
            "market_id": market["market_id"],
            "condition_id": market["condition_id"],
            "market_start_timestamp": market["start"].isoformat(),
            "market_resolution_timestamp": market["end"].isoformat(),
            "seconds_to_resolution": seconds,
            "yes_token_id": market["yes_token_id"],
            "no_token_id": market["no_token_id"],
            "best_ask_yes": yes_ask,
            "best_ask_no": no_ask,
            "best_bid_yes": yes_bid,
            "best_bid_no": no_bid,
            "market_probability": probability,
            "btc_price": btc_price,
            "btc_return_1m": return_1m,
            "btc_return_5m": return_5m,
            "btc_return_15m": return_15m,
            "btc_volatility_15m": volatility,
            "source_status": "PARTIAL" if errors else "OK",
            "error": errors,
        }
    except Exception as error:
        log_error("capture", error)
        return empty_row("ERROR", error)


def ensure_d_drive(path):
    resolved = Path(path).resolve()
    root = WORKSPACE_ROOT.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"output must stay inside {root}, got {resolved}")
    return resolved


def append_row(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    has_header = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        if not has_header:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in FIELDS})
        handle.flush()


def main():
    parser = argparse.ArgumentParser(
        description="Research-only BTC 5m Polymarket executable-price recorder."
    )
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--samples", type=int, default=0, help="0 runs continuously")
    args = parser.parse_args()

    output = ensure_d_drive(args.out)
    tracker = MarketTracker()
    print(f"RECORDER_READY=YES output={output}", flush=True)
    iteration = 0
    while args.samples <= 0 or iteration < args.samples:
        loop_started = time.monotonic()
        iteration += 1
        row = capture_once(tracker)
        try:
            append_row(output, row)
        except Exception as error:
            log_error("csv_write", f"output={output} cause={error}")
        print(
            f"[{iteration}] {row['source_status']} market={row['market_id']} "
            f"seconds_to_resolution={row['seconds_to_resolution']} "
            f"yes_ask={row['best_ask_yes']} no_ask={row['best_ask_no']} "
            f"btc={row['btc_price']} err={row['error']}",
            flush=True,
        )
        remaining = args.interval - (time.monotonic() - loop_started)
        if remaining > 0:
            time.sleep(remaining)


if __name__ == "__main__":
    main()
