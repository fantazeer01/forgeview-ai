# Polymarket Project State

Last updated: July 4, 2026
Canonical objective: [MASTER_OBJECTIVE.md](MASTER_OBJECTIVE.md)  
Active task: [NEXT_TASK.md](NEXT_TASK.md)  
Decision log: [DECISIONS.md](DECISIONS.md)

## Current stage

Strategic phase: **Phase 1 - First Automated Dollar**.

The **Foundation Phase is complete**. The current strategic objective is
Objective Alpha:

> The first fully autonomous paper trade from signal generation through result
> recording without human intervention.

Launch impact now takes priority over architectural completeness.
`LAUNCH_BLOCKERS.md` is the primary operational planning tool, and
`ALPHA_READINESS.md` is the single readiness dashboard. Alpha readiness
tracking is active with categorical values only; no percentage readiness is
used. This transition changes project prioritization, not detector logic,
Wallet logic, Repricing logic, frozen parameters, or execution authorization.

Business Stage 1 - Statistical edge demonstrated: in progress.

Supporting technical stage: Stage 9 - Slower-horizon Repricing derivative
testing. Wallet Intelligence has completed its final specialist validation and
is permanently frozen after a NO-GO decision.

Profit-first governance reset: the primary objective is to build an automated
system capable of generating sustainable profit on Polymarket BTC, ETH, and
SOL five-minute markets, with a long-term target of $10,000 in cumulative
realized profit. Research, engineering, AI, data collection, and infrastructure
are supporting tools. Every sprint must increase expected profitability or
remove a blocker preventing profitable automated trading; work satisfying
neither criterion must not be pursued.

Current business-stage status:

| Stage | Status |
|---|---|
| Statistical edge demonstrated | In progress |
| Continuous paper-trading MVP | In progress |
| Long-duration positive paper performance | Not started |
| Controlled live deployment, if justified | Not started |
| $10,000 cumulative profit target | Not started |

This governance change does not alter any research result, detector logic,
Wallet implementation, Repricing implementation, holdout boundary, or current
prohibition on real-money execution.

Risk Management Principles v1 are now recorded in `RISK_MANAGEMENT.md`.
Current capital status is **Capital Stage 0 - Research** with **$0 real-money
risk**. Any future real-money system, regardless of strategy branch, must pass
Capital Stage 1 proof before Capital Stage 2 scale, cap risk at 1% of current
trading capital per trade, stop new entries on configured loss or integrity
conditions, prohibit discretionary manual trading, and use documented change
control. No implementation or execution authorization follows from this policy
record.

Capital Scaling and Trading License Levels v1 are now recorded in
`CAPITAL_SCALING.md`. Levels 0-1 retain $0 real capital, Level 2 defines micro
execution at approximately $3-$5 per trade or the platform minimum, and Levels
3-5 define approximate $10, $25, and $50 position sizes. Promotion requires
predefined evidence gates; degradation triggers automatic demotion or pause.
No strategy currently has Level 2 or higher authorization, and this policy
update does not authorize execution.

Evidence Gates for Real Trading v1 are now recorded in `EVIDENCE_GATES.md`.
Paper trading is mandatory before any real-money transition. Every predefined
mandatory gate must pass, with automatic evaluation where possible, before CEO
approval may be requested. A failed, unresolved, or unevaluated mandatory gate
blocks promotion and cannot be overridden by CEO approval. The process applies
equally to Repricing, Wallet Intelligence, and future strategies. No numeric
threshold, implementation, strategy, detector, or execution authorization was
added by this governance update.

Strategy Shutdown Policy v1 is now recorded in
`STRATEGY_SHUTDOWN_POLICY.md`. No strategy has permanent trading permission.
Future systems must pause automatically when evidence, expectancy, drawdown,
execution, infrastructure, restart, API, duplicate-execution, or critical-data
conditions degrade, and must support an immediate global stop. A paused
real-money strategy returns to Level 1 paper trading and cannot resume without
a documented review and renewed evidence. Capital preservation takes priority
over continuous trading. No implementation, detector, threshold, strategy, or
execution authorization was changed.

ForgeViewAI KPI Framework v1 is now recorded in `KPI_FRAMEWORK.md` as the
canonical project dashboard definition. It measures five strategy-agnostic
groups: Research Health, Strategy Health, Trading Quality, Infrastructure
Health, and Business Progress. The framework requires explicit provenance,
measurement windows, paper/live separation, per-strategy readiness, and visible
unknown or blocked states. It defines no numeric targets and adds no dashboard
implementation, strategy change, detector change, or trading authorization.

Repository consolidation note: `research/probability-lab` is now maintained as
a normal folder inside the root ForgeViewAI repository. Its nested Git metadata
was removed, project files were preserved, and ForgeViewAI is the only Git
repository for this workspace.

Version-control hygiene note: runtime-generated artifacts are now excluded from
the ForgeViewAI Git index, including Polymarket run sessions, JSONL event
streams, Parquet datasets, logs, and Python/test caches. Source code,
configuration examples, docs, tests, research files, and small CSV/JSON reports
remain eligible for version control.

The public evidence and validation-protocol gates are passed. Baseline
diagnostics concluded `FEATURE_SET_INCOMPLETE`. Market Microstructure Feature
Capture v1, bounded public smoke validation, and Independent Microstructure
Development Dataset Batch 001 are complete. Development-only Batch 001
microstructure diagnostics found no incremental win over YES price and are
classified `DATASET_TOO_SMALL_OR_UNSTABLE`. Independent Microstructure
Development Dataset Batch 002 is also complete and stored separately from
canonical training data. Combined development-only diagnostics over Batches
001-002 still found YES price to be the best diagnostic predictor and are
classified `DATASET_STILL_TOO_SMALL_OR_UNSTABLE`. Repricing Research v1 is now
implemented as a separate development-only module focused on 30-180 second
probability repricing rather than final UP/DOWN outcomes. The final holdout
remains sealed.
Repricing Research v1 Data Sufficiency Audit classifies the current 28-signal
sample as `INSUFFICIENT_SMOKE_ONLY`: useful for diagnostics, but not enough
for model development, shadow validation, or edge claims.
Repricing-Focused Public Evidence Collection Plan v1 is complete. It keeps the
branch planning-only, finds YES-side scarcity as the binding collection
constraint, and recommends a no-capture threshold sensitivity audit before any
new public evidence campaign is authorized.
Repricing Threshold Sensitivity Audit v1 is complete. It recommends the
balanced collection stratum for future evidence gathering, selected for signal
density, asset/side balance, and horizon coverage rather than paper P&L.
Evidence gates remain unchanged and the final holdout remains sealed.
Balanced Repricing Evidence Collection Preflight v1 is complete. The balanced
stratum is operationally ready for a future explicitly authorized 12-hour
public-only evidence campaign, but no campaign was launched in the preflight
task.
Balanced Repricing Evidence Collection Batch 001 is complete. It produced a
complete continuous 12-hour public-only session and a deterministic balanced
repricing dataset. The single-session result is positive after conservative
slippage and clears signal, asset, and side count floors, but weak evidence is
not reached because the branch still lacks at least 40 observed hours and at
least 3 independent balanced-stratum sessions.
Wallet Intelligence Research v1 is now created as a separate research-only
branch for studying successful public Polymarket wallet behavior in fast
BTC/ETH/SOL Up or Down markets. It is descriptive only and remains separated
from final outcome prediction, Repricing Research v1, live trading, wallet
execution, capture campaigns, production modelling, and sealed holdout
evaluation.
Polymarket Open Source Intelligence Audit v1 is complete under
`polymarket/models/open_source_intelligence_audit_v1/`. The audit found
`ent0n29/polybot` to be the highest-priority deep-dive target for wallet
intelligence and strategy reverse engineering, `evan-kolberg/prediction-market-backtesting`
to be the strongest execution-realistic backtesting reference, and
`pmxt-dev/pmxt` to be the strongest read-only API normalization reference.
Wallet Intelligence Data Ingestion v1 is complete. It added a public-data
ingestion CLI under `polymarket/wallet_intelligence/`, produced normalized
outputs under `polymarket/data/wallet_intelligence/v1/`, and collected bounded
first-page public snapshots for the six seed profiles. The run resolved all
six seed profiles, wrote six wallet profile rows and 460 position rows, found
four fast-market crypto wallets, one weather-heavy wallet, and one crypto
non-fast wallet. It did not copy trades, place orders, connect wallets, launch
capture, run holdout evaluation, or train models. Average holding time,
drawdown, late-entry timing, and Binance-lag behavior remain unavailable from
the bounded public profile snapshot.
Wallet Intelligence Behavior Metrics v1 is complete under
`polymarket/models/wallet_intelligence_v1/behavior_metrics/`. It analyzed the
existing 460 position rows only, classified four wallets as fast crypto
focused, one as weather focused, and one as mixed. The strongest fast-market
wallet is `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`, with 100 visible BTC
Up/Down positions, 100% fast-market share, balanced YES/NO exposure, and
small visible position sizes relative to the other seed wallets. Copyability
scores remain deliberately low because public snapshots lack complete fill
history, observation delay, liquidity consumption, linked entry/exit timing,
drawdown, and Binance-lag alignment.
Wallet Intelligence Deep History Feasibility v1 is complete under
`polymarket/models/wallet_intelligence_v1/deep_history_feasibility/`. It
reviewed existing ingestion code and public Polymarket Data API/CLOB endpoint
coverage, performed one bounded read-only 50-row activity probe for
`0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`, and found that public
trade/activity history is feasible for bounded research. Entry timestamp,
entry price, side, size, market type, and partial exit/holding-period evidence
can be reconstructed with joins. Full strategy reconstruction, copyability,
queue/fill certainty, and Binance-lag conclusions remain unavailable from
wallet endpoints alone.
Wallet Public Trade History Ingestion Design v1 is complete under
`polymarket/models/wallet_intelligence_v1/trade_history_ingestion_design/`.
It defined a 35-field normalized trade-history schema, bounded seed-wallet
ingestion limits, raw JSONL and deterministic export architecture, duplicate
handling, source provenance, a seven-part join plan, and ten validation gates.
The design authorizes a future fixture-based implementation task only; it did
not ingest unbounded history, launch broad collection, place orders, copy
trades, connect wallets, inspect holdout outcomes, or run holdout evaluation.
Wallet Public Trade History Ingester Fixture Implementation v1 is complete
under
`polymarket/models/wallet_intelligence_v1/trade_history_ingester_fixture/`.
It added fixture-only trade-history normalization, 35-field schema constants,
dedupe keys, raw row/page hashing, timestamp parsing, BTC/ETH/SOL Up/Down
classification, bounded-limit checks, validation gates, deterministic fixture
exports, and the CLI command
`python -m polymarket.wallet_intelligence trade-history-fixture`. The fixture
run normalized 50 saved public `TRADE` rows and passed all ten gates. It did
not run broad public ingestion, live trading, trade copying, wallet/private-key
use, order placement, capture campaigns, holdout inspection, or holdout
evaluation.
Wallet Public Trade History Bounded Public Smoke v1 is complete under
`polymarket/data/wallet_intelligence/trade_history_smoke_v1/`. It fetched one
public read-only `activity?type=TRADE` page for each of the six seed wallets,
normalized 600 rows, removed zero duplicates, passed all ten validation gates,
and verified deterministic CSV repeat export. The smoke found 367 fast crypto
rows, with asset counts 359 BTC, 97 ETH, 11 SOL, and 133 other; YES-like /
NO-like outcomes were 249 / 351. It did not run broad public ingestion, live
trading, trade copying, wallet/private-key use, order placement, capture
campaigns, holdout inspection, or holdout evaluation.
Wallet Trade Lifecycle Reconstruction Fixture Prototype v1 is complete under
`polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture/`.
It added a deterministic lifecycle reconstruction module and the CLI command
`python -m polymarket.wallet_intelligence trade-lifecycle-fixture`, grouped
the existing 600 normalized public smoke trade rows by wallet, condition ID,
token ID, and outcome, and produced 112 lifecycle position candidates. The
prototype found 74 still-open candidates, 36 partial-exit candidates, and 2
bounded-history oversold candidates where a prior buy is missing from the
one-page public smoke window. Validation passed for deterministic ordering,
repeatable output, position-size conservation, and no unexpected negative
position size. It does not perform expiry joins, mark-to-market PnL,
Binance/reference alignment, copyability-delay estimation, queue-priority
modelling, live trading, order placement, wallet/private-key use, holdout
inspection, or holdout evaluation.
Wallet Lifecycle Reconstruction Review v1 is complete under
`polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_review/`.
It reviewed the lifecycle implementation, tests, and fixture outputs, and
confirmed that the zero full-exit count is explained by exact-size accounting:
36 groups contain both BUY and SELL rows, but none have equal total bought and
sold size. Still-open, partial-exit, and bounded-history oversold
classification are correct for the one-page public smoke window, with the
important limitation that visible status is not necessarily complete wallet
status. During review, lifecycle grouping was hardened to derive keys from
explicit wallet, condition, token, and outcome fields, and deterministic
ordering gained dedupe/provenance tie-breakers. No public ingestion, expiry
join, mark-to-market PnL, Binance/reference alignment, copyability-delay
model, queue model, scoring, wallet/private-key use, order placement, holdout
inspection, or holdout evaluation was added.
Wallet Lifecycle Metrics v1 is complete under
`polymarket/models/wallet_intelligence_v1/lifecycle_metrics/`. It added a
bounded structural metrics layer over existing lifecycle positions only,
producing `wallet_metrics.csv`, `wallet_metrics_summary.json`, and
`wallet_metrics_report.md`. The run analyzed 6 wallets and 112 lifecycle
position candidates, preserving the existing status counts of 74 still-open,
36 partial exits, 0 full exits, and 2 bounded-history oversold candidates. It
reported 543 visible BUY trades, 57 visible SELL trades, 2 SELL-only
lifecycles, and 10 near-flat residual groups using a documented 0.1-share
review-only threshold. Validation passed for wallet coverage, position-count
conservation, status-count conservation, BUY/SELL count matching, decimal
metric parsing, share ranges, deterministic wallet ordering, deterministic
CSV repeat export, and forbidden metric exclusion. It did not compute PnL,
ROI, Sharpe, copyability, wallet scoring/ranking, mark-to-market values,
expiry joins, reference alignment, queue modelling, execution, wallet/private
key use, order placement, holdout inspection, or holdout evaluation.
Wallet Metrics Readiness Review v1 is complete under
`polymarket/models/wallet_intelligence_v1/wallet_metrics_readiness_review/`.
It reviewed all currently available lifecycle metric fields and found that the
outputs are sufficient for a first structural Wallet Score design, but not for
profitability, copyability, execution-quality, ranking, or alpha claims. Ready
inputs include lifecycle coverage, fast-crypto lifecycle share, partial-exit
activity, still-open share, SELL-only/bounded-history risk, event density,
near-flat residual count, asset concentration, and outcome concentration.
Raw visible size fields are useful later after normalization, and full-exit
interpretation needs deeper history, expiry, or redemption context. No new
metrics, scoring implementation, ingestion, PnL, mark-to-market, expiry join,
copyability model, wallet/private-key use, order placement, holdout
inspection, or holdout evaluation was added.
Wallet Score Design v1 is complete under
`polymarket/models/wallet_intelligence_v1/wallet_score_design/`. It defines a
bounded 0-100 structural prioritization score for selecting wallets worth
deeper analysis, using only readiness-approved lifecycle metrics. The design
allows coverage, fast-crypto relevance, visible lifecycle activity,
event-density consistency, and specialization components, with penalties for
SELL-only/bounded-history risk, excessive still-open share, too few lifecycle
positions, excessive concentration, and near-flat residual ambiguity. It
explicitly forbids PnL, ROI, realized profit, Sharpe, execution quality,
copyability, alpha claims, mark-to-market values, sealed holdout data, private
wallet data, order-placement data, and authenticated trading data as score
inputs. No score computation, ranking, ingestion, metric-generation change,
wallet/private-key use, order placement, holdout inspection, or holdout
evaluation was implemented.
Wallet Score Fixture Implementation v1 is complete under
`polymarket/models/wallet_intelligence_v1/wallet_score_fixture/`. It added
`polymarket/wallet_intelligence/wallet_score.py` and the CLI command
`python -m polymarket.wallet_intelligence wallet-score-fixture`, using only
approved structural lifecycle metrics from existing `wallet_metrics.csv`. The
fixture produced `wallet_scores.csv`, `wallet_scores_summary.json`,
`wallet_score_validation.json`, and `wallet_score_report.md`. It scored six
seed wallets as structural research-priority records only: 1
`medium_priority`, 3 `low_priority`, and 2
`insufficient_visible_structure`; no `high_priority` records appeared in the
current fixture output. Validation passed for score bounds, deterministic
score calculation, deterministic ordering, forbidden-input exclusion, missing
metric handling, repeatable export, allowed-input exact match, component
bounds, penalty bounds, output schema completeness, and source provenance
completeness. No PnL, ROI, realized profit, Sharpe, execution quality,
copyability, alpha claims, mark-to-market values, resolved win/loss outcomes,
sealed holdout data, private wallet data, order-placement data, authenticated
trading data, public ingestion, wallet/private-key use, order placement, or
holdout evaluation was added.
Wallet Score Broader Evidence Collection Design v1 is complete under
`polymarket/models/wallet_intelligence_v1/wallet_score_broader_evidence_design/`.
It defines a bounded public read-only plan for applying the existing Wallet
Score v1 to a 30-wallet sample without adding score inputs or changing
thresholds. The target sample is five times the current fixture size and is
split across existing seed wallets, fast BTC/ETH/SOL Up/Down candidates,
mixed or non-fast controls, and lower-activity insufficient-data controls.
The planned limits are 30 wallets, two primary activity pages per wallet, 200
primary rows per wallet, 6,000 primary rows overall, one `/trades` cross-check
page per wallet, 100 cross-check rows per wallet, 3,000 cross-check rows
overall, two retries per page, and polite request pacing. The plan defines
expected artifact paths, validation gates, healthy score behavior, suspicious
score behavior, and review criteria. It preserves the strict boundary against
profitability, alpha, copyability, trading recommendations, wallet/private-key
use, order placement, capture campaigns, production model training, sealed
holdout inspection, and holdout evaluation.
Wallet Watchlist v1 and Wallet Watchlist Review v1 are complete from the
existing six-wallet score fixture. Wallet Copyability Feasibility Sprint v1
has now completed the broader 30-wallet evidence run. Wallet Market Outcome
Resolution Sprint v1 joined 2,134 of 2,135 lifecycle rows to public market
metadata and classified 2,122 rows with resolved outcomes. The active
successor task is now Wallet Activity Visibility Delay Sprint v1, a direct H2
test over the H1 candidate wallets.

## Completed milestones

- v1 deterministic paper-trading and P&L engine.
- v2 noise, slippage, latency, and walk-forward robustness validation.
- v3 real-market public capture, replay, and shadow validation.
- v4 BTC/ETH/SOL five-minute discovery and external-reference lag scanner.
- v5 long capture, market lifecycle tracking, evidence reports, inspect,
  replay, and live terminal modes.
- Feature Engine v1 with one leakage-controlled row per completed market.
- CSV and Parquet training exports with feature and label provenance.
- Dataset Quality Engine v1 with deterministic scoring and public-only exports.
- Resolution Engine v1 with strict public Gamma outcome parsing, saved raw
  evidence, deterministic replay, and proxy reconciliation.
- Feature Engine authoritative-label preference with proxy labels disabled by
  default.
- Public Feature Completeness Repair v1 with first-seen lifecycle recovery,
  stale as-of rejection, sparse-row exclusion, and reproducible missingness
  diagnostics.
- Public Evidence Batch Pipeline v1 with public-only capture enforcement,
  resumable fail-closed stages, immutable as-of session snapshots, artifact
  hashes, and master sample-gate verdicts.
- Campaign Reliability & Diagnostics v1 with monotonic-versus-UTC clock
  monitoring, actual start/completion timestamps, temporal completeness
  verdicts, independent discovery-failure evidence, partial endpoint success,
  and preserved campaign stdout/stderr artifacts.
- Campaign Observation Continuity Gate v1.1 with checkpoint-density, gap,
  terminal-continuity, completion-marker, and fatal-error acceptance gates.
  Batch 003 is now deterministically classified `INCOMPLETE_CAMPAIGN` while
  retaining all 368 usable clean rows.
- Campaign Observation Continuity Root Cause Analysis v1 established two
  independent causes for Batch 003:
  - the host entered Windows sleep from June 21, 2026 02:49:06 UTC to
    09:57:14 UTC, confirmed by Windows Power-Troubleshooter event 1;
  - while awake, the capture loop serialized approximately 16 blocking HTTP
    requests per cycle, then slept another two seconds, producing a median
    9.378-second and mean 11.803-second checkpoint interval instead of two
    seconds.
- Non-Blocking Capture Cadence Architecture v1 with fixed-deadline scheduling,
  cached background discovery, concurrent reference/discovery/quote requests,
  cadence-independent checkpoint emission, bounded network timeouts, Windows
  sleep inhibition, and fail-closed power preflight.
- Public Evidence Campaign Batch 004 (`20260621_220439`) completed with full
  six-hour continuity, fresh authoritative resolution processing, deterministic
  replay, and 268 additional clean public rows.
- Public Evidence Campaign Batch 005 (`20260622_110942`) completed with full
  six-hour continuity, fresh authoritative resolution processing, deterministic
  replay, and 215 additional clean public rows.
- Public Evidence Campaign Batch 006 (`20260622_211037`) completed with full
  six-hour continuity, fresh authoritative resolution processing, deterministic
  replay, and 213 additional clean public rows. It raised the authoritative
  dataset to 1,064 rows and passed the 1,000-row public evidence gate.
- Time-Ordered Holdout and Baseline Validation Protocol v1 with atomic
  five-minute window groups, one-window purge and embargo at each boundary,
  deterministic artifact hashes, separated holdout labels, and precommitted
  baseline metrics and acceptance rules.
- Baseline Probability Model v1 with deterministic class-prior, asset-prior,
  Polymarket YES-price, and fixed logistic predictors. The logistic model beat
  both prior baselines but lost to YES price on validation, producing
  `NO_EDGE_FOUND_YET`.
- Baseline Failure Diagnostics v1 with fixed feature-group ablations, asset and
  regime attribution, calibration, drift, correlation, and redundancy
  evidence. Conclusion: `FEATURE_SET_INCOMPLETE`.
- Market Microstructure Feature Capture v1 with public CLOB depth/timestamp
  preservation, schema-versioned session events, deterministic as-of features,
  cross-asset synchronization, explicit missingness, and legacy replay
  compatibility.
- Public Microstructure Capture Smoke Validation v1 with a complete,
  continuous 900-second BTC/ETH/SOL public session, 1,328 microstructure
  events, deterministic replay, and deterministic disposable feature export.
  Decision: `READY_FOR_PRODUCTION_CAPTURE`.
- Independent Microstructure Development Dataset Batch 001 from session
  `20260623_120611`, a complete continuous six-hour public-only schema-v1
  capture with 32,041 microstructure events, deterministic replay, and a
  separate 213-row development dataset under
  `polymarket/data/microstructure_dataset_batch_001/`. The dataset contains
  71 BTC, 71 ETH, and 71 SOL rows; all 19 microstructure feature columns are
  populated on every exported row. It has not been merged into canonical
  training data.
- Development-Only Microstructure Feature Diagnostics Batch 001 under
  `polymarket/models/microstructure_diagnostics_batch_001/`. The fixed
  chronological 70/30 development diagnostic used 149 train rows and 64
  evaluation rows from Batch 001 only. YES price remained the best diagnostic
  result with evaluation log loss 0.568340 and Brier 0.192367. The
  microstructure-only diagnostic model scored 0.628730 / 0.220724, and the
  YES-plus-microstructure diagnostic model scored 0.594523 / 0.203701.
  Decision: `DATASET_TOO_SMALL_OR_UNSTABLE`.
- Capture robustness repair for asynchronous discovery worker exceptions.
  Raw async discovery exceptions are now normalized into structured
  `discovery_failure` diagnostics instead of crashing capture. This was
  regression-tested in `tests/polymarket/test_v5.py`.
- Independent Microstructure Development Dataset Batch 002 from session
  `20260623_214015`, a complete continuous six-hour public-only schema-v1
  capture with 32,089 microstructure events, deterministic replay, and a
  separate 213-row development dataset under
  `polymarket/data/microstructure_dataset_batch_002/`. The dataset contains
  71 BTC, 71 ETH, and 71 SOL rows; all 19 microstructure feature columns are
  populated on every exported row. It has not been merged into canonical
  training data.
- Combined Development-Only Microstructure Diagnostics Batches 001-002 under
  `polymarket/models/microstructure_diagnostics_batches_001_002/`. The fixed
  chronological window-group 70/30 development diagnostic used 297 train rows
  and 129 evaluation rows from the two independent proxy-labelled batches.
  YES price remained the best diagnostic result with evaluation log loss
  0.546792 and Brier 0.182709. The microstructure-only diagnostic model scored
  0.677837 / 0.241526, and the YES-plus-microstructure diagnostic model scored
  0.610897 / 0.210249. YES price remained best on BTC, ETH, and SOL
  independently. Decision: `DATASET_STILL_TOO_SMALL_OR_UNSTABLE`.
- Repricing Research v1 under `polymarket/repricing_research/`, documented in
  `docs/polymarket/REPRICING_RESEARCH_V1.md`. This separate development-only
  module labels and simulates short-horizon contract repricing over 30, 60,
  120, and 180 seconds. It does not predict final market outcome, does not use
  the sealed holdout, does not place orders, and does not connect wallets or
  private keys.
- Repricing Research v1 short replay over completed schema-v1 microstructure
  Batches 001 and 002 under
  `polymarket/models/repricing_research_v1/short_replay/`. The replay produced
  28 non-overlapping paper signals, 16 target-before-stop wins, 57.14% win
  rate, 0.9665 simulated P&L before fees/slippage, 0.4065 simulated P&L after
  a 0.02 conservative slippage haircut per signal, 0.4050 max drawdown, and
  0.0145 expectancy per signal. This is a development smoke result only, not
  an alpha or production claim.
- Repricing Research v1 Data Sufficiency Audit under
  `polymarket/models/repricing_research_v1/data_sufficiency_audit/`. The
  audit found that the 28-signal sample is below the 100-signal weak-evidence
  floor, has only 13.1255 observed hours, is imbalanced by asset (5 BTC, 8
  ETH, 15 SOL) and side (5 YES, 23 NO), and is unstable: aggregate expectancy
  is positive at 0.0145 after slippage, but NO-side expectancy is -0.0084 and
  ETH expectancy is -0.0094. Current evidence level:
  `INSUFFICIENT_SMOKE_ONLY`.
- Repricing-Focused Public Evidence Collection Plan v1 under
  `polymarket/models/repricing_research_v1/evidence_collection_plan_v1/`.
  The plan estimates the current strict replay rate at 2.1333 signals/hour and
  identifies the binding evidence bottlenecks as small sample size, YES-side
  scarcity, BTC/ETH underrepresentation, strict lag admission filters,
  non-overlap compression, and incomplete 120/180 second forward-horizon
  coverage. Count-only accumulation would require about 4 / 12 / 40
  independent 12-hour sessions to reach 100 / 300 / 1,000 signals, but
  balance-adjusted gates at current rates require about 8 / 22 / 77 such
  sessions because YES-side count is binding. No capture was launched.
- Repricing Threshold Sensitivity Audit v1 under
  `polymarket/models/repricing_research_v1/threshold_sensitivity_audit_v1/`.
  The persisted current smoke dataset remains 28 signals at 2.1333
  signals/hour, with BTC / ETH / SOL counts of 5 / 8 / 15 and YES / NO counts
  of 5 / 23. The dominant detector-level removal filter is
  `external_move_below_threshold`, with 36,465 of 64,130 candidate
  observations in the recomputed audit. Requiring full 180-second horizon
  coverage removes every current signal; among entry-admission thresholds,
  `external_move_threshold_bps` has the largest density effect. The recommended
  future collection stratum is `balanced`: external move threshold 6 bps,
  repricing ratio 0.65, minimum confidence 0.45, minimum dataset expiry 60
  seconds, 180-second max hold, and accepted reasons
  `qualified_external_move_not_repriced` plus `confidence_below_threshold`.
  It estimates 61 outcome-free overlap-adjusted signals, 3.9184 signals/hour,
  BTC / ETH / SOL counts of 17 / 20 / 24, YES / NO counts of 14 / 47, and
  30s / 60s / 120s / 180s horizon coverage of
  100.0% / 98.36% / 80.33% / 0.0%. The recommendation was not selected by
  paper P&L, and no capture was launched.
- Balanced Repricing Evidence Collection Preflight v1 under
  `polymarket/models/repricing_research_v1/balanced_collection_preflight_v1/`.
  The preflight verified CLI support for the frozen balanced stratum, separated
  future paths under `polymarket/runs/repricing_balanced_v1/`,
  `polymarket/models/repricing_research_v1/balanced_collection_batch_001/`,
  and `polymarket/data/repricing_research_balanced_batch_001/`, and recorded
  the future launch command without executing it. Windows AC sleep and
  hibernate are disabled, no competing `python -m polymarket.edge_engine_v5
  capture` process was found, no stale lock was found, and available disk space
  is approximately 391.469 GB. The expected 12-hour run has 21,600 checkpoints,
  about 47.02 expected repricing signals at 3.9184 signals/hour, and about
  205 MB expected artifacts. Operational preflight result:
  `READY_FOR_AUTHORIZED_LAUNCH`. Campaign launch was not authorized or
  executed by the preflight task itself.
- Balanced Repricing Evidence Collection Batch 001 from session
  `polymarket/runs/repricing_balanced_v1/20260624_154206/session.jsonl`. The
  12-hour public-only balanced-stratum campaign completed with
  `session_completed`, campaign completeness status `complete`, 100.0%
  coverage, 21,600 / 21,600 checkpoints, observation continuity status
  `continuous`, maximum checkpoint gap 2.035487 seconds, no gaps over 10 / 60 /
  300 seconds, and zero fatal capture errors. V5 replay succeeded under
  `polymarket/models/repricing_research_v1/balanced_collection_batch_001/capture_replay/`.
  The balanced repricing dataset was exported under
  `polymarket/models/repricing_research_v1/balanced_collection_batch_001/repricing_dataset/`
  and copied separately to
  `polymarket/data/repricing_research_balanced_batch_001/`. Deterministic
  export was verified by matching SHA-256 hashes across repeated exports. The
  dataset has 130 signals, BTC / ETH / SOL counts of 37 / 29 / 64, YES / NO
  counts of 59 / 71, 11.2706 signals/hour, 58.46% target-before-stop win rate,
  +0.012331 expectancy after conservative slippage, +1.603 after-slippage
  simulated P&L, and 0.875 max drawdown. Exit reasons are 76
  `repricing_target`, 45 `stop_loss`, and 9 `timeout`. Evidence level:
  `SINGLE_SESSION_POSITIVE_BELOW_WEAK_EVIDENCE_HOURS_AND_SESSION_GATES`.
- Wallet Intelligence Research v1 under `polymarket/wallet_intelligence/`,
  documented in `docs/polymarket/WALLET_INTELLIGENCE_RESEARCH_V1.md`. This
  separate research-only branch defines wallet/profile schema, research
  questions, strict no-execution boundaries, copyability-score semantics, and
  an initial watched-wallet input template. It does not collect data yet, does
  not inspect the sealed holdout, does not launch capture, does not train
  production models, and does not connect wallets or copy trades.
- Polymarket Open Source Intelligence Audit v1 under
  `polymarket/models/open_source_intelligence_audit_v1/`. The audit inspected
  eight public GitHub repositories for relevance to Repricing Research, Wallet
  Intelligence, Binance-Polymarket lag strategies, smart-money/copy-trading
  analysis, backtesting, and dry-run simulation. It produced a report,
  machine-readable JSON, repository scorecard, feature gap matrix, and reuse
  recommendations. No dependencies were installed, no code was executed beyond
  read-only inspection, no wallets were connected, no campaigns were launched,
  no production models were trained, and the existing pipeline was not
  modified.
- Wallet Intelligence Data Ingestion v1 under
  `polymarket/data/wallet_intelligence/v1/`. The bounded public snapshot
  resolved all six seed profiles from
  `polymarket/wallet_intelligence/watched_wallets.example.csv`, wrote
  `wallets_raw.jsonl`, `wallet_profiles.csv`, `wallet_positions.csv`,
  `wallet_summary.json`, `ingestion_report.md`, and
  `ingestion_report.json`, and preserved source URLs plus retrieval timestamp
  `2026-06-24T20:00:17+00:00`. It uses only public profile/data endpoints and
  records unavailable timing fields explicitly.
- Wallet Intelligence Behavior Metrics v1 under
  `polymarket/models/wallet_intelligence_v1/behavior_metrics/`. It produced
  `behavior_metrics_report.md`, `behavior_metrics_report.json`,
  `wallet_behavior_metrics.csv`, `wallet_similarity_matrix.csv`,
  `wallet_clusters.csv`, and `copyability_risk.csv` from existing ingestion
  artifacts only. It found four fast-crypto-focused wallets, one
  weather-focused wallet, one mixed wallet, aggregate YES/NO counts of
  234 / 225, dominant entry bucket `80_100c`, and no support for late-window,
  hold-time, drawdown, or executable copyability claims.
- Wallet Intelligence Deep History Feasibility v1 under
  `polymarket/models/wallet_intelligence_v1/deep_history_feasibility/`. It
  produced `deep_history_feasibility_report.md`,
  `deep_history_feasibility_report.json`, `endpoint_inventory.csv`,
  `wallet_feasibility_matrix.csv`, and `bounded_probe_sample.jsonl`. It found
  a safe bounded public-history path through Data API activity/trades plus
  positions, closed positions, CLOB price history, and external BTC/ETH/SOL
  reference-price joins. A one-wallet 50-row read-only probe returned public
  `TRADE` rows with timestamps, transaction hashes, token IDs, condition IDs,
  sides, prices, sizes, outcomes, slugs, and event slugs. The result supports
  a future ingestion design task only.
- Wallet Public Trade History Ingestion Design v1 under
  `polymarket/models/wallet_intelligence_v1/trade_history_ingestion_design/`.
  It produced `trade_history_ingestion_design.md`,
  `trade_history_ingestion_design.json`, `trade_history_schema.csv`,
  `join_plan.csv`, `ingestion_limits.json`, and
  `validation_gate_definition.json`. The design caps the first future scope at
  the six seed wallets, 100 rows per page, three primary activity pages per
  wallet, one trades cross-check page per wallet, 1,800 primary activity rows
  total, 600 cross-check rows total, and public read-only cache-first
  endpoint usage only. No broad ingestion was run.
- Wallet Public Trade History Ingester Fixture Implementation v1 under
  `polymarket/models/wallet_intelligence_v1/trade_history_ingester_fixture/`.
  It produced `fixture_ingestion_report.md`,
  `fixture_ingestion_report.json`, `normalized_trades_fixture.csv`,
  `raw_trades_fixture.jsonl`, `validation_gate_results.json`, and
  `reproducibility_hashes.json`. The fixture run normalized 50 saved public
  trade rows for `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`, removed zero
  duplicates, passed all ten validation gates, and recorded deterministic CSV
  repeat-export status. The full automated suite now has 105 passing tests.
- Wallet Public Trade History Bounded Public Smoke v1 under
  `polymarket/data/wallet_intelligence/trade_history_smoke_v1/`. It produced
  `trade_history_raw.jsonl`, `trade_history_normalized.csv`,
  `trade_history_summary.json`, `bounded_smoke_report.md`,
  `bounded_smoke_report.json`, `validation_gate_results.json`, and
  `reproducibility_hashes.json`. The smoke attempted and succeeded for all six
  seed wallets, fetched 600 public `TRADE` rows across six pages, normalized
  600 rows, removed zero duplicates, passed all ten validation gates, and
  recorded deterministic CSV repeat-export status. It found 367 fast-crypto
  rows, 359 BTC rows, 97 ETH rows, 11 SOL rows, 133 other rows, 249 YES-like
  outcomes, and 351 NO-like outcomes. The full automated suite now has 106
  passing tests.
- Public Evidence Campaign Batch 003 (`20260620_213414`) was captured and fully
  processed through resolution, feature, quality, and deterministic replay.
  It added 139 clean authoritative rows, but is not accepted as a complete
  campaign: observations stop at June 21, 2026 02:48:58 UTC and the terminal
  event follows at 09:57:33 UTC, leaving a 7:08:34 observation-free tail. The
  v1 completeness metric incorrectly reported `complete` because UTC and
  monotonic clocks advanced together during the likely host suspension.
- Finalized public capture batch `20260619_174322` with fresh Gamma resolution
  refresh, deterministic replay, and measured dataset growth.
- Completed processing of Public Evidence Campaign Batch 002
  (`20260619_223637`) with fresh resolution refresh, deterministic replay, and
  155 additional clean rows. A subsequent integrity investigation found that
  the process exited through its normal completion path, but timestamped live
  observations cover only 5:05:15 of the requested six-hour wall-clock market
  period. The terminal completion timestamp was synthesized as start plus the
  configured duration and therefore overstates observed market coverage by
  54:44.951.
- Self-guiding project management documents with one active-task protocol,
  durable decisions, and a separated research backlog.
- Product isolation under `polymarket/`, `docs/polymarket/`,
  `tests/polymarket/`, and `polymarket/data|runs/`.
- Full automated suite passing: 89 tests.

## Active milestone

Phase 1 - First Automated Dollar. Wallet Intelligence is permanently frozen
after its final specialist alpha validation failed conservative value,
chronological stability, consensus, selection-independence, and executable-data
gates. The sole active task tests the preserved Repricing branch at fixed
slower horizons using existing public evidence.

Current measured baseline:

| Metric | Current | Milestone target |
|---|---:|---:|
| Clean completed rows | 1,064 | >=1,000 |
| Public rows | 1,064 | >=1,000 |
| Mock rows | 0 | Excluded from model validation |
| Public rows per asset | 353 BTC / 355 ETH / 356 SOL | >=200 |
| Public UP / DOWN | 527 / 537 | Minority class >=30% |
| Authoritative resolution coverage | 1,391 / 1,398 (99.50%) | >=95% |
| Feature completeness | 99.18% | >=95% |
| Duplicate rows | 0 | <=1% |
| Dataset quality score | 99.52 | >=75 |
| Dataset Quality Engine recommendation | Yes | Yes |
| Evidence-pipeline training authorization | Yes | Yes |
| Frozen train / validation / holdout rows | 741 / 153 / 158 | Deterministic |
| Boundary-excluded rows | 12 | Fully traceable |
| Holdout labels | Sealed, SHA-256 committed | Untouched |
| Best validation predictor | Polymarket YES price | Candidate must beat it |
| Baseline v1 verdict | `NO_EDGE_FOUND_YET` | `ADVANCE_CANDIDATE` |
| Diagnostic conclusion | `FEATURE_SET_INCOMPLETE` | New information required |
| Fixed groups beating YES price | 0 / 8 | At least one stable group |
| New microstructure columns | 19 | Implemented |
| Deterministic raw/depth fixture coverage | 100% | >=95% |
| Real public raw microstructure coverage | 100% | >=95% |
| Velocity / acceleration coverage | 99.10% / 98.19% | Warm-up adjusted |
| Smoke continuity | 450 / 450 checkpoints | >=95% |
| Smoke decision | `READY_FOR_PRODUCTION_CAPTURE` | Ready |
| Batch 001 dataset rows | 213 | Development evidence |
| Batch 001 rows per asset | 71 BTC / 71 ETH / 71 SOL | Balanced |
| Batch 001 microstructure row coverage | 100% | Complete |
| Batch 001 replay compatibility | Verified | Required |
| Batch 001 diagnostic decision | `DATASET_TOO_SMALL_OR_UNSTABLE` | Do not advance |
| Batch 001 best diagnostic predictor | YES price | Candidate must beat it |
| Batch 001 diagnostic eval rows | 64 | Too small |
| Batch 002 dataset rows | 213 | Development evidence |
| Batch 002 rows per asset | 71 BTC / 71 ETH / 71 SOL | Balanced |
| Batch 002 microstructure row coverage | 100% | Complete |
| Batch 002 replay compatibility | Verified | Required |
| Combined microstructure diagnostic rows | 426 | Development evidence |
| Combined diagnostic rows per asset | 142 BTC / 142 ETH / 142 SOL | Balanced |
| Combined diagnostic outcomes | 213 UP / 213 DOWN | Balanced proxy labels |
| Combined diagnostic best predictor | Polymarket YES price | Candidate must beat it |
| Combined diagnostic decision | `DATASET_STILL_TOO_SMALL_OR_UNSTABLE` | Do not advance |
| Repricing Research v1 short replay signals | 28 | Development smoke only |
| Repricing Research v1 short replay win rate | 57.14% | Not a production claim |
| Repricing Research v1 after-slippage paper P&L | 0.4065 | Needs stress testing |
| Repricing Research v1 evidence level | `INSUFFICIENT_SMOKE_ONLY` | Diagnostics only |
| Repricing weak evidence target | 100 signals / 40 hours / 3 sessions | Not met |
| Repricing moderate evidence target | 300 signals / 120 hours / 6 sessions | Not met |
| Repricing strong development target | 1,000 signals / 400 hours / 20 sessions | Not met |

## Blockers

- Historical sessions predate the schema and have 0% microstructure coverage.
- Public order flow is currently a depth/quote-change proxy, not authenticated
  trade aggressor data.
- Combined Batch 001-002 development diagnostics did not beat YES price and
  remain too small or unstable to justify a candidate specification.
- Repricing has 172 scientifically valid signals across two sessions and a
  supported matched random-timing comparison, but remains below the frozen
  40-hour and three-session weak-evidence gates. Its first 24-hour paper soak
  failed capture continuity, heartbeat liveness, bounded shutdown, and exact
  live-versus-replay reconciliation.
- Wallet Intelligence H1 remains inconclusive. The canonical H2/H3 accumulator
  exhausted 60 sessions on one UTC date, and 299 of 382 gate rows were
  historical trades first surfaced by later API pages rather than trades
  executed during their first observer session. The 83-row diagnostic subset
  with defensible prospective provenance remains below the frozen 100-row and
  five-date gates. Wallet Intelligence is therefore frozen, not graduated.
- OSS audit findings are descriptive only. Execution-heavy repositories expose
  private-key, live-order, copy-trading, market-making, or cancel/replace
  paths and must not be run or imported into ForgeView's research pipeline.
- The existing validation and holdout periods may not be retrofitted with new
  features.

The holdout remains sealed. Final holdout evaluation, alpha claims, P&L
optimization, and trading remain unauthorized.

## Next actions

The single active task is Run Repricing Slower-Horizon Derivative Validation
v1.
Its scope and acceptance criteria are defined in `NEXT_TASK.md`.

## Latest metrics

Measured June 25, 2026:

- automated tests: 120 passing;
- Wallet Intelligence Research v1 module path:
  `polymarket/wallet_intelligence/`;
- Wallet Intelligence Research v1 document:
  `docs/polymarket/WALLET_INTELLIGENCE_RESEARCH_V1.md`;
- Wallet Intelligence watched-wallet template:
  `polymarket/wallet_intelligence/watched_wallets.example.csv`;
- Wallet Intelligence seed profiles: 6;
- Wallet Intelligence normalized profile records collected: 6;
- Wallet Intelligence normalized position records collected: 460;
- Wallet Intelligence public-data output path:
  `polymarket/data/wallet_intelligence/v1/`;
- Wallet Intelligence fast-market crypto wallets found in bounded snapshot: 4;
- Wallet Intelligence weather-heavy wallets found in bounded snapshot: 1;
- Wallet Intelligence crypto non-fast wallets found in bounded snapshot: 1;
- Wallet Intelligence unresolved seed profiles: 0;
- Wallet Intelligence behavior metrics output path:
  `polymarket/models/wallet_intelligence_v1/behavior_metrics/`;
- Wallet Intelligence wallets analyzed in behavior metrics: 6;
- Wallet Intelligence classifications: 4 fast crypto focused, 1 weather
  focused, 1 mixed;
- Wallet Intelligence strongest fast-market wallet:
  `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`;
- Wallet Intelligence aggregate YES / NO counts: 234 / 225;
- Wallet Intelligence dominant entry bucket: `80_100c` with 111 / 460 visible
  positions;
- Wallet Intelligence most similar pair:
  `0x1f0ebc543b2d411f66947041625c0aa1ce61cf86` and
  `0xd0d6053c3c37e727402d84c14069780d360993aa`, similarity 0.939721;
- Wallet Intelligence late-window behavior available: false;
- Wallet Intelligence deep-history feasibility output path:
  `polymarket/models/wallet_intelligence_v1/deep_history_feasibility/`;
- Wallet Intelligence bounded public activity probe rows: 50;
- Wallet Intelligence public trade/activity history feasible: bounded yes;
- Wallet Intelligence full strategy reconstruction feasible: false;
- Wallet Intelligence Binance-lag alignment feasible from wallet endpoints
  alone: false;
- Wallet Intelligence trade-history ingestion design output path:
  `polymarket/models/wallet_intelligence_v1/trade_history_ingestion_design/`;
- Wallet Intelligence trade-history schema fields: 35;
- Wallet Intelligence trade-history join-plan rows: 7;
- Wallet Intelligence trade-history validation gates: 10;
- Wallet Intelligence first future activity row cap: 1,800 rows across six
  seed wallets;
- Wallet Intelligence first future trades cross-check cap: 600 rows across six
  seed wallets;
- Wallet Intelligence trade-history fixture ingester output path:
  `polymarket/models/wallet_intelligence_v1/trade_history_ingester_fixture/`;
- Wallet Intelligence fixture trade rows normalized: 50;
- Wallet Intelligence fixture validation gates passed: 10 / 10;
- Wallet Intelligence fixture duplicate rows removed: 0;
- Wallet Intelligence fixture deterministic CSV repeat export: true;
- Wallet Intelligence fixture Parquet status:
  `not_written_no_project_parquet_dependency`;
- Wallet Intelligence public trade-history smoke output path:
  `polymarket/data/wallet_intelligence/trade_history_smoke_v1/`;
- Wallet Intelligence public smoke wallets attempted / succeeded: 6 / 6;
- Wallet Intelligence public smoke pages fetched: 6;
- Wallet Intelligence public smoke rows fetched / normalized: 600 / 600;
- Wallet Intelligence public smoke validation gates passed: 10 / 10;
- Wallet Intelligence public smoke duplicate rows removed: 0;
- Wallet Intelligence public smoke deterministic CSV repeat export: true;
- Wallet Intelligence public smoke fast crypto rows: 367;
- Wallet Intelligence public smoke BTC / ETH / SOL / other rows:
  359 / 97 / 11 / 133;
- Wallet Intelligence public smoke YES-like / NO-like outcomes: 249 / 351;
- Wallet Intelligence lifecycle fixture output path:
  `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_fixture/`;
- Wallet Intelligence lifecycle fixture input rows: 600;
- Wallet Intelligence lifecycle positions reconstructed: 112;
- Wallet Intelligence lifecycle status counts: 74 still open, 36 partial
  exits, 2 bounded-history oversold candidates, 0 full exits in the bounded
  smoke window;
- Wallet Intelligence lifecycle asset counts: 78 BTC, 6 ETH, 2 SOL, 26 other;
- Wallet Intelligence lifecycle fast crypto position candidates: 75;
- Wallet Intelligence lifecycle deterministic ordering: true;
- Wallet Intelligence lifecycle position-size conservation: true;
- Wallet Intelligence lifecycle repeatable CSV output: true;
- Wallet Intelligence lifecycle unexpected negative position groups: 0;
- Wallet Intelligence lifecycle bounded-history missing-prior-buy groups: 2;
- Wallet Intelligence lifecycle review output path:
  `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_review/`;
- Wallet Intelligence lifecycle groups with both BUY and SELL rows: 36;
- Wallet Intelligence lifecycle exact full-exit groups: 0;
- Wallet Intelligence lifecycle current grouping hardening: explicit
  `wallet_id|condition_id|token_id|outcome` derivation;
- Wallet Intelligence lifecycle ordering hardening: dedupe and provenance
  tie-breakers added;
- Wallet Intelligence lifecycle metrics output path:
  `polymarket/models/wallet_intelligence_v1/lifecycle_metrics/`;
- Wallet Intelligence lifecycle metrics wallets analyzed: 6;
- Wallet Intelligence lifecycle metrics positions analyzed: 112;
- Wallet Intelligence lifecycle metrics status counts: 74 still open, 36
  partial exits, 0 full exits, 2 bounded-history oversold;
- Wallet Intelligence lifecycle metrics visible BUY / SELL trades: 543 / 57;
- Wallet Intelligence lifecycle metrics sell-only lifecycles: 2;
- Wallet Intelligence lifecycle metrics near-flat residual count: 10 at a
  0.1-share review-only threshold;
- Wallet Intelligence lifecycle metrics validation passed: true;
- Wallet Intelligence copyability overclaim allowed: false;
- Wallet Intelligence holdout outcomes read: false;
- Wallet Intelligence capture campaigns launched: 0;
- Wallet Intelligence wallet/private-key connections implemented: false;
- OSS audit output path:
  `polymarket/models/open_source_intelligence_audit_v1/`;
- OSS audit repositories inspected: 8;
- OSS audit top repository for first deep dive: `ent0n29/polybot`;
- OSS audit top backtesting reference:
  `evan-kolberg/prediction-market-backtesting`;
- OSS audit top API reference: `pmxt-dev/pmxt`;
- OSS audit live trading run: false;
- OSS audit wallet/private-key use: false;
- OSS audit dependencies installed globally: false;
- Repricing Research v1 module path: `polymarket/repricing_research/`;
- Repricing Research v1 document:
  `docs/polymarket/REPRICING_RESEARCH_V1.md`;
- Repricing Research v1 short replay output:
  `polymarket/models/repricing_research_v1/short_replay/`;
- Repricing Research v1 short replay input sessions:
  `polymarket/runs/microstructure_development_v1/20260623_120611/session.jsonl`
  and
  `polymarket/runs/microstructure_development_v1_batch_002/20260623_214015/session.jsonl`;
- Repricing Research v1 short replay rows/signals: 28;
- Repricing Research v1 target-before-stop wins: 16;
- Repricing Research v1 paper win rate: 57.14%;
- Repricing Research v1 average favorable repricing: 0.3265;
- Repricing Research v1 average adverse move: -0.1164;
- Repricing Research v1 simulated P&L before fees/slippage: 0.9665;
- Repricing Research v1 simulated P&L after conservative slippage: 0.4065;
- Repricing Research v1 max drawdown: 0.4050;
- Repricing Research v1 expectancy per signal: 0.0145;
- Repricing Research v1 signals per hour: 2.1333;
- Repricing Research v1 Data Sufficiency Audit path:
  `polymarket/models/repricing_research_v1/data_sufficiency_audit/`;
- Repricing Research v1 current evidence level:
  `INSUFFICIENT_SMOKE_ONLY`;
- Repricing Research v1 observed hours in current sample: 13.1255;
- Repricing Research v1 signals by asset: 5 BTC, 8 ETH, and 15 SOL;
- Repricing Research v1 signals by side: 5 YES and 23 NO;
- Repricing Research v1 exits: 16 repricing target, 8 stop loss, and 4
  timeout;
- Repricing Research v1 per-signal after-slippage P&L standard deviation:
  0.0948, variance 0.0090, median 0.0175, q25 -0.0500, q75 0.0400;
- Repricing Research v1 side stability: YES expectancy 0.1200, NO expectancy
  -0.0084;
- Repricing Research v1 asset stability: BTC expectancy 0.0890, ETH
  expectancy -0.0094, SOL expectancy 0.0024;
- Repricing Research v1 horizon coverage: 30s 100.0%, 60s 67.86%, 120s
  64.29%, 180s 0.0%;
- Repricing Research v1 weak evidence floor: at least 100 signals, 40 observed
  hours, 3 independent sessions, 25 signals per asset, 35 signals per side,
  and after-slippage expectancy at least 0.005;
- Repricing Research v1 moderate evidence floor: at least 300 signals, 120
  observed hours, 6 sessions, 75 signals per asset, 100 signals per side, and
  after-slippage expectancy at least 0.008;
- Repricing Research v1 strong development floor: at least 1,000 signals, 400
  observed hours, 20 sessions, 250 signals per asset, 350 signals per side,
  after-slippage expectancy at least 0.010, positive stress results, and no
  single asset/session contributing more than 40% of P&L;
- Repricing Research v1 data is sufficient for diagnostics: true;
- Repricing Research v1 data is sufficient for model development: false;
- Repricing Research v1 data is sufficient for shadow strategy validation:
  false;
- Repricing Research v1 data is sufficient for edge claims: false;
- Repricing Research v1 holdout outcomes read: false;
- Repricing Research v1 validation protocol modified: false;
- interrupted 12-hour Batch 003 capture process was stopped after the strategy
  direction changed; any partial run artifact remains excluded from analysis;
- Combined Batch 001-002 microstructure diagnostics path:
  `polymarket/models/microstructure_diagnostics_batches_001_002/`;
- Combined Batch 001-002 diagnostic decision:
  `DATASET_STILL_TOO_SMALL_OR_UNSTABLE`;
- Combined Batch 001-002 diagnostic rows analyzed: 426;
- Combined Batch 001-002 diagnostic split: chronological atomic window-group
  297 train rows / 129 evaluation rows, development-only and proxy-labelled;
- Combined Batch 001-002 rows per asset: 142 BTC, 142 ETH, and 142 SOL;
- Combined Batch 001-002 proxy outcomes: 213 UP and 213 DOWN;
- Combined Batch 001-002 microstructure feature coverage: 8,094 / 8,094
  cells populated (100.0%);
- Combined Batch 001-002 microstructure missing cells: 0;
- Combined Batch 001-002 best diagnostic result: YES price only, evaluation
  log loss 0.546792, Brier 0.182709, accuracy 72.87%, ROC AUC 0.8055;
- Combined Batch 001-002 microstructure-only diagnostic model: evaluation log
  loss 0.677837, Brier 0.241526, accuracy 56.59%, ROC AUC 0.6228;
- Combined Batch 001-002 YES-plus-microstructure diagnostic model:
  evaluation log loss 0.610897, Brier 0.210249, accuracy 65.89%, ROC AUC
  0.7295;
- Combined Batch 001-002 YES price beaten on development data: false;
- Combined Batch 001-002 per-asset best diagnostic predictor: YES price for
  BTC, ETH, and SOL;
- Combined Batch 001-002 stable possible incremental microstructure features:
  none under the fixed batch-stability rule;
- Combined Batch 001-002 features helping only one batch:
  `quote_age_seconds`, `time_since_quote_update_seconds`,
  `repricing_velocity`, `consecutive_quote_stability`, and
  `cross_asset_yes_dispersion`;
- Combined Batch 001-002 unstable feature: `book_imbalance`;
- Combined Batch 001-002 diagnostics holdout outcomes read: false;
- Combined Batch 001-002 diagnostics holdout evaluation run: false;
- Combined Batch 001-002 diagnostics validation protocol modified: false;
- Independent Microstructure Development Dataset Batch 002 session:
  `20260623_214015`;
- Batch 002 session path:
  `polymarket/runs/microstructure_development_v1_batch_002/20260623_214015/session.jsonl`;
- Batch 002 configured / observed duration: 21,600.0 / 21,600.013484
  seconds;
- Batch 002 campaign completeness: complete, 100.0% temporal coverage;
- Batch 002 observation continuity: 10,800 / 10,800 checkpoints (100.0%);
- Batch 002 maximum checkpoint gap: 2.038265 seconds;
- Batch 002 gaps over 10 / 60 / 300 seconds: 0 / 0 / 0;
- Batch 002 fatal capture errors: 0;
- Batch 002 discovery failures: 53, retained as independent diagnostics;
- Batch 002 microstructure events: 32,089;
- Batch 002 events by asset: 10,699 BTC, 10,691 ETH, and 10,699 SOL;
- Batch 002 raw microstructure coverage: quote age, latency, bid/ask size,
  total depth, book imbalance, spread, quote-change frequencies, and stability
  100%; repricing velocity 99.3175%; repricing acceleration 98.6350%;
  spread change/velocity/compression 99.3175%; cross-asset
  dispersion/relative YES 99.9907%;
- Batch 002 feature export rows: 213, with 71 BTC, 71 ETH, and 71 SOL;
- Batch 002 feature export outcomes: 123 UP and 90 DOWN using explicit proxy
  labels for development ingestion only;
- Batch 002 all 19 microstructure feature columns populated on feature rows:
  100%;
- Batch 002 core feature missingness: 1 / 4,260 cells missing (99.9765%
  complete), from `probability_change_30s`;
- Batch 002 CSV and Parquet repeat-export hashes: deterministic;
- Batch 002 CSV SHA-256:
  `4a9b5ea0628bef82e2202cfdbf12efe3759f92609f0f822a624aa414f01ce318`;
- Batch 002 Parquet SHA-256:
  `74004dadba89d3230674008ca74e35d730e1b471b6fbba017902818800766f4f`;
- Batch 002 replay metrics, campaign completeness, and microstructure coverage:
  exact match;
- Batch 002 dataset location:
  `polymarket/data/microstructure_dataset_batch_002/`;
- Batch 002 canonical training data merge status: not merged;
- Batch 002 holdout outcomes read: false;
- Batch 002 validation protocol modified: false;
- Batch 002 completed after one failed incomplete attempt
  (`20260623_185001`) exposed an async discovery exception-handling bug; the
  failed attempt has no `session_completed` marker and was excluded from the
  Batch 002 dataset export;
- Batch 001 microstructure diagnostics path:
  `polymarket/models/microstructure_diagnostics_batch_001/`;
- Batch 001 diagnostic decision: `DATASET_TOO_SMALL_OR_UNSTABLE`;
- Batch 001 diagnostic rows analyzed: 213;
- Batch 001 diagnostic split: chronological 149 train rows / 64 evaluation
  rows, development-only and proxy-labelled;
- Batch 001 best diagnostic result: YES price only, evaluation log loss
  0.568340, Brier 0.192367, accuracy 68.75%, ROC AUC 0.7882;
- Batch 001 microstructure-only diagnostic model: evaluation log loss
  0.628730, Brier 0.220724, accuracy 62.50%, ROC AUC 0.7395;
- Batch 001 YES-plus-microstructure diagnostic model: evaluation log loss
  0.594523, Brier 0.203701, accuracy 71.875%, ROC AUC 0.7672;
- Batch 001 YES price beaten on development data: false;
- Batch 001 possible incremental feature by residual partial correlation:
  `cross_asset_yes_dispersion`;
- Batch 001 feature redundant with YES price: `book_imbalance`;
- Batch 001 unstable microstructure features: none by the fixed half-sample
  one-standard-deviation rule;
- Batch 001 redundant feature pairs include `yes_change_frequency_30s` /
  `no_change_frequency_30s`, `spread_change` / `spread_compression`,
  `time_since_quote_update_seconds` / `consecutive_quote_stability`, and
  spread-change variants;
- Batch 001 diagnostics holdout outcomes read: false;
- Batch 001 diagnostics holdout evaluation run: false;
- Batch 001 diagnostics validation protocol modified: false;
- Independent Microstructure Development Dataset Batch 001 session:
  `20260623_120611`;
- latest session path:
  `polymarket/runs/microstructure_development_v1/20260623_120611/session.jsonl`;
- Batch 001 configured / observed duration: 21,600.0 / 21,600.009733
  seconds;
- Batch 001 campaign completeness: complete, 100.0% temporal coverage;
- Batch 001 observation continuity: 10,800 / 10,800 checkpoints (100.0%);
- Batch 001 maximum checkpoint gap: 2.042252 seconds;
- Batch 001 gaps over 10 / 60 / 300 seconds: 0 / 0 / 0;
- Batch 001 fatal capture errors: 0;
- Batch 001 discovery failures: 77, retained as independent diagnostics;
- Batch 001 microstructure events: 32,041;
- Batch 001 events by asset: 10,681 BTC, 10,684 ETH, and 10,676 SOL;
- Batch 001 raw microstructure coverage: quote age, latency, bid/ask size,
  total depth, book imbalance, spread, quote-change frequencies, and stability
  100%; repricing velocity 99.3165%; repricing acceleration 98.6330%;
  spread change/velocity/compression 99.3165%; cross-asset
  dispersion/relative YES 99.9782%;
- Batch 001 feature export rows: 213, with 71 BTC, 71 ETH, and 71 SOL;
- Batch 001 feature export outcomes: 90 UP and 123 DOWN using explicit proxy
  labels for development ingestion only;
- Batch 001 all 19 microstructure feature columns populated on feature rows:
  100%;
- Batch 001 core feature missingness: 6 / 4,260 cells missing (99.8592%
  complete), from `momentum_medium` and `return_60s`;
- Batch 001 CSV and Parquet repeat-export hashes: deterministic;
- Batch 001 CSV SHA-256:
  `4e790466fe24238a7dde282d1412a8aa771f1897c4b7f1d979bda21fbebef8a2`;
- Batch 001 Parquet SHA-256:
  `434376318dbe4acea954af1a895fa01e7d023c27329d628381fea3e123f0b553`;
- Batch 001 replay metrics, campaign completeness, and microstructure coverage:
  exact match;
- Batch 001 dataset location:
  `polymarket/data/microstructure_dataset_batch_001/`;
- canonical training data merge status: not merged;
- holdout outcomes read: false;
- validation protocol modified: false;
- public microstructure smoke session: `20260623_114635`;
- configured / observed duration: 900.0 / 900.008502 seconds;
- campaign completeness: complete, 100.0% temporal coverage;
- observation continuity: 450 / 450 checkpoints (100.0%);
- maximum checkpoint gap: 2.012861 seconds;
- microstructure events: 1,328;
- events by asset: 443 BTC, 443 ETH, 442 SOL;
- quote timestamp/age, latency, bid/ask size, total depth, book imbalance,
  spread, change frequencies, stability: 100% populated;
- repricing velocity: 1,316 / 1,328 (99.0964%);
- repricing acceleration: 1,304 / 1,328 (98.1928%);
- spread change/velocity/compression: 1,316 / 1,328 (99.0964%);
- cross-asset dispersion/relative YES: 1,327 / 1,328 (99.9247%);
- Feature Engine smoke export: 6 rows, 2 per asset;
- all 19 microstructure fields populated on smoke feature rows: 100%;
- CSV and Parquet repeat-export hashes: deterministic;
- replay metrics, completeness, and microstructure coverage: exact match;
- public smoke decision: `READY_FOR_PRODUCTION_CAPTURE`;
- decision scope: research capture only, not trading production;
- microstructure event schema: v1;
- optional Feature Engine microstructure columns: 19;
- deterministic raw quote/depth coverage: 100%;
- deterministic velocity coverage: 90%;
- deterministic acceleration coverage: 80%;
- deterministic synchronized cross-asset dispersion coverage: 96.67%;
- historical schema-v1 coverage: 0% because sessions predate implementation;
- real public schema-v1 coverage: unmeasured;
- legacy v5 shadow replay compatibility: verified;
- strictly as-of Feature Engine selection and future-event rejection: verified;
- frozen validation protocol hashes: unchanged and verified;
- baseline and diagnostic report hashes: unchanged and verified;
- holdout outcomes read: false;
- Baseline Failure Diagnostics conclusion: `FEATURE_SET_INCOMPLETE`;
- fixed feature groups beating YES price on both primary metrics: 0 / 8;
- logistic better individual validation rows: 71 / 153;
- YES price better or equal individual validation rows: 82 / 153;
- meaningful regimes where logistic beats YES on both metrics: 0;
- only apparent segment win: medium lag, 8 rows, rejected as insufficient;
- BTC logistic / YES log loss: 0.664369 / 0.625346;
- ETH logistic / YES log loss: 0.679225 / 0.627134;
- SOL logistic / YES log loss: 0.659881 / 0.598903;
- exact redundant pair: `yes_price` / `yes_no_spread`, correlation 1.0;
- near-redundant pair: `detection_delay` / `late_window_flag`, correlation
  0.9797;
- validation feature missingness: zero;
- all validation rows use the early-window feature anchor;
- largest mean distribution shifts include return_30s (-0.392 train standard
  deviations), return_15s (-0.370), and return_5s (-0.347);
- return_15s outcome correlation changes from +0.192 train to -0.065
  validation;
- diagnostic artifacts and deterministic hashes: verified;
- exactly one recommended hypothesis: new market-microstructure information;
- holdout outcomes read: false;
- Baseline Probability Model v1 verdict: `NO_EDGE_FOUND_YET`;
- best validation predictor: Polymarket YES price;
- constant-prior validation log loss / Brier: 0.699768 / 0.253309;
- asset-prior validation log loss / Brier: 0.700291 / 0.253566;
- YES-price validation log loss / Brier: 0.617128 / 0.216683;
- logistic validation log loss / Brier: 0.667825 / 0.238251;
- logistic validation accuracy / ROC AUC: 56.21% / 0.6462;
- YES-price validation accuracy / ROC AUC: 62.75% / 0.6721;
- logistic train log loss / Brier: 0.590650 / 0.204572;
- logistic train-to-validation log-loss gap: +0.077175;
- logistic failed to beat YES price on BTC, ETH, and SOL independently;
- holdout outcomes read: false;
- baseline artifacts and deterministic hashes: verified;
- validation protocol: `time_ordered_holdout_v1`, frozen and hash-verified;
- source commitment:
  `2be24229ef79638abbe3a843e5d79c97c4834d87ef19f0bcd5b5b736c897c276`;
- source windows / rows: 356 / 1,064;
- train: 248 windows / 741 rows, ending June 22, 2026 13:55 UTC;
- validation: 51 windows / 153 rows, from June 22, 2026 14:10 UTC through
  22:30 UTC;
- untouched holdout: 53 windows / 158 rows, beginning June 22, 2026 22:45 UTC;
- excluded boundary evidence: 4 windows / 12 rows;
- purge/embargo: one complete five-minute window on each side of both raw
  boundaries;
- sealed holdout label commitment:
  `9ea0faa072dd9c74146011da9cd6599e643fb7f40c2f8ce9643bb17f0394ca2b`;
- development loader exposes no holdout outcomes;
- model-development authorization: true for train/validation only;
- final holdout evaluation authorization: false;
- Batch 006 session: `20260622_211037`;
- Batch 006 continuity: 10,800 / 10,800 checkpoints (100.0%);
- Batch 006 temporal coverage: 100.0%;
- Batch 006 maximum checkpoint gap: 2.035024 seconds;
- Batch 006 gaps over 10 / 60 / 300 seconds: 0 / 0 / 0;
- Batch 006 fatal capture errors: 0;
- Batch 006 discovery failures: 41, retained as independent diagnostics;
- Batch 006 clean-row growth: 851 to 1,064 (+213);
- clean public rows per asset: 353 BTC, 355 ETH, 356 SOL;
- clean public outcomes: 527 UP, 537 DOWN;
- minority class share: 49.53%;
- authoritative resolutions: 1,391 / 1,398 (99.50%);
- feature completeness: 99.18%;
- missing values: 0.55% of all cells;
- duplicate rows: 0;
- dataset quality score: 99.52/100;
- Batch 006 manifest verdict: `DATA_GATE_PASSED`;
- total milestone progress: 100.0%;
- deterministic resolution replay: verified;
- evidence-pipeline training authorization: true;
- development-only baseline fitting authorization: true;
- final holdout evaluation authorization: false until one candidate and all
  evaluation assumptions are frozen;
- Batch 005 session: `20260622_110942`;
- Batch 005 continuity: 10,800 / 10,800 checkpoints (100.0%);
- Batch 005 temporal coverage: 100.0%;
- Batch 005 maximum checkpoint gap: 2.04033 seconds;
- Batch 005 gaps over 10 / 60 / 300 seconds: 0 / 0 / 0;
- Batch 005 fatal capture errors: 0;
- Batch 005 reference coverage / market data gap: 99.8426% / 0.8471%;
- Batch 005 completed windows / observed markets: 213 / 222;
- Batch 005 clean-row growth: 636 to 851 (+215);
- clean public rows per asset: 282 BTC, 284 ETH, 285 SOL;
- clean public outcomes: 427 UP, 424 DOWN;
- minority class share: 49.82%;
- authoritative resolutions: 1,174 / 1,176 (99.83%);
- proxy agreement: 937 matched / 61 mismatched (93.89%);
- feature completeness: 98.97%;
- duplicate rows: 0;
- dataset quality score: 99.60/100;
- Batch 005 manifest verdict: `INSUFFICIENT_PUBLIC_SAMPLE`;
- total milestone progress: 85.1%;
- deterministic resolution replay: verified;
- project training authorization: false because the 1,000-row total sample
  gate and untouched-holdout requirement remain unmet;
- Batch 004 session: `20260621_220439`;
- Batch 004 continuity: 10,800 / 10,800 checkpoints (100.0%);
- Batch 004 maximum checkpoint gap: 2.04185 seconds;
- Batch 004 gaps over 10 / 60 / 300 seconds: 0 / 0 / 0;
- Batch 004 reference coverage / market data gap: 99.9444% / 0.7364%;
- Batch 004 completed windows / observed markets: 211 / 222;
- Batch 004 clean-row growth: 368 to 636 (+268);
- clean public rows per asset: 210 BTC, 212 ETH, 214 SOL;
- clean public outcomes: 324 UP, 312 DOWN;
- minority class share: 49.06%;
- authoritative resolutions: 951 / 954 (99.69%);
- proxy agreement: 728 matched / 56 mismatched (92.86%);
- authoritative candidate rows: 908;
- sparse rows excluded: 272;
- feature completeness: 98.62%;
- missing values: 0.92% of all cells;
- duplicate rows: 0;
- dataset quality score: 99.12/100;
- Batch 004 manifest verdict: `INSUFFICIENT_PUBLIC_SAMPLE`;
- total milestone progress: 63.6%;
- per-asset sample progress: BTC 100%, ETH 100%, SOL 100%;
- deterministic resolution replay: verified;
- project training authorization: false because the 1,000-row total sample
  gate and untouched-holdout requirement remain unmet;
- accelerated cadence test: 300 / 300 checkpoints, 100.0% coverage;
- accelerated maximum checkpoint gap: 2.0 seconds;
- accelerated gaps over 10 / 60 / 300 seconds: 0 / 0 / 0;
- simulated recovery versus Batch 003: 14.8241% to 100.0%, an 85.1759
  percentage-point improvement;
- current Windows AC sleep timeout: 18,000 seconds;
- current Windows AC hibernate timeout: disabled;
- overnight preflight status: unsafe / blocked until AC sleep is disabled;
- capture process now requests Windows `ES_SYSTEM_REQUIRED` for its lifetime;
- Batch 003 session: `20260620_213414`;
- Batch 003 pipeline status: completed; deterministic replay verified;
- Batch 003 clean-row growth: 229 to 368 (+139);
- clean public rows per asset: 122 BTC, 123 ETH, 123 SOL;
- clean public outcomes: 198 UP, 170 DOWN;
- authoritative resolutions: 510 / 510 (100.00%);
- feature completeness: 98.27%;
- dataset quality score: 97.58/100;
- total milestone progress: 36.8%;
- Batch 003 capture checkpoints: 1,601;
- Batch 003 actual checkpoint span: 18,884.756 seconds
  (5:14:44.756);
- Batch 003 terminal observation gap: approximately 25,714.360 seconds
  (7:08:34.360);
- Batch 003 recorded runtime/span: 44,599.110 / 44,599.118 seconds;
- Batch 003 discovery failures: 10, with endpoint, exception type, and full
  message preserved;
- Batch 003 reference coverage / market data gap: 99.94% / 6.87%;
- Batch 003 integrity disposition: data rows remain usable, but the campaign
  is not accepted as a continuous six-hour evidence campaign;
- corrected Batch 003 verdict: `INCOMPLETE_CAMPAIGN`;
- Batch 003 checkpoint coverage: 1,601 / 10,800 (14.8241%);
- Batch 003 maximum checkpoint gap: 25,714.360435 seconds;
- Batch 003 gaps over 10 / 60 / 300 seconds: 530 / 5 / 1;
- Batch 003 effective observed duration: 18,884.756204 seconds;
- Batch 003 continuity rejection reasons:
  `checkpoint_coverage_below_95_percent` and
  `checkpoint_gap_over_300_seconds`;
- Batch 003 total checkpoint shortfall: 9,199;
- checkpoint shortfall while the host was awake: approximately 7,842
  (85.25% of the total shortfall);
- checkpoint shortfall during the remaining intended runtime after sleep
  began: approximately 1,357 (14.75%);
- Windows sleep interval: 25,687.148 seconds, from 02:49:06.910 UTC to
  09:57:14.058 UTC, wake source power button;
- active checkpoint interval distribution: minimum 7.847 seconds, median
  9.378 seconds, mean 11.803 seconds, p95 28.488 seconds;
- active-loop estimated work time excluding the configured post-cycle sleep:
  median 7.378 seconds and mean 9.803 seconds;
- each discovery cycle performs ten sequential Gamma requests; each poll also
  performs three sequential reference requests and up to three sequential
  CLOB quote requests before writing `capture_checkpoint`;
- because every observed cycle exceeded the five-second discovery interval,
  discovery ran on effectively every cycle, producing approximately 16,010
  sequential Gamma requests over 1,601 checkpoints;
- ten explicit Gamma discovery failures added an estimated 203.821 seconds
  above the clean-iteration median, but clean iterations still had a
  9.325-second median; timeouts amplified rather than caused the cadence
  failure;
- previous public sessions show the same architecture-limited cadence:
  11.661 seconds mean for `20260619_174322` and 10.394 seconds mean for
  `20260619_223637`;
- resolution processing did not interfere with capture because it begins only
  after `LongShadowCapture.run()` returns;
- finalized batch cutoff: June 21, 2026 09:57:33 UTC;
- Batch 002 requested duration: 21,600 seconds;
- Batch 002 timestamped live-observation span: 18,315.049 seconds
  (5:05:15.049), ending June 20, 2026 03:41:52.553 UTC;
- Batch 002 synthetic terminal gap: 3,284.951 seconds (54:44.951);
- Batch 002 process path: normal `session_completed`, not a crash or forced
  termination;
- Batch 002 session coverage: 189 markets (63 per asset), 5,289/5,289
  reference points, and 4,815/5,289 successful market quote points;
- Batch 002 discovery failure detail: unrecoverable beyond `URLError` because
  exception reasons and stdout/stderr were not persisted;
- new campaigns record actual UTC start/completion, monotonic elapsed runtime,
  observed UTC span, temporal coverage percentage, shortfall, and detected
  wall-clock discontinuities;
- temporal coverage below 99% with more than five seconds of shortfall is
  marked `incomplete_temporal_coverage`; the evidence-batch verdict becomes
  `INCOMPLETE_CAMPAIGN` and project training authorization remains false;
- each new discovery failure records timestamp, endpoint URL, exception type,
  and exception message as an independent `discovery_failure` event;
- partial discovery results survive failures from individual Gamma endpoints;
- new capture sessions preserve `campaign.stdout.log` and
  `campaign.stderr.log`;
- frozen input sessions: 20;
- public markets discovered for resolution: 510;
- authoritative resolutions: 510 (100.00%);
- proxy agreement: 399 matched / 36 mismatched (91.72%);
- sparse rows excluded: 116;
- clean public/mock rows: 368 / 0;
- minority class share: 46.20%;
- feature completeness: 98.27%;
- missing values: 1.15% of all cells;
- duplicate rows: 0;
- dataset quality score: 97.58/100;
- Dataset Quality Engine recommendation: true;
- batch verdict: `INSUFFICIENT_PUBLIC_SAMPLE`;
- total milestone progress: 36.8%;
- project training authorization: false because sample-size gates are unmet.

## Wallet Score Fixture Review v1

Wallet Score Fixture Review v1 is complete.

Output:

- `polymarket/models/wallet_intelligence_v1/wallet_score_fixture_review/wallet_score_fixture_review_report.md`

Files inspected:

- `polymarket/wallet_intelligence/wallet_score.py`
- `polymarket/wallet_intelligence/lifecycle_metrics.py`
- `tests/polymarket/test_wallet_intelligence.py`
- `polymarket/models/wallet_intelligence_v1/wallet_score_design/wallet_score_design_v1.md`
- `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_scores.csv`
- `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_scores_summary.json`
- `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_score_validation.json`
- `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_score_report.md`

Review findings:

- no bounded correctness bugs were found;
- approved structural score inputs remain the only scoring inputs;
- forbidden inputs remain absent;
- score bounds, deterministic calculation, deterministic ordering, missing
  metric handling, repeatable export, component bounds, penalty bounds, output
  schema completeness, and source provenance remain valid;
- interpretation language remains limited to structural research-priority
  labels only.

Score distribution reviewed:

- 1 `medium_priority`;
- 3 `low_priority`;
- 2 `insufficient_visible_structure`;
- 0 `high_priority`.

Threshold assessment:

- the current behavior is acceptable for the six-wallet fixture;
- the absence of `high_priority` wallets is conservative rather than a defect;
- no thresholds or penalties should be adjusted before a broader evidence
  collection design.

Strict exclusions remain active:

- no new score inputs;
- no threshold or penalty change;
- no public ingestion;
- no PnL, ROI, realized profit, Sharpe, execution quality, copyability, alpha
  claims, mark-to-market values, final resolved win/loss outcomes, sealed
  holdout labels, private wallet data, order-placement data, authenticated
  trading data, live trading, automatic trade copying, wallet/private-key use,
  order placement, capture campaign, production model training, sealed holdout
  inspection, or holdout evaluation.

Next research task: Wallet Score Broader Evidence Collection Design v1. It
should design a bounded, public, read-only evidence expansion plan before any
broader ingestion, score expansion, or threshold adjustment.

## Wallet Score Broader Evidence Collection Design v1

Wallet Score Broader Evidence Collection Design v1 is complete.

Output:

- `polymarket/models/wallet_intelligence_v1/wallet_score_broader_evidence_design/broader_evidence_plan.md`

Design summary:

- target sample: 30 public wallets;
- composition: 6 existing seed wallets, up to 12 fast BTC/ETH/SOL Up/Down
  candidates, up to 6 mixed or non-fast-crypto controls, and up to 6
  lower-activity insufficient-data controls;
- purpose: evaluate Wallet Score v1 score behavior beyond the six-wallet
  fixture, not wallet profitability, alpha, copyability, or trading quality;
- no implementation, ingestion, scoring change, threshold change, or metric
  generation change was added in this design task.

Safety limits:

- maximum wallets: 30;
- maximum primary activity pages per wallet: 2;
- maximum primary activity rows per wallet: 200;
- maximum primary activity rows overall: 6,000;
- maximum `/trades` cross-check pages per wallet: 1;
- maximum cross-check rows per wallet: 100;
- maximum cross-check rows overall: 3,000;
- maximum retries per page: 2;
- minimum one-second delay between wallet requests;
- no market-wide scans, recursive profile crawling, automatic follow-wallet
  expansion, authenticated requests, wallet/private-key use, order placement,
  capture campaigns, production model training, sealed holdout inspection, or
  holdout evaluation.

Healthy score behavior criteria:

- non-degenerate distribution across at least three score bands;
- deterministic outputs and stable ordering;
- insufficient-data rate between 10% and 45%;
- `high_priority` share no greater than 20%;
- visible separation between fast-crypto candidates and controls;
- no high score driven primarily by one fragile bounded-history artifact.

Suspicious behavior criteria:

- more than 70% of wallets in one bucket;
- more than 20% `high_priority`;
- more than 60% `insufficient_visible_structure`;
- high-priority scores driven by tiny samples, all-open positions, or
  bounded-history oversold artifacts;
- unstable ordering or guessed unavailable fields.

The current user-directed override superseded the immediate broader-evidence
implementation loop and created the first Wallet Watchlist v1 artifact from
existing Wallet Score outputs only.

## Wallet Watchlist v1

Wallet Watchlist v1 is complete.

Code and CLI:

- watchlist logic lives in
  `polymarket/wallet_intelligence/wallet_watchlist.py`;
- the CLI command is:
  `python -m polymarket.wallet_intelligence wallet-watchlist`.

Outputs:

- `polymarket/models/wallet_intelligence_v1/wallet_watchlist_v1/wallet_watchlist.csv`
- `polymarket/models/wallet_intelligence_v1/wallet_watchlist_v1/wallet_watchlist_summary.json`
- `polymarket/models/wallet_intelligence_v1/wallet_watchlist_v1/wallet_watchlist_report.md`

Scope and result:

- input: existing
  `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_scores.csv`;
- source score SHA-256:
  `52ceafde32dc6e6c4d07829e824a83c9b767bc7da4d1b3461188e6cda2e3b2ad`;
- wallets input: 6;
- wallets included: 6;
- wallets excluded by minimum visibility: 0;
- priority bucket distribution: 1 `medium_priority`, 3 `low_priority`, and
  2 `insufficient_visible_structure`;
- deterministic `wallet_watchlist.csv` SHA-256:
  `841dd43c7173161938c52349f753b19cd7ef5b680b5bcb249042a2f57e565caf`.

Validation:

- deterministic ordering: passed;
- output schema completeness: passed;
- reason codes present: passed;
- research actions present: passed;
- forbidden metric fields absent: passed;
- forbidden claim phrases absent: passed;
- repeatable export: passed;
- Wallet Intelligence tests: 29 passing;
- full automated suite: 123 passing.

Interpretation:

- the watchlist is a monitoring/research artifact only;
- it is not a trading signal;
- it is not a copy-trading recommendation;
- it is not a profitability ranking;
- it is based only on bounded public history and existing Wallet Score
  outputs;
- no score formula, thresholds, PnL, ROI, Sharpe, alpha, copyability,
  mark-to-market, execution-quality, order-placement, wallet/private-key,
  sealed-holdout, or holdout-evaluation logic was added.

## Wallet Watchlist Review v1

Wallet Watchlist Review v1 is complete.

Output:

- `polymarket/models/wallet_intelligence_v1/wallet_watchlist_review/wallet_watchlist_review_report.md`

Files inspected:

- `polymarket/wallet_intelligence/wallet_watchlist.py`
- `polymarket/models/wallet_intelligence_v1/wallet_watchlist_v1/wallet_watchlist.csv`
- `polymarket/models/wallet_intelligence_v1/wallet_watchlist_v1/wallet_watchlist_summary.json`
- `polymarket/models/wallet_intelligence_v1/wallet_watchlist_v1/wallet_watchlist_report.md`
- `polymarket/models/wallet_intelligence_v1/wallet_score_fixture/wallet_scores.csv`
- `tests/polymarket/test_wallet_intelligence.py`

Review findings:

- no score-formula, threshold, inclusion-gate, or safety-boundary bug was
  found;
- the watchlist uses existing Wallet Score outputs only;
- all six score-fixture wallets remain included and zero wallets are excluded
  by the minimum visibility gate;
- every included wallet has clear reason codes, structural strengths,
  structural risks, and a research-only next action;
- deterministic ordering and repeatable export remain validated;
- no trading recommendation, profitability, alpha, copyability, execution
  quality, PnL, ROI, Sharpe, or mark-to-market claim is present.

Small bounded review fixes:

- `wallet_watchlist_report.md` now includes strengths, risks, and next
  research action for each watchlist row;
- high/medium action wording changed from "monitor in research watchlist" to
  "include in research watchlist" to avoid implying live monitoring.

Updated watchlist artifact:

- wallets input: 6;
- wallets included: 6;
- wallets excluded: 0;
- priority bucket distribution: 1 `medium_priority`, 3 `low_priority`, and
  2 `insufficient_visible_structure`;
- source score SHA-256:
  `52ceafde32dc6e6c4d07829e824a83c9b767bc7da4d1b3461188e6cda2e3b2ad`;
- updated watchlist CSV SHA-256:
  `f8add3e19afb27ed800e2eb87cb8b045df1ac40356f462b5a2e322e5ef394e8c`.

Tests:

- Wallet Intelligence tests: 29 passing;
- full automated suite: 123 passing.

The current user-directed research sprint superseded the old
Wallet Watchlist Broader Evidence Batch v1 loop and completed the broader
evidence run as Wallet Copyability Feasibility Sprint v1.

## Wallet Copyability Feasibility Sprint v1

Wallet Copyability Feasibility Sprint v1 is complete.

Code and CLI:

- sprint orchestration lives in
  `polymarket/wallet_intelligence/copyability_sprint.py`;
- the CLI command is:
  `python -m polymarket.wallet_intelligence copyability-sprint`.

Primary outputs:

- `polymarket/models/wallet_intelligence_v1/wallet_copyability_feasibility_v1/wallet_copyability_research.csv`
- `polymarket/models/wallet_intelligence_v1/wallet_copyability_feasibility_v1/wallet_copyability_summary.json`
- `polymarket/models/wallet_intelligence_v1/wallet_copyability_feasibility_v1/wallet_copyability_report.md`

Pipeline outputs:

- `polymarket/wallet_intelligence/watched_wallets_broader_v1.example.csv`
- `polymarket/data/wallet_intelligence/trade_history_broader_v1/`
- `polymarket/models/wallet_intelligence_v1/lifecycle_reconstruction_broader_v1/`
- `polymarket/models/wallet_intelligence_v1/lifecycle_metrics_broader_v1/`
- `polymarket/models/wallet_intelligence_v1/wallet_score_broader_evidence_v1/`
- `polymarket/models/wallet_intelligence_v1/wallet_watchlist_broader_v1/`

Evidence size:

- wallets selected: 30;
- primary activity rows normalized: 5,765;
- cross-check `/trades` rows fetched: 3,000;
- lifecycle candidates reconstructed: 2,135;
- wallets scored and classified: 30.

Classification counts:

- `monitor_candidate`: 11;
- `needs_more_history`: 17;
- `insufficient_signal`: 2;
- `exclude_for_now`: 0.

Wallet Score bucket distribution:

- `high_priority`: 3;
- `medium_priority`: 13;
- `low_priority`: 12;
- `insufficient_visible_structure`: 2.

Research findings:

- Wallet Score separated the broader sample into four structural groups, so
  the score is not degenerate on this batch;
- strongest score drivers were fast-crypto relevance, lifecycle coverage,
  lifecycle activity, still-open penalty, and concentration penalty;
- no score component or penalty had zero range in the batch;
- five wallets looked structurally interesting despite weak raw evidence,
  mainly because bounded history leaves most visible lifecycle state still
  open;
- largest blockers remain realized outcome joins, expiry joins, complete
  unbounded wallet history, entry-to-exit holding time, observation delay,
  slippage, liquidity/fill uncertainty, queue position, maker/taker
  completeness, and external BTC/ETH/SOL reference alignment.

Validation:

- bounded public read-only limits were respected;
- deterministic ordering: passed;
- deterministic export/repeatability: passed;
- every wallet classified: passed;
- reason codes present for every wallet: passed;
- forbidden metric fields absent: passed;
- forbidden claim phrases absent: passed.

Research conclusion:

Based on the current bounded public evidence, Wallet Intelligence is moving
toward a useful copy-trading research system only as a structural triage
layer: 11 of 30 wallets became `monitor_candidate` and the score separated
wallets into multiple structural groups, but missing realized outcomes, expiry
joins, complete history, timing-delay, slippage, and liquidity evidence remain
too significant for any conclusion about copy outcomes, market advantage,
returns, or trading use.

Strict exclusions preserved:

- no Wallet Score formula or threshold changes;
- no PnL, ROI, Sharpe, market-advantage, return, mark-to-market,
  execution-quality, or trading-suitability computation;
- no wallet/private-key use, order placement, trade copying, live monitoring,
  capture campaign, production model training, sealed holdout inspection, or
  holdout evaluation.

Wallet Intelligence Information Gain Sprint v1 superseded the combined
expiry/outcome next-step framing and selected a narrower, higher cost/value
successor: Wallet Market Expiry Join Sprint v1.

## Wallet Intelligence Information Gain Sprint v1

Wallet Intelligence Information Gain Sprint v1 is complete.

Outputs:

- `polymarket/models/wallet_intelligence_v1/information_gain_sprint_v1/information_gain_matrix.csv`
- `polymarket/models/wallet_intelligence_v1/information_gain_sprint_v1/wallet_information_gain_report.md`
- `polymarket/models/wallet_intelligence_v1/information_gain_sprint_v1/wallet_research_roadmap.md`

Purpose:

- determine which missing information layer should be implemented next to
  maximize Wallet Intelligence quality;
- evaluate all candidate layers independently;
- do not implement any layer, change Wallet Score, change Wallet Watchlist, or
  redesign the pipeline.

Evidence base:

- 30 wallets classified in the previous copyability sprint;
- 5,765 normalized public primary activity rows;
- 3,000 `/trades` cross-check rows;
- 2,135 reconstructed lifecycle candidates;
- 1,735 still-open lifecycle candidates;
- 296 partial exits, 80 full exits, and 24 bounded-history oversold
  candidates;
- Wallet Score separated the batch into four structural buckets;
- previous blockers were realized outcome joins, expiry joins, complete
  unbounded history, holding time, observation delay, slippage, liquidity/fill
  uncertainty, queue position, maker/taker completeness, and BTC/ETH/SOL
  reference alignment.

Top 10 ranked layers:

1. Market expiry;
2. Resolved market outcome;
3. Full historical wallet activity;
4. Additional public endpoints;
5. Reference asset alignment for BTC/ETH/SOL;
6. Liquidity / slippage estimation;
7. Mark-to-market valuation;
8. Execution delay modelling;
9. Queue position / fill uncertainty;
10. Explorer or on-chain settlement metadata.

Conclusion:

- highest expected information gain: market expiry;
- highest engineering cost: queue position / fill uncertainty;
- best cost/value ratio: market expiry;
- recommended next sprint: Wallet Market Expiry Join Sprint v1.

Rationale:

- market expiry directly attacks the dominant measured ambiguity: 1,735 of
  2,135 lifecycle candidates are still-open;
- expiry enables time-to-expiry, late-window behavior, and held-through-expiry
  candidate analysis without introducing performance, return, or trading
  claims;
- resolved outcomes and full history remain high value, but expiry has better
  next-week reproducibility and lower hidden-assumption risk.

Strict exclusions preserved:

- no layer was implemented;
- no Wallet Score or Wallet Watchlist logic changed;
- no PnL, ROI, Sharpe, market-advantage, return, mark-to-market,
  execution-quality, or trading-suitability computation was added;
- no wallet/private-key use, order placement, trade copying, live monitoring,
  capture campaign, production model training, sealed holdout inspection, or
  holdout evaluation was performed.

Next research task: Wallet Market Expiry Join Sprint v1. It should add
report-only public expiry context to existing bounded wallet lifecycle
evidence and measure join coverage before resolved outcomes or any deeper
copyability layer is implemented.

## Polymarket Public Data Discovery Sprint v1

Polymarket Public Data Discovery Sprint v1 is complete.

Outputs:

- `polymarket/models/wallet_intelligence_v1/public_data_discovery_v1/public_endpoint_inventory.csv`
- `polymarket/models/wallet_intelligence_v1/public_data_discovery_v1/endpoint_dependency_graph.md`
- `polymarket/models/wallet_intelligence_v1/public_data_discovery_v1/wallet_data_source_report.md`

Purpose:

- perform a real-world discovery pass over public Polymarket data sources that
  can improve Wallet Intelligence;
- inventory Gamma API, Data API, CLOB read endpoints, public wallet activity,
  market/event/outcome metadata, expiry, resolution, liquidity, volume,
  orderbook, holder, open-interest, WebSocket, and settlement/redemption
  source paths;
- do not implement integration, change Wallet Score, change Wallet Watchlist,
  connect wallets, use private keys, place orders, copy trades, inspect sealed
  holdout outcomes, run holdout evaluation, or launch capture.

Discovery basis:

- official Polymarket API documentation;
- existing ForgeViewAI endpoint usage and Wallet Intelligence artifacts;
- small bounded read-only probes for one existing seed wallet, one historical
  BTC Up/Down market from the broader wallet batch, and one sampling
  orderbook-enabled CLOB market.

Findings:

- Gamma API is the strongest next source for market expiry and lifecycle
  metadata;
- Data API remains the primary public wallet-history source through
  `/activity`, `/trades`, `/positions`, `/closed-positions`, `/value`, and
  `/traded`;
- CLOB `/clob-markets/{condition_id}` is the best token/outcome cross-check
  for existing wallet rows;
- CLOB orderbook, price, midpoint, and spread routes are useful for future
  liquidity/slippage work, but bounded probes showed they can 404 for expired
  or non-orderbook tokens and should not be assumed available for historical
  wallet rows;
- CLOB `/prices-history` is useful later for mark-to-market research, but its
  parameters and historical coverage need a separate bounded validation;
- authenticated CLOB order/user endpoints, user WebSocket channels, bridge
  write paths, relayer write paths, wallet/private-key flows, order placement,
  and automatic trade copying remain excluded.

Endpoint set discovered for future hypothesis tests:

1. `GET https://gamma-api.polymarket.com/markets/slug/{market_slug}`;
2. `GET https://gamma-api.polymarket.com/events/slug/{event_slug}`;
3. `GET https://gamma-api.polymarket.com/events?slug={event_slug}`;
4. `GET https://gamma-api.polymarket.com/markets/token/{token_id}` as a
   fallback when slug joins fail;
5. `GET https://clob.polymarket.com/clob-markets/{condition_id}` as a
   token/outcome cross-check only.

Next research task remains Wallet Market Expiry Join Sprint v1, now with the
public endpoint path narrowed by discovery evidence.

## Wallet Market Outcome Resolution Sprint v1

Wallet Market Outcome Resolution Sprint v1 is complete.

Outputs:

- `polymarket/models/wallet_intelligence_v1/market_outcome_resolution_v1/market_outcome_join.csv`
- `polymarket/models/wallet_intelligence_v1/market_outcome_resolution_v1/market_outcome_join_summary.json`
- `polymarket/models/wallet_intelligence_v1/market_outcome_resolution_v1/market_outcome_join_report.md`
- `polymarket/models/wallet_intelligence_v1/market_outcome_resolution_v1/reproducibility_hashes.json`

Measured evidence:

- lifecycle positions evaluated: 2,135;
- unique conditions evaluated: 1,122;
- metadata join success: 2,134 of 2,135 rows, or 99.95%;
- automatic resolved outcome classification: 2,122 of 2,135 rows, or 99.39%;
- resolved market conditions: 1,112;
- unresolved market conditions: 9;
- failed joins: 1;
- ambiguous joins: 0;
- conflicting metadata rows: 0;
- lifecycle outcome classifications:
  - `matched_outcome`: 1,116;
  - `unmatched_outcome`: 1,006;
  - `unresolved_market`: 12;
  - `insufficient_evidence`: 1.

Implementation:

- added `polymarket/wallet_intelligence/market_outcome.py`;
- added `python -m polymarket.wallet_intelligence market-outcome-resolution`;
- added `MarketOutcomeJoinRecord` and deterministic output schema;
- added focused Wallet Intelligence unit tests for resolved, unresolved,
  conflicting, and repeatable-output behavior.

Conclusion:

- outcome-aware Wallet Intelligence is technically feasible on the current
  bounded public lifecycle evidence;
- public Gamma market-by-slug metadata is sufficient for the overwhelming
  majority of historical lifecycle rows;
- CLOB condition metadata remains useful as a fallback or token/outcome
  cross-check, but is not required for rows where Gamma condition IDs match;
- the biggest measured blocker is the single row where Gamma token fallback
  and CLOB condition fallback were both unavailable.

Strict exclusions preserved:

- no PnL, ROI, realized-profit, Sharpe, market-advantage, copyability,
  execution-quality, Wallet Score, Wallet Watchlist, trading recommendation,
  wallet/private-key, order-placement, holdout-inspection, holdout-evaluation,
  or capture-campaign logic was added.

Superseded successor note:

- the previous descriptive successor was Wallet Outcome-Aware Metrics Sprint
  v1;
- the Project Strategy Reset replaces it with Wallet Outcome Skill Baseline
  Sprint v1 because H1 must be tested directly before more descriptive wallet
  layers are justified.

## Project Strategy Reset

The project strategy reset is complete.

New strategic document:

- `docs/polymarket/RESEARCH_PRINCIPLES.md`

Core strategic question:

- Can ForgeViewAI build a statistically justified, reproducible strategy for
  the five-minute BTC, ETH, and SOL Polymarket markets using only public wallet
  activity?

Core principles:

- profit-first research;
- evidence before engineering;
- one research hypothesis per sprint;
- every sprint must end with a clear answer;
- tooling exists only to test hypotheses;
- weak hypotheses should be eliminated quickly;
- experiments are preferred over architecture;
- engineering work must justify itself through expected information gain.

Core hypotheses now governing Wallet Intelligence:

- H1: Some public wallets consistently make better decisions than random.
- H2: Their actions become visible quickly enough.
- H3: Enough time remains after detection to act.
- H4: Structural filters improve wallet selection.
- H5: Combining these signals can outperform random participation over time.

NEXT_TASK assessment:

- the previous `Wallet Outcome-Aware Metrics Sprint v1` was useful but too
  generic under the reset because it would add a descriptive metrics layer
  without directly deciding a research hypothesis;
- it has been replaced by `Wallet Outcome Skill Baseline Sprint v1`, which
  directly tests H1 using the existing `market_outcome_join.csv` evidence;
- exactly one active task remains.

## Wallet Outcome Skill Baseline Sprint v1

Wallet Outcome Skill Baseline Sprint v1 is complete.

Hypothesis tested:

- H1: Some public wallets consistently make better decisions than random.

Output artifacts:

- `polymarket/models/wallet_intelligence_v1/outcome_skill_baseline_v1/wallet_skill_baseline.csv`
- `polymarket/models/wallet_intelligence_v1/outcome_skill_baseline_v1/wallet_skill_summary.json`
- `polymarket/models/wallet_intelligence_v1/outcome_skill_baseline_v1/wallet_skill_report.md`

Evidence base:

- existing market outcome join evidence only;
- no new public ingestion, live monitoring, capture, wallet/private-key use,
  order placement, sealed holdout inspection, or holdout evaluation;
- main test restricted to resolved BTC/ETH/SOL fast Up/Down lifecycle rows.

Observed results:

- wallets evaluated: 28;
- fast crypto lifecycle positions: 1,789;
- resolved positions tested: 1,788;
- matched outcomes: 938;
- unmatched outcomes: 850;
- population match rate: 0.524609;
- random baseline rate: 0.500000;
- above-baseline evidence wallets: 4;
- below-baseline evidence wallets: 3;
- sample-size-consistent wallets: 13;
- insufficient-evidence wallets: 8.

Above-baseline evidence wallets:

- `0x088df3b7e5c1b5c2d4b7dc760863153480cf025e`;
- `0x1cc53dd33c49d0a222c61ebfd2f24ba48802b199`;
- `0x29a55c2bf8efd1029c001477b34be47d3ca37752`;
- `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`.

Evidence against H1:

- three wallets showed below-baseline evidence under the same gates;
- thirteen wallets were consistent with the population baseline after
  sample-size adjustment;
- eight wallets failed the minimum resolved-position sample gate;
- the wallet set is retrospectively selected and exposed to selection and
  survivorship bias;
- the evidence still lacks public visibility delay, actionable time remaining,
  fill certainty, and complete wallet history.

Final conclusion:

- `INCONCLUSIVE`.

Interpretation:

- H1 is not disproven because four wallets clear conservative above-baseline
  gates;
- H1 is not convincingly supported because the same evidence contains
  below-baseline wallets, many baseline-consistent wallets, and major
  retrospective-data invalidation risks.

Next active task:

- Wallet Activity Visibility Delay Sprint v1. It should test H2 only for the
  four H1 above-baseline wallets before any broader wallet strategy work is
  justified.

## Balanced Repricing Batch 002 Evidence Completion Sprint

Balanced Repricing Evidence Collection Batch 002 is fully post-processed from
the existing public-only session. No new capture was launched, frozen settings
were unchanged, and sealed holdout data was not accessed.

Artifacts:

- source session:
  `polymarket/runs/repricing_balanced_v1_batch_002/20260625_200724/session.jsonl`;
- model and validation outputs:
  `polymarket/models/repricing_research_v1/balanced_collection_batch_002/`;
- dedicated data copy:
  `polymarket/data/repricing_research_balanced_batch_002/`.

Capture and replay validation:

- configured / observed duration: 43,200.0 / 43,200.004030 seconds;
- campaign completeness: `complete`, 100.0%;
- checkpoints: 21,600 / 21,600, 100.0%;
- continuity: `continuous`;
- maximum checkpoint gap: 2.104670 seconds;
- gaps over 10 / 60 / 300 seconds: 0 / 0 / 0;
- fatal capture errors: 0;
- replay compatibility: verified by exact evidence, completeness, and
  continuity metrics.

Frozen candidate flow:

- raw events: 370,616;
- lag measurements: 64,176;
- candidate measurements matching the two frozen accepted reasons: 71;
- validated and accepted repricing signals: 42;
- favorable target-before-stop signals: 34;
- candidate validation rejections: 29, or 40.85%;
- post-candidate rejection reasons: 15 below the frozen 60-second dataset
  expiry floor and 14 suppressed by the non-overlapping paper-position rule;
- largest detector-level rejection: `polymarket_already_repriced`, 30,354.

Signal results:

- BTC / ETH / SOL: 8 / 12 / 22;
- YES / NO: 8 / 34;
- signals/hour: 3.539656;
- win rate: 80.95%;
- after-slippage P&L: +2.250000;
- after-slippage expectancy: +0.053571 per signal;
- maximum drawdown: 0.280000;
- exits: 34 `repricing_target`, 8 `stop_loss`, 0 `timeout`;
- horizon coverage 30s / 60s / 120s / 180s:
  100.00% / 100.00% / 83.33% / 0.00%;
- deterministic export: verified by identical repeated CSV and JSON hashes;
- relevant tests: 3 / 3 passed;
- full repository tests: 132 / 132 passed.

Research conclusion: `INCONCLUSIVE`.

Batch 002 strengthens directional development evidence because all three
assets and both sides had positive after-slippage expectancy. It does not
decide the master hypothesis that frozen repricing conditions outperform
random observation because no precommitted random-observation comparator was
evaluated. Weak evidence also still lacks 40 observed hours and 3 independent
sessions. Frozen parameters remain valid for comparison and unchanged, but no
edge, production, live-trading, holdout, or additional-capture authorization
follows from this result.

## Balanced Repricing Random Baseline Sprint v1

Balanced Repricing Random Baseline Sprint v1 tested the frozen repricing
detector against a predefined random-entry reference using only completed
Batch 001 and Batch 002 public sessions.

Artifacts:

- `polymarket/models/repricing_research_v1/balanced_random_baseline_v1/random_baseline_results.csv`;
- `polymarket/models/repricing_research_v1/balanced_random_baseline_v1/random_baseline_summary.json`;
- `polymarket/models/repricing_research_v1/balanced_random_baseline_v1/random_baseline_report.md`.

Baseline specification:

- 1,000 deterministic Monte Carlo trials, seed `20260628`;
- 172 entries per trial over 24.000000 observed hours;
- exact matching to detector counts by batch, asset, side, and 60-second
  expiry bucket;
- uniform random timing over eligible public snapshots;
- identical 60-second minimum expiry, 180-second timeout, 0.03 target, 0.03
  stop, 0.02 slippage, and non-overlapping same-market/same-side paper rule;
- signal density matched by design at 7.166667 signals/hour.

Measured comparison:

- detector: 172 signals, 110 wins, 63.9535% win rate, +0.022401
  after-slippage expectancy, 0.875 maximum drawdown;
- random mean: 47.8692% win rate, -0.019607 after-slippage expectancy,
  3.495447 maximum drawdown;
- random 95% win-rate interval: 40.6977% to 54.6512%;
- random 95% expectancy interval: -0.029563 to -0.011226;
- detector minus random: +16.0843 percentage points win rate and +0.042008
  expectancy;
- no random trial matched detector expectancy or win rate;
- one-sided finite-trial exceedance probability: 0.000999 for each metric;
- all three output artifacts reproduced byte-for-byte on an independent run;
- repricing tests: 4 / 4 passed;
- full repository tests: 136 / 136 passed.

Conclusion: `SUPPORTED` under the predefined development-only random-timing
baseline. The positive expectancy is not explained by random entry timing
alone under this matched control.

The conclusion remains exposed to two-session sample size, adjacent market
regimes, serially correlated snapshots, uniform-snapshot baseline choice,
development selection bias, midpoint-like paper prices, and absent executable
fill, depth, queue, and fee evidence. It is not a proven edge and does not
authorize frozen-parameter changes, holdout evaluation, production modelling,
live trading, or another capture.

## Repricing Continuous Paper Trading Readiness Sprint v1

Repricing Continuous Paper Trading Readiness Sprint v1 reviewed the complete
capture, detector, offline repricing, generic shadow, persistence, reporting,
and notification paths without changing detector logic or frozen parameters.

Artifacts:

- `polymarket/models/repricing_research_v1/paper_trading_readiness_v1/repricing_paper_trading_gap.md`;
- `polymarket/models/repricing_research_v1/paper_trading_readiness_v1/repricing_mvp_components.csv`;
- `polymarket/models/repricing_research_v1/paper_trading_readiness_v1/repricing_launch_plan.md`.

Measured readiness:

- components reviewed: 18;
- `READY`: 4;
- `MINOR WORK`: 7;
- `MAJOR WORK`: 7;
- launch-blocking components: 13;
- component estimate: 9.75 engineer-days;
- planning range: 9-11 engineer-days plus a minimum 24-hour supervised soak;
- earliest continuously running MVP: end of engineer-day 10;
- earliest initial readiness evidence: day 11 after one complete soak;
- repricing tests: 4 / 4 passed;
- full repository tests: 136 / 136 passed.

Current readiness: `NOT_READY`.

The v5 capture substrate, public feeds, frozen lag measurements, raw evidence,
continuity metrics, and replay are ready. The existing live v5 shadow strategy
is not the frozen repricing strategy: it admits only qualified measurements,
uses the generic v3 score engine and different slippage semantics, and closes
positions by score or end of session. The frozen repricing reason admission,
60-second floor, overlap rule, 0.03 target, 0.03 stop, 180-second timeout, and
0.02 slippage are evaluated only after a session completes.

Launch is blocked by missing causal repricing trade state, target/stop/timeout
processing, transactional persistence, restart recovery, durable duplicate
protection, daily statistics, health telemetry, Telegram notifications,
single-instance supervision, session rotation, and failure/soak validation.

The smallest safe architecture keeps v5 feeds and `LagDetector` unchanged,
persists raw evidence first, and adds a separate frozen admission consumer,
SQLite paper ledger, causal close state machine, event cursor recovery,
telemetry outbox, UTC daily reports, and optional outbound Telegram adapter.

The master readiness hypothesis is rejected for current software readiness.
This is an engineering-readiness finding, not a rejection of the repricing
research hypothesis. No capture or paper campaign was launched, the holdout
remained sealed, and no threshold or detector change was made.

Wallet Activity Visibility Delay Sprint v1 is complete and leaves H2
`INCONCLUSIVE` because the retrospective activity export has no publication
or first-seen timestamp. Wallet Detection-To-Expiry Feasibility Sprint v1
remains the planned Wallet Intelligence successor. The canonical repository
task in `NEXT_TASK.md` is the restart-safe repricing paper core.

## Wallet Activity Visibility Delay Sprint v1

Wallet Activity Visibility Delay Sprint v1 is complete.

Artifacts:

- `polymarket/models/wallet_intelligence_v1/activity_visibility_delay_v1/wallet_visibility_delay.csv`
- `polymarket/models/wallet_intelligence_v1/activity_visibility_delay_v1/wallet_visibility_delay_summary.json`
- `polymarket/models/wallet_intelligence_v1/activity_visibility_delay_v1/wallet_visibility_delay_report.md`

Observed evidence:

- 20 H1-classified wallets were analyzed: 4 above-baseline, 13 baseline, and
  3 below-baseline;
- 3,431 BTC/ETH/SOL fast Up/Down trade rows were analyzed;
- Group A contributed 684 rows, Group B 2,228, and Group C 519;
- all 3,431 rows had trade timestamps, fetch timestamps, transaction hashes,
  and deterministic event ordering;
- zero rows had a publication or first-seen timestamp;
- true publication-delay minimum, median, mean, and maximum are unavailable;
- all 3,431 publication delays are unknown;
- retrospective retrieval lag ranged from 18 to 11,200,902 seconds, with a
  22,207-second median and 778,179.988925-second mean, but this measures batch
  retrieval age rather than API latency.

Conclusion:

- H2 is `INCONCLUSIVE`;
- stronger, baseline, and weaker wallet visibility speed cannot be compared
  from the existing retrospective evidence;
- selection bias, bounded history, second-resolution activity time, and the
  absence of publication/first-seen time prevent a visibility claim.

Planned wallet successor:

- Wallet Detection-To-Expiry Feasibility Sprint v1, which must use bounded
  prospective first-seen timestamps before measuring remaining time.

## Wallet First-Seen Detection Sprint v1

Wallet First-Seen Detection Sprint v1 is complete.

Artifacts:

- `polymarket/models/wallet_intelligence_v1/first_seen_detection_v1/wallet_first_seen_dataset.csv`
- `polymarket/models/wallet_intelligence_v1/first_seen_detection_v1/wallet_first_seen_summary.json`
- `polymarket/models/wallet_intelligence_v1/first_seen_detection_v1/wallet_first_seen_report.md`

Bounded experiment:

- observation duration: 299.998 seconds;
- wallets: the four frozen H1 above-baseline wallets;
- endpoint: public unauthenticated Data API `/activity?type=TRADE`;
- cadence: one four-wallet cycle every 5 seconds;
- requests: 240 attempted, 240 successful, 0 failed;
- configured request rate: 8 requests per 10 seconds, 0.80% of the documented
  Data API general limit;
- startup baseline: 400 unique identities;
- response rows observed: 24,000.

Measured evidence:

- 124 identities not present in the startup pages appeared later;
- 118 were historical page churn and were excluded from delay statistics;
- 6 were trades executed in the live observation window;
- all 6 had measurable polling-quantized first-seen upper bounds;
- all-trade delay minimum / median / mean / maximum: 10.932 / 15.9675 /
  19.749167 / 41.529 seconds;
- 2 of the 6 trades were target five-minute markets;
- five-minute delay minimum / median / mean / maximum: 15.894 / 15.9675 /
  15.9675 / 16.041 seconds;
- response latency minimum / median / mean / maximum: 149 / 283 /
  322.329167 / 1,031 milliseconds;
- duplicate observations: 23,476;
- page-range missed observations: 440;
- reappearances after a page gap: 322.

Research conclusion:

- `H2_MEASURABLE_PROSPECTIVELY`;
- H2 can now be measured using local first-seen timestamps;
- the experiment does not support or reject H2 because only two target
  five-minute trades were observed;
- first-seen delay is an upper bound containing API publication delay,
  polling cadence, request duration, and clock uncertainty;
- latest-100 page instability requires historical page churn to remain
  excluded from future H2 evidence.

Next active task:

- Wallet Detection-To-Expiry Feasibility Sprint v1, using the committed two
  five-minute first-seen rows as a feasibility sample before any larger
  prospective evidence batch.

## Restart-Safe Repricing Paper Trading Core v1

Restart-Safe Repricing Paper Trading Core v1 is complete.

Implementation and artifacts:

- `polymarket/repricing_research/paper_core.py`
- `polymarket/models/repricing_research_v1/restart_safe_paper_core_v1/restart_recovery_report.md`
- `polymarket/models/repricing_research_v1/restart_safe_paper_core_v1/restart_recovery_validation.json`
- `tests/polymarket/test_repricing_paper_core.py`

Measured validation:

- raw v5-shaped events are committed before state transitions;
- signal admission, position state, realized paper PnL, and processed cursor
  update atomically in SQLite;
- open positions survive restart, closed positions remain closed, and repeated
  ingestion or recovery creates no duplicate signal, position, trade, or PnL;
- six admission/open and three close interruption cases recover
  deterministically;
- frozen fixture signals, exits, and PnL match the offline repricing simulator;
- v5 lifecycle closure exits an open paper position at the last durable quote;
- a frozen-strategy fingerprint mismatch fails closed;
- 11 repricing tests and 147 repository tests pass.

No public campaign was launched. Detector logic and thresholds were not
changed, and sealed holdout remains untouched. The core is not a 24/7 paper
engine yet: it still needs a read-only v5 event-stream adapter, lifecycle
supervision, session rotation, telemetry, daily statistics, and a soak test.

Next active task:

- Integrate Restart-Safe Repricing Paper Core with v5 Event Stream v1.

## v5 Repricing Paper Core Integration v1

Integrate Restart-Safe Repricing Paper Core with v5 Event Stream v1 is
complete.

Implementation and artifacts:

- `polymarket/repricing_research/v5_stream_adapter.py`;
- `tests/polymarket/test_repricing_v5_stream_adapter.py`;
- `polymarket/models/repricing_research_v1/v5_paper_core_integration_v1/v5_paper_core_integration_report.md`;
- `polymarket/models/repricing_research_v1/v5_paper_core_integration_v1/v5_paper_core_validation.json`.

Measured validation:

- complete v5 JSONL events convert directly into durable paper-core input;
- stable source path identity, first-event hash, event index, and canonical raw
  event provide end-to-end paper position audit lineage;
- duplicate detector delivery creates no duplicate signal or position;
- open and closed position state resumes deterministically after restart;
- appended events resume after the durable source cursor;
- committed-prefix mutation, source replacement, truncation, malformed
  complete records, unsupported assets, and timestamp regression fail closed;
- trailing partial writes are deferred until complete;
- UP/YES, DOWN/NO, target, stop, timeout, overlap, and 0.02 slippage semantics
  retain the frozen strategy fingerprint;
- interrupted and uninterrupted ingestion produce identical business state;
- 20 repricing tests and 159 repository tests pass.

No detector logic or threshold changed. No campaign, Telegram integration,
real-money execution, wallet/private-key path, or holdout access occurred.
The integration is callable and append-resumable but is not yet a managed
24/7 process. Repricing runtime lifecycle, health telemetry, session rotation,
daily statistics, and soak validation remain planned blockers, not active
tasks. The newer canonical project task remains Wallet H2/H3 Prospective
Evidence Accumulation Sprint v1.

## Wallet First-Seen Prospective Experiment v1

Wallet First-Seen Prospective Experiment v1 is complete as an implementation
and fixture-validation sprint. It did not launch another observation window
and did not evaluate H2.

Implementation:

- restart-safe SQLite store under the local runtime path
  `polymarket/data/wallet_intelligence/first_seen_prospective_v1/observer.sqlite3`;
- every completed poll persists request/response timestamps, endpoint status,
  raw payload JSON, payload hash, row count, and error before analysis;
- every new trade persists wallet, asset, condition, token, transaction hash,
  trade timestamp, first-seen timestamp, poll timestamp, endpoint, and raw
  provenance;
- active run deadline, request count, wallet baselines, and next poll cycle
  survive restart;
- immutable global trade identities and unique poll keys prevent duplicate
  first-seen rows and duplicate poll insertion;
- expired interrupted runs close before a new bounded run starts;
- CLI observation requires explicit `--observe`; preparation mode makes no
  public requests.

Bounded configuration:

- four frozen H1 wallets only;
- public unauthenticated Data API activity endpoint only;
- 5-second polling interval;
- maximum 300 seconds, 240 requests, and 100 rows per wallet poll;
- configured 8 requests per 10 seconds, or 0.80% of the documented Data API
  general limit.

Artifacts:

- `polymarket/models/wallet_intelligence_v1/first_seen_prospective_v1/wallet_first_seen_dataset.csv`;
- `polymarket/models/wallet_intelligence_v1/first_seen_prospective_v1/wallet_first_seen_validation.json`;
- `polymarket/models/wallet_intelligence_v1/first_seen_prospective_v1/wallet_first_seen_design_report.md`.

Validation:

- restart safe: passed;
- duplicate safe: passed;
- every completed poll persisted: passed;
- first-seen timestamp immutable: passed;
- deterministic export: passed;
- H2 evaluated: false;
- initialized dataset rows: 0.

Remaining Wallet Intelligence blocker:

- a future explicitly authorized bounded collection must gather enough target
  five-minute first-seen observations before H2 or H3 can be evaluated.

## Wallet Decision Window Sprint v1

Wallet Decision Window Sprint v1 is complete and tested the H3 feasibility
hypothesis using only committed prospective first-seen evidence.

Artifacts:

- `polymarket/models/wallet_intelligence_v1/decision_window_v1/wallet_decision_window.csv`;
- `polymarket/models/wallet_intelligence_v1/decision_window_v1/wallet_decision_window_summary.json`;
- `polymarket/models/wallet_intelligence_v1/decision_window_v1/wallet_decision_window_report.md`.

Observed evidence:

- eligible prospective five-minute trades: 2;
- represented wallets: 1;
- assets: BTC 1, SOL 1;
- Gamma-verified first-seen-to-expiry windows: 85.106 and 44.959 seconds;
- minimum / median / mean / maximum: 44.959 / 65.0325 / 65.0325 /
  85.106 seconds;
- sufficient (`>=60s`): 1;
- marginal (`>=30s` and `<60s`): 1;
- insufficient (`<30s`): 0;
- shares at 60 / 120 / 180 seconds: 50% / 0% / 0%.

Conclusion:

- `INCONCLUSIVE`;
- the observed windows are not uniformly incompatible with future automated
  copy-trading research, but two trades from one wallet cannot establish an
  actionable distribution;
- exact API publication time remains unknown within the 5-second polling
  interval;
- execution, order-submission, fill, slippage, liquidity, and queue latency
  remain unmeasured.

Evidence-driven successor:

- Wallet H2/H3 Prospective Evidence Accumulation Sprint v1;
- stop when 30 eligible target five-minute observations are accumulated or
  after 20 bounded five-minute sessions, whichever occurs first;
- use the existing restart-safe observer and frozen decision-window
  thresholds without changing Wallet Score or simulating execution.

## Wallet H2/H3 Decision Framework Sprint v1

Wallet H2/H3 Decision Framework Sprint v1 is complete. It defines when the
Wallet Intelligence branch continues, graduates, or freezes without changing
the observer, polling, Wallet Score, or either hypothesis.

Artifacts:

- `polymarket/models/wallet_intelligence_v1/h2_h3_decision_framework_v1/wallet_h2_h3_decision_framework.md`;
- `polymarket/models/wallet_intelligence_v1/h2_h3_decision_framework_v1/wallet_h2_h3_progress.json`;
- `polymarket/models/wallet_intelligence_v1/h2_h3_decision_framework_v1/wallet_h2_h3_remaining_evidence.md`.

Minimum final-decision evidence:

- 100 eligible prospective five-minute trades;
- 3 distinct wallets with at least 10 rows each and no wallet above 60%;
- 10 bounded sessions across 5 UTC dates;
- 2 assets with at least 20 rows each;
- at least 95% timestamp, expiry-join, and request completeness;
- 100% stable identity uniqueness;
- two-sided 95% Wilson confidence intervals.

Current automatic evaluation:

- H2: 2/2 within 30 seconds, point estimate 100%, Wilson interval
  34.24%-100%, `INCONCLUSIVE`;
- H3: 1/2 with at least 60 seconds remaining, point estimate 50%, Wilson
  interval 9.45%-90.55%, `INCONCLUSIVE`;
- current action: `CONTINUE`;
- remaining headline evidence: 98 trades, 2 wallets, 9 minimum-gate sessions,
  and 4 UTC dates;
- observed rate implies approximately 49 additional five-minute sessions, or
  245 minutes, but that estimate comes from one session and is not a forecast.

Stop/go policy:

- graduate only if both H2 and H3 satisfy their support gates;
- freeze if either satisfies its rejection gate;
- freeze if 60 total bounded sessions finish without minimum evidence;
- evaluate every 10 sessions and never extend the budget automatically.

Next active task:

- Wallet H2/H3 Gate-Bound Evidence Collection Sprint v1.

## Wallet Autonomous Evidence Accumulator v1

Wallet Autonomous Evidence Accumulator v1 is complete as an implementation
and fixture-validation sprint. No public observation session was launched.

Implementation:

- `polymarket/wallet_intelligence/evidence_accumulator.py`;
- `wallet-evidence-accumulator status` computes progress without polling;
- `wallet-evidence-accumulator run` executes bounded sessions until a frozen
  terminal gate;
- `wallet-evidence-accumulator start` launches that same loop as a detached
  background process;
- local SQLite persists control state, automatic session numbering, restart
  state, per-session results, stop reason, process ID, and Gamma expiry cache;
- the existing observer SQLite remains the sole source for polls and newly
  observed trades;
- progress and gate artifacts are atomically replaced after every completed
  session.

Artifacts:

- `polymarket/models/wallet_intelligence_v1/autonomous_evidence_accumulator_v1/wallet_progress.json`;
- `polymarket/models/wallet_intelligence_v1/autonomous_evidence_accumulator_v1/wallet_progress_report.md`;
- `polymarket/models/wallet_intelligence_v1/autonomous_evidence_accumulator_v1/wallet_gate_status.json`.

Current automatic progress:

- automation status: `ready`;
- current action: `CONTINUE`;
- eligible trades: 2 / 100;
- represented wallets: 1 / 3;
- completed sessions: 1 / 60;
- remaining session budget: 59;
- H2: 2/2, `INCONCLUSIVE`;
- H3: 1/2, `INCONCLUSIVE`;
- observer database runs/polls/new trades: 0 / 0 / 0;
- required artifact exports are byte-repeatable across consecutive status
  runs.

Automatic stop behavior:

- both hypotheses supported: `GRADUATE_TO_ENGINEERING` and stop;
- either hypothesis rejected: `FREEZE` and stop;
- session 60 without a terminal decision: `FREEZE` and stop;
- database reservation prevents competing session numbers and an interrupted
  active session resumes under the same number.

Validation:

- support, rejection, and budget-exhaustion branches passed fixture tests;
- an end-to-end session-60 fixture ran exactly one final session, emitted
  `FREEZE`, and persisted stopped state;
- no hypothesis, threshold, polling setting, endpoint, or Wallet Score logic
  changed.

Next active task:

- Wallet Autonomous Evidence Accumulator Controlled Launch v1.

## Wallet Autonomous Evidence Accumulator Controlled Launch v1

Wallet Autonomous Evidence Accumulator Controlled Launch v1 is complete.

Artifacts:

- `polymarket/models/wallet_intelligence_v1/controlled_launch_v1/wallet_controlled_launch_report.md`;
- `polymarket/models/wallet_intelligence_v1/controlled_launch_v1/wallet_runtime_validation.json`;
- `polymarket/models/wallet_intelligence_v1/controlled_launch_v1/wallet_runtime_status.json`.

Measured public launch:

- detached process started once, PID 18296, and exited cleanly;
- isolated development state preserved canonical evidence and budget;
- automatic session number: 2;
- observer run: `f9d8a73029135498ee276c2c`;
- duration: 15 seconds;
- polling interval: unchanged at 5 seconds;
- poll cycles: 3;
- public requests: 12 attempted, 12 successful;
- wallet baselines: 4 of 4;
- response rows: 1,200;
- post-baseline observations persisted: 800;
- every poll retained raw JSON and a SHA-256 payload hash;
- new prospective/eligible trades: 0 / 0.

Post-session state:

- controlled session counter: 2;
- controlled remaining budget: 58;
- evidence remained 2 eligible trades, correctly unchanged;
- H2 and H3 remained `INCONCLUSIVE`;
- action remained `CONTINUE`;
- process ID cleared and control returned to `ready`;
- two fresh status processes reopened SQLite and emitted byte-identical
  progress artifacts.

Bounded correctness fix:

- launch-only `--session-limit` and `--session-duration` options permit a
  development smoke without altering canonical defaults;
- polling remains fixed at 5 seconds;
- status now derives the actual completed-session runtime from the linked
  observer run, distinguishing the 15-second smoke from the canonical
  300-second configuration.

Gamma expiry cache:

- live entries: 0 because no new target trade existed;
- this is not a join failure;
- condition-ID matching, expiry parsing, and durable cache persistence passed
  a focused fixture test.

Validation:

- Wallet Intelligence tests: 55 passed;
- full repository tests: 182 passed;
- SUPPORT, REJECT, and session-60 stop behavior remains frozen and tested;
- no hypothesis, threshold, polling interval, Wallet Score, or canonical
  evidence changed.

Next active task:

- Wallet Autonomous Evidence Accumulator Canonical Background Run v1.

## Managed Repricing Paper Runtime Loop v1

Managed Repricing Paper Runtime Loop v1 is complete for bounded, fixture-driven
paper operation.

Implementation and artifacts:

- `polymarket/repricing_research/paper_runtime.py`;
- `tests/polymarket/test_repricing_paper_runtime.py`;
- `polymarket/models/repricing_research_v1/paper_runtime_v1/repricing_paper_runtime_report.md`;
- `polymarket/models/repricing_research_v1/paper_runtime_v1/repricing_paper_runtime_validation.json`;
- `repricing-paper-runtime` command entrypoint.

Measured validation:

- the managed loop starts the v5 adapter and restart-safe core, processes
  valid appended events, and persists paper positions and trades;
- restart restores open positions and accepts subsequent close events without
  duplication;
- repeated source replay is idempotent;
- Ctrl+C/termination support requests graceful shutdown where feasible;
- shutdown closes SQLite without force-closing open paper positions;
- invalid complete stream data fails closed and records the error;
- health JSON is replaced atomically at startup, poll, failure, and shutdown;
- bounded dry-run health output is byte deterministic under a fixed clock;
- 28 repricing tests and 167 repository tests pass.

Health fields cover runtime start/stop, last poll/event, accepted/rejected and
duplicate event counts, positions opened/closed, recovered/current open
positions, completed polls, last error, source/database paths, strategy
fingerprint, and dry-run state.

No detector logic or threshold changed. No campaign, real trade, Telegram
integration, wallet/private-key path, or holdout access occurred. Unattended
continuous operation is not authorized.

The required Repricing successor is **Repricing Paper Runtime Supervision And
Soak Sprint v1**. It remains planned branch work because the sole global task
in `NEXT_TASK.md` is Wallet H2/H3 Gate-Bound Evidence Collection Sprint v1.

## Continuous Repricing Paper Trading MVP v1

Continuous Repricing Paper Trading MVP v1 is complete at bounded dry-run
validation level.

Implementation and committed outputs:

- `polymarket/repricing_research/runtime_mvp.py`;
- `tests/polymarket/test_repricing_runtime_mvp.py`;
- `repricing-runtime-mvp --config <runtime.json>`;
- `polymarket/models/repricing_research_v1/continuous_runtime_mvp_v1/repricing_runtime_status.json`;
- `polymarket/models/repricing_research_v1/continuous_runtime_mvp_v1/repricing_runtime_heartbeat.json`;
- `polymarket/models/repricing_research_v1/continuous_runtime_mvp_v1/repricing_runtime_summary.json`;
- `polymarket/models/repricing_research_v1/continuous_runtime_mvp_v1/repricing_runtime_mvp_report.md`.

Operational behavior:

- one JSON file defines source, state/output paths, cadence, bounds, dry-run,
  and restart policy;
- startup validates configuration, holdout separation, complete v5 input,
  writable directories, recoverable SQLite state, and frozen fingerprint;
- an OS byte-range lock rejects a competing runtime process and releases on
  normal exit or process death;
- temporary source unavailability restarts within the configured budget;
- malformed/source-integrity/fingerprint/state failures stop closed;
- unclean process restart reuses the prior session ID and increments restart
  count;
- Ctrl+C/termination requests graceful shutdown without force-closing paper
  positions;
- atomic status and heartbeat, UTC daily summary, and unified JSONL log are
  updated throughout the run;
- daily duration is split exactly at UTC midnight boundaries;
- 39 repricing tests and 185 repository tests pass.

Validation status is `PASS_BOUNDED_DRY_RUN`. No 24-hour run was launched. No
detector, frozen threshold, strategy, holdout, wallet/private-key, Telegram,
or live-trading behavior changed.

Remaining Repricing blockers are 24-hour launch preflight, v5 producer/session
rotation procedure, stale-event/write-latency thresholds, supervised restart
drills with open positions, and one reconciled 24-hour paper soak. The branch
successor is **Run First 24-Hour Repricing Paper Soak Preflight v1**. The sole
global task remains Wallet Autonomous Evidence Accumulator Canonical
Background Run v1 under repository policy.

## Repricing Pre-Soak Consolidation v1

Repricing Pre-Soak Consolidation v1 is complete with verdict
`READY_FOR_24H_SOAK`.

Implementation and artifacts:

- `polymarket/repricing_research/pre_soak.py`;
- `tests/polymarket/test_repricing_pre_soak.py`;
- `polymarket/models/repricing_research_v1/pre_soak_v1/repricing_pre_soak_report.md`;
- `polymarket/models/repricing_research_v1/pre_soak_v1/repricing_pre_soak_validation.json`;
- `polymarket/models/repricing_research_v1/pre_soak_v1/repricing_runtime_readiness.json`.

Measured machine preflight:

- AC sleep / hibernate: 0 / 0 seconds, safe for overnight operation;
- free disk: 35,648,344,064 bytes against a 2,147,483,648-byte floor;
- marker write latency: 0.694 ms against a 500 ms ceiling;
- stale-event ceiling: 30 seconds;
- source-root rotation: enabled and selected the latest timestamped v5 session;
- frozen strategy fingerprint: verified;
- pending events / open positions in the temporary readiness ledger: 0 / 0.

Completed engineering gates:

- automatic latest-session discovery and live adapter rotation;
- stale-event fail-closed guard;
- health-write latency fail-closed guard;
- restart with an open position;
- restart after interruption during position creation;
- restart after graceful shutdown followed by a close event;
- power, disk, writable-path, source, ledger, and fingerprint preflight;
- 45 Repricing tests and 191 repository tests pass.

No engineering blockers remain before an explicitly authorized 24-hour soak.
The soak itself was not launched and remains the next Repricing branch task:
**Run First 24-Hour Repricing Paper Soak v1**. Its completion must reconcile
raw events, heartbeats, daily summaries, positions, trades, failures, restarts,
continuity, and duplicate/lost transitions. The sole global task remains
Wallet Autonomous Evidence Accumulator Canonical Background Run v1.

No detector, threshold, strategy, holdout, wallet/private-key, Telegram, or
live-trading boundary changed.

## Wallet Autonomous Evidence Accumulator Terminal Review v1

The canonical background run completed automatically at session 60 and is no
longer running. Terminal runtime state is `FREEZE` with stop reason
`SESSION_BUDGET_EXHAUSTED`, zero remaining sessions, and no active process.

Operational evidence:

- 59 observer runs plus the preserved seed session, 14,019 polls, and
  1,377,100 observation links;
- 14,247 successful and 12 failed public requests, a 99.9158% success rate;
- 614 globally deduplicated observed trades and 382 rows admitted by the
  frozen H2/H3 target-market filter;
- four wallets and three assets: 308 BTC, 49 ETH, and 25 SOL rows;
- timestamp, Gamma expiry, and identity completeness all reached 100%;
- 11 of 12 minimum-evidence gates passed; only date diversity failed at one
  of five required UTC dates.

The frozen aggregate reported H2 at 51/382 (13.35%, Wilson 95%
10.30%-17.13%) and H3 at 58/382 (15.18%, Wilson 95% 11.93%-19.13%). Both
formal conclusions remained `INCONCLUSIVE` because minimum evidence did not
pass.

An evidence-integrity review found that 299 of the 382 rows were timestamped
before the observer session that first inserted them. Per-session baselines
prevented initial-page rows from being called new, but historical rows exposed
later by public API page churn were still admitted. Those 299 rows produced no
H2 or H3 successes and must not be interpreted as prospective latency or
decision-window evidence.

The defensible diagnostic subset contains 83 unique rows: 82 observer trades
executed at or after their first session began plus one non-overlapping seed
trade. On that subset:

- H2 is 51/83, 61.45%, Wilson 95% 50.69%-71.19%;
- H3 is 58/83, 69.88%, Wilson 95% 59.31%-78.69%;
- observer-only prospective delay has a 2.825-second minimum, 25.046-second
  median, 31.009-second mean, and 136.920-second maximum;
- observer-only time from first seen to expiry has a -33.367-second minimum,
  102.426-second median, 108.259-second mean, and 288.939-second maximum.

These diagnostic rates do not replace the frozen framework. They leave H2
below its 80% support threshold and H3 near but short of its support gates,
with only one observation date and fewer than 100 defensible rows. H1 also
remains inconclusive. The combined Wallet hypothesis is materially weaker,
but neither H2 nor H3 receives a formal rejection from this run.

Wallet Intelligence is frozen under its precommitted session budget. The next
global task is the already preflighted 24-hour Repricing paper soak, which has
greater immediate information value for Objective Alpha. No Wallet code,
threshold, hypothesis, score, or methodology changed in this review.

## First 24-Hour Repricing Paper Soak v1

The first authorized public-only Repricing paper soak is complete with verdict
`FAILED_OPERATIONAL_INTEGRITY`. Exactly one source producer and one paper
runtime were launched. Preflight passed with safe AC power, sufficient disk,
writable state/output paths, source rotation enabled, zero recovered open
positions, and frozen strategy fingerprint
`d5d389be45d472628aab06b3aeeb281593e74d48b82902e12712047c91fec010`.

GitHub-safe summary artifacts:

- `polymarket/models/repricing_research_v1/paper_soak_v1_summary/soak_report.md`;
- `polymarket/models/repricing_research_v1/paper_soak_v1_summary/soak_summary.json`;
- `polymarket/models/repricing_research_v1/paper_soak_v1_summary/soak_validation.json`;
- `polymarket/models/repricing_research_v1/paper_soak_v1_summary/reproducibility_hashes.json`.

Source capture:

- session:
  `polymarket/runs/repricing_paper_soak_v1/20260628_173831/v5_sessions/20260628_173831/session.jsonl`;
- configured duration: 86,400 seconds;
- observed UTC span / monotonic runtime: 88,630.525266 / 88,632.328 seconds;
- `session_completed`: present;
- checkpoints: 32,540 / 43,200, or 75.3241%;
- maximum checkpoint gap: 23,554.333577 seconds;
- internal gaps over 300 seconds: one, lasting 4,112.812693 seconds;
- terminal gap: 23,554.333577 seconds;
- fatal capture errors: 0;
- campaign status: `incomplete_campaign`.

Runtime reconciliation:

- last current heartbeat covered 12,310.53587 seconds and then stopped;
- the runtime process remained CPU-active beyond its 24-hour bound instead of
  stopping closed;
- source cursor stopped at event 351,230 of 531,314;
- SQLite integrity: `ok`;
- live signals / positions / trades: 60 / 60 / 60;
- all 60 positions closed, with zero open positions and zero duplicate
  business keys;
- deterministic offline export reconstructed 73 signals, exposing a
  13-signal live-processing shortfall.

Replay and export were each repeated and matched byte-for-byte. The descriptive
offline result was 73 signals: BTC / ETH / SOL 13 / 17 / 43, YES / NO 26 / 47,
80.82% win rate, +0.071432 after-slippage expectancy, +5.2145 after-slippage
P&L, and 0.22 maximum drawdown. All 45 Repricing tests and all 191 repository
tests pass. These rows are excluded from evidence-gate aggregation because
source continuity and live reconciliation failed.

Scientifically valid Repricing evidence remains 172 signals over 24 hours and
two independent sessions. Signal, asset, side, expectancy, drawdown, and
stability gates remain passed; weak evidence still fails the frozen 40-hour
and three-session requirements.

Objective Alpha impact:

- `ALPHA-B002` is resolved by 60 autonomous, unique, fully closed public-input
  paper trades under the frozen fingerprint;
- `ALPHA-B001`, `ALPHA-B004`, `ALPHA-B006`, and `ALPHA-B007` remain in progress
  because the consumer fell behind, heartbeat freshness stopped, bounded
  shutdown failed, and the operating-day summary did not reconcile;
- `ALPHA-B003` remains in progress because no integrated restart with an open
  position occurred during this soak;
- `ALPHA-B008` remains blocked.

The next active task is **Fix Repricing Runtime Backpressure And Liveness
Fail-Closed v1**. It must correct incremental source consumption, independent
heartbeat/watchdog behavior, bounded shutdown, and deterministic cursor catch-up
without changing the frozen detector or launching another soak.

No live trading, wallet/private-key path, model training, holdout inspection,
holdout evaluation, detector change, threshold change, or strategy change
occurred.

## Repricing Runtime Backpressure And Liveness Fix v1

The runtime blocker exposed by the first 24-hour soak is fixed at component and
stress-validation level. Verdict: `READY_FOR_SECOND_24H_SOAK_PREFLIGHT`.

Failure diagnosis:

- heartbeat stopped at `2026-06-28T21:04:31.905461+00:00`, after
  12,310.53587 seconds;
- capture checkpoints continued until `2026-06-29T11:43:08.054053+00:00` and
  capture completed at `2026-06-29T18:15:42.387630+00:00`;
- the paper cursor continued to event 351,230 while telemetry was stale;
- `V5JsonlPaperAdapter.sync()` consumed toward EOF from a growing file;
- every event incurred one raw-journal commit and one apply/cursor commit under
  `SQLite synchronous=FULL`;
- heartbeat, stale-source, and maximum-runtime checks ran only after the
  unbounded sync returned.

Implemented safeguards:

- bounded 1,000-event in-memory batches and one MiB maximum JSONL line size;
- one atomic journal/apply/cursor transaction per batch;
- 64 MiB uncommitted-backlog fail-closed ceiling;
- in-transaction progress callbacks so a watchdog failure rolls back the batch;
- independent 30-second processing-progress watchdog and independent runtime
  deadline enforcement;
- periodic progress heartbeat fields for batch size, backlog, progress time,
  watchdog state, fatal code, and safe-shutdown marker;
- durable `FAILED_CLOSED` safe-shutdown marker for liveness, backpressure,
  source-validation, and terminal session-health failures;
- explicit rejection of `session_completed` when campaign completeness or
  observation continuity is unhealthy;
- bounded, exactly-once committed-prefix restart and cursor catch-up.

Validation:

- telemetry-stall, overload, fail-closed marker, healthy long-run, incomplete
  session health, and soak-scale cursor catch-up tests pass;
- a 5,000-event healthy fixture and a 5,000 + 100 event restart/catch-up fixture
  reconcile exactly;
- 10,000 preserved soak events processed in 0.479278 seconds across ten
  1,000-event batches, or 20,864.72 events/second;
- Repricing tests: 51 passed;
- full repository tests: 197 passed.

Artifacts:

- `polymarket/models/repricing_research_v1/runtime_backpressure_liveness_fix_v1/runtime_fix_report.md`;
- `polymarket/models/repricing_research_v1/runtime_backpressure_liveness_fix_v1/runtime_fix_validation.json`.

`ALPHA-B001`, `ALPHA-B004`, and `ALPHA-B007` remain `IN_PROGRESS` until a
second unattended soak validates the fixes under live growth. `ALPHA-B002`
remains resolved. No capture or soak was launched in this sprint.

The next active task is **Run Second 24-Hour Repricing Paper Soak v1**. It is
authorized only after a fresh green preflight and must demonstrate complete
capture continuity, current heartbeat, bounded shutdown, and exact
live-versus-offline reconciliation.

No detector, threshold, strategy, fingerprint, evidence gate, holdout,
wallet/private-key, order, or live-money behavior changed.

## Second 24-Hour Repricing Paper Soak v1 Recovery

The second soak was recovered after an external power interruption before its
scheduled completion. Recovery status is `RECOVERED_DESCRIPTIVE_ONLY`. The raw
session remains outside GitHub and was not edited. It contains 691,284 valid
JSONL records, no malformed or partial line, and ends exactly at capture
checkpoint 40,638 (`2026-06-30T18:15:38.155862+00:00`, line 691,284, byte
324,528,106). The immutable session SHA-256 is
`491a5363051e5ed033513d85a22bb6bc5c9a205faf1d5cdad2fe753b9dbb526f`.

The recovered source covers 40,638 / 43,200 planned checkpoints (94.069444%)
over 81,273.99968 seconds. `session_completed` is absent and the largest
checkpoint gap is 891.868253 seconds. Replay completed twice with matching
artifacts: 807 completed windows, eight opportunities, 99.85% reference
coverage, 0.86% data gaps, and v5 verdict `INSUFFICIENT_DATA`.

Frozen repricing export completed twice and matched byte-for-byte. Descriptive
results are 84 signals; BTC / ETH / SOL 14 / 30 / 40; YES / NO 35 / 49; 58
wins; 69.047619% win rate; +0.0383214286 after-slippage expectancy; +3.219
after-slippage P&L; +4.899 before-slippage P&L; and 0.45 maximum drawdown.
Exits are 58 repricing targets, 23 stop losses, and three timeouts. The durable
ledger passes SQLite integrity and its 84 signals, positions, and closed trades
reconcile exactly with offline export; no position remains open.

Operational interruption and research output remain separate. The managed
runtime recorded `FAILED_CLOSED` / `TELEMETRY_STALLED` before final capture
interruption. The run is analytically useful, but campaign completion,
continuity, and fatal-marker gates fail. It contributes zero rows, hours, or
sessions to frozen evidence. Valid aggregate evidence remains 172 signals,
24.000000389 hours, and two independent sessions, below the weak gates of 40
hours and three sessions. The sealed holdout remained untouched.

GitHub-safe artifacts are under
`polymarket/models/repricing_research_v1/paper_soak_v2_recovery_summary/`.
The next active task is **Diagnose Repricing Runtime Telemetry Stall After
Interrupted Soak v1**. No new soak is authorized during that task.

## Repricing Soak v2 Telemetry Stall Diagnosis

Root cause is confirmed as host S3 sleep, not ingestion backpressure. Windows
Power-Troubleshooter records sleep from `2026-06-30T17:52:16.060434Z` through
`2026-06-30T18:07:06.226392Z`, with power-button wake. Kernel-Power Event 42
records `Application API` as the sleep reason. The OS did not reboot.

The runtime committed event 685145 at `2026-06-30T17:52:16.146150Z`, then its
health log paused for 900.159992 seconds while the source developed an
891.868253-second checkpoint gap. On resume, the independent watchdog correctly
failed closed and preserved an atomic, fully reconciled ledger. The prior
bounded-ingestion fix therefore worked, but two gaps remained: the canonical
MVP did not activate the existing Windows sleep inhibitor, and host suspension
was reported under the ambiguous `TELEMETRY_STALLED` code.

The managed MVP now holds `WindowsSleepInhibitor` for its complete locked
lifetime. The watchdog also measures its own scheduling gap: a gap at least
five times the processing-stall threshold fails closed as
`HOST_SUSPEND_DETECTED`, while a genuine active-batch stall remains
`TELEMETRY_STALLED`. Host suspension is not recoverable and cannot silently
continue.

The diagnostic artifact is under
`polymarket/models/repricing_research_v1/soak_v2_telemetry_stall_diagnosis/`.
Another soak is allowed only after a fresh preflight. The next active task is
**Run Third 24-Hour Repricing Paper Soak v1**. The interrupted second soak
remains excluded from evidence, and the frozen strategy and sealed holdout are
unchanged. Validation passes with 53 Repricing tests and 199 repository tests.

## Third 24-Hour Repricing Paper Soak v1

The third public-only soak completed its full source duration with a healthy
sleep-inhibited host, but final verdict is
`FAILED_TERMINAL_DRAIN_RECONCILIATION`. Source capture was complete and
continuous: 43,200 / 43,200 checkpoints, 100% coverage, 2.105269-second maximum
gap, zero fatal capture errors, no wall-clock discontinuity, and no Windows
sleep/resume transition.

The managed runtime stopped cleanly after 86,398.257341 wall-clock seconds with
no restart, fatal marker, watchdog trip, backlog, rejected stream event,
duplicate, or open position. The ledger passes SQLite integrity and contains
175 signals, 175 positions, and 175 closed trades. Live and deterministic
offline paper results reconcile exactly by count, asset, side, and P&L.

Terminal source reconciliation failed by four records. The runtime cursor
stopped at event 741,528 while the source ends at 741,532. The producer appended
three historical `shadow_trade` rows after the final checkpoint, followed by
`session_completed`. Their timestamps precede the final checkpoint, violating
the adapter's monotonic-order contract, and the runtime never consumed terminal
source health.

Descriptive frozen export is 175 signals; BTC / ETH / SOL 33 / 39 / 103; YES /
NO 82 / 93; 68.571429% win rate; +0.0371228571 expectancy after slippage;
+6.4965 P&L after slippage; and 0.77 maximum drawdown. Replay and export each
match their repeat byte-for-byte.

The run is excluded from evidence because operational integrity failed.
Scientifically valid evidence remains 172 signals, 24.000000389 hours, and two
sessions; weak evidence remains below its 40-hour and three-session gates.
Artifacts are under
`polymarket/models/repricing_research_v1/paper_soak_v3_summary/`.

The next active task is **Fix Repricing Terminal Drain And Session Completion
Reconciliation v1**. No fourth soak is authorized until terminal event ordering,
post-deadline drain, and explicit runtime consumption of `session_completed`
are fixture-validated. The frozen strategy and sealed holdout remain unchanged.
All 53 Repricing tests and all 199 repository tests pass.

## Repricing Terminal Drain And Session Completion Fix v1

The third-soak terminal failure is fixed at component and regression level.
Root cause had two parts: final `shadow_trade` summaries were appended with
historical envelope timestamps after the final checkpoint, and the managed
runtime treated its nominal duration as an immediate stop without draining
producer finalization.

Producer terminal summaries now retain historical business time inside their
payload while using final append time for the JSONL envelope. Production paper
runtimes require `session_completed` and enter a bounded 60-second `DRAINING`
phase at nominal expiry. Success requires complete campaign/continuity health,
zero remaining source bytes, and a durable cursor through the final event.

Missing completion fails closed as `TERMINAL_DRAIN_INCOMPLETE`; missing or
disagreeing terminal health fails as `SESSION_HEALTH_INCOMPLETE`. The MVP also
rejects a false `STOPPED` result unless completion, health, and terminal drain
are all verified. Heartbeat state now exposes session-completion and drain
status.

Regression fixtures cover delayed post-deadline completion, 258 terminal
events drained across 32-event batches, final atomic flush, exact cursor EOF,
missing completion, missing health fields, false clean stop, and producer
append monotonicity. No new soak was launched.

Artifacts are under
`polymarket/models/repricing_research_v1/terminal_drain_fix_v1/`. The next task
is **Run Fourth 24-Hour Repricing Paper Soak v1**, authorized only after fresh
preflight. Frozen evidence remains 172 signals, 24.000000389 hours, and two
sessions; strategy and holdout boundaries are unchanged.

## Repricing Evidence Protocol Review v1

The protocol review retains **Run Fourth 24-Hour Repricing Paper Soak v1**.
This is not justified as another generic endurance repeat. Frozen admissible
evidence is 172 signals over 24.000000389 hours and two independent sessions;
a valid 24-hour session would produce 48 observed hours and three sessions,
crossing the currently missing weak-evidence duration and independence floors.
A valid 6-hour or 12-hour session would reach only about 30 or 36 aggregate
hours and would leave the 40-hour gate failed.

At the frozen planning density of 3.9184 signals/hour, 6 / 12 / 24 hours are
expected to add about 24 / 47 / 94 signals. At the observed admissible density
of 7.1667 signals/hour, they would add about 43 / 86 / 172. The corresponding
nominal independent-signal standard-error reduction versus the current
172-signal sample is approximately 6-10% / 11-18% / 20-29%; serial correlation
and session clustering make those figures optimistic.

No known correctness defect requires more than 12 hours to manifest. The first
soak failed after about 3.4 healthy runtime hours, terminal reconciliation can
be exercised at any bounded duration, and deterministic fixtures now cover its
exact race. The second soak's host suspension happened late because of an
external host event, not a duration-dependent algorithm. A 24-hour run still
adds operational information by increasing exposure to host scheduling,
resource growth, market rotation, UTC daily reporting, and terminal shutdown.

Going forward, operational validation is tiered: deterministic regression and
preflight first; an evidence-ineligible bounded 2-hour canary only when a live
integration uncertainty is not covered by fixtures; a 12-hour integrity run
for changes whose risk is accumulation or rotation but not daily-boundary
behavior; and a 24-hour canonical run only when required for a frozen evidence
gate, UTC-day/endurance validation, or final operational admission. Existing
weak, moderate, and strong evidence gates are unchanged. The fourth soak skips
an extra canary because the exact terminal defect is fixture-reproduced and a
12-hour run cannot close the next scientific gate.

## Fourth Soak Prelaunch Abort

The first fourth-soak launch attempt was aborted after 2.007355 seconds of
source capture and before the managed paper runtime started. PowerShell wrote
`runtime_config.json` with a UTF-8 BOM; the strict UTF-8 loader rejected it.
The orchestration sequence had started the producer before parsing runtime
configuration, so the producer was stopped immediately and no replacement was
launched in the same task.

The preserved prefix contains six valid public events, zero signals, no paper
positions, and no `session_completed`. It is operationally incomplete and
evidence-ineligible. Frozen valid evidence remains 172 signals,
24.000000389 hours, and two sessions; Weak Evidence remains failed.

The loader now accepts `utf-8-sig`. The exact preserved config parses and
passes preflight, and a Windows BOM regression is included. Future launch
ordering must parse and statically validate runtime configuration before any
producer starts. All 59 Repricing tests and all 205 repository tests pass.
The frozen strategy and sealed holdout remain unchanged.

Artifacts are under
`polymarket/models/repricing_research_v1/paper_soak_v4_prelaunch_abort_summary/`.
The successor is **Run Fourth 24-Hour Repricing Paper Soak v1 - Clean
Relaunch**, subject to fresh preflight and exactly one producer.

## Fourth 24-Hour Repricing Paper Soak v1 - Clean Relaunch

The canonical clean relaunch passed operational integrity. The public source
ran for 86,400 seconds with 43,200 / 43,200 checkpoints, 100% temporal
coverage, a 2.090353-second maximum gap, zero fatal capture errors, and a final
append-monotonic `session_completed` event.

The managed runtime ran for 86,400.51311 seconds and consumed all 741,438
records through source index 741,437. Terminal health and drain passed. There
was zero final backlog, no fatal marker, watchdog trip, host suspension,
restart, duplicate, rejected event, stale source, or open position. Its 166
signals, positions, and trades reconcile exactly to deterministic replay and
export; repeat hashes match.

Batch results are 31 BTC / 39 ETH / 96 SOL and 61 YES / 105 NO signals,
78.915663% win rate, +0.042771 expectancy after slippage, +7.1000 P&L after
slippage, and 0.2600 maximum drawdown.

Admissible Batch 001, Batch 002, and soak evidence now totals 338 signals over
48.000000389 hours and three independent sessions. Aggregate BTC / ETH / SOL
is 76 / 80 / 182; YES / NO is 128 / 210; win rate is 71.301775%; expectancy is
+0.032405; after-slippage P&L is +10.9530; and max drawdown is 0.8750. Every
frozen Weak Evidence gate passes, including positive expectancy in all assets
and both sides. Nominal 95% intervals are 66.2612%-75.8636% for win rate and
+0.021666 to +0.043145 for expectancy, with serial-correlation and
three-session limitations.

Repricing advances to weak development evidence, not proven edge. The next
task is **Run Repricing Weak-Evidence Stability And Executable-Cost Stress
Sprint v1**. No holdout was opened and no live trading was enabled.

Artifacts are under
`polymarket/models/repricing_research_v1/paper_soak_v4_summary/`.

## Repricing Weak-Evidence Cost Stress v1

The three admitted sessions and 338 signals were evaluated under a frozen
execution-stress grid. As-of entry spread and visible side size were recovered
from raw public sessions with 100% coverage. The sprint conclusion is
`WEAKENED`.

Recorded conservative evidence remains +0.032405 expectancy, +10.9530 P&L,
and 0.8750 drawdown with all sessions, assets, and sides positive. Stability is
limited: the fourth-soak session contributes 64.82% of P&L and SOL contributes
46.37%, both above the 40% concentration target.

Half-spread (+0.023673), an additional 0.005 transaction cost (+0.027405),
fill impairment (+0.006651), and modeled delay through one second (+0.022508)
remain positive. Quote-age stress falls below the weak expectancy floor.
Combined moderate execution is negative: -0.015614 expectancy, -5.2777 P&L,
and 5.2777 drawdown with zero positive sessions.

Actual public bid/ask replay is positive at immediate execution (+0.035944),
but a two-second entry plus 0.005 cost is negative across all sessions:
-0.009810 expectancy, -3.3157 P&L, 3.9548 drawdown, and nominal 95% expectancy
interval [-0.018432, -0.001188]. Five-second visible-size scenarios are also
negative.

Weak Evidence therefore does not remain stable under executable-cost stress.
The detector may contain short-lived timing information, but current data do
not prove it can be captured at realistic end-to-end latency. Repricing does
not advance to production-candidate status. The next task is **Run Repricing
Execution Latency Feasibility Audit v1**. Frozen strategy, evidence protocol,
and sealed holdout remain unchanged.

Artifacts are under
`polymarket/models/repricing_research_v1/weak_evidence_cost_stress_v1/`.

## Repricing Execution Latency Feasibility Audit v1

The audit conclusion is `INSUFFICIENT_MEASUREMENT`. The current polling
architecture is not capable of reliable sub-two-second execution and cannot
achieve sub-one-second execution.

Across 338 admitted signals, quote age was 1.771s minimum, 2.653s median,
7.137s p95, and 49.065s maximum before runtime consumption or order submission.
The source checkpoint cadence is 1.998s median and the runtime adds a configured
0-1s stream-poll phase delay. Home-PC CLOB cold HTTPS was 178ms median and
346ms p95, with a 6.857s outlier; Binance REST was 1.169s median.

Local processing is negligible: detector decision 0.0043ms median, JSON
encode/decode about 0.0054ms combined, and full-sync SQLite commit 0.859ms
median. The current inferred end-to-end lower bounds are approximately 1.914s
best, 3.333s median, 8.435s p95, and 56.925s worst observed, excluding
authenticated signing, order submission, exchange acknowledgement, matching,
and queue delay.

Sub-two-second execution is plausible only after a major event-driven redesign:
persistent external and CLOB WebSockets, one in-memory decision loop,
asynchronous durability, persistent order transport, and deployment near the
CLOB region. Sub-one-second median may be technically plausible in-region but
is not proven and cannot be claimed from current public data.

Engineering improvements alone do not make Repricing production-ready. The
two-second executable replay is already negative, and authenticated execution
latency/fills are unmeasured. The branch should proceed only to a bounded public
WebSocket timing instrument while less latency-sensitive hypotheses receive
priority. Frozen strategy, evidence gates, and sealed holdout remain unchanged.

Artifacts are under
`polymarket/models/repricing_research_v1/execution_latency_feasibility_audit_v1/`.
The next task is **Implement Repricing Public WebSocket Latency Instrumentation
v1**.

## State update protocol

At the end of every completed active task:

1. Move the result into Completed milestones.
2. Refresh blockers and latest measured metrics from generated artifacts.
3. Update the active milestone if its exit criteria changed or passed.
4. Add material decisions to `DECISIONS.md`.
5. Replace the completed task in `NEXT_TASK.md` with exactly one active task.
6. Keep speculative work in `RESEARCH_BACKLOG.md`.

## Current commands

```powershell
python -m polymarket.edge_engine_v5 capture --assets BTC ETH SOL --duration 21600
python -m polymarket.edge_engine_v5 lifecycle --assets BTC ETH SOL --duration 600 --poll-interval 1
python -m polymarket.resolution_engine reconcile
python -m polymarket.resolution_engine replay
python -m polymarket.feature_engine build
python -m polymarket.dataset_quality analyze
python -m polymarket.dataset_quality build-public
python -m polymarket.evidence_batch resume --session polymarket/runs/v5/20260619_223637/session.jsonl --resolution-mode replay
python -m unittest discover -s tests -v
```

## Repricing Public WebSocket Latency Instrumentation v1

A bounded 180-second simultaneous benchmark completed with 137,107 public CLOB
WebSocket events, 179 REST polling observations, and 974 Binance WebSocket
trade events. No authentication, wallet, order, strategy, threshold, evidence,
model, or holdout path was used.

The public WebSocket path removed the polling cadence bottleneck. CLOB
inter-message gap p95 improved from 5,150.8863 ms under simultaneous polling
to 6.7460 ms over WebSocket. WebSocket p95 queue, parse, decision,
serialization, and journal latencies were 0.0003, 0.0298, 0.0016, 0.0207, and
0.2632 ms. Local processing is not the dominant blocker.

Absolute server-to-local quote age remains clock contaminated: both CLOB paths
showed an approximately one-second offset without NTP correction. Same-host
mean quote-age improvement was 11.8656 ms; compared descriptively with the
prior admitted-signal polling mean, the observed WebSocket value was 2,477.5
ms lower. CLOB packet loss is not measurable because the public feed has no
usable sequence number.

Sub-two-second public ingestion and decision is supported. End-to-end
execution below two seconds is plausible but unvalidated; sub-one-second
end-to-end execution remains unproven. Authenticated signing, order transport,
acknowledgement, matching, queue position, and fills now dominate uncertainty.
Weak Evidence is conditionally executable in principle, not production-ready.

Artifacts are under
`polymarket/models/repricing_research_v1/websocket_latency_instrumentation_v1/`.
The next task is **Design Repricing Authenticated Execution Latency Measurement
Protocol v1**. This is design-only and does not authorize credentials or orders.

## Repricing Authenticated Execution Latency Measurement Protocol v1

The complete authenticated execution measurement protocol is designed without
credentials, private keys, authenticated calls, or orders. It separates signal,
decision, EIP-712 signing, L2 authentication, serialization, transport,
acknowledgement, acceptance, book appearance, partial/complete match,
settlement, cancellation, timeout, retry and reconciliation timestamps.

The frozen economic break remains two seconds. Protocol feasibility gates are
stricter: signal-to-ack p95 <=750 ms, signal-to-first-match p95 <=1,000 ms,
and signal-to-terminal-fill-or-cancel p95 <=1,500 ms, with zero duplicates or
unreconciled ambiguous submissions. At least 100 fixed-protocol attempts over
three independent sessions would be required for a later authenticated
feasibility conclusion.

Using measured public transport proxies and explicitly modeled unknown stages,
the expected warm Home-PC signal-to-ack path is 145 ms best, 205 ms median,
490 ms p95, and over 7 seconds in the observed transport tail. Expected
signal-to-first-match is 175 ms best, 275 ms median and 800 ms p95, with timeout
or no fill as the true worst case. These estimates are not order measurements.

Weak Evidence remains conditionally executable in principle, but Repricing is
`NOT_PRODUCTION_READY_EXECUTION_FEASIBLE_TO_MEASURE`. The next task is
**Implement Repricing Authenticated Execution Latency Dry-Run Harness v1**.
That task permits only deterministic signer/transport stubs and a local sink;
it does not authorize credentials, authenticated endpoints, wallets, or orders.

## Repricing Authenticated Execution Latency Dry-Run Harness v1

The deterministic no-secret harness is implemented with canonical event IDs,
hash-chained predecessor correlation, monotonic and UTC timestamps, fixture
signer and L2-header boundaries, a loopback-only HTTP sink, fixture lifecycle
updates, partial/complete fills, cancellation, clock gates, bounded pre-send
retry, ambiguous-timeout fail-closed behavior, redaction and replay.

A 120-attempt benchmark completed with 60 fixture fills and 60 fixture
cancellations. Replay validated 1,680 events and 120 terminal correlations. Two
independent runs produced identity hash
`91f195181252da87d05d6c18a620a0e38e975e546cef93ac74a12d40f5392633`.
No credentials, authenticated endpoint, wallet, private key or order was used;
all network traffic was restricted to `127.0.0.1`.

Measured local p95 was 0.3091 ms fixture signing, 0.0255 ms serialization/auth
stub, 1.0215 ms transport queue, 16.8979 ms signal-to-local-ack, 31.1120 ms
signal-to-first-fixture-transition and 47.7829 ms signal-to-terminal. Local
numerical gates pass, but authenticated exchange admission is `NOT_EVALUATED`.
The prior 490 ms acknowledgement and 800 ms first-match models are neither
confirmed nor rejected.

Weak Evidence remains conditionally plausible and Repricing remains
`NOT_PRODUCTION_READY_LOCAL_HARNESS_VALIDATED`. The next task is **Integrate
Repricing Latency Dry-Run Harness With Public Event Stream v1**, still with no
credentials or real orders.

Artifacts are under
`polymarket/models/repricing_research_v1/authenticated_execution_dry_run_harness_v1/`.

Artifacts are under
`polymarket/models/repricing_research_v1/authenticated_execution_measurement_protocol_v1/`.

## Repricing Public-Stream Latency Dry Run v1

The no-secret latency harness is integrated with the live public CLOB WebSocket
and a loopback-only execution sink. A bounded 90-second run completed 60
correlated engineering probes across BTC / ETH / SOL counts of 21 / 20 / 19.
It observed 38,194 public events, zero reconnects, zero stale events, zero
backpressure drops and 60 / 60 subsequent same-token public transitions.

Measured p95 was 2.2538 ms from public receipt to probe signal, 9.8616 ms from
signal to local acknowledgement, 36.4036 ms from signal to the next public
event and 15.4593 ms from signal to fixture terminal. Public event-gap p95 was
29.6157 ms and maximum was 264.8276 ms. Reported absolute event age remained
clock contaminated by an approximately one-second server/local offset.

Replay validated 900 lifecycle events and 60 terminal correlations. The probe
is not a frozen-strategy trade signal and is ineligible as research evidence.
No credential, authenticated endpoint, wallet, private key or real order was
used. Local/public engineering gates pass; authenticated exchange admission
remains `NOT_EVALUATED`.

Weak Evidence remains conditionally executable. Production status is
`NOT_PRODUCTION_READY_PUBLIC_DRY_RUN_VALIDATED`. The next task is **Prepare
Repricing Credentialed No-Order Calibration Security Review v1**, which may
design and verify controls but may not provision credentials or contact an
authenticated endpoint.

Artifacts are under
`polymarket/models/repricing_research_v1/public_stream_dry_run_v1/`.

## Repricing Credentialed No-Order Calibration Security Review v1

The review verdict is `NOT_AUTHORIZED_SANDBOX_ENFORCEMENT_REQUIRED`. No
credential, private key, authenticated endpoint, heartbeat, order or
cancellation was used.

A mechanically testable deny-by-default policy now conditionally allowlists
only `GET /data/orders`, `GET /trades`, public `GET /time`, and receive-only
connection to the authenticated user WebSocket. All state-changing methods,
order/cancel paths, heartbeat, credential creation/derivation, redirects,
unknown routes, wallet material and general-purpose authenticated CLOB SDKs are
forbidden.

The review defines external secret injection, exact environment names,
structural redaction, process isolation, proxy-only egress, kill-switch and
parent-watchdog behavior, empty-open-order precondition, audit hashes,
fail-closed conditions and rollback. Because L2 credentials may carry trading
capability, application policy alone is insufficient; a sandbox and egress
proxy must prove order-route unreachability before authorization is considered.

The next task is **Implement Repricing No-Order Calibration Sandbox Enforcement
v1** using fixture credentials and local endpoints only. Real credentials and
authenticated calls remain forbidden.

Artifacts are under
`polymarket/models/repricing_research_v1/credentialed_no_order_security_review_v1/`.

## Repricing No-Order Calibration Sandbox Enforcement v1

The fixture sandbox verdict is
`SANDBOX_FIXTURE_READY_REAL_CALIBRATION_NOT_AUTHORIZED`. It implements exact
deny-by-default routing, a no-socket fixture proxy, direct-egress denial,
fixture-only secret handles, clean environment rules, kill switch, parent and
proxy watchdogs, zero-open-order abort, structural redaction, deterministic
hash-chained audit replay and operator rollback.

Fixture validation allowed the observational routes and denied order, batch
order, cancellation, heartbeat, unknown route and direct-egress attempts.
Parent death, watchdog expiry, proxy loss and nonzero open orders fail closed.
Eight compact audit records replayed with terminal hash
`6e6353ac8ad6522df320540f9f1ee6552585ed204e8fcbe301cc7445db170ba6`.

No credentials, authenticated calls, network calls, orders, cancellations,
wallet material, holdout access or strategy changes occurred. Application and
fixture controls pass, but host firewall/process isolation and independent
authorization remain unverified. Real calibration is still blocked.

The next task is **Run Repricing No-Order Calibration Independent Authorization
Gate Review v1**. It may verify host-level controls and authorization evidence
but may not provision credentials or make authenticated calls.

Artifacts are under
`polymarket/models/repricing_research_v1/no_order_sandbox_enforcement_v1/`.

## Repricing No-Order Calibration Independent Authorization Gate Review v1

Authorization verdict: `NOT_AUTHORIZED`. The fixture sandbox, exact route
policy, redaction, zero-open-order gate, kill switch, watchdog, audit replay and
rollback hooks pass at application/fixture level. No credentials,
authenticated calls, orders, cancellations, wallet material, holdout access or
strategy changes occurred.

Host containment fails the independent gate. Domain, Private and Public
Windows Firewall profiles all reported disabled with outbound policy not
configured, and no matching ForgeView/Polymarket/Repricing/Calibration outbound
rule exists. No restricted process boundary, operational external secret
provider, assigned revocation/rollback/incident owner, unique expiring
authorization record or host-level failure drill evidence exists.

Credentialed no-order calibration may not proceed. The next task is **Implement
Repricing No-Order Calibration Host Containment Preflight v1**, restricted to
read-only inspection, fixture process isolation and non-applied firewall/proxy
plans. It may not enable firewall rules, provision credentials or authenticate.

Artifacts are under
`polymarket/models/repricing_research_v1/no_order_authorization_gate_review_v1/`.

## Repricing No-Order Calibration Host Containment Preflight v1

The read-only Windows preflight is implemented and fixture-tested. It checks
firewall profiles, scoped outbound rules, proxy/direct-egress evidence,
restricted process metadata, clean child environment, kill switch, watchdog,
owners, expiring authorization, secret-provider metadata and host drills. It
returns PASS only when every mandatory gate passes and never authorizes
calibration itself.

The live Home PC result is `NOT_READY_FOR_CREDENTIALS` with 14 failed gates.
All three Windows Firewall profiles remain disabled, no scoped containment
rules exist, and proxy, restricted process, host kill/watchdog drills, owner
assignments, authorization record, provider metadata and host drill evidence
are absent. Firewall inspection and clean fixture child environment pass.

The implementation reads environment names but not secret-provider values,
rejects secret-bearing governance fields, uses only read-only firewall cmdlets
and emits `host_settings_modified=false`. No credentials, authenticated calls,
orders, cancellations, holdout access or strategy changes occurred.

The next task is **Prepare Repricing Host Containment Remediation And Governance
Package v1**. It may refine proposed changes and role templates for approval but
may not apply host settings or use credentials.

Artifacts are under
`polymarket/models/repricing_research_v1/host_containment_preflight_v1/`.

## Repricing Host-Containment Architectural Review v1

The architectural decision is `C_CHANGE_RESEARCH_PRIORITY`. The complete host
remediation/governance package is not the highest-value immediate task, and
minimum containment for credentialed no-order calibration is deferred.

Weak Repricing evidence remains preserved: immediate execution replay is
positive, while actual two-second entry plus cost is negative. Public WebSocket
and local paths are already fast. The decisive unknown is the real order path:
EIP-712 signing, order submission, exchange acceptance, matching, queue
position, fills and cancellation. Credentialed no-order calibration measures
only L2 authentication, read RTT and user-channel behavior, so it cannot close
that uncertainty.

The full governance package has low direct information gain and high cost. A
minimum package has low-to-moderate engineering information gain but still does
not establish executability. Public-only review of less-latency-sensitive
hypotheses has the highest current portfolio-level information gain and avoids
credential and Home PC containment risk.

Repricing is preserved as `PRESERVED_DEFERRED`, not rejected. If reactivated,
only mandatory containment should be implemented before a bounded no-order
calibration; optional production governance remains postponed. All existing
authorization and safety gates remain unchanged.

The next task is **Run Public-Only Less-Latency-Sensitive Strategy Candidate
Review v1**.

Artifacts are under
`polymarket/models/repricing_research_v1/host_containment_architectural_review_v1/`.

## Polymarket Research Portfolio Synthesis v1

Incremental infrastructure work is stopped. The existing public datasets and
research artifacts were reviewed as one portfolio, with profitability speed as
the selection objective. The sealed holdout remains untouched.

The primary research branch is now **Wallet Intelligence**. Its strongest
existing signal is not generic wallet following: four of 28 evaluated wallets
passed above-baseline outcome-alignment gates on 258 resolved fast-crypto
positions, with individual match rates from 0.714286 to 0.833333. The complete
sample contains 1,788 resolved positions, including three below-baseline
wallets, so wallet identity and asset specialization must be frozen before any
validation. Prospective public observability remains inconclusive at only two
eligible trades and cannot support a copyability claim.

Repricing remains `PRESERVED_DEFERRED`. Its 338-signal weak-evidence result is
statistically meaningful and beats a matched random-timing baseline, but actual
two-second entry plus cost produced -0.009810 expectancy. More credential,
containment or sub-second infrastructure is not justified before a strategy
passes public, cost-aware validation.

Final-outcome prediction and standalone microstructure prediction are frozen as
negative controls: YES price remained best, and the 426-row microstructure
sample produced no stable incremental feature. Microstructure may be reused
only as a preregistered feasibility or regime filter.

The next task is **Run Wallet Specialist Alpha Chronological Validation v1**.
It uses existing public data only, attempts to disprove the four-wallet
specialist hypothesis with leakage-safe time splits and conservative
delay/cost assumptions, and may not tune wallet selection or strategy
parameters on evaluation folds.

Artifacts are under `polymarket/models/research_synthesis_v1/`.

## Repricing Slower-Horizon Derivative Validation v1

The final Repricing derivative test is complete with a **NO-GO**. Using the
same 338 frozen signal anchors, actual executable ask-to-bid quotes, a two-second
entry delay and the existing 0.005 transaction-cost stress, continuation point
estimates were positive at 30, 60, 120 and 180 seconds. None passed the complete
gate.

The best continuation point estimate was 120 seconds: 269 signals, 56.51% win
rate, +0.038394 expectancy, +10.328 P&L and 3.922 max drawdown. Its clustered
95% interval was [-0.026077, +0.101316], matched random timing was not beaten,
and SOL expectancy was negative. The 30-second and 60-second anchors beat
matched random timing, but their adjusted confidence intervals crossed zero
and asset/session P&L concentration exceeded 40%. Mean reversion was negative
at all four horizons and in all three sessions.

Repricing is permanently frozen. Existing code, datasets and reports remain
preserved for audit and negative-control use, but no Repricing evidence,
execution, latency, credential, infrastructure or derivative task may be
prioritized. Wallet Intelligence remains permanently frozen under D-123.

The next task is **Run Polymarket Executable Structural Mispricing Triage v1**,
an existing-data-only review of directly executable non-directional
opportunities such as complete-set and internally crossed public quotes.

Artifacts are under
`polymarket/models/repricing_research_v1/slower_horizon_derivative_validation_v1/`.

## Polymarket Executable Structural Mispricing Triage v1

Decision: **B_FREEZE_STRUCTURAL_MISPRICING_RECOMMEND_NEW_DIRECTION**.

The fixed existing-data triage used five complete and continuous public
sessions totaling 60 hours, 2,175 markets, 320,736 raw snapshots and 280,284
valid fresh deduplicated quote states. It found zero crossed/inverted books,
zero locked books, zero positive near-expiry structural states and zero
profitable conservative capacity.

Temporary wide spreads were the only frequent pattern: 7,534 states in 6,312
episodes, or 125.5667 states/hour. Only 533 episodes persisted two seconds and
102 persisted five seconds. The best marketable net margin was -0.040000 and
mean margin was -0.066406 after the existing 0.01 cost. Passive spread capture
cannot be admitted because both queue fills and adverse selection are unknown.

The schema contains one independent YES book. It does not contain independently
synchronized NO-token books or multi-outcome books. Algebraically derived
complete-set acquisition and liquidation margins are exactly `-YES spread`
before cost; the best observed theoretical margin was -0.011000 after cost.

Structural mispricing is permanently frozen. Wallet Intelligence and Repricing
remain frozen. The next task is **Run Polymarket Passive Liquidity Provision
Existing-Data Feasibility Triage v1**, which may test maker-fill proxies and
post-fill adverse selection from the same sessions but may not capture data,
place orders or treat displayed spread as earned P&L.

Artifacts are under `polymarket/models/structural_mispricing_triage_v1/` and
the branch record is `docs/polymarket/STRUCTURAL_MISPRICING_RESEARCH_V1.md`.

## Polymarket Passive Liquidity Provision Existing-Data Feasibility Triage v1

Decision: **B_FREEZE_PASSIVE_LIQUIDITY_PROVISION_RECOMMEND_NEW_DIRECTION**.

The fixed replay used the same five complete public sessions and 6,312
wide-spread episodes. Maker-fill eligibility required subsequent fresh public
quotes to deplete through the posted level. Expected quantity was discounted
to 37.5% of capped visible size using the existing severe fill and miss
assumptions. Unmatched inventory was crossed out after fixed quote lives plus
two-second cancellation latency; displayed spread was never treated as P&L.

Every preregistered policy was negative with its market-cluster confidence
interval wholly below zero. Broad 2/5/15/30-second expectancy per attempt was
-0.795748 / -0.944989 / -1.244880 / -1.507288 dollars. Longer quote life
increased two-sided completion but worsened adverse-selection loss and
drawdown.

The least-negative policy was SOL 15s: 157 attempts (2.6167/hour), 36.54%
queue-adjusted fill probability, 73.20% one-sided share among triggered
attempts, 43.3709 expected filled shares/hour, -0.709218 dollars per attempt,
-0.042789 per expected filled share and 113.380 max drawdown. Its clustered
95% interval was [-0.977226, -0.452753]. No asset was positive; near-expiry
quoting was worse than broad 5-second quoting.

Passive liquidity provision is permanently frozen. The narrow five-minute
BTC/ETH/SOL research asset has now rejected outcome prediction, Wallet
Intelligence, Repricing, structural mispricing and passive LP after conservative
execution treatment.

The next task is **Run Polymarket Five-Minute Alpha Exhaustion And
Market-Universe Pivot Review v1**. It must decide whether the project should
pivot to slower or structurally richer Polymarket markets, or stop Polymarket
research, without launching data collection or implementation.

Artifacts are under `polymarket/models/passive_liquidity_triage_v1/` and the
branch record is `docs/polymarket/PASSIVE_LIQUIDITY_RESEARCH_V1.md`.

## Wallet Specialist Alpha Chronological Validation v1

The final Wallet Intelligence alpha sprint is complete with irreversible
decision `NO_GO_PERMANENTLY_FREEZE_WALLET_INTELLIGENCE`. Only existing public
data was used; sealed holdout outcomes were neither opened nor evaluated.

Frozen protocol:

- four previously selected H1 specialist wallets and their committed asset
  specialties;
- five-minute BTC/ETH/SOL Up/Down markets only;
- earliest BUY per wallet and condition, with simultaneous rows resolved by
  largest notional and no threshold search;
- three global chronological folds grouped by condition ID;
- 30-second observation delay, at least 60 seconds remaining after detection,
  and fixed 0.05 adverse entry burden;
- severe stress at 60 seconds and 0.10 adverse entry burden.

Measured evidence:

- 124 eligible signals across 119 unique markets and seven UTC dates;
- 96 matched and 28 unmatched outcomes, 77.4194% match rate, Wilson 95%
  69.3010%-83.8899%;
- reported-price expectancy +0.009937, but conservative expectancy -0.038117
  with 95% interval -0.105499 to +0.029264;
- the same-protocol non-candidate population produced -0.037642 conservative
  expectancy on 910 signals, so specialists did not improve executable value;
- conservative maximum drawdown 6.901368;
- severe-stress expectancy -0.075165 across 111 eligible signals;
- all three chronological fold expectancies were negative: -0.103971,
  -0.006424, and -0.007063;
- BTC / ETH / SOL conservative expectancy: -0.031251 / -0.088448 /
  +0.026667, with SOL supported by only nine signals and no confidence interval
  excluding zero;
- only six specialist-overlap markets existed; equal consensus was available
  on three with -0.223333 expectancy, while five weighted decisions produced
  -0.288000 expectancy;
- modeled decision-window median was 172.5 seconds, but direct contemporaneous
  spread and liquidity coverage was zero.

Individual conservative expectancy:

- `0x088df...025e`: +0.021818 on 26 signals, confidence interval crosses zero,
  all rows from one UTC date;
- `0x1cc53...b199`: +0.020208 on 46 signals, confidence interval crosses zero,
  only one of three folds positive;
- `0x29a55...7752`: -0.143750 on 16 signals;
- `0xde79...3d9a`: -0.108983 on 36 signals, all rows from one UTC date.

Mechanical ordering, market grouping, deterministic export, candidate freeze,
and repeatability gates pass. Promotion fails because candidate selection used
outcomes from the same bounded history, conservative aggregate value is
negative, every chronological fold is negative, no wallet has confidently
positive expectancy, consensus is sparse and negative, and delayed executable
quotes plus direct spread/liquidity/fill evidence are unavailable.

Wallet Intelligence is permanently frozen as a failed alpha direction. No
further Wallet exploration, scoring, monitoring, copyability, selection, or
execution work is authorized. The fastest remaining public-only route is the
preserved Repricing branch's slower 30-180 second continuation/reversion
derivative, tested without new capture or credential infrastructure.

Artifacts are under
`polymarket/models/wallet_intelligence_v1/specialist_alpha_chronological_v1/`.
Validation: 57 Wallet Intelligence tests and 256 repository tests pass.
