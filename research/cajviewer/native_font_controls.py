#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Original one-page, unique-code controls for bounded FreeType observations.

No input document or font program is read. This is the previously measured C8
framing, not a general document generator. Mode 0 labels are raw native codes;
only mode 1 carries the authored ASCII semantics.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

CHARACTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
STATES = (0, 4, 3, 28, 31)


def document(codes, mode=0, state=0, step=600):
    if (not 1 <= len(codes) <= 62 or len(set(codes)) != len(codes)
            or any(type(code) is not int or not 0xa0b0 <= code <= 0xa0fa for code in codes)
            or type(mode) is not int or mode not in (0, 1)
            or type(state) is not int or state not in STATES
            or type(step) is not int or step not in (300, 600)
            or 4800 + ((len(codes) - 1) // 4) * step >= 10274):
        raise ValueError('outside the unique-code control profile')
    header = bytearray(80)
    struct.pack_into('<IIII', header, 0, 200, 0, 1, 2)
    header[16:28] = '北大二扫1.00'.encode('gbk')
    struct.pack_into('<HHHH', header, 28, 4652, 4274, 4200, 6000)
    words = []
    for i, code in enumerate(codes):
        row, col = divmod(i, 4)
        if col == 0:
            words += [(0x8001, 4800 + row * step), (0x8002, 0x10a5),
                      (0x801d, state), (0x8067, 6), (0x80ce, mode)]
        words.append((5100 + col * 750, code))
    words.append((0x8004, 1))
    body = b''.join(struct.pack('<HH', *pair) for pair in words)
    return bytes(header) + struct.pack('<IIIII', 100, len(body), 0, 0, 100 + len(body)) + body


def generate(output):
    output.mkdir(exist_ok=False)
    cohorts = {'pilot': [], 'latin': [], 'isolated-latin': [], 'isolated-cjk': []}
    def add(cohort, label, characters, mode, state, step):
        codes = [0xa080 + ord(c) for c in characters]
        data = document(codes, mode, state, step)
        path = output / (cohort + '-' + label + '.caj')
        path.write_bytes(data)
        cohorts[cohort].append({'label': label, 'source_path': str(path.resolve()),
            'source_sha256': hashlib.sha256(data).hexdigest(), 'pages': 1,
            'state': state, 'mode': mode, 'expected_codes': [f'{c:04x}' for c in codes]})
    for order, characters in [('forward', CHARACTERS[:26]), ('reverse', CHARACTERS[:26][::-1])]:
        add('pilot', order, characters, 0, 0, 600)
    for state in STATES:
        for order, characters in [('forward', CHARACTERS), ('reverse', CHARACTERS[::-1])]:
            add('latin', f'{state}-{order}', characters, 1, state, 300)
        for char in 'A1':
            add('isolated-latin', f'1-{state}-{char}', char, 1, state, 300)
    for char in 'AZ':
        add('isolated-cjk', f'0-0-{char}', char, 0, 0, 300)
    for cohort, cases in cohorts.items():
        (output / (cohort + '.json')).write_text(json.dumps(cases, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    generate(parser.parse_args().output)
