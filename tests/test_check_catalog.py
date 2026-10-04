# SPDX-License-Identifier: MIT
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_catalog

ROW = {'path': 'a.caj', 'aliases': [], 'sha256': 'a' * 64, 'size_bytes': 1, 'detected_type': 'CAJ',
       'source_repository': 'https://example.invalid/r', 'source_revision': 'x',
       'redistribution': 'not_declared', 'local_integrity': 'PASS', 'conversion': 'NOT_RUN',
       'viewer': 'NOT_RUN'}


def check(*rows):
    raw = json.dumps({'schema_version': 1, 'samples': list(rows)}, indent=2, ensure_ascii=False) + '\n'
    return list(check_catalog.problems(raw))


class CatalogCheckTests(unittest.TestCase):
    def test_current_catalog_passes(self):
        raw = (Path(__file__).resolve().parents[1] / 'catalog.json').read_text(encoding='utf-8')
        self.assertEqual(list(check_catalog.problems(raw)), [])

    def test_each_rule_reports_the_row(self):
        cases = [
            (dict(ROW, sha256='A' * 64), 'sha256'),
            (dict(ROW, size_bytes=0), 'size_bytes'),
            (dict(ROW, detected_type='DOC'), 'detected_type'),
            (dict(ROW, conversion='OK'), 'conversion'),
            (dict(ROW, path='../a.caj'), 'non-canonical'),
            ({k: v for k, v in ROW.items() if k != 'viewer'}, 'missing viewer'),
            ({k: v for k, v in ROW.items() if k != 'source_revision'}, 'source_revision or source_url'),
        ]
        for row, message in cases:
            with self.subTest(message):
                self.assertTrue(any(message in p and 'a.caj' in p for p in check(row)), check(row))

    def test_duplicates_and_formatting_fail(self):
        self.assertTrue(any('duplicate sha256' in p for p in check(ROW, dict(ROW, path='b.caj'))))
        self.assertTrue(any('duplicate path' in p for p in check(ROW, dict(ROW, sha256='b' * 64))))
        compact = json.dumps({'schema_version': 1, 'samples': [ROW]})
        self.assertTrue(any('formatted' in p for p in check_catalog.problems(compact)))


if __name__ == '__main__':
    unittest.main()
