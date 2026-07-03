# Recommended Roadmap

## Now

1. Freeze the Repricing credentialed-calibration sequence at
   `NOT_AUTHORIZED`; preserve all policies, preflight and remediation artifacts.
2. Run a public-only candidate review for strategies with longer actionable
   windows and lower sensitivity to sub-two-second execution.
3. Rank candidates by expected after-cost robustness, public-data feasibility,
   time-to-test and compatibility with existing capture/replay infrastructure.

## Candidate preference

Prefer hypotheses whose holding/response window is measured in minutes rather
than milliseconds or low seconds, whose entry can tolerate one to five seconds
of delay, and whose evidence can be developed without credentials. Wallet
timing/lifecycle, slower cross-market dislocations, spread/liquidity regimes and
post-event continuation/reversion are candidate families, not approved edges.

## If Repricing is resumed

Use **Option B**, not the full package. Implement only the mandatory P0/P1
controls in a separate isolated environment, rerun host preflight, obtain a
unique expiring authorization, and conduct a bounded no-order calibration. Do
not mistake that result for order-path evidence.

## Before any order-path work

Require a new strategic review showing that expected information gain justifies
credential and capital risk. The order-path stage must be separately authorized
under risk policy and may not inherit authorization from no-order calibration.
