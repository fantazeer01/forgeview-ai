# Research Log

## v1 - Probability Dataset

Built the first resolved BTC 5m dataset with market probability, BTC spot
price, short-horizon returns, volatility, and final outcome.

## v2 - Baseline Models

Compared market probability, BTC-only features, and combined logistic models
using chronological out-of-sample evaluation.

## v3 - Snapshot Timing

Evaluated 4m, 3m, 2m, 1m, and 30s snapshots. The combined market-plus-BTC
model showed predictive improvement over raw market probability.

Conclusion: **Predictive edge: YES.**

## v4 - Trading Simulation

Converted model probability differences into simulated UP/DOWN purchases at
2%, 5%, 10%, and 15% thresholds. Tested base and stress execution assumptions.

Conclusion: **Simulated profit edge: YES.**

## v5 - Executable Price Proxy

Historical order books were unavailable, so conservative execution proxies
were tested. Results remained promising but could not establish executable
profitability.

## v6 - Live Real-Ask Validation

Built a live recorder and joined captured asks to resolved outcomes.

- 125 usable recorder rows
- 9 resolved markets
- Positive 2m cell based on only 2 trades
- Negative results at several other timing buckets

Conclusion: **Real ask edge: NOT CONFIRMED.**

## Recorder Findings

The recorder switched markets after expiry and survived transient Gamma,
CLOB, Binance, and Coinbase failures. Upstream SSL timeouts generated many
partial rows and reduced sampling frequency. Recorder resilience and stable
market selection remain the immediate engineering priority.

