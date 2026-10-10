#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Inventory existing native-model font roles/repertoires without text order.

This reuses the published original-control model. It is not a source-font
oracle, a fallback-font inventory or evidence of a required caller font.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import struct

from hnc8_layout_source import FileInput, SourceExtractor
from native_glyph_model import source_model
from native_text_order import digest, read_exact


def inventory(path, sha256):
    if digest(path) != sha256:
        raise ValueError('source hash mismatch')
    result = {'source_sha256': sha256, 'bytes': path.stat().st_size}
    with FileInput(path) as data:
        reader = SourceExtractor(data, sha256); variant = reader.header['variant']
        result.update(variant=variant, pages=reader.header['page_count'])
        base = 0 if variant == 'C8' else 136
        mode = int.from_bytes(read_exact(data, base + 12, 4), 'little')
        result['header_mode'] = mode
        if variant not in ('C8', 'HN-B') or not (mode == 2 or variant == 'HN-B' and mode == 0):
            result['status'] = 'OUTSIDE_NATIVE_MODEL'
        else:
            origin = struct.unpack('<HH', read_exact(data, base + 28, 4))
            height = int.from_bytes(read_exact(data, base + 34, 2), 'little') + (100 if mode == 0 else 0)
            counts, states, pages = Counter(), set(), []
            for page in reader.iter_pages():
                glyphs, _ = source_model(data, page, variant, mode, origin, height)
                pages.append({'page': page['page_number'],
                              'glyphs': sum(g['kind'] == 'g' for g in glyphs),
                              'ornaments': sum(g['kind'] == 'o' for g in glyphs)})
                for glyph in glyphs:
                    counts[(glyph['role'], glyph['character'], glyph['kind'])] += 1
                    states.add((glyph['role'], glyph['profile'], glyph['state']))
                    if len(counts) > 65536 or len(states) > 65536:
                        raise ValueError('document repertoire/state combination limit')
            roles = []
            for role in sorted({key[0] for key in counts}):
                roles.append({'role': role,
                    'ordinary_draws': sum(n for (r, _, k), n in counts.items() if r == role and k == 'g'),
                    'ornament_draws': sum(n for (r, _, k), n in counts.items() if r == role and k == 'o'),
                    'unicode_repertoire': sorted(f'U+{ord(c):04X}' for r, c, k in counts if r == role and k == 'g'),
                    'model_state_character_combinations': sum(r == role for r, _, _ in states)})
            result.update(status='INVENTORIED_EXISTING_MODEL', per_page=pages, roles=roles)
    if digest(path) != sha256:
        raise ValueError('source changed during inventory')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--source-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(inventory(args.source, args.source_sha256), indent=2))
