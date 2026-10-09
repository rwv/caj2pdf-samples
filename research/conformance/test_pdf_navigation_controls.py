# SPDX-License-Identifier: MIT
"""Independently parse/check fixed original PDF controls; no viewer/corpus."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import pikepdf

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH/'cajviewer'))
from pdf_navigation_controls import content, generate, write


class PdfNavigationTests(unittest.TestCase):
    def test_framing_content_and_measured_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            cases = generate(Path(directory)/'controls')
            self.assertEqual([row['sha256'] for row in cases], [
                '80dd555d6a8cfc8ed37ac13793f32fa00bc74dd69fa0722a66143d7aa1decbed',
                '164f598498d6d722aaf243592d7535d73f0b628818dba05a65c64b3d2c3921e8'])
            prefix = []
            for case in cases:
                path = Path(case['path'])
                self.assertLess(path.stat().st_size, 160*1024)
                subprocess.run(['qpdf', '--check', str(path)], check=True, capture_output=True, timeout=20)
                with pikepdf.open(path) as pdf:
                    self.assertEqual(len(pdf.pages), case['pages'])
                    prefix.append([page.Contents.read_bytes() for page in pdf.pages][:5])
                    for number, page in enumerate(pdf.pages, 1):
                        self.assertEqual(list(map(float, page.MediaBox)), [0, 0, 595.2756, 841.8898])
                        font = page.Resources.Font.F1
                        self.assertEqual(str(font.BaseFont), '/Helvetica')
                        self.assertNotIn('/FontDescriptor', font)
                        ops = pikepdf.parse_content_stream(page)
                        self.assertEqual(sum(str(op.operator) == 'Tj' for op in ops),
                                         number + (0 if number in (2, 3, 4) else 1600))
            self.assertEqual(*prefix)

    def test_profile_bounds_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'not-created.pdf'
            for pages in (0, 4, 7, True, 5.0):
                with self.assertRaises(ValueError):
                    write(path, pages)
            self.assertFalse(path.exists())
        for page in (0, 7, True, 1.0):
            with self.assertRaises(ValueError):
                content(page)

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'sentinel'
            path.write_bytes(b'original')
            with self.assertRaises(FileExistsError):
                generate(Path(directory))
            with self.assertRaises(FileExistsError):
                write(path, 5)
            self.assertEqual(path.read_bytes(), b'original')

    def test_checkout_output_is_refused(self):
        path = RESEARCH/'must-not-create-pdf-controls'
        with self.assertRaises(ValueError):
            generate(path)
        self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()
