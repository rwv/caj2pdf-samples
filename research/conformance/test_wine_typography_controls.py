# SPDX-License-Identifier: MIT
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "cajviewer")]
from fontTools.ttLib import TTFont
from hnc8_layout_source import FileInput, SourceExtractor
from native_glyph_model import source_model
from native_text_order import digest
from wine_typography_controls import STYLES, generate, typography


class TypographyControls(unittest.TestCase):
    def test_independent_source_parser_keeps_two_rows_across_styles_and_canvases(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.caj"
            for style in STYLES.values():
                for width, height in ((6400, 4800), (4000, 2400)):
                    path.write_bytes(typography(style, width=width, height=height))
                    with FileInput(path) as source:
                        page = next(SourceExtractor(source, digest(path)).iter_pages())
                        glyphs, painting = source_model(source, page, "C8", 2, (4652, 4274), height)
                    self.assertEqual(painting, ["g"] * 14)
                    self.assertEqual("".join(g["character"] for g in glyphs), "中AM1（2）" * 2)
                    self.assertEqual([g["matrix"][4] for g in glyphs[:7]],
                                     [g["matrix"][4] for g in glyphs[7:]])

    def test_alias_and_advance_variants_preserve_original_outlines(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"
            generate(output)
            with TTFont(output / "alias-both.ttf") as both, \
                 TTFont(output / "alias-native.ttf") as native, \
                 TTFont(output / "alias-unicode.ttf") as unicode:
                for plain, alias in ((65, 31908), (77, 37213), (49, 25969)):
                    self.assertIn(alias, native.getBestCmap())
                    self.assertNotIn(plain, native.getBestCmap())
                    self.assertIn(plain, unicode.getBestCmap())
                    self.assertNotIn(alias, unicode.getBestCmap())
                    self.assertEqual(both.getBestCmap()[plain], native.getBestCmap()[alias])
                self.assertEqual(both["glyf"].compile(both), native["glyf"].compile(native))
                self.assertEqual(both["glyf"].compile(both), unicode["glyf"].compile(unicode))
            for variant, alias in (("a", 31908), ("m", 37213), ("one", 25969)):
                with TTFont(output / f"alias-{variant}.ttf") as isolated:
                    cmap = isolated.getBestCmap()
                    self.assertEqual({c for c in (65, 77, 49, 31908, 37213, 25969) if c in cmap},
                                     {alias})
            with TTFont(output / "marker-HGBZ_CNKI.ttf") as before, \
                 TTFont(output / "double-advance-HGBZ_CNKI.ttf") as after:
                self.assertEqual(before["glyf"].compile(before), after["glyf"].compile(after))
                self.assertEqual(before.getBestCmap(), after.getBestCmap())
                for name, (advance, lsb) in before["hmtx"].metrics.items():
                    self.assertEqual(after["hmtx"].metrics[name], (2 * advance, lsb))


if __name__ == "__main__":
    unittest.main()
