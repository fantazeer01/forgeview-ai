# Wallet Intelligence Research

Research-only module skeleton for public Polymarket wallet/profile behavior.

This module is separate from outcome prediction, repricing simulation, live
trading, wallet execution, and production modelling. It contains schema and
input templates only.

It must not:

- inspect sealed holdout outcomes;
- run holdout evaluation;
- connect wallets or private keys;
- place orders or copy trades;
- launch capture campaigns;
- train production models.

Primary document:

- `docs/polymarket/WALLET_INTELLIGENCE_RESEARCH_V1.md`

Initial input template:

- `polymarket/wallet_intelligence/watched_wallets.example.csv`

