import datetime as dt
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from contextlib import closing

MODULE = Path(__file__).resolve().parents[1] / 'operations/ops.py'
spec = importlib.util.spec_from_file_location('ops', MODULE)
ops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)


class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='harborlight-tests-')
        self.root = Path(self.tmp.name)
        (self.root / 'backups').mkdir()
        (self.root / 'control').mkdir()
        self.db = self.root / 'backups/snapshot-20261005T120000Z-deadbeef.sqlite'
        with closing(sqlite3.connect(self.db)) as con:
            con.execute('CREATE TABLE orders(id INTEGER PRIMARY KEY, reference TEXT, status TEXT)')
            con.execute("INSERT INTO orders VALUES(1,'HL-001','Ready')")
            con.commit()
        self.now = dt.datetime(2026, 10, 5, 12, 0, tzinfo=dt.timezone.utc)
        self.manifest = {'file': self.db.name, 'completed_at': self.now.isoformat(),
                         'sha256': ops.digest(self.db), **ops.database_facts(self.db)}
        self.save()

    def tearDown(self):
        self.tmp.cleanup()

    def save(self):
        (self.root / 'backups/latest.json').write_text(json.dumps(self.manifest))

    def test_valid_backup(self):
        self.assertEqual(ops.validate_backup(self.root, self.now)[1]['rows'], 1)

    def test_stale_backup_rejected(self):
        with self.assertRaisesRegex(ValueError, 'stale'):
            ops.validate_backup(self.root, self.now + dt.timedelta(seconds=3601))

    def test_future_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError, 'future'):
            ops.validate_backup(self.root, self.now - dt.timedelta(seconds=31))

    def test_timezone_required(self):
        self.manifest['completed_at'] = '2026-10-05T12:00:00'
        self.save()
        with self.assertRaisesRegex(ValueError, 'timezone'):
            ops.validate_backup(self.root, self.now)

    def test_corrupt_snapshot_rejected(self):
        self.db.write_bytes(b'not a database')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            ops.validate_backup(self.root, self.now)

    def test_manifest_dataset_mismatch_rejected(self):
        self.manifest['rows'] = 9
        self.save()
        with self.assertRaisesRegex(ValueError, 'dataset'):
            ops.validate_backup(self.root, self.now)

    def test_manifest_path_traversal_rejected(self):
        self.manifest['file'] = '../orders.sqlite'
        self.save()
        with self.assertRaisesRegex(ValueError, 'filename'):
            ops.validate_backup(self.root, self.now)

    def test_absolute_path_rejected(self):
        with self.assertRaises(ValueError):
            ops.safe_child(self.root, '/etc/passwd')

    def test_parent_path_rejected(self):
        with self.assertRaises(ValueError):
            ops.safe_child(self.root, '../outside')

    def test_symlink_rejected(self):
        (self.root / 'escape').symlink_to('/tmp', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            ops.safe_child(self.root, 'escape/file')

    def test_missing_database_does_not_create_file(self):
        missing = self.root / 'missing.sqlite'
        with self.assertRaises(ValueError):
            ops.database_facts(missing)
        self.assertFalse(missing.exists())

    def test_empty_business_dataset_rejected(self):
        with closing(sqlite3.connect(self.db)) as con:
            con.execute('DELETE FROM orders')
            con.commit()
        with self.assertRaisesRegex(ValueError, 'empty'):
            ops.database_facts(self.db)

    def test_concurrent_operation_rejected(self):
        with ops.exclusive(self.root):
            with self.assertRaisesRegex(ValueError, 'lock'):
                with ops.exclusive(self.root):
                    self.fail('Second lock acquired')

    def test_atomic_manifest_roundtrip(self):
        target = self.root / 'manifest.json'
        ops.atomic_json(target, {'value': 2})
        ops.atomic_json(target, {'value': 3})
        self.assertEqual(json.loads(target.read_text()), {'value': 3})
        self.assertEqual(list(self.root.glob('*.tmp')), [])

    def test_health_connection_failure(self):
        with patch.object(ops, 'urlopen', side_effect=OSError('offline')):
            self.assertFalse(ops.health('http://127.0.0.1:18765/health'))

    def test_unmarked_or_alternate_root_rejected(self):
        with self.assertRaisesRegex(ValueError, 'dedicated'):
            ops.Operations(self.root)


if __name__ == '__main__':
    unittest.main(verbosity=2)
