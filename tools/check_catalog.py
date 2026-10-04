#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check catalog.json structure without the external corpus."""
import json
from pathlib import Path
import re
import sys

REQUIRED = {'path', 'aliases', 'sha256', 'size_bytes', 'detected_type', 'source_repository',
            'redistribution', 'local_integrity', 'conversion', 'viewer'}
TYPES = {'CAJ', 'HN', 'C8', 'KDH', 'PDF', 'TEB', 'CAA', 'CAS', 'NH'}
STATUS = {'NOT_RUN', 'PASS', 'FAIL', 'UNSUPPORTED', 'INCOMPLETE_TIMEOUT'}
SHA256 = re.compile(r'[0-9a-f]{64}')


def problems(raw):
    data = json.loads(raw)
    if raw != json.dumps(data, indent=2, ensure_ascii=False) + '\n':
        yield 'catalog: not formatted as 2-space UTF-8 JSON with a trailing newline'
    if data.get('schema_version') != 1 or not isinstance(data.get('samples'), list):
        yield 'catalog: needs schema_version 1 and a samples list'
        return
    hashes, paths = set(), set()
    for index, row in enumerate(data['samples']):
        name = f"row {index} ({row.get('path', '?')})"
        missing = REQUIRED - row.keys()
        if missing:
            yield f'{name}: missing {", ".join(sorted(missing))}'
            continue
        if not ('source_revision' in row or 'source_url' in row):
            yield f'{name}: needs source_revision or source_url'
        if not SHA256.fullmatch(row['sha256']):
            yield f'{name}: sha256 must be 64 lowercase hex digits'
        if not isinstance(row['size_bytes'], int) or row['size_bytes'] <= 0:
            yield f'{name}: size_bytes must be a positive integer'
        if row['detected_type'] not in TYPES:
            yield f'{name}: unknown detected_type {row["detected_type"]!r}'
        for key in ('conversion', 'viewer', 'local_integrity'):
            if row[key] not in STATUS:
                yield f'{name}: unknown {key} {row[key]!r}'
        for path in [row['path'], *row['aliases']]:
            if path.startswith('/') or '..' in Path(path).parts or '\\' in path:
                yield f'{name}: non-canonical path {path!r}'
            if path in paths:
                yield f'{name}: duplicate path {path!r}'
            paths.add(path)
        if row['sha256'] in hashes:
            yield f'{name}: duplicate sha256'
        hashes.add(row['sha256'])


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'catalog.json')
    found = list(problems(path.read_text(encoding='utf-8')))
    for problem in found:
        print(problem)
    print(f'{path.name}: {"FAIL" if found else "PASS"} ({len(found)} problems)')
    return int(bool(found))


if __name__ == '__main__':
    raise SystemExit(main())
