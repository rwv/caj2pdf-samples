#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Inventory native source records and output drawing/font use, not fidelity.

Record framing reuses the independent bounded research parser. Numeric source
state values remain observations, not inferred font identities. Only metadata
is emitted; document text, pixels and font programs stay external.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

from hnc8_layout_source import FileInput, SourceExtractor
from native_text_order import (
    MAX_CONTENT_BYTES, digest, raw_stream, read_exact, semantic_glyphs, source_glyphs,
)


def source_page(data, page, variant, mode):
    records, controls, drawings, uses = Counter(), {}, Counter(), Counter()
    state = {0x8002: None, 0x801d: None, 0x8067: None, 0x80ce: None}

    def visit(at, tag, value, size):
        if tag < 0x8000:
            records['glyph'] += 1
            uses[tuple(state.values())] += 1
            return
        records[f'{tag:04x}'] += 1
        if tag in state:
            state[tag] = value
        if size == 4:
            controls.setdefault(f'{tag:04x}', Counter())[f'{value:04x}'] += 1
        if tag in (0x8006, 0x8007, 0x8010, 0x8090):
            drawings[f'{tag:04x}/{value:04x}'] += 1

    glyphs, tail = source_glyphs(data, page, variant, mode, record_visitor=visit)
    assert len(glyphs) == records['glyph']
    return {
        'glyphs': len(glyphs), 'image_descriptors': len(page['images']),
        'records': dict(sorted(records.items())), 'drawing_records': dict(sorted(drawings.items())),
        'fixed_control_values': {k: dict(sorted(v.items())) for k, v in sorted(controls.items())},
        'glyph_state_use': [
            dict(zip(('style_8002', 'state_801d', 'value_8067', 'mode_80ce', 'glyphs'), (*key, count)))
            for key, count in uses.items()
        ],
        'opaque_tail_bytes': tail,
    }


def inventory(source, pdf, source_sha256, pdf_sha256):
    import fitz
    if digest(source) != source_sha256 or digest(pdf) != pdf_sha256:
        raise ValueError('input digest mismatch')
    pages = []
    with FileInput(source) as data, fitz.open(pdf) as output:
        reader = SourceExtractor(data, source_sha256)
        variant = reader.header['variant']
        if variant not in ('C8', 'HN-B') or len(output) != reader.header['page_count']:
            raise ValueError('unmeasured profile or page count mismatch')
        mode = int.from_bytes(read_exact(data, 12 if variant == 'C8' else 148, 4), 'little')
        for page in reader.iter_pages():
            observed = source_page(data, page, variant, mode)
            actual = output[page['page_number'] - 1]
            content = bytearray()
            for xref in actual.get_contents():
                content.extend(raw_stream(output, xref, MAX_CONTENT_BYTES - len(content)))
            # Rendering and font correctness cannot be inferred from these counts.
            pdf_fonts = {name.decode(): count for name, count in
                         sorted(Counter(re.findall(rb'/([A-Za-z0-9]+)\s+[\d.]+\s+Tf\b', content)).items())}
            vector_items = Counter()
            paths = actual.get_drawings()
            for path in paths:
                vector_items.update(item[0] for item in path['items'])
            pages.append({
                'page': page['page_number'], 'source': observed,
                'pdf': {'semantic_glyphs': len(semantic_glyphs(bytes(content))),
                        'actual_text_spans': content.count(b'/ActualText'),
                        'artifact_blocks': content.count(b'/Artifact'),
                        'font_selection_counts': pdf_fonts,
                        'fonts': [{'resource': f[4], 'base_font': f[3], 'type': f[2]}
                                  for f in actual.get_fonts()],
                        'vector_paths': len(paths), 'vector_items': dict(sorted(vector_items.items())),
                        'image_draws': len(actual.get_image_info())},
            })
    if digest(source) != source_sha256 or digest(pdf) != pdf_sha256:
        raise ValueError('input changed during inventory')
    return {'source_sha256': source_sha256, 'pdf_sha256': pdf_sha256,
            'variant': variant, 'native_mode': mode, 'pymupdf': fitz.VersionBind,
            'status': 'INVENTORIED', 'render_fidelity': 'UNVERIFIED', 'pages': pages}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--pdf-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(inventory(args.source, args.pdf, args.source_sha256, args.pdf_sha256), indent=2))
