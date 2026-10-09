# SPDX-License-Identifier: MIT
"""Original marker fonts must preserve outlines/metrics across cmap variants."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cajviewer'))
from composition_marker_fonts import generate, ROLES, TABLES


class MarkerFontTests(unittest.TestCase):
    def test_seven_roles_with_identical_outline_and_metric_tables(self):
        names = [family + '.ttf' for family in ROLES] + ['OriginalSymbols.TTF']
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'fonts'
            generate(names, root)
            rows = json.loads((root / 'manifest.json').read_text())['resources']
            self.assertEqual({row['marker'] for row in rows}, set(range(1, 8)))
            for row in rows:
                with TTFont(root / 'viewer' / row['resource']) as viewer, TTFont(root / 'pdf' / (row['pdf_role'] + '.ttf')) as pdf:
                    for table in TABLES:
                        self.assertEqual(viewer.getTableData(table), pdf.getTableData(table))
                    self.assertEqual(viewer['cmap'].tables[0].format, 13)
                    self.assertEqual(pdf['cmap'].tables[0].format, 12)
                    self.assertEqual(pdf.getBestCmap()[0xe6c7], 'square')
                    self.assertNotIn(0xd800, pdf.getBestCmap())
            with self.assertRaises(ValueError):
                generate(names + ['../bad.ttf'], Path(directory) / 'invalid')


if __name__ == '__main__':
    unittest.main()
