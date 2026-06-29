# First 24-Hour Repricing Paper Soak v1

Verdict: `FAILED_OPERATIONAL_INTEGRITY`

The preflight passed with safe Windows power settings, sufficient disk, a
writable ledger, source rotation enabled, and frozen strategy fingerprint
`d5d389be45d472628aab06b3aeeb281593e74d48b82902e12712047c91fec010`.
Exactly one public-only producer and one paper runtime were launched. No live
order, wallet, private key, model training, holdout inspection, or parameter
change occurred.

The producer emitted `session_completed`, but the campaign failed continuity:
32,540 of 43,200 checkpoints were present (75.3241%), one internal gap was
4,112.812693 seconds, the terminal gap was 23,554.333577 seconds, and the
campaign was classified `incomplete_campaign`. There were no fatal capture
errors.

The paper ledger remained valid and contained 60 unique signals, positions,
and closed trades with no open positions or duplicate business keys. However,
the heartbeat stopped after 12,310.53587 seconds while the process remained
CPU-active beyond its 24-hour bound. Its cursor stopped at event 351,230 of
531,314. Deterministic offline export reconstructed 73 signals, leaving a
13-signal live-processing shortfall. The consumer was terminated only after
the source had completed and all persisted positions were closed.

Replay and export each reproduced exactly. The descriptive offline result was
73 signals: BTC / ETH / SOL 13 / 17 / 43, YES / NO 26 / 47, 80.82% win rate,
+0.071432 expectancy after slippage, +5.2145 P&L after slippage, and 0.22
maximum drawdown. These rows are excluded from frozen evidence-gate aggregation
because campaign continuity and live reconciliation failed.

Scientifically valid Repricing evidence therefore remains 172 signals over 24
hours and two independent sessions. Weak evidence remains unmet at the frozen
40-hour and three-session gates. The next task must fix incremental stream
backpressure, heartbeat liveness, bounded shutdown, and fail-closed detection
before any second soak is authorized. All 45 Repricing tests and all 191
repository tests pass.
