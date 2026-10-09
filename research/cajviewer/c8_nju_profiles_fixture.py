#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Original measurement controls for NJU C8 profiles (Rust #513/#514).

These are hypotheses and discriminating controls, not an admission list.
No external source document, font data or converter implementation is read.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from c8_additional_profiles_fixture import text_control
from c8_image_fixture import jpeg, mixed_control


def mixed(words, state):
    return mixed_control(jpeg(), words).replace(
        struct.pack('<HH', 0x801d, 4), struct.pack('<HH', 0x801d, state))


def controls():
    yield 'base', text_control()
    for style in (0x096b, 0x116b, 0x0d6b, 0x6084, 0x1084, 0x0508, 0x1108, 0x108b, 0x1164):
        yield f'style-{style:04x}', text_control(style)
    for axis in (1, 2, 4, 94, 95, 96, 97, 98):
        yield f'axis-{axis}', text_control(0, (0x8070, axis, 0x8071, axis))
    for font in (0, 5, 6, 8, 9, 11):
        yield f'font-{font}', text_control(words=(0x8067, font))
    for shear in (0x2800, 0x2815, 0x281c, 0x281d):
        yield f'shear-{shear:04x}', text_control(words=(0x8024, shear))
    for mode in (0, 1):
        for state in (0, 4):
            for shear in (0x2800, 0x2815):
                for label, record in (('base', ()), ('2000', (0x8021, 0x2000)),
                                      ('2009', (0x8021, 0x2009)),
                                      ('2009-reset', (0x8021, 0x2009, 0x8021, 0x2000))):
                    words = (0x80ce, mode, 0x81ff, 1, 0, 200, 0x8024, shear) + record
                    yield f'mixed-{mode}-{state}-{shear:04x}-{label}', mixed(words, state)
    yield 'base-repeat', text_control()
    for style in (0x096b, 0x0508, 0x6084, 0x64c6, 0x10c6, 0x114a, 0x094a):
        for mode in (0, 1):
            yield f'extra-style-{style:04x}-{mode}', text_control(style, (0x80ce, mode))
    for size, style in ((11, 0x096b), (4, 0x1084)):
        for dy in (-7, -6, -5, 14, 15, 16):
            yield f'extra-align-{size}-{dy}', text_control(style, codes=(0xd6d0,), y=4374 + dy)
    for code in (0xa3ba, 0xa1aa):
        for style in (0x096b, 0x0508):
            yield f'extra-symbol-{style:04x}-{code:04x}', text_control(style, codes=(code, 0xd6d0))
    for state in (0, 4):
        for font in (0, 4, 5, 6, 7, 11):
            yield f'extra-mixed-font-{state}-{font}', mixed((0x8067, font), state)
    for tag, styles in ((0x8006, (0xa381, 0xa383, 0xa385, 0xa387, 0xa38b, 0xa38d)),
                        (0x8008, (0xa380,))):
        for direction, points in (('h', (4702, 4500, 5172, 4500)),
                                  ('v', (4902, 4380, 4902, 4590)),
                                  ('d', (4702, 4380, 5172, 4590)),
                                  ('rev', (5172, 4590, 4702, 4380))):
            for style in styles:
                yield f'extra-draw-{tag:04x}-{style:04x}-{direction}', text_control(
                    words=(tag, style, *points), codes=())
    yield 'extra-axes1-source', text_control(0x1084, (0x801c, 4, 0x8070, 1, 0x8071, 1))
    for state in (0, 4):
        for code in (0xa1b2, 0xa1b3):
            yield f'bracket-{state}-{code:04x}', text_control(
                words=(0x801d, state), codes=(code,))
        # Known field-4 opener: x + 22 and y + 0. Shift that independent
        # control to distinguish candidate offsets 20/21/22 and 5/6/7.
        for dx, dy in ((-2, 6), (-1, 5), (-1, 6), (-1, 7), (0, 6)):
            yield f'bracket-reference-{state}-{dx}-{dy}', text_control(
                words=(0x801d, state), codes=(0xa3a8,), x=4672 + dx, y=4374 + dy)
    for code in (0xd6d0, 0xaab3):
        yield f'tiny-{code:04x}', text_control(
            words=(0x801c, 4, 0x8070, 1, 0x8071, 1), codes=(code,))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='new directory outside the repository')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = []
    for name, data in controls():
        filename = name + '.caj'
        (args.output / filename).write_bytes(data)
        manifest.append({'file': filename, 'sha256': hashlib.sha256(data).hexdigest()})
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
