# Public Microstructure Capture Smoke Validation v1

Decision: **READY_FOR_PRODUCTION_CAPTURE**

- Duration: 900.009s
- Events: 1328
- Assets: {'BTC': 443, 'ETH': 443, 'SOL': 442}
- Replay compatible: True
- Feature rows: 6
- Holdout outcomes read: False

| Feature | Event population | Missing | Valid | Feature rows |
|---|---:|---:|---:|---:|
| quote_age_seconds | 100.00% | 0.00% | 1328 | 100.00% |
| time_since_quote_update_seconds | 100.00% | 0.00% | 1328 | 100.00% |
| repricing_velocity | 99.10% | 0.90% | 1316 | 100.00% |
| repricing_acceleration | 98.19% | 1.81% | 1304 | 100.00% |
| yes_change_frequency_30s | 100.00% | 0.00% | 1328 | 100.00% |
| no_change_frequency_30s | 100.00% | 0.00% | 1328 | 100.00% |
| consecutive_quote_stability | 100.00% | 0.00% | 1328 | 100.00% |
| bid_ask_spread | 100.00% | 0.00% | 1328 | 100.00% |
| spread_change | 99.10% | 0.90% | 1316 | 100.00% |
| spread_velocity | 99.10% | 0.90% | 1316 | 100.00% |
| spread_compression | 99.10% | 0.90% | 1316 | 100.00% |
| yes_bid_size | 100.00% | 0.00% | 1328 | 100.00% |
| yes_ask_size | 100.00% | 0.00% | 1328 | 100.00% |
| total_bid_depth | 100.00% | 0.00% | 1328 | 100.00% |
| total_ask_depth | 100.00% | 0.00% | 1328 | 100.00% |
| book_imbalance | 100.00% | 0.00% | 1328 | 100.00% |
| market_refresh_latency | 100.00% | 0.00% | 1328 | 100.00% |
| cross_asset_yes_dispersion | 99.92% | 0.08% | 1327 | 100.00% |
| cross_asset_relative_yes | 99.92% | 0.08% | 1327 | 100.00% |

This report measures capture plumbing, not predictive edge.
