#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Bounded glyph-model verification; optionally identify original marker roles.

Marker font inputs must be this project's generated diagnostic fonts. Their
original outlines may be inspected; vendor/real font outlines are never needed.
Ordinary PDFs are checked for geometry, color and semantic order only.
"""
import argparse
from collections import Counter
from fractions import Fraction as F
import hashlib
import io
import json
from pathlib import Path
import struct

import fitz
import pikepdf
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

from hnc8_layout_source import FileInput, SourceExtractor
from native_glyph_model import source_model
from native_text_order import digest, identity_cmap, raw_stream, read_exact
from native_vector_geometry import IDENTITY, MAX_OPERATIONS, inherited
from source_image_geometry import UNIT, TOLERANCE, multiply, pdf_content, require, residual

ROLES = ('cjk', 'latin', 'alternate-latin', 'symbols', 'latin-state3', 'latin-state28', 'latin-state31')
FONT_LIMIT = 4 * 1024 * 1024


def marker_identity(font, name):
    glyph = font['glyf'][name]
    require(0 <= glyph.numberOfContours <= 8, 'non-original marker contour profile')
    coordinates, _, _ = glyph.getCoordinates(font['glyf'])
    require(len(coordinates) <= 128 and not glyph.program.getBytecode(), 'marker point/instruction limit')
    pen = RecordingPen()
    font.getGlyphSet()[name].draw(pen)
    units = font['head'].unitsPerEm
    require(font['hmtx'][name][0] == units, 'non-full-em marker advance')
    value = [units, font['hmtx'][name], pen.value]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def original_markers(directory):
    identities, hashes = {}, {}
    for role in ROLES:
        path = directory / (role + '.ttf')
        require(path.stat().st_size <= FONT_LIMIT, 'marker font limit')
        with TTFont(path) as font:
            identity = marker_identity(font, 'square')
        require(identity not in identities, 'ambiguous marker roles')
        identities[identity] = role
        hashes[role] = digest(path)
    return identities, hashes


def marker_widths(cid):
    # These original markers all advance one em. Verify PDF widths as well
    # as the embedded TrueType metrics; resource names alone prove neither.
    require(F(str(cid.get('/DW', 1000))) == 1000, 'marker default width')
    values, at, count = cid.get('/W', []), 0, 0
    require(len(values) <= 131072, 'marker width array limit')
    while at < len(values):
        require(at + 1 < len(values), 'partial width array')
        start, following = values[at], values[at + 1]
        require(isinstance(start, int) and 0 <= start <= 65535, 'width CID')
        if isinstance(following, pikepdf.Array):
            require(start + len(following) <= 65536, 'width CID range')
            require(all(F(str(x)) == 1000 for x in following), 'marker explicit width')
            count += len(following); at += 2
        else:
            require(isinstance(following, int) and start <= following <= 65535
                    and at + 2 < len(values), 'width range end')
            require(F(str(values[at + 2])) == 1000, 'marker range width')
            count += following - start + 1; at += 3
        require(count <= 65536, 'marker total width limit')


class Fonts:
    def __init__(self, auxiliary, markers):
        self.auxiliary, self.markers, self.cache = auxiliary, markers, {}

    def inspect(self, resource, code):
        key = resource.objgen
        require(key[0] > 0, 'unmeasured direct font resource')
        if key not in self.cache:
            require(len(self.cache) < 64, 'document font resource limit')
            require(resource.Subtype == pikepdf.Name('/Type0') and resource.Encoding == pikepdf.Name('/Identity-H'),
                    'unmeasured PDF font encoding')
            require(identity_cmap(raw_stream(self.auxiliary, resource.ToUnicode.objgen[0], 65536)),
                    'nonidentity Unicode map')
            record = None
            if self.markers is not None:
                cid = resource.DescendantFonts[0]
                require(cid.Subtype == pikepdf.Name('/CIDFontType2'), 'unmeasured marker font type')
                marker_widths(cid)
                data = raw_stream(self.auxiliary, cid.FontDescriptor.FontFile2.objgen[0], FONT_LIMIT)
                mapping = raw_stream(self.auxiliary, cid.CIDToGIDMap.objgen[0], 131072)
                require(len(mapping) % 2 == 0, 'partial CID map')
                with TTFont(io.BytesIO(data)) as font:
                    order = font.getGlyphOrder()
                    require(len(order) <= 8, 'marker subset glyph limit')
                    roles = [self.markers.get(marker_identity(font, name)) if font['glyf'][name].numberOfContours else None
                             for name in order]
                record = mapping, roles
            self.cache[key] = record
        record = self.cache[key]
        if record is None:
            return None
        mapping, roles = record
        require(2 * code + 2 <= len(mapping), 'CID outside marker map')
        gid = int.from_bytes(mapping[2 * code:2 * code + 2], 'big')
        require(gid < len(roles) and roles[gid] is not None, 'unidentified marker glyph')
        return roles[gid]


def pdf_glyphs(page, fonts):
    pdf_content(page)
    require(inherited(page, '/Rotate', 0) == 0 and page.get('/UserUnit', 1) == 1
            and page.get('/Group') is None, 'PDF page transform/group')
    state = {'matrix': IDENTITY, 'gray': F(0), 'font': None, 'size': None,
             'clip': None, 'blend': '/Normal'}
    stack, marked, result, painting, path = [], [], [], [], []
    pending_clip = False
    text, matrix, fresh_matrix = False, None, False
    passive = {'w', 'J', 'j', 'M', 'G'}
    for number, (args, operator) in enumerate(pikepdf.parse_content_stream(page)):
        require(number < MAX_OPERATIONS, 'PDF operation limit')
        op = str(operator)
        require(not pending_clip or op == 'n', 'unfinished clipping path')
        if op == 'q':
            require(not args and len(stack) < 32, 'graphics stack bound')
            stack.append(state.copy())
        elif op == 'Q':
            require(not args and stack, 'unbalanced restore')
            state = stack.pop()
        elif op == 'cm':
            require(len(args) == 6, 'matrix arity')
            state['matrix'] = tuple(multiply(state['matrix'], [F(str(x)) for x in args]))
        elif op == 'g':
            require(len(args) == 1, 'gray arity')
            state['gray'] = F(str(args[0]))
        elif op == 'BT':
            require(not args and not text, 'nested text')
            text, matrix, fresh_matrix = True, None, False
        elif op == 'ET':
            require(not args and text, 'text close')
            text = False
        elif op == 'Tf':
            require(text and len(args) == 2, 'font selection')
            state['font'], state['size'] = str(args[0]), F(str(args[1]))
        elif op == 'Tm':
            require(text and len(args) == 6, 'text matrix')
            matrix, fresh_matrix = tuple(F(str(x)) for x in args), True
        elif op in ('BMC', 'BDC'):
            require(len(marked) < 2, 'marked nesting bound')
            if op == 'BMC':
                require(not marked and len(args) == 1 and str(args[0]) == '/Artifact', 'unmeasured artifact')
                marked.append(('artifact', None))
            else:
                require((not marked or marked == [('artifact', None)]) and len(args) == 2
                        and str(args[0]) == '/Span' and set(args[1].keys()) == {'/ActualText'}, 'unmeasured text span')
                value = bytes(args[1].ActualText)
                require(not value or (len(value) == 4 and value.startswith(b'\xfe\xff')), 'ActualText encoding/limit')
                marked.append(('actual', value.removeprefix(b'\xfe\xff').decode('utf-16-be')))
        elif op == 'EMC':
            require(not args and marked, 'unbalanced marked context')
            marked.pop()
        elif op in ('m', 'l', 're'):
            require(len(path) < 8 and len(args) == (4 if op == 're' else 2), 'path bound/arity')
            path.append((op, tuple(F(str(x)) for x in args)))
        elif op == 'W':
            require(not args and state['clip'] is None and state['matrix'] == IDENTITY
                    and len(path) == 1 and path[0][0] == 're', 'unmeasured clipping path')
            state['clip'], pending_clip = path[0][1], True
        elif op in ('n', 'S'):
            require(not args, 'path end arity')
            if op == 'S':
                require(path, 'empty stroke'); painting.append('v')
            path, pending_clip = [], False
        elif op == 'gs':
            require(len(args) == 1, 'graphics state arity')
            params = page.Resources.ExtGState[str(args[0])]
            require(set(params.keys()) == {'/Type', '/BM'} and params.Type == pikepdf.Name('/ExtGState')
                    and params.BM in (pikepdf.Name('/Normal'), pikepdf.Name('/Multiply')), 'unmeasured graphics state')
            state['blend'] = str(params.BM)
        elif op == 'Do':
            require(len(args) == 1 and page.Resources.XObject[str(args[0])].Subtype == pikepdf.Name('/Image'),
                    'unmeasured image/form')
            painting.append('i')
        elif op == 'Tj':
            require(text and fresh_matrix and state['size'] == 1 and len(args) == 1, 'unmeasured glyph operation')
            fresh_matrix = False
            data = bytes(args[0]); require(len(data) == 2, 'non-BMP glyph string')
            ornament = bool(marked and marked[0][0] == 'artifact')
            require(state['matrix'] == IDENTITY and state['blend'] == '/Normal' and not path,
                    'unmeasured glyph graphics state')
            display = data.decode('utf-16-be')
            semantic = marked[-1][1] if marked else display
            if ornament:
                require(marked == [('artifact', None), ('actual', '')] and state['clip'] is not None,
                        'ornament semantics/clip')
            else:
                require(len(semantic) == 1 and state['clip'] is None, 'ordinary glyph semantics/clip')
            role = fonts.inspect(page.Resources.Font[state['font']], int.from_bytes(data, 'big'))
            result.append({'matrix': matrix, 'gray': state['gray'], 'role': role,
                           'character': semantic, 'replacement': not ornament and display != semantic,
                           'kind': 'o' if ornament else 'g', 'clip': state['clip']})
            painting.append('o' if ornament else 'g')
        else:
            require(op in passive, 'unmeasured PDF operator: ' + op)
    require(not stack and not marked and not text and not path and not pending_clip, 'unfinished PDF state')
    return result, painting


def compare(expected, actual, marker_roles):
    reasons, failures, maximum = Counter(), [], F(0)
    if len(expected) != len(actual):
        reasons['glyph count'] += 1
    for number, (want, got) in enumerate(zip(expected, actual), 1):
        delta = residual(got['matrix'], want['matrix']); maximum = max(maximum, delta)
        errors = []
        if delta > TOLERANCE: errors.append('matrix')
        if abs(got['gray'] - want['gray']) > F(1, 1000000): errors.append('gray')
        if got['character'] != want['character']: errors.append('semantic order')
        if got['kind'] != want['kind']: errors.append('glyph kind')
        if (got['clip'] is None) != (want['clip'] is None): errors.append('clip presence')
        elif want['clip'] is not None and residual(got['clip'], want['clip']) > TOLERANCE: errors.append('clip geometry')
        if marker_roles and got['role'] != want['role']: errors.append('marker role')
        if errors:
            reasons.update(errors)
            if len(failures) < 16:
                failures.append({'ordinal': number, 'profile': want['profile'], 'errors': errors,
                                 'matrix_delta_points': float(delta),
                                 'expected_role': want['role'], 'actual_role': got['role']})
    return {'status': 'FAIL' if reasons else 'PASS',
            'source_glyphs': sum(g['kind'] == 'g' for g in expected), 'pdf_glyphs': sum(g['kind'] == 'g' for g in actual),
            'source_ornament_records': sum(g.get('record_start', False) for g in expected),
            'source_ornament_marks': sum(g['kind'] == 'o' for g in expected), 'pdf_ornament_marks': sum(g['kind'] == 'o' for g in actual),
            'maximum_matrix_delta_points': float(maximum), 'failure_counts': dict(reasons),
            'first_failures': failures, 'actual_text_replacements': sum(g['replacement'] for g in actual),
            'source_role_counts': dict(Counter(g['role'] for g in expected)),
            'source_state_counts': dict(sorted(Counter(g['state'] for g in expected).items())),
            'marker_roles_checked': marker_roles}


def inspect(source, pdf, source_sha, pdf_sha, marker_directory=None):
    require(digest(source) == source_sha and digest(pdf) == pdf_sha, 'input hash mismatch')
    markers, font_hashes = original_markers(marker_directory) if marker_directory else (None, {})
    pages = []
    with FileInput(source) as data, pikepdf.open(pdf) as output, fitz.open(pdf) as auxiliary:
        reader = SourceExtractor(data, source_sha); variant = reader.header['variant']
        require(variant in ('C8', 'HN-B') and len(output.pages) == reader.header['page_count'], 'native page profile')
        base = 0 if variant == 'C8' else 136
        mode = int.from_bytes(read_exact(data, base + 12, 4), 'little')
        require(mode == 2 or (variant == 'HN-B' and mode == 0), 'native mode')
        origin = struct.unpack('<HH', read_exact(data, base + 28, 4))
        extent = [x + (100 if mode == 0 else 0) for x in struct.unpack('<HH', read_exact(data, base + 32, 4))]
        fonts = Fonts(auxiliary, markers)
        for row in reader.iter_pages():
            page = output.pages[row['page_number'] - 1]
            box = [F(0), F(0), extent[0] * UNIT, extent[1] * UNIT]
            require(residual(inherited(page, '/MediaBox'), box) <= TOLERANCE
                    and residual(inherited(page, '/CropBox', inherited(page, '/MediaBox')), box) <= TOLERANCE,
                    'page/crop geometry')
            expected, source_painting = source_model(data, row, variant, mode, origin, extent[1])
            actual, pdf_painting = pdf_glyphs(page, fonts)
            checked = compare(expected, actual, markers is not None)
            checked['painting_order_matches'] = source_painting == pdf_painting
            checked['source_paint_events'], checked['pdf_paint_events'] = len(source_painting), len(pdf_painting)
            if source_painting != pdf_painting:
                checked['status'] = 'FAIL'; checked['failure_counts']['painting order'] = 1
            pages.append({'page': row['page_number'], **checked})
    require(digest(source) == source_sha and digest(pdf) == pdf_sha, 'inputs changed')
    if marker_directory:
        require(all(digest(marker_directory / (r + '.ttf')) == h for r, h in font_hashes.items()), 'marker inputs changed')
    return {'source_sha256': source_sha, 'pdf_sha256': pdf_sha, 'variant': variant, 'native_mode': mode,
            'pages': pages, 'status': 'PASS' if all(p['status'] == 'PASS' for p in pages) else 'FAIL',
            'source_and_pdf_unchanged': True, 'marker_font_sha256': font_hashes,
            'scope': 'Existing glyph geometry/color/semantic models and optional original marker roles; not vendor-font or raster fidelity'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path); parser.add_argument('pdf', type=Path)
    parser.add_argument('--source-sha256', required=True); parser.add_argument('--pdf-sha256', required=True)
    parser.add_argument('--original-marker-directory', type=Path)
    args = parser.parse_args()
    result = inspect(args.source, args.pdf, args.source_sha256, args.pdf_sha256, args.original_marker_directory)
    print(json.dumps(result, indent=2)); raise SystemExit(0 if result['status'] == 'PASS' else 1)
