# SPDX-License-Identifier: MIT
"""Original palette controls, generated in temporary files without corpus data."""
import base64
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zlib

import pikepdf

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "indexed_lookup_audit.py"
SPEC = importlib.util.spec_from_file_location("indexed_lookup_audit", MODULE)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class LookupTests(unittest.TestCase):
    def inspect(self, lookup, *, filter_name=None, inline=False, contents=None, wrong_hash=False):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "control.pdf"
            with pikepdf.Pdf.new() as pdf:
                page = pdf.add_blank_page()
                pdf.Root.ControlInteger = pdf.make_indirect(17)
                if filter_name:
                    lookup = pikepdf.Stream(pdf, lookup)
                    lookup.Filter = pikepdf.Name(filter_name)
                else:
                    lookup = pikepdf.String(lookup)
                page.Resources = pikepdf.Dictionary(ColorSpace=pikepdf.Dictionary(
                    Control=pikepdf.Array([
                        pikepdf.Name.Indexed, pikepdf.Name.DeviceRGB, 0, lookup,
                    ])
                ))
                if inline:
                    page.Contents = pikepdf.Stream(pdf,
                        b"BI /W 1 /H 1 /BPC 8 /CS [/I /CMYK 0 <010203>] ID \0 EI\n")
                if contents is not None:
                    page.Contents = pikepdf.Array([pikepdf.Stream(pdf, p) for p in contents])
                pdf.save(path, compress_streams=False,
                         stream_decode_level=pikepdf.StreamDecodeLevel.none)
            return audit.inspect(path, "0" * 64 if wrong_hash else audit.file_hash(path))

    def test_short_exact_extra_and_indirect_primitive(self):
        for length, expected in [(2, "SHORT"), (3, "EXACT"), (4, "EXTRA")]:
            with self.subTest(length=length):
                row = self.inspect(bytes(range(length)))
                self.assertEqual(row["status"], "COMPLETE")
                self.assertTrue(row["pdf_unchanged"])
                self.assertEqual([p["status"] for p in row["palettes"]], [expected])

    def test_inline_palette_is_not_lost_in_content_bytes(self):
        row = self.inspect(b"\1\2\3", inline=True)
        self.assertEqual(row["inline_images"], 1)
        self.assertCountEqual([p["status"] for p in row["palettes"]], ["EXACT", "SHORT"])

    def test_flate_boundary_and_independent_decoder_agreement(self):
        for raw, tail, expected in [(b"abc", b"", "EXACT"),
                                    (b"abc", b"\n", "EXACT"),
                                    (b"ab", b"\n", "SHORT"),
                                    (b"abc", b"x", "UNEXAMINED_ENCODED_TRAILER")]:
            with self.subTest(raw=raw, tail=tail):
                row = self.inspect(zlib.compress(raw) + tail, filter_name="/FlateDecode")
                palette = row["palettes"][0]
                self.assertEqual(palette["status"], expected)
                if expected in {"EXACT", "SHORT"}:
                    self.assertTrue(palette["qpdf_decoded_bytes_agree"])

    def test_truncated_and_oversized_flate_are_unresolved(self):
        for encoded in [zlib.compress(b"abc")[:-1], zlib.compress(b"x" * 65537)]:
            with self.subTest(size=len(encoded)):
                row = self.inspect(encoded, filter_name="/FlateDecode")
                self.assertEqual(row["palettes"][0]["status"], "LOOKUP_DECODE_LIMIT_OR_BOUNDARY")

    def test_pdf_ascii85_without_postscript_opening_marker(self):
        for raw, expected in [(b"abc", "EXACT"), (b"ab", "SHORT")]:
            encoded = base64.a85encode(raw) + b"~>"
            row = self.inspect(encoded, filter_name="/ASCII85Decode")
            self.assertEqual(row["palettes"][0]["status"], expected)
            self.assertTrue(row["palettes"][0]["qpdf_decoded_bytes_agree"])

    def test_identity_mismatch_is_not_inspected(self):
        with self.assertRaises(ValueError):
            self.inspect(b"abc", wrong_hash=True)

    def test_split_page_contents_are_parsed_as_one_sequence(self):
        row = self.inspect(b"abc", contents=[
            b"/Span << /MCID 1 ", b">> BDC\nEMC\n",
            b"BI /W 1 /H 1 /BPC 8 /CS [/I /CMYK 0 <010203>] ID \0 EI\n",
        ])
        self.assertEqual(row["status"], "COMPLETE")
        self.assertEqual(row["qpdf_warning_count"], 0)
        self.assertEqual(row["python_content_warning_count"], 0)
        self.assertEqual(row["inline_images"], 1)
        self.assertCountEqual([p["status"] for p in row["palettes"]], ["EXACT", "SHORT"])

    def test_nonfatal_content_parse_warning_is_not_a_complete_inspection(self):
        row = self.inspect(b"abc", contents=[b"/Span << /MCID 1 "])
        self.assertEqual(row["status"], "INCOMPLETE")
        self.assertGreater(row["qpdf_warning_count"] + row["python_content_warning_count"], 0)


if __name__ == "__main__":
    unittest.main()
