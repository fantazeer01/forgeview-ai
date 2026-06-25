# Wallet Copyability Feasibility Sprint v1

Generated: 2026-06-25T21:41:10+00:00

## Scope And Non-Claims

This is public, read-only Wallet Intelligence research. It is not a trading signal, not a copy-trading recommendation, does not provide financial advice, and is not a claim about performance, market advantage, returns, copy outcomes, or execution quality.

## Evidence Size

- Wallet count: 30
- Primary normalized trade rows: 5765
- Cross-check rows fetched: 3000

## Classification Counts

- `insufficient_signal`: 2
- `monitor_candidate`: 11
- `needs_more_history`: 17

## Required Research Questions

- A. Monitor candidates: 11
- B. Exclude for now: 0
- C. Score separation: non_degenerate: scores span 4 priority buckets ({'high_priority': 3, 'insufficient_visible_structure': 2, 'low_priority': 12, 'medium_priority': 13})
- D. Most influential structural metrics: fast_crypto_component, coverage_component, lifecycle_activity_component, still_open_penalty, concentration_penalty
- E. Almost useless metrics in this batch: none with zero range
- F. Interesting despite weak raw evidence: 0x54afeb88e709fbfb7e75a1ab8275ed4f0b333130, 0x0e0d60ea727cb7a569ea391263cc10952d1e6e5b, 0x1a561cdee16a7a263231aacc9ee50447ea6cf475, 0x11e7740bc4f6f16f4c56bcdc8abda23f0863d3c2, 0x47d7dfd8b93e656d44ed173c848203e05982113a
- G. Largest blockers: realized outcome joins, expiry joins, complete unbounded wallet history, entry-to-exit holding time, observation delay model, slippage model, liquidity and fill uncertainty, queue position, maker/taker completeness, external BTC/ETH/SOL reference alignment

## Observed Versus Unknown

Observed:
- public activity/trade rows
- normalized trade fields
- visible lifecycle structure
- visible BUY/SELL side counts
- fast-crypto exposure
- structural Wallet Score components
- watchlist inclusion reason codes

Unknown:
- realized outcome joins
- expiry joins
- complete unbounded wallet history
- entry-to-exit holding time
- observation delay model
- slippage model
- liquidity and fill uncertainty
- queue position
- maker/taker completeness
- external BTC/ETH/SOL reference alignment

## Wallet Classifications

- `0x4228048ea2f8f571ff2777cc32baee584c5134cb`: recommendation=monitor_candidate, score=85.8974358974358974358974359, bucket=high_priority, confidence=medium_structural
  - reasons: bucket_high_priority;minimum_visibility_passed;fast_crypto_relevant;visible_partial_exit_activity
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible partial-exit structure; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment
- `0x4a0b6dacb223f1126080048826f0271dbe31ff39`: recommendation=monitor_candidate, score=84.2, bucket=high_priority, confidence=medium_structural
  - reasons: bucket_high_priority;minimum_visibility_passed;fast_crypto_relevant;visible_partial_exit_activity;near_flat_residual_ambiguity
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible partial-exit structure; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; near-flat residual ambiguity
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment
- `0xde79cc7660d5c05b4cd2f4e72cae30cde2583d9a`: recommendation=monitor_candidate, score=75, bucket=high_priority, confidence=medium_structural
  - reasons: bucket_high_priority;minimum_visibility_passed;fast_crypto_relevant;visible_partial_exit_activity;concentration_risk;near_flat_residual_ambiguity
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible partial-exit structure; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; high concentration limits generality; near-flat residual ambiguity
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment
- `0x1cc53dd33c49d0a222c61ebfd2f24ba48802b199`: recommendation=monitor_candidate, score=73.83333333333333333333333334, bucket=medium_priority, confidence=low_to_medium_structural
  - reasons: bucket_medium_priority;minimum_visibility_passed;fast_crypto_relevant;visible_partial_exit_activity;bounded_history_artifact_risk;concentration_risk;near_flat_residual_ambiguity
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible partial-exit structure; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; bounded-history artifact risk; high concentration limits generality; near-flat residual ambiguity
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; prior buys before bounded window
- `0x3c6afcbc144b6bb110dbf8538bde2781c24a8a58`: recommendation=monitor_candidate, score=69.5, bucket=medium_priority, confidence=low_to_medium_structural
  - reasons: bucket_medium_priority;minimum_visibility_passed;fast_crypto_relevant;visible_partial_exit_activity;bounded_history_artifact_risk;concentration_risk;near_flat_residual_ambiguity
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible partial-exit structure; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; bounded-history artifact risk; high concentration limits generality; near-flat residual ambiguity
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; prior buys before bounded window
- `0x4bfb3f47ad1a0b494ecaa3c1a9bfba22a4c39f3a`: recommendation=monitor_candidate, score=67.31818181818181818181818182, bucket=medium_priority, confidence=low_to_medium_structural
  - reasons: bucket_medium_priority;minimum_visibility_passed;fast_crypto_relevant;visible_partial_exit_activity;bounded_history_artifact_risk;concentration_risk;near_flat_residual_ambiguity
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible partial-exit structure; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; bounded-history artifact risk; high concentration limits generality; near-flat residual ambiguity
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; prior buys before bounded window
- `0x1a39c44c2bc6b23cc715a197cc0d76574ab51bb6`: recommendation=monitor_candidate, score=66, bucket=medium_priority, confidence=medium_structural
  - reasons: bucket_medium_priority;minimum_visibility_passed;fast_crypto_relevant;visible_partial_exit_activity;concentration_risk
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible partial-exit structure; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; high concentration limits generality
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment
- `0x088df3b7e5c1b5c2d4b7dc760863153480cf025e`: recommendation=monitor_candidate, score=63.13636363636363636363636363, bucket=medium_priority, confidence=low_to_medium_structural
  - reasons: bucket_medium_priority;minimum_visibility_passed;visible_partial_exit_activity;bounded_history_artifact_risk
  - strengths: strong visible lifecycle coverage; visible partial-exit structure; visible repeated event density
  - weaknesses: bounded public history only; bounded-history artifact risk
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; prior buys before bounded window
- `0x2e554602dbe0d9549fd5a356892f3f7ddb28c549`: recommendation=monitor_candidate, score=61.85950413223140495867768595, bucket=medium_priority, confidence=low_to_medium_structural
  - reasons: bucket_medium_priority;minimum_visibility_passed;fast_crypto_relevant;visible_partial_exit_activity
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible partial-exit structure; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment
- `0x20d2309cd92b797ae7ca175ed828ed8a27fbe29d`: recommendation=monitor_candidate, score=59.33333333333333333333333334, bucket=medium_priority, confidence=low_to_medium_structural
  - reasons: bucket_medium_priority;minimum_visibility_passed;fast_crypto_relevant;visible_partial_exit_activity;bounded_history_artifact_risk
  - strengths: minimum visible lifecycle coverage; high fast-crypto lifecycle share; visible partial-exit structure; visible repeated event density
  - weaknesses: bounded public history only; bounded-history artifact risk
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; prior buys before bounded window
- `0x29a55c2bf8efd1029c001477b34be47d3ca37752`: recommendation=monitor_candidate, score=56.1875, bucket=medium_priority, confidence=low_to_medium_structural
  - reasons: bucket_medium_priority;minimum_visibility_passed;fast_crypto_relevant;visible_partial_exit_activity;bounded_history_artifact_risk;concentration_risk
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible partial-exit structure; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; bounded-history artifact risk; high concentration limits generality
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; prior buys before bounded window
- `0x54afeb88e709fbfb7e75a1ab8275ed4f0b333130`: recommendation=needs_more_history, score=59, bucket=medium_priority, confidence=low_to_medium_structural
  - reasons: bucket_medium_priority;minimum_visibility_passed;fast_crypto_relevant;visible_partial_exit_activity;all_or_mostly_open_visibility;concentration_risk
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible partial-exit structure; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; all or mostly open visible lifecycle state; high concentration limits generality
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; later exits beyond bounded window
- `0x0e0d60ea727cb7a569ea391263cc10952d1e6e5b`: recommendation=needs_more_history, score=52, bucket=medium_priority, confidence=low_to_medium_structural
  - reasons: bucket_medium_priority;minimum_visibility_passed;fast_crypto_relevant;all_or_mostly_open_visibility;concentration_risk
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; all or mostly open visible lifecycle state; high concentration limits generality
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; later exits beyond bounded window
- `0x11e7740bc4f6f16f4c56bcdc8abda23f0863d3c2`: recommendation=needs_more_history, score=52, bucket=medium_priority, confidence=low_to_medium_structural
  - reasons: bucket_medium_priority;minimum_visibility_passed;fast_crypto_relevant;all_or_mostly_open_visibility;concentration_risk
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; all or mostly open visible lifecycle state; high concentration limits generality
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; later exits beyond bounded window
- `0x1a561cdee16a7a263231aacc9ee50447ea6cf475`: recommendation=needs_more_history, score=52, bucket=medium_priority, confidence=low_to_medium_structural
  - reasons: bucket_medium_priority;minimum_visibility_passed;fast_crypto_relevant;all_or_mostly_open_visibility;concentration_risk
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; all or mostly open visible lifecycle state; high concentration limits generality
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; later exits beyond bounded window
- `0x47d7dfd8b93e656d44ed173c848203e05982113a`: recommendation=needs_more_history, score=52, bucket=medium_priority, confidence=low_to_medium_structural
  - reasons: bucket_medium_priority;minimum_visibility_passed;fast_crypto_relevant;all_or_mostly_open_visibility;concentration_risk
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; all or mostly open visible lifecycle state; high concentration limits generality
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; later exits beyond bounded window
- `0xd0d6053c3c37e727402d84c14069780d360993aa`: recommendation=needs_more_history, score=48.3076923076923076923076923, bucket=low_priority, confidence=low_to_medium_structural
  - reasons: bucket_low_priority;minimum_visibility_passed;fast_crypto_relevant;visible_partial_exit_activity;bounded_history_artifact_risk;small_visible_sample
  - strengths: minimum visible lifecycle coverage; high fast-crypto lifecycle share; visible partial-exit structure; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; small visible lifecycle sample; bounded-history artifact risk
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; prior buys before bounded window
- `0x01b739b360d3c2f6cc8ec84cda900d48650e2eca`: recommendation=needs_more_history, score=48, bucket=low_priority, confidence=low_to_medium_structural
  - reasons: bucket_low_priority;minimum_visibility_passed;fast_crypto_relevant;all_or_mostly_open_visibility;concentration_risk
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; all or mostly open visible lifecycle state; high concentration limits generality
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; later exits beyond bounded window
- `0x4d0730b1c8b4da2444ab7a4a389a607584132b94`: recommendation=needs_more_history, score=46.2368421052631578947368421, bucket=low_priority, confidence=low_to_medium_structural
  - reasons: bucket_low_priority;minimum_visibility_passed;visible_partial_exit_activity;bounded_history_artifact_risk;near_flat_residual_ambiguity
  - strengths: strong visible lifecycle coverage; visible partial-exit structure; visible repeated event density
  - weaknesses: bounded public history only; bounded-history artifact risk; near-flat residual ambiguity
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; prior buys before bounded window
- `0x25f4707c93e4bfdf26cd6c5cc46c5464691cf88e`: recommendation=needs_more_history, score=46.2, bucket=low_priority, confidence=low_to_medium_structural
  - reasons: bucket_low_priority;minimum_visibility_passed;fast_crypto_relevant;all_or_mostly_open_visibility;concentration_risk
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; all or mostly open visible lifecycle state; high concentration limits generality
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; later exits beyond bounded window
- `0x251c1a283703beed41590b0875a8dcb8ddd1541f`: recommendation=needs_more_history, score=45, bucket=low_priority, confidence=low_to_medium_structural
  - reasons: bucket_low_priority;minimum_visibility_passed;fast_crypto_relevant;all_or_mostly_open_visibility
  - strengths: minimum visible lifecycle coverage; high fast-crypto lifecycle share; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; all or mostly open visible lifecycle state
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; later exits beyond bounded window
- `0x59e9593d9ad358947577a51f2c2d32b49cff2f9d`: recommendation=needs_more_history, score=45, bucket=low_priority, confidence=low_to_medium_structural
  - reasons: bucket_low_priority;minimum_visibility_passed;fast_crypto_relevant;all_or_mostly_open_visibility;concentration_risk
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; all or mostly open visible lifecycle state; high concentration limits generality
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; later exits beyond bounded window
- `0x3b19d4c9e38af6e6d6923039275d5cfe89bc3655`: recommendation=needs_more_history, score=44.63302752293577981651376147, bucket=low_priority, confidence=low_to_medium_structural
  - reasons: bucket_low_priority;minimum_visibility_passed;fast_crypto_relevant;all_or_mostly_open_visibility;concentration_risk
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; all or mostly open visible lifecycle state; high concentration limits generality
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; later exits beyond bounded window
- `0x2c3ef176341ced9b0c5456d355d58fc0832e282d`: recommendation=needs_more_history, score=38, bucket=low_priority, confidence=low_to_medium_structural
  - reasons: bucket_low_priority;minimum_visibility_passed;fast_crypto_relevant;all_or_mostly_open_visibility;concentration_risk
  - strengths: strong visible lifecycle coverage; high fast-crypto lifecycle share; visible repeated event density
  - weaknesses: bounded public history only; all or mostly open visible lifecycle state; high concentration limits generality
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; later exits beyond bounded window
- `0x60ca7ed001bb8496c50fde95329f6a8fa756f86e`: recommendation=needs_more_history, score=37.63157894736842105263157895, bucket=low_priority, confidence=low_to_medium_structural
  - reasons: bucket_low_priority;minimum_visibility_passed;all_or_mostly_open_visibility
  - strengths: strong visible lifecycle coverage; visible repeated event density
  - weaknesses: bounded public history only; all or mostly open visible lifecycle state
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; later exits beyond bounded window
- `0x63ce342161250d705dc0b16df89036c8e5f9ba9a`: recommendation=needs_more_history, score=37.14285714285714285714285714, bucket=low_priority, confidence=low_structural
  - reasons: bucket_low_priority;minimum_visibility_passed;fast_crypto_relevant;visible_partial_exit_activity;small_visible_sample;near_flat_residual_ambiguity
  - strengths: minimum visible lifecycle coverage; high fast-crypto lifecycle share; visible partial-exit structure; interpretable market specialization
  - weaknesses: bounded public history only; small visible lifecycle sample; near-flat residual ambiguity
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment
- `0x4af813b3fc6038c55d06ce21531e9dceab093b6d`: recommendation=needs_more_history, score=37, bucket=low_priority, confidence=low_to_medium_structural
  - reasons: bucket_low_priority;minimum_visibility_passed;fast_crypto_relevant;all_or_mostly_open_visibility;concentration_risk
  - strengths: minimum visible lifecycle coverage; high fast-crypto lifecycle share; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; all or mostly open visible lifecycle state; high concentration limits generality
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; later exits beyond bounded window
- `0x1f0ebc543b2d411f66947041625c0aa1ce61cf86`: recommendation=needs_more_history, score=33.14285714285714285714285714, bucket=low_priority, confidence=low_to_medium_structural
  - reasons: bucket_low_priority;minimum_visibility_passed;fast_crypto_relevant;all_or_mostly_open_visibility;small_visible_sample
  - strengths: minimum visible lifecycle coverage; high fast-crypto lifecycle share; visible repeated event density
  - weaknesses: bounded public history only; all or mostly open visible lifecycle state; small visible lifecycle sample
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; later exits beyond bounded window
- `0xde17f7144fbd0eddb2679132c10ff5e74b120988`: recommendation=insufficient_signal, score=23, bucket=insufficient_visible_structure, confidence=low_to_medium_structural
  - reasons: bucket_insufficient_visible_structure;minimum_visibility_passed;no_fast_crypto_visibility;all_or_mostly_open_visibility;concentration_risk
  - strengths: strong visible lifecycle coverage; visible repeated event density; interpretable market specialization
  - weaknesses: bounded public history only; all or mostly open visible lifecycle state; no visible fast-crypto lifecycle share; high concentration limits generality; insufficient visible structure bucket
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; later exits beyond bounded window; fast crypto relevance
- `0x594edb9112f526fa6a80b8f858a6379c8a2c1c11`: recommendation=insufficient_signal, score=19, bucket=insufficient_visible_structure, confidence=low_to_medium_structural
  - reasons: bucket_insufficient_visible_structure;minimum_visibility_passed;no_fast_crypto_visibility;all_or_mostly_open_visibility;concentration_risk
  - strengths: strong visible lifecycle coverage; visible repeated event density
  - weaknesses: bounded public history only; all or mostly open visible lifecycle state; no visible fast-crypto lifecycle share; high concentration limits generality; insufficient visible structure bucket
  - missing: realized outcome joins; expiry joins; complete unbounded wallet history; entry-to-exit holding time; observation delay model; slippage model; liquidity and fill uncertainty; queue position; maker/taker completeness; external BTC/ETH/SOL reference alignment; later exits beyond bounded window; fast crypto relevance

## Validation

- `deterministic_ordering`: true
- `output_schema_completeness`: true
- `every_wallet_classified`: true
- `reason_codes_present`: true
- `no_forbidden_metric_fields`: true
- `forbidden_metric_fields`: []
- `no_forbidden_claims`: true
- `forbidden_claim_phrases`: []
- `all_validation_passed`: true
- `repeatable_export`: true

## Research Conclusion

Based on the current bounded public evidence, Wallet Intelligence is moving toward a useful copy-trading research system only as a structural triage layer: 11 of 30 wallets became monitor_candidate and the score separated wallets into multiple structural groups, but missing realized outcomes, expiry joins, complete history, timing-delay, slippage, and liquidity evidence remain too significant for any conclusion about copy outcomes, market advantage, returns, or trading use.

## Recommended Next Sprint

`Wallet Expiry And Outcome Join Feasibility Sprint v1`
