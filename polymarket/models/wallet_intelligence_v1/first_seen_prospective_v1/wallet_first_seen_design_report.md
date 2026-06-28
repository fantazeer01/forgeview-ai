# Wallet First-Seen Prospective Experiment v1

This sprint implements the observation system. It does not evaluate H2 and does not estimate latency.

## Observation Boundary

- Wallets: 4 frozen H1 wallets
- Endpoint: `https://data-api.polymarket.com/activity`
- Poll interval: 5.0 seconds
- Maximum duration per run: 300.0 seconds
- Maximum requests per run: 240
- Latest rows per wallet poll: 100
- Public GET only; no authentication, wallet connection, orders, or trading

## Persistence

- SQLite transactions persist every poll payload before analysis
- Active run deadline and request count survive restart
- `(run_id, poll_cycle, wallet_id)` prevents duplicate poll insertion
- Trade identity is globally unique and first-seen timestamp is immutable
- Startup rows are persisted as run baseline identities, not new trades

## API Limits

- Documented Data API limit: 1000 requests per 10 seconds
- Configured usage: 8.0 requests per 10 seconds (0.80%)
- Documentation: https://docs.polymarket.com/api-reference/rate-limits

## Validation

- Restart safe: True
- Duplicate safe: True
- Every poll persisted: True
- First-seen immutable: True
- Deterministic export: True

## Research Status

H2 is not evaluated in this sprint. The system can measure H2 after a future bounded collection produces a preregistered number of target five-minute trades.

Remaining blocker: insufficient prospective target-market observations.
