# SPDX-License-Identifier: MIT
"""Original independent page/count and state controls; no external corpus."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cajviewer'))
from c8_navigation_fixture import document
from native_composition_inventory import source_page


class Source:
    def __init__(self, data):
        self.data, self.size = data, len(data)

    def read_at(self, offset, length):
        return self.data[offset:offset + min(length, 3)]


class CompositionInventoryTests(unittest.TestCase):
    def test_twelve_independently_identifiable_pages(self):
        data = document()
        for index in range(12):
            offset, size = struct.unpack_from('<II', data, 80 + index * 20)
            page = {'text_offset': offset, 'text_length': size, 'images': []}
            result = source_page(Source(data), page, 'C8', 2)
            self.assertEqual(result['glyphs'], index + 1)
            self.assertEqual(result['records']['8001'], index + 1)
            self.assertEqual(result['drawing_records'], {})
            self.assertEqual(result['glyph_state_use'], [{'style_8002': 0x1084, 'state_801d': 0,
                             'value_8067': 6, 'mode_80ce': None, 'glyphs': index + 1}])

    def test_vector_payload_does_not_add_state_or_glyphs(self):
        words = [0x8006, 0xa381, 0x801d, 4, 20, 30, 100, 0xd6d0, 0x8004, 1]
        data = struct.pack('<' + 'H' * len(words), *words)
        result = source_page(Source(data), {'text_offset': 0, 'text_length': len(data), 'images': []}, 'C8', 2)
        self.assertEqual(result['glyphs'], 1)
        self.assertEqual(result['drawing_records'], {'8006/a381': 1})
        self.assertIsNone(result['glyph_state_use'][0]['state_801d'])


if __name__ == '__main__':
    unittest.main()
