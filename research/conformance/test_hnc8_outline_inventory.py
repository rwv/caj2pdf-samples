# SPDX-License-Identifier: MIT
"""Original structural controls; no external titles, links or document bytes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "hnc8_outline_inventory.py"
SPEC = importlib.util.spec_from_file_location("hnc8_outline_inventory", MODULE)
inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory)


def fixture(variant="C8", *, compact=False, xml=None, declared=None, corrupt=False):
    start = 0x50 if variant == "C8" else 0xd8
    width = 12 if compact else 20
    end = start + width
    raw = bytearray(end + 1)
    if variant == "C8":
        raw[:4] = b"\xc8\0\0\0"
        count_at = 8
    else:
        raw[:8] = b"HN\0\0\xc8\0\0\0"
        struct.pack_into("<I", raw, 0x88, 0 if compact else 200)
        count_at = 0x90
    struct.pack_into("<I", raw, count_at, 1)
    struct.pack_into("<II", raw, start, end, 1)
    if xml is not None:
        at = len(raw)
        encoded = zlib.compress(xml)
        if corrupt:
            encoded = encoded[:-1]
        raw.extend(struct.pack("<II", len(xml) if declared is None else declared, len(encoded)))
        raw.extend(encoded)
        raw.extend(f"APPINFOSIGN {at}".encode())
    return bytes(raw)


class OutlineInventoryTests(unittest.TestCase):
    def inspect(self, raw, expected=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "original.caj"
            path.write_bytes(raw)
            return inventory.inspect(path, expected or hashlib.sha256(raw).hexdigest())

    def test_c8_and_both_hnb_index_widths(self):
        for variant, compact, width in [("C8", False, 20), ("HN-B", False, 20), ("HN-B", True, 12)]:
            with self.subTest(variant=variant, width=width):
                row = self.inspect(fixture(variant, compact=compact))
                self.assertEqual(row["variant"], variant)
                self.assertEqual(row["page_row_bytes"], width)
                self.assertTrue(row["first_text_immediately_after_index"])
                self.assertTrue(row["source_unchanged"])
                self.assertEqual(row["application_info"]["status"], "NO_FINAL_MARKER")

    def test_link_types_do_not_export_xml_text_or_attribute_values(self):
        xml = b'<Package Author="DO-NOT-EXPORT"><Item Type="Link"><Item Type="UrlLink">PRIVATE-URL</Item></Item></Package>'
        row = self.inspect(fixture(xml=xml))
        info = row["application_info"]
        self.assertEqual(info["status"], "PARSED")
        self.assertEqual(info["known_structural_type_counts"], {"Link": 1, "UrlLink": 1})
        self.assertEqual(info["outline_named_elements"], [])
        self.assertNotIn("DO-NOT-EXPORT", json.dumps(row))
        self.assertNotIn("PRIVATE-URL", json.dumps(row))

    def test_outline_named_structure_is_a_hint_without_extracted_bookmarks(self):
        row = self.inspect(fixture(xml=b'<Package><Outline><Item Type="Bookmark">TITLE</Item></Outline></Package>'))
        self.assertEqual(row["application_info"]["outline_named_elements"], ["Outline"])
        self.assertEqual(row["application_info"]["known_structural_type_counts"], {"Bookmark": 1})
        self.assertNotIn("TITLE", json.dumps(row))
        self.assertNotIn("bookmark_count", row)

    def test_bad_package_lengths_checksum_and_xml_remain_unresolved(self):
        for raw in [fixture(xml=b"<Package/>", declared=inventory.LIMIT + 1),
                    fixture(xml=b"<Package/>", declared=1),
                    fixture(xml=b"<Package/>", corrupt=True),
                    fixture(xml=b"<!DOCTYPE Package><Package/>"),
                    fixture(xml='<Package/>'.encode('utf-16')),
                    fixture(xml='<Package/>'.encode('utf-16-le')),
                    fixture(xml=b"<Package>")]:
            with self.subTest(size=len(raw)):
                self.assertEqual(self.inspect(raw)["application_info"]["status"], "UNRESOLVED")

    def test_identity_bounds_and_hna_marker_are_not_accepted_as_hnb(self):
        with self.assertRaises(ValueError):
            self.inspect(fixture(), "0" * 64)
        for raw in [fixture()[:90], b"HN\0\0\x90\x01\0\0" + fixture("HN-B")[8:]]:
            with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                self.inspect(raw)

    def test_nonfinal_marker_is_reported_without_guessing_a_package(self):
        for suffix in [b" trailing", b"\n"]:
            with self.subTest(suffix=suffix):
                row = self.inspect(fixture() + b"APPINFOSIGN 101" + suffix)
                self.assertEqual(row["application_info"], {
                    "status": "NO_FINAL_MARKER", "marker_name_elsewhere_in_tail": True,
                })

    def test_package_offsets_and_concatenated_frames_remain_unresolved(self):
        raw = fixture(xml=b"<Package/>")
        marker = raw.index(b"APPINFOSIGN")
        second_frame = zlib.compress(b"<Other/>")
        joined = bytearray(raw[:marker] + second_frame + raw[marker:])
        encoded = struct.unpack_from("<I", joined, 105)[0]
        struct.pack_into("<I", joined, 105, encoded + len(second_frame))
        for altered in [raw.replace(b"APPINFOSIGN 101", b"APPINFOSIGN 0"),
                        raw.replace(b"APPINFOSIGN 101", b"APPINFOSIGN 999999"),
                        bytes(joined)]:
            with self.subTest(size=len(altered)):
                self.assertEqual(self.inspect(altered)["application_info"]["status"], "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
