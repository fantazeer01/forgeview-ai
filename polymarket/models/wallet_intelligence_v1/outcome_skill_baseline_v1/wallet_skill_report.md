# Wallet Outcome Skill Baseline Sprint v1

Hypothesis: H1 - Some public wallets consistently make better decisions than random.

This sprint tries to disprove H1 using currently available public evidence. It is not a trading signal, not investment advice, and not an execution-quality study.

## Observed Evidence

- Wallets evaluated: 28
- Fast crypto lifecycle positions: 1789
- Resolved positions tested: 1788
- Matched outcomes: 938
- Unmatched outcomes: 850
- Population match rate: 0.524609
- Random baseline rate: 0.500000

## Classification Counts

- `above_baseline_evidence`: 4
- `below_baseline_evidence`: 3
- `insufficient_evidence`: 8
- `sample_size_consistent_with_baseline`: 13

## Evidence Supporting H1

- 4 wallets exceeded the population baseline under the minimum sample and uncertainty gates.
- The aggregate resolved-position match rate was 0.524609 over 1788 resolved fast-crypto rows.
- Above-baseline wallets: 0x088df3b7e5c1b5c2d4b7dc760863153480cf025e, 0x1cc53dd33c49d0a222c61ebfd2f24ba48802b199, 0x29a55c2bf8efd1029c001477b34be47d3ca37752, 0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a.

## Evidence Against H1

- 3 wallets showed below-baseline evidence under the same gates.
- 13 wallets were consistent with the population baseline after sample-size adjustment.
- 8 wallets failed the minimum resolved-position sample gate.
- The wallet set is retrospectively selected and therefore exposed to selection and survivorship bias.
- The current evidence does not measure public visibility delay, actionable time remaining, fill certainty, or complete wallet history.

## Final Conclusion

INCONCLUSIVE

H1 is not disproven, but it is not convincingly supported: several wallets clear above-baseline gates, several fail in the opposite direction, and major retrospective-data invalidation risks remain.

## Recommended Next Hypothesis

H2: Wallet Activity Visibility Delay Sprint v1, but only for wallets that cleared the above-baseline H1 gates.
