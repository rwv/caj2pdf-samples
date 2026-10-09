#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Original missing-content counterexamples; neither completion is a repair."""
import argparse
import hashlib
import json
from pathlib import Path


def content(digits, ending):
    if digits not in (b'', b'4', b'41', b'4142'):
        raise ValueError('unmeasured original control')
    prefix = b'0 g 30 680 80 30 re f\nBT /F1 24 Tf 30 620 Td (BEFORE) Tj 0 -40 Td\n'
    if ending == 'omitted':
        return prefix + b'ET\n'
    tail = b'<' + digits + b'\r\n'
    if ending == 'broken':
        return prefix + tail
    if ending not in ('a', 'b'):
        raise ValueError('unknown completion')
    if not digits:
        suffix = b'41' if ending == 'a' else b'42'
    elif digits == b'4':
        suffix = b'1' if ending == 'a' else b'2'
    else:
        suffix = b'' if ending == 'a' else b'43'
    return prefix + tail + suffix + b'> Tj ET\n'


def write(path, data):
    if len(data) > 4096:
        raise ValueError('original control content limit')
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>',
               b'<< /Type /Pages /Count 1 /Kids [4 0 R] >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800] '
               b'/Resources << /Font << /F1 3 0 R >> >> /Contents 5 0 R >>',
               b'<< /Length ' + str(len(data)).encode() + b' >>\nstream\n' + data + b'endstream']
    with path.open('xb') as out:
        out.write(b'%PDF-1.7\n% Original MIT control\n')
        offsets = []
        for number, obj in enumerate(objects, 1):
            offsets.append(out.tell())
            out.write(f'{number} 0 obj\n'.encode() + obj + b'\nendobj\n')
        xref = out.tell()
        out.write(b'xref\n0 6\n0000000000 65535 f \n')
        for offset in offsets:
            out.write(f'{offset:010d} 00000 n \n'.encode())
        out.write(f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())


def generate(output):
    output = output.resolve()
    checkout = Path(__file__).resolve().parents[2]
    if output == checkout or checkout in output.parents:
        raise ValueError('binary controls must remain outside the checkout')
    output.mkdir(exist_ok=False)
    rows = []
    for digits in (b'', b'4', b'41', b'4142'):
        for ending in ('broken', 'omitted', 'a', 'b'):
            path = output / f'hex-{len(digits)}-{ending}.pdf'
            data = content(digits, ending)
            write(path, data)
            rows.append({'file': path.name, 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                         'pages': 1, 'hex_digits': len(digits), 'ending': ending,
                         'content_sha256': hashlib.sha256(data).hexdigest()})
    (output / 'manifest.json').write_text(json.dumps(rows, indent=2) + '\n')
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    generate(parser.parse_args().output)
