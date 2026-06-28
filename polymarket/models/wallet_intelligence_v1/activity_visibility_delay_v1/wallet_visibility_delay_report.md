# Wallet Activity Visibility Delay Sprint v1

Hypothesis: H2 - Wallet activity becomes publicly observable early enough to support future copy-trading research.

This is a retrospective public-data timing study, not a trading signal or a copy-trading recommendation.

## Observed Evidence

- Wallets analyzed: 20
- Fast-crypto trades analyzed: 3431
- Trade timestamps available: 3431
- Publication/first-seen timestamps available: 0
- Fetch timestamps available: 3431
- Unknown publication timing: 3431

## Wallet Groups

- Group A `above_baseline`: 4 wallets, 684 trades, 684 unknown publication delays
- Group B `baseline`: 13 wallets, 2228 trades, 2228 unknown publication delays
- Group C `below_baseline`: 3 wallets, 519 trades, 519 unknown publication delays

## Delay Measurement

- Minimum publication delay: unavailable
- Median publication delay: unavailable
- Mean publication delay: unavailable
- Maximum publication delay: unavailable
- Publication delay is unavailable because the source contains no publication or first-seen timestamp.
- Retrospective retrieval lag is reported separately and must not be interpreted as API latency.
- Retrieval-lag minimum / median / mean / maximum: 18.0 / 22207.0 / 778179.988925 / 11200902.0

## Visibility Comparison

not_measurable

No trade has a publication or first-seen timestamp; group retrieval-age differences reflect retrospective batch composition, not API visibility speed.

## Evidence Supporting H2

- No direct evidence supports H2 because publication or first-seen timestamps are absent.
- Trade occurrence, fetch timestamps, transaction hashes, and event ordering are complete for 3431 rows, but they support only a future prospective test.

## Evidence Against H2

- Publication or first-seen time is absent for 3431 of 3431 trades.
- The Data API activity timestamp represents the trade event, not when the API published the row.
- Source fetch timestamps came from retrospective bounded pages and cannot measure API latency.
- The cohort is selected retrospectively from H1 and remains exposed to selection and bounded-history bias.

## Final Conclusion

INCONCLUSIVE

H2 cannot be supported or rejected from retrospective activity exports because no per-trade publication or first-seen timestamp exists. The observed timestamps establish event order and retrieval age only.

## Biggest Blocker

Missing prospective first-seen timestamp for each public wallet trade.

## Recommended H3

Wallet Detection-To-Expiry Feasibility Sprint v1, using prospectively recorded first-seen times before interpreting remaining actionable time.
