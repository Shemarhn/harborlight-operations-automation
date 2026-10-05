# Safe operation and reporting

This repository is a synthetic disposable lab. It accepts no arbitrary remote target, unit name or production path. The fault harness requires root on a fresh GitHub Actions runner and refuses existing lab directories. It must never be deployed as a fault-injection script on a client server.

Public source and evidence contain synthetic data only. Do not publish passwords, keys, tokens, cookies, environment dumps, client records, Terraform state or runtime database exports. Review new evidence before adding it. The application is loopback-only and read-only; no remote login account or authentication secret is created.

The CLI requires the fixed lab root, exact ownership marker and path checks. It defaults to audit; remediation defaults to preview. Explicit restart applies only to the owned app and requires healthy non-service checks, a lock, root and cooldown. These controls do not protect against a malicious privileged host operator.

For a suspected issue, email [shemarmarks.tech@gmail.com](mailto:shemarmarks.tech@gmail.com) with the source revision, reproduction using synthetic data, expected result and observed result. Do not send credentials or sensitive records. There is no bug-bounty or response-time commitment.
