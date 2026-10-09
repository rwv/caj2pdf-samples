# SPDX-License-Identifier: MIT
"""Check original control framing/content without a viewer or document corpus."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH / 'cajviewer'))
sys.path.insert(0, str(RESEARCH / 'scripts'))
from native_navigation_controls import document, generate, page_records
from hnc8_layout_source import FileInput, SourceExtractor
from native_text_order import source_glyphs


class NavigationControlTests(unittest.TestCase):
    def test_independent_framing_all_pages_and_identical_target(self):
        with tempfile.TemporaryDirectory() as directory:
            cases = generate(Path(directory) / 'controls')
            self.assertEqual(len(cases), 6)
            targets = set()
            prefix_hashes = {page: set() for page in range(1, 6)}
            for case in cases:
                path = Path(case['source_path'])
                self.assertLessEqual(path.stat().st_size, 60 * 1024)
                with path.open('rb') as stream:
                    self.assertEqual(hashlib.file_digest(stream, 'sha256').hexdigest(), case['source_sha256'])
                with FileInput(path) as source:
                    reader = SourceExtractor(source, case['source_sha256'])
                    self.assertEqual(reader.header['variant'], 'HN-B')
                    self.assertEqual(reader.header['page_count'], case['pages'])
                    self.assertEqual(reader.header['page_index_row_bytes'], case['index_bytes'])
                    for page in reader.iter_pages():
                        self.assertEqual(page['image_count'], 0)
                        glyphs, tail = source_glyphs(source, page, 'HN-B', 2)
                        number = page['page_number']
                        self.assertEqual(len(glyphs), number + (0 if number in (2, 3, 4) else 1600))
                        self.assertEqual(tail, 0)
                        if number <= 5:
                            prefix_hashes[number].add(page['text_sha256'])
                        if number == 5:
                            targets.add(source.read_at(page['text_offset'], page['text_length']))
            self.assertEqual(len(targets), 1)
            self.assertTrue(all(len(hashes) == 1 for hashes in prefix_hashes.values()))

    def test_profile_bounds(self):
        for pages, stride in ((4, 20), (13, 20), (True, 20), (5, 16), (5, 12.0)):
            with self.assertRaises(ValueError):
                document(pages, stride)
        for page in (0, 13, True):
            with self.assertRaises(ValueError):
                page_records(page)

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sentinel = root / 'sentinel'
            sentinel.write_bytes(b'original')
            with self.assertRaises(FileExistsError):
                generate(root)
            self.assertEqual(sentinel.read_bytes(), b'original')
            self.assertEqual(list(root.iterdir()), [sentinel])

    def test_checkout_output_is_refused_before_creation(self):
        output = RESEARCH / 'must-not-create-navigation-controls'
        with self.assertRaises(ValueError):
            generate(output)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
