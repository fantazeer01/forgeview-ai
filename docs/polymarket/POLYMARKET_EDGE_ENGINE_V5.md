# Polymarket Edge Engine v5 — Long Shadow Capture and Edge Evidence

## Purpose

v5 observes rotating BTC, ETH, and SOL five-minute UP/DOWN markets over long
periods. It reuses v4 public discovery, external reference prices, CLOB quotes,
lag detection, and the v3 shadow adapter. Its job is evidence collection, not
profit optimization.

There is no wallet, private key, authenticated trading client, or order method.

## Commands

From `D:\ForgeViewAI`:

```powershell
python -m polymarket.edge_engine_v5 capture --duration 3600
python -m polymarket.edge_engine_v5 capture --duration 21600
python -m polymarket.edge_engine_v5 capture --assets BTC ETH SOL --duration 3600
python -m polymarket.edge_engine_v5 replay --session polymarket/runs/v5/latest/session.jsonl
python -m polymarket.edge_engine_v5 inspect --session polymarket/runs/v5/latest/session.jsonl
python -m polymarket.edge_engine_v5 live --assets BTC ETH SOL --poll-interval 5
python -m polymarket.edge_engine_v5 lifecycle --assets BTC ETH SOL --duration 600 --poll-interval 1
```

Fast deterministic evidence run:

```powershell
python -m polymarket.edge_engine_v5 capture \
  --mock \
  --duration 1800 \
  --poll-interval 60 \
  --discovery-interval 60
```

## Live terminal mode

Live mode runs the normal v5 evidence capture and prints each active market's
current analysis:

```powershell
python -m polymarket.edge_engine_v5 live \
  --assets BTC ETH SOL \
  --poll-interval 5
```

Useful options:

```powershell
--duration 3600
--min-confidence 0.70
--min-entry-seconds 60
--show-skipped
--quiet
--mock
```

`--quiet` suppresses market blocks but still writes the complete timestamped
session and evidence report. `--show-skipped` includes liquidity, expiry,
missing-reference, and quote-error cases.

Example:

```text
[12:41:05] BTC 5m
Lifecycle: newly_opened
Detected after open: 5.0s
Window: EARLY
Market: Bitcoin Up or Down - 5m
Time left: 04:55 | Expiry: 12:45:00 UTC
External price: 60,100.0000
External: UP +0.080%
Polymarket YES: 0.430 | NO: 0.570 | Move: -0.020
Lag score: 0.740 | Confidence: 68.0%
Action: BUY YES (shadow)
Reason: BTC moved up, Polymarket has not fully repriced
```

Actions are display-only:

- `BUY YES` / `BUY NO`: first qualified shadow opportunity for that market;
- `HOLD`: weak move, already repriced, low confidence, or existing shadow signal;
- `SKIP`: low liquidity, expiry risk, quote failure, or missing data.

No real order is created.

## Market lifecycle tracking

Live mode rediscovers markets every five seconds by default and selects the
newest active five-minute window for each asset. Baselines are scoped to a
market ID and removed at rollover, so a new window cannot inherit price or
probability history from the prior market.

Lifecycle states:

- `waiting_for_next_window`
- `newly_opened`
- `active`
- `near_expiry`
- `closed`
- `quote_unavailable`

The default entry guard forces `SKIP` whenever less than 60 seconds remain,
even when the lag detector otherwise qualifies a BUY. The market remains
visible in the terminal so late-entry bias is explicit.

Quote failures do not terminate capture. The market is marked
`quote_unavailable`, the reason is stored, and the quote is retried on the next
poll. Repeated failures increment diagnostics without repeating the same
console warning every poll.

Lifecycle-only diagnostics:

```powershell
python -m polymarket.edge_engine_v5 lifecycle \
  --assets BTC ETH SOL \
  --duration 600 \
  --poll-interval 1
```

Example:

```text
[17:45:06] BTC 5m
Lifecycle: newly_opened
Detected after open: 6.0s
Time left: 04:54
Window: EARLY | Quote: available
Market: Bitcoin Up or Down - June 19, 1:45PM-1:50PM ET
```

## Market rotation

At each discovery interval, v5 requests current and next five-minute markets,
deduplicates by market ID, and records lifecycle transitions:

- `waiting_for_next_window`
- `newly_opened`
- `active`
- `near_expiry`
- `closed`
- `quote_unavailable`

Completed-window metrics count only closed markets with at least one usable
Polymarket snapshot.

## Session evidence

Every capture writes an append-only `session.jsonl`. Events include:

- session configuration and completion counters;
- market discovery and lifecycle transitions;
- external reference prices;
- Polymarket YES/NO snapshots;
- lag measurements;
- opportunities and skipped reasons;
- v3 shadow decisions and closed trades.

Replay recomputes lag decisions and shadow trades from market, reference, and
snapshot events. It does not trust the prior report.

Interrupted legacy sessions without a final completion event reconstruct
coverage and data-gap counters from saved reference/snapshot/skip events.
Modern captures write a checkpoint every polling cycle.

To prevent persistent lag from becoming thousands of duplicate signals, v5
permits at most one opportunity per market window. A change between Binance,
Coinbase, or mock reference sources resets that market's baseline instead of
being interpreted as a price move. Shadow timeouts scale to approximately one
minute rather than a fixed four updates.

## Session inspection

The inspect command reports event counts, time range, market/reference/snapshot
counts, timestamp alignment, missing completion/checkpoint metadata, mixed
reference sources, likely cause, and recommended repair:

```powershell
python -m polymarket.edge_engine_v5 inspect \
  --session polymarket/runs/v5/latest/session.jsonl
```

## Storage

Each capture is stored at:

```text
polymarket/runs/v5/YYYYMMDD_HHMMSS/
```

The completed capture is also copied to:

```text
polymarket/runs/v5/latest/
```

Artifacts:

```text
session.jsonl
markets.csv
opportunities.csv
trades.csv
skipped_markets.csv
evidence_report.json
report.md
lifecycle_events.csv
lifecycle_summary.json
```

Lifecycle summary fields include markets detected, average detection delay,
markets caught within 15 seconds, markets caught after 60 seconds, quote error
count, and rollover count.

## Metrics

- markets observed and completed windows;
- opportunity count and rate;
- shadow trades, P&L, win rate, average win/loss;
- maximum drawdown;
- early-versus-late edge decay;
- one-poll adverse latency/slippage sensitivity;
- reference coverage;
- market-data gap percentage.

## Conservative verdict policy

Default evidence minimums:

- at least 30 completed market windows;
- at least 20 closed shadow trades;
- reference coverage of at least 95%;
- data gaps no greater than 10%.

If any minimum is missing, the verdict is `INSUFFICIENT_DATA`.

`NO_EDGE` is returned for non-positive P&L, win rate below 45%, severe
drawdown, or severe edge decay.

`POTENTIAL_EDGE` additionally requires:

- positive P&L after configured shadow slippage;
- win rate at least 50%;
- maximum drawdown no greater than 5%;
- edge decay no greater than 50%;
- latency sensitivity no greater than 50%.

Evidence that clears minimum sample requirements but misses one of those
quality controls is `WEAK_EDGE`.

A public capture that falls back to mock data is always capped at
`INSUFFICIENT_DATA`.

## Limitations

- REST polling can miss sub-second opportunities.
- Exchange spot prices may differ from a market's formal resolution source.
- Shadow fills do not model full order-book depth or market impact.
- Statistical confidence intervals and multiple-testing corrections are not
  yet included.
