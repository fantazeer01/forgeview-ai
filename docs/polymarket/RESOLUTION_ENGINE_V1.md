# Polymarket Resolution Engine v1

## Purpose

Resolution Engine v1 retrieves authoritative outcomes for completed BTC, ETH,
and SOL five-minute markets from Polymarket's public Gamma event data. It
matches the saved condition ID, accepts only explicit closed and resolved
binary `Up`/`Down` markets, stores raw evidence, and reconciles the result with
the Feature Engine's former external-reference proxy label.

It is public-data research tooling. It has no wallet, private key,
authentication, order placement, or trading capability.

## Commands

Fetch and reconcile public resolution data:

```powershell
python -m polymarket.resolution_engine reconcile
```

Deterministically replay the saved Gamma responses:

```powershell
python -m polymarket.resolution_engine replay
```

Build the authoritative-only feature dataset:

```powershell
python -m polymarket.feature_engine build
```

Proxy fallback is disabled by default. It can be enabled only explicitly for
pipeline development:

```powershell
python -m polymarket.feature_engine build --allow-proxy-labels
```

## Acceptance rules

A market is labelled only when:

- the event contains exactly one market matching the saved condition ID;
- the market is closed;
- `umaResolutionStatus` is `resolved` or the market is explicitly marked
  automatically resolved;
- outcomes are exactly `Up` and `Down`;
- terminal outcome prices are `[1, 0]` or `[0, 1]` within a 0.001 tolerance.

Unresolved, missing, cancelled, malformed, non-binary, and non-terminal markets
remain unlabelled and are reported. A proxy disagreement is preserved in the
reconciliation report; it is never silently overwritten.

## Artifacts

Stored under `polymarket/data/resolutions/`:

```text
raw_gamma_events.jsonl
resolutions.jsonl
reconciliation_report.json
```

The raw file makes replay independent of future API changes. Each normalized
record stores market ID, asset, question, slug, outcome, resolution timestamp,
resolution source, retrieval timestamp, status, and rejection reason.

Reconciliation regenerates a dedicated proxy-only reference dataset beneath
`polymarket/data/resolutions/proxy_reference_dataset/`. It never compares
authoritative labels against the main dataset after that dataset has been
rebuilt.

## Initial measured result

Run on June 19, 2026:

- discovered public markets in the current session archive: 120;
- authoritative resolutions: 105;
- authoritative coverage in the saved fixture: 87.50%;
- proxy-comparable markets: 65;
- proxy matches: 66;
- proxy mismatches: 9;
- proxy agreement: 88.00%;
- unresolved: 8;
- missing: 1.

The authoritative-only Feature Engine build produced 91 completed public rows:
30 BTC, 31 ETH, and 30 SOL.

## Limitations

- Gamma is a public API and may be temporarily unavailable.
- A resolved market can lack sufficient saved feature observations and
  therefore not produce a training row.
- Gamma outcome status is authoritative for Polymarket settlement, but the raw
  Chainlink observation values are not independently archived by this module.
