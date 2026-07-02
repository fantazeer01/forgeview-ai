# Preflight and Rollback

## Preflight

1. Verify clean approved commit and exact policy hash.
2. Verify unique unexpired independent authorization ID.
3. Verify no private-key/seed environment names and exact required L2 names.
4. Verify no credential value appears in command line, files or parent logs.
5. Verify isolated process, no shell/child process, restricted run directory.
6. Verify direct network egress fails and allowlist proxy is the only route.
7. Replay positive and negative endpoint fixtures through the proxy.
8. Verify kill switch, parent watchdog and proxy-loss fail-closed drills.
9. Verify NTP and CLOB clock uncertainty gates.
10. Verify redaction, exception and crash-path tests.
11. Verify `GET /data/orders` returns zero open orders after authorization; any
    nonzero result aborts without cancellation.
12. Start bounded observation only after every gate records PASS.

## Rollback

1. Arm kill switch and stop new requests.
2. Close WebSocket and HTTP connections.
3. Terminate isolated process and verify no child remains.
4. Revoke proxy egress and preserve redacted audit hashes.
5. Independently inspect open-order state; calibration never cancels.
6. Rotate/revoke L2 credentials externally.
7. Record incident, revocation confirmation and last successful checkpoint.
8. Return to public-only operation; no automatic restart.
