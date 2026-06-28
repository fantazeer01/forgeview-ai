# Repricing Continuous Paper Trading Readiness Sprint v1

## Verdict

Current readiness: **NOT READY** for continuous repricing paper trading.

The public capture substrate is mature enough to reuse, but the currently
running v5 shadow path is not the frozen repricing strategy. The frozen
repricing entry and exit semantics exist only in post-session replay.

Component classification:

- `READY`: 4;
- `MINOR WORK`: 7;
- `MAJOR WORK`: 7;
- launch-blocking components: 13 of 18.

Estimated implementation effort: **9.75 engineer-days**, before contingency.
A realistic planning range is **9-11 engineer-days**, followed by a minimum
24-hour supervised public paper soak.

## Pipeline Review

### What Is Ready

- `edge_engine_v5` discovers rotating public BTC/ETH/SOL five-minute markets.
- Async public quote and reference feeds sustain two-second capture cadence.
- `LagDetector` emits the frozen measurement inputs and reasons.
- JSONL evidence records references, quotes, microstructure, lag measurements,
  lifecycle, checkpoints, failures, and completion status.
- Campaign continuity and deterministic replay are proven on two 12-hour
  balanced sessions.
- Windows power inspection and sleep inhibition exist in the evidence-batch
  wrapper, though not in the direct capture CLI.

### Critical Semantic Mismatch

The live v5 path opens a generic v3 score-based shadow position only when
`measurement.qualified` is true. It uses `EdgeScorer`, `DecisionEngine`, a
$100 stake, 10 bps slippage, score-based closes, and end-of-session force
closure.

The frozen repricing research path instead accepts both:

- `qualified_external_move_not_repriced`;
- `confidence_below_threshold`.

It requires at least 60 seconds to expiry, suppresses overlapping paper
positions, enters YES for UP and NO for DOWN, and exits at the first 0.03
target, 0.03 stop, or 180-second timeout with 0.02 conservative slippage.
Those rules are evaluated only after the full session is loaded. Therefore
existing v5 shadow trades and PnL cannot be treated as continuous repricing
paper trades.

## Required Components

The detailed classification and effort estimate are in
`repricing_mvp_components.csv`.

The launch-critical missing path is:

1. consume each persisted lag measurement causally;
2. apply the frozen reason, expiry, and non-overlap admission rules;
3. transactionally create a repricing paper position;
4. evaluate target, stop, timeout, and expiry on each subsequent quote;
5. persist every state transition, realized PnL, and processing cursor;
6. recover by replaying raw events after the last committed cursor;
7. suppress duplicate entries and closes across process restarts;
8. publish heartbeat, daily statistics, and bounded notifications.

## Launch Blockers

1. No online implementation of the frozen repricing admission contract.
2. No causal repricing-specific paper position lifecycle.
3. No live target/stop/timeout close detector.
4. Existing live PnL uses incompatible strategy and slippage semantics.
5. No transactional persistent state for open positions or event cursors.
6. No crash/restart recovery for open positions.
7. Duplicate and overlap protection are memory-only.
8. Fixed-duration sessions force-close generic positions and do not operate as
   one continuous repricing ledger.
9. No repricing UTC daily statistics or persistent equity curve.
10. No paper-engine health heartbeat, stale-feed alarm, or write-failure alarm.
11. No Polymarket-specific Telegram notification adapter.
12. No single-instance process lock, supervisor, or automatic restart policy.
13. No crash, duplicate, recovery, notification, or 24-hour soak validation.

## Evidence Limitations

Operational readiness is separate from strategy evidence. The random-baseline
sprint supports frozen timing over 172 development signals, but only two
adjacent sessions are available. Current paper prices do not establish
executable fills, depth consumption, queue position, fees, or live latency.
A continuously running paper engine may collect those diagnostics, but its
existence cannot turn development evidence into a proven edge.

## Readiness Conclusion

The master hypothesis is **REJECTED FOR CURRENT SOFTWARE READINESS**: the
detector substrate can run continuously, but the frozen repricing paper
strategy cannot yet survive a restart or produce a causally correct continuous
ledger. Detector maturity must not be confused with engine maturity.

Frozen detector logic and thresholds were not modified. The sealed holdout was
not opened. No capture or paper campaign was launched.
