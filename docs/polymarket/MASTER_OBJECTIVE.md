# Polymarket Project - Master Objective

Status: Active  
Last updated: June 28, 2026
Authority: Permanent source of truth for the ForgeViewAI Polymarket project

This document defines why the project exists, what constitutes business
success, and which gates must be passed before the system can progress from
research through paper trading to any controlled live deployment. If another
Polymarket document conflicts with this one, this document takes precedence.

## Project guidance hierarchy

Future engineering sessions must read these documents in order:

1. `MASTER_OBJECTIVE.md` - permanent objective and gates.
2. `RESEARCH_PRINCIPLES.md` - strategic hypothesis filter.
3. `PROJECT_STATE.md` - measured current status and blockers.
4. `NEXT_TASK.md` - the single authorized active task.
5. `DECISIONS.md` - durable architecture and policy decisions.
6. `RESEARCH_BACKLOG.md` - future ideas that are not yet active.

After completing work, update the state, decisions, and next-task documents in
the same change. Code is not fully handed off while those documents are stale.

## 1. Mission

Build an automated system capable of generating sustainable profit on
Polymarket five-minute BTC, ETH, and SOL markets.

Sustainable profit means positive net expectancy that persists after realistic
fees, spread, slippage, latency, liquidity constraints, operational costs, and
risk limits. The system must distinguish a genuine edge from random
participation, survivorship bias, public-data delays, incomplete history,
simulation artifacts, data errors, market-regime luck, and overfitting.

## 2. Final business objective

Generate at least **$10,000 in cumulative realized profit** through a
controlled, automated Polymarket system trading BTC, ETH, and SOL five-minute
markets.

This target does not authorize premature capital deployment. Statistical edge,
continuous paper operation, long-duration positive paper performance, and
independent production-readiness approval must precede any controlled live
deployment. The current repository remains research and paper simulation only;
wallet, private-key, authenticated trading, and real-money order-placement
capability require a separately authorized execution phase with explicit risk
controls.

## 3. Supporting disciplines

Research, engineering, AI, data collection, modelling, and infrastructure are
tools for reaching the business objective. They are not independent end goals.
Work in these areas is justified only when it increases expected profitability
or removes a blocker preventing profitable automated trading.

## 4. Research objective

Answer the following question with empirical evidence:

> Does public wallet activity contain timely, incremental information about
> five-minute BTC, ETH, and SOL Polymarket outcomes or probability changes
> after accounting for random baselines, class imbalance, missing data,
> visibility delay, spread, slippage, liquidity, and changing market regimes?

The project must also determine:

- whether selected public wallets make better decisions than random;
- whether their actions become visible quickly enough to observe;
- whether enough time remains after detection to act;
- whether structural wallet filters improve selection;
- whether combined wallet-activity signals can outperform random
  participation over time after realistic delay and transaction costs;
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

## 5. Success metrics

Business success:

- positive net expectancy after executable costs;
- repeatable profitability across assets, sessions, and market regimes;
- controlled drawdown and bounded capital exposure;
- reliable autonomous operation with monitoring, reconciliation, and shutdown
  controls;
- cumulative realized profit of at least $10,000 after controlled live
  deployment is explicitly authorized.

Research success:

- each sprint tests one named hypothesis from `RESEARCH_PRINCIPLES.md`;
- each sprint ends with `supported`, `rejected`, or
  `inconclusive_with_next_blocker`;
- negative evidence is preserved as a successful research outcome when it
  eliminates a weak hypothesis;
- every engineering task states its expected information gain before it is
  authorized;
- descriptive Wallet Intelligence work advances only when it supports a
  wallet-skill, visibility-delay, actionable-time, structural-filter, or
  combined-strategy hypothesis.

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

## 6. Measurable project stages

| Stage | Completion gate | Current status |
|---|---|---|
| 1. Statistical edge demonstrated | A frozen strategy shows positive net expectancy after conservative executable costs across precommitted out-of-sample, stress, and prospective validation gates | In progress |
| 2. Continuous paper-trading MVP | The frozen strategy runs continuously with durable state, restart recovery, monitoring, reconciliation, and no duplicate or missed transitions | In progress |
| 3. Long-duration positive paper performance | At least 30 consecutive days of stable prospective paper operation remain profitable within predefined drawdown and reliability limits | Not started |
| 4. Controlled live deployment, if justified | Independent technical and risk approval authorizes bounded capital, hard loss limits, circuit breakers, reconciliation, and rollback | Not started |
| 5. $10,000 cumulative profit target | Controlled live operation records at least $10,000 in cumulative realized profit after all costs | Not started |

Stages may not be skipped. Passing a stage permits evaluation of the next
stage; it does not guarantee that the next stage is safe or economically
justified.

### Technical development history

| Technical stage | Purpose | Status |
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

These technical stages preserve project history and support the measurable
business stages above. Completing a technical stage is not itself business
success.

## 7. Architecture map

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

## 8. Data quality requirements

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

## 9. Model quality requirements

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

## 10. Validation requirements

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

## 11. Risk management requirements

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

## 12. Definition of proven edge

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

## 13. Definition of production readiness

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

## 14. Current project status

As of June 26, 2026:

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

The research tooling is operational, but the project is now governed by the
profit-first business objective. No future sprint should exist merely to add
metrics, joins, or reports. Each sprint must increase expected profitability
or remove a blocker preventing profitable automated trading. No model,
strategy, alpha, or profitability claim is currently justified.

## 15. Next milestone

### Wallet Detection-To-Expiry Feasibility Sprint v1

Wallet Activity Visibility Delay Sprint v1 tested H2 over 3,431 fast-crypto
trade rows from 20 H1-classified wallets. Trade occurrence and retrospective
fetch timestamps were complete, but publication or first-seen timestamps were
absent for every row. H2 is therefore `INCONCLUSIVE`: retrieval age cannot be
substituted for public API latency.

Wallet First-Seen Detection Sprint v1 then ran a bounded five-minute
prospective experiment over the four frozen H1 wallets. It detected six live
crypto Up/Down trades, including two target five-minute trades with
polling-quantized first-seen upper bounds of 15.894 and 16.041 seconds. This
establishes that H2 is technically measurable prospectively, but the two-row
target sample cannot support or reject H2.

Wallet First-Seen Prospective Experiment v1 now provides the restart-safe
observation system required for future H2 evidence: transactional SQLite poll
payloads, immutable first-seen trades, persisted run bounds, restart recovery,
duplicate protection, and deterministic export. The sprint did not run a new
public observation window and did not evaluate H2.

The next Wallet Intelligence milestone remains a direct H3 test after a
future bounded H2 evidence collection:

> Enough time remains after public detection to act.

It must use the committed prospective first-seen evidence and public expiry
metadata to determine whether detection-to-expiry is technically measurable.
The initial two target rows are a feasibility sample only.

Wallet Decision Window Sprint v1 joined those two rows to Gamma-verified
expiry metadata. Their first-seen-to-expiry windows were 85.106 and 44.959
seconds: one met the frozen 60-second sufficient threshold and one was
marginal. No row had 120 seconds remaining. H3 is `INCONCLUSIVE` because the
sample contains only two trades from one wallet and excludes execution,
liquidity, fill, and queue latency. The next Wallet Intelligence milestone is
therefore bounded prospective evidence accumulation to at least 30 eligible
target trades, not a scoring or execution expansion.

Wallet H2/H3 Decision Framework Sprint v1 supersedes that provisional
30-trade target with a confidence-based gate. A final H2/H3 decision now
requires 100 eligible trades, at least 3 wallets, 10 sessions, 5 UTC dates,
2 assets, and 95% timestamp/expiry completeness. Two-sided 95% Wilson
intervals govern support and rejection. Collection has a hard cap of 60 total
five-minute sessions; failure to satisfy minimum evidence within that budget
freezes the wallet-copy branch for insufficient observable opportunity
density. Both H2 and H3 must be supported before any execution-feasibility
engineering may begin.

Wallet Autonomous Evidence Accumulator v1 now automates that frozen decision
contract without changing it. A local transactional session ledger wraps the
existing restart-safe observer, assigns session numbers, accumulates the two
committed seed rows plus new public observations, caches condition-matched
Gamma expiries, evaluates H2/H3 after every completed session, and stops on
support, rejection, or session 60. `status` is read-only, `run` operates to a
terminal gate, and `start` launches the same bounded loop detached. The
automation is implemented and fixture-validated but has not been publicly
launched; current evidence remains two trades and one session.

Exit criteria:

- restrict prospective observation to the four H1 above-baseline wallets;
- remain public, read-only, bounded, and research-only;
- record trade timestamp, local first-seen timestamp, fetch completion
  timestamp, market expiry, and stable trade identity;
- measure first-seen-to-expiry only for prospectively observed rows;
- report the share of candidate actions visible with at least 60, 120, and
  180 seconds remaining;
- report whether H3 is `SUPPORTED`, `REJECTED`, or `INCONCLUSIVE`;
- do not change Wallet Score, tune thresholds, rank wallets for trading,
  compute ROI, Sharpe, market advantage, mark-to-market values, or execution
  quality;
- keep outputs separate from canonical outcome-prediction datasets,
  repricing datasets, validation data, and sealed holdout data.

No trade copying, wallet/private-key use, live trading, holdout evaluation,
production model training, or broad scraping is authorized.
