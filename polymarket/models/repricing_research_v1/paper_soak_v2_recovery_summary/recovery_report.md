# Second 24-Hour Repricing Paper Soak v1 Recovery

Recovery status: `RECOVERED_DESCRIPTIVE_ONLY`

Interruption classification: **Interrupted by external power loss before
scheduled completion.** The raw public session was preserved byte-for-byte.
On recovery, an orphan producer was still appending to the existing session;
it was stopped without graceful finalization at `2026-06-30T18:15:41Z` to
honor the instruction not to resume the soak. No `session_completed` record was
written or synthesized.

The session contains 691,284 complete JSONL records and no malformed or partial
line. Its final record is capture checkpoint 40,638 at
`2026-06-30T18:15:38.155862+00:00`, line 691,284 and byte offset 324,528,106.
The immutable session SHA-256 is
`491a5363051e5ed033513d85a22bb6bc5c9a205faf1d5cdad2fe753b9dbb526f`.

The captured span contains 40,638 of 43,200 planned two-second checkpoints
(94.069444%) over 81,273.99968 seconds. Reference coverage was 99.852358%,
market-point coverage was 99.137303%, and the largest checkpoint gap was
891.868253 seconds. Replay classified the capture `INSUFFICIENT_DATA`, with
807 completed windows, eight v5 opportunities, 99.85% reference coverage, and
0.86% data gaps.

Frozen repricing export reconstructed 84 signals: BTC / ETH / SOL 14 / 30 /
40 and YES / NO 35 / 49. There were 58 wins (69.047619%), after-slippage
expectancy was +0.0383214286 per signal, after-slippage P&L was +3.219,
before-slippage P&L was +4.899, and maximum drawdown was 0.45. Exits were 58
repricing targets, 23 stop losses, and three timeouts. Average favorable
repricing was +0.243309524 and average adverse movement was -0.252452381.

Replay and export were each repeated and matched byte-for-byte. The durable
SQLite ledger passed `integrity_check`, and its 84 signals, 84 positions, and
84 closed trades reconcile exactly with the offline export; no position
remains open. Separately, the managed runtime recorded a fail-closed
`TELEMETRY_STALLED` marker before final capture interruption. That operational
diagnostic is retained and is not reclassified as research performance.

The recovered run has analytical value because it supplies a deterministic,
reconciled 84-signal descriptive sample. It is not evidence-eligible: campaign
completion is absent, checkpoint continuity failed, and the runtime emitted a
fatal liveness marker. Frozen aggregate evidence therefore remains 172 signals,
24 observed hours, and two independent sessions, below the weak-evidence gates
of 40 hours and three valid sessions. The sealed holdout was not inspected.
All 51 Repricing tests and all 197 repository tests pass.
