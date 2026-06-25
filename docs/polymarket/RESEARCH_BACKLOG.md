# Polymarket Research Backlog

Last updated: June 19, 2026  
Active work authority: [NEXT_TASK.md](NEXT_TASK.md)

This is an idea inventory, not an execution queue. Items here must not displace
the single active task unless `PROJECT_STATE.md` is updated and the selected
item is promoted into `NEXT_TASK.md`.

## Probability model

- Establish unconditional-frequency and Polymarket-implied-probability
  baselines.
- Train an interpretable logistic probability model before complex models.
- Measure log loss, Brier score, calibration error, balanced accuracy, and
  performance by asset and regime.
- Add purged walk-forward splits and an untouched final holdout.
- Study feature ablation, drift, and calibration stability.

Prerequisite: public dataset and authoritative labels pass the quality gate.

## Kelly sizing

- Compare fixed-risk sizing with fractional Kelly.
- Estimate uncertainty-adjusted edge rather than using point estimates.
- Cap sizing by liquidity, spread, asset exposure, and drawdown state.
- Stress estimation error and correlated outcomes.

Prerequisite: proven calibrated probabilities and positive net expectancy.

## Execution engine

- Design as a separately authorized boundary, not an extension enabled by
  default in the research system.
- Model order-book depth, queue position, partial fills, cancellations, and
  stale quotes.
- Require kill switches, reconciliation, risk limits, audit logs, and staged
  deployment.

Prerequisite: proven edge, production-readiness review, and explicit approval.

## Portfolio construction

- Allocate risk across BTC, ETH, SOL, overlapping windows, and correlated
  signals.
- Add exposure limits, covariance-aware sizing, concentration controls, and
  portfolio drawdown budgets.
- Attribute P&L by asset, regime, signal family, and holding period.

Prerequisite: multiple independently validated signals or assets.

## Market microstructure

- Capture bid/ask depth, spread dynamics, quote age, trade flow, and repricing
  latency.
- Measure whether observed lag is executable after queue position and adverse
  selection.
- Study market-maker response around window open and expiry.
- Compare venue/reference-source latency and resolution-source alignment.

Prerequisite: stable higher-frequency public capture.

## Additional assets

- Evaluate whether other crypto assets have sufficient five-minute market
  frequency and liquidity.
- Consider non-crypto short-duration markets only under a separate feature and
  label specification.
- Require asset-specific quality and validation gates before inclusion.

Prerequisite: BTC/ETH/SOL pipeline passes the public evidence milestone.

## Other research ideas

- Authoritative resolution-source comparison.
- Regime classification using only ex-ante information.
- Probability calibration by time-to-expiry bucket.
- Signal decay and crowding monitoring.
- Cost-aware abstention thresholds.
- Data-source redundancy and clock-drift diagnostics.
- Wallet intelligence extensions after ingestion: cluster public wallet
  behavior by market type, holding period, cheap-side buying, late-entry
  timing, and copyability-delay risk without copying trades or connecting
  wallets.
- Wallet intelligence public-history follow-up: after the active fixture
  implementation task, consider a separately authorized bounded public smoke
  ingestion using the seed-wallet caps in `ingestion_limits.json`, with
  public-source provenance, deterministic rebuild checks, and no execution or
  copy-trading capability.
- Open-source intelligence follow-ups: deep-inspect `ent0n29/polybot` for
  wallet snapshot schema, replication score design, paired-outcome detection,
  stale top-of-book diagnostics, and maker-fill calibration; separately review
  `prediction-market-backtesting` for execution-realism assumptions before any
  repricing simulator changes.
