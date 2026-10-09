#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate same-outline viewer/PDF markers from original geometric fonts.

The input contains resource filenames only. No input font, glyph outline,
vendor implementation or private converter is read. cmap differs because the
viewer requests its obfuscated aliases while the PDF uses semantic Unicode.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from c8_geometric_font import font, identified_resource_font

ROLES = {'HGHT_CNKI': ('cjk', 1), 'HGBZ_CNKI': ('latin', 2),
         'HGHZ_CNKI': ('alternate-latin', 3), 'HGBX_CNKI': ('latin-state3', 4),
         'HGB1_CNKI': ('latin-state28', 5), 'HGB1X_CNKI': ('latin-state31', 6)}
TABLES = ('glyf', 'hmtx', 'hhea', 'OS/2', 'maxp', 'name', 'post')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(resources, output):
    names = sorted(resources)
    if not 1 <= len(names) <= 84 or len(set(names)) != len(names):
        raise ValueError('require at most 84 unique resource filenames')
    if any(not re.fullmatch('[A-Za-z0-9_-]+[.](ttf|TTF)', name) for name in names):
        raise ValueError('unmeasured resource filename')
    if not {name + '.ttf' for name in ROLES}.issubset(names):
        raise ValueError('missing identified native resource')
    output.mkdir(exist_ok=False)
    viewer, pdf = output / 'viewer', output / 'pdf'
    viewer.mkdir(); pdf.mkdir()
    rows, symbol_written = [], False
    for name in names:
        family = Path(name).stem
        role, marker = ROLES.get(family, ('symbols', 7))
        path = viewer / name
        font(path, family)
        identified_resource_font(path, path, marker)
        generated = TTFont(path, recalcTimestamp=False)
        cmap = CmapSubtable.newSubtable(13)
        cmap.platformID, cmap.platEncID, cmap.language = 3, 10, 0
        cmap.cmap = {code: 'square' for code in range(65536)}
        generated['cmap'].tables = [cmap]
        generated.save(path)
        row = {'resource': name, 'marker': marker, 'viewer_sha256': digest(path)}
        if role != 'symbols' or not symbol_written:
            # All anonymous resources intentionally share marker 7. This
            # checks their common outer geometry, not individual identities.
            target = pdf / (role + '.ttf')
            cmap = CmapSubtable.newSubtable(12)
            cmap.platformID, cmap.platEncID, cmap.language = 3, 10, 0
            cmap.cmap = {code: 'square' for code in range(65536) if not 0xd800 <= code <= 0xdfff}
            generated['cmap'].tables = [cmap]
            generated.save(target)
            row.update(pdf_role=role, pdf_sha256=digest(target))
            with TTFont(path) as a, TTFont(target) as b:
                if any(a.getTableData(t) != b.getTableData(t) for t in TABLES):
                    raise ValueError('viewer/PDF outline or metric mismatch')
            symbol_written |= role == 'symbols'
        generated.close()
        rows.append(row)
    (output / 'manifest.json').write_text(json.dumps({'resources': rows, 'identical_tables': TABLES,
        'scope': 'Original marker geometry/resources, not source font appearance; anonymous resources share marker 7'}, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('resource_names', type=Path, help='JSON array of filenames; no font bytes')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.resource_names.stat().st_size > 16384:
        parser.error('resource filename manifest exceeds 16 KiB')
    generate(json.loads(args.resource_names.read_text()), args.output)
