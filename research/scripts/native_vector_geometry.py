#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check measured native vector models and their order among other paint events.

Independent source measurements: c8-native-records.md (segments),
c8-native-controls.md (radicals), hnb-compact-index.md (mode 0), and the
Rust provenance section for #391 (8007). This verifies those existing models,
not source pixels, glyph transforms, font outlines, or decoration appearance.
"""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import struct

import pikepdf

from hnc8_layout_source import FileInput, SourceExtractor
from native_text_order import digest, read_exact, source_glyphs
from source_image_geometry import UNIT, TOLERANCE, multiply, pdf_content, require, residual

IDENTITY = tuple(map(Fraction, (1, 0, 0, 1, 0, 0)))
MAX_OPERATIONS = 131072


def source_vectors(source, page, variant, mode, origin, height):
    vectors, painting = [], []
    gray = Fraction(68, 255)

    def visit(at, tag, value, size):
        nonlocal gray
        if tag < 0x8000:
            painting.append('g')
        elif tag in (0x800a, 0x810a):
            painting.append('i')
        elif tag == 0x8010:
            require(value in (1, 2, 46, 117), 'unmeasured decoration')
        elif tag == 0x81ff and value in (1, 2, 3):
            require(read_exact(source, at + 4, 4) == struct.pack('<HH', 0, 200),
                    'unmeasured color payload')
            gray = Fraction(0)
        elif tag in (0x8006, 0x8007, 0x8008, 0x8090):
            require(size == 12, 'drawing record size')
            x, y, u, v = struct.unpack('<4H', read_exact(source, at + 4, 8))
            if tag == 0x8090:
                require(variant == 'C8' and mode == 2, 'radical profile')
                require(x & 0xc000 in (0, 0xc000) and u & 0xc000 == x & 0xc000
                        and y < 0x4000 and v < 0x4000, 'radical marker bits')
                x, u = x & 0x3fff, u & 0x3fff
                require(u >= 30 and v >= 45, 'radical dimensions')
                points = [(x - 45, y + v - 25), (x - 25, y + v - 45),
                          (x + 10, y + v), (x + 30, y), (x + u + 20, y)]
                width, color = 4 * UNIT, gray
            else:
                require((tag == 0x8006 and value in (0xa381, 0xa383, 0xa385, 0xa38b))
                        or (variant == 'C8' and (tag, value) in ((0x8006, 0xa387), (0x8006, 0xa38d),
                            (0x8007, 0xa380), (0x8007, 0xa382), (0x8008, 0xa380))), 'segment style')
                if tag == 0x8008 or value in (0xa387, 0xa38d):
                    require(all(word < 0x4000 for word in (x, y, u, v)), 'unmeasured segment flags')
                require(mode == 2 or (variant == 'HN-B' and mode == 0
                                     and tag == 0x8006 and value == 0xa385), 'segment mode')
                if value == 0xa385 and x & 0xc000 == 0xc000:
                    x &= 0x3fff
                if mode == 0 and u & 0xc000 == 0xc000:
                    u &= 0x3fff
                margin_y = 15 if mode == 0 else 20
                points = [(x + 20, y + margin_y), (u + 20, v + margin_y)]
                width, color = Fraction(0), Fraction(0)
            points = [(UNIT * (x - origin[0]), UNIT * (height - y + origin[1]))
                      for x, y in points]
            vectors.append({'record': f'{tag:04x}/{value:04x}', 'points': points,
                            'width': width, 'gray': color})
            painting.append('v')

    source_glyphs(source, page, variant, mode, record_visitor=visit)
    return vectors, painting


def inherited(page, key, default=None):
    node = page.obj
    for _ in range(32):
        if key in node:
            return node[key]
        node = node.get('/Parent')
        if node is None:
            return default
    raise ValueError('page ancestor depth limit')


def pdf_vectors(page):
    # Enforce bounded stream decoding before the library parses instructions.
    pdf_content(page)
    require(inherited(page, '/Rotate', 0) == 0 and page.get('/UserUnit', 1) == 1
            and page.get('/Group') is None,
            'unmeasured PDF page transform')
    state = {'matrix': IDENTITY, 'gray': Fraction(0), 'width': Fraction(1),
             'cap': 0, 'join': 0, 'miter': Fraction(10), 'clipped': False,
             'blend': '/Normal'}
    stack, marked, path, vectors, painting = [], [], [], [], []
    # Text geometry is outside this check; these operators do not alter strokes.
    passive = {'BT', 'ET', 'Tf', 'Tm', 'g'}
    for number, (args, operator) in enumerate(pikepdf.parse_content_stream(page)):
        require(number < MAX_OPERATIONS, 'PDF operation budget')
        op = str(operator)
        if op == 'q':
            require(not args and len(stack) < 32, 'graphics stack bound')
            stack.append(state.copy())
        elif op == 'Q':
            require(not args and stack, 'unbalanced graphics restore')
            state = stack.pop()
        elif op == 'cm':
            # Image matrices are local. A transformed vector is deliberately
            # outside this narrow checker rather than compared in wrong units.
            require(len(args) == 6, 'matrix arity')
            state['matrix'] = tuple(multiply(state['matrix'], [Fraction(str(x)) for x in args]))
            require(not path, 'matrix changes inside path')
        elif op in ('G', 'w', 'J', 'j', 'M'):
            require(len(args) == 1, 'stroke parameter arity')
            state[{'G': 'gray', 'w': 'width', 'J': 'cap', 'j': 'join', 'M': 'miter'}[op]] = Fraction(str(args[0]))
        elif op in ('m', 'l'):
            require(len(args) == 2 and len(path) < 8, 'path point bound')
            require(state['matrix'] == IDENTITY, 'transformed vector')
            require((op == 'm') == (not path), 'multiple/missing subpath')
            path.append(tuple(Fraction(str(x)) for x in args))
        elif op == 'S':
            require(not args and len(path) >= 2, 'incomplete stroke')
            require(not state['clipped'] and state['blend'] == '/Normal'
                    and not marked, 'clipped/blended/marked stroke')
            require(state['cap'] == state['join'] == 0 and state['miter'] == 10,
                    'unmeasured stroke cap/join/miter')
            vectors.append({'points': path, 'width': state['width'], 'gray': state['gray']})
            painting.append('v')
            path = []
        elif op == 're':
            require(len(args) == 4 and not path, 'unexpected rectangle path')
            path = ['clip-rectangle']
        elif op in ('W', 'W*'):
            require(not args and path == ['clip-rectangle'], 'unmeasured clip path')
            state['clipped'] = True
        elif op == 'n':
            require(not args and path == ['clip-rectangle'] and state['clipped'], 'unmeasured empty path')
            path = []
        elif op in ('BMC', 'BDC'):
            if op == 'BMC':
                require(not marked and len(args) == 1 and str(args[0]) == '/Artifact', 'unmeasured artifact')
                marked.append('artifact')
            else:
                require(marked in ([], ['artifact']) and len(args) == 2 and str(args[0]) == '/Span'
                        and set(args[1].keys()) == {'/ActualText'}, 'unmeasured marked span')
                marked.append('actual-text')
        elif op == 'EMC':
            require(not args and marked, 'unbalanced marked content')
            marked.pop()
        elif op == 'Tj':
            require(len(args) == 1 and len(bytes(args[0])) == 2, 'unmeasured glyph string')
            if 'artifact' not in marked:
                painting.append('g')
        elif op == 'Do':
            require(len(args) == 1 and not marked, 'unmeasured image painting')
            resource = page.Resources.XObject[str(args[0])]
            require(resource.get('/Subtype') == pikepdf.Name('/Image'), 'unmeasured XObject')
            painting.append('i')
        elif op == 'gs':
            require(len(args) == 1, 'graphics state arity')
            params = page.Resources.ExtGState[str(args[0])]
            require(set(params.keys()) == {'/Type', '/BM'}
                    and params.Type == pikepdf.Name('/ExtGState')
                    and params.BM in (pikepdf.Name('/Normal'), pikepdf.Name('/Multiply')),
                    'unmeasured graphics state')
            state['blend'] = str(params.BM)
        else:
            require(op in passive, 'unmeasured PDF operator: ' + op)
    require(not stack and not marked and not path, 'unfinished PDF context')
    return vectors, painting


def compare(expected, observed, source_order, pdf_order):
    errors, rows = [], []
    if len(expected) != len(observed):
        errors.append('vector count')
    if source_order != pdf_order:
        errors.append('painting order')
    for number, (left, right) in enumerate(zip(expected, observed), 1):
        points = [coordinate for point in left['points'] for coordinate in point]
        actual = [coordinate for point in right['points'] for coordinate in point]
        delta = residual(actual, points) if len(actual) == len(points) else None
        width_delta = abs(right['width'] - left['width'])
        gray_delta = abs(right['gray'] - left['gray'])
        valid = delta is not None and delta <= TOLERANCE and width_delta <= TOLERANCE and gray_delta <= Fraction(1, 1000000)
        if not valid:
            errors.append(f'vector {number}')
        rows.append({'number': number, 'source_record': left['record'],
                     'points': len(left['points']), 'status': 'PASS' if valid else 'FAIL',
                     'maximum_coordinate_delta_points': None if delta is None else float(delta),
                     'width_delta_points': float(width_delta), 'gray_delta': float(gray_delta)})
    return {'status': 'FAIL' if errors else 'PASS', 'errors': errors,
            'source_vectors': len(expected), 'pdf_vectors': len(observed),
            'source_paint_events': len(source_order), 'pdf_paint_events': len(pdf_order),
            'painting_order_match': source_order == pdf_order, 'vectors': rows}


def inspect(source, pdf, source_sha, pdf_sha):
    require(digest(source) == source_sha and digest(pdf) == pdf_sha, 'input hash mismatch')
    pages = []
    with FileInput(source) as data, pikepdf.open(pdf) as output:
        reader = SourceExtractor(data, source_sha)
        variant = reader.header['variant']
        require(variant in ('C8', 'HN-B'), 'unmeasured native variant')
        require(reader.header['page_count'] == len(output.pages), 'page count mismatch')
        base = 0 if variant == 'C8' else 136
        mode = int.from_bytes(read_exact(data, base + 12, 4), 'little')
        require(mode == 2 or (variant == 'HN-B' and mode == 0), 'native mode')
        origin = struct.unpack('<HH', read_exact(data, base + 28, 4))
        extent = struct.unpack('<HH', read_exact(data, base + 32, 4))
        extent = [v + (100 if mode == 0 else 0) for v in extent]
        for source_page in reader.iter_pages():
            page = output.pages[source_page['page_number'] - 1]
            box = [Fraction(0), Fraction(0), extent[0] * UNIT, extent[1] * UNIT]
            require(residual(inherited(page, '/MediaBox'), box) <= TOLERANCE, 'PDF page extent')
            require(residual(inherited(page, '/CropBox', inherited(page, '/MediaBox')), box) <= TOLERANCE, 'PDF crop extent')
            expected, source_order = source_vectors(data, source_page, variant, mode, origin, extent[1])
            actual, pdf_order = pdf_vectors(page)
            pages.append({'page': source_page['page_number'],
                          **compare(expected, actual, source_order, pdf_order)})
    require(digest(source) == source_sha and digest(pdf) == pdf_sha, 'input changed')
    return {'source_sha256': source_sha, 'pdf_sha256': pdf_sha, 'variant': variant,
            'native_mode': mode, 'pikepdf': pikepdf.__version__, 'pages': pages,
            'status': 'PASS' if all(p['status'] == 'PASS' for p in pages) else 'FAIL',
            'source_and_pdf_unchanged': True,
            'scope': 'Measured vector geometry, stroke properties and glyph/image/vector kind order (excluding ornaments); not pixel/font/glyph/ornament fidelity'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--pdf-sha256', required=True)
    args = parser.parse_args()
    result = inspect(args.source, args.pdf, args.source_sha256, args.pdf_sha256)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
