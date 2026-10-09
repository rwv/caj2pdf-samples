# SPDX-License-Identifier: MIT
"""Original controls for new source framing and bounded geometry profiles."""
from fractions import Fraction as F
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cajviewer'))
from c8_nju_profiles_fixture import controls
from native_glyph_model import Model
from native_text_order import source_glyphs
from native_vector_geometry import source_vectors


class Source:
    def __init__(self, data):
        self.data, self.size = bytes(data), len(data)

    def read_at(self, offset, count):
        return self.data[offset:offset + min(count, 3)]


def words(*values):
    return struct.pack('<' + 'H' * len(values), *values)


class NjuProfiles(unittest.TestCase):
    def test_original_controls_are_bounded_framed_and_reproducible(self):
        cases = list(controls())
        self.assertEqual(len(cases), 148)
        self.assertEqual(len({name for name, _ in cases}), 148)
        self.assertEqual(cases, list(controls()))
        for name, data in cases:
            with self.subTest(name=name):
                self.assertLess(len(data), 8192)
                start, length = struct.unpack_from('<II', data, 80)
                glyphs, tail = source_glyphs(Source(data), {'text_offset': start, 'text_length': length}, 'C8', 2)
                self.assertEqual(tail, 0)
                self.assertLessEqual(len(glyphs), 6)

    def test_8008_payload_is_atomic_and_never_creates_fake_glyphs(self):
        drawing = words(0x8008, 0xa380, 100, 0xa0c1, 0x8004, 1)
        data = drawing + words(200, 0xa0c2, 0x8004, 1)
        self.assertEqual(source_glyphs(Source(data), {'text_offset': 0, 'text_length': len(data)}, 'C8', 2), (['B'], 0))
        for cut in range(1, 12):
            with self.assertRaises(ValueError):
                source_glyphs(Source(data[:cut]), {'text_offset': 0, 'text_length': cut}, 'C8', 2)
        unmeasured = words(0x8008, 0xa381, 10, 20, 30, 40, 0x8004, 1)
        with self.assertRaises(ValueError):
            source_glyphs(Source(unmeasured), {'text_offset': 0, 'text_length': len(unmeasured)}, 'C8', 2)

    def test_nju_title_model_keeps_exact_95_and_rejects_latin_inference(self):
        model = Model('C8', 2, (4652, 4274), 450)
        source = Source(b'')
        model.control(source, 0, 0x8001, 4374)
        model.control(source, 0, 0x8002, 0x096b)
        glyph = model.glyph(4672, 0xd6d0)
        self.assertEqual(glyph['matrix'][0], F(7125, 301))
        self.assertEqual(glyph['matrix'][3], F(7125, 301))
        with self.assertRaises(ValueError):
            model.glyph(4672, 0xa0c1)
        for style in (0x096a, 0x098b, 0x116b):
            model.control(source, 0, 0x8002, style)
            with self.assertRaises(ValueError):
                model.glyph(4672, 0xd6d0)

    def test_new_segments_keep_measured_margins_order_and_flags(self):
        for tag, style in ((0x8006, 0xa387), (0x8006, 0xa38d), (0x8008, 0xa380)):
            data = words(tag, style, 10, 20, 30, 40, 0x8004, 1)
            page = {'text_offset': 0, 'text_length': len(data)}
            vectors, order = source_vectors(Source(data), page, 'C8', 2, (0, 0), 100)
            unit = F(240, 2473)
            self.assertEqual(vectors[0]['points'], [(30 * unit, 60 * unit), (50 * unit, 40 * unit)])
            self.assertEqual((vectors[0]['width'], vectors[0]['gray'], order), (0, 0, ['v']))
            with self.assertRaises(ValueError):
                source_vectors(Source(data), page, 'HN-B', 2, (0, 0), 100)
            flagged = words(tag, style, 0xc00a, 20, 30, 40, 0x8004, 1)
            with self.assertRaises(ValueError):
                source_vectors(Source(flagged), page, 'C8', 2, (0, 0), 100)


if __name__ == '__main__':
    unittest.main()
