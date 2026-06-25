# Wallet Lifecycle Reconstruction Review v1

Generated: 2026-06-25

## Scope

Reviewed the Wallet Trade Lifecycle Reconstruction Fixture Prototype v1 code,
tests, and fixture outputs. The review used only existing normalized public
smoke trade history and did not launch public ingestion, connect wallets,
place orders, inspect sealed holdout outcomes, run holdout evaluation, add
expiry joins, add mark-to-market PnL, add Binance/reference alignment, model
copyability delay, model queue priority, or add scoring.

## Files Inspected

- `polymarket/wallet_intelligence/lifecycle.py`
- `polymarket/wallet_intelligence/schema.py`
- `polymarket/wallet_intelligence/cli.py`
- `tests/polymarket/test_wallet_intelligence.py`
- `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture/lifecycle_positions.csv`
- `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture/lifecycle_summary.json`
- `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture/lifecycle_validation.json`

## Confirmed Invariants

- Input rows: 600 normalized public smoke trade rows.
- Lifecycle grouping is by `wallet_id`, `condition_id`, `token_id`, and
  `outcome`.
- Lifecycle candidates reconstructed: 112.
- Status counts: 74 still open, 36 partial exits, 2 bounded-history oversold,
  and 0 full exits.
- BUY rows are treated as entry candidates and SELL rows are treated as exit
  candidates, matching the current normalized public activity rows.
- Position-size conservation passed for all groups.
- Deterministic ordering passed.
- Repeatable CSV export passed.
- Unexpected negative position groups: 0.
- Bounded-history missing-prior-buy groups: 2.

## Review Findings

Full-exit count is 0 because none of the 36 groups with both BUY and SELL rows
has exact equality between total bought size and total sold size. The closest
near-flat group has a remaining residual of 0.0056 shares, so retaining
`partial_exit` is conservative and avoids inventing a tolerance-based close.

Still-open classification is correct for the bounded fixture because these
groups contain BUY rows and no visible SELL rows in the one-page public smoke
window. They should be interpreted as still open within the observed bounded
history, not necessarily still open in the wallet's complete history.

Partial-exit classification is correct for visible groups with BUY size greater
than SELL size. It identifies observed partial liquidation inside the bounded
window, but does not prove final holding time or final position status.

Bounded-history oversold handling is correct for the two visible SELL-only XRP
Up/Down groups. The public smoke captured sells without prior buys, so the
rows are best classified as bounded-history gaps rather than unexpected
negative positions.

Grouping by wallet, condition ID, token ID, and outcome is sufficient for this
fixture prototype. It separates paired outcomes in the same market and avoids
collapsing Up and Down tokens. Future deeper reconstruction should still
cross-check token/outcome mappings against market metadata before interpreting
holding time.

Deterministic ordering was adequate for the current data; no duplicate current
sort keys were found. During review, the implementation was hardened to derive
the lifecycle key from explicit columns and to include dedupe/provenance fields
as additional stable tie-breakers.

## Known Limitations

- One-page public smoke history can omit earlier buys and later sells.
- No REDEEM or resolution rows are handled yet.
- No expiry or market metadata joins are present.
- No holding-time estimate is reliable yet.
- No mark-to-market or realized PnL is computed.
- No Binance/reference alignment is present.
- No copyability delay, liquidity, fill priority, or queue position can be
  inferred.
- Near-flat residuals are not tolerance-closed; this is deliberate until a
  documented precision policy is authorized.

## Suspicious Observations

- Several partial exits are near-flat by tiny residuals, including a BTC group
  with 203.5656 bought versus 203.56 sold. These may be rounding dust, but the
  current exact-size policy correctly leaves them as partial exits.
- The two oversold groups are XRP Up/Down, not BTC/ETH/SOL, and therefore do
  not affect fast BTC/ETH/SOL lifecycle interpretation.

## Recommendation

Proceed to `Wallet Lifecycle Metrics v1`.

That task should compute bounded, descriptive wallet-level lifecycle metrics
from the existing `lifecycle_positions.csv` only, including status counts,
partial-exit frequency, bounded-history gap rate, near-flat residual counts,
asset/outcome concentration, and wallet-level summaries. It must not add new
public ingestion, expiry joins, PnL, Binance/reference alignment, copyability
delay, queue modelling, scoring, live trading, wallet/private-key use, order
placement, holdout inspection, holdout evaluation, or production modelling.
