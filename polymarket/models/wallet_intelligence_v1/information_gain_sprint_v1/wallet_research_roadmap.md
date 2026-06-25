# Wallet Intelligence Research Roadmap

Generated: June 26, 2026

## Top 10 Ranked Layers

1. **Market expiry**  
   Implement first. It has the best cost/value ratio because it directly reduces the largest measured ambiguity: 1,735 still-open lifecycle candidates in the 30-wallet batch.

2. **Resolved market outcome**  
   Implement after or alongside expiry only if report-only boundaries are preserved. It adds final-side context but must not become a profitability or trading-quality score.

3. **Full historical wallet activity**  
   Implement after metadata joins. It reduces bounded-history artifacts, including 24 oversold groups and many still-open groups, but requires careful pagination and caching.

4. **Additional public endpoints**  
   Inventory and reconcile positions, closed positions, value/traded aggregates, prices history, activity, trades, and market metadata. This improves reproducibility and endpoint confidence.

5. **Reference asset alignment (BTC/ETH/SOL)**  
   Use after expiry context to test whether fast-crypto entries are actually aligned with external asset moves.

6. **Liquidity / slippage estimation**  
   Use after lifecycle and timing context are stronger. It is important for execution realism but has high engineering and assumption risk.

7. **Mark-to-market valuation**  
   Useful for open-position context, but defer until expiry/outcome joins prevent misleading valuation interpretations.

8. **Execution delay modelling**  
   Valuable for copyability research later, but weak before reference alignment and liquidity context exist.

9. **Queue position / fill uncertainty**  
   Important eventually, but likely the hardest public-data layer and least suitable for near-term research velocity.

10. **Other public data source: explorer / on-chain settlement metadata**  
   Useful for provenance and redemption cross-checks later, but not the next highest-value layer.

## Recommended Next Sprint

**Wallet Market Expiry Join Sprint v1**

Objective:

- Join existing bounded wallet trade and lifecycle evidence to public market expiry metadata.
- Measure join coverage by wallet, market slug, condition ID, token ID, and event slug.
- Add report-only expiry context to lifecycle research artifacts.
- Do not change Wallet Score, Wallet Watchlist, copyability classifications, or any trading boundary.

Why this sprint next:

- It is the best one-week capability by information gain per engineering effort.
- It improves Lifecycle, Metrics, Watchlist reasoning, Copyability confidence, and future Ranking readiness without introducing performance claims.
- It is a prerequisite for interpreting resolved outcomes safely.

Expected outputs:

- `market_expiry_join_report.md`
- `market_expiry_join_summary.json`
- `expiry_join_coverage_by_wallet.csv`
- `expiry_join_coverage_by_market.csv`
- `expiry_join_endpoint_inventory.csv`

Strict non-goals:

- no resolved-outcome scoring;
- no PnL, ROI, Sharpe, market-advantage, expected-return, execution-quality, or trading-suitability logic;
- no Wallet Score formula change;
- no Wallet Watchlist logic change;
- no wallet/private-key use;
- no order placement;
- no trade copying;
- no sealed holdout inspection;
- no holdout evaluation.

## Follow-On Roadmap

After Wallet Market Expiry Join Sprint v1:

1. Wallet Resolved Outcome Join Sprint v1
2. Wallet Full History Pagination Feasibility Sprint v1
3. Wallet Endpoint Reconciliation Sprint v1
4. Wallet Reference Asset Alignment Sprint v1
5. Wallet Liquidity Context Feasibility Sprint v1
6. Wallet Mark-To-Market Context Design v1
7. Wallet Observation Delay Measurement Design v1
8. Wallet Queue/Filling Uncertainty Feasibility v1
9. Wallet On-Chain Provenance Cross-Check v1

Each follow-on sprint must remain public, bounded, deterministic, and research-only.
