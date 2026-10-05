# Recurring infrastructure care pathway

This is a proposed service model supported by executed tooling. It is not a paid-client engagement, signed retainer or observed month of support.

## Starting point

A one-off deployment, migration or hardening project can hand over a working system. Ongoing care keeps its operating assumptions visible: is the service healthy, did configuration change, are backups fresh and readable, can a copy be recovered, and what needs attention next? Harborlight supplies a concrete repeatable review and safe response procedure for that work.

## Agree scope before recurring work

Record the systems covered; business owner; technical contact; access method; maintenance windows; permitted changes; alert recipients; support hours; escalation route; backup destination/retention; data-loss authorization; and what the report must contain. Define patch/restart ownership, exclusions and any separate emergency agreement. Do not infer 24/7 support or a guaranteed response time.

## Suggested cadence

| Cadence | Activity | Deliverable / evidence |
|---|---|---|
| Agreed automated interval | Service/HTTP/configuration/data/backup/capacity audit on a persistent owned host. | Timestamped JSON and concise readable report; local transitions; tested external delivery if separately implemented. |
| Each maintenance window | Review failed checks, incident context, current state and change authorization; verify backup before changes. | Change record, preview, approved operation and post-change checks. |
| Weekly or agreed backup review | Check latest completion, checksum, integrity, destination and retention; investigate missed cycles. | Backup review and unresolved findings; snapshot presence alone is insufficient. |
| Monthly or agreed operating review | Review patches/support status/restarts, access changes, disk growth, config approval, incident noise and outstanding actions. | A short operational report and next maintenance plan. |
| Periodic recovery exercise | Restore into a separate approved environment and verify application records and functionality. | Recovery exercise record, measured scope/timing where actually collected, corrective actions. |
| After an incident or significant change | Establish cause, verification, lessons and procedure updates. | Incident/change closeout linked to evidence. |

The lab's five-second timer is deliberately accelerated. Its two automatic runs prove the scheduler can invoke the audit in that environment; they do not prove this proposed cadence occurred over time.

## Monthly report structure

1. **Service status:** period covered and point-in-time checks, with any data gaps disclosed.
2. **Incidents:** opened/recovered checks, impact if known, cause, response and evidence. Count only observed events; do not turn a lab fault into a real customer incident.
3. **Backups and recovery:** last verified backup, destination, failed cycles, last restore exercise and remaining exposure.
4. **Changes and patching:** approved changes, updates actually applied, restart needs and post-change validation.
5. **Capacity and access:** measured trends when available, thresholds, access review and owner changes.
6. **Risk and action list:** unresolved items, owner, priority, target date and any decision needed.
7. **Next window:** planned checks/changes and approval needed before acting.

The generated report demonstrates the status/findings/action portion. It does not manufacture a monthly trend, incident-impact metric, patch history or maintenance contract.

## Practical boundaries

Automation should observe broadly and change narrowly. The supplied timer only audits. The restart workflow is an operator-applied action in this lab; it does not silently approve drift or repair corrupt data. Low capacity raises an action item instead of deleting unknown files. Backup refresh is explicit and restores remain isolated.

External notifications, persistent deployment, off-device backup, retention, security-update execution and reboot tests are requirements to scope for the actual client. No paid product is required by this repository. Any extension must continue to use resources owned by the client or an option verified to remain free for the agreed workload.

## What a prospect can hire Shemar to do

Set up repeatable operational checks; establish a reviewed configuration baseline; implement and verify backup/restore procedures; automate agreed routine tasks; troubleshoot failures; document response and rollback; and provide concise recurring review. The commercial deliverable is a system the owner can operate and a clear record of what was verified.

Use the [runbook](RUNBOOK.md) for an actual incident path, the [risk register](RISK-ASSESSMENT.md) for remaining exposure and the [case study](CASE-STUDY.md) for executed proof. Contact [shemarmarks.tech@gmail.com](mailto:shemarmarks.tech@gmail.com) with the current environment, problem and desired outcome.
