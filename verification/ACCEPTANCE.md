# Acceptance criteria and repeat procedure

Source: [accepted Ubuntu run](https://github.com/Shemarhn/harborlight-operations-automation/actions/runs/37343589687), commit 112ab9532c0b2f6bac99a13bcaf9fbccc480c289. All 15 scenarios below were observed as PASS; the full outcome and UTC for each are retained in [cases.json](../evidence/observed/cases.json).

| ID | Executed scenario | Result |
|---|---|---|
| A01 | healthy baseline: six checks | PASS |
| A02 | service outage detected | PASS |
| A03 | dry-run leaves stopped service unchanged | PASS |
| A04 | guarded restart and post-change validation | PASS |
| A05 | repeat apply is a no-op when healthy | PASS |
| A06 | cooldown blocks a second restart | PASS |
| A07 | configuration drift and incident deduplication | PASS |
| A08 | drift blocks remediation before restart | PASS |
| A09 | stale backup detected and replaced by verified snapshot | PASS |
| A10 | corrupt backup rejected; live workload preserved | PASS |
| A11 | isolated restore serves identical five orders through HTTP | PASS |
| A12 | overlapping operation refused | PASS |
| A13 | two automatic systemd timer audits observed | PASS |
| A14 | final operational state healthy | PASS |
| A15 | rollback removes lab units and stops workload | PASS |

## Acceptance meaning

The healthy workload must pass six checks. A stopped service must fail service/health. Preview must preserve stopped state. Explicit guarded apply must restore health, while healthy repetition changes nothing. Cooldown, overlap and bad non-service prerequisites must refuse the operation. Drift must fail without duplicate events. Stale/corrupt snapshots must fail, and corrupt restoration must stop before data copying. A new backup must validate, and the separate recovered application must serve five matching orders. At least two timer reports must be created automatically. Final checks must pass before the three owned units are stopped/removed.

Failures are injected only into the synthetic disposable lab. The stale test edits a timestamp; it does not represent a real two-hour missed backup. The corruption test edits an owned snapshot; it does not damage the live database. The configuration fault is an owned fixture edit; it is not a reported client incident.

## Automated boundaries

The successful run reports **19 tests**, covering valid/stale/future/naive-time/corrupt/dataset-mismatched/malformed backups; filename type/traversal; absolute/parent/symlink path rejection; missing/empty database behavior; operation locking; atomic JSON replacement; failed HTTP; and rejection of an alternate unmarked root. Compilation and an unmarked-host CLI refusal also pass.

## Repeat

Use Actions → Verify Harborlight operations → Run workflow → main. Read the complete job conclusion, acceptance table and final report. Do not infer overall acceptance from a partial table in a failed run. No paid service, secret or separate account is required. The fault harness is intentionally unsuitable for production execution.

The workflow generates fresh run-specific timestamps and hashes. The retained source run is historical evidence, not a promise that all future runs pass. Run history remains visible, and source changes require validation again.

## Planned / not observed

Off-device backup, remote alert delivery, retained monthly trend, reboot behavior, low-disk live fault, unattended patching and production cutover were not executed. No SLA, production uptime, measured RPO or guaranteed recovery duration is inferred. [Risk register](../docs/RISK-ASSESSMENT.md) and [evidence guide](../evidence/README.md) explain the residual exposure.
