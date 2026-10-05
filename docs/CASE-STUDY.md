# Harborlight — turning manual maintenance into a verified operation

**Synthetic portfolio engagement by Shemar Marks. Real Ubuntu execution, fictional business and records.**

## Business problem

A small dispatch business depends on a Linux application to view queued, ready and dispatched orders. A successful deployment is only the start of reliable operation. If routine checks are manual, a stopped service, unreviewed configuration edit or damaged backup can go unnoticed until the business needs the system or its data. Maintenance also becomes difficult to hand over: another operator cannot see what was checked, what failed or whether a change actually recovered the workload.

Harborlight demonstrates a repeatable operating process: inspect the required state, record findings, change only when conditions permit, verify afterward and leave an understandable report. It complements Northstar's migration/recovery and Cedarfield's server hardening with evidence of ongoing operational care.

## Scope and constraints

The user required zero spend and browser execution. The implementation was authored through the signed-in GitHub browser and executed on a free standard Ubuntu 24.04 runner in a public repository. No new account, password, paid platform, trial, cloud instance or external notification service was needed. The runner is disposable; this is not a persistent hosted service.

The workload is a small Python/SQLite dispatch register with five synthetic orders. It exposes loopback health and order endpoints, runs under a locked unprivileged identity and has protected filesystem settings. The infrastructure work concerns operations behavior, not feature development for a dispatch product.

## Engineering approach

The controller checks six conditions: systemd service state, HTTP health, approved configuration, live database integrity/fixture, backup assurance and filesystem capacity. Each audit writes machine-readable evidence and a short human report with next actions. It maintains local OPEN/RECOVERED transitions to avoid duplicate incident events while preserving repeated failed reports.

Observation and change are separate. The recurring timer runs audit only. The restart workflow previews its action; explicit apply is required. It permits a single fixed service restart only when configuration, data, backup and capacity are healthy. A lock prevents overlapping CLI work and a persisted cooldown limits repeated attempts. Recovery must pass all checks afterward.

Backup is also an operation with acceptance. SQLite's online backup API produces a candidate, which is validated before its manifest becomes current. Freshness, SHA256, integrity, row count and ordered-record fingerprint are checked. Restore-drill writes a separate database and never replaces current business data. The harness verifies that a separate recovered app serves the original records.

## What was actually executed

The acceptance exercise installed the app and controller, captured a healthy baseline, stopped the service, observed failed service/health checks, previewed a restart without changing state, applied a guarded restart and validated recovery. Reapplying to a healthy workload changed nothing. A second restart within cooldown was refused.

Next, an unapproved startup-config edit produced drift. A repeated audit added no duplicate OPEN event. With the service also stopped, drift blocked remediation before any restart. Returning the captured approved bytes and explicitly starting the app restored health.

A controlled two-hour-old manifest failed freshness. A new verified snapshot recovered that check. A controlled corrupt backup then failed the checksum and was refused by restore-drill while the live application remained healthy. A new snapshot was restored into a separate path; the second HTTP application served the same five orders, with matching integrity and fingerprint.

The exercise also held the operation lock and confirmed a second CLI request was refused. A real systemd timer generated at least two automatic audit reports and a successful oneshot exit. The final six checks passed. Cleanup stopped the owned application/audit units, removed their three unit files and verified that the app was inactive.

## Observed result

All **15 live acceptance scenarios** completed in the successful source run. Automated boundary tests cover valid/stale/future/corrupt/malformed manifests, unsafe paths, symlinks, missing/empty databases, locking, atomic publication, failed HTTP and alternate-root refusal. The final [evidence guide](../evidence/README.md) names the exact accepted source run and test count; [Actions](https://github.com/Shemarhn/harborlight-operations-automation/actions) provides the current CI status.

The useful outcome is not a generic green badge: failures were detected, unsafe changes were refused, recovery was verified, data was served from an isolated restore, recurring checks actually executed and the handover explains how to operate the design.

## Delivery and recurring-care relevance

A prospect can inspect runnable source, the architecture, engineering decisions, risk register, acceptance mapping, sanitized evidence, response runbook and proposed maintenance cadence. That represents the practical delivery pattern for infrastructure work: agree required behavior, implement a controlled operation, exercise failure paths, verify the result and document the remaining responsibilities.

A real engagement could continue into agreed health/backup reviews, configuration upkeep, patch windows, capacity/access review, troubleshooting, periodic recovery exercises and concise operational reporting. The proposed pathway is not a fictional retainer contract or guaranteed emergency service.

## Residual limitations

The lab is a single ephemeral host with same-filesystem backups and a fixed read-only fixture. It does not protect against host loss. Integrity/count checks cannot prove arbitrary business-record correctness; SHA256 is not immutable or signed evidence. No off-host alert delivery, sustained monthly operation, reboot test, unattended patch cycle, production SLA, measured RPO or recovery-time guarantee is claimed. Persistent deployment, backup retention/destination, alert recipients and support hours require actual client requirements and verification.

## Supporting record

[Architecture](ARCHITECTURE.md) · [Decisions](DECISIONS.md) · [Risk assessment](RISK-ASSESSMENT.md) · [Implementation](IMPLEMENTATION.md) · [Runbook](RUNBOOK.md) · [Maintenance](MAINTENANCE.md) · [Acceptance](../verification/ACCEPTANCE.md) · [Evidence](../evidence/README.md)

[Discuss the environment, problem and desired outcome](mailto:shemarmarks.tech@gmail.com) · [Service portfolio](https://shemarhn.github.io/)
