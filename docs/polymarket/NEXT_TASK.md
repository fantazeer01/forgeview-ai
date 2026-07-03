# Polymarket Next Task

Last updated: July 4, 2026
Task status: ACTIVE

This file contains exactly one active task. Read canonical project memory
before starting it.

## Active task: Run Public-Only Less-Latency-Sensitive Strategy Candidate Review v1

### Objective

Identify and rank Polymarket strategy hypotheses whose expected economics are
less sensitive than Repricing to sub-two-second execution, using existing
public data, project evidence and replay capabilities only.

### Required scope

1. Define a latency-tolerance rubric emphasizing one-to-five-second delay and
   minute-scale holding/action windows.
2. Review candidate families including slower cross-market dislocations,
   wallet lifecycle/timing, spread-liquidity regimes and post-event
   continuation/reversion.
3. Estimate public-data availability, testability, sample density, executable
   cost exposure and time-to-evidence for each candidate.
4. Identify which candidates can reuse existing sessions and infrastructure.
5. Recommend exactly one public-only candidate sprint or conclude none is
   sufficiently promising.

### Forbidden

- no credentials, authenticated endpoints, wallet/private-key logic or orders;
- no host firewall or containment changes;
- no sealed holdout inspection or evaluation;
- no production model training;
- no strategy parameter optimization or new long capture campaign.

### Acceptance criteria

- candidates ranked by information gain and executable robustness;
- latency assumptions and missing data explicit;
- one successor selected without changing existing frozen protocols;
- relevant and full repository tests pass;
- exactly one active successor remains.
