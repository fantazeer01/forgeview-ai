# Credential Handling Protocol

## Provisioning boundary

No private key, seed phrase or wallet is permitted. L2 credentials must be
created, reviewed and revoked outside the repository and outside the
calibration process. The process receives them only after a unique, expiring
authorization ID and all preflight gates pass.

## Required environment names

- `FORGEVIEW_CALIBRATION_API_KEY`
- `FORGEVIEW_CALIBRATION_API_SECRET`
- `FORGEVIEW_CALIBRATION_PASSPHRASE`
- `FORGEVIEW_CALIBRATION_ADDRESS`
- `FORGEVIEW_CALIBRATION_AUTHORIZATION_ID`
- `FORGEVIEW_CALIBRATION_KILL_SWITCH_PATH`

Values must come from an external secret provider into a clean child process.
They may not appear in command arguments, `.env` files, PowerShell history,
source, fixtures, tests, logs, dumps or Git. The parent process receives opaque
handles only. Environment inheritance is an explicit allowlist, not a copy of
the parent environment.

Forbidden environment names include `PRIVATE_KEY`, `POLYMARKET_PRIVATE_KEY`,
`WALLET_PRIVATE_KEY` and `SEED_PHRASE`. Their presence fails preflight.

## Lifetime

Credentials are loaded after network and policy preflight, retained only for
the bounded run, and references are discarded on shutdown. Core dumps and
debugger attachment are disabled. Swap/pagefile exposure must be documented;
memory zeroization is best effort in Python and cannot be claimed as guaranteed.

## Redaction

Structural redaction occurs before formatting. Keys containing API key,
secret, passphrase, signature, authorization, private key or seed terminology
are replaced by `[REDACTED]`. Raw headers and authenticated subscription bodies
are never logged. Unknown payload schemas fail closed before persistence.

Audit correlation uses SHA-256 over already-redacted canonical metadata. Never
hash raw low-entropy secrets as a substitute for redaction.

## Rotation and incident handling

Credential revocation/rotation is performed by an independent operator outside
the calibration process after every incident and after the approved run window.
The repository stores only revocation confirmation ID and time, never the
credential or provider response.
