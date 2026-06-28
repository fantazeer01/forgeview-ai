# Balanced Repricing Batch 002 Evidence Completion Report

Source session: `D:\ForgeViewAI\polymarket\runs\repricing_balanced_v1_batch_002\20260625_200724\session.jsonl`

## Validation Flow

- Raw events: 370,616.
- Lag measurements: 64,176.
- Candidate events after the frozen accepted-reason filter: 71.
- Validated and accepted repricing signals: 42.
- Favorable repricing signals: 34.
- Rejected after candidate admission: 29.
- Candidate disappearance after validation: 40.85%.
- Post-candidate rejections: 15 below the 60-second dataset expiry floor and
  14 overlapping an open paper position.
- Largest detector-level rejection: `polymarket_already_repriced`, 30,354
  measurements.

## Signal Results

- BTC / ETH / SOL: 8 / 12 / 22.
- YES / NO: 8 / 34.
- Signals/hour: 3.539656.
- Target-before-stop wins: 34 / 42 (80.95%).
- Simulated P&L before fees/slippage: +3.090000.
- Simulated P&L after conservative slippage: +2.250000.
- Expectancy after conservative slippage: +0.053571 per signal.
- Maximum drawdown: 0.280000.
- Exit reasons: 34 `repricing_target`, 8 `stop_loss`, 0 `timeout`.
- Horizon coverage 30s / 60s / 120s / 180s:
  100.00% / 100.00% / 83.33% / 0.00%.

## Segment Results

- BTC: 8 signals, 87.50% wins, +0.082500 expectancy.
- ETH: 12 signals, 100.00% wins, +0.075000 expectancy.
- SOL: 22 signals, 68.18% wins, +0.031364 expectancy.
- YES: 8 signals, 87.50% wins, +0.087500 expectancy.
- NO: 34 signals, 79.41% wins, +0.045588 expectancy.

## Research Questions

1. Candidate events after the frozen reason filter: **71**.
2. Events surviving full validation: **42**.
3. Valid repricing signals: **42**; **34** reached the favorable repricing
   target before the stop.
4. Opportunities disappearing after validation: **40.85%**.
5. Largest post-candidate rejection: **below the 60-second dataset expiry
   floor (15)**. Across all detector observations, the largest rejection was
   **Polymarket already repriced (30,354)**.
6. The frozen parameters do not appear too strict for collection density:
   observed density was 3.5397 signals/hour versus the preflight estimate of
   3.9184. They remain unchanged.
7. Conclusion: **INCONCLUSIVE**. Batch 002 strengthens directional development
   evidence with positive results in all three assets and both sides, but it
   does not test a precommitted random-observation comparator. Weak evidence
   also still lacks the required 40 observed hours and 3 independent sessions.

## Validation

- Campaign completeness: `complete`, 100.0%.
- Observation continuity: `continuous`, 100.0% checkpoints.
- Expected / actual checkpoints: 21,600 / 21,600.
- Maximum checkpoint gap: 2.104670 seconds.
- Gaps over 10 / 60 / 300 seconds: 0 / 0 / 0.
- Fatal capture errors: 0.
- Replay compatibility: verified.
- Deterministic export: verified by two identical exports.
- Frozen parameters unchanged: true.
- Holdout: sealed and not inspected.

## Evidence Status

Batch 002 is a second independent positive development session, but it does
not independently pass weak evidence gates for signal count, observed hours,
independent sessions, per-asset counts, or YES-side count. This result is not
an edge claim and does not authorize parameter changes, holdout evaluation,
production modelling, live trading, or another capture.
