# Event Correlation Report

- Public trigger events: 60.
- Terminal loopback lifecycles: 60.
- Subsequent public transitions observed: 60.
- Missing transitions: 0.
- Replay events: 900.
- Replay correlations: 60.
- Replay status: PASS.
- Duplicate public identities suppressed: 303.
- Stale events rejected: 0.
- Backpressure drops: 0.
- Reconnects: 0.

Correlation IDs are deterministic SHA-256 values derived from the fixed dry-run
run ID and attempt index. Public payloads are represented only by SHA-256 hash.
No credentials, authorization headers, signed exchange orders or raw public
event journal are present in Git-safe artifacts.

The “next public transition” is the first recognized public event for the same
token after simulated submission. It demonstrates event-stream observability;
it is not proof that a simulated order appeared on the public book.
