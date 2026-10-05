# Implementation and verification design

## Repository map

| Path | Responsibility |
|---|---|
| app/server.py | Standard-library HTTP app; read-only SQLite queries; loopback /health and /orders. |
| operations/ops.py | Checks, reports, online snapshots, isolated restore, incident state and guarded restart. |
| lab/exercise.py | Root-only disposable Ubuntu fixture, controlled faults, assertions, timer exercise and cleanup. |
| tests/test_operations.py | Input, backup, path, locking and failure-boundary tests. |
| .github/workflows/verify.yml | Free standard Ubuntu runner, read-only token, test/lab execution and public summary/logs. |
| verification/ACCEPTANCE.md | Scenario-to-evidence mapping and repeat criteria. |
| evidence/ | Provenance, retained observed output and the boundaries of each artifact. |
| docs/ | Architecture, decisions, risk, case study, response runbook and recurring care. |

## Fixture installation

The harness requires root and GITHUB_ACTIONS=true, then refuses existing /var/lib/harborlight-lab or /opt/harborlight-lab paths. A process-local ownership flag prevents its finally block from cleaning an existing lab it refused to create. Files are root-owned with a restrictive umask; app directories are explicitly made traversable, and only the app configuration/database are group-readable by harborapp. The service identity is locked and has no home or login shell.

The SQLite fixture contains exactly five synthetic reference/status rows. The app starts under systemd as harborapp with no capabilities, no new privileges, private temporary space and protected system/home paths. Restart=no is intentional: an injected outage remains stopped until the guarded operation or explicit lab repair occurs.

## CLI contract

Commands: audit (default), backup, restore-drill and remediate. --apply is legal only with remediate. Root and explicit apply are required to execute the restart. There is no target-host, target-unit, arbitrary-path or arbitrary-shell-command argument. An exact fixed ownership marker is required before operations, and every CLI command acquires the same nonblocking file lock.

| Return | Meaning |
|---|---|
| 0 | PASS, healthy no-op, or valid PLAN; inspect JSON status. |
| 2 | Completed audit found failed checks. |
| 3 | Refused/errored operation, including invalid ownership, lock, cooldown or failed preconditions. |

Operational errors are returned as small JSON messages. Malformed manifest objects, filenames and timestamps receive explicit refusal. Missing source databases are opened only after an existence check and through SQLite read-only URI mode, preventing accidental creation of an empty source.

## Six audit checks

| Check | Exact lab rule | Failure response |
|---|---|---|
| service | systemctl is-active for harborlight-app.service. | Inspect service and recent journal; preview only after other state is healthy. |
| health | HTTP 200, JSON status=ok and nonempty order count within a two-second request timeout. | Investigate app/database; no HTTP-only blind restart. |
| configuration | SHA256 of startup app.json equals the approved digest. | Review drift; never automatically replace approval. |
| database | SQLite integrity_check=ok, expected orders schema and exactly five fixture rows. | Inspect data and recovery requirements; block restart. |
| backup | Valid manifest/name/time, SHA256, SQLite integrity, count and ordered-record fingerprint; five rows. | Create a new valid backup and investigate missed/damaged snapshot. |
| capacity | Actual filesystem free bytes are at least 32 MiB. | Investigate usage; block restart; no automatic deletion. |

The five-row rule is deliberately fixture-specific. It is not a general client application invariant. Valid but semantically wrong business records can pass integrity/count checks; production validation must reflect actual business requirements.

## Snapshot publication protocol

1. Confirm source existence and readable schema/integrity/nonempty data.
2. Choose a unique timestamp/UUID snapshot name in the owned backups directory.
3. Use SQLite's online backup API into a staging .partial file.
4. Validate the candidate and compute its ordered-row fingerprint.
5. Rename it to the final snapshot name.
6. Atomically publish a JSON manifest with filename, completion UTC, SHA256, row count, fingerprint and integrity result.
7. Revalidate the published manifest and snapshot.

JSON publication uses an exclusive temporary file, flush/fsync, and os.replace. Temporary JSON/staging files are removed in finally blocks. Crash durability of the parent directory and underlying storage is not guaranteed by this implementation. An interruption after final snapshot rename but before manifest update can leave an unreferenced candidate; it does not change the approved latest pointer. No retention deletion is performed.

Freshness is maximum one hour; a timestamp more than 30 seconds ahead is rejected. Snapshot filenames are constrained to the generated pattern. Relative traversal, absolute paths and symlinks below the fixed lab root are rejected. These are local path controls, not protection against a malicious root operator.

## Isolated restoration

The drill verifies the selected snapshot, copies it to a unique restores/drill-*.sqlite path and compares integrity/count/fingerprint with the manifest. The CLI writes a restore report and has no live database replacement operation. The harness starts a second app on loopback 18766 against that copy, compares all HTTP rows with the running original and stops the second process. The drill proves one observed application's data can be served after isolated restoration; it does not establish production cutover timing or data-loss objectives.

## Restart control

Remediate audits first. No failures means changed=false. Only service and/or health failures qualify. Any configuration/database/backup/capacity failure produces a refusal before restart. Preview returns PLAN and changed=false. Apply checks root and a persisted 60-second cooldown, writes the attempt timestamp, invokes only systemctl restart harborlight-app.service, polls for service/HTTP recovery, then audits all six checks. Failed post-validation escalates through an error, not an unbounded retry.

The lock coordinates CLI operations. Direct method calls in the owned test harness are used only to hold the lock for the concurrency assertion. There is no distributed coordination or universal host-remediation abstraction.

## Reports and incident state

Each audit writes timestamp/UUID JSON, latest JSON, latest Markdown and the current failed-check set. OPEN records set difference from the previous audit; RECOVERED records previously failed checks that now pass. Repeated failures generate reports without duplicate OPEN events. These are local state transitions, not delivered remote alerts.

## Scheduler exercise

The harness installs an audit-only oneshot plus an accelerated timer: first activation after two seconds, then five-second intervals. It records the report count before starting, waits up to 30 seconds for two new reports, verifies Result=success and ExecMainStatus=0, then stops the timer. The final audit and cleanup follow. Timer behavior after reboot, long operating periods or suspended hosts is not established.

## Evidence and CI

The workflow compiles Python; runs boundary tests; checks that an unmarked host is refused; executes all 15 live scenarios; validates generated SHA256 sums and scenario count; prints a compact sanitized record for each case; and adds the acceptance and final report to the job summary. No artifact upload/cache step remains and repository access is contents-read only.

Generated evidence contains selected synthetic outcomes, public run/commit identifiers, UTC timestamps, fingerprints, checksums and the three owned unit definitions. It excludes runtime databases, environment dumps, credentials, unrelated process lists, network inventory and personal data. The evidence guide links the source run and distinguishes a retained observed copy from a cryptographically authenticated attestation.
