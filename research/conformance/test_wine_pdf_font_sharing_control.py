# SPDX-License-Identifier: MIT
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "cajviewer")]
from hnc8_layout_source import FileInput, SourceExtractor
from native_glyph_model import source_model
from native_text_order import digest
from wine_pdf_font_sharing_control import control


class FontSharingControl(unittest.TestCase):
    def test_independent_parser_preserves_nonsemantic_ornaments_and_latin(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "original.caj"
            path.write_bytes(control())
            with FileInput(path) as source:
                page = next(SourceExtractor(source, digest(path)).iter_pages())
                glyphs, painting = source_model(source, page, "C8", 2, (4652, 4274), 7469)
        self.assertEqual(painting, ["o"] * 47 + ["g"] * 8)
        self.assertTrue(all(glyph["character"] == "" for glyph in glyphs[:47]))
        self.assertEqual("".join(glyph["character"] for glyph in glyphs[47:]), "AM1am234")
        self.assertTrue(all(glyph["role"] == "latin" for glyph in glyphs[47:]))


if __name__ == "__main__":
    unittest.main()
