# Polymarket Passive Liquidity Research v1

Status: Permanently frozen after existing-data feasibility triage
Last updated: July 4, 2026

## Question

Can passive quoting in observed wide-spread five-minute BTC/ETH/SOL markets
produce positive net value after queue uncertainty, adverse selection,
inventory, cancellation latency, stale quotes and costs?

## Evidence

The fixed replay used five complete public sessions and 6,312 wide-spread
episodes. Fill eligibility required the public best quote to deplete through
the posted level. Expected quantity was discounted to 37.5% of visible capped
size. Unmatched inventory was crossed out after a two-second cancellation delay.

Every fixed policy was negative. The least-negative result was SOL at 15
seconds: 157 attempts, 36.54% queue-adjusted fill probability, 73.20% one-sided
share among triggered attempts, -0.709218 dollars per attempt, -0.042789 per
expected filled share and 113.380 max drawdown. Its market-cluster 95% interval
was [-0.977226, -0.452753].

The broad 2/5/15/30-second policies became increasingly negative as quote life
increased. No asset was positive, and near-expiry quoting was worse than broad
5-second quoting.

## Decision

Passive liquidity provision is permanently frozen under D-126. Displayed
spread is not earned P&L, and unmeasured queue details cannot justify advancing
an already negative conservative replay. No prospective shadow, capture,
credential, execution or infrastructure work is authorized for this branch.

The sealed holdout remains untouched. Wallet Intelligence, Repricing and
structural mispricing remain permanently frozen.
