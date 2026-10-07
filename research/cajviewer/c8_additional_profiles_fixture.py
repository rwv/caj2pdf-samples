#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate original controls for caj2pdf-rust #380/#382 outside the repository."""

import argparse
import hashlib
import json
from pathlib import Path
import struct

from c8_style_fixture import document
from c8_image_reference_fixture import document as image_document, jpeg


def text_control(style=0x1084, words=(), codes=(0xD6D0, 0xA0C1), x=4672, y=4374):
    base = document([(style, 0, 6)], codes=(), width=700, height=450,
                    first_x=x, first_y=y)
    words += tuple(word for i, code in enumerate(codes) for word in (x + i * 220, code))
    data = bytearray(base[:100] + base[100:-4] + struct.pack('<' + 'H' * len(words), *words) + base[-4:])
    struct.pack_into('<I', data, 84, len(data) - 100)
    struct.pack_into('<I', data, 96, len(data))
    return bytes(data)


def controls():
    yield 'base', text_control()
    for style in (0x094A, 0x114A, 0xA4A5, 0x10A5):
        yield f'c8-style-{style:04x}', text_control(style)
    for value in (2, 3):
        yield f'c8-control-801c-{value:04x}', text_control(words=(0x801C, value))
    for axis in (22, 34, 35, 36, 38, 40):
        yield f'c8-axis-{axis}', text_control(0, (0x8070, axis, 0x8071, axis))
    for code in (0xA1A3, 0xA1AB):
        yield f'c8-code-{code:04x}', text_control(codes=(code, 0xA0C1))
    for name, payload in (('plain', (0xE041, 0xE042)),
                          ('nul', (0xE041, 0xE042, 0xE000)),
                          ('embedded', (0xE041, 0xE000, 0xE042)),
                          ('nulonly', (0xE000,))):
        yield 'string-' + name, text_control(words=(0x80CC, 0x102 + len(payload)) + payload)
    for flag in (1, 2, 46):
        drawing = (0x8010, flag, 4672, 4500, 5272, 4500, 0xFFFF, 5)
        yield f'decoration-{flag}', text_control(words=drawing)
        for axis in (34, 40):
            yield f'decor-axis-{axis}-{flag}', text_control(words=(0x8070, axis, 0x8071, axis) + drawing)
    for axis in (22, 34, 40):
        for code in (0xD6D0, 0xA0C1, 0xA3A8, 0xA3A9, 0xA3DB, 0xA3DD, 0xA3A7, 0xA3FC):
            yield f'punct-{axis}-{code:04x}', text_control(0, (0x8070, axis, 0x8071, axis), (code, 0xA0C1))
    for code in (0xA3A6, 0xA3A7, 0xA3FC):
        yield f'newcode-{code:04x}', text_control(codes=(code, 0xA0C1))
    for axis in (34, 40):
        for code in (0xA3A8, 0xA3DB):
            yield f'punct-reset-{axis}-{code:04x}', text_control(words=(0x8070, axis, 0x8071, axis, 0x8002, 0x1084), codes=(code, 0xA0C1))
    for axis, dx, dys in ((22, 19, (4, 5)), (34, 29, (-2, -3)), (40, 34, (-5, -6))):
        for dy in dys:
            yield f'align-{axis}-{dy}', text_control(0, (0x8070, axis, 0x8071, axis), x=4672 + dx, y=4374 + dy)
    for size in (0, 4, 8, 24, 260):
        for padded in (False, True):
            data = bytearray(image_document([b'a' * size], [(4682, 4314, 80, 50)], [jpeg()]))
            if not padded:
                at = 116 + size
                del data[at:at + 4]
                length = struct.unpack_from('<I', data, 84)[0] - 4
                struct.pack_into('<I', data, 84, length)
                struct.pack_into('<I', data, 96, len(data))
                struct.pack_into('<I', data, 100 + length + 4, 100 + length + 12)
            yield f'ref-{size}-' + ('padded' if padded else 'bare'), bytes(data)


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
