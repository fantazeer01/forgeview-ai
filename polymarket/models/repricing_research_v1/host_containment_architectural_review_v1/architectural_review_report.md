# Repricing Host-Containment Architectural Review v1

## Recommendation

Choose **C: change research priority**.

Do not proceed with the complete host-containment remediation package now. Do
not implement even the minimum credentialed no-order containment on the Home PC
as the immediate next step. Preserve the reviewed remediation design for a
future explicit decision, and redirect current research effort toward
less-latency-sensitive Polymarket hypotheses that can be tested with public data
and paper execution.

## Why the current task is not highest value

The Repricing branch has frozen Weak Evidence: 338 signals over 48 hours and
three sessions. Recorded and immediate executable replay are positive, but the
combined moderate execution scenario is negative, and actual two-second entry
plus cost is -0.009810 expectancy with a nominal interval below zero. Public
WebSockets remove the polling bottleneck, with 9.8616 ms p95 public-trigger to
local acknowledgement in the bounded dry run.

The remaining decisive uncertainty is not generic authentication. It is the
real order path: EIP-712 signing, order submission, exchange acceptance,
matching, queue position, partial/full fills and cancellation. A credentialed
**no-order** calibration can measure L2 HMAC, authenticated GET round trips and
user-WebSocket connection/publication behavior. It cannot measure any of the
decisive order/fill stages.

A full governance package has near-zero direct scientific information gain; it
only prepares infrastructure. A minimum package plus no-order calibration has
low-to-moderate engineering information gain but leaves the strategy's core
executability claim unresolved. On this Home PC it also requires firewall and
process-containment changes, credential operations and assigned incident roles.

## Remaining uncertainty

### Scientific

- whether the weak result survives actual marketable execution under one second;
- whether fill probability and queue position erase positive immediate replay;
- whether concentration in one session and SOL persists;
- whether a larger independent sample remains positive;
- whether a less latency-sensitive signal offers better executable robustness.

### Engineering

- authenticated order acceptance and matching latency;
- EIP-712 signing under the eventual secure signer;
- order/fill/cancel lifecycle and ambiguous state reconciliation;
- host or remote execution environment suitable for credential-bearing work.

No-order calibration resolves only a narrow subset of engineering uncertainty.

## Option comparison

### A. Full governance package

Information gain: low. Cost and operational impact: high. It is premature
because production governance would be built around a branch that is not a
production candidate and whose actual order path would remain unmeasured.

### B. Minimum host containment plus no-order calibration

Information gain: low-to-moderate. It can validate credential handling, HMAC,
authenticated read RTT and user-channel connectivity. It cannot validate
execution. This is the preferred path only if the project later resumes
Repricing specifically and accepts a staged credential program.

### C. Change research priority

Information gain: highest at portfolio level. Public-only analysis of
less-latency-sensitive hypotheses can test whether the project can find an edge
whose economics do not fail at two seconds, without introducing credentials or
modifying the Home PC security posture. Repricing remains preserved, not
rejected, and can resume from the completed package if strategic conditions
change.

## Decision boundary

Credentialed no-order calibration remains `NOT_AUTHORIZED`. This review does
not relax any gate, alter the frozen strategy, inspect holdout, or authorize
trading. It changes sequencing only.
