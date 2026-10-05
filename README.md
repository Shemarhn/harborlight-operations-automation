# Harborlight: operations automation & recurring maintenance

**Shemar Marks · Synthetic portfolio engagement · Executed on Ubuntu 24.04 through GitHub Actions · Entirely free tooling**

[![Verify operations](https://github.com/Shemarhn/harborlight-operations-automation/actions/workflows/verify.yml/badge.svg)](https://github.com/Shemarhn/harborlight-operations-automation/actions/workflows/verify.yml)

A small dispatch business depends on a working Linux application. Its maintenance is manual: service failures, changed configuration and unusable backups can escape review. Harborlight turns that review into a repeatable, evidence-producing operation with a safe response path. The company and its five dispatch orders are fictional; the Ubuntu services, fault injections, backups, restored application and timer runs are real.

## What a client would receive

- A defined service inventory and approved configuration baseline.
- Repeatable health, service, configuration, database, backup and capacity checks.
- An operational report that pairs failed checks with the next action.
- Validated online SQLite snapshots and an isolated restore procedure.
- A guarded restart workflow with preview mode, preconditions, a lock and cooldown.
- An incident transition log, maintenance checklist, rollback procedure and usable handover.

## Executed outcome

| Area | What was observed |
|---|---|
| Routine review | Six checks pass on the healthy workload; JSON and Markdown reports are generated. |
| Outage handling | A deliberately stopped systemd service is detected. Preview leaves it stopped; explicit guarded apply restarts it and rechecks health. |
| Change control | Configuration drift is detected and blocks a restart; returning to the approved configuration restores the check. |
| Backup assurance | A deliberately stale manifest and a corrupt snapshot are rejected. A new online backup passes SHA256, SQLite integrity and dataset validation. |
| Recovery exercise | A separate restored database serves the same five orders through HTTP. The live database is not overwritten. |
| Repetition and coordination | A healthy repeated apply is a no-op; overlapping operations and a second restart during cooldown are refused. |
| Detection noise | Repeated configuration failure creates no duplicate OPEN event; recovery produces a RECOVERED transition. |
| Recurring execution | At least two automatic systemd audits run during the accelerated lab timer exercise. |
| Closeout | Final workload checks pass; rollback stops the application and removes the three owned lab units. |

The lab has **15 live acceptance scenarios** and **16 automated boundary tests**. [Run history](https://github.com/Shemarhn/harborlight-operations-automation/actions) is the source of CI status. [Evidence guide](evidence/README.md) explains provenance and what each result does and does not prove.

## Architecture

![Harborlight operations architecture](docs/diagrams/operations.svg)

The public standard Ubuntu runner hosts a disposable systemd application and an operations controller. The application binds to loopback and runs as a locked service identity. The controller uses a fixed lab root and fixed unit name; it accepts no arbitrary host, service, command or production path. Reports and backups are local to that runner. The hosted runner is discarded after the job.

## Explore the handover

| Document | Purpose |
|---|---|
| [Case study](docs/CASE-STUDY.md) | Business problem, engineering work, observed outcome and client relevance. |
| [Architecture](docs/ARCHITECTURE.md) | Trust boundaries, data flow, service identity and execution model. |
| [Decisions](docs/DECISIONS.md) | Why these controls and tradeoffs were chosen. |
| [Risk assessment](docs/RISK-ASSESSMENT.md) | Operational risks, treatment, evidence and residual exposure. |
| [Implementation](docs/IMPLEMENTATION.md) | File map, checks, backup protocol, event model and CI. |
| [Runbook](docs/RUNBOOK.md) | Routine review, failure response, restart, backup, restore and rollback. |
| [Maintenance](docs/MAINTENANCE.md) | Proposed recurring-care cadence, reporting and engagement boundaries. |
| [Acceptance](verification/ACCEPTANCE.md) | Executed criteria and repeat procedure. |
| [Evidence](evidence/README.md) | Source run, retained results, sanitization and limitations. |
| [Security](SECURITY.md) | Safe reuse and vulnerability reporting. |

## Repeat the free demonstration

Open [Verify Harborlight operations](https://github.com/Shemarhn/harborlight-operations-automation/actions/workflows/verify.yml), choose **Run workflow**, and run the main branch. The job runs tests, refuses an unmarked host, installs the synthetic workload on a fresh runner, injects owned faults, validates recovery, exercises the timer and removes its units. Read the job summary and sanitized output. This workflow needs only repository read access and no user-provided secrets.

Do not run the fault harness on a production server. It requires root, a fresh GitHub Actions runner and absent lab directories. The controller separately requires the exact synthetic ownership marker. Production use requires adapting inventory, thresholds, access, backup destination, change policy and recovery authorization to the actual engagement.

## Honest limits

This is one disposable host and a fixed five-order fixture. Backups share its filesystem and disappear with the runner; they do not protect against host or disk loss. Checks cover availability, integrity, freshness and known lab state, not the business correctness of arbitrary live records. SHA256 is a consistency check, not a signed attestation or immutable backup. Local incident events and a CI summary do not prove external alert delivery. The timer was observed briefly; no month of maintenance, production availability, measured RPO, SLA, recurring-client contract or guaranteed response time is claimed. Security patch review and off-device backup are documented client requirements, not executed features here.

## Cost and credentials

The project uses an existing GitHub account, a public repository, the standard Ubuntu runner, Python's standard library and systemd. There is no paid cloud resource, trial, new account, new password, extension, external API or payment method. The final workflow uses run logs and summaries rather than artifact/cache storage. [GitHub's billing documentation](https://docs.github.com/en/billing/concepts/product-billing/github-actions) states that standard public-repository runners are free and run logs/summaries do not count against artifact storage. The lab opens no public application port and contains no client data or authentication secrets.

## Related infrastructure evidence

[Northstar recovery](https://github.com/Shemarhn/northstar-aws-recovery) demonstrates migration, Terraform and an executed recovery. [Cedarfield Linux operations](https://github.com/Shemarhn/cedarfield-linux-operations) demonstrates risk-driven host hardening. Harborlight demonstrates the repeatable operational review and guarded maintenance path that can follow such a delivery.

[Discuss an infrastructure engagement](mailto:shemarmarks.tech@gmail.com) · [Service portfolio](https://shemarhn.github.io/)
