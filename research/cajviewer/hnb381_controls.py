#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Author HN-B #381 controls without reading an external document.

The optional bilevel directory contains the five original MQ payloads generated
by hnb381_type3.rs, never bytes extracted from a source document.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from c8_style_fixture import document
from hnb_geometry_fixture import hn_container
from hnb_image_fixture import document as image_document

SYMBOLS = (0xA1B4, 0xA1B5, 0xA1C0, 0xA1C1, 0xA1C3, 0xA1D6, 0xA1DD,
           0xA1E4, 0xA2F2, 0xA6B8, 0xA6C4, 0xA6CC, 0xA6D2, 0xA661)


def glyphs(style=0x1084, state=0, codes=(0xD6D0, 0xA0C1), words=(), y=4374, hnb=True):
    data = document([(style, state, 6)], codes=codes, run_words=words,
                    width=700, height=450, first_x=4672, first_y=y)
    return hn_container(data) if hnb else data


def bilevel(order, patterns, directory):
    # Retain the original image/order control's authored records, replacing
    # its independently generated JPEG resources with authored type-3 payloads.
    original = image_document(order)
    length = struct.unpack_from('<I', original, 220)[0]
    data = bytearray(original[:236 + length])
    struct.pack_into('<HH', data, 168, 700, 450)
    for item in order:
        if item == 'T':
            continue
        payload = (directory / (patterns[item] + '.bin')).read_bytes()
        data += struct.pack('<III', 3, len(data) + 12, len(payload)) + payload
    struct.pack_into('<I', data, 232, len(data))
    return bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--bilevel-dir', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    records = []

    def add(name, data):
        path = args.output / (name + '.caj')
        path.write_bytes(data)
        records.append({'file': path.name, 'bytes': len(data),
                        'sha256': hashlib.sha256(data).hexdigest()})

    for style in (0x0929, 0x1129, 0x1000):
        add(f'style-{style:04x}', glyphs(style))
    add('c8-small1000', glyphs(0x1000, hnb=False))
    add('resource18', glyphs(words=(0x8067, 18)))
    add('base', glyphs())
    for code in SYMBOLS:
        for state in (0, 3):
            add(f'symbol-{state}-{code:04x}', glyphs(state=state, codes=(code, 0xA0C1)))
    for tag in (0x8072, 0x8073, 0x8074):
        for value in (0, 278, 288, 0xA3AC, 0x8001, 0x8004, 0xFFFF):
            add(f'metadata-{tag:04x}-{value:04x}', glyphs(words=(tag, value)))
    for state in (0, 3):
        add(f'beta5-{state}', glyphs(0x10A5, state, (0xA6C2, 0xA0C1)))
        add(f'beta5-reference-{state}', glyphs(0x10A5, state, (0xA3AC, 0xA0C1), y=4399))
    for hnb in (False, True):
        for code in (0xA3DB, 0xA3DD, 0xA0C1):
            add(f'bracket1-{hnb}-{code:04x}', glyphs(0x1021, codes=(code, 0xA0C1), hnb=hnb))
    if args.bilevel_dir:
        add('bi2-T', bilevel('T', {}, args.bilevel_dir))
        for pattern in ('white', 'black', 'left', 'top', 'checker'):
            for order in ('A', 'TA', 'AT'):
                add(f'bi2-{order}-{pattern}', bilevel(order, {'A': pattern}, args.bilevel_dir))
        for order in ('TAB', 'TBA', 'ATB', 'ABT', 'TATB'):
            add(f'bi2-{order}-cross', bilevel(order, {'A': 'left', 'B': 'top'}, args.bilevel_dir))
    (args.output / 'manifest.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
