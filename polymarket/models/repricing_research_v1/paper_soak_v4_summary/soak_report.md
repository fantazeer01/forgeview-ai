# Fourth 24-Hour Repricing Paper Soak v1

Verdict: `PASS_OPERATIONAL_INTEGRITY`

The clean relaunch completed one public-only 86,400-second capture under the
frozen Repricing configuration. Source completeness and continuity passed with
43,200 / 43,200 checkpoints, 100% temporal coverage, a 2.090353-second maximum
gap, zero fatal capture errors, and `session_completed` as the final
append-monotonic event.

The managed runtime consumed all 741,438 source records through final index
741,437. Terminal health was `complete`, terminal drain completed, backlog was
zero, and no watchdog, host-suspend, stale-event, fatal, duplicate, restart, or
open-position condition occurred. The ledger contains 166 signals, positions,
and closed trades and reconciles exactly to frozen offline export.

Batch metrics: BTC / ETH / SOL 31 / 39 / 96; YES / NO 61 / 105; 131 wins;
78.915663% win rate; +0.042771 after-slippage expectancy; +7.1000
after-slippage P&L; and 0.2600 maximum drawdown. Exits were 131 targets, 32
stops, and 3 timeouts. Replay and export repeated byte-for-byte.

Scientifically valid Batch 001, Batch 002, and this soak aggregate to 338
signals over 48.000000389 hours and three independent sessions. BTC / ETH / SOL
are 76 / 80 / 182; YES / NO are 128 / 210; win rate is 71.301775%; expectancy
is +0.032405; after-slippage P&L is +10.9530; and maximum drawdown is 0.8750.
The nominal 95% Wilson win-rate interval is 66.2612%-75.8636%; the nominal
normal interval for expectancy is +0.021666 to +0.043145. Serial correlation
and three-session clustering limit those intervals.

All frozen Weak Evidence gates pass. This advances Repricing to weak
development evidence only. It does not establish production edge, authorize
holdout access, or authorize live trading. The next stage is predefined
stability and executable-cost stress without parameter optimization.

Validation: 59 Repricing tests and 205 repository tests passed. The sealed
holdout was untouched.
