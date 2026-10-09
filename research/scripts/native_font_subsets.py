#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compare native PDF subsets with pinned caller fonts, not viewer fonts.

Checks selected CID outlines and advances through fontTools independently of
the Rust subsetter. Paths stay in memory; reports contain counts/hashes only.
This is an unhinted outline/metric check, not a source-typography/raster oracle.
"""
import argparse
from collections import Counter
from contextlib import ExitStack
from fractions import Fraction as F
import hashlib
import io
import json
from pathlib import Path
import struct

from fontTools.cffLib import CFFFontSet
from fontTools.pens.recordingPen import DecomposingRecordingPen

import native_glyph_geometry as g

FONT_BYTES = 64 * 1024 * 1024
SUBSET_BYTES = 4 * 1024 * 1024
POINTS = 16384


class Recording(list):
    def __init__(self):
        super().__init__(); self.points = 0

    def append(self, value):
        self.points += len(value[1])
        g.require(len(self) < POINTS and self.points <= POINTS, 'glyph path limit')
        super().append(value)


class Pen(DecomposingRecordingPen):
    def __init__(self, glyphs):
        super().__init__(glyphs, skipMissingComponents=False)
        self.value, self.depth = Recording(), 0

    def addComponent(self, name, transform):
        g.require(self.depth < 16, 'glyph component depth')
        self.depth += 1
        try:
            super().addComponent(name, transform)
        finally:
            self.depth -= 1


def outline(glyphs, name, units):
    g.require(16 <= units <= 16384, 'font em range')
    pen = Pen(glyphs); glyphs[name].draw(pen)
    normalized = [(op, [None if point is None else [str(F(str(v)) / units) for v in point]
                       for point in points]) for op, points in pen.value]
    return hashlib.sha256(json.dumps(normalized, separators=(',', ':')).encode()).hexdigest()


class Caller:
    def __init__(self, path, face, sha, stack):
        g.require(path.stat().st_size <= FONT_BYTES and g.digest(path) == sha, 'caller font size/hash')
        self.path, self.sha, self.face = path, sha, face
        self.font = stack.enter_context(g.TTFont(path, fontNumber=face, lazy=True))
        g.require('fvar' not in self.font, 'variable caller font')
        self.units = self.font['head'].unitsPerEm
        self.cmap = self.font.getBestCmap()
        g.require(self.cmap is not None and len(self.cmap) <= 65536, 'caller cmap limit')
        g.require(len(self.font.getGlyphOrder()) <= 65536, 'caller glyph count limit')
        self.glyphs, self.cache = self.font.getGlyphSet(), {}

    def glyph(self, code):
        g.require(code in self.cmap, 'caller glyph unavailable')
        if code not in self.cache:
            name = self.cmap[code]
            self.cache[code] = (outline(self.glyphs, name, self.units),
                               F(self.font['hmtx'][name][0] * 1000, self.units))
        return self.cache[code]


def widths(cid):
    default = F(str(cid.get('/DW', 1000)))
    values, at, result = cid.get('/W', []), 0, {}
    g.require(len(values) <= 131072, 'width array limit')
    while at < len(values):
        g.require(at + 1 < len(values), 'partial width array')
        start, following = values[at], values[at + 1]
        g.require(isinstance(start, int) and 0 <= start <= 65535, 'width start')
        if isinstance(following, g.pikepdf.Array):
            g.require(len(following) <= 65536 - start, 'width extent')
            entries = enumerate(following, start); at += 2
        else:
            g.require(isinstance(following, int) and start <= following <= 65535
                      and at + 2 < len(values), 'width range')
            width = values[at + 2]
            entries = ((code, width) for code in range(start, following + 1)); at += 3
        for code, width in entries:
            g.require(code not in result, 'overlapping widths')
            result[code] = F(str(width))
    return default, result


class Subsets(g.Fonts):
    def __init__(self, auxiliary, stack):
        super().__init__(auxiliary, None)
        self.stack, self.programs, self.glyphs = stack, {}, {}
        self.types = Counter()

    def inspect(self, resource, code):
        super().inspect(resource, code)
        key = resource.objgen
        if key not in self.programs:
            g.require(len(resource.DescendantFonts) == 1, 'descendant font count')
            cid = resource.DescendantFonts[0]; fd = cid.FontDescriptor
            default, explicit = widths(cid)
            if cid.Subtype == g.pikepdf.Name('/CIDFontType2'):
                data = g.raw_stream(self.auxiliary, fd.FontFile2.objgen[0], SUBSET_BYTES)
                font = self.stack.enter_context(g.TTFont(io.BytesIO(data)))
                order = font.getGlyphOrder()
                g.require(len(order) <= 65536 and 'fvar' not in font, 'subset glyph profile')
                mapping = g.raw_stream(self.auxiliary, cid.CIDToGIDMap.objgen[0], 131072)
                g.require(len(mapping) % 2 == 0, 'partial CID map')
                names = [int.from_bytes(mapping[n:n + 2], 'big') for n in range(0, len(mapping), 2)]
                g.require(all(n < len(order) for n in names), 'CID glyph outside subset')
                names = {n: order[index] for n, index in enumerate(names)}
                glyphs, units = font.getGlyphSet(), font['head'].unitsPerEm
                advance = lambda name: F(font['hmtx'][name][0] * 1000, units)
                kind = 'TrueType'
            else:
                g.require(cid.Subtype == g.pikepdf.Name('/CIDFontType0')
                          and fd.FontFile3.Subtype == g.pikepdf.Name('/CIDFontType0C'), 'subset font type')
                data = g.raw_stream(self.auxiliary, fd.FontFile3.objgen[0], SUBSET_BYTES)
                font = CFFFontSet(); font.decompile(io.BytesIO(data), None)
                g.require(len(font.topDictIndex) == 1, 'CFF top dictionary count')
                top = font.topDictIndex[0]
                g.require(top.FontMatrix == [.001, 0, 0, .001, 0, 0]
                          and len(top.FDArray) <= 256
                          and all(getattr(d, 'FontMatrix', None) is None for d in top.FDArray),
                          'unmeasured CFF matrices')
                g.require(1 <= len(top.charset) <= 65536 and top.charset[0] == '.notdef', 'CFF charset limit')
                names = {0: '.notdef'}
                for name in top.charset[1:]:
                    g.require(name.startswith('cid') and name[3:].isdigit(), 'non-CID CFF charset')
                    value = int(name[3:])
                    g.require(1 <= value <= 65535 and value not in names, 'duplicate/outside CFF CID')
                    names[value] = name
                glyphs, units = top.CharStrings, 1000
                advance = lambda name: F(str(glyphs[name].width))
                kind = 'CFF'
            self.types[kind] += 1
            self.programs[key] = (glyphs, units, names, advance, default, explicit)
        if (key, code) not in self.glyphs:
            glyphs, units, names, advance, default, explicit = self.programs[key]
            g.require(code in names and names[code] != '.notdef', 'CID glyph missing')
            name = names[code]
            identity = outline(glyphs, name, units)
            self.glyphs[key, code] = {'outline': identity, 'advance': advance(name),
                                     'pdf_width': explicit.get(code, default), 'code': code}
        return self.glyphs[key, code]


def selection(want, callers):
    code = 0x25ba if want['kind'] == 'o' else ord(want['character'])
    role = 'latin' if want['kind'] == 'o' else want['role']
    # Published default-role fallback; optional roles were not supplied in
    # this measured baseline. Keep the one reported PUA approximation explicit.
    if role not in callers or code not in callers[role].cmap:
        role = 'cjk' if (0x2e80 <= code <= 0x9fff or 0xf900 <= code <= 0xfaff
                         or 0xfe10 <= code <= 0xfe1f or 0xfe30 <= code <= 0xfe6f
                         or 0xff00 <= code <= 0xffef) else 'latin'
    if code == 0xe6c7 and code not in callers[role].cmap:
        role, code = 'latin', 0x0403
    return role, code


def inspect(source, pdf, source_sha, pdf_sha, font_inputs):
    g.require(set(font_inputs) == {'cjk', 'latin'}, 'requires exactly two default caller fonts')
    g.require(g.digest(source) == source_sha and g.digest(pdf) == pdf_sha, 'input hash mismatch')
    pages, roles = [], Counter()
    with ExitStack() as stack:
        callers = {role: Caller(Path(item['path']), item['face'], item['sha256'], stack)
                   for role, item in font_inputs.items()}
        data = stack.enter_context(g.FileInput(source))
        doc = stack.enter_context(g.pikepdf.open(pdf)); auxiliary = stack.enter_context(g.fitz.open(pdf))
        reader = g.SourceExtractor(data, source_sha); variant = reader.header['variant']
        g.require(variant in ('C8', 'HN-B') and len(doc.pages) == reader.header['page_count'], 'native page profile')
        base = 0 if variant == 'C8' else 136
        mode = int.from_bytes(g.read_exact(data, base + 12, 4), 'little')
        origin = struct.unpack('<HH', g.read_exact(data, base + 28, 4))
        height = struct.unpack('<HH', g.read_exact(data, base + 32, 4))[1] + (100 if mode == 0 else 0)
        subsets = Subsets(auxiliary, stack)
        for row in reader.iter_pages():
            expected, source_order = g.source_model(data, row, variant, mode, origin, height)
            actual, pdf_order = g.pdf_glyphs(doc.pages[row['page_number'] - 1], subsets)
            errors = Counter()
            if len(expected) != len(actual) or source_order != pdf_order: errors['paint sequence'] += 1
            for want, got in zip(expected, actual):
                role, code = selection(want, callers); roles[role] += 1
                shape, advance = callers[role].glyph(code); drawn = got['role']
                if got['character'] != want['character'] or got['kind'] != want['kind']: errors['semantic/kind'] += 1
                if drawn['code'] != code: errors['display code'] += 1
                if drawn['outline'] != shape: errors['outline'] += 1
                if drawn['advance'] != advance: errors['font advance'] += 1
                if abs(drawn['pdf_width'] - advance) > F(1, 20000): errors['PDF width'] += 1
            pages.append({'page': row['page_number'], 'glyphs': len(expected), 'errors': dict(errors),
                          'replacements': sum(x['replacement'] for x in actual), 'status': 'FAIL' if errors else 'PASS'})
        summary = {'font_programs': dict(subsets.types), 'unique_resource_cids': len(subsets.glyphs),
                   'selected_role_counts': dict(roles)}
        g.require(not doc.get_warnings(), 'PDF parser warnings')
    g.require(g.digest(source) == source_sha and g.digest(pdf) == pdf_sha, 'input changed')
    g.require(all(g.digest(c.path) == c.sha for c in callers.values()), 'caller font changed')
    return {'source_sha256': source_sha, 'pdf_sha256': pdf_sha, 'pages': pages, **summary,
            'status': 'PASS' if all(x['status'] == 'PASS' for x in pages) else 'FAIL'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path); parser.add_argument('pdf', type=Path)
    parser.add_argument('fonts', type=Path, help='external cjk/latin path, face and sha256 JSON')
    parser.add_argument('--source-sha256', required=True); parser.add_argument('--pdf-sha256', required=True)
    args = parser.parse_args()
    g.require(args.fonts.stat().st_size <= 65536, 'font manifest limit')
    result = inspect(args.source, args.pdf, args.source_sha256, args.pdf_sha256, json.loads(args.fonts.read_text()))
    print(json.dumps(result, indent=2)); raise SystemExit(result['status'] != 'PASS')
