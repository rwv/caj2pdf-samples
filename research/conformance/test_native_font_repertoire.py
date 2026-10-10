# SPDX-License-Identifier: MIT
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'cajviewer'))
from native_font_repertoire import inventory
from native_font_controls import document
from native_text_order import digest
from test_hnc8_layout_source import sample


class RepertoireTests(unittest.TestCase):
    def test_hna_header_bytes_are_not_interpreted_as_a_native_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'original-hna.caj'
            path.write_bytes(sample('HN-A')[0])
            with patch('native_font_repertoire.read_exact') as read:
                got = inventory(path, digest(path))
                read.assert_not_called()
            self.assertEqual(got['status'], 'OUTSIDE_NATIVE_MODEL')
            self.assertIsNone(got['header_mode'])

    def test_authored_characters_roles_and_hash_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'control.caj'
            for mode, state, role in [(0, 0, 'cjk'), (1, 0, 'latin'), (1, 3, 'latin-state3')]:
                path.write_bytes(document([0xa0c1, 0xa0b1], mode=mode, state=state))
                got = inventory(path, digest(path))
                self.assertEqual(got['status'], 'INVENTORIED_EXISTING_MODEL')
                self.assertEqual(got['per_page'], [{'page': 1, 'glyphs': 2, 'ornaments': 0}])
                self.assertEqual(got['roles'], [{'role': role, 'ordinary_draws': 2,
                    'ornament_draws': 0, 'unicode_repertoire': ['U+0031', 'U+0041'],
                    'model_state_character_combinations': 2}])
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                inventory(path, '0' * 64)


if __name__ == '__main__':
    unittest.main()
