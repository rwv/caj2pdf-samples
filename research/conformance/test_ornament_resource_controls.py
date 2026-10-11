# SPDX-License-Identifier: MIT
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'cajviewer'))
from fontTools.ttLib import TTFont
from hnc8_layout_source import FileInput, SourceExtractor
from native_glyph_model import source_model
from native_text_order import digest
from ornament_resource_controls import ALIASES, control, generate


class OrnamentControls(unittest.TestCase):
    def test_record_discriminator_preserves_three_spans_and_neighbor(self):
        reference = control(1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.caj'
            for value in ALIASES:
                data = control(value)
                self.assertEqual(len(data), len(reference))
                self.assertLessEqual({i for i, pair in enumerate(zip(data, reference))
                                     if pair[0] != pair[1]}, {118, 130, 142})
                path.write_bytes(data)
                with FileInput(path) as source:
                    page = next(SourceExtractor(source, digest(path)).iter_pages())
                    glyphs, painting = source_model(source, page, 'C8', 2, (4652, 4274), 4800)
                self.assertEqual(painting, ['o'] * 43 + ['v'])
                self.assertTrue(all(glyph['character'] == '' for glyph in glyphs))
                self.assertEqual(data[152:156], b'\x06\x80\x83\xa3')
        with self.assertRaises(ValueError):
            control(3)

    def test_single_slot_fonts_keep_geometry_but_distinguish_the_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'generated'
            generate(output)
            outlines = []
            for value, alias in ALIASES.items():
                with TTFont(output / f'marker-{value}' / 'HGBZ_CNKI.ttf') as font:
                    cmap = font.getBestCmap()
                    self.assertEqual({code for code in ALIASES.values() if code in cmap}, {alias})
                    self.assertEqual(cmap[alias], 'upper')
                    glyph = font['glyf']['upper']
                    outlines.append((glyph.numberOfContours, tuple(glyph.coordinates),
                                     tuple(glyph.endPtsOfContours), font['hmtx']['upper']))
            self.assertTrue(all(outline == outlines[0] for outline in outlines))
            self.assertEqual(outlines[0][0], 1)
            self.assertEqual(set(outlines[0][1]), {(0, 500), (250, 500), (250, 1000), (0, 1000)})


if __name__ == '__main__':
    unittest.main()
