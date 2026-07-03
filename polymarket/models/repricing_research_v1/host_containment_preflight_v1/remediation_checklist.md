# Host Containment Remediation Checklist

No item below is authorized for execution by this sprint.

1. Select the exact calibration executable path and dedicated local proxy port.
2. Review impact of enabling Windows Firewall profiles on unrelated Home PC
   workloads; define backup and rollback first.
3. Review proposed executable-scoped outbound block and loopback proxy allow
   rules with an administrator.
4. Choose a restricted process mechanism that denies shell and child-process
   creation and limits filesystem writes to one run directory.
5. Define a proxy that rejects redirects and permits only the frozen endpoint
   matrix.
6. Assign rollback, credential revocation, incident and independent approval
   roles using non-secret identifiers.
7. Approve an external L2 secret-provider metadata contract; do not store
   secret values in the governance record.
8. Define kill-switch and watchdog host paths, ownership and permissions.
9. Run firewall bypass, proxy loss, parent death, child escape, log failure,
   clock drift and rollback drills using fixture handles only.
10. Record drill evidence hashes and verify direct CLOB egress fails.
11. Re-run this preflight; every gate must pass.
12. Only then create a unique, narrow, expiring authorization record and submit
   it to a new independent review. Passing preflight still does not execute a
   credentialed calibration.
