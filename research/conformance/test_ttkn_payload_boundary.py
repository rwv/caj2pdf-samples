# SPDX-License-Identifier: MIT
"""Original plaintext/encrypted controls; no external documents or credentials."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zlib

import pikepdf

SPEC = importlib.util.spec_from_file_location(
    "ttkn_payload_boundary", Path(__file__).resolve().parents[1] / "scripts" / "ttkn_payload_boundary.py")
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)
PAYLOAD = b"0.25 g 10 10 30 40 re f\n" * 10


def fixture(path, *, encrypted=False, opaque=False):
    with pikepdf.new() as pdf:
        page = pdf.add_blank_page(page_size=(100, 100))
        page.Contents = pdf.make_stream(PAYLOAD)
        if opaque:
            page.Resources.XObject = pikepdf.Dictionary(
                Example=pdf.make_stream(b"original opaque data", Filter=pikepdf.Name("/DCTDecode")),
                Fax=pdf.make_stream(b"original opaque fax", Filter=pikepdf.Name("/CCITTFaxDecode")))
        if not encrypted:
            # A deliberately decorative handler selector tests the possibility
            # that the original payload was already valid plaintext.
            pdf.trailer.Xncrypt = pdf.make_indirect(pikepdf.Dictionary(Filter=pikepdf.Name("/TTKN.PubSec")))
        pdf.save(path, object_stream_mode=pikepdf.ObjectStreamMode.disable,
                 compress_streams=not opaque,
                 encryption=pikepdf.Encryption(owner="original-owner-control", user="original-user-control",
                                                R=4, aes=True) if encrypted else None)
    if not encrypted:
        raw = path.read_bytes()
        assert raw.count(b"/Xncrypt") == 1
        path.write_bytes(raw.replace(b"/Xncrypt", b"/Encrypt"))


class PayloadBoundaryTests(unittest.TestCase):
    def test_plaintext_is_detected_after_one_byte_change_and_tail_omission(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            output = Path(directory) / "diagnostic.pdf"
            fixture(source)
            original = source.read_bytes()
            source.write_bytes(original + b"original synthetic non-PDF wrapper")
            sha = probe.digest(source)
            result = probe.disable_handler(source, sha, len(original), output)
            changed = [i for i, (a, b) in enumerate(zip(original, output.read_bytes(), strict=True)) if a != b]
            self.assertEqual(changed, [result["trailer_key_offset"] + 1])
            self.assertEqual(probe.digest(source), sha)
            inventory = probe.payload_inventory(output)
            self.assertEqual(inventory["stream_counts"]["flate_check"], {"VALID_COMPLETE_ZLIB": 1})
            self.assertEqual(inventory["streams"][0]["flate_check"]["decoded_bytes"], len(PAYLOAD))

    def test_valid_known_encrypted_control_does_not_become_plaintext(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            output = Path(directory) / "diagnostic.pdf"
            fixture(source, encrypted=True)
            with pikepdf.open(source, password="original-user-control") as pdf:
                self.assertEqual(pdf.pages[0].Contents.read_bytes(), PAYLOAD)
            probe.disable_handler(source, probe.digest(source), source.stat().st_size, output)
            inventory = probe.payload_inventory(output)
            self.assertEqual(inventory["stream_counts"]["flate_check"], {"INVALID_ZLIB": 1})
            self.assertEqual(inventory["stream_counts"]["length_modulo_16"], {0: 1})

    def test_opaque_and_unfiltered_streams_are_not_counted_as_decodes(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            output = Path(directory) / "diagnostic.pdf"
            fixture(source, opaque=True)
            probe.disable_handler(source, probe.digest(source), source.stat().st_size, output)
            inventory = probe.payload_inventory(output)
            self.assertEqual(inventory["stream_counts"]["flate_check"], {"NOT_CHECKED": 3})

    def test_flate_completion_limits_and_neighbors(self):
        raw = zlib.compress(PAYLOAD)
        self.assertEqual(probe.flate_boundary(raw, len(PAYLOAD))["status"], "VALID_COMPLETE_ZLIB")
        self.assertEqual(probe.flate_boundary(raw, len(PAYLOAD) - 1)["status"], "OUTPUT_LIMIT")
        self.assertEqual(probe.flate_boundary(raw[:-1])["status"], "INCOMPLETE_ZLIB")
        self.assertEqual(probe.flate_boundary(raw + b"x")["status"], "TRAILING_DATA")
        self.assertEqual(probe.flate_boundary(raw + raw)["status"], "TRAILING_DATA")
        self.assertEqual(probe.flate_boundary(b"not zlib")["status"], "INVALID_ZLIB")

    def test_identity_extent_existing_output_and_unknown_boundaries_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            output = Path(directory) / "diagnostic.pdf"
            fixture(source)
            sha = probe.digest(source)
            size = source.stat().st_size
            for expected, extent in [("0" * 64, size), (sha, size - 5), (sha, size + 1)]:
                with self.subTest(expected=expected, extent=extent), self.assertRaises(ValueError):
                    probe.disable_handler(source, expected, extent, output)
                self.assertFalse(output.exists())
            output.write_bytes(b"keep")
            with self.assertRaises(FileExistsError):
                probe.disable_handler(source, sha, size, output)
            self.assertEqual(output.read_bytes(), b"keep")
            output.unlink()
            original = source.read_bytes()
            source.write_bytes(original.replace(b"/Encrypt", b"/Prev 0 /Encrypt"))
            with self.assertRaises(ValueError):
                probe.disable_handler(source, probe.digest(source), source.stat().st_size, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
