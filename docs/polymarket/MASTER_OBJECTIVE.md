# Polymarket Project - Master Objective

Status: Active  
Last updated: June 26, 2026
Authority: Permanent source of truth for the ForgeViewAI Polymarket project

This document defines why the project exists, what constitutes success, and
which gates must be passed before the system can progress from research to any
production consideration. If another Polymarket document conflicts with this
one, this document takes precedence.

## Project guidance hierarchy

Future engineering sessions must read these documents in order:

1. `MASTER_OBJECTIVE.md` - permanent objective and gates.
2. `PROJECT_STATE.md` - measured current status and blockers.
3. `NEXT_TASK.md` - the single authorized active task.
4. `DECISIONS.md` - durable architecture and policy decisions.
5. `RESEARCH_BACKLOG.md` - future ideas that are not yet active.

After completing work, update the state, decisions, and next-task documents in
the same change. Code is not fully handed off while those documents are stale.

## 1. Mission

Build a reproducible quantitative research system that determines whether
short-window Polymarket crypto markets contain a real, executable statistical
edge caused by slower probability repricing relative to external crypto
markets.

The system must distinguish genuine edge from simulation artifacts, data
errors, market-regime luck, latency advantages that cannot be captured, and
overfitting.

## 2. Final business objective

Create a defensible decision system that can identify, validate, and monitor
repeatable mispricing in BTC, ETH, and SOL five-minute UP/DOWN markets.

The research system may support a future decision about limited capital
deployment only after every production-readiness gate in this document is
passed and a separate execution project is explicitly authorized. The current
repository is research and shadow simulation only. It must not contain wallet,
private-key, order-placement, or real-money execution capability.

## 3. Research objective

Answer the following question with empirical evidence:

> Does external crypto price movement contain timely, incremental information
> about five-minute Polymarket outcomes or probability changes after accounting
> for class imbalance, missing data, latency, spread, slippage, market
> liquidity, and changing market regimes?

The project must also determine:

- whether the signal works on public, real-market observations rather than
  mock data;
- whether performance persists across BTC, ETH, SOL, and different periods;
- whether the signal remains after realistic delay and transaction costs;
- whether probability estimates are calibrated, not merely directionally
  accurate;
- whether observed performance survives walk-forward and untouched holdout
  evaluation.

The project may separately study short-horizon Polymarket contract repricing
as a development-only hypothesis. Repricing research asks whether external
BTC/ETH/SOL movement predicts favorable YES/NO price movement over the next
30-180 seconds, with exits before expiry. It is not the same as final
UP/DOWN outcome prediction and must remain separated from canonical
outcome-prediction training, validation, and holdout paths.

The project may also separately study public wallet behavior as Wallet
Intelligence Research. Wallet intelligence asks whether successful public
Polymarket profiles show repeatable timing, sizing, market-selection, or
holding-period patterns in fast BTC/ETH/SOL Up or Down markets. It is
descriptive research only. It must remain separated from outcome prediction,
repricing validation, live trading, wallet execution, production modelling,
and sealed holdout evaluation.

## 4. Success metrics

Engineering success:

- deterministic capture and replay;
- complete lineage from raw event to feature row, label, signal, and report;
- no silent fallback from public to mock data;
- automated tests pass from the repository root;
- public capture survives quote failures and market rollover without stopping.

Dataset success:

- at least 80% public samples in any mixed research dataset;
- a public-only modelling dataset with at least 1,000 completed windows;
- at least 200 completed public windows per supported asset;
- minority outcome class of at least 30%;
- feature completeness of at least 95%;
- duplicate rate no greater than 1%;
- authoritative or independently verified outcome labels;
- Dataset Quality Engine score of at least 75/100.

Model and strategy success:

- better out-of-sample log loss and Brier score than Polymarket price and
  unconditional-frequency baselines;
- positive net expectancy after conservative spread, fees, slippage, and
  latency assumptions;
- positive results across multiple non-overlapping walk-forward windows;
- no single asset, day, or regime contributes more than 40% of total net P&L;
- controlled drawdown and stable calibration;
- results remain positive under predefined stress tests.

These are minimum gates, not guarantees of production suitability.

## 5. Development stages

| Stage | Purpose | Status |
|---|---|---|
| 1. Paper simulation | Deterministic signals, simulated trades, and P&L | Complete |
| 2. Robustness validation | Noise, dropout, lag, slippage, and walk-forward testing | Complete |
| 3. Real-market shadow validation | Capture public Polymarket data and compare live versus model behavior | Complete |
| 4. Crypto lag scanner | Discover BTC/ETH/SOL five-minute markets and compare external prices | Complete |
| 5. Long evidence capture | Track rotating windows, lifecycle, shadow decisions, and evidence metrics | Complete |
| 6. Feature and dataset layer | Build one labelled feature row per completed market | Complete |
| 7. Dataset quality gate | Measure suitability and create public-only subsets | Complete |
| 8. Public evidence expansion | Collect a sufficiently large, complete, representative public dataset | Complete |
| 9. Baseline probability modelling | Freeze validation protocol, then train simple interpretable baselines | Active |
| 10. Out-of-sample alpha validation | Purged walk-forward, holdout, calibration, and cost stress tests | Not started |
| 11. Extended shadow probation | Freeze a candidate and monitor it prospectively without retraining | Not started |
| 12. Production-readiness review | Independent approval against all technical and risk gates | Not started |

Stages may not be skipped because later-stage results depend on the integrity of
earlier-stage evidence.

## 6. Architecture map

```text
Public Polymarket data + external BTC/ETH/SOL reference data
                              |
                              v
               Market discovery and lifecycle
                    edge_engine_v4 / v5
                              |
                              v
                Replayable raw session evidence
                      polymarket/runs/v5/
                              |
                 +------------+------------+
                 |                         |
                 v                         v
         Shadow validation           Feature Engine
         and evidence P&L            one row/window
                 |                         |
                 v                         v
         v5 evidence reports         training dataset
                                           |
                                           v
                                  Dataset Quality Engine
                                           |
                              +------------+------------+
                              |                         |
                              v                         v
                       quality report            public-only data
                                                        |
                                                        v
                                            future baseline models
                                                        |
                                                        v
                                              walk-forward validation
                                                        |
                                                        v
                                             shadow probation only
```

Primary locations:

- engines: `polymarket/`;
- operating documentation: `docs/polymarket/`;
- raw and generated evidence: `polymarket/runs/`;
- datasets: `polymarket/data/`;
- automated tests: `tests/polymarket/`.

Content Machine is a separate product area and must not be imported, modified,
or used by Polymarket modules.

## 7. Data quality requirements

Every modelling row must have:

- a stable market ID and asset;
- window start, expiry, feature timestamp, and resolution timestamp;
- source classification (`public` or `mock`);
- traceability to the originating session;
- features calculated only from information available at the feature timestamp;
- a deterministic label and explicit label source.

Required controls:

- mock and public observations must never be silently mixed;
- model selection and final validation must use public-only data;
- incomplete windows and unverified labels must be excluded, not imputed into
  outcomes;
- missingness must be reported per feature and by time period;
- duplicate markets and duplicate rows must be rejected;
- capture gaps, source changes, clock alignment, and quote failures must be
  observable;
- train, validation, and test splits must follow time order and prevent
  overlapping-window leakage.

Proxy labels based on external reference returns are acceptable for dataset
engineering, but authoritative Polymarket resolution labels are required
before a production-readiness claim.

## 8. Model quality requirements

No complex model should be introduced before simple baselines are measured.
The minimum comparison set is:

- unconditional class-frequency baseline;
- current Polymarket YES probability;
- simple logistic regression or equivalent interpretable linear probability
  model;
- the existing deterministic lag score.

Required model reporting:

- log loss, Brier score, ROC AUC, precision/recall, and balanced accuracy;
- reliability/calibration tables and calibration error;
- performance by asset, market age, liquidity, volatility, and time period;
- feature stability, missingness sensitivity, and ablation results;
- prediction and outcome distributions;
- uncertainty intervals where sample size permits.

Accuracy alone is not an acceptable success metric, particularly while class
imbalance exists. Feature selection, thresholds, and hyperparameters must be
chosen without access to the final holdout period.

For repricing research, edge-development evidence must additionally report
signal count, observed hours, independent sessions, asset and side balance,
target/stop/timeout exits, after-slippage expectancy, max drawdown, fold
stability, and executable-cost stress. A positive paper replay is not an edge
claim unless precommitted repricing evidence gates and prospective validation
requirements are met.

## 9. Validation requirements

Validation must include:

- chronological, purged walk-forward evaluation;
- an untouched final holdout period;
- transaction-cost, spread, slippage, and latency simulation;
- signal dropout and missing-data stress;
- adverse price perturbation and quote staleness stress;
- asset-level and regime-level attribution;
- sensitivity to feature anchor time and entry cutoff;
- comparison with Polymarket's own implied probability;
- prospective shadow testing of a frozen model.

A result is invalid if it depends on shuffled time splits, duplicate windows,
future information, post-resolution values, mock observations in the holdout,
or thresholds selected using final-test performance.

## 10. Risk management requirements

Current mandatory controls:

- no real trading;
- no wallet or private-key handling;
- no order-placement code;
- no authenticated trading client;
- public-data and shadow-mode operation only;
- explicit marking of mock fallback;
- replayable decisions and immutable evidence artifacts.

Requirements for any future execution proposal:

- separate, explicitly authorized execution repository or module boundary;
- independent code and risk review;
- maximum position, market, asset, daily loss, and drawdown limits;
- liquidity and maximum-spread filters;
- stale-data, clock-drift, disconnect, and quote-integrity circuit breakers;
- automatic kill switch and manual shutdown procedure;
- reconciliation, audit logs, and alerting;
- staged capital limits with rollback criteria.

No research result automatically authorizes real-money deployment.

## 11. Definition of proven edge

An edge is proven only when all of the following are true:

1. The dataset passes the quality gates in this document.
2. Labels are authoritative or independently verified.
3. A frozen strategy beats Polymarket probability and naive baselines on an
   untouched public holdout.
4. Net expectancy remains positive after conservative executable costs.
5. Results persist across multiple time windows and at least two assets.
6. Performance is not dominated by one regime, asset, or small group of trades.
7. Calibration and probability scoring improve meaningfully over baselines.
8. Stress tests do not eliminate the edge.
9. Prospective shadow results agree with historical expectations within
   predefined tolerances.
10. The complete experiment can be reproduced from stored data and code.

Until every condition is met, the correct status is either `UNPROVEN_EDGE` or
`NO_EDGE`, never proven alpha.

For the repricing branch, the current status remains `UNPROVEN_EDGE`.
Development evidence is insufficient until the branch reaches at least the
precommitted strong development evidence floor and then survives a separate
prospective or untouched repricing validation period with executable-cost
stress. No repricing result authorizes real-money deployment.

## 12. Definition of production readiness

Production readiness is stricter than proven edge. It requires:

- proven edge as defined above;
- at least 30 consecutive days of stable prospective shadow operation;
- operational monitoring, reconciliation, incident handling, and kill switches;
- bounded risk limits approved independently from strategy development;
- documented infrastructure, security, deployment, rollback, and recovery
  procedures;
- evidence that expected profit materially exceeds operational and tail risk;
- explicit human authorization for a separately scoped execution phase.

The project is not production-ready while it contains only research and shadow
engines.

## 13. Current project status

As of June 23, 2026:

- v1 through v5 engines are implemented;
- public market discovery, external reference capture, quote capture, lifecycle
  tracking, deterministic replay, and shadow evidence reporting work;
- Feature Engine v1 and Dataset Quality Engine v1 are implemented;
- Resolution Engine v1 is implemented with deterministic raw-response replay;
- all 89 automated repository tests pass;
- Campaign Reliability & Diagnostics v1 records monotonic and UTC timing,
  downgrades incomplete temporal coverage, preserves campaign logs, and stores
  endpoint-level discovery failures without discarding partial success;
- Public Evidence Batch Pipeline v1 produces immutable, hashed, fail-closed
  as-of manifests;
- the latest processed evidence contains 1,391 authoritative resolutions from
  1,398 discovered public markets;
- proxy and authoritative labels disagree on 72 of 1,212 comparable markets;
- 275 sparse rows are excluded under the latest deterministic completeness
  rebuild;
- the clean public-only dataset contains 1,064 rows:
  - 353 BTC, 355 ETH, and 356 SOL;
  - 527 UP and 537 DOWN;
- dataset quality score is 99.52/100;
- feature completeness is 99.18%;
- duplicate rows are zero;
- Batch 003 data is usable, but its campaign completeness claim is rejected
  because a 7:08:34 terminal observation gap was not detected by the v1
  monotonic-versus-UTC check;
- Campaign Observation Continuity Gate v1.1 now recomputes acceptance from raw
  checkpoints and correctly classifies Batch 003 `INCOMPLETE_CAMPAIGN`;
- Non-Blocking Capture Cadence Architecture v1 achieves 100% checkpoint
  coverage in accelerated slow-endpoint testing and blocks overnight capture
  when Windows power settings remain unsafe;
- Batch 004 confirmed 100% checkpoint coverage over a real six-hour public
  capture, with a 2.042-second maximum checkpoint gap;
- Batch 005 confirmed a second consecutive 100%-continuity six-hour public
  capture, with a 2.040-second maximum checkpoint gap;
- Batch 006 confirmed a third consecutive 100%-continuity six-hour public
  capture, with a 2.035-second maximum checkpoint gap, and raised the clean
  public dataset beyond the 1,000-row gate;
- all public evidence and Dataset Quality Engine gates now pass;
- Time-Ordered Holdout Protocol v1 is frozen with 741 train rows, 153
  validation rows, 158 sealed holdout rows, and 12 boundary-excluded rows;
- Baseline Probability Model v1 found that fixed logistic regression beats
  class-prior baselines but loses to Polymarket YES price on validation;
- the baseline verdict is `NO_EDGE_FOUND_YET`; the holdout remains sealed and
  final evaluation remains prohibited.
- Baseline Failure Diagnostics v1 concludes `FEATURE_SET_INCOMPLETE`: zero of
  eight fixed feature groups beats YES price on both primary validation
  metrics, and no meaningful asset or regime exception is present.
- Market Microstructure Feature Capture v1 is implemented with 19 optional
  as-of features, schema-versioned session evidence, and deterministic replay;
  a complete 900-second public smoke measured 98.19%-100% field coverage,
  deterministic replay, and deterministic feature export;
- the smoke decision is `READY_FOR_PRODUCTION_CAPTURE` for research evidence
  collection only.

The engineering pipeline is operational, but statistical evidence is
insufficient. No model or alpha claim is currently justified.

## 14. Next milestone

### Wallet Score Fixture Review v1

The next milestone is to review the first bounded structural Wallet Score
fixture before any score expansion, deeper-history weighting, expiry joins, or
copyability modelling. This milestone must not treat the score as
profitability, alpha, ROI, PnL, Sharpe, execution quality, copyability, or
live-trading evidence.

Exit criteria:

- read Wallet Intelligence ingestion, behavior metrics, deep-history
  feasibility, trade-history ingestion design, fixture-ingester, bounded
  public smoke, lifecycle reconstruction fixture outputs, lifecycle review,
  lifecycle metrics outputs, Wallet Metrics Readiness Review v1, and Wallet
  Score Design v1, and Wallet Score Fixture Implementation v1 outputs;
- review `wallet_scores.csv`, `wallet_scores_summary.json`,
  `wallet_score_validation.json`, and `wallet_score_report.md`;
- confirm score bounds, deterministic ordering, forbidden-input exclusion,
  missing metric handling, repeatable export, component bounds, output schema,
  and source provenance remain valid;
- check that score bands are interpreted only as structural research-priority
  labels and not as wallet-quality, profitability, execution, or copyability
  labels;
- recommend exactly one successor task;
- do not launch new public ingestion or add new score inputs, PnL, reference
  alignment, expiry joins, mark-to-market, copyability delay, queue modelling,
  trading ranking, or execution logic;
- keep outputs separate from canonical outcome-prediction datasets,
  repricing datasets, validation data, and sealed holdout data.

No trade copying, wallet/private-key use, live trading, holdout evaluation,
production model training, or automatic capture campaign is authorized.
