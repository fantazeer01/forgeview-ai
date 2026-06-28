# Polymarket Next Task

Last updated: June 28, 2026
Task status: ACTIVE

This file contains exactly one active task. A future Codex session must read
`MASTER_OBJECTIVE.md`, `RESEARCH_PRINCIPLES.md`, `PROJECT_STATE.md`,
`DECISIONS.md`, `REPRICING_RESEARCH_V1.md`, and
`WALLET_INTELLIGENCE_RESEARCH_V1.md` before starting it.

## Active task: Wallet Detection-To-Expiry Feasibility Sprint v1

### Hypothesis under test

H3: Enough time remains after public wallet activity is first detected to
support future strategy research.

### Evidence basis

Wallet Activity Visibility Delay Sprint v1 analyzed 3,431 fast-crypto trades
and found complete trade/fetch timestamps but zero publication or first-seen
timestamps. H2 remains `INCONCLUSIVE`; retrospective fetch age is not API
latency.

### Objective

Run the smallest bounded prospective public read-only observation needed to
record local first-seen times for newly visible activity from the four H1
above-baseline wallets, join those observations to market expiry, and test
whether meaningful time remains after detection.

### Required scope

1. Observe only the four H1 above-baseline wallets already recorded in the H1
   and H2 artifacts.
2. Define a strict time, request, and row bound before observation begins.
3. Record local request start, response completion, first-seen, trade event,
   and market expiry timestamps with stable transaction identity.
4. Deduplicate repeated observations without replacing the earliest
   first-seen timestamp.
5. Report detection-to-expiry distributions and shares with at least 60, 120,
   and 180 seconds remaining.
6. Separate observed network/API delay bounds from local polling interval,
   clock uncertainty, reaction time, fill uncertainty, liquidity, and
   slippage.
7. End with exactly one H3 conclusion: `SUPPORTED`, `REJECTED`, or
   `INCONCLUSIVE`.
8. Do not copy trades, place orders, connect wallets/private keys, modify
   Wallet Score or Watchlist, inspect sealed holdout outcomes, run holdout
   evaluation, or claim profitability, alpha, execution quality, or trading
   suitability.
9. Run Wallet Intelligence tests and the full test suite.

### Acceptance criteria

- prospective first-seen provenance is present for every measured row;
- no retrospective fetch timestamp is treated as first-seen evidence;
- exports and ordering are deterministic;
- the sprint directly answers H3 or names the single measured blocker;
- exactly one active successor task remains after completion.
