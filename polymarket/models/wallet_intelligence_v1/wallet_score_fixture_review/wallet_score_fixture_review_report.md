# Wallet Score Fixture Review v1

Generated: 2026-06-26

## Scope

This review inspected Wallet Score Fixture Implementation v1 for correctness,
design compliance, and readiness for broader evidence collection. It did not
expand scoring, add new metrics, launch ingestion, join expiry data, compute
PnL/ROI/Sharpe, estimate copyability, model execution quality, connect wallets,
place orders, inspect sealed holdout outcomes, or run holdout evaluation.

## Files Inspected

- `polymarket/wallet_intelligence/wallet_score.py`
- `polymarket/wallet_intelligence/lifecycle_metrics.py`
- `tests/polymarket/test_wallet_intelligence.py`
- `polymarket/models/wallet_intelligence_v1/wallet_score_design/wallet_score_design_v1.md`
- `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_scores.csv`
- `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_scores_summary.json`
- `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_score_validation.json`
- `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_score_report.md`

## Confirmed Invariants

- The scorer uses the approved structural allowlist from Wallet Score Design v1.
- `wallet_id` and `profile_url` are report/provenance fields, not scoring values.
- Forbidden inputs are absent from the scoring allowlist and generated outputs:
  PnL, ROI, realized profit, Sharpe, execution quality, copyability, alpha,
  mark-to-market values, final resolved win/loss outcomes, sealed holdout
  labels or outputs, private wallet data, order-placement data, and
  authenticated trading data.
- Score bounds are enforced at 0 to 100.
- Component and penalty bounds match the design document.
- Priority buckets are deterministic:
  `high_priority >= 75`, `medium_priority >= 50`, `low_priority >= 25`,
  and `insufficient_visible_structure < 25`.
- Ordering is deterministic by score descending, fast-crypto share descending,
  lifecycle-position count descending, then `wallet_id` ascending.
- Missing required structural metrics fail validation rather than being guessed.
- The generated report explicitly states that scores are structural
  research-priority labels only and are not profitability, alpha, execution,
  copyability, or trading-suitability claims.

## Score Behavior Observations

Current six-wallet fixture distribution:

- `medium_priority`: 1
- `low_priority`: 3
- `insufficient_visible_structure`: 2
- `high_priority`: 0

The strongest structural wallet remains
`0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a` with score `73`, one band below
`high_priority`. This is consistent with the design: the wallet has strong
visible coverage, fast-crypto relevance, and lifecycle activity, but it also
receives concentration and near-flat residual ambiguity penalties.

Small fast-crypto wallets remain `low_priority` because the fixture only has
bounded public history and their small sample or still-open share penalties are
material. Non-fast-crypto or weather/other wallets remain
`insufficient_visible_structure` despite visible lifecycle counts because
Wallet Score v1 is intentionally focused on BTC/ETH/SOL Up/Down research
triage.

## Threshold And Penalty Assessment

The current threshold behavior is acceptable for a six-wallet fixture. The
absence of `high_priority` wallets is conservative rather than a defect:
bounded one-page public history still has incomplete lifecycle evidence, no
expiry joins, no mark-to-market context, and no copyability modelling.

No threshold or penalty adjustment is recommended before broader evidence
collection design. Raising the top wallet into `high_priority` from this small
fixture would overfit the thresholds to one sample and weaken the
interpretation-safety boundary.

## Known Limitations

- The fixture uses six seed wallets only.
- Scores depend on bounded visible public trade history, not complete account
  history.
- Full exits remain structurally uncertain without expiry, redemption, or
  deeper history joins.
- The score does not measure profitability, alpha, ROI, PnL, Sharpe,
  execution quality, copyability, liquidity, or live-trading suitability.
- Concentration penalties are generality warnings only, not claims that
  concentrated wallets are worse traders.
- Current bands should not be used as wallet rankings or recommendations.

## Bounded Correctness Findings

No bounded correctness bugs were found. No code or metric-generation changes
are required for this review.

## Recommended Successor Task

`Wallet Score Broader Evidence Collection Design v1`

The next task should design a bounded, public, read-only evidence expansion
plan for applying the existing Wallet Score v1 to more wallet samples. It
should define wallet selection criteria, per-wallet/page limits, provenance,
rate limits, validation gates, and review criteria. It must not launch
ingestion, add score inputs, change thresholds, compute PnL/ROI/Sharpe, infer
copyability, join mark-to-market values, connect wallets/private keys, place
orders, inspect sealed holdout outcomes, or run holdout evaluation.
