#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Verify local corpus identity; this is not a conversion test."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    catalog = json.loads((Path(__file__).resolve().parents[1] / 'catalog.json').read_text())
    failed = 0
    seen = set()
    for row in catalog['samples']:
        digest = row['sha256']
        if digest in seen:
            raise ValueError('Duplicate catalog SHA-256: ' + digest)
        seen.add(digest)
        path = (root / row['path']).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Path outside corpus root')
        try:
            size = 0
            actual = hashlib.sha256()
            with path.open('rb') as source:
                while chunk := source.read(262144):
                    size += len(chunk)
                    actual.update(chunk)
            status = 'PASS' if size == row['size_bytes'] and actual.hexdigest() == digest else 'FAIL'
        except FileNotFoundError:
            status = 'NOT_RUN'
        except OSError:
            status = 'FAIL'
        print(status, row['path'])
        failed += status != 'PASS'
    print(f"Integrity: {len(seen) - failed}/{len(seen)} passed; compatibility: NOT_RUN")
    return int(failed != 0)


if __name__ == '__main__':
    raise SystemExit(main())
