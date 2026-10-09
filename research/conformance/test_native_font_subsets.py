# SPDX-License-Identifier: MIT
"""Original caller-font/PDF controls; no external fonts or documents."""
from contextlib import ExitStack
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pikepdf
from fontTools.cffLib import FDArrayIndex, FDSelect, FontDict
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import native_font_subsets as f
from test_native_glyph_geometry import fixture, generate, ROLES


def original_cff(path, shift=0, width=1000, matrix=None):
    builder = FontBuilder(1000, isTTF=False)
    names = ['.notdef', 'cid20013']
    builder.setupGlyphOrder(names); builder.setupCharacterMap({0x4e2d: names[1]})
    strings = {}
    for name in names:
        pen = T2CharStringPen(width, None)
        if name != '.notdef':
            pen.moveTo((shift, 0)); pen.lineTo((900, 0)); pen.lineTo((900, 850)); pen.closePath()
        strings[name] = pen.getCharString()
    builder.setupCFF('OriginalCFF', {}, strings, {})
    builder.setupHorizontalMetrics({name: (width, 0) for name in names})
    builder.setupHorizontalHeader(ascent=1000, descent=0)
    builder.setupNameTable({'familyName': 'OriginalCFF', 'styleName': 'Regular'})
    builder.setupOS2(); builder.setupPost(); builder.save(path)
    top = builder.font['CFF '].cff.topDictIndex[0]
    fd = FontDict(); fd.Private = top.Private
    top.FDArray = FDArrayIndex(); top.FDArray.append(fd)
    top.FDSelect = FDSelect(format=3); top.FDSelect.gidArray = [0, 0]
    top.ROS = ('Adobe', 'Identity', 0); top.CIDCount = 20014
    if matrix is not None: top.FontMatrix = matrix
    top.CharStrings.fdArray, top.CharStrings.fdSelect = top.FDArray, top.FDSelect
    del top.Private
    stream = io.BytesIO(); builder.font['CFF '].cff.compile(stream, builder.font)
    return stream.getvalue()


class FontSubsetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(); cls.root = Path(cls.temp.name)
        generate([name + '.ttf' for name in ROLES] + ['OriginalSymbols.TTF'], cls.root / 'fonts')
        cls.fonts = cls.root / 'fonts/pdf'
        cls.inputs = {r: {'path': str(cls.fonts / (r + '.ttf')), 'face': -1,
                         'sha256': f.g.digest(cls.fonts / (r + '.ttf'))} for r in ('cjk', 'latin')}

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def check(self, source, pdf, inputs=None):
        return f.inspect(source, pdf, f.g.digest(source), f.g.digest(pdf), inputs or self.inputs)

    def test_complete_original_ttf_pair_ornaments_and_cli(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); source, pdf = fixture(root, self.fonts, ornament=True)
            report = self.check(source, pdf)
            self.assertEqual(report['status'], 'PASS')
            self.assertEqual(report['pages'][0]['glyphs'], 4)
            manifest = root / 'fonts.json'; manifest.write_text(json.dumps(self.inputs))
            result = subprocess.run([sys.executable, f.__file__, str(source), str(pdf), str(manifest),
                '--source-sha256', f.g.digest(source), '--pdf-sha256', f.g.digest(pdf)],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'PASS')

    def test_cff_charset_outline_and_advance_control(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); source, pdf = fixture(root, self.fonts)
            cff = root / 'original.otf'; data = original_cff(cff)
            inputs = {**self.inputs, 'cjk': {'path': str(cff), 'face': -1, 'sha256': f.g.digest(cff)}}
            with pikepdf.open(pdf) as doc:
                cid = doc.pages[0].Resources.Font.Arbitrary9.DescendantFonts[0]
                cid.Subtype = pikepdf.Name('/CIDFontType0'); del cid.CIDToGIDMap
                fd = cid.FontDescriptor; del fd.FontFile2
                fd.FontFile3 = doc.make_stream(data); fd.FontFile3.Subtype = pikepdf.Name('/CIDFontType0C')
                modified = root / 'cff.pdf'; doc.save(modified)
            report = self.check(source, modified, inputs)
            self.assertEqual(report['status'], 'PASS')
            self.assertEqual(report['font_programs'], {'CFF': 1, 'TrueType': 1})
            for mutation in ('outline', 'advance', 'matrix'):
                data = original_cff(root / 'mutant.otf', shift=1 if mutation == 'outline' else 0,
                    width=999 if mutation == 'advance' else 1000,
                    matrix=[.002, 0, 0, .001, 0, 0] if mutation == 'matrix' else None)
                with self.subTest(mutation=mutation), pikepdf.open(modified) as doc:
                    fd = doc.pages[0].Resources.Font.Arbitrary9.DescendantFonts[0].FontDescriptor
                    fd.FontFile3 = doc.make_stream(data); fd.FontFile3.Subtype = pikepdf.Name('/CIDFontType0C')
                    bad = root / (mutation + '.pdf'); doc.save(bad)
                if mutation == 'matrix':
                    with self.assertRaisesRegex(ValueError, 'CFF matrices'): self.check(source, bad, inputs)
                else:
                    self.assertEqual(self.check(source, bad, inputs)['status'], 'FAIL')
            with pikepdf.open(modified) as doc:
                page = doc.pages[0]; page.Contents = doc.make_stream(page.Contents.read_bytes().replace(b'<4E2D>', b'<4E2E>'))
                bad = root / 'missing-cid.pdf'; doc.save(bad)
            with self.assertRaisesRegex(ValueError, 'CID glyph missing'): self.check(source, bad, inputs)

    def test_glyph_resource_mapping_outline_width_and_advance_mutations(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); source, pdf = fixture(root, self.fonts)
            for kind in ('resource', 'outline', 'advance', 'pdf-width', 'cid-map', 'display-code'):
                with self.subTest(kind=kind), pikepdf.open(pdf) as doc:
                    page = doc.pages[0]; cid = page.Resources.Font.Arbitrary9.DescendantFonts[0]
                    if kind == 'resource': page.Resources.Font.Arbitrary9 = page.Resources.Font.Unrelated3
                    elif kind in ('outline', 'advance'):
                        with f.g.TTFont(io.BytesIO(cid.FontDescriptor.FontFile2.read_bytes())) as font:
                            if kind == 'outline': font['glyf']['square'].coordinates[0] = (8, 0)
                            else: font['hmtx']['square'] = (999, 0)
                            out = io.BytesIO(); font.save(out)
                        cid.FontDescriptor.FontFile2 = doc.make_stream(out.getvalue())
                    elif kind == 'pdf-width': cid.W = [0x4e2d, [999]]
                    elif kind == 'cid-map': cid.CIDToGIDMap = doc.make_stream(b'\0\2' * 65536)
                    else: page.Contents = doc.make_stream(page.Contents.read_bytes().replace(b'<0041>', b'<0042>'))
                    bad = root / (kind + '.pdf'); doc.save(bad)
                self.assertEqual(self.check(source, bad)['status'], 'FAIL', kind)

    def test_width_ranges_ambiguity_and_cid_limits(self):
        cid = pikepdf.Dictionary(DW=500, W=[10, 12, 321, 20, [800, 900]])
        self.assertEqual(f.widths(cid), (500, {10: 321, 11: 321, 12: 321, 20: 800, 21: 900}))
        for values in ([1], [2, 1, 400], [65535, [1, 2]], [1, [300], 1, [300]]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                f.widths(pikepdf.Dictionary(W=values))

    def test_default_fallback_and_explicit_pua_alias(self):
        class Caller:
            def __init__(self, codes): self.cmap = dict.fromkeys(codes)
        callers = {'cjk': Caller([0x4e2d, 65]), 'latin': Caller([65, 0x403, 0x25ba])}
        for role, character, expected in [('latin-state3', '中', ('cjk', 0x4e2d)),
                ('cjk', 'A', ('cjk', 65)), ('latin', '中', ('cjk', 0x4e2d)),
                ('latin', '\ue6c7', ('latin', 0x403))]:
            self.assertEqual(f.selection({'role': role, 'character': character, 'kind': 'g'}, callers), expected)
        self.assertEqual(f.selection({'role': 'cjk', 'character': '', 'kind': 'o'}, callers), ('latin', 0x25ba))

    def test_original_composite_depth_path_and_input_limits(self):
        class Cycle:
            def draw(self, pen): pen.addComponent('cycle', (1, 0, 0, 1, 0, 0))
        with self.assertRaisesRegex(ValueError, 'component depth'): f.outline({'cycle': Cycle()}, 'cycle', 1000)
        recording = f.Recording()
        with self.assertRaisesRegex(ValueError, 'path limit'):
            for _ in range(f.POINTS + 1): recording.append(('lineTo', ((0, 0),)))
        with ExitStack() as stack, self.assertRaisesRegex(ValueError, 'size/hash'):
            f.Caller(self.fonts / 'cjk.ttf', -1, '0' * 64, stack)
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); source, pdf = fixture(root, self.fonts)
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                f.inspect(source, pdf, '0' * 64, f.g.digest(pdf), self.inputs)
