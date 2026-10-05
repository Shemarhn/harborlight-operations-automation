# Harborlight operations runbook

Audience: an infrastructure operator reviewing this synthetic engagement. Commands describe the owned lab after installation. The fault harness installs only on a fresh GitHub Actions runner; the ephemeral instance is removed after each completed job. No permanent managed server has been created.

## 1. Scope and ownership

Owned service: `harborlight-app.service`. Code: `/opt/harborlight-lab`. State: `/var/lib/harborlight-lab`. HTTP: `127.0.0.1:18765`. Restore test HTTP: `127.0.0.1:18766`, only while the drill process runs. The lab creates no remote login account or password. Its locked `harborapp` service identity cannot log in.

Only operate on these names and paths. The ownership marker must exactly identify Harborlight and synthetic-only data. Do not copy the fault harness onto a client machine. A real engagement needs an approved inventory and recovery console first.

## 2. Repeat the free lab

Open Actions, select **Verify Harborlight operations**, choose **Run workflow**, leave main selected and submit. No secret, payment information or additional account is required. Read the summary after completion. Green CI means compilation, 19 boundary tests, unmarked-host refusal, all 15 live scenarios and evidence hashes completed. A partial table from a failed job is not overall acceptance.

The standard public runner is temporary. The workflow is event-driven and manually runnable; it is not a continuous production monitor or scheduled hosted server.

## 3. Routine audit

```sh
sudo python3 /opt/harborlight-lab/operations/ops.py audit
sudo cat /var/lib/harborlight-lab/reports/latest.md
```

Checks: systemd activity; HTTP health; approved configuration digest; live SQLite integrity/five-order fixture; backup freshness/checksum/integrity/fingerprint; at least 32 MiB filesystem free space. The audit reads the workload and writes controller reports and incident state. It does not restart the app, patch packages, change configuration, rotate credentials or delete files.

Exit 0: checks pass or a valid preview is returned. Exit 2: an audit completed with failed checks. Exit 3: an operation was refused or errored. Check the exit code **and** JSON status. PLAN does not mean a change was applied.

## 4. Service or health failure

1. Read failed checks and next-action text; preserve the timestamped report.
2. Inspect `systemctl status harborlight-app.service` and `journalctl -u harborlight-app.service --since '-15 minutes'`.
3. Resolve any configuration, database, backup or capacity failure first. The controller refuses restart when any of these is unhealthy.
4. Preview with `sudo python3 /opt/harborlight-lab/operations/ops.py remediate`.
5. With the lab change authorized, run `sudo python3 /opt/harborlight-lab/operations/ops.py remediate --apply`.
6. Read post-validation. A systemd restart alone is not recovery: the controller requires health and all six checks to pass.

There is one allowlisted restart, a 60-second cooldown recorded before the attempt, and a nonblocking exclusive lock. It never loops indefinitely. A restart error or failed post-check requires investigation. Do not delete the cooldown file to force repeated attempts; preserve evidence and fix the cause.

## 5. Configuration drift

Compare `app.json` with the approved change record. The application reads its site label and dispatch mode at startup. The audit compares exact file bytes with the protected approved digest; whitespace changes also count as drift.

For an unintended change, restore reviewed approved configuration, then recheck and restart only if needed. For an intentional change, review and validate it, update the change record, then explicitly replace the approved digest through the operator's controlled procedure. Automation never silently approves drift. The exercise restores captured original bytes; it does not redefine approval after an unexpected edit.

## 6. Missing, stale or corrupt backup

```sh
sudo python3 /opt/harborlight-lab/operations/ops.py backup
sudo python3 /opt/harborlight-lab/operations/ops.py audit
```

The online SQLite backup API copies the live database without a raw copy of an open database. The snapshot is staged, inspected, atomically renamed, described by a new manifest, and verified again. The manifest is published after snapshot validation. Failure keeps the previous manifest available. An unreferenced candidate left by interruption is not the active backup.

The lab accepts a latest completed snapshot no older than one hour and rejects a timestamp more than 30 seconds in the future. The stale exercise edits the manifest to two hours ago; it tests the rule without waiting two hours. Never edit timestamps to make an old backup appear fresh. Create a new verified snapshot and investigate the missed schedule.

No automatic deletion or retention rotation is implemented. Inspect capacity and agree a tested retention policy before continuous operation. Local backups cannot protect against disk/host loss. A client engagement needs an owned off-device destination, access policy, recovery objective and independent restore test.

## 7. Isolated restore drill

```sh
sudo python3 /opt/harborlight-lab/operations/ops.py restore-drill
```

This verifies the current manifest, copies the snapshot to a unique database under `restores/`, checks integrity and ordered-record fingerprint, and writes `reports/restore-latest.json`. It never replaces `orders.sqlite`. The acceptance harness additionally starts a separate loopback app on port 18766, compares all five HTTP records with the live app and stops that process.

A damaged candidate is rejected before copying. A successful SQLite open is not complete application recovery. Production cutover, data-loss authorization, write quiescence, DNS/access changes and user acceptance need a separate approved procedure. They were not performed here.

## 8. Capacity failure

Inspect filesystem usage and backup/report growth. Low capacity is reported and blocks restart. There is no automatic deletion. The 32 MiB threshold is a lab safeguard, not a production recommendation. A real threshold must account for growth, temporary workspace, backup volume and maintenance needs.

## 9. Incident events and noise

`control/events.jsonl` records OPEN when a check first fails and RECOVERED when it next passes. `control/incidents.json` stores the failed-check set. Repeating a failure updates its report but adds no duplicate OPEN. A recurrence after recovery opens a new incident.

State is local and unsigned. Losing controller state can cause a new OPEN after rebuilding. No email, chat, SMS or external alert delivery was tested. Agree recipients, hours and channels for client work, then test failure and recovery delivery. Local events are not observed external notifications.

## 10. Recurring timer

The harness writes `harborlight-audit.service` and `harborlight-audit.timer`. The audit-only oneshot protects system paths and writes only owned state. The lab timer starts after two seconds, repeats after five seconds, and has one-second accuracy. At least two new reports and a successful unit exit are observed.

The short interval exists for this test. For a client, agree an interval such as 15 minutes, validate runtime/failure behavior, enable it on a persistent host and test reboot behavior. The timer does not create backups or invoke remediation. Schedule backups separately after agreeing destination and retention. GitHub Actions is the demonstration environment, not a persistent timer host.

## 11. Patch and maintenance review

Inventory OS release, support status, pending security updates and restart requirements. Record approvals, window, backup verification, update results and post-change checks. Cedarfield separately demonstrates update-policy configuration. Harborlight does not execute an unattended patch cycle. An operations report checking service/data/backup state cannot establish patch success.

## 12. Rollback and closeout

The harness stops the two audit units and app unit, removes only the three named unit files, reloads systemd and verifies the app is inactive. Sanitized evidence remains in the checkout for the summary. Runtime files and the locked identity disappear when the hosted runner is discarded. No unrelated unit or firewall rule is changed.

On a persistent approved lab, preserve evidence and inspect ownership first. Stop the timer, then the app. Keep data until its owner authorizes its lifecycle. Avoid broad recursive cleanup against a computed path. Production rollback must account for accepted data changes and needs its own procedure.

## 13. Handover checklist

- Explicit owner, service inventory and approved change record.
- Healthy and failed reports that the operator can interpret.
- Agreed backup destination, freshness, integrity, retention and restore procedure.
- Response authorization, escalation hours and notification recipients.
- Operator can preview a change, explain refusal and validate recovery.
- Scheduler, reboot behavior, patching and rollback tested on the actual host.
- Residual risks and next actions understood; no availability guarantee implied.
