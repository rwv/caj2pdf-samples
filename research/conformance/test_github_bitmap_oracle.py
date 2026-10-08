# SPDX-License-Identifier: MIT
"""Original PDF controls for the opt-in bitmap verification runner."""

import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest

import github_bitmap_oracle as oracle


def image_pdf(path: Path, *, swapped=False, omitted=False, corrupt=False):
    """Two distinct, original 8x2 one-bit images; no corpus bytes."""
    raw = b"\x81\x01" if corrupt else b"\x80\x01"
    paint = b"" if omitted else b"q 8 0 0 2 0 0 cm /Im Do Q\n"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Count 2 /Kids " +
        (b"[4 0 R 3 0 R]" if swapped else b"[3 0 R 4 0 R]") + b" >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 8 2] /Resources << /XObject << /Im 5 0 R >> >> /Contents 7 0 R >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 8 2] /Resources << /XObject << /Im 6 0 R >> >> /Contents 7 0 R >>",
    ]
    for bits in (raw, b"\x10\x08"):
        objects.append(b"<< /Type /XObject /Subtype /Image /Width 8 /Height 2 "
                       b"/ColorSpace /DeviceGray /BitsPerComponent 1 /Decode [1 0] "
                       b"/Length 2 >>\nstream\n" + bits + b"\nendstream")
    objects.append(f"<< /Length {len(paint)} >>\nstream\n".encode() + paint + b"endstream")
    data = bytearray(b"%PDF-1.7\n")
    offsets = []
    for number, body in enumerate(objects, 1):
        offsets.append(len(data))
        data.extend(f"{number} 0 obj\n".encode() + body + b"\nendobj\n")
    startxref = len(data)
    data.extend(b"xref\n0 8\n0000000000 65535 f \n")
    for offset in offsets:
        data.extend(f"{offset:010} 00000 n \n".encode())
    data.extend(f"trailer\n<< /Size 8 /Root 1 0 R >>\nstartxref\n{startxref}\n%%EOF\n".encode())
    path.write_bytes(data)


@unittest.skipUnless(shutil.which("pdfimages"), "Poppler required for real PDF image controls")
class BitmapVerificationTests(unittest.TestCase):
    def test_real_page_swap_omission_and_pixel_change_fail(self):
        tools = {"pdfimages": Path(shutil.which("pdfimages"))}
        with tempfile.TemporaryDirectory() as directory:
            pdf = Path(directory) / "original.pdf"
            image_pdf(pdf)
            expected = [("bits", 8, 2, hashlib.sha256(b"\x80\x01").hexdigest())]
            images = [{"record_type": 3}]
            self.assertEqual(oracle.check_page(pdf, 1, images, expected, tools)["status"], "PASS")
            # Type 0 has a known different row convention, selected from its
            # source descriptor. The checker must not accept either direction.
            bottom_up = [("bits", 8, 2, hashlib.sha256(b"\x01\x80").hexdigest())]
            self.assertEqual(oracle.check_page(pdf, 1, [{"record_type": 0}], bottom_up, tools)["status"], "PASS")
            self.assertEqual(oracle.check_page(pdf, 1, images, bottom_up, tools)["status"], "FAIL")
            for change in ("swapped", "omitted", "corrupt"):
                image_pdf(pdf, **{change: True})
                self.assertEqual(oracle.check_page(pdf, 1, images, expected, tools)["status"], "FAIL", change)
            # An empty page is outside bitmap evidence, never a pixel PASS.
            image_pdf(pdf, omitted=True)
            self.assertEqual(oracle.check_page(pdf, 1, [], [], tools)["status"], "NOT_APPLICABLE")


if __name__ == "__main__":
    unittest.main()
