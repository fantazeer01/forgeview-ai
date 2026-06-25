# Market Microstructure Feature Capture v1

Status: Implemented  
Date: June 23, 2026

## Purpose

Capture information that can distinguish a genuinely stale Polymarket quote
from a market already repricing internally. This milestone adds data and
features only. It does not train a model, evaluate the holdout, launch a
campaign, or implement trading.

## Storage schema

Every successful v5 quote now produces:

1. the backward-compatible `polymarket_snapshot` event;
2. a schema-versioned `microstructure_snapshot` event.

The machine-readable schema is
`polymarket/data/microstructure/schema_v1.json`.

Raw public fields come from Polymarket's unauthenticated CLOB `/book`
endpoint. Missing source fields remain null.

## Feature definitions

| Feature | Definition |
|---|---|
| Quote age | Observation UTC minus CLOB quote timestamp |
| Repricing velocity | YES midpoint change divided by elapsed seconds |
| Repricing acceleration | Change in repricing velocity per second |
| YES/NO change frequency | Quote midpoint changes during the trailing 30 seconds divided by 30 |
| Spread | Best YES ask minus best YES bid |
| Spread change | Current spread minus previous spread |
| Spread velocity | Spread change divided by elapsed seconds |
| Spread compression | Negative spread change; positive means narrowing |
| Time since quote update | Seconds since any price/spread/depth fingerprint changed |
| Quote stability | Consecutive observations with an unchanged fingerprint |
| Top sizes | Size available at best YES bid and ask |
| Total depth | Sum of visible YES bid and ask sizes |
| Book imbalance | `(bid_depth - ask_depth) / (bid_depth + ask_depth)` |
| Refresh latency | Local elapsed time for the public CLOB request |
| Cross-asset dispersion | Max minus min synchronized BTC/ETH/SOL YES midpoint |
| Cross-asset relative YES | Asset YES midpoint minus synchronized asset mean |

Signed order flow is represented only by a public-data proxy: changes in book
imbalance and quote fingerprints. No private trade feed is assumed.

## Feature Engine

Feature Engine exports 19 optional microstructure columns. It selects only the
latest `microstructure_snapshot` at or before the feature timestamp and rejects
events older than the existing 15-second as-of limit. Future events are never
eligible.

Legacy sessions remain valid. Their new columns are null and are reported
separately from core-feature completeness, so historical quality gates and the
frozen validation protocol are unchanged.

## Replay compatibility

v5 replay ignores the additive microstructure event when reproducing legacy
shadow decisions. Feature replay consumes the event deterministically.
Capture/replay parity and future-event rejection are covered by tests.

## Coverage

Deterministic 30-observation fixture:

- raw quote/depth, quote age, latency, and imbalance: 100%;
- repricing velocity: 90% after one-observation warm-up;
- repricing acceleration: 80% after two-observation warm-up;
- synchronized cross-asset dispersion: 96.67%.

Historical public sessions have 0% microstructure coverage because they
predate schema v1. Real public schema-v1 coverage is not yet measured because
this task prohibited launching a campaign or live smoke run.

## Expected information value

Potentially highest:

- repricing velocity and acceleration;
- quote age and refresh staleness;
- book imbalance and depth changes;
- spread compression during external impulses.

Potentially moderate:

- cross-asset synchronization and relative probability;
- quote-change frequency and stability.

These are hypotheses, not alpha evidence. A separately authorized public smoke
validation must establish actual endpoint coverage before any collection
campaign or model experiment.

## Future public command

After the active successor task validates real endpoint coverage, a future
independent development capture may use the existing evidence command. It must
not overwrite or reopen the frozen holdout.
