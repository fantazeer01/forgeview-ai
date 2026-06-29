# Polymarket Architectural Decisions

Last updated: June 29, 2026

This append-only log records durable project choices and their rationale.
Future sessions should add a decision when work changes architecture, data
semantics, validation policy, safety boundaries, or milestone gates. Existing
decisions should be superseded explicitly rather than silently rewritten.

## D-001: Research and execution remain separated

Status: Accepted  
Decision: This repository contains research, simulation, capture, replay, and
shadow validation only. It contains no wallet, private-key, authenticated
trading client, or order-placement code.

Reason: Research results must not accidentally authorize capital deployment.
Any future execution system requires a separately scoped approval and risk
review.

## D-002: Product-area isolation is mandatory

Status: Accepted  
Decision: Polymarket code, docs, tests, data, and runs remain under the approved
Polymarket paths and do not import or modify Content Machine.

Reason: Independent ownership and failure domains prevent unrelated product
changes from contaminating research evidence.

## D-003: Raw sessions are replayable evidence

Status: Accepted  
Decision: Capture systems store timestamped raw events, and replay recomputes
decisions instead of trusting generated reports.

Reason: Reproducibility and forensic inspection are prerequisites for any edge
claim.

## D-004: Public and mock data are explicitly distinguished

Status: Accepted  
Decision: Every dataset row carries `market_source`; public and mock data are
never silently mixed. Model validation must use public-only holdouts.

Reason: Mock behavior can validate software but cannot prove market alpha.

## D-005: Feature rows are anchored before resolution

Status: Accepted  
Decision: Feature Engine v1 anchors rows at the first saved snapshot at or
after 60 seconds from market open.

Reason: This leaves a forward prediction horizon and reduces accidental
end-of-window label leakage.

## D-006: Dataset quality gates precede modelling

Status: Accepted  
Decision: Probability model development is blocked until the dataset reaches
the public-sample, completeness, class-balance, duplicate, label-integrity, and
quality-score gates in `MASTER_OBJECTIVE.md`.

Reason: Modelling a weak dataset creates convincing overfit faster than it
creates evidence.

## D-007: Current proxy labels are not authoritative

Status: Accepted  
Decision: `reference_window_return` labels are permitted for pipeline
engineering and must retain explicit provenance. They are insufficient for a
proven-edge or production-readiness claim.

Reason: The external reference direction may differ from Polymarket's formal
resolution source or rules.

## D-008: Quality scoring includes hard gates

Status: Accepted  
Decision: Dataset Quality Engine uses a weighted 0-100 score plus independent
hard gates for public ratio, minority class, feature completeness, duplicate
rate, and total score.

Reason: An average score must not hide a fatal weakness such as no public data
or a missing outcome class.

## D-009: Time-ordered validation is required

Status: Accepted  
Decision: Future model evaluation uses chronological purged walk-forward
testing and an untouched final holdout. Random shuffled splits are invalid.

Reason: Adjacent five-minute windows and market regimes create temporal
dependence and leakage risk.

## D-010: Project management has one active task

Status: Accepted  
Decision: `NEXT_TASK.md` contains exactly one active task. Future ideas remain
in `RESEARCH_BACKLOG.md`.

Reason: A single explicit priority makes autonomous sessions predictable and
prevents roadmap ideas from becoming uncoordinated implementation work.

## D-011: Authoritative outcomes require strict terminal settlement

Status: Accepted  
Decision: Resolution Engine accepts a label only when the saved condition ID
matches exactly, the market is closed and resolved, outcomes are exactly
`Up`/`Down`, and terminal outcome prices are 1/0 within 0.001. Ambiguous,
unresolved, cancelled, malformed, and missing markets remain unlabelled.

Reason: Market closure or a near-terminal quote alone is not sufficient
evidence of Polymarket's formal outcome.

## D-012: Raw resolution responses are evidence and replay input

Status: Accepted  
Decision: Public Gamma event responses are saved before normalization.
Resolution replay uses those saved responses and original retrieval timestamps,
not the current API.

Reason: Outcome parsing must remain reproducible if Gamma data changes or
becomes unavailable.

## D-013: Proxy labels are opt-in and reconciled independently

Status: Accepted  
Decision: Feature Engine defaults to authoritative labels only. External
reference-return labels require `--allow-proxy-labels`. Reconciliation rebuilds
a dedicated proxy-only dataset so it cannot accidentally compare authoritative
labels against themselves.

Reason: The initial public sample showed 9 proxy disagreements among 75
comparable markets. Silent proxy fallback would corrupt label provenance.

## D-014: First-seen market evidence defines legacy detection delay

Status: Accepted  
Decision: When explicit lifecycle tracking is absent, Feature Engine derives
`detection_delay` from the earliest saved `market_lifecycle` timestamp minus
window start, floored at zero for markets discovered before opening.

Reason: The value is recoverable from immutable evidence and does not require
imputation or future information.

## D-015: As-of feature values have a maximum age

Status: Accepted  
Decision: Return and probability-change lookbacks use only observations at or
before the requested timestamp and reject observations more than 15 seconds
old. Future observations are never eligible.

Reason: Unlimited last-observation carry-forward hides data gaps and creates
misleading short-horizon features.

## D-016: Sparse rows are excluded instead of filled

Status: Accepted  
Decision: A training row may retain at most two unavailable modelling
features. Rows with more missing features are excluded and listed in
`missingness_diagnostics.json`. No zero, mean, future, or synthetic fill is
used.

Reason: The 29 excluded windows began too late or contained polling gaps that
made the required history irrecoverable. Exclusion preserves feature semantics
and raises clean-dataset completeness to 98.71%.

## D-017: Evidence batches are immutable as-of snapshots

Status: Accepted  
Decision: A resumed batch copies and hashes sessions whose final saved event is
no later than the selected source session's completion timestamp. Later or
still-active captures are excluded.

Reason: Global run directories can change while capture continues. An explicit
cutoff is required for deterministic reports and comparable batch deltas.

## D-018: Batch stages are fail-closed and single-writer

Status: Accepted  
Decision: Resolution, feature, and quality stages execute in order under an
exclusive repository-local lock. A failed stage stops the pipeline, records the
failure, and cannot reuse a stale downstream artifact as a new result.

Reason: Canonical resolution and training artifacts are shared outputs.
Concurrent or partial writers would invalidate lineage.

## D-019: Master sample gates override component recommendations

Status: Accepted  
Decision: The evidence batch verdict remains
`INSUFFICIENT_PUBLIC_SAMPLE` until at least 1,000 clean public rows and 200 rows
per asset exist, even if Dataset Quality Engine recommends training.

Reason: Completeness and class balance do not compensate for inadequate sample
size or an unusable holdout.

## D-020: Batch refresh maps to resolution reconciliation

Status: Accepted  
Decision: Evidence Batch `resolution_mode=refresh` invokes Resolution Engine's
public `reconcile` command; `resolution_mode=replay` invokes its saved-fixture
`replay` command.

Reason: The batch vocabulary describes workflow intent, while Resolution
Engine retains its existing command names. An explicit adapter and regression
test prevent refresh requests from failing at the CLI boundary.

## D-021: Campaign completeness is an independent evidence gate

Status: Accepted  
Decision: Public capture duration is measured with a monotonic clock and
reported alongside actual UTC start, actual UTC completion, and observed UTC
span. A campaign with more than the greater of five seconds or one percent
temporal shortfall is marked `incomplete_temporal_coverage`. Post-processing
may continue for forensic and dataset recovery, but its evidence-batch verdict
is `INCOMPLETE_CAMPAIGN` and it cannot authorize training. Wall-clock
discontinuities and every discovery endpoint failure are immutable session
events. Individual discovery request failures do not discard successful
responses from other endpoints.

Reason: A terminal marker alone cannot prove that the requested market period
was observed. Separating campaign integrity from strategy metrics prevents
clock changes and transport failures from silently overstating evidence while
retaining valid partial observations.

## D-022: Raw checkpoint continuity overrides endpoint duration

Status: Accepted  
Decision: Campaign acceptance is recomputed from immutable
`capture_checkpoint` events. A complete campaign requires at least 99%
temporal coverage, at least 95% of the configured checkpoint count, no
checkpoint or terminal boundary gap over 300 seconds, a terminal
`session_completed` event, and zero fatal capture errors. Failure produces
`INCOMPLETE_CAMPAIGN`, preserves usable rows, and blocks training
authorization. Embedded legacy completeness metadata cannot override this
calculation.

Reason: Host sleep can advance UTC and monotonic clocks together while no
observations are collected. Endpoint duration therefore cannot establish
continuous evidence coverage; only the saved checkpoint stream can.

## D-023: Heartbeat cadence is isolated from network I/O

Status: Accepted  
Decision: Public capture uses fixed monotonic deadlines for checkpoint
heartbeats. Discovery, reference, and quote requests execute in bounded
background workers; discovery uses a cached market set and quote results are
cached per market. Gamma and reference requests are parallelized internally.
Network completion may affect data availability metrics, but it may not block
checkpoint creation.

Reason: Batch 003 proved that serialized HTTP requests made a two-second
heartbeat physically impossible even while the host was awake. Evidence
continuity and data-source availability must be measured independently.

## D-024: Overnight campaigns require safe Windows power state

Status: Accepted  
Decision: Evidence Batch `run` fails before capture when AC sleep or hibernate
timeouts are enabled or cannot be inspected. During an accepted run, the
process also holds a Windows `ES_SYSTEM_REQUIRED` execution-state request.
Operators must pass the repository preflight and keep the machine on AC power;
lid-close policy must not suspend the host.

Reason: Windows sleep caused a verified 25,687-second evidence gap in Batch
003. Application-level inhibition plus fail-closed configuration inspection
provides defense in depth.

## D-025: Five-minute windows are atomic and the final holdout is sealed

Status: Accepted  
Decision: Validation Protocol v1 assigns complete `window_start` groups, not
individual asset rows, to chronological train, validation, or final holdout
sets. The split targets are 70% / 15% / 15% by window group. One complete
five-minute group before each boundary is purged and one group after it is
embargoed. Holdout features and labels are stored separately; development
loaders expose train and validation labels only. The holdout label file is
committed by SHA-256 and may be opened once after the candidate, preprocessing,
thresholds, and stress assumptions are frozen.

Reason: BTC, ETH, and SOL rows from the same market interval share time and
external conditions. Splitting them independently or allowing adjacent
boundary windows would leak regime information. Separating and committing
holdout labels prevents accidental model selection against the final test.

## D-026: Primary probability metrics and advancement rules are precommitted

Status: Accepted  
Decision: Log loss and Brier score are the primary metrics. The mandatory
baselines are training-frequency probability, Polymarket YES probability,
existing deterministic lag score, and interpretable logistic regression. A
candidate advances from validation only under the rules frozen in
`TIME_ORDERED_HOLDOUT_PROTOCOL_V1.md`; final holdout success requires at least
1% improvement over Polymarket on both primary metrics plus cross-asset and
cost-stress controls. Holdout reuse is prohibited.

Reason: Defining metrics and thresholds before fitting or reading holdout
outcomes prevents post-hoc metric selection and optimistic alpha claims.

## D-027: Baseline v1 is a fixed dependency-free linear evaluation

Status: Accepted  
Decision: Baseline Probability Model v1 evaluates exactly four predictors:
constant prior, asset prior, Polymarket YES price, and one fixed-feature
L2-regularized logistic regression. Missing-value medians and scaling are
learned from train only. No hyperparameter search, shallow tree, P&L
optimization, or validation-driven feature selection is performed.

Reason: A single interpretable specification provides an honest first test
with minimal researcher degrees of freedom. Baseline v1 failed to beat
Polymarket YES price on validation, so the holdout remains sealed and the
negative result is preserved rather than tuned away.

## D-028: Current snapshot features are insufficient; next work targets microstructure

Status: Accepted  
Decision: Baseline Failure Diagnostics v1 concludes
`FEATURE_SET_INCOMPLETE`. None of the eight predeclared feature groups beats
Polymarket YES price on both validation log loss and Brier score. The project
will not open the holdout or search larger models. Exactly one follow-up signal
family is authorized for engineering: market microstructure features covering
depth, quote age, order-flow proxy, repricing velocity, probability
acceleration, and synchronized cross-asset lead/lag.

Reason: Current features beat class priors but are dominated by YES price
across all three assets and every meaningful validation regime. They also
contain exact redundancy and material train/validation drift. New information,
not model complexity, is the defensible next hypothesis.

## D-029: Microstructure evidence is additive, versioned, and optional

Status: Accepted  
Decision: Every successful new public quote retains the legacy
`polymarket_snapshot` event and adds a schema-v1 `microstructure_snapshot`.
Raw CLOB timestamps, sizes, and depth are preserved; derived values are
strictly as-of. Missing fields remain null. Microstructure columns are optional
for legacy Feature Engine rows and have a separate coverage report, so they do
not retroactively fail historical core-feature quality gates or alter the
frozen validation protocol.

Reason: Additive events preserve replay compatibility and evidence lineage.
Separating core completeness from new-feature coverage prevents unavailable
historical data from being silently imputed or from invalidating prior
research.

## D-030: Public microstructure schema v1 is ready for research capture

Status: Accepted  
Decision: The bounded 900-second public smoke is classified
`READY_FOR_PRODUCTION_CAPTURE`, meaning production-quality research capture,
not live trading. A longer independent development campaign may be authorized
separately because raw quote timestamp, latency, top size, total depth, and
book imbalance each achieved 100% population; warm-up-dependent velocity and
acceleration exceeded 98%; checkpoint coverage was 100%; replay and disposable
Feature Engine exports were deterministic.

Reason: The public CLOB supplies the schema reliably across BTC, ETH, and SOL.
The smoke establishes capture fitness only. It provides no predictive-edge,
holdout, P&L, or production-trading evidence.

## D-031: Batch 001 microstructure diagnostics do not advance a candidate

Status: Accepted  
Decision: Independent Microstructure Development Dataset Batch 001 is
classified `DATASET_TOO_SMALL_OR_UNSTABLE` for signal-development purposes.
The 213-row proxy-labelled development dataset has complete microstructure
feature coverage, but the fixed chronological diagnostic evaluation contains
only 64 rows, YES price remains the best diagnostic predictor, and neither the
microstructure-only nor YES-plus-microstructure diagnostic model beats YES
price on both primary development metrics. The project will not open the
sealed holdout, modify the frozen validation protocol, or merge Batch 001 into
canonical training data on this evidence.

Reason: Batch 001 is valuable operational and feature-lineage evidence, but
it is too small and temporally narrow to distinguish weak incremental
microstructure signal from sample noise. Additional independent development
evidence is required before any candidate specification can be frozen.

## D-032: Async discovery exceptions are nonfatal structured diagnostics

Status: Accepted  
Decision: Public capture treats asynchronous market-discovery worker
exceptions as structured `discovery_failure` diagnostics instead of fatal
capture errors. The async wrapper normalizes raw worker exceptions to the same
timestamp, endpoint, exception type, and message shape already emitted by the
underlying discovery feed.

Reason: A Batch 002 capture attempt encountered a raw `IncompleteRead`
exception from the async discovery worker. The exception carried no
`DiscoveryFailure` fields and crashed the campaign before completion. Network
transport failures should remain observable evidence, but they must not stop
checkpoint cadence or invalidate otherwise recoverable public capture.

## D-033: Combined Batch 001-002 microstructure diagnostics do not advance a candidate

Status: Accepted  
Decision: Combined development-only diagnostics over Independent
Microstructure Development Dataset Batches 001 and 002 are classified
`DATASET_STILL_TOO_SMALL_OR_UNSTABLE`. The combined 426-row proxy-labelled
dataset has complete microstructure feature coverage, but YES price remains
the best diagnostic predictor overall and independently for BTC, ETH, and SOL.
No microstructure feature is both incrementally useful beyond YES price and
stable across both batches under the fixed diagnostic rules.

Reason: The YES-plus-microstructure diagnostic model loses to YES price on
both primary development metrics, and apparent feature effects are batch
dependent. This evidence is useful for data engineering and hypothesis
generation, but it does not justify opening the sealed holdout, modifying the
validation protocol, merging microstructure rows into canonical training data,
or freezing a candidate specification.

## D-034: Repricing research is separate from outcome prediction

Status: Accepted  
Decision: Polymarket Repricing Research v1 is implemented as a separate
development-only module under `polymarket/repricing_research/`. It studies
whether external BTC, ETH, and SOL moves predict favorable YES/NO contract
repricing over the next 30-180 seconds. It does not predict final UP/DOWN
outcomes, does not write to canonical training/validation/holdout paths, and
does not modify the frozen validation protocol.

Reason: The current outcome-prediction path has not beaten Polymarket YES
price. Observed strategy descriptions and profitable-wallet behavior appear
closer to short-term probability repricing than final settlement prediction.
Separating the repricing module preserves the negative outcome-prediction
result while allowing a distinct hypothesis to be tested without contaminating
sealed holdout evidence or canonical outcome datasets.

## D-035: Repricing simulation remains paper-only

Status: Accepted  
Decision: Repricing Research v1 includes only deterministic labels and a
shadow strategy simulator. It may simulate entries, repricing-target exits,
timeout exits, stop-loss exits, conservative slippage, drawdown, and
expectancy. It must not implement real orders, wallet access, private keys,
authenticated clients, position sizing for deployment, or production model
training.

Reason: Short-horizon repricing research can create more execution-like
metrics than final outcome prediction. Keeping the implementation paper-only
maintains the repository's research boundary and prevents a promising
development smoke result from being mistaken for trading authorization.

## D-036: Repricing evidence gates precede model development and edge claims

Status: Accepted  
Decision: Repricing Research v1 Data Sufficiency Audit classifies the current
28-signal short replay as `INSUFFICIENT_SMOKE_ONLY`. Current data may support
diagnostics and label engineering only. It does not authorize model
development, shadow strategy validation, holdout evaluation, production
training, or any repricing edge claim. Repricing weak evidence requires at
least 100 signals, 40 observed hours, 3 independent sessions, 25 signals per
asset, 35 signals per side, and after-slippage expectancy of at least 0.005.
Moderate evidence requires 300 signals, 120 hours, 6 sessions, 75 signals per
asset, 100 per side, and expectancy at least 0.008. Strong development
evidence requires 1,000 signals, 400 hours, 20 sessions, 250 signals per
asset, 350 per side, expectancy at least 0.010 after stress, stable
chronological folds, and no single asset or session contributing more than
40% of P&L.

Reason: The current aggregate repricing smoke result is positive after the
simple slippage haircut, but it is based on only 28 signals, 13.1255 observed
hours, 5 BTC / 8 ETH / 15 SOL signals, and 5 YES / 23 NO signals. The result
is unstable across side and asset: NO-side expectancy is negative and ETH
expectancy is negative. Precommitted gates prevent a small favorable smoke
sample from becoming an implicit strategy claim.

## D-037: Repricing collection must be threshold-gated before new capture

Status: Accepted  
Decision: Repricing-Focused Public Evidence Collection Plan v1 is accepted as
a planning-only roadmap. The current strict replay rate is 2.1333 signals/hour
over 28 signals, but YES-side scarcity is the binding balance constraint. At
current rates, count-only evidence floors would require about 4 / 12 / 40
independent 12-hour sessions for weak / moderate / strong signal counts, while
balance-adjusted gates require about 8 / 22 / 77 sessions. Before launching any
new repricing-focused public campaign, the project must run a no-capture
threshold sensitivity audit on existing public sessions and freeze any future
collection stratum based on signal density, asset balance, side balance, and
horizon coverage, not on maximizing historical paper P&L.

Reason: The strongest current bottleneck is not capture infrastructure but
candidate admission. Existing lag measurements show most observations are
filtered as external move below threshold, already repriced, or near expiry,
with only 87 confidence-below-threshold lag events compressed to 28
non-overlapping paper entries. Running a threshold audit first is faster and
safer than spending new public capture time under thresholds that may remain
too sparse or too imbalanced.

## D-038: Balanced repricing stratum is selected for collection preflight

Status: Accepted  
Decision: Repricing Threshold Sensitivity Audit v1 selects the `balanced`
stratum as the recommended frozen collection stratum for future public
repricing evidence, subject to explicit preflight and collection authorization.
The balanced stratum uses external move threshold 6 bps, repricing ratio 0.65,
minimum confidence 0.45, minimum dataset expiry 60 seconds, 180-second maximum
hold, and accepted reasons `qualified_external_move_not_repriced` plus
`confidence_below_threshold`. The selection criterion is statistical evidence
collection quality: signal density, BTC/ETH/SOL balance, YES/NO balance, and
horizon coverage. Paper P&L is not an optimization target.

Reason: The persisted current smoke dataset has 28 signals at 2.1333
signals/hour and remains too small and imbalanced. The audit found
`external_move_below_threshold` is the dominant detector-level removal filter,
with 36,465 of 64,130 recomputed candidate observations. Requiring full
180-second horizon coverage removes every current signal, while among
entry-admission thresholds the external move threshold has the largest
signal-density effect. The balanced stratum improves estimated density to
3.9184 outcome-free overlap-adjusted signals/hour while keeping a cleaner
no-already-repriced interpretation than the aggressive stratum. This is not an
edge claim, does not change evidence gates, and does not authorize live
trading or holdout evaluation.

## D-039: Balanced repricing campaign preflight is operationally ready

Status: Accepted  
Decision: Balanced Repricing Evidence Collection Preflight v1 classifies the
future 12-hour public-only balanced repricing campaign as
`READY_FOR_AUTHORIZED_LAUNCH` from an operational preflight perspective. The
planned run uses BTC, ETH, and SOL; duration 43,200 seconds; poll interval 2
seconds; discovery interval 5 seconds; no mock fallback; external move
threshold 6 bps; repricing ratio 0.65; minimum confidence 0.45; minimum
dataset expiry 60 seconds; and 180-second max holding window. Future artifacts
must remain separated under `polymarket/runs/repricing_balanced_v1/`,
`polymarket/models/repricing_research_v1/balanced_collection_batch_001/`, and
`polymarket/data/repricing_research_balanced_batch_001/`. The preflight did
not launch the campaign.

Reason: The preflight verified CLI/config support, disabled Windows AC sleep
and hibernate, no competing `python -m polymarket.edge_engine_v5 capture`
process, no stale lock, enough disk space, and separated output paths. The
single-session expectation is approximately 21,600 checkpoints, 47.02 signals,
and 205 MB of artifacts. Operational readiness does not imply a repricing edge
claim, does not change evidence gates, and does not authorize live trading,
wallet/private-key use, production training, or sealed holdout evaluation.

## D-040: Balanced repricing Batch 001 is positive but below weak evidence

Status: Accepted  
Decision: Balanced Repricing Evidence Collection Batch 001 is accepted as a
complete continuous public-only balanced-stratum evidence session, but it does
not satisfy weak development evidence. The batch produced 130 deterministic
repricing signals with BTC / ETH / SOL counts of 37 / 29 / 64 and YES / NO
counts of 59 / 71. It achieved 58.46% target-before-stop win rate, +0.012331
after-slippage expectancy per signal, +1.603 simulated P&L after conservative
slippage, and 0.875 max drawdown. However, weak evidence still requires at
least 40 observed hours and at least 3 independent sessions; this batch is one
12-hour session.

Reason: The signal, asset, side, expectancy, and drawdown gates passed for the
single batch, and deterministic replay/export passed. Treating it as weak
evidence would violate the precommitted hours and independent-session gates.
No holdout evaluation, production model training, live trading, wallet access,
or balanced-stratum change is authorized by this result.

## D-040: Wallet intelligence is descriptive research only

Status: Accepted
Decision: Wallet Intelligence Research v1 is a separate research-only branch
under `polymarket/wallet_intelligence/`, documented in
`docs/polymarket/WALLET_INTELLIGENCE_RESEARCH_V1.md`. It studies public
Polymarket wallet/profile behavior for repeatable timing, sizing,
market-selection, side-selection, holding-period, and drawdown patterns in
fast BTC/ETH/SOL Up or Down markets. It must not inspect sealed holdout
outcomes, run holdout evaluation, implement live trading, connect wallets or
private keys, copy trades automatically, launch capture campaigns, train
production models, or write to canonical outcome-prediction or repricing
validation paths.

Reason: Public wallet behavior may generate useful hypotheses about whether
successful participants trade repricing, final resolution, cheap outcomes,
late entries, or repeatable sizing rules. Those observations are not evidence
of a ForgeViewAI edge by themselves. Keeping the branch descriptive and
separate prevents survivorship bias, copy-trading temptation, and accidental
contamination of the sealed validation and holdout workflow.

## D-041: Open-source intelligence is reference material, not dependency adoption

Status: Accepted
Decision: Polymarket Open Source Intelligence Audit v1 is accepted as a
read-only research input under
`polymarket/models/open_source_intelligence_audit_v1/`. The audit may inform
future Wallet Intelligence, Repricing Research, API normalization, and
execution-realism tasks. It does not approve importing third-party code,
installing global dependencies, connecting wallets, using private keys,
running live trading bots, launching campaigns, training production models, or
modifying the frozen validation/holdout protocol.

Reason: Several inspected repositories contain useful research ideas but also
execution-heavy code paths, private-key configuration, live order placement,
copy-trading, market-making, or hosted trading surfaces. Treating them as
reference material preserves ForgeView's research-only boundary while allowing
safe reuse of concepts such as wallet snapshots, replication scoring, L2
execution-realism assumptions, read-only API normalization, depth guards, and
dry-run gates.

## D-042: Wallet ingestion uses bounded public snapshots only

Status: Accepted
Decision: Wallet Intelligence Data Ingestion v1 uses read-only public
Polymarket profile/data endpoints and bounded first-page snapshots for the
seed watched-wallet list. Normalized outputs live under
`polymarket/data/wallet_intelligence/v1/` and remain separated from canonical
outcome-prediction, repricing validation, holdout, live-run, and execution
paths. Unavailable fields such as complete trade/fill history, linked
entry/exit timestamps, average holding time, drawdown, Binance-lag timing, and
observation-delay risk must be recorded explicitly rather than inferred.

Reason: Public profile snapshots are useful for market-type, side, sizing,
cheap-entry, and resolved-price evidence, but they are not sufficient to prove
late-entry behavior, hold-to-expiry behavior, copyability, or executable
repricing edge. Keeping ingestion bounded prevents accidental scraping,
survivorship-biased copy-trading claims, and contamination of validation or
holdout workflows.

## D-043: Wallet behavior metrics are descriptive and non-executable

Status: Accepted
Decision: Wallet Intelligence Behavior Metrics v1 may classify seed wallets,
compute market exposure, side distribution, entry-price buckets, sizing
concentration, similarity, clusters, and copyability risk from existing
ingested public snapshots only. It must not treat any metric as a trade signal
or copy-trading instruction. Copyability scores remain capped and conservative
while complete trade/fill history, observation delay, liquidity consumption,
linked entry/exit timing, drawdown, and Binance-lag alignment are unavailable.

Reason: The behavior metrics found repeatable fast-market patterns, but the
same public snapshots are incomplete on the variables that determine whether
the behavior could be observed and replicated. Descriptive clustering is useful
for hypothesis triage; it is not evidence of executable edge or authorization
for trading automation.

## D-044: Public wallet trade history is feasible only as bounded research

Status: Accepted
Decision: Wallet Intelligence Deep History Feasibility v1 establishes that
public Polymarket Data API activity/trade endpoints can support bounded,
read-only wallet-history research. Future work may design a cached ingestion
path around public `activity?user=<wallet>&type=TRADE` rows, cross-checked
with public `/trades`, `/positions`, `/closed-positions`, CLOB
`/prices-history`, and external BTC/ETH/SOL reference prices. This does not
authorize live trading, automatic trade copying, wallet/private-key use,
orders, broad scraping, market capture campaigns, production model training,
sealed holdout inspection, or holdout evaluation.

Reason: A one-wallet, 50-row read-only probe for
`0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a` returned public trade rows with
timestamps, transaction hashes, token IDs, condition IDs, sides, prices, sizes,
outcomes, slugs, and event slugs. These fields can support linked entry/exit
and time-to-expiry research after careful joins, but they still do not expose
private intent, queue position, fill priority, guaranteed maker/taker
completeness, full copyability, or Binance-lag conclusions from wallet
endpoints alone.

## D-045: Wallet trade-history ingestion must be schema-first and bounded

Status: Accepted
Decision: Wallet Public Trade History Ingestion Design v1 defines the only
authorized path for future wallet trade-history implementation. The first
future implementation must use the 35-field normalized schema, raw JSONL page
storage, source-fetch manifests, raw row/page SHA-256 hashes, deterministic
CSV/optional Parquet rebuilds, explicit dedupe keys, and validation gates
defined under
`polymarket/models/wallet_intelligence_v1/trade_history_ingestion_design/`.
The first collection scope remains seed-wallet only, with 100 rows per page,
at most three primary activity pages per wallet, at most one `/trades`
cross-check page per wallet, at most 1,800 primary activity rows total, and at
most 600 cross-check rows total. The next implementation task is limited to
fixtures and mocked tests before any bounded public fetch is authorized.

Reason: Public activity/trade rows can support useful lifecycle research only
if provenance, deduplication, endpoint completeness, and unavailable fields
are preserved from the start. Free-form fetching would quickly become hard to
reproduce and could drift toward copy-trading or aggressive scraping. A
schema-first, cache-first, fixture-tested design keeps wallet intelligence
descriptive and separated from live execution, repricing validation,
canonical outcome modelling, and the sealed holdout.

## D-046: Wallet trade-history fixture ingester is non-executable

Status: Accepted
Decision: Wallet Public Trade History Ingester Fixture Implementation v1
implements schema constants, deterministic normalization, raw payload/page
hashing, dedupe-key generation, timestamp parsing, market classification,
bounded-limit checks, fixture exports, validation gates, and the
`python -m polymarket.wallet_intelligence trade-history-fixture` CLI command
for saved fixtures only. This implementation is accepted as a local
normalization scaffold. It does not authorize network-enabled wallet-history
collection, live trading, automatic trade copying, wallet/private-key use,
order placement, market capture campaigns, production model training, sealed
holdout inspection, or holdout evaluation.

Reason: The fixture run normalized 50 saved public `TRADE` rows from the
prior bounded probe, preserved 35-field provenance, removed zero duplicates,
passed all ten validation gates, and produced deterministic CSV repeat
exports. Keeping the first implementation fixture-only proves the schema and
quality gates before any separately authorized bounded public smoke touches
public endpoints again.

## D-047: Wallet public trade-history smoke is bounded descriptive evidence

Status: Accepted
Decision: Wallet Public Trade History Bounded Public Smoke v1 is accepted as a
small public read-only data availability smoke under
`polymarket/data/wallet_intelligence/trade_history_smoke_v1/`. It fetched at
most one public `activity?type=TRADE` page for each of the six seed wallets,
normalized 600 rows into the 35-field schema, preserved raw JSONL provenance,
passed all ten validation gates, and verified deterministic CSV repeat export.
The smoke output may inform a future lifecycle reconstruction design task, but
it does not authorize broad wallet-history ingestion, automatic trade copying,
live trading, wallet/private-key use, order placement, market capture
campaigns, production model training, sealed holdout inspection, or holdout
evaluation.

Reason: The smoke proved that the fixture ingester can operate against
bounded public endpoint responses across all seed wallets while staying inside
the design caps. It also exposed the next data-engineering need: lifecycle
reconstruction must be designed before interpreting entries, exits, holding
time, copyability delay, queue/fill uncertainty, or Binance-lag alignment.

## D-048: Wallet lifecycle reconstruction remains bounded and descriptive

Status: Accepted
Decision: Wallet Trade Lifecycle Reconstruction Fixture Prototype v1 is
accepted as a small deterministic reconstruction layer over existing
normalized public smoke trade history only. It may group rows by
`wallet_id`, `condition_id`, `token_id`, and `outcome`; classify BUY/SELL
groups as still-open, partial-exit, full-exit, or bounded-history oversold
candidates; and validate deterministic ordering, repeatable CSV export,
position-size conservation, and no unexpected negative position size. It must
not perform expiry joins, mark-to-market PnL, Binance/reference alignment,
copyability-delay estimation, queue-priority modelling, live trading,
automatic trade copying, wallet/private-key use, order placement, broad
public ingestion, capture campaigns, sealed holdout inspection, or holdout
evaluation.

Reason: The bounded public smoke contains useful entry/exit candidate
structure, but a one-page wallet activity window can omit earlier buys or
later sells. Treating oversold groups as bounded-history gaps preserves
reproducibility while preventing overclaims about strategy intent,
copyability, holding time, or executable edge.

## D-049: Wallet lifecycle status uses exact visible size accounting

Status: Accepted
Decision: Wallet lifecycle reconstruction and review use exact visible
BUY/SELL size accounting for bounded public trade-history rows. A group is a
full-exit candidate only when total visible bought size exactly equals total
visible sold size. Near-flat residuals remain partial exits until a separate
precision or dust policy is explicitly authorized. Lifecycle grouping is
derived from explicit `wallet_id`, `condition_id`, `token_id`, and `outcome`
fields, and deterministic ordering includes timestamp, transaction hash, side,
price, size, dedupe key, raw payload hash, endpoint name, and fetch timestamp
tie-breakers.

Reason: The bounded smoke has several near-flat BUY/SELL groups, but treating
small residuals as closed positions would invent a tolerance policy and could
overstate exits from a one-page public history window. Exact accounting keeps
the fixture reproducible and descriptive while preserving room for a future
reviewed dust policy.

## D-050: Wallet lifecycle metrics are structural only

Status: Accepted
Decision: Wallet Lifecycle Metrics v1 computes only bounded structural metrics
from existing `lifecycle_positions.csv` rows. Authorized metrics include
wallet-level lifecycle counts, status counts and shares, BUY/SELL event
counts, visible bought/sold/remaining/oversold sizes, average and median
visible position size, average event counts per lifecycle, SELL-only
lifecycle share, near-flat residual counts under a documented review-only
threshold, asset/outcome concentration, and fast-crypto lifecycle share. The
metrics layer must not compute PnL, ROI, Sharpe, copyability, wallet scoring,
wallet ranking, mark-to-market values, expiry joins, Binance/reference
alignment, queue modelling, execution logic, wallet/private-key logic, order
placement, sealed holdout inspection, or holdout evaluation.

Reason: Structural lifecycle summaries are useful for research triage, but
bounded one-page public history does not support value, ranking, copyability,
or execution conclusions. Keeping the first metrics layer structural preserves
the descriptive Wallet Intelligence boundary.

## D-051: Wallet score design must start from readiness-approved structural metrics

Status: Accepted
Decision: Wallet Metrics Readiness Review v1 authorizes a design-only Wallet
Score v1 task using current structural lifecycle metrics as inputs. Ready
inputs include lifecycle coverage, fast-crypto lifecycle count/share,
partial-exit activity, still-open share, SELL-only and bounded-history risk,
BUY/SELL event density, near-flat residual count, asset concentration, and
outcome concentration. Raw visible size fields may remain descriptive or be
used only after an explicit normalization policy. Full-exit interpretation,
PnL, ROI, Sharpe, mark-to-market, expiry/resolution behavior, copyability,
wallet ranking, and execution quality remain unauthorized until additional
data and separate design gates exist.

Reason: The current Wallet Intelligence outputs are deterministic and
structurally informative, but they come from bounded public smoke history.
Starting Wallet Score with a design-only pass prevents accidental ranking or
copyability claims while preserving a path to specify data-quality gates and
allowed inputs.

## D-052: Wallet Score v1 is structural prioritization only

Status: Accepted
Decision: Wallet Score Design v1 defines a bounded 0-100 structural
prioritization score for deciding which public wallets deserve deeper
analysis. Authorized components are coverage, fast-crypto relevance, visible
lifecycle activity, event-density consistency, and limited specialization.
Authorized penalties are SELL-only/bounded-history risk, excessive still-open
share, too few lifecycle positions, excessive concentration, and near-flat
residual ambiguity. The score must use only readiness-approved lifecycle
metrics from `wallet_metrics.csv`; raw visible size fields and `full_exits`
remain excluded from v1 scoring.

Forbidden score inputs include PnL, ROI, realized profit, Sharpe, execution
quality, copyability, alpha claims, mark-to-market values, final resolved
win/loss outcomes, sealed holdout labels or outputs, private wallet data,
order-placement data, and authenticated trading data. `wallet_id` and
`profile_url` may be used only for joins and reporting, not as score values.

Reason: The current bounded wallet metrics can identify wallets with enough
visible structural activity to inspect first, but they cannot establish
profitability, skill, copyability, or executable edge. The first score must be
a research triage tool with explicit validation gates, not a performance or
trading-quality model.

## D-053: Wallet Score fixture implementation is validation-gated and non-executable

Status: Accepted
Decision: Wallet Score Fixture Implementation v1 is accepted as a deterministic
fixture implementation of the approved Wallet Score Design v1. It may compute
a bounded 0-100 structural research-priority score from existing
`wallet_metrics.csv` only, write `wallet_scores.csv`,
`wallet_scores_summary.json`, `wallet_score_validation.json`, and
`wallet_score_report.md`, and validate score bounds, deterministic
calculation, deterministic ordering, forbidden-input exclusion, missing metric
handling, repeatable export, component/penalty bounds, output schema
completeness, and source provenance. The score bands must remain structural
research-priority labels only.

The fixture implementation does not authorize profitability claims, alpha
claims, ROI/PnL/Sharpe computation, execution-quality scoring, copyability
scoring, wallet ranking for trading, mark-to-market joins, final
win/loss-outcome inputs, sealed holdout access, private wallet data,
order-placement data, authenticated trading data, public ingestion, live
trading, automatic trade copying, wallet/private-key use, order placement, or
holdout evaluation.

Reason: The implementation proves the score can be calculated and exported
deterministically from approved structural metrics while preserving the
research-only boundary. A review task should inspect the fixture before any
score expansion or deeper-history use.

## D-054: Wallet Score fixture thresholds remain frozen pending broader evidence design

Status: Accepted
Decision: Wallet Score Fixture Review v1 accepts the current six-wallet score
behavior as design-compliant and conservative. The reviewed distribution is 1
`medium_priority`, 3 `low_priority`, 2 `insufficient_visible_structure`, and 0
`high_priority`. The strongest structural wallet scores 73, below the
`high_priority` threshold, because concentration and near-flat residual
ambiguity penalties remain active. This is acceptable for the bounded fixture
and does not require threshold or penalty adjustment.

The project will not tune Wallet Score v1 thresholds, penalties, or allowed
inputs from the six-wallet fixture alone. The next step must be a design task
for bounded, public, read-only broader evidence collection before any broader
ingestion, score expansion, threshold change, or deeper-history use.

Reason: Adjusting thresholds to create a high-priority wallet from six bounded
public seed wallets would overfit the fixture and weaken the interpretation
safety boundary. A conservative zero-high distribution is preferable until a
broader sample can test whether the score bands generalize without adding
profitability, copyability, execution, or live-trading claims.

## D-055: Wallet Score broader evidence uses a bounded 30-wallet design

Status: Accepted
Decision: Wallet Score Broader Evidence Collection Design v1 defines the first
broader Wallet Score evidence batch as a bounded public read-only 30-wallet
sample. The target composition is 6 existing seed wallets, up to 12 fast
BTC/ETH/SOL Up/Down candidates, up to 6 mixed or non-fast-crypto controls, and
up to 6 lower-activity insufficient-data controls. The first implementation
must not add score inputs or change Wallet Score v1 thresholds or penalties.

The batch limits are 30 wallets, 2 primary activity pages per wallet, 200
primary rows per wallet, 6,000 primary rows overall, 1 `/trades` cross-check
page per wallet, 100 cross-check rows per wallet, 3,000 cross-check rows
overall, 2 retries per page, and polite request pacing. Healthy score behavior
is defined as a non-degenerate distribution across at least three bands,
stable deterministic outputs, 10% to 45% insufficient-data rate, no more than
20% `high_priority`, visible separation between fast-crypto candidates and
controls, and no high score driven primarily by one fragile bounded-history
artifact.

Suspicious behavior requiring review includes more than 70% of wallets in one
bucket, more than 20% `high_priority`, more than 60%
`insufficient_visible_structure`, unstable ordering, guessed unavailable
fields, or excessive sensitivity to bounded-history artifacts.

Reason: The six-wallet fixture is too small to tune thresholds or judge score
distribution quality. A capped 30-wallet public sample is large enough to
detect obvious score pathologies while staying reproducible, manually
reviewable, and clearly separated from profitability, alpha, copyability,
trading recommendations, execution, canonical outcome validation, and sealed
holdout workflows.

## D-056: Wallet Watchlist v1 is monitoring research only

Status: Accepted
Decision: Wallet Watchlist v1 may transform existing Wallet Score fixture
outputs into a deterministic monitoring/research artifact with `wallet_id`,
profile URL, score, priority bucket, reason codes, structural strengths,
structural risks, and a recommended next research action. The watchlist must
use existing Wallet Score outputs only, must not change the score formula or
thresholds, and must exclude wallets that fail minimum visible-structure
requirements.

The watchlist is not a trading signal, not a copy-trading recommendation, not
a profitability ranking, and not an alpha claim. It must not add PnL, ROI,
Sharpe, realized profit, copyability, execution quality, mark-to-market
values, final win/loss outcomes, sealed holdout data, private wallet data,
order-placement data, authenticated trading data, public ingestion, live
trading, automatic trade copying, wallet/private-key use, order placement, or
holdout evaluation.

Reason: The current six-wallet score fixture is useful enough to create a
small research handoff for monitoring and deeper analysis, but it remains
bounded public history with structural scores only. A watchlist improves
review ergonomics without changing score behavior or implying profitability,
copyability, execution quality, or trading suitability.

## D-057: Wallet copyability research is structural triage until expiry/outcome joins exist

Status: Accepted
Decision: Wallet Copyability Feasibility Sprint v1 accepts the existing
Wallet Intelligence pipeline as a bounded public-data research path for
structural triage only. The broader 30-wallet sprint may classify wallets as
`monitor_candidate`, `needs_more_history`, `insufficient_signal`, or
`exclude_for_now` for future research prioritization, using existing
normalized public trade history, lifecycle reconstruction, lifecycle metrics,
Wallet Score, and Wallet Watchlist outputs without changing score formulas or
thresholds.

The sprint does not authorize trade copying, live monitoring, live trading,
wallet/private-key use, order placement, production model training, sealed
holdout inspection, holdout evaluation, broad scraping, capture campaigns, or
any profitability, market-advantage, return, execution-quality, or trading
claim. The next research sprint must target expiry and public outcome joins,
because the copyability feasibility evidence found those fields, plus complete
history, timing delay, slippage, liquidity, queue, and reference alignment, to
be the largest remaining blockers.

Reason: The 30-wallet sprint produced a non-degenerate structural separation
across four Wallet Score buckets and 11 monitor candidates, but the result is
only a research prioritization layer. Without expiry and resolved-outcome
context, wallet lifecycles cannot yet distinguish final-resolution behavior,
pre-expiry exits, realized side correctness, holding time, or whether observed
behavior could be studied as a copy-trading hypothesis.

## D-058: Market expiry is the next highest-information Wallet Intelligence layer

Status: Accepted
Decision: Wallet Intelligence Information Gain Sprint v1 ranks market expiry
as the next missing information layer to implement. The sprint evaluated
market expiry, resolved outcomes, full historical wallet activity,
mark-to-market valuation, BTC/ETH/SOL reference alignment, execution delay,
liquidity/slippage, queue/fill uncertainty, additional public endpoints, and
external public provenance sources independently. It selected market expiry as
the best one-week capability by information gain per engineering effort.

Resolved market outcomes remain highly valuable but should follow expiry
context so final-side evidence is not misinterpreted as profitability, market
advantage, return, execution quality, or trading suitability. Full historical
wallet activity is also high value but requires more engineering work than an
expiry join. Wallet Score, Wallet Watchlist, and copyability classifications
must remain unchanged during the expiry join task.

Reason: The previous 30-wallet copyability sprint reconstructed 2,135
lifecycle candidates, of which 1,735 were still-open. Expiry context directly
reduces that dominant ambiguity, enables time-to-expiry and late-window
analysis, improves lifecycle and watchlist interpretation, and has lower
implementation risk than full-history pagination, liquidity reconstruction,
execution-delay modelling, or queue-position estimation.

## D-059: Wallet expiry joins are Gamma-first with CLOB token cross-checks

Status: Accepted
Decision: Polymarket Public Data Discovery Sprint v1 narrows the next Wallet
Market Expiry Join Sprint v1 to public read-only endpoint joins only. The
primary expiry and lifecycle metadata path is Gamma
`/markets/slug/{market_slug}`, Gamma `/events/slug/{event_slug}`, and Gamma
`/events?slug={event_slug}`. Gamma `/markets/token/{token_id}` may be used as a
fallback when slug joins fail. CLOB `/clob-markets/{condition_id}` may be used
only as a token/outcome mapping cross-check.

CLOB `/book`, `/price`, `/midpoint`, `/spread`, `/last-trade-price`,
`/prices-history`, and `/batch-prices-history` remain useful later for
liquidity, slippage, and mark-to-market research, but they are not part of the
expiry join sprint. Authenticated CLOB order, user order, user trade, user
WebSocket, bridge write, relayer write, wallet/private-key, and order-placement
paths remain excluded.

Reason: Bounded public probes confirmed that Data API wallet activity/trade
rows expose join keys, Gamma path-by-slug and event-by-slug routes can resolve
historical fast-market metadata, and CLOB `/clob-markets/{condition_id}`
returns token/outcome mappings for historical and sampling conditions. The same
probes showed that CLOB orderbook/price routes can return 404 for expired or
non-orderbook tokens, so they should not be required for expiry joins. This
keeps the next sprint focused on the highest-information missing layer without
introducing mark-to-market, liquidity, execution, copyability, or trading
claims.

## D-060: Outcome joins may advance to descriptive outcome-aware metrics

Status: Accepted
Decision: Wallet Market Outcome Resolution Sprint v1 authorizes a bounded
descriptive outcome-aware metrics sprint over the generated
`market_outcome_join.csv` artifact. The approved inputs are public read-only
Gamma market metadata joined to existing wallet lifecycle rows, with Gamma
event/token and CLOB condition metadata used only as fallbacks or
cross-checks. The approved output semantics are limited to `matched_outcome`,
`unmatched_outcome`, `unresolved_market`, and `insufficient_evidence`.

The next sprint must not change Wallet Score, Wallet Watchlist, copyability
classifications, trading boundaries, or any live system. It must not compute
or claim PnL, ROI, realized profit, Sharpe, market advantage, copyability,
execution quality, expected value, trading suitability, or recommendations.

Reason: The sprint evaluated 2,135 lifecycle rows across 1,122 unique
conditions and joined 2,134 rows to public market metadata. Automatic resolved
outcome classification covered 2,122 rows, with 1,112 resolved conditions, 9
unresolved conditions, 1 failed join, 0 ambiguous joins, and 0 conflicting
metadata rows. That coverage is strong enough to compute descriptive
outcome-aware metrics, but not enough to infer wallet profitability,
trade-copying viability, or execution results.

## D-061: Wallet research is governed by profit-first hypothesis testing

Status: Accepted
Decision: ForgeViewAI Polymarket work is reset around one strategic question:
can a statistically justified, reproducible strategy for five-minute BTC,
ETH, and SOL Polymarket markets be built using only public wallet activity?
Future work must test a named hypothesis from `RESEARCH_PRINCIPLES.md` or
reject it quickly enough to avoid wasted effort.

The core hypotheses are:

- H1: Some public wallets consistently make better decisions than random.
- H2: Their actions become visible quickly enough.
- H3: Enough time remains after detection to act.
- H4: Structural filters improve wallet selection.
- H5: Combining these signals can outperform random participation over time.

Tasks that merely add infrastructure, metrics, joins, reports, or analytics
without expected information gain against one of these hypotheses should not
become active. The previous `Wallet Outcome-Aware Metrics Sprint v1` framing
is superseded because it was descriptive but did not directly decide a core
hypothesis. The active successor is `Wallet Outcome Skill Baseline Sprint v1`,
which directly tests H1 using existing public wallet lifecycle and market
outcome join evidence.

Reason: The project had begun accumulating Wallet Intelligence infrastructure
and review loops faster than it was eliminating strategy hypotheses. A
profit-first hypothesis filter keeps engineering subordinate to evidence and
forces every sprint to answer whether public wallet activity is moving toward
a tradable, statistically justified strategy or should be abandoned/narrowed.

## D-062: H1 remains inconclusive and narrows to H2 visibility testing

Status: Accepted
Decision: Wallet Outcome Skill Baseline Sprint v1 does not support broad
wallet strategy work, but it also does not reject H1. The sprint classifies H1
as `INCONCLUSIVE` on current bounded public evidence. Future wallet-strategy
research may continue only as a narrow H2 visibility-delay test for the four
wallets that cleared the conservative above-baseline outcome-quality gates:

- `0x088df3b7e5c1b5c2d4b7dc760863153480cf025e`;
- `0x1cc53dd33c49d0a222c61ebfd2f24ba48802b199`;
- `0x29a55c2bf8efd1029c001477b34be47d3ca37752`;
- `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`.

The project must not generalize these wallets into a strategy, alter Wallet
Score, tune Watchlist thresholds, infer copy success, or add broad wallet
infrastructure from this result. The next authorized task is Wallet Activity
Visibility Delay Sprint v1.

Reason: The H1 sprint evaluated 28 wallets and 1,788 resolved BTC/ETH/SOL fast
Up/Down lifecycle rows. The aggregate match rate was 0.524609 against a
0.500000 random baseline. Four wallets exceeded the population baseline under
minimum-sample and uncertainty gates, but three wallets showed below-baseline
evidence, thirteen were baseline-consistent, and eight lacked enough resolved
positions. Retrospective selection, survivorship bias, bounded history,
missing public visibility delay, unknown actionable time remaining, missing
fill certainty, and incomplete wallet history prevent a stronger conclusion.

## D-063: Balanced Repricing Batch 002 remains inconclusive without a random comparator

Status: Accepted
Decision: Balanced Repricing Evidence Collection Batch 002 is accepted as a
complete, continuous, replay-compatible, and deterministically exported second
development session. Its sprint conclusion is `INCONCLUSIVE`. The frozen
balanced parameters remain unchanged, and the result does not authorize
holdout evaluation, production modelling, live trading, or another capture.

Reason: The existing 12-hour public-only session yielded 71 frozen-reason
candidates, 42 validated signals, and 34 target-before-stop outcomes. Results
were positive across all three assets and both sides, with +0.053571
after-slippage expectancy and 0.280000 maximum drawdown. However, 40.85% of
candidates disappeared under frozen validation, YES and BTC/ETH samples remain
small, the 180-second horizon has no full coverage, weak evidence still lacks
40 observed hours and 3 independent sessions, and no precommitted
random-observation comparator was evaluated. Positive paper replay therefore
strengthens directional evidence without deciding the master hypothesis.

## D-064: Retrospective fetch time is not public visibility time

Status: Accepted
Decision: Wallet Activity Visibility Delay Sprint v1 classifies H2 as
`INCONCLUSIVE`. `activity_timestamp` is the trade event time and
`source_fetch_timestamp` is the time a bounded retrospective page was fetched.
Neither field records when a trade first became publicly observable. Future
Wallet Intelligence work must not use their difference as API publication
latency or compare wallet visibility speed from that difference.

The next authorized task is Wallet Detection-To-Expiry Feasibility Sprint v1.
It must use a bounded prospective local first-seen timestamp before computing
detection-to-expiry. It remains public, read-only, and research-only.

Reason: The H2 sprint analyzed 3,431 fast-crypto trade rows across 20 wallets.
Trade and fetch timestamps were complete, but publication/first-seen time was
missing for all 3,431 rows. Retrospective retrieval lag ranged from 18 to
11,200,902 seconds and varied sharply by H1 group because bounded pages
contained trades of different ages. Those values are batch-composition
evidence, not API-latency evidence.

## D-065: Frozen repricing timing beats the predefined matched random baseline

Status: Accepted
Decision: Balanced Repricing Random Baseline Sprint v1 classifies the narrow
development hypothesis as `SUPPORTED`: on Batch 001 and Batch 002, frozen
detector entries outperform a predefined random-entry timing reference matched
exactly by batch, asset, side, expiry bucket, signal count, slippage, target,
stop, timeout, and paper-position constraints.

This decision does not change detector logic, thresholds, evidence gates,
holdout policy, production status, or execution boundaries. It supports only
the statement that random timing alone did not explain the measured detector
result under this one declared baseline.

Reason: Across 172 detector signals and 24 observed hours, detector win rate
was 63.9535% and after-slippage expectancy was +0.022401. Across 1,000
deterministic matched random trials, mean win rate was 47.8692% and mean
expectancy was -0.019607; the random 97.5th percentiles were 54.6512% and
-0.011226. No random trial reached either detector metric, so both one-sided
finite-trial exceedance probabilities were 0.000999. The detector also had
lower maximum drawdown, 0.875 versus a 3.495447 random mean.

The evidence remains limited to two adjacent development sessions, 172
detector signals, serially correlated snapshots, one uniform-snapshot baseline
definition, and non-executable public paper prices. Selection, regime,
sampling, fill, depth, queue, fee, and live-latency risks remain unresolved.

## D-066: Continuous repricing paper trading requires a separate restart-safe core

Status: Accepted
Decision: The current repository is `NOT_READY` to run the frozen repricing
strategy continuously in paper mode. Future implementation must not reuse v5
generic shadow trades as repricing evidence. It must add a separate causal
paper state machine around unchanged v5 feeds and `LagDetector`, with a
transactional SQLite ledger, durable event cursor, restart recovery, persisted
duplicate protection, daily statistics, health telemetry, and optional
outbound notifications.

The next authorized task is Implement Restart-Safe Repricing Paper Trading
Core v1. It may implement frozen signal admission, paper entry/close state,
persistence, recovery, and fixture replay equivalence only. It may not launch
a public campaign, connect wallets, place orders, change detector logic or
thresholds, open the sealed holdout, or add Telegram and service supervision
before the causal core passes its acceptance gates.

Reason: Of 18 required continuous-paper components, 4 are ready, 7 require
minor work, and 7 require major work; 13 are launch blockers. Existing v5
capture is reliable, but its live shadow engine accepts different signals,
uses `EdgeScorer` and `DecisionEngine`, applies different stake/slippage
semantics, and force-closes at session end. Frozen repricing target, stop,
timeout, overlap, and accepted-reason behavior exists only in offline replay.
Open positions and duplicate gates are memory-only, and no repricing restart
recovery, daily ledger, supervisor, or Telegram notifier exists. Estimated
effort is 9-11 engineer-days plus a 24-hour supervised soak.

## D-067: H2 timing requires prospective first-seen evidence

Status: Accepted
Decision: Wallet First-Seen Detection Sprint v1 establishes that H2 is
technically measurable only with prospectively recorded local first-seen
timestamps. A measured value is a polling-quantized upper bound from public
trade event time to response completion; it contains API publication delay,
poll cadence, request duration, and local clock uncertainty. It is not an
exact server publication timestamp.

Historical identities that rotate into the latest-100 activity page after the
startup snapshot must be classified as `historical_page_churn` and excluded
from first-seen delay statistics. Future evidence must preserve that gate.

Reason: The five-minute, four-wallet public experiment completed 240 of 240
requests successfully and observed 24,000 response rows. Of 124 identities
absent from startup pages, 118 were historical page churn and only 6 were
executed during the live window. Two were target five-minute trades, with
first-seen upper bounds of 15.894 and 16.041 seconds. The endpoint also showed
440 page-range misses and 322 reappearances, making startup and live-window
classification mandatory. The method is feasible, but two target rows cannot
support or reject H2.

## D-068: Repricing paper state uses a journaled SQLite transition ledger

Status: Accepted
Decision: Frozen repricing paper execution state is persisted in a separate
SQLite ledger. Every raw source event is committed before processing; signal
admission, position open or close, realized paper PnL, and the processed event
cursor then commit in one transaction. Recovery replays only unprocessed
journal rows. Database uniqueness constraints enforce one signal identity,
one position per signal, one close per position, and no overlapping open
position for the same market and side.

The ledger stores and verifies a SHA-256 fingerprint of the frozen strategy
contract. A mismatched fingerprint fails closed. Existing v5 lifecycle closure
is accepted as an expiry transition and uses the last durable market quote.
This design remains paper-only and separate from v5 generic shadow trades.

Reason: Seven dedicated restart tests prove that open positions survive,
closed positions never reopen, duplicate input does not duplicate state or
PnL, and interruptions before or after admission, open, close, and cursor
commit recover deterministically. Fixture output matches the existing offline
frozen simulator. The next task may add only a read-only v5 event-stream
adapter; it may not change detector logic, thresholds, or launch a campaign.

## D-069: Prospective first-seen state is transactional and restart bounded

Status: Accepted
Decision: Future H2 collection must use the restart-safe prospective observer
implemented in Wallet First-Seen Prospective Experiment v1. Every completed
poll is committed transactionally with raw payload and timing provenance
before analysis. Trade identity is globally unique, first-seen time is
immutable, and run deadline/request budget survive interruption. Startup rows
remain run baselines rather than new trades.

The observer is restricted to the four frozen H1 wallets, public unauthenticated
Data API GET requests, at least 5 seconds between four-wallet cycles, and at
most 300 seconds, 240 requests, and 100 rows per wallet poll in one run. A
public run requires the explicit CLI `--observe` flag. Runtime SQLite state is
local and excluded from Git; deterministic CSV and validation reports are the
portable research artifacts.

Reason: Fixture validation proved restart recovery, expired-run rollover,
duplicate poll rejection, duplicate trade rejection, immutable first-seen
timestamps, complete poll persistence, and repeatable export. No new public
collection occurred, the initialized dataset is empty, and H2 was not
evaluated.

## D-070: H3 decision-window thresholds are descriptive and sample gated

Status: Accepted
Decision: Wallet Decision Window v1 classifies a prospective first-seen trade
as `sufficient_decision_window` with at least 60 seconds remaining,
`marginal_decision_window` with at least 30 but fewer than 60 seconds, and
`insufficient_decision_window` with fewer than 30 seconds. Sixty seconds is
the pre-existing H3 project gate and equals twelve 5-second polling intervals;
30 seconds is a descriptive lower boundary equal to six polling intervals.
Neither threshold represents measured execution feasibility.

H3 may not be supported or rejected until at least 30 eligible prospective
five-minute observations exist. Until then, decision-window output must remain
`INCONCLUSIVE` and must report polling granularity, API publication
uncertainty, cohort selection, and missing execution/liquidity latency.

Reason: The only committed feasibility evidence contains two trades from one
wallet. Their Gamma-verified first-seen-to-expiry windows were 85.106 and
44.959 seconds, producing one sufficient and one marginal classification, but
zero observations with 120 seconds remaining. This establishes measurability,
not practical copy-trading compatibility.

## D-071: v5 repricing ingestion verifies its committed source prefix

Status: Accepted
Decision: The frozen repricing paper core consumes existing v5 JSONL through a
separate read-only adapter. A normalized absolute session path defines stable
source identity. The SQLite ledger persists the source path, first canonical
event hash, and first timestamp; every signal also records source ID and event
index, while the raw journal retains the canonical event.

On restart, the adapter verifies the complete committed prefix against the raw
journal before accepting appended events. Source replacement, committed-event
mutation, truncation before the cursor, malformed complete records, invalid
ordering, and unsupported asset snapshots fail closed. An incomplete trailing
line is deferred because it may be an in-progress v5 append. Duplicate
delivery remains idempotent through existing event, signal, position, and
trade uniqueness constraints.

Reason: Nine dedicated adapter tests establish conversion, audit lineage,
duplicate suppression, open and closed restart behavior, invalid and partial
record handling, frozen DOWN/NO timeout and slippage behavior, source
replacement/truncation refusal, and equivalence between interrupted and
uninterrupted ingestion. This decision changes no detector behavior or frozen
parameter and does not authorize a continuous process or campaign.

## D-072: H2/H3 decisions use confidence, diversity, and a finite collection budget

Status: Accepted
Decision: The provisional 30-row H3 floor in D-070 is superseded for final
H2/H3 decisions. Support or rejection now requires 100 eligible prospective
five-minute trades, 3 represented wallets with at least 10 rows each, no
wallet above 60% of rows, 10 sessions, 5 UTC dates, 2 assets with at least 20
rows each, 95% timestamp/expiry/request completeness, and 100% stable identity
uniqueness. Primary proportions use two-sided 95% Wilson intervals.

H2 support requires at least 80% observed within 30 seconds and a Wilson lower
bound of at least 70%; rejection requires no more than 50% and a Wilson upper
bound of at most 60%. H3 support requires at least 70% retaining 60 seconds
and a Wilson lower bound of at least 60%; rejection requires no more than 30%
and a Wilson upper bound of at most 40%.

The branch continues only while evidence is inconclusive and the budget
remains. It graduates only when both hypotheses are supported, and then only
to bounded execution-feasibility engineering. It freezes if either hypothesis
is rejected or if 60 total five-minute sessions fail to satisfy minimum
evidence. Progress is evaluated every 10 sessions and the budget cannot extend
automatically.

Reason: Current H2 evidence is 2/2 with a 34.24%-100% Wilson interval; current
H3 evidence is 1/2 with a 9.45%-90.55% interval. Point estimates therefore do
not distinguish weak from strong underlying rates. A 100-row floor gives a
worst-case approximate 95% proportion margin of 9.8 percentage points, while
wallet, asset, date, and session gates reduce concentration risk.

## D-073: Managed repricing runtime never force-closes on process shutdown

Status: Accepted
Decision: The managed repricing paper runtime owns one restart-safe core and
one v5 JSONL adapter for its process lifetime. Each poll writes atomic health
state, and Ctrl+C or termination requests a graceful stop where supported.
Shutdown completes the current atomic operation, closes SQLite, and preserves
open paper positions for deterministic restart recovery. It must not synthesize
an exit or force-close a position merely because the process stops.

Runtime telemetry is operational health, not strategy statistics. Accepted
events are newly journaled valid v5 records; rejected events are complete
records that fail stream validation; detector admission remains defined only
by the frozen paper core. Position counters separately expose actual paper
entries and exits.

Reason: Eight dedicated runtime tests prove bounded start/stop, event flow,
duplicate replay idempotency, open-position recovery and appended close,
failed-closed invalid input, pre-requested graceful stop, deterministic health
output, and the CLI dry-run contract. Continuous unattended operation remains
unauthorized until Repricing Paper Runtime Supervision And Soak Sprint v1
adds supervision controls and produces soak evidence.

## D-074: H2/H3 accumulation is autonomous but remains hard bounded

Status: Accepted
Decision: The H2/H3 accumulator uses a separate local SQLite control ledger
beside the existing prospective observer database. Session 1 is the committed
feasibility experiment; autonomous numbering begins at session 2. An
`IMMEDIATE` SQLite reservation returns an existing active session on restart
and prevents competing session allocation. Poll and trade evidence remains in
the existing observer database rather than being copied into another source
of truth.

After every completed session, the accumulator condition-matches public Gamma
expiry metadata, evaluates the unchanged D-072 gates, and atomically replaces
`wallet_progress.json`, `wallet_progress_report.md`, and
`wallet_gate_status.json`. It stops when both hypotheses are supported, either
is rejected, or 60 sessions are complete. Background launch is a detached
wrapper around the same bounded `run` command; it is not permanent monitoring
and cannot extend the evidence budget.

Reason: Fixture tests prove persistent numbering, restart reuse, deterministic
status output without polling, frozen support and rejection paths, and an
end-to-end session-60 stop. Current status remains `ready` with 2 eligible
trades, 1 completed session, and 59 sessions remaining. No public session was
launched in the implementation sprint.

## D-075: Sustainable automated profit is the governing objective

Status: Accepted
Decision: ForgeViewAI Polymarket work is governed by the business objective of
building an automated system capable of generating sustainable profit on BTC,
ETH, and SOL five-minute markets. The long-term milestone is at least $10,000
in cumulative realized profit. Research, engineering, AI, data collection,
modelling, and infrastructure are supporting tools rather than independent end
goals.

Every sprint must either increase expected profitability or remove a blocker
preventing profitable automated trading. A sprint satisfying neither criterion
must not be pursued. Progress is measured through five ordered stages:
statistical edge demonstrated, continuous paper-trading MVP, long-duration
positive paper performance, controlled live deployment if justified, and the
$10,000 cumulative profit target.

This decision supersedes D-061 only where D-061 makes public-wallet hypothesis
testing the project's highest-level strategic objective. Its evidence rules,
named wallet hypotheses, and rejection discipline remain valid as one
supporting research path. This decision does not alter research results,
detector logic, Wallet or Repricing implementations, sealed-holdout policy, or
current execution prohibitions. Controlled live deployment still requires
separate authorization and the production-readiness and risk gates in
`MASTER_OBJECTIVE.md`.

Reason: The previous governance correctly constrained weak research and
unnecessary infrastructure, but it treated research validation as the end
state. Explicit business stages keep evidence quality and safety controls while
making profitability, reliable automation, and disciplined capital deployment
the measures of project progress.

## D-076: Controlled wallet launches are isolated and launch bounded

Status: Accepted
Decision: Operational validation may set a launch-only session cap and a
shorter session duration while retaining the frozen 5-second polling interval,
wallet cohort, endpoint, page limit, hypotheses, and H2/H3 decision contract.
Development launches must use isolated accumulator and observer databases and
must not consume canonical session budget or evidence.

Every session links to its observer run. Status output derives the actual
duration, polling interval, page limit, request ceiling, and request count from
that persisted run rather than presenting canonical defaults as measured
runtime. A launch cap ends the process in `ready` when the research action is
still `CONTINUE`; SUPPORT, REJECT, and session-60 remain the only research
terminal conditions.

Reason: The first detached 15-second launch automatically completed session 2
with 12 of 12 successful requests, four wallet baselines, 1,200 response rows,
and deterministic restart status. It found no new target trade, so evidence
correctly remained unchanged and the live Gamma cache had no eligible join.
The launch exposed and fixed the runtime-provenance display issue without
changing collection or decision behavior.

## D-077: Continuous repricing MVP restarts only explicit transient failures

Status: Accepted
Decision: Continuous Repricing Paper Trading MVP v1 is configured from one JSON
file and runs under an OS byte-range single-instance lock. Automatic restart is
limited to explicit temporary v5 source unavailability and the configured
restart budget. Malformed input, source mutation/truncation, frozen-fingerprint
mismatch, ledger integrity errors, and unexpected exceptions stop closed.

An unclean supervisor process restart reuses the prior session identity and
increments restart count. Graceful process shutdown never synthesizes a paper
exit. Status, heartbeat, daily summary, and the unified log are operational
evidence; they do not redefine detector admission or strategy performance.
Daily runtime duration is split at exact UTC day boundaries.

Reason: Eleven MVP tests prove configuration loading, preflight, holdout-path
refusal, lock exclusion/reuse, full-stack bounded outputs, recoverable restart,
unrecoverable fail-closed behavior, process-session continuity, UTC midnight
accounting, valid/rejected signal summaries, and the single-config CLI. This
completes bounded MVP engineering
but does not substitute for a supervised 24-hour public paper soak.

## D-078: Repricing is ready for an explicitly authorized 24-hour paper soak

Status: Accepted
Decision: Repricing Pre-Soak Consolidation v1 classifies the runtime
`READY_FOR_24H_SOAK`. Production-mode startup requires safe Windows AC sleep
and hibernate settings, at least 2 GiB free disk, writable state/output paths,
a valid v5 source, a recoverable ledger, and the frozen strategy fingerprint.
The runtime resolves the newest timestamped session under its source root and
rotates adapters when a newer session appears.

A source event older than 30 seconds or a health write exceeding 500 ms stops
closed. Restart drills must preserve exactly one open position after normal
restart, recover a transaction interrupted after position creation, and retain
then close an open position across graceful shutdown. Every gate passed on the
current machine; the 24-hour soak itself remains a separate explicit action.

Reason: Windows AC sleep and hibernate were both disabled, free disk was
35,648,344,064 bytes, marker write latency was 0.694 ms, session rotation and
all three restart drills passed, and stale/write fault injection stopped
closed. Forty-five Repricing tests and 191 repository tests passed. No soak,
live trade, detector change, threshold change, or holdout access occurred.

## D-079: Real-money capital progresses through research, proof, and scale

Status: Accepted
Decision: Future real-money deployment uses three Capital Stages. Capital
Stage 0 is research, replay, offline testing, and paper trading with $0
real-money risk. Capital Stage 1 begins only after successful paper evidence
and explicit approval, using approximately $3-$5 per trade or the platform
minimum if higher. Its purpose is to verify real execution against paper
assumptions, not maximize profit. Capital Stage 2 begins only after stable
Stage 1 behavior and increases size gradually under predefined rules.

Reason: Separating execution proof from scaling prevents promising paper
results from becoming an uncontrolled capital decision.

## D-080: Per-trade risk is capped at 1% of current trading capital

Status: Accepted
Decision: No trade may risk more than 1% of current trading capital regardless
of signal confidence. If the platform minimum exceeds that ceiling, the system
remains in paper mode unless use of the smallest permitted size receives
explicit approval. This platform-minimum case is the sole exception.

Reason: Confidence estimates do not eliminate model, market, liquidity, or
operational risk. A fixed capital-relative ceiling bounds single-trade damage.

## D-081: Real execution stops new entries on loss or integrity failures

Status: Accepted
Decision: A future real-money system must stop opening new trades when any
configured daily-loss, consecutive-loss, critical-infrastructure, API/data,
data-consistency, duplicate-position, restart-recovery, or unexpected
order/execution-state condition triggers. Numeric loss thresholds may be set
after paper statistics exist, but they must be predefined, paper-validated,
documented, and approved before Capital Stage 1.

Reason: A system with uncertain state or breached loss limits must fail closed
instead of attempting to trade through the fault.

## D-082: Automated strategies prohibit discretionary manual trading

Status: Accepted
Decision: Once launched, an automated strategy permits no manual trade opening,
manual trade closing, or emotion-driven parameter change. Every parameter
change requires a hypothesis, reproducible test, paper-trading validation, and
documented decision. Operational shutdown controls remain required but must not
become a discretionary trading interface.

Reason: Manual intervention invalidates reproducibility, bypasses tested risk
controls, and turns isolated outcomes into unreviewed strategy changes.

## D-083: Automation and engineering priority are strategy agnostic

Status: Accepted
Decision: ForgeViewAI minimizes manual work through automated data collection,
signal generation, paper trading, statistics, and reporting. Eventual real
execution may be automated only after evidence and explicit authorization.
Engineering priority follows the fastest reproducible evidence-backed path to
profitable BTC/ETH/SOL five-minute trading, not loyalty to Repricing, Wallet
Intelligence, or any other branch. Rejected branches may be frozen; supported
branches receive higher priority.

Reason: Automation improves repeatability, while strategy-agnostic allocation
prevents sunk cost or preference from overriding evidence.

## D-084: Trading licenses refine capital stages into Levels 0-5

Status: Accepted
Decision: ForgeViewAI uses six Trading License Levels. Level 0 is offline
research with $0 real capital and no paper requirement. Level 1 is automated
paper trading with $0 real capital and is mandatory before real trading. Level
2 is micro real trading at approximately $3-$5 per trade or the platform
minimum. Levels 3, 4, and 5 use approximate position sizes of $10, $25, and $50
per trade respectively. Higher levels require a future CEO decision.

Levels 0-1 map to Capital Stage 0, Level 2 maps to Capital Stage 1, and Levels
3-5 map to Capital Stage 2. The license ladder does not alter the 1% default
risk cap or its explicitly approved platform-minimum exception.

Reason: A finer ladder separates paper validation, real execution proof, and
gradual scaling without replacing the existing risk-stage policy.

## D-085: License promotion requires predefined evidence gates

Status: Accepted
Decision: Promotion requires a predefined minimum completed-trade count,
positive expectancy, acceptable drawdown, no critical infrastructure failures,
no duplicate-position incidents, no restart recovery failures, and stable
execution behavior. Numeric thresholds may be defined after paper statistics
are available, but must be documented and validated before use. The first
real-money transition from Level 1 to Level 2 requires documented CEO approval.

Reason: Promotion must follow reproducible evidence rather than recent outcomes
or operator discretion.

## D-086: Quality degradation automatically demotes or pauses trading

Status: Accepted
Decision: A future trading system must automatically reduce its license level
or pause new trading after a daily loss stop, consecutive-loss stop, negative
expectancy over a predefined window, excessive drawdown, infrastructure
integrity failure, API/data reliability failure, unexpected execution behavior,
or manual emergency stop. Recovery and re-promotion gates must be predefined.

Reason: Capital exposure must decrease when strategy quality or system
integrity deteriorates.

## D-087: Trading license levels cannot be raised emotionally

Status: Accepted
Decision: Position size may not increase because of perceived confidence, a
recent lucky streak, impatience, a desire to reach $10,000 faster, or an
undocumented manual override. Every increase must follow the promotion and
change-control process.

Reason: Emotional scaling converts short-term variance into uncontrolled risk
and invalidates the evidence basis for capital allocation.

## D-088: Every strategy earns the same capital license through evidence

Status: Accepted
Decision: Trading License Levels apply equally to Repricing, Wallet
Intelligence, and every future Polymarket strategy. A strategy earns capital
allocation only through evidence and receives no exception for sunk cost,
preference, or prior engineering investment.

Reason: Strategy-agnostic licensing keeps capital focused on the fastest
reproducible path toward profitable BTC/ETH/SOL five-minute trading.

## D-089: Paper trading and predefined gates precede every first real trade

Status: Accepted
Decision: No ForgeViewAI strategy may execute a real-money trade until paper
trading is complete and every predefined mandatory evidence gate for that
strategy has passed. Gate categories may include sufficient paper-trade sample,
positive expectancy, acceptable drawdown, infrastructure stability,
deterministic recovery, zero unresolved integrity failures, reproducible
exports, successful long-duration runs, and successful restart tests. Evidence
thresholds are not created by this decision.

Reason: Real-money eligibility must follow reproducible evidence rather than a
promising result, implementation readiness, or operator judgment.

## D-090: Mandatory evidence gates are evaluated automatically where possible

Status: Accepted
Decision: Every mandatory gate must have a durable result linked to source
evidence and must be evaluated automatically where possible. A gate requiring
manual review must receive an explicit documented result. Missing, incomplete,
stale, ambiguous, unresolved, or unevaluated evidence does not satisfy a gate.

Reason: Automatic and durable evaluation reduces discretion and makes the
promotion decision reproducible and auditable.

## D-091: Failed gates block CEO approval and apply to every strategy

Status: Accepted
Decision: Failure of any mandatory evidence gate blocks promotion to real
trading. CEO approval is required only after every mandatory gate passes and
can never override a failed, unresolved, or unevaluated gate. This process
applies equally to Repricing, Wallet Intelligence, and every future strategy.

Reason: Approval is the final authorization after evidence, not a mechanism for
bypassing evidence or granting a favored strategy an exception.

## D-092: Every strategy continuously re-earns permission to trade

Status: Accepted
Decision: No strategy is permanent. Every active strategy must continuously
maintain its approved evidence, risk, execution, and integrity conditions.
Automatic pause conditions include evidence gates no longer being satisfied,
sustained negative expectancy, drawdown beyond predefined limits, abnormal
execution behavior, infrastructure integrity failures, repeated restart
failures, API instability, duplicate execution risk, corrupted data, and
missing critical market data.

Reason: Historical success or prior promotion cannot justify continued capital
exposure after the evidence or operating assumptions degrade.

## D-093: Every future trading system requires an immediate global stop

Status: Accepted
Decision: Every future real-money system must support an immediate global
trading stop that prevents further automated trading activity and invokes its
predefined safe shutdown behavior. Emergency-stop authority is a risk control,
not a discretionary manual trading path.

Reason: A system-wide hazard requires one unambiguous way to stop exposure
without waiting for strategy-specific logic.

## D-094: Shutdown returns a strategy to paper trading and blocks auto-resume

Status: Accepted
Decision: A paused real-money strategy returns to Trading License Level 1 paper
trading. It may not resume real-money trading automatically. Resumption
requires a documented review of the shutdown cause, corrective evidence,
revalidation of every applicable mandatory gate, and the normal promotion and
approval process.

Reason: Restarting from a prior license would bypass the evidence needed to
show that the shutdown cause is actually resolved.

## D-095: Capital preservation overrides continuous trading

Status: Accepted
Decision: Shutdown policy applies equally to Repricing, Wallet Intelligence,
and every future strategy. Capital preservation is more important than
continuous trading, and ForgeViewAI prefers missing opportunities over
accepting uncontrolled risk.

Reason: Strategy preference, sunk cost, or urgency to reach the profit target
must not weaken shutdown decisions.

## D-096: Project health uses five canonical KPI groups

Status: Accepted
Decision: The ForgeViewAI Polymarket project dashboard uses five canonical,
strategy-agnostic KPI groups. Research Health tracks active, supported,
rejected, and inconclusive hypotheses. Strategy Health tracks current stage,
paper readiness, real-money readiness, and last evidence review for every
strategy. Trading Quality tracks expectancy, drawdown, trade count, and
paper/live status. Infrastructure Health tracks uptime, restart reliability,
duplicate protection, integrity checks, and API health. Business Progress
tracks current capital stage, current trading license level, active strategy,
and next required milestone.

Reason: A fixed dashboard vocabulary makes project health comparable across
strategies without making any strategy the default.

## D-097: KPI reporting preserves provenance and governance boundaries

Status: Accepted
Decision: Every KPI snapshot must identify observation time, evidence cutoff,
source evidence, and whether values are measured, unavailable, or not
applicable. Strategy, paper/live, asset, and evidence-window boundaries remain
separate. Missing values are not inferred, aggregate metrics cannot hide a
mandatory failure, and the KPI framework defines no numeric target or trading
authorization.

Reason: Dashboard convenience must not weaken evidence lineage, conceal risk,
or turn descriptive metrics into promotion criteria.

## D-098: Foundation is complete and launch blockers govern Phase 1

Status: Accepted
Decision: The Foundation Phase is complete. ForgeViewAI enters Phase 1 - First
Automated Dollar, governed by Objective Alpha: the first fully autonomous paper
trade from signal generation through result recording without human
intervention. `LAUNCH_BLOCKERS.md` becomes the primary operational planning
tool, and `ALPHA_READINESS.md` becomes the single readiness dashboard.

Reason: The project now has sufficient research, persistence, recovery,
governance, and runtime foundations to prioritize integrated launch progress
over additional architectural breadth.

## D-099: Every engineering sprint identifies its launch-blocker impact

Status: Accepted
Decision: Every future engineering sprint must identify the unique launch
blocker it removes or reduces, record the expected exit-condition impact before
work starts, and update the blocker and Alpha readiness state when evidence is
available.

Reason: Explicit blocker ownership prevents infrastructure work from becoming
an end in itself and keeps engineering aligned with Objective Alpha.

## D-100: Non-launch work requires explicit CEO justification

Status: Accepted
Decision: If a sprint does not reduce a launch blocker or increase
evidence-based confidence toward Objective Alpha, it requires explicit CEO
justification before authorization. Evidence has priority over feature count
and architectural completeness.

Reason: Phase 1 must reduce the distance to an autonomous signal-to-result
paper cycle rather than accumulate unvalidated features or infrastructure.

## D-101: Freeze Wallet Intelligence after terminal H2/H3 budget exhaustion

Status: Accepted
Decision: Wallet Intelligence is frozen after the canonical accumulator
completed session 60 with `SESSION_BUDGET_EXHAUSTED`. It does not graduate to
execution engineering. The frozen gate result remains formally inconclusive
because only one of five required UTC dates was observed.

The terminal 382-row aggregate must not be used as a prospective H2/H3
estimate: a read-only provenance audit found 299 historical trades admitted
after per-session baseline pages changed. The 83-row defensible diagnostic
subset remains below the 100-row and five-date evidence gates, leaves H2 below
support, and leaves H3 short of support. Neither diagnostic filtering nor this
decision changes the frozen hypotheses, thresholds, or canonical artifacts.

Wallet work may resume only for materially new multi-date evidence or an
explicitly authorized integrity correction with clear information gain.
Current engineering priority moves to the preflight-approved 24-hour Repricing
paper soak because it directly reduces Objective Alpha launch blockers.

Reason: The precommitted Wallet session budget is exhausted, the aggregate
latency evidence is contaminated by historical page churn, and continuing the
same collection would spend engineering effort without satisfying the date or
prospective-provenance requirements.

## D-102: Failed soak continuity and reconciliation evidence is not admissible

Status: Accepted
Decision: First 24-Hour Repricing Paper Soak v1 is classified
`FAILED_OPERATIONAL_INTEGRITY`. Its deterministic 73-signal offline export is
descriptive only and must not be added to frozen Repricing evidence gates.
Scientifically valid aggregate evidence remains Batch 001 plus Batch 002 until
a public session passes continuity and its live paper ledger reconciles exactly
to deterministic replay.

The next launch-blocker task must fix incremental JSONL consumption,
heartbeat/watchdog independence, bounded shutdown, and deterministic cursor
catch-up. It must preserve the frozen strategy fingerprint and may not launch a
replacement soak. `ALPHA-B002` is resolved by 60 unique, autonomous, fully
closed public-input paper trades; the continuous-engine, supervisor, daily
reporting, health-monitoring, and end-to-end blockers remain unresolved.

Reason: The source had only 75.3241% checkpoint coverage and a
23,554.333577-second maximum gap. The live heartbeat stopped after
12,310.53587 seconds, the process remained active beyond its configured bound,
and the live ledger persisted 60 signals while offline export reconstructed
73. Positive paper P&L cannot override continuity or exactly-once evidence
failures.
