# Public Evidence Batch Pipeline v1

## Purpose

This pipeline joins public v5 capture, authoritative resolution processing,
Feature Engine, and Dataset Quality Engine into one fail-closed workflow. It
exists to grow the public evidence base while keeping the 1,000-window and
per-asset sample gates visible.

It is shadow research infrastructure only. It has no wallet, key,
authentication, order-placement, or real-trading capability.

## Commands

Before an overnight campaign, run the fail-closed Windows power preflight:

```powershell
python -m polymarket.evidence_batch preflight
```

If it reports unsafe AC sleep or hibernate settings, open an elevated
PowerShell and run:

```powershell
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /setacvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION 0
powercfg /S SCHEME_CURRENT
powercfg /getactivescheme
powercfg /query SCHEME_CURRENT SUB_SLEEP
```

Keep the computer connected to AC power and do not close a laptop lid unless
the lid action is configured to `Do nothing`. The capture process also holds a
Windows `ES_SYSTEM_REQUIRED` execution-state request for its lifetime, but the
preflight remains mandatory because lid-close and administrative power policy
can override application requests.

Capture a new six-hour public batch with mock fallback disabled:

```powershell
python -m polymarket.evidence_batch run \
  --assets BTC ETH SOL \
  --duration 21600 \
  --poll-interval 2 \
  --discovery-interval 5
```

Resume post-processing from an existing session using saved resolution
responses:

```powershell
python -m polymarket.evidence_batch resume \
  --session polymarket/runs/v5/SESSION/session.jsonl \
  --resolution-mode replay
```

Use `--resolution-mode refresh` to query current public Gamma resolution data.
Resume rejects sessions without a final `session_completed` event so an active
capture cannot be processed while its evidence file is still changing.

## Stage order

1. Public v5 capture (`run` only), with `mock=False` and
   `allow_mock_fallback=False`.
2. Resolution refresh or deterministic replay.
3. Authoritative Feature Engine rebuild.
4. Dataset quality analysis and public-only export.
5. Batch manifest generation.

The pipeline stops at the first failed stage. Later stages do not read or
report stale outputs as new results.

A repository-local exclusive lock prevents overlapping batch invocations from
writing the canonical resolution and training artifacts concurrently.

## Manifest

Written to:

```text
polymarket/runs/evidence_batches/SESSION/batch_manifest.json
```

It includes:

- capture start/end and configuration;
- source-session and artifact SHA-256 hashes;
- discovered, resolved, unresolved, and missing market counts;
- clean rows and rows per asset;
- class balance, completeness, quality score, and sparse exclusions;
- progress toward 1,000 total rows and 200 rows per asset;
- stage status and failure reason;
- a project-level verdict.

Verdicts:

- `BATCH_FAILED`
- `INSUFFICIENT_PUBLIC_SAMPLE`
- `DATA_QUALITY_FAILED`
- `DATA_GATE_PASSED`

Dataset Quality Engine recommendation alone does not authorize model training.
The manifest remains `INSUFFICIENT_PUBLIC_SAMPLE` until both master sample
targets pass.

## Determinism

Resume mode derives capture times from the saved session and hashes every
artifact. Given the same session, resolution fixture, configuration, and code,
the manifest is byte-deterministic.

Before post-processing, the pipeline copies sessions whose final saved event is
no later than the selected source session's completion timestamp into an
immutable batch input view. This preserves older interrupted evidence while
excluding captures that were still active at the batch cutoff. Every copied
session is hashed and marked terminal or interrupted in the snapshot index.
