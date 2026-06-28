# Polymarket Repricing Research v1

Status: Implemented  
Date: June 28, 2026
Scope: Development-only research module, separate from outcome prediction

## Purpose

Repricing Research v1 studies whether external BTC, ETH, and SOL moves predict
short-term Polymarket contract repricing within the next 30 to 180 seconds.
It does not predict final UP/DOWN market resolution.

The research hypothesis is:

1. external crypto price moves sharply;
2. the Polymarket YES/NO contract has not fully repriced;
3. a paper entry on the lagging side can exit after probability repricing;
4. the position normally exits before expiry and does not rely on final
   resolution.

This is not live trading, not production modelling, and not holdout
evaluation.

## Separation From Outcome Prediction

The existing outcome-prediction pipeline remains intact. Repricing Research v1
does not write to canonical training, validation, or holdout paths. It does
not inspect sealed holdout outcomes. It does not modify the frozen validation
protocol.

The module lives under:

- `polymarket/repricing_research/`

Development replay outputs live under:

- `polymarket/models/repricing_research_v1/`

## Dataset Schema

Each repricing row is one paper entry opportunity and contains:

- `entry_timestamp`
- `asset`
- `market_id`
- `side`
- `yes_price_at_entry`
- `no_price_at_entry`
- `side_price_at_entry`
- `external_price_move`
- `external_return_5s`
- `external_return_15s`
- `external_return_30s`
- `external_return_60s`
- `momentum`
- `quote_age_seconds`
- `repricing_velocity`
- `repricing_acceleration`
- `spread_compression`
- `book_imbalance`
- `cross_asset_movement`
- `time_to_expiry_seconds`
- `lag_score`
- `polymarket_price_move_after_30s`
- `polymarket_price_move_after_60s`
- `polymarket_price_move_after_120s`
- `polymarket_price_move_after_180s`
- `max_favorable_excursion`
- `max_adverse_excursion`
- `time_to_repricing_seconds`
- `simulated_exit_timestamp`
- `simulated_exit_seconds`
- `simulated_exit_price`
- `simulated_exit_reason`
- `simulated_pnl_before_slippage`
- `simulated_pnl_after_slippage`
- `repriced_favorably`
- `source_session`

`repriced_favorably` is true when the selected side reaches the configured
repricing target before timeout. It is independent of final market outcome.

## Feature Groups

The v1 row schema includes:

- external returns over 5, 15, 30, and 60 seconds;
- momentum from short-minus-long external return;
- quote age;
- repricing velocity;
- repricing acceleration;
- spread compression;
- book imbalance;
- cross-asset movement from synchronized YES dispersion;
- time to expiry;
- Polymarket lag score.

## Shadow Strategy Simulator

The simulator is paper-only. It never creates orders, uses wallets, connects
private keys, or requires authenticated clients.

Entry condition:

- an existing lag measurement indicates `UP` or `DOWN`;
- the measurement reason is either `qualified_external_move_not_repriced` or
  `confidence_below_threshold`;
- the market has enough time remaining for an exit attempt;
- no paper position is already open for the same market and side.

Exit condition:

- `repricing_target`: side price moves favorably by the configured target;
- `stop_loss`: side price moves adversely by the configured stop amount;
- `timeout`: no target or stop is reached before the configured holding limit
  or pre-expiry boundary.

Default parameters:

- repricing target: 0.03 contract-price points;
- stop loss: 0.03 contract-price points;
- maximum holding time: 180 seconds;
- conservative slippage: 0.02 contract-price points per signal.

## Metrics

The simulator reports:

- number of signals;
- win rate;
- average favorable repricing;
- average adverse move;
- simulated P&L before fees and slippage;
- simulated P&L after conservative slippage;
- max drawdown;
- expectancy per signal;
- signals per hour.

These are paper diagnostics only. They are not alpha claims.

## Initial Replay

A short development replay was run against the two completed schema-v1
microstructure sessions:

- `polymarket/runs/microstructure_development_v1/20260623_120611/session.jsonl`
- `polymarket/runs/microstructure_development_v1_batch_002/20260623_214015/session.jsonl`

Output:

- `polymarket/models/repricing_research_v1/short_replay/repricing_labels.csv`
- `polymarket/models/repricing_research_v1/short_replay/simulation_summary.json`

Result:

- signals: 28;
- wins: 16;
- win rate: 57.14%;
- average favorable repricing: 0.3265;
- average adverse move: -0.1164;
- simulated P&L before fees/slippage: 0.9665;
- simulated P&L after conservative slippage: 0.4065;
- max drawdown: 0.4050;
- expectancy per signal: 0.0145;
- signals per hour: 2.1333.

This result shows that existing microstructure sessions are sufficient to
exercise the repricing label and simulator code. They are not sufficient to
prove a strategy.

## Data Sufficiency Audit

The Repricing Research v1 Data Sufficiency Audit is stored under:

- `polymarket/models/repricing_research_v1/data_sufficiency_audit/`

Required artifacts:

- `data_sufficiency_report.md`
- `data_sufficiency_report.json`
- `signal_summary.csv`
- `sample_size_targets.csv`
- `evidence_gate_definition.json`

Current audited sample:

- evidence level: `INSUFFICIENT_SMOKE_ONLY`;
- total signals: 28;
- observed hours: 13.1255;
- signals per hour: 2.1333;
- signals by asset: 5 BTC, 8 ETH, 15 SOL;
- signals by side: 5 YES, 23 NO;
- exits: 16 repricing target, 8 stop loss, 4 timeout;
- win rate: 57.14%;
- after-slippage P&L: 0.4065;
- after-slippage expectancy: 0.0145 per signal;
- max drawdown: 0.4050;
- per-signal after-slippage standard deviation: 0.0948;
- per-signal after-slippage variance: 0.0090;
- horizon coverage: 30s 100.0%, 60s 67.86%, 120s 64.29%, 180s 0.0%.

Current sufficiency:

- diagnostics: sufficient;
- model development: insufficient;
- shadow strategy validation: insufficient;
- edge claims: prohibited.

The aggregate smoke result is positive, but it is not stable enough to advance:

- YES expectancy is 0.1200, but NO expectancy is -0.0084;
- BTC expectancy is 0.0890, ETH expectancy is -0.0094, and SOL expectancy is
  0.0024;
- the sample is too small and too imbalanced by asset and side;
- the 180-second forward horizon has no full coverage in the current rows.

## Evidence Gates

Weak development evidence requires all of:

- at least 100 signals;
- at least 40 observed hours;
- at least 3 independent sessions;
- at least 25 signals per asset;
- at least 35 signals per side;
- after-slippage expectancy at least 0.005;
- max drawdown no more than 2.5x total after-slippage P&L;
- positive expectancy overall and in at least 2 of 3 assets;
- no side worse than -0.005 expectancy.

Moderate development evidence requires all of:

- at least 300 signals;
- at least 120 observed hours;
- at least 6 independent sessions;
- at least 75 signals per asset;
- at least 100 signals per side;
- after-slippage expectancy at least 0.008;
- max drawdown no more than 1.5x total after-slippage P&L;
- positive expectancy in all assets and both sides;
- positive expectancy in at least 4 chronological folds.

Strong development evidence requires all of:

- at least 1,000 signals;
- at least 400 observed hours;
- at least 20 independent sessions;
- at least 250 signals per asset;
- at least 350 signals per side;
- after-slippage expectancy at least 0.010 after stress;
- max drawdown no more than 1.0x total after-slippage P&L;
- positive stress results in all assets and both sides;
- positive expectancy in at least 80% of chronological folds;
- no single asset or session contributes more than 40% of total P&L.

Repricing edge claims remain prohibited until strong development evidence is
met, the strategy and stress assumptions are frozen, and a separate untouched
or prospective repricing validation period succeeds once under executable
cost assumptions.

## Evidence Collection Plan v1

The Repricing-Focused Public Evidence Collection Plan v1 is stored under:

- `polymarket/models/repricing_research_v1/evidence_collection_plan_v1/`

Required artifacts:

- `evidence_collection_plan.md`
- `evidence_collection_plan.json`
- `signal_generation_analysis.csv`
- `evidence_roadmap.csv`
- `collection_gate_definition.json`

Current signal-generation bottlenecks:

- the smoke replay has only 28 signals over 13.1255 observed hours, or 2.1333
  signals/hour;
- BTC / ETH / SOL counts are 5 / 8 / 15, so BTC and ETH are underrepresented;
- YES / NO counts are 5 / 23, making YES-side scarcity the binding collection
  constraint;
- the two existing schema-v1 sessions produced 63,891 lag measurements, but
  only 87 confidence-below-threshold lag events and zero fully qualified lag
  events;
- non-overlapping paper-position rules compressed those 87 candidate lag
  events to 28 paper entries;
- current forward-horizon coverage is incomplete, especially at 120 seconds
  and 180 seconds.

Lag reason distribution in the two existing sessions:

- external move below threshold: 37,843;
- Polymarket already repriced: 19,565;
- near expiry insufficient time: 6,396;
- confidence below threshold: 87;
- qualified external move not repriced: 0.

Planning signal-rate estimates:

- current strict baseline: 2.13 signals/hour;
- complete market-lifecycle capture with unchanged replay rules: about 3.0
  signals/hour;
- precommitted threshold-sweep stratum after freezing density and balance
  rules: about 4.5 signals/hour;
- separate short-horizon near-expiry stratum: about 6.0 signals/hour, but it
  must remain tagged separately;
- additional longer expiry horizons: about 1.5 incremental signals/hour until
  measured.

Collection roadmap:

- weak evidence count-only target: about 4 independent 12-hour sessions at the
  current strict signal rate;
- weak evidence balance-adjusted target: about 8 independent 12-hour sessions
  because YES-side count is binding;
- moderate evidence count-only target: about 12 independent 12-hour sessions;
- moderate evidence balance-adjusted target: about 22 independent 12-hour
  sessions;
- strong development count-only target: about 40 independent 12-hour sessions;
- strong development balance-adjusted target: about 77 independent 12-hour
  sessions.

Collection gates:

- pause and review if signal density remains below 1.0 signal/hour after any
  24 observed hours;
- healthy strict-baseline density is at least 2.0 signals/hour;
- preferred post-threshold-audit density is at least 3.0 signals/hour;
- 30s and 60s forward-horizon coverage should be at least 95%;
- 120s forward-horizon coverage should be at least 90%;
- 180s forward-horizon coverage should be at least 80% where time to expiry
  permits, otherwise the row must remain in a tagged short-horizon stratum;
- every accepted collection session must have `session_completed`, no fatal
  capture errors, deterministic replay, deterministic export, checkpoint
  coverage at least 95%, no checkpoint gap above 300 seconds, and preferred
  temporal coverage of at least 99%.

The next active repricing task is a no-capture threshold sensitivity audit on
existing public sessions. Any future collection stratum must be selected for
signal density, BTC/ETH/SOL balance, YES/NO balance, and horizon coverage, not
for maximizing historical paper P&L.

## Threshold Sensitivity Audit v1

The Repricing Threshold Sensitivity Audit v1 is stored under:

- `polymarket/models/repricing_research_v1/threshold_sensitivity_audit_v1/`

Required artifacts:

- `threshold_audit_report.md`
- `threshold_audit_report.json`
- `threshold_sensitivity.csv`
- `stratum_comparison.csv`
- `recommended_collection_stratum.json`

Audit constraints:

- existing public sessions only;
- no sealed holdout outcome inspection;
- no holdout evaluation;
- no new capture;
- no production model training;
- no validation protocol changes;
- no use of paper P&L as the optimization target;
- no change to frozen evidence gates.

Current persisted smoke density remains:

- 28 signals;
- 2.1333 signals/hour;
- BTC / ETH / SOL: 5 / 8 / 15;
- YES / NO: 5 / 23.

Recomputed audit observations:

- 64,130 candidate observations were reconstructed from the two existing
  public schema-v1 sessions;
- dominant detector-level removal filter:
  `external_move_below_threshold`, 36,465 observations;
- strongest density filter overall: requiring full 180-second horizon coverage,
  which removes every current signal;
- strongest entry-admission density lever: `external_move_threshold_bps`;
- YES scarcity is caused primarily by directional external-move distribution
  after strict admission filters;
- BTC/ETH scarcity is caused by asset-level candidate density after strict
  thresholds, with BTC lowest and SOL highest in the persisted smoke sample.

Collection strata:

- conservative: 48 outcome-free overlap-adjusted signals, 3.0833 signals/hour,
  BTC / ETH / SOL 14 / 16 / 18, YES / NO 9 / 39, candidate retention 0.4054%;
- balanced: 61 outcome-free overlap-adjusted signals, 3.9184 signals/hour,
  BTC / ETH / SOL 17 / 20 / 24, YES / NO 14 / 47, candidate retention 0.5769%;
- aggressive: 124 outcome-free overlap-adjusted signals, 7.9652 signals/hour,
  BTC / ETH / SOL 28 / 33 / 63, YES / NO 44 / 80, candidate retention 1.1679%.

Recommended future collection stratum:

- name: `balanced`;
- external move threshold: 6 bps;
- repricing ratio: 0.65;
- minimum confidence: 0.45;
- minimum dataset expiry: 60 seconds;
- maximum holding window: 180 seconds;
- accepted reasons: `qualified_external_move_not_repriced` and
  `confidence_below_threshold`;
- expected horizon coverage: 30s 100.0%, 60s 98.36%, 120s 80.33%, 180s 0.0%.

The balanced stratum is selected for future collection preflight because it
improves signal density and balance without selecting on historical paper P&L.
It is not an edge claim and does not authorize capture by itself.

## Balanced Collection Preflight v1

Balanced Repricing Evidence Collection Preflight v1 is stored under:

- `polymarket/models/repricing_research_v1/balanced_collection_preflight_v1/`

Required artifacts:

- `preflight_report.md`
- `preflight_report.json`
- `balanced_stratum_config.json`
- `expected_artifacts.json`
- `launch_command.txt`

Preflight result:

- operational status: `READY_FOR_AUTHORIZED_LAUNCH`;
- campaign launched by preflight task: no;
- Windows AC sleep timeout: 0 seconds;
- Windows AC hibernate timeout: 0 seconds;
- competing `python -m polymarket.edge_engine_v5 capture` process: none;
- stale lock: none;
- free disk space at preflight: approximately 391.469 GB;
- separated output paths verified.

Future 12-hour balanced run plan:

- duration: 43,200 seconds;
- poll interval: 2 seconds;
- discovery interval: 5 seconds;
- expected checkpoints: 21,600;
- expected signals: approximately 47.02;
- estimated total artifacts: approximately 205 MB;
- minimum recommended free space: 1 GB;
- capture output root: `polymarket/runs/repricing_balanced_v1/`;
- post-run model output root:
  `polymarket/models/repricing_research_v1/balanced_collection_batch_001/`;
- dedicated data copy path:
  `polymarket/data/repricing_research_balanced_batch_001/`.

Future launch command, for an explicitly authorized task only:

```powershell
python -m polymarket.edge_engine_v5 capture --assets BTC ETH SOL --duration 43200 --poll-interval 2 --discovery-interval 5 --output-root polymarket/runs/repricing_balanced_v1 --no-mock-fallback --min-completed-windows 1 --min-shadow-trades 1 --min-entry-seconds 60 --external-move-threshold-bps 6 --repricing-ratio 0.65 --min-confidence 0.45
```

Post-run replay command template:

```powershell
python -m polymarket.edge_engine_v5 replay --session polymarket/runs/repricing_balanced_v1/<YYYYMMDD_HHMMSS>/session.jsonl --output polymarket/models/repricing_research_v1/balanced_collection_batch_001/capture_replay
```

Post-run repricing dataset command template:

```powershell
python -m polymarket.repricing_research --session polymarket/runs/repricing_balanced_v1/<YYYYMMDD_HHMMSS>/session.jsonl --output polymarket/models/repricing_research_v1/balanced_collection_batch_001/repricing_dataset --timeout 180 --min-seconds-to-expiry 60 --signal-reason qualified_external_move_not_repriced --signal-reason confidence_below_threshold
```

Future validation gates:

- campaign completeness: `session_completed` present and completeness status
  `complete`;
- observation continuity: at least 95% checkpoint coverage, no gap above 300
  seconds, no fatal capture errors;
- replay compatibility: v5 replay succeeds;
- deterministic export: repricing dataset export runs twice and hashes match;
- signal count, asset balance, and side balance are measured against existing
  evidence gates, which remain unchanged.

## Balanced Repricing Evidence Batch 001

Balanced Repricing Evidence Collection Batch 001 is stored under:

- source session:
  `polymarket/runs/repricing_balanced_v1/20260624_154206/session.jsonl`;
- capture replay:
  `polymarket/models/repricing_research_v1/balanced_collection_batch_001/capture_replay/`;
- repricing dataset:
  `polymarket/models/repricing_research_v1/balanced_collection_batch_001/repricing_dataset/`;
- repeated deterministic export:
  `polymarket/models/repricing_research_v1/balanced_collection_batch_001/repricing_dataset_repeat/`;
- dedicated data copy:
  `polymarket/data/repricing_research_balanced_batch_001/`;
- summary artifacts:
  `polymarket/models/repricing_research_v1/balanced_collection_batch_001/batch_001_summary.json`
  and
  `polymarket/models/repricing_research_v1/balanced_collection_batch_001/batch_001_summary.md`.

Campaign integrity:

- duration: 43,200 seconds;
- campaign completeness: `complete`;
- coverage percentage: 100.0%;
- `session_completed`: present;
- expected / actual checkpoints: 21,600 / 21,600;
- observation continuity: `continuous`;
- checkpoint coverage: 100.0%;
- maximum checkpoint gap: 2.035487 seconds;
- gaps over 10 / 60 / 300 seconds: 0 / 0 / 0;
- fatal capture errors: 0;
- v5 replay compatibility: verified.

Dataset and deterministic export:

- deterministic export: verified;
- `repricing_labels.csv` SHA-256:
  `0c0472c46a14324b61fb2b954dced082dd6f082695bddd51be52dd3daf5f128a`;
- `simulation_summary.json` SHA-256:
  `028ae5e5f5a27d669eeb813370066c6bedc6b2b35132ab5ec50eedce9b020257`;
- source `session.jsonl` SHA-256:
  `1126972b0adcc31741e41d22bb89d3d999531077b0cd40836b20885b4103e8a0`.

Signal results:

- signals: 130;
- BTC / ETH / SOL: 37 / 29 / 64;
- YES / NO: 59 / 71;
- signals/hour: 11.2706;
- target-before-stop wins: 76;
- win rate: 58.46%;
- simulated P&L before fees/slippage: +4.203;
- simulated P&L after conservative slippage: +1.603;
- expectancy after conservative slippage: +0.012331 per signal;
- max drawdown: 0.875;
- exit reasons: 76 `repricing_target`, 45 `stop_loss`, 9 `timeout`;
- horizon coverage 30s / 60s / 120s / 180s:
  99.23% / 96.92% / 76.15% / 0.0%.

Evidence gate status:

- signal count >= 100: passed;
- signals per asset >= 25: passed;
- signals per side >= 35: passed;
- after-slippage expectancy >= 0.005: passed;
- max drawdown <= 2.5x after-slippage P&L: passed;
- observed hours >= 40: failed;
- independent sessions >= 3: failed.

Evidence level:
`SINGLE_SESSION_POSITIVE_BELOW_WEAK_EVIDENCE_HOURS_AND_SESSION_GATES`.

Weak development evidence is not reached. The result remains development-only
and does not authorize production model training, holdout evaluation, live
trading, wallet/private-key access, or changes to the frozen balanced stratum.

## Balanced Repricing Evidence Batch 002

Balanced Repricing Evidence Collection Batch 002 is stored under:

- source session:
  `polymarket/runs/repricing_balanced_v1_batch_002/20260625_200724/session.jsonl`;
- capture replay:
  `polymarket/models/repricing_research_v1/balanced_collection_batch_002/capture_replay/`;
- primary and repeated repricing exports:
  `polymarket/models/repricing_research_v1/balanced_collection_batch_002/repricing_dataset/`
  and `repricing_dataset_repeat/`;
- dedicated data copy:
  `polymarket/data/repricing_research_balanced_batch_002/`;
- final report:
  `polymarket/models/repricing_research_v1/balanced_collection_batch_002/batch_002_summary.md`.

Frozen settings were unchanged: 6 bps external move, 0.65 repricing ratio,
0.45 minimum confidence, 60-second minimum dataset expiry, 180-second maximum
holding window, and the two precommitted accepted reasons.

Validation results:

- campaign completeness: `complete`, 100.0%;
- observation continuity: `continuous`, 21,600 / 21,600 checkpoints;
- maximum checkpoint gap: 2.104670 seconds;
- fatal capture errors: 0;
- replay compatibility: verified;
- deterministic export: verified;
- `repricing_labels.csv` SHA-256:
  `f414c673c47a39faeef98635ec6e694fbb14e1eadfcb4b57034ee8268edc84b0`;
- `simulation_summary.json` SHA-256:
  `a94ce3bd5c6010a6b657b9307e01e30cefb0bf67a1bbd686ccfcf8d669d083a4`;
- source session SHA-256:
  `30dda21d57ecb25ed6adbc2a511561dd7408950998aeffcadbb19663161a27bd`.

Candidate flow:

- 64,176 lag measurements;
- 71 candidates after the frozen accepted-reason filter;
- 42 validated and accepted repricing signals;
- 29 post-candidate rejections, or 40.85%;
- 15 rejected below the 60-second dataset expiry floor;
- 14 rejected by the non-overlapping paper-position rule;
- 34 of 42 accepted signals reached the repricing target before the stop.

Signal results:

- BTC / ETH / SOL: 8 / 12 / 22;
- YES / NO: 8 / 34;
- signals/hour: 3.539656;
- win rate: 80.95%;
- simulated P&L before fees/slippage: +3.090000;
- simulated P&L after conservative slippage: +2.250000;
- after-slippage expectancy: +0.053571 per signal;
- maximum drawdown: 0.280000;
- exits: 34 `repricing_target`, 8 `stop_loss`, 0 `timeout`;
- horizon coverage 30s / 60s / 120s / 180s:
  100.00% / 100.00% / 83.33% / 0.00%.

Per-asset and side after-slippage expectancy was positive in every observed
segment. BTC / ETH / SOL expectancy was +0.082500 / +0.075000 / +0.031364;
YES / NO expectancy was +0.087500 / +0.045588.

Conclusion: `INCONCLUSIVE`.

Batch 002 strengthens directional development evidence but does not test a
precommitted random-observation comparator, so it cannot decide whether frozen
conditions identify genuine opportunities better than random observation.
Weak evidence also still lacks the required observed hours and independent
sessions. The frozen settings remain unchanged, the holdout remains sealed,
and no additional capture or edge claim is authorized.

## Balanced Repricing Random Baseline Sprint v1

The random-baseline falsification artifacts are stored under:

- `polymarket/models/repricing_research_v1/balanced_random_baseline_v1/random_baseline_results.csv`;
- `polymarket/models/repricing_research_v1/balanced_random_baseline_v1/random_baseline_summary.json`;
- `polymarket/models/repricing_research_v1/balanced_random_baseline_v1/random_baseline_report.md`.

Predefined baseline:

- 1,000 deterministic trials with seed `20260628`;
- exactly 172 signals per trial;
- exact distribution match by source batch, BTC/ETH/SOL, YES/NO, and
  60-second expiry bucket;
- random entry timing sampled uniformly from eligible public snapshots;
- 60-second minimum expiry, 180-second maximum hold, 0.03 target, 0.03 stop,
  0.02 conservative slippage, and no overlapping same-market/same-side paper
  position;
- identical signal density of 7.166667 signals/hour by design.

Detector result across Batch 001 and Batch 002:

- sample size: 172 signals over 24.000000 observed hours;
- wins: 110;
- win rate: 63.9535%;
- after-slippage P&L: +3.853000;
- after-slippage expectancy: +0.022401;
- maximum drawdown: 0.875000.

Random baseline result:

- mean win rate: 47.8692%;
- 95% win-rate interval: 40.6977% to 54.6512%;
- mean after-slippage expectancy: -0.019607;
- 95% expectancy interval: -0.029563 to -0.011226;
- mean maximum drawdown: 3.495447;
- 95% maximum-drawdown interval: 2.097862 to 5.165125;
- no random trial matched detector expectancy or win rate;
- one-sided exceedance probability: 0.000999 for each metric.

Observed differences:

- win rate: +16.0843 percentage points versus random mean;
- expectancy: +0.042008 versus random mean;
- detector drawdown: 2.620447 below random mean;
- signal density: no difference by construction.

Conclusion: `SUPPORTED` under this predefined development-only baseline. The
observed positive expectancy is not explained by random entry timing alone in
the two captured sessions.

This is not a proven repricing edge. The result remains vulnerable to the two
adjacent sessions, small independent-session count, serial correlation,
uniform snapshot weighting, alternative random-baseline definitions,
development selection bias, market-regime persistence, midpoint-like paper
prices, and absent executable fills, queue position, depth consumption, fees,
and live latency. Frozen parameters and evidence gates remain unchanged; the
holdout remains sealed.

## Continuous Paper Trading Readiness Sprint v1

Readiness artifacts are stored under:

- `polymarket/models/repricing_research_v1/paper_trading_readiness_v1/repricing_paper_trading_gap.md`;
- `polymarket/models/repricing_research_v1/paper_trading_readiness_v1/repricing_mvp_components.csv`;
- `polymarket/models/repricing_research_v1/paper_trading_readiness_v1/repricing_launch_plan.md`.

Readiness classification:

- 18 required components reviewed;
- 4 `READY`;
- 7 `MINOR WORK`;
- 7 `MAJOR WORK`;
- 13 launch blockers;
- current status: `NOT_READY`;
- estimated effort: 9-11 engineer-days plus a 24-hour supervised public paper
  soak;
- earliest continuously running MVP: engineer-day 10;
- earliest initial readiness evidence: day 11.

Ready foundations include public market discovery, async BTC/ETH/SOL reference
and quote feeds, frozen lag measurement, append-only raw evidence, checkpoint
continuity, failure recording, and deterministic replay.

The primary blocker is semantic: v5 live shadow execution is generic
score-based simulation, not frozen repricing execution. It does not admit
`confidence_below_threshold` as a paper signal, uses different slippage and
stake semantics, closes by score or session end, and does not implement the
frozen 0.03 target, 0.03 stop, 180-second timeout, or 0.02 conservative
slippage causally.

The smallest approved architecture keeps detector code unchanged and adds:

- a frozen causal admission consumer;
- a transactional SQLite signal, position, trade, and cursor ledger;
- target/stop/timeout close processing on each subsequent quote;
- raw-event replay after the last committed cursor on restart;
- durable duplicate and overlap constraints;
- UTC daily statistics and equity summaries;
- heartbeat, stale-feed, exception, disk, and write telemetry;
- an optional persisted notification outbox and outbound Telegram adapter;
- single-instance supervision, session rotation, and crash/soak tests.

No continuous run is authorized until the causal paper core demonstrates
offline replay equivalence and crash-safe idempotency. Frozen parameters,
evidence gates, and holdout policy remain unchanged.

## Restart-Safe Paper Core v1

The local restart-safe execution foundation is implemented under
`polymarket/repricing_research/paper_core.py`. It is separate from v5 generic
shadow execution and preserves the frozen repricing contract unchanged.

Durability rules:

- journal each raw event before applying a state transition;
- atomically commit admission, position state, realized paper PnL, and the
  processed cursor;
- replay only unprocessed journal rows after restart;
- enforce unique signal, position, and close identities in SQLite;
- enforce one open position per market and side in SQLite;
- restore open positions and never reopen a closed signal;
- verify the frozen strategy fingerprint and fail closed on mismatch;
- close on target, stop, timeout, or v5 lifecycle expiry using a durable quote.

Validation passed for open-position restoration, duplicate suppression,
closed-position idempotency, nine injected interruption cases, lifecycle
expiry, strategy mismatch refusal, and exact fixture equivalence with the
offline simulator. Eleven repricing tests and 147 repository tests pass.
Artifacts are under
`polymarket/models/repricing_research_v1/restart_safe_paper_core_v1/`.

This does not authorize continuous operation. A read-only v5 stream adapter,
process supervision, rotation, telemetry, daily statistics, and sustained soak
validation remain missing. No campaign, Telegram integration, wallet
connection, real order, holdout access, or parameter change occurred.

## v5 Event Stream Integration v1

The restart-safe paper core now consumes existing v5 `session.jsonl` streams
through `polymarket/repricing_research/v5_stream_adapter.py`.

The adapter:

- tails only complete UTF-8 JSONL records and defers a partial trailing write;
- validates required v5 event fields and timezone-aware chronological order;
- persists stable source identity and immutable first-event metadata;
- verifies all committed source events against the raw journal after restart;
- resumes appended events after the durable source cursor;
- fails closed on source replacement, committed-prefix mutation, truncation,
  malformed complete input, invalid ordering, or unsupported assets;
- preserves raw detector events and the frozen paper-core fingerprint without
  recomputing signals or changing thresholds;
- provides lineage from paper position/trade through signal and source event
  index to the canonical raw event and absolute source path.

Validation covers duplicate delivery, open and closed restart recovery,
appended resume, invalid and partial records, source replacement/truncation,
DOWN-to-NO timeout/slippage behavior, and equality between interrupted and
uninterrupted ingestion. Twenty repricing tests and 159 repository tests
pass. Artifacts are under
`polymarket/models/repricing_research_v1/v5_paper_core_integration_v1/`.

This adapter is not a process supervisor and does not authorize continuous
operation. A single-instance runtime loop, graceful shutdown, session
rotation, heartbeat/stale-feed/disk/write telemetry, daily statistics, and a
supervised soak remain missing. No detector, threshold, campaign, holdout,
Telegram, wallet, or real-money execution path changed.

## Managed Paper Runtime Loop v1

The paper-only runtime entrypoint is implemented in
`polymarket/repricing_research/paper_runtime.py` and installed as
`repricing-paper-runtime`.

The runtime:

- owns one v5 stream adapter and restart-safe paper core;
- polls continuously or under explicit `--max-polls` / runtime bounds;
- requires a bound in `--dry-run` mode;
- restores open positions and pending journal state before polling;
- persists all entries and exits through the existing transactional ledger;
- treats duplicate source replay as idempotent;
- handles Ctrl+C and termination as graceful stop requests where feasible;
- closes SQLite without force-closing open positions;
- atomically replaces health JSON after startup, each poll, failure, and stop;
- fails closed and preserves the ledger when complete stream input is invalid.

Health telemetry includes runtime start/stop, last poll/event timestamp,
received/accepted/rejected and duplicate event counts, positions opened/closed,
recovered/current open positions, completed polls, last error, source/database
paths, frozen strategy fingerprint, and dry-run state. These are operational
counters, not detector or performance optimization metrics.

Eight runtime tests pass, including byte-deterministic bounded dry-run output
under a fixed clock. The combined repricing suite passes 28 tests and the full
repository suite passes 167 tests. Artifacts are under
`polymarket/models/repricing_research_v1/paper_runtime_v1/`.

Continuous unattended operation remains unauthorized. The required Repricing
successor is **Repricing Paper Runtime Supervision And Soak Sprint v1**, which
must address single-instance supervision, restart policy, session rotation,
stale-feed/disk/write controls, and supervised soak evidence. The global
repository NEXT_TASK remains the wallet branch task under the one-task policy.

No detector, threshold, campaign, holdout, Telegram, wallet/private-key, order
placement, or real-money execution path changed.

## Continuous Paper Trading MVP v1

The continuous paper-only entrypoint is implemented in
`polymarket/repricing_research/runtime_mvp.py` and installed as:

```text
repricing-runtime-mvp --config <runtime.json>
```

One JSON configuration controls the v5 session path, state/output directories,
poll interval, optional dry-run bounds, and restart budget/backoff. Runtime
paths are derived consistently for the paper ledger, lock, status, heartbeat,
daily summary, and unified JSONL log.

Startup validation requires valid configuration, holdout-separated paths, a
complete structurally valid v5 event, writable state/output directories, a
recoverable SQLite ledger, and the frozen strategy fingerprint. An OS-level
byte-range lock prevents duplicate processes and is released by the operating
system after process death.

Supervision rules are fail closed:

- explicit temporary source unavailability may restart within budget;
- malformed streams, source replacement/truncation, fingerprint mismatch,
  state-integrity failure, and unexpected exceptions do not restart;
- unclean process restart retains the prior session ID and increments restart
  count;
- Ctrl+C/termination requests graceful shutdown and never force-closes a paper
  position.

The heartbeat includes liveness, last poll/event/successful processing,
detector and paper-core state, event/signal/position counts, duplicate count,
last error, and strategy fingerprint. The UTC daily summary contains runtime
duration, events, valid/rejected signals, opened/closed/current positions,
failures, and restarts, with duration split across midnight. The unified log
records startup, health, failures, process recovery, and stop.

Eleven dedicated MVP tests pass. The combined Repricing suite passes 39 tests and
the full repository suite passes 185 tests. Committed validation outputs live
under `polymarket/models/repricing_research_v1/continuous_runtime_mvp_v1/`.

Status is `PASS_BOUNDED_DRY_RUN`; no continuous public paper run occurred. The
next Repricing task is **Run First 24-Hour Repricing Paper Soak Preflight v1**.
It must verify power, disk, source/session rotation, stale-event thresholds,
restart drills, and reconciliation before a separately authorized soak.

No detector, threshold, strategy, holdout, Telegram, wallet/private-key, order
placement, or live-money path changed.

## Missing Data

The current evidence is missing:

- a larger independent repricing-focused sample;
- balanced YES and NO signal coverage;
- balanced BTC, ETH, and SOL signal coverage;
- complete 60, 120, and 180 second forward-horizon coverage;
- full executable bid/ask exit modelling for YES and NO token sides;
- explicit fee and slippage stress grids;
- order book depth consumption for realistic position sizing;
- non-overlapping walk-forward periods for repricing labels;
- prospective shadow replay under a frozen repricing specification;
- authoritative evidence that observed repricing would be executable at the
  quoted public prices.

## Open Source Intelligence Notes

Polymarket Open Source Intelligence Audit v1 is stored under:

- `polymarket/models/open_source_intelligence_audit_v1/`

Repricing-related findings:

- `evan-kolberg/prediction-market-backtesting` is the strongest reference for
  execution-realistic backtesting assumptions: L2 market-by-price replay,
  queue-position proxy, latency, slippage, fees, maker rebates, and strategy /
  loader / runner separation.
- `pmxt-dev/pmxt` is the strongest read-only API normalization reference for
  Polymarket Gamma, CLOB, Data API, WebSocket order books/trades, and Binance
  feed normalization.
- `ent0n29/polybot` suggests that at least some profitable wallet behavior in
  BTC/ETH Up/Down markets may depend on execution edge, paired-outcome or
  complete-set-like behavior, maker fills, and decision-time book state rather
  than pure final-outcome prediction.
- `lihanyu81/polymarket_lp_tool` is useful only as passive-order risk
  vocabulary: midpoint jump pause, stable-mid confirmation, EMA/median
  filtering, fill cooldown, and max chase limits.

These findings are research inputs only. They do not authorize importing
third-party execution code, opening the sealed holdout, changing the frozen
validation protocol, launching capture campaigns, connecting wallets, or
placing orders.

## Wallet Evidence Note

Wallet Intelligence Data Ingestion v1 found four seed profiles with substantial
fast BTC/ETH/SOL Up/Down exposure in a bounded public snapshot. This supports
continuing to study wallet behavior as a hypothesis source for repricing
research, especially cheap-entry and repeated fast-market participation.

No repricing edge direction changes are authorized from this evidence. The
wallet snapshot does not expose complete trade/fill history, linked entry and
exit timestamps, average holding time, Binance-aligned entry timing, queue
position, liquidity consumption, or observation-delay risk. Any wallet-derived
repricing hypothesis must pass the existing public, leakage-controlled
repricing evidence gates before it can become a research claim.

Behavior Metrics v1 refines this note but does not change repricing
assumptions. Four seed wallets are fast crypto focused, aggregate YES/NO
behavior is balanced at 234 / 225, and `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`
is the strongest visible BTC Up/Down specialist. However, late-window behavior,
entry timing, exit timing, observation delay, and Binance alignment remain
unavailable. Wallet behavior may prioritize which public-history questions to
study next, but it does not modify repricing evidence gates or authorize a
campaign, model, holdout evaluation, or execution work.

Deep History Feasibility v1 updates the data-availability assessment only. A
bounded public path exists for wallet trade/activity history via Data API
`activity?user=<wallet>&type=TRADE`, cross-checked with `/trades`, joined to
positions, closed positions, CLOB price history, and external BTC/ETH/SOL
reference prices. This means Binance-lag alignment can be studied as a future
descriptive wallet-history question after careful timestamp joins. It does not
change repricing assumptions, authorize a new evidence campaign, prove any
edge, or make wallet behavior an execution signal.

Wallet Public Trade History Ingestion Design v1 specifies the future
Binance/reference join as a descriptive wallet-history enrichment only:
normalized wallet trade rows should join external BTC/ETH/SOL reference
snapshots by asset class and timestamp after the public activity row is
normalized and provenance-hashed. This plan does not alter repricing evidence
gates, does not merge wallet rows into repricing validation data, and does not
authorize capture, live execution, model training, or holdout evaluation.

Wallet Public Trade History Ingester Fixture Implementation v1 implements the
local fixture normalizer and validation gates for saved public trade rows only.
It improves provenance and classification readiness for future descriptive
wallet-history joins, but it does not add Binance/reference data, modify
repricing assumptions, alter evidence gates, launch a campaign, or create an
execution signal.

Wallet Public Trade History Bounded Public Smoke v1 confirms that bounded
public wallet trade rows can be collected and normalized for all six seed
wallets. The smoke found 600 normalized rows, including 367 fast crypto rows
and BTC / ETH / SOL counts of 359 / 97 / 11. This improves wallet-history data
availability for future descriptive lifecycle and Binance/reference join
design. It does not join external reference prices yet, does not prove
Binance-lag alignment, does not change repricing evidence gates, does not
authorize a capture campaign, and does not create an execution signal.

## Safety Rules

Repricing Research v1 must not:

- inspect sealed holdout outcomes;
- run holdout evaluation;
- train production models;
- modify the frozen validation protocol;
- merge repricing rows into canonical outcome-prediction training data;
- implement real trading;
- connect wallets, private keys, or authenticated order placement.
