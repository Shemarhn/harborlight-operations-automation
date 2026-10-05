# Evidence, provenance and limits

## Accepted source run

[Successful verification run 37343589687](https://github.com/Shemarhn/harborlight-operations-automation/actions/runs/37343589687) · [Job output](https://github.com/Shemarhn/harborlight-operations-automation/actions/runs/37343589687/job/111876615887)

Source commit: **112ab9532c0b2f6bac99a13bcaf9fbccc480c289**. Environment: GitHub-hosted standard Ubuntu 24.04 runner. Date: 2026-10-05 UTC. The job completed compilation, **19 boundary tests**, unmarked-host refusal, **15 live acceptance scenarios** and generated evidence checksum verification.

Final audit: **2026-10-05T16:48:38.064689+00:00**, all six checks PASS. Timer case: **2 automatic reports**, Result=success, ExecMainStatus=0. Isolated restore: **5 orders**, SQLite integrity ok, dataset fingerprint **cad1d8fda12c3e35aee898d9eaab408c2054d10e4956aafe7bf40bfc63344556**. Rollback observed: app inactive and three owned unit files removed.

## Retained artifacts

The successful workflow emits compact sanitized JSON in its visible log. Four files were copied through the browser and reconstructed with the original formatting. Their SHA256 values match the original file hashes printed by the runner, byte for byte. They are committed here so an expiring log is not the only source of the observed result.

| Artifact | What it proves | What it does NOT prove |
|---|---|---|
| [cases.json](observed/cases.json) | Ordered timestamped evidence for each of the 15 completed assertions, including deliberate failures and safe refusals. | Production incidents, sustained operation or every possible failure path. |
| [latest.json](observed/latest.json) | Six point-in-time checks passed before teardown; includes exact UTC. | Continuous uptime, performance, business-data correctness or patch status. |
| [restore-latest.json](observed/restore-latest.json) | Separate SQLite copy passed integrity/count/fingerprint; live_database_overwritten=false. The corresponding case also records recovered HTTP rows. | Production cutover, host-loss protection, measured RPO or recovery-time guarantee. |
| [context.json](observed/context.json) | Public run and source revision, environment, synthetic scope and untested notification boundary. | A signed independent attestation or a permanent server deployment. |
| [SHA256SUMS.txt](observed/SHA256SUMS.txt) | Integrity of the four retained files and equality with their printed source-run digests. | Authenticity against a malicious repository owner or immutable retention. |
| [Acceptance mapping](../verification/ACCEPTANCE.md) | Human-readable criteria linked to the executed scenarios and repeat procedure. | Additional checks not present in source or the run. |

The runtime SQLite snapshots, journal, full host inventory and unrelated state are not committed. The hosted machine and its local backups disappear with the job. CI logs/summaries follow GitHub retention and are not an off-device business-backup solution. The committed JSON remains versioned source evidence, with the limitations above.

## Reading PASS correctly

A scenario can PASS by correctly refusing an unsafe operation. For example, a corrupt snapshot must produce a failed backup check and ERROR from restore-drill. The scenario passes because those outcomes were asserted and the live workload remained healthy. A failed check inside that scenario is intentional; it is not presented as healthy operating state. Only the final operational report says all six checks passed.

## Sanitization

Only synthetic reference/status records, check names, outcomes, fixed owned paths, UTC timestamps, hashes, unit names and public GitHub run/commit IDs are retained. No password, token, cookie, SSH key, environment dump, client record, private network inventory, account billing data, Terraform state or VM export is included. Review future evidence before publication; this is not a comprehensive security-scanner certification.

## Development history

Run 1 completed the live scenarios but failed the final acceptance-count assertion because the workflow expected 16 rather than 15. It is not the accepted CI result. The count was corrected; run 2 succeeded. Three malformed-input tests and clear manifest-type refusals were then added, and compact log output made all retained results accessible. The accepted run above includes those changes. A small seven-day artifact existed in the first development run; the final workflow has no artifact/cache upload or repository-write step.

## Not observed or implemented

- Off-host notification delivery or agreed on-call response.
- Off-device/immutable backup, retention rotation or host/disk-loss recovery.
- Production deployment, continuous availability, a month of maintenance, RPO or SLA.
- Persistent timer behavior after reboot/suspend.
- A low-space live fault; healthy capacity was checked, but the disk was not filled.
- An unattended security patch cycle or a production data cutover.

These remain client-specific requirements or separate exercises, never successful-validation claims for this lab.
