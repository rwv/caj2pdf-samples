# SPDX-License-Identifier: MIT
"""Original source/font/PDF pairs and deliberate glyph corruptions."""
from fractions import Fraction as F
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

import pikepdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cajviewer'))
import native_glyph_geometry as g
from native_glyph_model import Model
from composition_marker_fonts import generate, ROLES


def fixture(root, fonts, ornament=False):
    words = (0x8002, 0x1084, 0x8001, 230, 120, 0xd6d0)
    if ornament:
        words += (0x8010, 1, 120, 270, 210, 270, 0x8006, 0xa385, 100, 300, 200, 300)
    words += (280, 0xa0c1, 0x8004, 0)
    records = struct.pack('<' + 'H' * len(words), *words)
    data = bytearray(100)
    data[:4] = b'\xc8\0\0\0'
    struct.pack_into('<II', data, 8, 1, 2)
    struct.pack_into('<4H', data, 28, 100, 200, 400, 500)
    struct.pack_into('<5I', data, 80, 100, len(records), 0, 0, 100 + len(records))
    source = root / 'original.caj'; source.write_bytes(data + records)
    pdf = root / 'original.pdf'
    # Independently authored from the published field-4 observations. No
    # geometry evaluator supplies these coordinates or the page dimensions.
    em = F(2625, 301)
    matrices = ((em, 0, 0, em, F(9600, 2473), F(116400, 2473) - em),
                (em, 0, 0, em, F(48000, 2473) + F(2625, 2408), F(114480, 2473) - em))
    with pikepdf.new() as doc:
        page = doc.add_blank_page(page_size=(float(F(96000, 2473)), float(F(120000, 2473))))
        resources = pikepdf.Dictionary()
        for name, role in (('/Arbitrary9', 'cjk'), ('/Unrelated3', 'latin')):
            program = doc.make_stream((fonts / (role + '.ttf')).read_bytes())
            descriptor = doc.make_indirect(pikepdf.Dictionary(Type=pikepdf.Name('/FontDescriptor'),
                FontName=pikepdf.Name('/Original'), Flags=4, FontBBox=[0, 0, 1000, 1000],
                ItalicAngle=0, Ascent=1000, Descent=0, CapHeight=1000, StemV=80, FontFile2=program))
            descendant = doc.make_indirect(pikepdf.Dictionary(Type=pikepdf.Name('/Font'),
                Subtype=pikepdf.Name('/CIDFontType2'), BaseFont=pikepdf.Name('/Original'),
                CIDSystemInfo=pikepdf.Dictionary(Registry='Adobe', Ordering='Identity', Supplement=0),
                FontDescriptor=descriptor, DW=1000, CIDToGIDMap=doc.make_stream(b'\0\1' * 65536)))
            cmap = doc.make_stream(b'/CIDInit /ProcSet findresource begin 12 dict begin begincmap\n'
                b'/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n'
                b'/CMapName /OriginalUnicode def /CMapType 2 def\n'
                b'1 begincodespacerange <0000> <FFFF> endcodespacerange\n'
                b'1 beginbfrange <0000> <FFFF> <0000> endbfrange\n'
                b'endcmap CMapName currentdict /CMap defineresource pop end end\n')
            resources[name] = doc.make_indirect(pikepdf.Dictionary(Type=pikepdf.Name('/Font'),
                Subtype=pikepdf.Name('/Type0'), BaseFont=pikepdf.Name('/Original'),
                Encoding=pikepdf.Name('/Identity-H'), DescendantFonts=[descendant], ToUnicode=cmap))
        page.Resources.Font = resources
        lines = []
        for matrix, name, code in zip(matrices, ('/Arbitrary9', '/Unrelated3'), ('4E2D', '0041')):
            values = ' '.join(str(float(v)) for v in matrix)
            lines.append(f'q 0.266667 g BT {name} 1 Tf {values} Tm <{code}> Tj ET Q\n')
        if ornament:
            decoration = []
            # A 90-unit span is slightly wider than one em: two marks, with
            # only the last sliver of the second visible at the endpoint.
            for i in range(2):
                matrix = (em, 0, 0, em, F(4800, 2473) + i * em, F(103200, 2473) - em / 2)
                clip = (F(4800, 2473), 0, F(21600, 2473), F(120000, 2473))
                decoration.append('q ' + ' '.join(str(float(v)) for v in clip) + ' re W n '
                    '/Artifact BMC /Span << /ActualText () >> BDC BT /Unrelated3 1 Tf '
                    + ' '.join(str(float(v)) for v in matrix) + ' Tm <25BA> Tj ET EMC EMC Q\n')
            decoration.append('q 0 w 1 2 m 3 4 l S Q\n')  # Only kind/order belongs to this checker.
            lines[1:1] = decoration
        page.Contents = doc.make_stream(''.join(lines).encode())
        doc.save(pdf)
    return source, pdf


class GlyphGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        generate([name + '.ttf' for name in ROLES] + ['OriginalSymbols.TTF'], cls.root / 'fonts')
        cls.fonts = cls.root / 'fonts/pdf'

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_complete_original_pair_and_cli(self):
        with tempfile.TemporaryDirectory() as name:
            source, pdf = fixture(Path(name), self.fonts)
            for marker_directory in (None, self.fonts):
                report = g.inspect(source, pdf, g.digest(source), g.digest(pdf), marker_directory)
                self.assertEqual(report['status'], 'PASS')
                self.assertEqual(report['pages'][0]['source_role_counts'], {'cjk': 1, 'latin': 1})
                self.assertEqual(report['pages'][0]['marker_roles_checked'], marker_directory is not None)
            process = subprocess.run([sys.executable, g.__file__, str(source), str(pdf),
                '--source-sha256', g.digest(source), '--pdf-sha256', g.digest(pdf)], capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(json.loads(process.stdout)['status'], 'PASS')

    def test_geometry_gray_identity_order_and_resource_mutations_fail(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); source, original = fixture(root, self.fonts)
            for mutation in ('x', 'y', 'width', 'height', 'shear', 'gray', 'character', 'order', 'omission', 'duplicate', 'resource'):
                with self.subTest(mutation=mutation), pikepdf.open(original) as doc:
                    page = doc.pages[0]; content = page.Contents.read_bytes()
                    if mutation in ('x', 'y', 'width', 'height', 'shear'):
                        operations = list(pikepdf.parse_content_stream(page))
                        for i, (operands, operator) in enumerate(operations):
                            if str(operator) == 'Tm':
                                values = list(operands); slot = {'width': 0, 'height': 3, 'shear': 2, 'x': 4, 'y': 5}[mutation]
                                values[slot] = float(values[slot]) + 1
                                operations[i] = pikepdf.ContentStreamInstruction(values, operator)
                                break
                        content = pikepdf.unparse_content_stream(operations)
                    elif mutation == 'gray': content = content.replace(b'0.266667 g', b'0 g')
                    elif mutation == 'character': content = content.replace(b'<0041>', b'<0042>')
                    elif mutation == 'order': content = b'\n'.join(reversed(content.splitlines()))
                    elif mutation == 'omission': content = content.splitlines()[0]
                    elif mutation == 'duplicate': content += content.splitlines()[0]
                    else: page.Resources.Font.Arbitrary9 = page.Resources.Font.Unrelated3
                    page.Contents = doc.make_stream(content); changed = root / (mutation + '.pdf'); doc.save(changed)
                    report = g.inspect(source, changed, g.digest(source), g.digest(changed), self.fonts)
                    self.assertEqual(report['status'], 'FAIL', mutation)
            process = subprocess.run([sys.executable, g.__file__, str(source), str(changed),
                '--source-sha256', g.digest(source), '--pdf-sha256', g.digest(changed),
                '--original-marker-directory', str(self.fonts)], capture_output=True, text=True)
            self.assertEqual(process.returncode, 1, process.stderr)

    def test_font_widths_and_actual_cid_mapping_are_checked(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); source, original = fixture(root, self.fonts)
            for kind in ('default-width', 'explicit-width', 'cid-glyph', 'direct-resource'):
                with pikepdf.open(original) as doc:
                    cid = doc.pages[0].Resources.Font.Arbitrary9.DescendantFonts[0]
                    if kind == 'default-width': cid.DW = 500
                    elif kind == 'explicit-width': cid.W = [0x4e2d, [500]]
                    elif kind == 'cid-glyph': cid.CIDToGIDMap = doc.make_stream(b'\0\2' * 65536)
                    else:
                        fonts = doc.pages[0].Resources.Font
                        fonts.Arbitrary9 = pikepdf.Dictionary(fonts.Arbitrary9)
                    changed = root / (kind + '.pdf'); doc.save(changed)
                with self.subTest(kind=kind), self.assertRaises(ValueError):
                    g.inspect(source, changed, g.digest(source), g.digest(changed), self.fonts)

    def test_ornament_endpoint_clipping_repetition_and_painting_order(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); source, original = fixture(root, self.fonts, ornament=True)
            report = g.inspect(source, original, g.digest(source), g.digest(original), self.fonts)
            self.assertEqual(report['status'], 'PASS')
            page = report['pages'][0]
            self.assertEqual((page['source_glyphs'], page['source_ornament_records'], page['pdf_ornament_marks']), (2, 1, 2))
            self.assertEqual(page['source_paint_events'], 5)
            for kind in ('clip', 'spacing', 'omit', 'duplicate', 'order', 'vector-order', 'gray'):
                with self.subTest(kind=kind), pikepdf.open(original) as doc:
                    page = doc.pages[0]; lines = page.Contents.read_bytes().splitlines(keepends=True)
                    if kind == 'clip':
                        values = lines[1].split(); values[3] = b'1'; lines[1] = b' '.join(values) + b'\n'
                    elif kind == 'spacing': lines[2] = lines[1]
                    elif kind == 'omit': del lines[2]
                    elif kind == 'duplicate': lines.insert(2, lines[1])
                    elif kind == 'order': lines[0], lines[1] = lines[1], lines[0]
                    elif kind == 'vector-order': lines.insert(0, lines.pop(3))
                    else: lines[1] = lines[1].replace(b' BT ', b' 0.5 g BT ')
                    page.Contents = doc.make_stream(b''.join(lines)); changed = root / (kind + '.pdf'); doc.save(changed)
                    self.assertEqual(g.inspect(source, changed, g.digest(source), g.digest(changed), self.fonts)['status'], 'FAIL')
            for content in (b'/ActualText <FEFF0041>', b'/ActualText <0041>'):
                with pikepdf.open(original) as doc:
                    page = doc.pages[0]
                    page.Contents = doc.make_stream(page.Contents.read_bytes().replace(b'/ActualText ()', content))
                    changed = root / 'semantic.pdf'; doc.save(changed)
                with self.assertRaises(ValueError):
                    g.inspect(source, changed, g.digest(source), g.digest(changed), self.fonts)

    def test_unmeasured_ornament_profiles_are_refused(self):
        m = Model('C8', 2, (100, 200), 500); m.style = 0x1084
        for value, points in ((3, (120, 270, 210, 270)), (1, (210, 270, 120, 270)), (1, (120, 270, 210, 271))):
            with self.assertRaises(ValueError): m.ornaments(value, points)
        m.axes = (34, 40)
        with self.assertRaises(ValueError): m.ornaments(1, (120, 270, 210, 270))
        m.axes = (34, 34)
        with self.assertRaises(ValueError): m.ornaments(117, (120, 270, 210, 270))

    def test_resource_state_reset_axes_and_shear_following_glyph(self):
        m = Model('C8', 2, (100, 200), 500); m.y = 230; m.style = 0x10a5
        m.control(None, 0, 0x801d, 28)
        self.assertEqual(m.glyph(120, 0xa0c1)['role'], 'latin-state28')
        self.assertEqual(m.glyph(120, 0xa1ce)['role'], 'latin')
        self.assertEqual(m.glyph(120, 0xa0c1)['role'], 'latin')
        m.control(None, 0, 0x8070, 34); m.control(None, 0, 0x8071, 34)
        m.control(None, 0, 0x8024, 0x281c)
        self.assertEqual(m.glyph(120, 0xd6d0)['matrix'][:4], (F(2550, 301), 0, F(2295, 1204), F(2550, 301)))
        m.control(None, 0, 0x8002, 0x1084)
        self.assertEqual(m.axes, (None, None)); self.assertEqual(m.shear, F(9, 40))

    def test_legacy_digit_alphabet_symbol_and_hyphen_are_distinct(self):
        m = Model('HN-B', 0, (100, 200), 600); m.y = 230; m.style = 0x1084
        chinese, digit, latin, alternate, symbol, hyphen = [m.glyph(120, code) for code in (0xd6d0, 0xa3b1, 0xa3c1, 0xa980, 0xa3db, 0xaab2)]
        self.assertEqual([x['role'] for x in (chinese, digit, latin, alternate, symbol, hyphen)], ['cjk', 'latin', 'latin', 'alternate-latin', 'symbols', 'symbols'])
        self.assertEqual(digit['matrix'][4] - chinese['matrix'][4], F(-5280, 2473))
        self.assertEqual(digit['matrix'][5] - chinese['matrix'][5], F(-4320, 2473))
        self.assertEqual(latin['matrix'][5] - chinese['matrix'][5], F(-2400, 2473))
        self.assertEqual(hyphen['matrix'][4] - chinese['matrix'][4], F(-7920, 2473))
        self.assertEqual(symbol['matrix'], chinese['matrix'])

    def test_neighboring_unmeasured_styles_and_classes_are_refused(self):
        for variant, mode, style, code, axes in (
            ('C8', 2, 0x1400, 0xd6d0, (None, None)),
            ('C8', 2, 0x1084, 0xd6d0, (43, 43)),
            ('C8', 2, 0xb94c, 0xa0c1, (None, None)),
            ('HN-B', 0, 0x1084, 0xa6b8, (None, None)),
            ('HN-B', 0, 0x1084, 0xd6d0, (28, 28)),
            ('HN-B', 2, 0x1084, 0xa6c2, (None, None)),
        ):
            m = Model(variant, mode, (100, 200), 500)
            m.style, m.y, m.axes = style, 230, axes
            with self.subTest(variant=variant, mode=mode, style=style, code=code), self.assertRaises(ValueError):
                m.glyph(120, code)

    def test_unknown_clipping_transform_encoding_and_hashes_refused(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); source, original = fixture(root, self.fonts)
            for prefix in (b'1 0 0 1 3 0 cm ', b'0 0 1 1 re W n ', b'2 Tr '):
                with pikepdf.open(original) as doc:
                    page = doc.pages[0]; page.Contents = doc.make_stream(prefix + page.Contents.read_bytes())
                    changed = root / 'bad.pdf'; doc.save(changed)
                with self.assertRaises(ValueError):
                    g.inspect(source, changed, g.digest(source), g.digest(changed))
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                g.inspect(source, original, '0' * 64, g.digest(original))
            with pikepdf.open(original) as doc:
                doc.pages[0].Resources.Font.Arbitrary9.Encoding = pikepdf.Name('/WinAnsiEncoding')
                changed = root / 'encoding.pdf'; doc.save(changed)
            with self.assertRaises(ValueError):
                g.inspect(source, changed, g.digest(source), g.digest(changed))


if __name__ == '__main__':
    unittest.main()
