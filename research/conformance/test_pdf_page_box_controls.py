# SPDX-License-Identifier: MIT
"""Independent parser checks for 75 original page IDs and box omission."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import pikepdf

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH/'cajviewer'))
from pdf_page_box_controls import content, generate, write


class PageBoxControls(unittest.TestCase):
    def test_all_page_ids_boxes_and_unchanged_painting(self):
        with tempfile.TemporaryDirectory() as temp:
            rows = generate(Path(temp)/'controls')
            streams = []
            for row in rows:
                path = Path(row['path'])
                self.assertLess(path.stat().st_size, 32*1024)
                check = subprocess.run(['qpdf', '--check', str(path)], capture_output=True, timeout=20)
                self.assertEqual(check.returncode, 0 if row['explicit_letter'] else 3)
                # Keep qpdf from materializing default/inherited boxes before inspection.
                with pikepdf.open(path, inherit_page_attributes=False) as pdf:
                    self.assertEqual(len(pdf.Root.Pages.Kids), 75)
                    self.assertNotIn('/MediaBox', pdf.Root.Pages)
                    bodies = []
                    for ordinal, page in enumerate(pdf.Root.Pages.Kids, 1):
                        self.assertEqual(bool('/MediaBox' in page), row['explicit_letter'])
                        if row['explicit_letter']:
                            self.assertEqual(list(page.MediaBox), [0, 0, 612, 792])
                        self.assertEqual(len(page.Resources), 0)
                        ops = list(pikepdf.parse_content_stream(page.Contents))
                        rectangles = [list(map(int, op.operands)) for op in ops if str(op.operator) == 're']
                        self.assertEqual(rectangles[:2], [[2, 2, 608, 788], [100, 100, 40, 60]])
                        observed = 0
                        for x, y, w, h in rectangles[2:]:
                            self.assertEqual((y, w, h), (740, 12, 12))
                            self.assertEqual((x-40) % 20, 0)
                            bit = (x-40)//20
                            self.assertIn(bit, range(7))
                            self.assertFalse(observed & (1 << bit))
                            observed |= 1 << bit
                        self.assertEqual(observed, ordinal)
                        self.assertEqual({str(op.operator) for op in ops}, {'q','Q','RG','rg','w','re','m','l','S','f'})
                        bodies.append(page.Contents.read_bytes())
                    self.assertEqual(len(set(bodies)), 75)
                    streams.append(bodies)
            self.assertEqual(*streams)

    def test_bounds_and_no_overwrite_or_checkout_output(self):
        for value in (0, 76, True, 1.0):
            with self.assertRaises(ValueError):content(value)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'sentinel.pdf';path.write_bytes(b'untouched')
            with self.assertRaises(ValueError):write(path, explicit_letter=1)
            with self.assertRaises(FileExistsError):write(path, explicit_letter=True)
            with self.assertRaises(FileExistsError):generate(Path(temp))
            self.assertEqual(path.read_bytes(), b'untouched')
        with self.assertRaises(ValueError):generate(RESEARCH/'must-not-create-page-controls')


if __name__ == '__main__':
    unittest.main()
