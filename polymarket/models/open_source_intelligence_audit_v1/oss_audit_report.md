# Polymarket Open Source Intelligence Audit v1

Date: June 24, 2026
Status: Complete
Scope: Read-only audit of public GitHub repositories that may accelerate ForgeView Polymarket research.

## Safety Confirmation

This audit did not:

- run live trading;
- connect wallets;
- use private keys;
- install dependencies globally;
- modify the existing trading/research pipeline;
- launch capture campaigns;
- train production models.

The inspected repositories were treated as untrusted external code. They were
read as source/reference material only.

## Repositories Inspected

1. `alsk1992/CloddsBot` - https://github.com/alsk1992/CloddsBot
2. `ent0n29/polybot` - https://github.com/ent0n29/polybot
3. `MrFadiAi/Polymarket-bot` - https://github.com/MrFadiAi/Polymarket-bot
4. `HarrierOnChain/Prediction-Markets-Trading-Bot-Toolkits` - https://github.com/HarrierOnChain/Prediction-Markets-Trading-Bot-Toolkits
5. `evan-kolberg/prediction-market-backtesting` - https://github.com/evan-kolberg/prediction-market-backtesting
6. `pmxt-dev/pmxt` - https://github.com/pmxt-dev/pmxt
7. `lihanyu81/polymarket_lp_tool` - https://github.com/lihanyu81/polymarket_lp_tool
8. `aarora4/Awesome-Prediction-Market-Tools` - https://github.com/aarora4/Awesome-Prediction-Market-Tools

## Executive Verdict

The most directly useful repository for the next ForgeView step is
`ent0n29/polybot`. It overlaps strongly with Wallet Intelligence Research
because it contains public user-trade ingestion, Polymarket profile resolution,
research snapshots, replication scoring, paper-vs-target-user matching, maker
fill calibration, and detailed BTC/ETH Up/Down reverse-engineering notes.

The strongest backtesting reference is
`evan-kolberg/prediction-market-backtesting`. It should not be copied directly
without a license review, but its design is highly relevant: strict separation
between venue loaders, pure strategy logic, and runners; L2 book replay;
queue-position assumptions; latency, slippage, fee, and maker-rebate modeling;
and account-ledger replay.

The most useful API reference is `pmxt-dev/pmxt`. It is relevant for
read-only normalization of Polymarket Gamma/CLOB/Data/WebSocket semantics and
for comparing ForgeView's Binance/external-feed handling against a broader
unified market-data adapter.

## Top 3 Most Useful Repositories

| Rank | Repository | Why it matters |
|---:|---|---|
| 1 | `ent0n29/polybot` | Best wallet-intelligence and strategy reverse-engineering reference. It already studies target-user behavior, paired outcomes, execution edge, stale top-of-book risk, replication scoring, and paper strategy matching. |
| 2 | `evan-kolberg/prediction-market-backtesting` | Best execution-realistic backtesting reference. It addresses the exact missing layer in ForgeView repricing research: visible depth, queue position, latency, slippage, fees, and fill realism. |
| 3 | `pmxt-dev/pmxt` | Best Polymarket API/data normalization reference. It covers Gamma, CLOB, Data API, WebSocket order books/trades, SDKs, CLI watch commands, and Binance feed normalization. |

## Repository Findings

### 1. alsk1992/CloddsBot

CloddsBot is a broad autonomous trading terminal for prediction markets, crypto
futures, Solana/EVM wallets, and conversational execution. It advertises
Polymarket, Kalshi, Binance, whale tracking, copy trading, market making,
paper trading, dry-run behavior, and a large skill catalog.

Useful overlap:

- Polymarket feed handlers;
- Binance futures handlers;
- paper trading and backtest modules;
- dry-run signal router tests;
- whale tracking concepts;
- market-making and copy-trading vocabulary.

Reuse risk:

- very broad autonomous execution surface;
- private-key and wallet management paths;
- global `npm install -g` quickstart;
- postinstall dependency behavior;
- too much unrelated multi-chain execution for ForgeView's research boundary.

Recommendation: reference only. Do not import code or install globally.

### 2. ent0n29/polybot

Polybot is the strongest direct match. Its research docs and code show a
pipeline for reverse-engineering a target Polymarket trader using user-trade
data, ClickHouse, profile resolution, top-of-book capture, on-chain receipt
joins, strategy snapshots, paper-trade matching, replication scores, and maker
fill calibration.

Useful overlap:

- public wallet/profile resolution;
- user-trade ingestion;
- target-wallet reverse engineering;
- BTC/ETH Up/Down market family analysis;
- paired UP/DOWN behavior detection;
- complete-set-like behavior;
- stale top-of-book diagnostics;
- paper strategy order-stream matching;
- maker fill/queue calibration.

Important insight:

Polybot's research notes suggest that for at least one studied target wallet,
profitability may depend less on final directional prediction and more on
execution edge, paired outcome behavior, maker fills, and reliable decision-time
book state. That is directly relevant to both Wallet Intelligence Research and
Repricing Research.

Reuse risk:

- Java/Spring/ClickHouse infrastructure is heavy;
- execution and signing code exists in the same repo;
- target-user findings may be regime and period specific;
- direct code reuse should be avoided until design is isolated.

Recommendation: inspect first in depth.

### 3. MrFadiAi/Polymarket-bot

Polymarket-bot is a TypeScript Polymarket SDK/bot with examples for smart
money, market analysis, kline aggregation, follow-wallet strategy, real-time
WebSocket, trading orders, arbitrage scans, and rewards tracking. It has a
dry-run flag and dashboard/risk controls, but its setup centers on wallet
private keys.

Useful overlap:

- smart-money service shape;
- follow-wallet strategy example;
- market and kline analysis examples;
- real-time WebSocket examples;
- dashboard/risk-control vocabulary;
- dry-run configuration.

Reuse risk:

- private key is required in setup docs;
- examples include real order placement;
- dashboard can switch live/dry-run;
- execution is too close to the surface for direct adoption.

Recommendation: use as a wallet-intelligence field inventory and service-shape
reference only.

### 4. HarrierOnChain/Prediction-Markets-Trading-Bot-Toolkits

This Rust toolkit is execution-oriented and advertises copy trading, BTC
short-window arbitrage, cross-market arbitrage, orderbook imbalance, market
making, whale signal, depth guard, circuit breaker, and dry run.

Useful overlap:

- dry-run-first framing;
- depth guard;
- circuit breaker;
- copy-trading architecture vocabulary;
- BTC short-window arbitrage concept;
- orderbook imbalance and market-making concept list.

Reuse risk:

- production/live execution orientation;
- private-key config;
- direct copy-trading scope conflicts with ForgeView boundaries;
- marketing/performance claims require independent verification.

Recommendation: design-reference only. Do not use execution code.

### 5. evan-kolberg/prediction-market-backtesting

This is the strongest research/backtesting accelerator. It provides a
NautilusTrader-based prediction-market backtesting framework with Polymarket
L2 replay, PMXT/Telonex data loading, strategy modules, live sandbox plumbing
for BTC 5m markets, account-ledger replay, execution modeling, latency,
slippage, fees, maker rebates, queue-position assumptions, and test coverage.

Useful overlap:

- repricing simulator realism;
- dry-run strategy simulation;
- backtesting and report design;
- strategy/loader/runner separation;
- account-ledger replay and copy-trading interpretation;
- BTC 5m sandbox concepts.

Reuse risk:

- mixed licensing requires review before code reuse;
- large framework footprint;
- some live sandbox paths exist;
- integrating Nautilus would be a major architecture decision.

Recommendation: reuse concepts, not code, until a separate backtesting
architecture decision is made.

### 6. pmxt-dev/pmxt

PMXT is a CCXT-style unified prediction-market API with Python, TypeScript,
CLI, local sidecar, and hosted options. It includes Polymarket Gamma/CLOB/Data
API specs, WebSocket orderbook/trade examples, and Binance feed normalization.

Useful overlap:

- Polymarket API normalization;
- Gamma/CLOB/Data/WebSocket references;
- orderbook and trade stream examples;
- Binance feed normalization;
- CLI watch patterns;
- possible future read-only adapter comparison.

Reuse risk:

- hosted writes/trading are in scope for PMXT;
- private-key examples exist;
- adding the SDK would expand dependency and trust surface;
- local sidecar is more infrastructure than ForgeView currently needs.

Recommendation: read-only reference. Evaluate API semantics before any
dependency decision.

### 7. lihanyu81/polymarket_lp_tool

This is a passive liquidity/order-monitoring tool with Python and Rust paths.
It manages existing open orders, cancel/replace decisions, reward-band pricing,
custom pricing rules, Telegram/Web controls, fill/depth risk alerts, and a
WebSocket-first Rust rewrite. It is not a repricing or wallet-intelligence
tool, but it is valuable for passive execution-risk vocabulary.

Useful overlap:

- market-making and liquidity reward behavior;
- orderbook depth and midpoint jump monitoring;
- anti-sniping filters;
- fill cooldown;
- max chase limits;
- post-only cancel/replace safety;
- Telegram/Web operator controls.

Reuse risk:

- private keys and API credentials are required;
- execution path cancels/replaces live orders;
- not aligned with current active research.

Recommendation: keep in backlog for execution realism and LP research, not for
the next task.

### 8. aarora4/Awesome-Prediction-Market-Tools

This is a curated directory of prediction-market tools, APIs, dashboards,
alerts, analytics platforms, copy-trading services, and data vendors.

Useful overlap:

- discovery of smart-money trackers;
- discovery of alerting tools;
- discovery of market-data vendors;
- discovery of analytics dashboards.

Reuse risk:

- directory only;
- many tools are commercial, closed, or unaudited;
- no direct code reuse.

Recommendation: keep as an OSS/source discovery index.

## Directly Useful for ForgeView

Directly useful:

- `ent0n29/polybot`
- `evan-kolberg/prediction-market-backtesting`
- `pmxt-dev/pmxt`
- `MrFadiAi/Polymarket-bot`

Useful only as design/reference:

- `HarrierOnChain/Prediction-Markets-Trading-Bot-Toolkits`
- `lihanyu81/polymarket_lp_tool`
- `alsk1992/CloddsBot`
- `aarora4/Awesome-Prediction-Market-Tools`

## Feature Overlap With Current ForgeView Work

Repricing Research overlap:

- PMXT and prediction-market-backtesting overlap with market data,
  WebSockets, orderbook replay, BTC 5m sandboxing, and execution assumptions.
- Polybot overlaps through the finding that some profitable behavior may be
  execution-edge or paired-outcome behavior rather than final outcome
  prediction.
- LP Tool overlaps through passive-order and anti-sniping risk concepts.

Wallet Intelligence overlap:

- Polybot overlaps most strongly through user profile/trade ingestion,
  strategy reverse engineering, target-user snapshots, and replication scores.
- Polymarket-bot overlaps through smart-money and follow-wallet examples.
- Awesome-Prediction-Market-Tools overlaps as a source-discovery directory.

Backtesting/dry-run overlap:

- prediction-market-backtesting is the strongest overlap.
- Polybot includes paper bot matching and maker fill calibration.
- Polymarket-bot and CloddsBot include dry-run/paper modes, but with more
  execution risk.

## Missing ForgeView Features

1. Normalized wallet/profile/position ingestion.
2. Wallet behavior metrics: paired outcomes, side distribution, holding time,
   sizing, market family, realized/unrealized split, and drawdown.
3. Copy-delay risk measurement.
4. Replication-score reports comparing observed wallet behavior against a
   research hypothesis.
5. L2 execution realism for repricing: visible depth, queue proxy, maker/taker
   fill assumptions, latency, fees, slippage, and timeout sensitivity.
6. Read-only API adapter comparison against external Polymarket tooling.

## Safe Reuse Ideas

- Polybot-style frozen wallet snapshots and replication-score reports.
- Prediction-market-backtesting-style execution realism checklist.
- PMXT-style read-only API normalization vocabulary.
- Strategy/data-loader/runner separation.
- Dry-run invariants and depth-guard terminology from execution-heavy repos.
- LP Tool anti-sniping vocabulary: midpoint jump pause, stable-mid
  confirmation, EMA/median filters, fill cooldown, max chase.

## Too Risky or Irrelevant

Highest risk:

- `alsk1992/CloddsBot`
- `HarrierOnChain/Prediction-Markets-Trading-Bot-Toolkits`
- `lihanyu81/polymarket_lp_tool`
- `MrFadiAi/Polymarket-bot`

Reason: these expose or emphasize wallet/private-key configuration,
authenticated trading, live order placement, copy trading, or cancel/replace
execution. They are useful references, but not safe to run or import into
ForgeView's current research-only boundary.

Least directly relevant:

- `aarora4/Awesome-Prediction-Market-Tools`, because it is a directory rather
  than an implementation.

## First Deep-Dive Target

Inspect `ent0n29/polybot` first in depth.

Reason:

- It is the best bridge between Wallet Intelligence and Repricing Research.
- It contains target-wallet reverse-engineering artifacts, not only bot code.
- Its findings directly challenge the idea that profitable wallets are simply
  predicting final outcomes.
- It suggests a concrete next research path: ingest public wallet data, compute
  behavior metrics, then test whether those behaviors resemble repricing,
  complete-set execution, passive spread capture, or final-resolution betting.

## Recommended Next Technical Task

Keep the active successor task as:

`Wallet Intelligence Data Ingestion v1`

This should collect and normalize public profile/position data for the existing
seed wallet list. It should not score wallets, copy trades, train models, run
holdout evaluation, launch capture campaigns, or connect wallets.

After ingestion, the natural follow-up is a behavior-metrics task inspired by
Polybot's snapshot and replication-score design.

