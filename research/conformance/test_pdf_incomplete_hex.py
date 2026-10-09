# SPDX-License-Identifier: MIT
"""Original lexical negatives and independent missing-text counterexamples."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import fitz
import pikepdf
from PIL import Image

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH / 'scripts'))
sys.path.insert(0, str(RESEARCH / 'cajviewer'))
from pdf_incomplete_hex import MAX_CONTENT, MAX_NESTING, unfinished_hex
from pdf_incomplete_hex_controls import content, generate, write


class LexicalBoundary(unittest.TestCase):
    def test_only_unfinished_hex_is_reported(self):
        prefix = b'% BT q <bad\r\n/BT /q /Name#3C (q < (BT) \\) \\r) Tj '
        prefix += b'<< /Name (ET) /List [ /BT /q <4142> ] >> q BT '
        for digits in (b'', b'4', b'41', b'4142'):
            with self.subTest(digits=digits):
                self.assertEqual(unfinished_hex(prefix + b'<' + digits + b'\r\n'),
                                 dict(offset=len(prefix), hex_digits=len(digits),
                                      whitespace_bytes=2, container_depth=0,
                                      text_depth=1, graphics_depth=1))
        self.assertIsNone(unfinished_hex(prefix + b'<414> Tj ET Q'))
        self.assertIsNone(unfinished_hex(b'/ /Name% comment <41'))
        self.assertEqual(unfinished_hex(b'BT [<41')['container_depth'], 1)

    def test_rejects_unmeasured_and_malformed_constructs(self):
        for data in (b'<4Z', b'(', b'(\\', b'[', b'<<', b'[>>', b'<<]',
                     b'>', b')', b'Q', b'BT BT', b'ET', b'BI /W 1 ID <41'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                unfinished_hex(data)

    def test_resource_bounds(self):
        self.assertIsNone(unfinished_hex(b' ' * MAX_CONTENT))
        for data in ('<41', bytearray(b'<41'), b' ' * (MAX_CONTENT + 1),
                     b'[' * (MAX_NESTING + 1), b'<<' * (MAX_NESTING + 1),
                     b'(' * (MAX_NESTING + 1), b'q ' * (MAX_NESTING + 1)):
            with self.subTest(type=type(data)), self.assertRaises(ValueError):
                unfinished_hex(data)


class MissingTextControls(unittest.TestCase):
    def test_distinct_completions_have_same_surviving_prefix(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rows = generate(root / 'first')
            self.assertEqual(rows, generate(root / 'second'))
            self.assertEqual(len(rows), 16)
            for digits in (b'', b'4', b'41', b'4142'):
                renders = {}
                texts = {}
                for ending in ('broken', 'omitted', 'a', 'b'):
                    name = f'hex-{len(digits)}-{ending}.pdf'
                    path = root / 'first' / name
                    data = content(digits, ending)
                    with pikepdf.open(path) as pdf:
                        self.assertEqual(len(pdf.pages), 1)
                        self.assertEqual(bytes(pdf.pages[0].Contents.read_bytes()), data)
                    result = subprocess.run(['qpdf', '--check', str(path)],
                                            capture_output=True, timeout=20)
                    self.assertEqual(result.returncode, 3 if ending == 'broken' else 0,
                                     result.stderr.decode(errors='replace'))
                    with fitz.open(path) as pdf:
                        pixmap = pdf[0].get_pixmap(alpha=False)
                        texts[ending] = pdf[0].get_text().strip()
                        mupdf = hashlib.sha256(pixmap.samples).hexdigest()
                    target = root / name
                    subprocess.run(['pdftoppm', '-singlefile', '-r', '72',
                                    str(path), str(target)], check=True,
                                   capture_output=True, timeout=20)
                    with Image.open(str(target) + '.ppm') as image:
                        poppler = hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()
                    renders[ending] = (mupdf, poppler)
                    if ending in ('a', 'b'):
                        self.assertTrue(data.startswith(content(digits, 'broken')))
                self.assertEqual(renders['broken'], renders['omitted'])
                self.assertEqual(texts['broken'], 'BEFORE')
                self.assertNotEqual(texts['a'], texts['b'])
                for index in (0, 1):
                    self.assertNotEqual(renders['a'][index], renders['b'][index])

    def test_invalid_inputs_and_existing_outputs_are_refused(self):
        for digits, ending in ((b'Z', 'a'), (b'41', 'unknown')):
            with self.assertRaises(ValueError): content(digits, ending)
        with self.assertRaises(ValueError): generate(RESEARCH / 'must-not-create-hex-controls')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / 'sentinel.pdf'
            path.write_bytes(b'untouched')
            with self.assertRaises(FileExistsError): write(path, b'')
            with self.assertRaises(ValueError): write(root / 'large.pdf', b' ' * 4097)
            with self.assertRaises(FileExistsError): generate(root)
            self.assertEqual(path.read_bytes(), b'untouched')
            self.assertFalse((root / 'large.pdf').exists())


if __name__ == '__main__':
    unittest.main()
