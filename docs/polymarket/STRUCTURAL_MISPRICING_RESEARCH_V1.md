# Polymarket Structural Mispricing Research v1

Status: Permanently frozen after triage
Last updated: July 4, 2026

## Question

Do existing public quote sessions contain directly executable, non-directional
mispricing after spread, costs, visible liquidity, queue uncertainty and
latency?

## Evidence

The fixed triage used five complete continuous public sessions totaling 60
hours, 2,175 markets and 280,284 fresh deduplicated executable quote states.
It found no crossed or locked books, no positive near-expiry state and no
profitable visible capacity.

Wide spreads appeared in 7,534 states, but marketable round trips had best net
margin -0.040000 and mean -0.066406. Only 102 wide-spread episodes persisted
five seconds. Capturing the displayed spread passively requires queue and
adverse-selection evidence that this branch does not have.

Historical files contain one independent YES book, not independently captured
YES and NO books or multi-outcome books. Complete-set margins derived by
complement are mechanically `-spread` before cost and cannot establish a
two-token arbitrage.

## Decision

Structural mispricing is permanently frozen under D-125. Existing artifacts
remain available for audit. No capture, execution or infrastructure work is
authorized for this branch. Passive liquidity provision is a separate research
hypothesis and must first pass an existing-data feasibility triage.

The sealed holdout remains untouched. Wallet Intelligence and Repricing remain
permanently frozen.
