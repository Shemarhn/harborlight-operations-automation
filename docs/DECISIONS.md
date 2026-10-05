# Engineering decisions

## D1 — Use a disposable free Ubuntu runner

The user required browser execution and zero spend. GitHub already supplied authenticated source control and a free standard runner for this public repository. That allows real systemd, SQLite and HTTP behavior with repeatable teardown. It avoids paid cloud resources and another account/password. The tradeoff is ephemerality: this demonstrates operations tooling, not a persistent client host or continuous service.

## D2 — Standard-library Python and systemd

The workload and controller need no third-party Python dependency. The selected primitives are available on the runner and easy to inspect: HTTP, SQLite, subprocess, SHA256, atomic rename, JSON and flock. This keeps the demonstration reproducible and makes the operator's boundary visible. A fleet engagement might justify Ansible or another established orchestrator; this single-host exercise does not need a second orchestration layer.

## D3 — Separate observation from changes

Audit reads workload state and produces reports. It does not remediate. Remediate produces a plan unless --apply is present. Only an allowlisted service restart is implemented. Configuration/data/backup/capacity failures block restart. This limits a common automation failure: repeatedly restarting a service whose underlying state is broken. The cost is that more complex incidents still require operator judgment.

## D4 — Record an attempt before restarting

Cooldown state is written before calling systemctl. A failed restart therefore still counts as an attempt. The interval is 60 seconds in this lab, and post-check polling is bounded to approximately five seconds plus individual request limits. This is a containment control, not an agreed response target. The lock prevents concurrent CLI operations; the cooldown handles serial repeated attempts.

## D5 — Online backup, then validation

Copying the raw file of an active SQLite database is unsafe in some journal/WAL situations. The online backup API produces a consistent copy. Integrity, nonempty ordered rows, count, fingerprint and SHA256 are recorded. The manifest is replaced only after validation, reducing exposure to partial publication. SHA256 does not authenticate the manifest against a malicious privileged user, and local storage remains a single failure domain.

## D6 — Restore into a separate path

The restore command never replaces the live DB. A unique destination lets the harness test recovered data through an independent HTTP process while comparing the original workload. This demonstrates recoverability without approving a destructive cutover. Production restoration needs an explicit data-loss decision and workload-specific procedure.

## D7 — Track incident transitions, preserve repeated failures

The controller writes OPEN once, records recovery, and opens a new event on recurrence. Repeated failed audits still produce failed reports. This reduces event duplication without suppressing the problem. There is no remote notification transport, delivery test or on-call service. State loss can cause duplicates after rebuild.

## D8 — Schedule checks without scheduling remediation

A real systemd timer performs automatic audit runs during the lab. Its five-second interval is deliberately accelerated to make two executions observable. A production cadence, backup schedule, retention and reboot behavior must be agreed and validated on a persistent host. No ongoing GitHub cron or paid monitoring resource was created.

## D9 — Keep CI repository access read-only

The final workflow has only contents:read and does not persist checkout credentials. Successful results are exposed in the job summary and sanitized logs; the documentation retains their source run and scope. An automatic repository evidence push would need broader access and was excluded after approval review. Routine browser-authored documentation is sufficient for this engagement.

## D10 — Avoid artifact storage and caches in the final workflow

GitHub documents public standard-runner execution as free, while artifacts can share a metered allowance. The final workflow uses logs and summaries, which do not consume artifact storage. No cache or artifact upload step remains. One initial development run produced a 6.15 KB artifact with seven-day retention before this was removed from the design; the account usage view showed zero billed usage at inspection. That development run is retained as an honest failed-run record, not the final acceptance claim.

## D11 — Keep the public story bounded

The report's integrity, freshness and fixture checks do not establish arbitrary business-data correctness. The exercise does not establish a month of maintenance, SLA, production uptime, RPO, external alert delivery or security certification. The recurring-care offer is a proposed commercial pathway based on delivered tooling and procedures, not an invented customer contract.

## Sources

- [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions): free standard public runners; logs/summaries excluded from artifact allowance. Checked 2026-10-05.
- Source code is the executable specification for the lab's exact checks, guardrails and thresholds; observed runs establish only what completed in that environment.
