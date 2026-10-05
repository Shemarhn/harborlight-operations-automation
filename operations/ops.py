"""Harborlight lab operations. No third-party Python dependencies."""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import time
import uuid
from contextlib import contextmanager, closing
from urllib.request import urlopen

ROOT = Path('/var/lib/harborlight-lab')
UNIT = 'harborlight-app.service'
UTC = dt.timezone.utc
MIN_FREE = 32 * 1024 * 1024
MAX_BACKUP_AGE = 3600
COOLDOWN = 60


def utcnow():
    return dt.datetime.now(UTC)


def stamp():
    return utcnow().isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path, value):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('x') as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def safe_child(root, relative):
    path = root / relative
    if Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise ValueError('Unsafe relative path')
    cursor = path
    while cursor != root:
        if cursor.is_symlink():
            raise ValueError('Symlink rejected')
        cursor = cursor.parent
    if root.is_symlink() or root.resolve() not in path.resolve().parents:
        raise ValueError('Path escapes lab root')
    return path


def database_facts(path):
    if not path.is_file():
        raise ValueError('Database missing')
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as con:
        if con.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('SQLite integrity failed')
        rows = con.execute('SELECT id, reference, status FROM orders ORDER BY id').fetchall()
    if not rows:
        raise ValueError('Synthetic business dataset is empty')
    fingerprint = hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode()).hexdigest()
    return {'integrity': 'ok', 'rows': len(rows), 'fingerprint': fingerprint}


def validate_backup(root, now=None):
    now = now or utcnow()
    manifest = json.loads(safe_child(root, 'backups/latest.json').read_text())
    filename = manifest['file']
    if not re.fullmatch(r'snapshot-[0-9TZ]+-[a-f0-9]{8}\.sqlite', filename):
        raise ValueError('Invalid backup filename')
    created = dt.datetime.fromisoformat(manifest['completed_at'])
    if created.tzinfo is None:
        raise ValueError('Backup timestamp must have timezone')
    age = (now - created).total_seconds()
    if age < -30 or age > MAX_BACKUP_AGE:
        raise ValueError('Backup is stale or timestamp is in the future')
    candidate = safe_child(root, 'backups/' + filename)
    if digest(candidate) != manifest['sha256']:
        raise ValueError('Backup checksum mismatch')
    facts = database_facts(candidate)
    if facts['fingerprint'] != manifest['fingerprint'] or facts['rows'] != manifest['rows']:
        raise ValueError('Backup dataset does not match manifest')
    return candidate, {**facts, 'age_seconds': round(age, 3), 'sha256': manifest['sha256']}


def health(url):
    try:
        with urlopen(url, timeout=2) as response:
            payload = json.load(response)
            return response.status == 200 and payload.get('status') == 'ok' and payload.get('orders', 0) > 0
    except (OSError, ValueError, TypeError, AttributeError):
        return False


def service_active():
    return subprocess.run(['systemctl', 'is-active', '--quiet', UNIT], timeout=5).returncode == 0


@contextmanager
def exclusive(root):
    with safe_child(root, 'control/operation.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError('Another operation holds the lock') from error
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


class Operations:
    def __init__(self, root=ROOT):
        if root != ROOT or root.is_symlink():
            raise ValueError('Only the dedicated Harborlight lab root is allowed')
        marker = json.loads(safe_child(root, 'LAB.json').read_text())
        if marker != {'engagement': 'harborlight', 'synthetic_only': True}:
            raise ValueError('Owned synthetic lab marker required')
        self.root = root
        for directory in ('backups', 'control', 'reports', 'restores'):
            safe_child(root, directory).mkdir(exist_ok=True)

    def audit(self):
        checks = []
        def record(name, test, success, failure):
            try:
                passed = bool(test())
            except (OSError, ValueError, KeyError, sqlite3.Error):
                passed = False
            checks.append({'check': name, 'status': 'PASS' if passed else 'FAIL',
                           'detail': success if passed else failure})
        record('service', service_active, 'Owned systemd service is active', 'Service is inactive; investigate before restarting')
        record('health', lambda: health('http://127.0.0.1:18765/health'), 'HTTP health and nonempty dataset verified', 'HTTP health failed; inspect service and database')
        record('configuration', lambda: digest(safe_child(self.root, 'app.json')) == safe_child(self.root, 'control/approved-config.sha256').read_text().strip(),
               'Configuration matches approved digest', 'Configuration drift; compare with approved change record')
        record('database', lambda: database_facts(safe_child(self.root, 'orders.sqlite'))['rows'] == 5,
               'Live SQLite integrity and five synthetic orders verified', 'Live database failed integrity or expected dataset check')
        record('backup', lambda: validate_backup(self.root)[1]['rows'] == 5,
               'Backup freshness, SHA256, SQLite integrity and dataset verified', 'Backup missing, stale, damaged or inconsistent; create and verify a new snapshot')
        record('capacity', lambda: shutil.disk_usage(self.root).free >= MIN_FREE,
               'At least 32 MiB free on lab filesystem', 'Low free space; investigate usage; no automatic deletion')
        failed = sorted(row['check'] for row in checks if row['status'] == 'FAIL')
        state_path = safe_child(self.root, 'control/incidents.json')
        previous = json.loads(state_path.read_text()) if state_path.exists() else []
        events = []
        for name in sorted(set(failed) - set(previous)):
            events.append({'at': stamp(), 'check': name, 'transition': 'OPEN'})
        for name in sorted(set(previous) - set(failed)):
            events.append({'at': stamp(), 'check': name, 'transition': 'RECOVERED'})
        if events:
            with safe_child(self.root, 'control/events.jsonl').open('a') as stream:
                for event in events:
                    stream.write(json.dumps(event, sort_keys=True) + '\n')
        atomic_json(state_path, failed)
        result = {'engagement': 'synthetic Harborlight', 'observed_at': stamp(),
                  'status': 'PASS' if not failed else 'FAIL', 'checks': checks, 'transitions': events}
        run_id = utcnow().strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
        atomic_json(safe_child(self.root, 'reports/' + run_id + '.json'), result)
        atomic_json(safe_child(self.root, 'reports/latest.json'), result)
        lines = ['# Harborlight operational report', '', 'Synthetic Ubuntu lab; point-in-time observation.', '',
                 'Observed UTC: ' + result['observed_at'], '', '**Overall: ' + result['status'] + '**', '',
                 '| Check | Result | Evidence / next action |', '|---|---|---|']
        lines += ['| {check} | {status} | {detail} |'.format(**row) for row in checks]
        lines += ['', '## Incident transitions', '']
        lines += [event['check'] + ': ' + event['transition'] for event in events] or ['No new transition. Repeated failures remain visible in the table.']
        lines += ['', '## Limits', '', 'Local checks and local backups. No off-host alert delivery, immutable backup, SLA, RPO or production uptime measurement. Automatic remediation is restricted to one owned service and requires explicit apply mode.']
        safe_child(self.root, 'reports/latest.md').write_text('\n'.join(lines) + '\n')
        return result

    def backup(self):
        source = safe_child(self.root, 'orders.sqlite')
        database_facts(source)
        filename = 'snapshot-' + utcnow().strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8] + '.sqlite'
        final = safe_child(self.root, 'backups/' + filename)
        staging = final.with_suffix('.partial')
        try:
            with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as live:
                with closing(sqlite3.connect(staging)) as target:
                    live.backup(target)
            facts = database_facts(staging)
            os.replace(staging, final)
            manifest = {'file': filename, 'completed_at': stamp(), 'sha256': digest(final), **facts}
            atomic_json(safe_child(self.root, 'backups/latest.json'), manifest)
            validate_backup(self.root)
            return {'status': 'PASS', 'operation': 'backup', **manifest}
        finally:
            staging.unlink(missing_ok=True)

    def restore_drill(self):
        source, expected = validate_backup(self.root)
        destination = safe_child(self.root, 'restores/drill-' + uuid.uuid4().hex + '.sqlite')
        shutil.copyfile(source, destination)
        actual = database_facts(destination)
        if actual['fingerprint'] != expected['fingerprint']:
            raise ValueError('Restore dataset mismatch')
        result = {'status': 'PASS', 'operation': 'isolated-restore', 'live_database_overwritten': False, **actual}
        atomic_json(safe_child(self.root, 'reports/restore-latest.json'), result)
        return result

    def remediate(self, apply=False):
        before = self.audit()
        failures = {row['check'] for row in before['checks'] if row['status'] == 'FAIL'}
        if not failures:
            return {'status': 'PASS', 'action': 'none', 'changed': False}
        if failures - {'service', 'health'}:
            raise ValueError('Restart refused: configuration, data, backup or capacity precondition failed')
        if not apply:
            return {'status': 'PLAN', 'action': 'restart ' + UNIT, 'changed': False}
        if os.geteuid() != 0:
            raise ValueError('Explicit lab apply requires root')
        history_path = safe_child(self.root, 'control/remediation.json')
        history = json.loads(history_path.read_text()) if history_path.exists() else {}
        if time.time() - history.get('last_attempt_epoch', 0) < COOLDOWN:
            raise ValueError('Restart refused: 60-second cooldown')
        atomic_json(history_path, {'last_attempt_epoch': time.time(), 'at': stamp(), 'unit': UNIT})
        subprocess.run(['systemctl', 'restart', UNIT], check=True, timeout=15)
        for _ in range(20):
            if service_active() and health('http://127.0.0.1:18765/health'):
                break
            time.sleep(0.25)
        after = self.audit()
        if after['status'] != 'PASS':
            raise ValueError('Restart completed but post-change checks failed; escalate')
        return {'status': 'PASS', 'action': 'restart ' + UNIT, 'changed': True, 'post_validation': after}


def main():
    parser = argparse.ArgumentParser(description='Guarded synthetic-lab operations; no arbitrary remote hosts or commands')
    parser.add_argument('operation', choices=('audit', 'backup', 'restore-drill', 'remediate'), nargs='?', default='audit')
    parser.add_argument('--apply', action='store_true', help='Explicitly permit one guarded service restart')
    args = parser.parse_args()
    os.umask(0o077)
    try:
        if args.apply and args.operation != 'remediate':
            raise ValueError('--apply is only valid for remediate')
        ops = Operations()
        with exclusive(ops.root):
            result = {'audit': ops.audit, 'backup': ops.backup, 'restore-drill': ops.restore_drill,
                      'remediate': lambda: ops.remediate(args.apply)}[args.operation]()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2 if result['status'] == 'FAIL' else 0
    except (OSError, ValueError, KeyError, sqlite3.Error, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'ERROR', 'reason': str(error)}))
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
