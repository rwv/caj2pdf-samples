# SPDX-License-Identifier: MIT
"""Original synthetic structural controls; no external document or credential."""

import base64
import hashlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "ttkn_inventory.py"
SPEC = importlib.util.spec_from_file_location("ttkn_inventory", MODULE)
inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory)

ENCRYPT = (
    b"<</Length 40/SubFilter/TTKN.PubSec.s1/CF<</DefaultCryptFilter"
    b"<</CFM/AESV2/Recipients[(AppendCA)]>>>>/Filter/TTKN.PubSec"
    b"/StrF/DefaultCryptFilter/StmF/DefaultCryptFilter"
    b"/EncryptMetadata true/R 2/V 2>>"
)


def fixture(*, offset_delta=0, extra_trailer=b"", xml=None):
    if xml is None:
        xml = (
            b"<right-meta><protect><auth><server><url>uncontacted.invalid"
            b"</url></server><password>"
            + base64.b64encode(b"original-structural-control")
            + b"</password></auth></protect></right-meta>"
        )
    raw = bytearray(b"%PDF-1.6\n")
    at = len(raw)
    raw.extend(b"1 0 obj\n" + ENCRYPT + b"\nendobj\n")
    xref = len(raw)
    raw.extend(b"xref 0 2\n0000000000 65535 f\n")
    raw.extend(f"{at + offset_delta:010} 00000 n\n".encode())
    raw.extend(b"trailer\n<< /Size 2 /Encrypt 1 0 R " + extra_trailer + b">>\n")
    raw.extend(f"startxref\n{xref}\n%%EOF\n".encode())
    extent = len(raw)
    raw.extend(b"WebFastLoad\0" + xml)
    raw.extend(f"startrights {extent + 12},{len(xml)}".encode())
    return bytes(raw), extent


class InventoryTests(unittest.TestCase):
    def inspect(self, raw, sha=None):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "source.caj"
            path.write_bytes(raw)
            return inventory.inventory(
                path, sha or hashlib.sha256(raw).hexdigest(), {"kind": "synthetic"}
            )

    def test_selected_xref_and_exact_pdf_extent(self):
        raw, end = fixture()
        result = self.inspect(raw)
        self.assertEqual(result["pdf"]["extent"], [0, end])
        self.assertEqual(result["pdf"]["sha256"], hashlib.sha256(raw[:end]).hexdigest())
        self.assertEqual(result["pdf"]["encryption_object"], [1, 0])
        self.assertTrue(result["source_unchanged"])
        self.assertNotIn("original-structural-control", str(result))
        self.assertNotIn("uncontacted.invalid", str(result))

    def test_wrong_identity_or_xref_does_not_scan_for_a_matching_dictionary(self):
        raw, _ = fixture()
        with self.assertRaises(ValueError):
            self.inspect(raw, "0" * 64)
        raw, _ = fixture(offset_delta=1)
        with self.assertRaises(ValueError):
            self.inspect(raw)

    def test_conflicting_trailers_or_unproved_revisions_are_refused(self):
        for extra in [b"/Encrypt 1 0 R", b"/Prev 9", b"/XRefStm 9"]:
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                self.inspect(fixture(extra_trailer=extra)[0])

    def test_unknown_handler_and_recipient_are_refused(self):
        for source, replacement in [(b"AESV2", b"V2"), (b"AppendCA", b"not-CMS"),
                                    (b"TTKN.PubSec.s1", b"adbe.pkcs7.s5")]:
            with self.subTest(source=source), self.assertRaises(ValueError):
                inventory.encryption_profile(ENCRYPT.replace(source, replacement))

    def test_unbounded_or_credential_exporting_xml_is_refused(self):
        for xml in [b"<!DOCTYPE right-meta><right-meta/>", b"<right-meta><unknown/></right-meta>",
                    b"<right-meta private-key='secret'/>", b" " * (inventory.WINDOW + 1),
                    b"<right-meta>" + b"<iv/>" * 64 + b"</right-meta>"]:
            with self.subTest(length=len(xml)), self.assertRaises(ValueError):
                inventory.wrapper_fields(xml)

    def test_xref_entry_and_line_limits(self):
        for raw in [b"xref 0 100001\n", b"xref\n" + b"0" * 128,
                    b"xref 0 1\n0000000009 00000 f\ntrailer\n"]:
            with self.subTest(length=len(raw)), self.assertRaises(ValueError):
                inventory.xref_entry(io.BytesIO(raw), 0, 0)


if __name__ == "__main__":
    unittest.main()
