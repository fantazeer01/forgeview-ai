# Wallet Market Outcome Resolution Sprint v1

Status: Complete
Generated: 2026-06-25T22:17:45+00:00

This is a public read-only Wallet Intelligence research artifact. It is not a trading signal, not a copy-trading recommendation, and not a wallet ranking.

## Evidence

- Lifecycle positions evaluated: 2135
- Unique conditions evaluated: 1122
- Join success rate: 99.95%
- Automatic resolved outcome rate: 99.39%
- Resolved market conditions: 1112
- Unresolved market conditions: 9
- Ambiguous joins: 0
- Failed joins: 1
- Conflicting metadata rows: 0

## Lifecycle Resolution Status Counts

- `insufficient_evidence`: 1
- `matched_outcome`: 1116
- `unmatched_outcome`: 1006
- `unresolved_market`: 12

## Join Confidence Counts

- `high`: 2122
- `low`: 1
- `medium`: 12

## Research Answers

1. Lifecycle positions can be linked to public market metadata reliably: False.
2. Automatic metadata join success is 99.95%.
3. Biggest blocker: `gamma_markets_token_missing;clob_markets_condition_missing`.
4. Remaining ambiguity needs complete wallet history, settlement/redemption provenance for ambiguous cases, and timestamp-semantics review.
5. Outcome-aware Wallet Intelligence is technically feasible: True.

## Safety Boundary

The sprint classifies only matched outcome, unmatched outcome, unresolved market, or insufficient evidence. It does not compute value, performance, or execution quality.

## Recommended Next Sprint

`Wallet Outcome-Aware Metrics Sprint v1`
