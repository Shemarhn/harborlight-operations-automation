"""Execute destructive tests only inside a fresh GitHub-hosted Ubuntu runner."""
from contextlib import closing
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time
from urllib.request import urlopen

REPO = Path(__file__).resolve().parents[1]
ROOT = Path('/var/lib/harborlight-lab')
CODE = Path('/opt/harborlight-lab')
UNIT = 'harborlight-app.service'
ARTIFACT = REPO / 'evidence/run'
CASES = []


def command(*args, check=True):
    return subprocess.run(args, check=check, text=True, capture_output=True, timeout=30)


def cli(operation='audit', apply=False, expected=0):
    args = [sys.executable, str(CODE / 'operations/ops.py'), operation]
    if apply:
        args.append('--apply')
    result = command(*args, check=False)
    if result.returncode != expected:
        raise AssertionError('Unexpected exit for ' + operation + ': ' + result.stdout + result.stderr)
    return json.loads(result.stdout)


def record(name, evidence):
    CASES.append({'scenario': name, 'result': 'PASS', 'observed_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'evidence': evidence})
    print('PASS: ' + name, flush=True)
    (ARTIFACT / 'cases.json').write_text(json.dumps(CASES, indent=2, sort_keys=True) + '\n')


def failed(report):
    return {row['check'] for row in report['checks'] if row['status'] == 'FAIL'}


def wait_health(port=18765):
    for _ in range(40):
        try:
            with urlopen('http://127.0.0.1:' + str(port) + '/health', timeout=1) as response:
                data = json.load(response)
            if data['status'] == 'ok' and data['orders'] == 5:
                return data
        except (OSError, ValueError):
            pass
        time.sleep(0.25)
    raise AssertionError('Application failed health validation')


def install():
    if os.geteuid() != 0 or os.environ.get('GITHUB_ACTIONS') != 'true':
        raise SystemExit('This fault harness requires root on a fresh GitHub Actions runner')
    if ROOT.exists() or CODE.exists():
        raise SystemExit('Refusing to overwrite an existing lab')
    ARTIFACT.mkdir(parents=True, exist_ok=True)
    os.umask(0o077)
    ROOT.mkdir(mode=0o755)
    CODE.mkdir(mode=0o755)
    for part in ('app', 'operations'):
        shutil.copytree(REPO / part, CODE / part)
        (CODE / part).chmod(0o755)
        for source in (CODE / part).glob('*.py'):
            source.chmod(0o644)
    for directory in ('control', 'backups', 'reports', 'restores'):
        (ROOT / directory).mkdir(mode=0o700)
    command('useradd', '--system', '--no-create-home', '--shell', '/usr/sbin/nologin', 'harborapp')
    command('chown', 'root:harborapp', str(ROOT))
    (ROOT / 'LAB.json').write_text(json.dumps({'engagement': 'harborlight', 'synthetic_only': True}))
    (ROOT / 'app.json').write_text(json.dumps({'mode': 'dispatch', 'site': 'Harborlight synthetic dispatch'}))
    (ROOT / 'app.json').chmod(0o640)
    command('chown', 'root:harborapp', str(ROOT / 'app.json'))
    approved = hashlib.sha256((ROOT / 'app.json').read_bytes()).hexdigest()
    (ROOT / 'control/approved-config.sha256').write_text(approved + '\n')
    with closing(sqlite3.connect(ROOT / 'orders.sqlite')) as con:
        con.execute('CREATE TABLE orders(id INTEGER PRIMARY KEY, reference TEXT NOT NULL UNIQUE, status TEXT NOT NULL)')
        con.executemany('INSERT INTO orders VALUES(?,?,?)', [(1,'HL-001','Ready'), (2,'HL-002','Dispatched'), (3,'HL-003','Queued'), (4,'HL-004','Ready'), (5,'HL-005','Queued')])
        con.commit()
    (ROOT / 'orders.sqlite').chmod(0o640)
    command('chown', 'root:harborapp', str(ROOT / 'orders.sqlite'))
    app_unit = '''[Unit]
Description=Harborlight synthetic dispatch workload
[Service]
User=harborapp
Group=harborapp
ExecStart=/usr/bin/python3 /opt/harborlight-lab/app/server.py --database /var/lib/harborlight-lab/orders.sqlite --config /var/lib/harborlight-lab/app.json
Restart=no
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
CapabilityBoundingSet=
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
UMask=0027
[Install]
WantedBy=multi-user.target
'''
    (Path('/etc/systemd/system') / UNIT).write_text(app_unit)
    command('systemctl', 'daemon-reload')
    command('systemctl', 'start', UNIT)
    wait_health()
    return app_unit


def exercise():
    app_unit = install()
    initial_backup = cli('backup')
    healthy = cli()
    assert healthy['status'] == 'PASS'
    record('healthy baseline: six checks', healthy)
    command('systemctl', 'stop', UNIT)
    outage = cli(expected=2)
    assert failed(outage) == {'service', 'health'}
    record('service outage detected', outage)
    plan = cli('remediate')
    assert plan['status'] == 'PLAN' and not plan['changed']
    assert command('systemctl', 'is-active', '--quiet', UNIT, check=False).returncode != 0
    record('dry-run leaves stopped service unchanged', plan)
    repaired = cli('remediate', apply=True)
    assert repaired['changed'] and repaired['post_validation']['status'] == 'PASS'
    record('guarded restart and post-change validation', repaired)
    noop = cli('remediate', apply=True)
    assert not noop['changed']
    record('repeat apply is a no-op when healthy', noop)
    command('systemctl', 'stop', UNIT)
    cooldown = cli('remediate', apply=True, expected=3)
    assert 'cooldown' in cooldown['reason']
    assert command('systemctl', 'is-active', '--quiet', UNIT, check=False).returncode != 0
    record('cooldown blocks a second restart', cooldown)
    command('systemctl', 'start', UNIT)
    wait_health()
    cli()
    original_config = (ROOT / 'app.json').read_bytes()
    (ROOT / 'app.json').write_text(json.dumps({'mode': 'dispatch', 'site': 'UNAPPROVED lab change'}))
    drift = cli(expected=2)
    assert failed(drift) == {'configuration'}
    event_count = len((ROOT / 'control/events.jsonl').read_text().splitlines())
    repeated = cli(expected=2)
    assert repeated['transitions'] == []
    assert len((ROOT / 'control/events.jsonl').read_text().splitlines()) == event_count
    record('configuration drift and incident deduplication', {'first': drift, 'repeat': repeated})
    command('systemctl', 'stop', UNIT)
    refused = cli('remediate', apply=True, expected=3)
    assert 'precondition' in refused['reason']
    assert command('systemctl', 'is-active', '--quiet', UNIT, check=False).returncode != 0
    record('drift blocks remediation before restart', refused)
    (ROOT / 'app.json').write_bytes(original_config)
    command('systemctl', 'start', UNIT)
    wait_health()
    cli()
    manifest_path = ROOT / 'backups/latest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['completed_at'] = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=2)).isoformat()
    manifest_path.write_text(json.dumps(manifest))
    stale = cli(expected=2)
    assert failed(stale) == {'backup'}
    new_backup = cli('backup')
    assert cli()['status'] == 'PASS'
    record('stale backup detected and replaced by verified snapshot', {'failure': stale, 'replacement': new_backup})
    corrupt_file = ROOT / 'backups' / new_backup['file']
    corrupt_file.write_bytes(b'controlled corruption in disposable synthetic lab')
    corrupt = cli(expected=2)
    assert failed(corrupt) == {'backup'}
    restore_refusal = cli('restore-drill', expected=3)
    assert 'checksum' in restore_refusal['reason']
    wait_health()
    record('corrupt backup rejected; live workload preserved', {'audit': corrupt, 'restore': restore_refusal})
    good_backup = cli('backup')
    drill = cli('restore-drill')
    assert drill['rows'] == 5 and drill['fingerprint'] == good_backup['fingerprint'] and not drill['live_database_overwritten']
    restored_database = sorted((ROOT / 'restores').glob('*.sqlite'))[-1]
    drill_process = subprocess.Popen([sys.executable, str(CODE / 'app/server.py'), '--database', str(restored_database), '--config', str(ROOT / 'app.json'), '--port', '18766'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        restored_health = wait_health(18766)
        with urlopen('http://127.0.0.1:18766/orders', timeout=2) as response:
            restored_orders = json.load(response)['orders']
        with urlopen('http://127.0.0.1:18765/orders', timeout=2) as response:
            live_orders = json.load(response)['orders']
        assert restored_orders == live_orders and len(restored_orders) == 5
        record('isolated restore serves identical five orders through HTTP', {'drill': drill, 'restored_health': restored_health, 'records': restored_orders})
    finally:
        drill_process.terminate()
        drill_process.wait(timeout=5)
    spec = importlib.util.spec_from_file_location('harbor_ops', CODE / 'operations/ops.py')
    ops = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ops)
    with ops.exclusive(ROOT):
        locked = cli(expected=3)
        assert 'lock' in locked['reason']
    record('overlapping operation refused', locked)
    ops_unit = '''[Unit]
Description=Harborlight read-only workload audit
[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /opt/harborlight-lab/operations/ops.py audit
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/harborlight-lab
CapabilityBoundingSet=
UMask=0077
'''
    timer_unit = '''[Unit]
Description=Accelerated Harborlight lab audit timer
[Timer]
OnActiveSec=2s
OnUnitActiveSec=5s
AccuracySec=1s
[Install]
WantedBy=timers.target
'''
    (Path('/etc/systemd/system/harborlight-audit.service')).write_text(ops_unit)
    (Path('/etc/systemd/system/harborlight-audit.timer')).write_text(timer_unit)
    command('systemctl', 'daemon-reload')
    before = len(list((ROOT / 'reports').glob('20*.json')))
    command('systemctl', 'start', 'harborlight-audit.timer')
    for _ in range(30):
        time.sleep(1)
        after = len(list((ROOT / 'reports').glob('20*.json')))
        if after - before >= 2:
            break
    assert after - before >= 2
    timer_state = command('systemctl', 'show', 'harborlight-audit.service', '-p', 'Result', '-p', 'ExecMainStatus').stdout
    assert 'Result=success' in timer_state and 'ExecMainStatus=0' in timer_state
    command('systemctl', 'stop', 'harborlight-audit.timer')
    record('two automatic systemd timer audits observed', {'automatic_reports': after - before, 'unit_result': timer_state, 'lab_interval_seconds': 5})
    final = cli()
    assert final['status'] == 'PASS'
    record('final operational state healthy', final)
    for file in ('latest.json', 'latest.md', 'restore-latest.json'):
        shutil.copyfile(ROOT / 'reports' / file, ARTIFACT / file)
    shutil.copyfile(ROOT / 'control/events.jsonl', ARTIFACT / 'events.jsonl')
    (ARTIFACT / 'units.txt').write_text(app_unit + '\n' + ops_unit + '\n' + timer_unit)
    shutil.copyfile(ROOT / 'backups/latest.json', ARTIFACT / 'backup-manifest.json')
    context = {'environment': 'GitHub-hosted Ubuntu 24.04 ephemeral runner', 'synthetic_only': True,
               'run_id': os.environ.get('GITHUB_RUN_ID'), 'source_commit': os.environ.get('GITHUB_SHA'),
               'observed_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'outbound_notification_tested': False,
               'paid_resources_created': False}
    (ARTIFACT / 'context.json').write_text(json.dumps(context, indent=2) + '\n')


def cleanup():
    if not ROOT.exists():
        return
    for unit in ('harborlight-audit.timer', 'harborlight-audit.service', UNIT):
        command('systemctl', 'stop', unit, check=False)
        Path('/etc/systemd/system', unit).unlink(missing_ok=True)
    command('systemctl', 'daemon-reload')
    if CASES:
        assert command('systemctl', 'is-active', '--quiet', UNIT, check=False).returncode != 0
        record('rollback removes lab units and stops workload', {'application_active': False, 'lab_units_removed': True, 'other_units_changed': False})
    if ARTIFACT.exists():
        lines = ['# Executed Harborlight acceptance results', '', '| Scenario | Observed result |', '|---|---|']
        lines += ['| ' + row['scenario'] + ' | ' + row['result'] + ' |' for row in CASES]
        lines += ['', 'Each PASS is an assertion that completed in the named run. A failed job is not a completed acceptance run.', '',
                  'This is a disposable synthetic lab. No paid-client, production SLA, off-host alert delivery or continuous uptime claim.']
        (ARTIFACT / 'acceptance.md').write_text('\n'.join(lines) + '\n')
        hashes = []
        for file in sorted(ARTIFACT.iterdir()):
            if file.is_file() and file.name != 'SHA256SUMS.txt':
                hashes.append(hashlib.sha256(file.read_bytes()).hexdigest() + '  ' + file.name)
        (ARTIFACT / 'SHA256SUMS.txt').write_text('\n'.join(hashes) + '\n')
        for file in ARTIFACT.iterdir():
            file.chmod(0o644)
        ARTIFACT.chmod(0o755)


if __name__ == '__main__':
    try:
        exercise()
    finally:
        cleanup()
