# Repricing No-Order Calibration Host Containment Preflight v1

## Decision

`NOT_READY_FOR_CREDENTIALS`

The read-only preflight completed successfully and modified no host setting. It
read no credential value, made no authenticated call and performed no order,
cancellation, wallet, strategy or holdout operation.

## Passed gates

- Windows Firewall inspection command completed without error.
- Fixture child launched with a clean exact environment.
- Inspection script contains only read-only firewall cmdlets.
- Secret-provider readiness checks use environment-name presence only.
- Governance parser rejects secret-bearing fields.
- Credential calibration remains explicitly unauthorized.

## Failed mandatory gates

1. All firewall profiles enabled.
2. Scoped deny-direct-egress rule present.
3. Scoped allow-local-proxy rule present.
4. Proxy-only egress configured and proven.
5. Restricted process identity configured.
6. Host kill switch configured and drilled.
7. Host watchdog configured and drilled.
8. Rollback owner assigned.
9. Revocation owner assigned.
10. Incident owner assigned.
11. Independent approver assigned.
12. Unique unexpired scope-bound authorization record present.
13. External secret-provider metadata present.
14. Host failure drills passed with evidence ID.

Domain, Private and Public firewall profiles all reported `enabled=false` and
`default_outbound_action=NotConfigured`. No matching containment rule was
found. The preflight therefore returns exit code 2 and
`NOT_READY_FOR_CREDENTIALS`, as designed.

## Safety proof

`host_settings_modified=false` and `secret_values_read=false` are emitted in
the machine-readable result. Proposed firewall commands are inert review data;
the preflight cannot execute them because its command runner rejects mutation
cmdlets before process creation.

## Recommendation

Prepare a reviewed remediation and governance package with exact executable
path, local proxy endpoint, proposed firewall commands, restricted process
design, owner-role assignments, secret-provider metadata contract, host drill
plan and rollback commands. Do not apply it until separately approved.
