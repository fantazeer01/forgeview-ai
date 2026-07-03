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

## Pre-Soak Consolidation v1

Repricing pre-soak engineering is complete with verdict
`READY_FOR_24H_SOAK`.

Production-mode preflight now enforces:

- Windows AC sleep and hibernate disabled when required;
- configurable minimum free disk, currently 2 GiB;
- writable state and output directories with measured write latency;
- complete valid v5 source input and automatic newest-session discovery;
- recoverable SQLite state and the frozen strategy fingerprint;
- strict separation from sealed/holdout paths.

The managed runtime may use `session_root` instead of a fixed session file. It
selects timestamped `*/session.jsonl` sources, excludes the copied `latest`
directory, and rotates to a newer source without replacing the paper ledger.
Rotation was fixture-validated while one paper position remained traceable and
closed exactly once.

Runtime safety thresholds are 30 seconds maximum source-event age and 500 ms
maximum health-write latency. Either breach stops closed. Fault injection
confirmed both guards.

Required restart drills all pass:

- open-position restart preserves one open position without duplication;
- interruption after position creation replays the pending event and converges
  to one open position;
- graceful shutdown preserves the open position and a subsequent runtime closes
  it exactly once.

Measured readiness: AC sleep/hibernate 0/0 seconds, 35,648,344,064 bytes free,
0.694 ms marker write latency, all nine readiness gates passed, no remaining
engineering blocker. Forty-five Repricing tests and 191 repository tests pass.
Artifacts are under
`polymarket/models/repricing_research_v1/pre_soak_v1/`.

At pre-soak completion, the next Repricing task was **Run First 24-Hour
Repricing Paper Soak v1**. That launch state is superseded by the completed soak
result below.

No detector, threshold, strategy, holdout, wallet/private-key, Telegram,
order-placement, or live-money behavior changed.

## First 24-Hour Paper Soak v1

The first authorized public-only Repricing paper soak completed with verdict
`FAILED_OPERATIONAL_INTEGRITY`. Preflight passed and the frozen strategy
fingerprint remained
`d5d389be45d472628aab06b3aeeb281593e74d48b82902e12712047c91fec010`.
Exactly one producer and one paper runtime were used.

The source session emitted `session_completed` but failed continuity with
32,540 / 43,200 checkpoints, 75.3241% coverage, an internal 4,112.812693-second
gap, and a 23,554.333577-second terminal gap. Campaign status is
`incomplete_campaign`; fatal capture errors are zero.

The live ledger retained 60 unique signals, positions, and closed trades with
SQLite integrity `ok`, no open positions, and no duplicate business keys. The
heartbeat stopped after 12,310.53587 seconds while the consumer remained
CPU-active beyond its configured 24-hour bound. Its cursor stopped at event
351,230 of 531,314. Deterministic offline replay reconstructed 73 signals, so
13 qualifying signals were not persisted by the live consumer.

Repeated replay and repeated frozen export matched byte-for-byte. Descriptive
offline metrics are:

- signals: 73;
- BTC / ETH / SOL: 13 / 17 / 43;
- YES / NO: 26 / 47;
- wins / win rate: 59 / 80.82%;
- after-slippage expectancy: +0.071432;
- after-slippage P&L: +5.2145;
- maximum drawdown: 0.22;
- exits: 59 repricing target, 11 stop loss, 3 timeout.

All 45 Repricing tests and all 191 repository tests pass.

The positive descriptive result is not admissible evidence because campaign
continuity and live signal reconciliation failed. Frozen aggregate evidence
therefore remains 172 signals, 24 observed hours, and two independent sessions.
Weak evidence remains below gate because at least 40 hours and three valid
sessions are required.

Summary artifacts are under
`polymarket/models/repricing_research_v1/paper_soak_v1_summary/`. The next task
is **Fix Repricing Runtime Backpressure And Liveness Fail-Closed v1**. No second
soak is authorized until incremental stream consumption, heartbeat liveness,
bounded shutdown, and cursor catch-up are fixture- and stress-validated.

No detector logic, threshold, strategy, holdout, model, wallet/private-key,
order-placement, or live-money behavior changed.

## Runtime Backpressure And Liveness Fix v1

The first soak failure was caused by an unbounded consume-to-EOF adapter call
against a growing session plus two `SQLite synchronous=FULL` commits per source
event. Heartbeat, source freshness, and maximum-runtime enforcement could run
only after that call returned. Capture and ledger processing therefore
continued after telemetry became unhealthy.

The paper runtime now:

- consumes at most 1,000 events per batch;
- rejects JSONL lines above one MiB;
- commits raw journal, paper transitions, and cursor once per atomic batch;
- caps uncommitted source backlog at 64 MiB;
- emits progress heartbeat diagnostics during in-flight processing;
- runs an independent 30-second progress watchdog and runtime deadline;
- rolls back an in-flight batch if liveness fails;
- writes a durable `FAILED_CLOSED` safe-shutdown marker with a fatal code;
- rejects incomplete terminal campaign or observation-continuity health;
- resumes committed-prefix verification and appended catch-up in bounded,
  exactly-once batches.

Validation passed for telemetry stall, overload, fail-closed shutdown,
incomplete terminal health, a 5,000-event healthy path, and a 5,000 + 100 event
restart/catch-up path. A bounded validation against 10,000 events from the
preserved failed-soak session completed in 0.479278 seconds at 20,864.72
events/second with no watchdog trip. All 51 Repricing tests and all 197
repository tests pass.

Artifacts are under
`polymarket/models/repricing_research_v1/runtime_backpressure_liveness_fix_v1/`.
Verdict is `READY_FOR_SECOND_24H_SOAK_PREFLIGHT`. No new capture or soak was
launched. The next task is **Run Second 24-Hour Repricing Paper Soak v1**.

The frozen strategy fingerprint, detector logic, thresholds, target, stop,
timeout, slippage, admission reasons, evidence gates, holdout boundary, and
paper-only restriction remain unchanged.

## Second 24-Hour Paper Soak Recovery

The second authorized soak is classified `RECOVERED_DESCRIPTIVE_ONLY` after an
external power interruption before scheduled completion. The raw session was
preserved without alteration and ends on a complete capture checkpoint. It has
691,284 valid JSONL records, zero invalid records, 40,638 / 43,200 checkpoints
(94.069444%), an 81,273.99968-second checkpoint span, and an 891.868253-second
largest gap. No `session_completed` event exists.

Repeated replay and repeated frozen export match byte-for-byte. Replay found
807 completed windows and eight opportunities with 99.85% reference coverage.
The descriptive repricing export contains 84 signals: BTC / ETH / SOL 14 / 30
/ 40; YES / NO 35 / 49; 58 wins; 69.047619% win rate; +0.0383214286
after-slippage expectancy; +3.219 after-slippage P&L; +4.899 before-slippage
P&L; and 0.45 maximum drawdown. Exits are 58 repricing targets, 23 stop losses,
and three timeouts. The live SQLite ledger is healthy and reconciles exactly at
84 signals, positions, and closed trades with no open position.

These are analytical results only. The source lacks terminal campaign
completion, fails continuity, and the managed runtime independently recorded a
fatal `TELEMETRY_STALLED` fail-closed marker. The interrupted run therefore
does not enter evidence aggregation. Frozen valid evidence remains 172 signals,
24.000000389 observed hours, and two independent sessions, so weak evidence
remains below the 40-hour and three-session gates.

Recovery artifacts are under
`polymarket/models/repricing_research_v1/paper_soak_v2_recovery_summary/`.
The next task is **Diagnose Repricing Runtime Telemetry Stall After Interrupted
Soak v1**. It must explain the recorded liveness failure without changing the
frozen strategy or launching another soak.

## Second Soak Host-Suspend Diagnosis

Windows power records prove that the second soak's 15-minute interruption was
host S3 sleep initiated by an Application API. Sleep began at
`2026-06-30T17:52:16.060434Z`; resume completed at
`2026-06-30T18:07:06.226392Z`. This aligns with the 900.159992-second runtime
health-log gap and the 891.868253-second source checkpoint gap. No reboot
occurred.

The previous runtime correction was partially successful: bounded atomic
ingestion, ledger durability, duplicate protection, and fail-closed behavior
all held. The ledger reconciles exactly and did not continue after the
watchdog fatal marker. Static AC timer preflight was insufficient because the
managed MVP had not activated the available Windows sleep inhibitor, and the
watchdog labeled host suspension as generic telemetry stall.

The MVP now holds `WindowsSleepInhibitor` throughout managed operation.
Watchdog scheduling gaps at least five times the processing-stall threshold are
classified `HOST_SUSPEND_DETECTED`; ordinary consumer stalls remain
`TELEMETRY_STALLED`. Both conditions remain fail closed. No detector or frozen
strategy parameter changed.

Artifact:
`polymarket/models/repricing_research_v1/soak_v2_telemetry_stall_diagnosis/`.
The next task is **Run Third 24-Hour Repricing Paper Soak v1**, subject to a
fresh passing preflight. The second soak remains descriptive and excluded from
evidence. All 53 Repricing tests and all 199 repository tests pass.

## Third 24-Hour Paper Soak

The third soak completed a full, public-only 86,400-second source capture under
the active Windows sleep inhibitor. Campaign completeness and observation
continuity passed with 43,200 checkpoints, 100% coverage, 2.105269-second
maximum gap, zero fatal capture errors, and no host power transition.

The paper runtime was bounded and healthy throughout. It stopped with no fatal
marker, watchdog trip, backlog, rejected event, duplicate, restart, or open
position. Its 175 signals, positions, and trades reconcile exactly to frozen
offline export by count, asset, side, and after-slippage P&L.

Verdict is nevertheless `FAILED_TERMINAL_DRAIN_RECONCILIATION`. The source has
741,533 records, but the durable cursor ends at index 741,528. After the final
checkpoint the producer appended three historical `shadow_trade` events whose
timestamps moved backward, then appended `session_completed`. The runtime
stopped before consuming those four records and therefore never enforced
terminal source health.

Descriptive performance is 175 signals; BTC / ETH / SOL 33 / 39 / 103; YES /
NO 82 / 93; 120 wins; 68.571429% win rate; +0.0371228571 after-slippage
expectancy; +6.4965 after-slippage P&L; and 0.77 maximum drawdown. Exits are 120
targets, 22 stops, and 33 timeouts. Replay and export are deterministic.

The third soak remains analytical only and contributes nothing to evidence.
Valid evidence remains 172 signals, 24.000000389 hours, and two sessions, below
weak evidence. Summary artifacts are under
`polymarket/models/repricing_research_v1/paper_soak_v3_summary/`.

The next task is **Fix Repricing Terminal Drain And Session Completion
Reconciliation v1**. It may not launch another soak or change the frozen
strategy. All 53 Repricing tests and all 199 repository tests pass.

## Terminal Drain And Completion Fix

The third soak's four-record terminal shortfall is reproduced and fixed. The
producer had appended terminal `shadow_trade` summaries using historical close
times after a later final checkpoint. The runtime separately stopped at its
nominal duration without waiting for producer finalization.

Terminal summary envelopes now use append time and preserve close time in the
payload. Production Repricing runtimes require a healthy `session_completed`,
drain for at most 60 seconds after nominal expiry, and succeed only after
source EOF and exact durable cursor reconciliation. Missing completion,
incomplete health, and false supervisor clean stops all fail closed under
distinct terminal error paths.

Fixtures validate 258 delayed terminal records across multiple bounded batches,
zero lost records, final batch commit, completion-marker agreement, source EOF,
and monotonic producer output. No capture or soak was launched. The frozen
detector and strategy remain unchanged.

Artifacts:
`polymarket/models/repricing_research_v1/terminal_drain_fix_v1/`.
The next task is **Run Fourth 24-Hour Repricing Paper Soak v1**, after fresh
preflight. Existing evidence remains unchanged until a complete live soak
passes every operational gate.

## Evidence Duration Protocol Review

The fourth 24-hour soak remains the correct next experiment, but canonical
24-hour repetitions are not the default for every runtime change. Current
admissible evidence is 172 signals, 24.000000389 hours, and two independent
sessions. The weak floor is 100 signals, 40 hours, and three sessions, plus the
unchanged balance, expectancy, drawdown, and stability gates.

Expected additions under the frozen balanced stratum are:

| Duration | Planned-density signals | Admissible-density signals | Aggregate hours | Weak duration gate |
|---|---:|---:|---:|---|
| 6 hours | about 24 | about 43 | about 30 | fail |
| 12 hours | about 47 | about 86 | about 36 | fail |
| 24 hours | about 94 | about 172 | about 48 | potentially pass |

Planned density is 3.9184 signals/hour; admissible Batch 001-002 density is
7.1667 signals/hour. These are planning ranges, not promises. If signals were
independent, the resulting sample sizes would reduce nominal standard error by
roughly 6-10%, 11-18%, and 20-29%, respectively, relative to 172 signals.
Within-market serial correlation and only three prospective sessions mean the
effective gain is smaller and regime confidence remains weak even if the weak
gate passes.

No known failure mode is logically restricted to appearing after hour 12.
Backpressure appeared early, terminal drain occurs at the configured endpoint,
and host suspension is exogenous. Longer operation nevertheless increases the
chance of observing host scheduling, resource-growth, rotation, UTC daily
reporting, and shutdown interactions. Those are operational endurance reasons,
not evidence that the detector edge itself needs a 24-hour unit.

Future duration selection follows D-108:

1. deterministic regression and preflight for every runtime change;
2. optional evidence-ineligible 2-hour canary only for uncovered live
   integration uncertainty;
3. 12-hour integrity validation for accumulation/rotation risk when it can
   answer the named question;
4. 24-hour canonical evidence only for daily-boundary/endurance admission or
   when it can materially advance a frozen evidence gate.

The fourth soak proceeds directly to 24 hours because the terminal failure is
reproduced by regression fixtures and a shorter valid run cannot close the
40-hour gate. Frozen evidence gates, strategy parameters, and holdout policy
remain unchanged.

## Fourth Soak Prelaunch Abort

The initial fourth-soak attempt is `PRELAUNCH_ABORTED_CONFIG_ENCODING`. The
producer wrote six valid events over 2.007355 seconds, but the managed runtime
never started because its PowerShell-generated JSON configuration had a UTF-8
BOM that strict UTF-8 parsing rejected. The producer was stopped immediately
and no replacement run was launched.

This prefix has zero signals, no paper state, no completion marker, and no
scientific eligibility. Valid evidence remains 172 signals over
24.000000389 hours and two sessions. The Weak Evidence Gate remains failed.

The loader now accepts `utf-8-sig`; a dedicated Windows BOM regression passes,
and the exact preserved configuration passes preflight. D-109 requires config
parse/static validation before producer startup. The frozen strategy, evidence
gates, and holdout boundary are unchanged. The next task is **Run Fourth
24-Hour Repricing Paper Soak v1 - Clean Relaunch**.

## Fourth 24-Hour Canonical Soak Result

The clean fourth soak is `PASS_OPERATIONAL_INTEGRITY`. It completed 86,400
seconds, 43,200 checkpoints, 100% temporal coverage, and exact terminal source
reconciliation. The runtime consumed all 741,438 events through final cursor
741,437, verified healthy `session_completed`, drained to EOF, and closed 166
of 166 paper positions without restart, duplicate, backlog, fatal marker, or
open position.

Frozen batch results:

- signals: 166;
- BTC / ETH / SOL: 31 / 39 / 96;
- YES / NO: 61 / 105;
- win rate: 78.915663%;
- expectancy after slippage: +0.042771;
- P&L after slippage: +7.1000;
- max drawdown: 0.2600.

Valid aggregate evidence across three sessions is 338 signals and
48.000000389 hours. BTC / ETH / SOL is 76 / 80 / 182; YES / NO is 128 / 210;
win rate is 71.301775%; expectancy is +0.032405; P&L is +10.9530; and max
drawdown is 0.8750. All frozen Weak Evidence gates pass. Every asset and both
sides have positive expectancy.

The nominal 95% Wilson interval for win rate is 66.2612%-75.8636%; the nominal
normal interval for expectancy is +0.021666 to +0.043145. These intervals are
optimistic because observations are serially correlated and only three
independent sessions are represented.

Repricing therefore advances to weak development evidence only. The next
stage is **Run Repricing Weak-Evidence Stability And Executable-Cost Stress
Sprint v1** using only admitted public evidence and frozen strategy behavior.
No production-edge claim, holdout access, parameter tuning, or live execution
is authorized.

## Weak-Evidence Stability And Executable-Cost Stress

The frozen 338-signal, three-session evidence set was subjected to as-of
spread, delay, quote-age, visible-liquidity, partial-fill, missed-fill, and
transaction-cost stress. Source microstructure enrichment is complete for all
338 rows. Conclusion: `WEAKENED`.

Recorded conservative expectancy is +0.032405. One-factor spread, 0.005 cost,
fill impairment, and modeled delay through one second remain positive. Modeled
two-second delay weakens to +0.007211 with only two positive sessions;
quote-age stress falls to +0.001565. Combined moderate execution is negative
at -0.015614 with all sessions, assets, and sides negative.

Actual executable bid/ask replay remains positive only at immediate entry
(+0.035944). At two seconds plus 0.005 cost it is -0.009810 across all three
sessions. Five-second/100-share and 250-share visible-size scenarios are also
negative. The two-second nominal 95% expectancy interval is
[-0.018432, -0.001188].

The result does not erase the frozen Weak Evidence count/history finding, but
it shows that evidence is not stable under executable conditions. Latency and
stale quote exposure are the dominant break. Only three sessions exist, one
session supplies 64.82% of baseline P&L, SOL supplies 46.37%, and two-second
public snapshots cannot resolve sub-second queue position or fill probability.

Repricing remains active as an unproven research branch but does not advance
to production candidate. The next task is **Run Repricing Execution Latency
Feasibility Audit v1**, without detector or threshold changes.

## Execution Latency Feasibility Audit

Conclusion: `INSUFFICIENT_MEASUREMENT`.

Current architecture cannot reliably execute below two seconds and cannot
execute below one second. Admitted-signal quote age is 1.771s minimum, 2.653s
median, 7.137s p95, and 49.065s maximum. The two-second source scheduler and
one-second runtime poll dominate; current lower-bound end-to-end estimates are
1.914s best, 3.333s median, 8.435s p95, and 56.925s worst observed before
unmeasured exchange processing.

Home-PC public measurements found CLOB cold HTTPS at 178ms median / 346ms p95
and Binance REST at 1.169s median / 1.217s p95. Detector decision, JSON, and
durable local state are each sub-millisecond median and are not material
latency blockers.

An event-driven WebSocket design on a stable host could plausibly make
sub-two-second transport achievable. In-region deployment may make sub-one-
second median plausible. Neither is proven because authenticated signing,
POST `/order`, acknowledgement, matching, queue position, and fill probability
were not measured and remain outside the authorized paper-only boundary.

The strategy cannot become production-ready through incremental optimization
of the current architecture. It requires a major event-driven redesign and a
new latency measurement contract; even then, the economic edge may remain too
short-lived. Less latency-sensitive strategies should be prioritized in
parallel. The next task is **Implement Repricing Public WebSocket Latency
Instrumentation v1** with no orders or authentication.

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

## Public WebSocket Latency Instrumentation v1

A 180-second bounded public-only benchmark measured polling and WebSockets
simultaneously. CLOB WebSocket inter-message gap was 1.2867 ms mean, 0.5095 ms
median, 6.7460 ms p95, and 14.2408 ms p99 across 137,107 messages. Simultaneous
polling was 1,025.7355 ms mean and 5,150.8863 ms p95 across 179 observations.

WebSocket local processing remained negligible: p95 queue 0.0003 ms, parse
0.0298 ms, decision 0.0016 ms, serialization 0.0207 ms, and journal 0.2632 ms.
This supports sub-two-second public event-to-decision processing and removes
the polling cadence as the dominant architectural blocker.

Absolute quote age cannot be treated as corrected one-way network latency.
Both CLOB paths showed an approximately one-second server/local clock offset,
with no NTP correction. CLOB packet loss is also not measurable from the
public messages because no usable sequence number is exposed. Reconnects,
stale-event guards, inter-message gaps, and external aggregate-ID gaps are
recorded explicitly.

Weak Evidence is now conditionally executable in principle, but end-to-end
execution remains unvalidated. Authenticated signing, submission,
acknowledgement, matching, queue position, and fill probability remain the
dominant unknowns. No production-edge claim is made. The next task is the
design-only **Design Repricing Authenticated Execution Latency Measurement
Protocol v1**; it does not authorize credentials, wallets, or orders.

## Authenticated Execution Latency Measurement Protocol v1

The design covers the full event chain from public signal generation through
decision, signing, L2 authentication, serialization, transport,
acknowledgement, acceptance, first book appearance, partial/complete match,
settlement, cancellation, timeout, retry and terminal reconciliation. Local
durations use monotonic nanoseconds; cross-clock attribution requires NTP
discipline and explicit offset uncertainty. Ambiguous submissions are queried
by deterministic order hash and are never blindly retried.

The protocol defines separate authorization phases: deterministic no-secret
fixtures, public transport calibration, future credentialed no-order
calibration, and only then a separately authorized minimum-risk order-path
measurement. This sprint completed design only and used no credentials or
orders.

The frozen two-second negative replay remains the economic break. Admission
targets are signal-to-ack p95 <=750 ms, first-match p95 <=1,000 ms, and
terminal-fill-or-cancel p95 <=1,500 ms. A future conclusion requires at least
100 attempts over three sessions, zero duplicate/unreconciled orders, complete
clock and replay integrity, and positive expectancy under the measured latency
distribution.

The modeled warm path is 205 ms median / 490 ms p95 to acknowledgement and
275 ms median / 800 ms p95 to first match. These use public RTT proxies plus
explicit assumptions and are not authenticated evidence. Weak Evidence is
conditionally plausible under the expected budget; Repricing remains
`NOT_PRODUCTION_READY_EXECUTION_FEASIBLE_TO_MEASURE`.

The successor is **Implement Repricing Authenticated Execution Latency Dry-Run
Harness v1**, restricted to deterministic stubs and a local sink.

## Authenticated Execution Latency Dry-Run Harness v1

The protocol's Phase 0 harness is implemented. It records deterministic event
identities and complete local lifecycle timestamps through decision, fixture
signing/authentication, serialization, loopback submission, acknowledgement,
fixture user updates, partial/complete fill, cancellation, timeout, retry and
terminal reconciliation. Ambiguous timeouts fail closed without retry; only a
proven pre-send failure can retry once.

The 120-attempt benchmark produced 60 fixture fills, 60 fixture cancellations
and 1,680 replay-valid events. Repeated runs produced the same identity hash.
Local p95 signal-to-ack was 16.8979 ms, first fixture transition 31.1120 ms and
terminal 47.7829 ms. Fixture signing p95 was 0.3091 ms and local transport queue
p95 was 1.0215 ms.

These values do not measure authenticated exchange execution. No credential,
private key, wallet, authenticated endpoint or real order was used, and the
network boundary was `127.0.0.1`. The modeled 490 ms p95 acknowledgement and
800 ms p95 first-match budgets remain unconfirmed. Weak Evidence remains
conditionally plausible, while production status remains
`NOT_PRODUCTION_READY_LOCAL_HARNESS_VALIDATED`.

The next task is **Integrate Repricing Latency Dry-Run Harness With Public Event
Stream v1** under the same no-credential and no-order boundary.

## Public-Stream Latency Dry Run v1

The live public CLOB WebSocket now feeds the local-only latency harness. The
90-second engineering validation completed 60 probes with BTC / ETH / SOL
counts 21 / 20 / 19. It observed 38,194 recognized public events, zero
reconnects, zero stale events, zero backpressure drops, 303 duplicate identities
suppressed and all 60 subsequent same-token public transitions observed.

Latency p95 was 2.2538 ms public receipt to probe signal, 9.8616 ms signal to
loopback acknowledgement, 36.4036 ms signal to next public event and 15.4593
ms signal to fixture terminal. Event-gap p95 was 29.6157 ms. Absolute event age
still contains an approximately one-second clock offset and is not one-way
network latency.

Replay passed for 900 events and 60 correlations. These probes are not accepted
frozen-strategy signals and cannot enter evidence. No credentials, authenticated
endpoint or real orders were used. Weak Evidence remains conditionally
executable, but authenticated exchange admission remains `NOT_EVALUATED` and
production status is `NOT_PRODUCTION_READY_PUBLIC_DRY_RUN_VALIDATED`.

The next task is **Prepare Repricing Credentialed No-Order Calibration Security
Review v1**, with no credential provisioning or authenticated calls.

## Credentialed No-Order Calibration Security Review v1

The security verdict is `NOT_AUTHORIZED_SANDBOX_ENFORCEMENT_REQUIRED`. A future
calibration may conditionally observe only authenticated open orders, trades
and user WebSocket lifecycle plus public server time. All order, batch-order,
cancellation, heartbeat, credential creation/derivation, wallet, signing and
unknown routes are denied.

The exact allowlist is implemented as a deny-by-default policy with tests for
method, scheme, host and path. Required controls include proxy-only egress,
direct-egress denial, isolated process, external L2 secret provider, forbidden
private-key environment names, structural redaction, clock gates, kill switch,
parent watchdog, empty-open-order precondition and independent rollback.

No credential or authenticated call was used. The next task is **Implement
Repricing No-Order Calibration Sandbox Enforcement v1** with fixtures and local
endpoints only. Authenticated exchange admission remains `NOT_EVALUATED`.

## No-Order Calibration Sandbox Enforcement v1

The fixture-only sandbox is implemented and validated. Allowed observational
routes pass only through a local no-socket proxy; direct egress, order, batch
order, cancellation, heartbeat and unknown routes fail closed. Kill-switch,
parent death, watchdog expiry, proxy loss and open-order fixtures all abort
without an order or cancellation.

Clean child-environment rules use opaque fixture handles, and redacted audit
records reveal none of their values. Eight deterministic audit envelopes replay
successfully. The sprint used zero credentials, network calls, authenticated
calls, orders and cancellations.

Status is `FIXTURE_SANDBOX_READY_AUTHORIZATION_BLOCKED`. The next task is **Run
Repricing No-Order Calibration Independent Authorization Gate Review v1** to
assess host-level and procedural prerequisites without credentials.

## No-Order Calibration Independent Authorization Gate Review v1

The independent decision is `NOT_AUTHORIZED`. Application policy and fixture
sandbox controls pass, but host containment and operational governance fail.
All Windows Firewall profiles are disabled, no matching outbound containment
rules or restricted process boundary exist, and secret-provider, revocation,
rollback, incident and expiring-authorization ownership are not operationally
assigned.

No credentialed calibration may proceed. The next task is **Implement Repricing
No-Order Calibration Host Containment Preflight v1**, which remains read-only
and fixture-only and may not apply firewall changes or use credentials.

## No-Order Calibration Host Containment Preflight v1

The deterministic read-only preflight is implemented. The Home PC result is
`NOT_READY_FOR_CREDENTIALS`: firewall inspection and clean fixture-child gates
pass, while 14 mandatory containment/governance gates fail. All firewall
profiles are disabled and no scoped proxy/direct-egress rules are present.

The preflight reads no secret values and modifies no host settings. Credentialed
calibration remains prohibited. The next task is **Prepare Repricing Host
Containment Remediation And Governance Package v1**, limited to non-applied
change plans and assignment templates.

## Host-Containment Architectural Review v1

The project selected `C_CHANGE_RESEARCH_PRIORITY`. Repricing remains preserved
but deferred. Full host governance is premature, and minimum credentialed
no-order calibration is not the immediate next step because it cannot measure
order acceptance, matching, queue position or fills.

If the branch resumes, use the minimum mandatory containment path only: isolated
environment, exact proxy/egress enforcement, external L2-only provider,
expiring authorization, accountable owners, kill/watchdog drills,
zero-open-order gate, redaction/audit and clock controls. Production governance
may wait until authenticated evidence justifies order-path work.

Frozen strategy, evidence gates, holdout status and authorization prohibitions
are unchanged. The next project task is a public-only review of
less-latency-sensitive strategy candidates.

## Slower-Horizon Derivative Validation v1

The final derivative validation returned `NO_GO_FREEZE_REPRICING_PERMANENTLY`.
It replayed the same 338 valid anchors from Balanced Batches 001-002 and the
fourth canonical soak. Entry used the first executable ask after a two-second
delay; fixed 30/60/120/180-second exits used executable bids; actual spread and
the existing 0.005 transaction-cost stress were included.

Continuation expectancy was +0.019601 / +0.035171 / +0.038394 / +0.028768 at
30 / 60 / 120 / 180 seconds. Mean-reversion expectancy was -0.056146 /
-0.071653 / -0.076056 / -0.066227. No continuation result had a clustered or
eight-way-adjusted confidence interval above zero. The 30/60-second detector
timing beat matched random timing but failed concentration and confidence
gates; 120/180-second timing did not beat random. SOL and session concentration
prevented robustness at every horizon.

Repricing is permanently frozen under D-124. The branch must not be reopened
for more data, derivatives, latency, credentials, infrastructure or execution.
Artifacts remain available for audit. The sealed holdout remains untouched.
