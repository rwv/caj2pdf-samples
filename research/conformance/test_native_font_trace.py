# SPDX-License-Identifier: MIT
"""Original controls exercise false associations, missing coverage and limits."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cajviewer'))
from native_font_trace import analyze, agree, SIZES
from native_font_controls import document, generate


def records():
    rows = []
    def add(op, a, b, size, depth=0):
        rows.append([len(rows), len(rows) * 100, 7, 8, op, '0x123',
                     'HGBZ_CNKI', a, b, 0, size, size, depth])
    for size in SIZES:
        add('cmap', 65, 9, size)  # Ordinary font probe, not a document use.
        add('load', 9, 1, size)
        for alias, gid in [(200, 2), (201, 3)]:
            add('cmap', alias, gid, size)
            add('cmap', 66, 4, size, 1)  # Nested auto-hinter lookup.
            add('load', gid, 75785, size, 1)
            add('load', gid, 65548, size)
    return rows


class TraceTests(unittest.TestCase):
    def analyze(self, rows):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ft-events.tsv'
            path.write_text(''.join('\t'.join(map(str, row)) + '\n' for row in rows))
            return analyze(path, ['a0c1', 'a0c2'], 'HGBZ_CNKI')

    def test_probes_and_nested_calls_do_not_become_document_mappings(self):
        got = self.analyze(records())
        self.assertEqual(got['render_loads'], 10)
        self.assertEqual(got['nested_events'], 20)
        self.assertEqual(got['mappings'], [
            {'native_code': 'a0c1', 'cmap_argument': 200, 'glyph_id': 2},
            {'native_code': 'a0c2', 'cmap_argument': 201, 'glyph_id': 3}])

    def test_lost_nesting_information_is_refused(self):
        rows = records()
        for row in rows:
            row[12] = 0
        with self.assertRaisesRegex(ValueError, 'unpaired'):
            self.analyze(rows)

    def test_ambiguous_incomplete_failed_and_unmeasured_records_are_refused(self):
        for index, column, value in [(5, 7, 4), (5, 10, 30), (5, 9, 6),
                                     (5, 3, 99), (5, 5, '0x456'),
                                     (5, 6, 'different'), (5, 0, 90),
                                     (5, 8, 1), (5, 7, 0)]:
            with self.subTest(index=index, column=column, value=value):
                rows = records(); rows[index][column] = value
                with self.assertRaises(ValueError):
                    self.analyze(rows)
        with self.assertRaises(ValueError):
            self.analyze(records()[:-1])
        rows = records(); rows[-1][7] = 8; rows[-2][7] = 8; rows[-4][8] = 8
        with self.assertRaisesRegex(ValueError, 'across sizes'):
            self.analyze(rows)

    def test_reversed_and_isolated_observations_must_agree(self):
        full = self.analyze(records()); reverse = copy.deepcopy(full)
        reverse['mappings'].reverse()
        isolated = copy.deepcopy(full); isolated['mappings'] = isolated['mappings'][:1]
        self.assertEqual(agree([full, reverse, isolated]), 2)
        isolated['mappings'][0]['glyph_id'] = 4
        with self.assertRaisesRegex(ValueError, 'disagreement'):
            agree([full, reverse, isolated])

    def test_limit_truncation_old_schema_and_duplicate_codes_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ft-events.tsv'; path.write_text('x\n')
            for content in ['', 'x', 'x' * 513 + '\n', '\t'.join(map(str, records()[0][:-1])) + '\n']:
                path.write_text(content)
                with self.assertRaises(ValueError):
                    analyze(path, ['a0c1'], 'HGBZ_CNKI')
            path.write_text('x\n'); (path.parent / 'ft-limit').touch()
            with self.assertRaisesRegex(ValueError, 'limit'):
                analyze(path, ['a0c1'], 'HGBZ_CNKI')
            with self.assertRaisesRegex(ValueError, 'codes'):
                analyze(path, ['a0c1', 'a0c1'], 'HGBZ_CNKI')

    def test_original_generator_bounds_and_all_cohorts(self):
        import hashlib
        import json
        self.assertEqual(hashlib.sha256(document(list(range(0xa0c1, 0xa0db)))).hexdigest(),
                         'f703d957c3cc9eeff5aaa3974e299a6523d8fdbeb05e2f166e70db5509886315')
        for codes, options in [([], {}), ([0xa0c1] * 2, {}), ([0xa080], {}),
                               ([0xa0c1], {'mode': True}), ([0xa0c1], {'state': 5}),
                               (list(range(0xa0b0, 0xa0ee)), {'step': 600})]:
            with self.assertRaises(ValueError):
                document(codes, **options)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'controls'; generate(root)
            cases = [case for path in root.glob('*.json') for case in json.loads(path.read_text())]
            self.assertEqual(len(cases), 24)
            self.assertEqual(len({c['source_sha256'] for c in cases}), 24)
            with self.assertRaises(FileExistsError):
                generate(root)


if __name__ == '__main__':
    unittest.main()
