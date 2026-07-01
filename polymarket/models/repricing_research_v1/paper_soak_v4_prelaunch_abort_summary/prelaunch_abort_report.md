# Fourth Repricing Soak Prelaunch Abort

Verdict: `PRELAUNCH_ABORTED_CONFIG_ENCODING`

Canonical Windows and repository preflight passed. The producer was then
started before the generated runtime configuration had been parsed by the
canonical loader. Windows PowerShell 5 wrote the JSON with a UTF-8 BOM;
`RepricingRuntimeMVPConfig.from_json()` used strict `utf-8`, rejected it, and
the producer was stopped immediately. The managed paper runtime never started.

The preserved public prefix is
`polymarket/runs/repricing_paper_soak_v4/20260701_211813/v5_sessions/20260701_211813/session.jsonl`.
It contains six valid events over 2.007355 seconds, zero signals, no paper
position, and no completion marker. It is not evidence. No replacement run
was launched.

The loader now accepts `utf-8-sig`; a dedicated BOM regression passes and the
exact preserved configuration now passes runtime preflight. Future launch
ordering requires config parse/static validation before producer startup.

Validation: 59 Repricing tests and 205 repository tests passed. Frozen strategy
parameters and evidence gates are unchanged. The sealed holdout was untouched.
