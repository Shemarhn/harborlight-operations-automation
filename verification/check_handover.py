"""Validate the complete public handover, not only application code."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
markdown = sorted(ROOT.rglob('*.md'))
link_count = 0
for file in markdown:
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', file.read_text(encoding='utf-8')):
        if target.startswith(('https://', 'http://', 'mailto:', '#')):
            continue
        target = target.split('#', 1)[0].split('?', 1)[0].strip('<>')
        if not target:
            continue
        resolved = (file.parent / target).resolve()
        assert ROOT in resolved.parents, 'Link escapes repository: ' + target
        assert resolved.exists(), str(file.relative_to(ROOT)) + ': missing ' + target
        link_count += 1

namespace = '{http://www.w3.org/2000/svg}'
for file in ROOT.rglob('*.svg'):
    svg = ET.fromstring(file.read_text(encoding='utf-8'))
    assert svg.find(namespace + 'title') is not None
    assert svg.find(namespace + 'desc') is not None
    assert svg.get('viewBox')
    assert not list(svg.iter(namespace + 'script')), 'Active script in public diagram'

observed = ROOT / 'evidence/observed'
manifest = (observed / 'SHA256SUMS.txt').read_text().splitlines()
assert len(manifest) == 4
for line in manifest:
    expected, filename = line.split('  ', 1)
    assert filename in {'cases.json', 'latest.json', 'restore-latest.json', 'context.json'}
    assert hashlib.sha256((observed / filename).read_bytes()).hexdigest() == expected, filename + ': hash mismatch'
cases = json.loads((observed / 'cases.json').read_text())
assert len(cases) == 15 and all(case['result'] == 'PASS' for case in cases)
context = json.loads((observed / 'context.json').read_text())
assert context['synthetic_only'] and context['run_id'] == '37343589687'
assert context['source_commit'] == '112ab9532c0b2f6bac99a13bcaf9fbccc480c289'
latest = json.loads((observed / 'latest.json').read_text())
assert latest == next(case['evidence'] for case in cases if case['scenario'] == 'final operational state healthy')
assert len(latest['checks']) == 6 and all(row['status'] == 'PASS' for row in latest['checks'])
restore = json.loads((observed / 'restore-latest.json').read_text())
assert restore['rows'] == 5 and restore['integrity'] == 'ok' and not restore['live_database_overwritten']

credential = re.compile('-----BEGIN ' + r'(?:RSA |OPENSSH |EC )?PRIVATE KEY-----|AKIA[A-Z0-9]{16}|gh[pous]_[A-Za-z0-9]{30,}')
for file in ROOT.rglob('*'):
    if '.git' in file.parts or file.suffix not in {'.py', '.md', '.yml', '.json', '.txt', '.svg'}:
        continue
    assert not credential.search(file.read_text(encoding='utf-8')), 'Credential pattern found: ' + str(file.relative_to(ROOT))
print('PASS: ' + str(len(markdown)) + ' Markdown documents; ' + str(link_count) + ' local links; accessible SVG; four evidence hashes; 15-case provenance; selected credential patterns')
