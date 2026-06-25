# Project Status

Updated: 2026-06-18

## Evidence Summary

| Layer | Status | Interpretation |
| --- | --- | --- |
| Predictive edge | YES | Model D beat raw market probability out of sample in the v3 study. |
| Simulated profit edge | YES | v4/v5 simulations produced positive results under modeled execution costs. |
| Real ask edge | NOT CONFIRMED | v6 used captured asks, but the sample was insufficient for confirmation. |

## Latest Real-Ask Validation

- Recorder rows loaded: 125
- Unique resolved markets: 9
- Best observed setup: 2 minutes, threshold 5%
- Trades in best setup: 2
- Observed ROI: +47.06%
- Net PnL: +0.32 contracts

This result is not statistically meaningful. Other tested timing buckets were
negative or produced no executable signals.

## Current Blocker

At least 30 real-ask trades are required before an edge can be considered
provisionally confirmed. A sample of 100 or more resolved trades is preferred.

The exact v3 snapshot scaler datasets were also unavailable during v6, so v6
used the archived v1 feature distribution with frozen v3 coefficients.

## Recorder Status

The recorder refreshes the exact current BTC 5m slug each loop, preserves a
still-active market during transient API failures, and switches after expiry.
It retries transient URL, SSL, and timeout failures with exponential backoff.

A live rollover test on 2026-06-18 captured 36 consecutive complete rows and
switched from `btc-updown-5m-1781800200` to
`btc-updown-5m-1781800500` immediately after expiry.

## Safety Boundary

Do not trade. Do not connect a wallet. Keep all work research-only until
real-ask validation confirms a robust edge with sufficient sample size.
