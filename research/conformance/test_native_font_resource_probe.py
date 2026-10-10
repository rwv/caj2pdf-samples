# SPDX-License-Identifier: MIT
"""Original generated fonts distinguish resource identity and cmap identity."""
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'cajviewer'))
sys.path.insert(0, str(ROOT / 'scripts'))
from c8_geometric_font import font
from native_font_resource_probe import digest, probe


class ResourceTests(unittest.TestCase):
    def test_pinned_original_resource_aliases_and_ordinary_slots(self):
        library = Path(subprocess.check_output(['gcc', '-print-file-name=libfreetype.so'], text=True).strip()).resolve()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); path = root / 'HGBZ_CNKI.ttf'; font(path, 'HGBZ_CNKI')
            with TTFont(path) as original:
                cmap = original.getBestCmap(); gid = original.getGlyphID(cmap[65])
            resources = [{'family': 'HGBZ_CNKI', 'sha256': digest(path),
                          'mappings': [{'native_code': 'a0c1', 'cmap_argument': 65, 'glyph_id': gid}]}]
            got = probe(resources, root, library)
            self.assertEqual(got['status'], 'CMAP_MATCH')
            self.assertEqual(got['mappings'][0]['ordinary_glyph_id'], gid)
            for mutation in ('hash', 'glyph', 'duplicate', 'family', 'bound', 'code'):
                with self.subTest(mutation=mutation):
                    changed = copy.deepcopy(resources)
                    if mutation == 'hash': changed[0]['sha256'] = '0' * 64
                    elif mutation == 'glyph': changed[0]['mappings'][0]['glyph_id'] = gid + 1
                    elif mutation == 'duplicate': changed[0]['mappings'] *= 2
                    elif mutation == 'family': changed[0]['family'] = '../HGBZ_CNKI'
                    elif mutation == 'bound': changed[0]['mappings'][0]['cmap_argument'] = 0x10000
                    else: changed[0]['mappings'][0]['native_code'] = 'ffff'
                    with self.assertRaises(ValueError):
                        probe(changed, root, library)


if __name__ == '__main__':
    unittest.main()
