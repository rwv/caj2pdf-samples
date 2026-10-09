#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Original 75-page, font-free Letter/missing-box navigation controls."""
import argparse
import hashlib
import json
from pathlib import Path

PAGES = 75


def content(page):
    if type(page) is not int or not 1 <= page <= PAGES:
        raise ValueError('page outside original control inventory')
    # Fixed frame, diagonal and square reproduce the earlier one-page control.
    # Seven binary page markers distinguish every page, including last-page jumps.
    parts = ['q 1 0 0 RG 2 w 2 2 608 788 re S',
             '0 0 1 RG 10 10 m 600 780 l S',
             '0 0 0 rg 100 100 40 60 re f']
    for bit in range(7):
        if page & (1 << bit):
            parts.append(f'{40+20*bit} 740 12 12 re f')
    parts.append('Q')
    return ('\n'.join(parts)+'\n').encode('ascii')


def write(path, *, explicit_letter):
    if type(explicit_letter) is not bool:
        raise ValueError('explicit_letter must be boolean')
    offsets = []
    with path.open('xb') as out:
        out.write(b'%PDF-1.7\n% original page-box controls\n')
        def obj(number, body):
            offsets.append(out.tell())
            out.write(f'{number} 0 obj\n'.encode()+body+b'\nendobj\n')
        obj(1, b'<< /Type /Catalog /Pages 2 0 R >>')
        kids = ' '.join(f'{3+2*p} 0 R' for p in range(PAGES))
        obj(2, f'<< /Type /Pages /Count {PAGES} /Kids [{kids}] >>'.encode())
        for page in range(1, PAGES+1):
            number = 1+2*page
            box = ' /MediaBox [0 0 612 792]' if explicit_letter else ''
            obj(number, f'<< /Type /Page /Parent 2 0 R /Resources << >> /Contents {number+1} 0 R{box} >>'.encode())
            body = content(page)
            obj(number+1, f'<< /Length {len(body)} >>\nstream\n'.encode()+body+b'endstream')
        xref = out.tell()
        out.write(f'xref\n0 {len(offsets)+1}\n0000000000 65535 f \n'.encode())
        for offset in offsets:
            out.write(f'{offset:010d} 00000 n \n'.encode())
        out.write(f'trailer\n<< /Size {len(offsets)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())


def generate(output):
    output = output.resolve()
    root = Path(__file__).resolve().parents[2]
    if output == root or root in output.parents:
        raise ValueError('generated PDF bodies must remain outside checkout')
    output.mkdir(exist_ok=False)
    rows = []
    for name, explicit in [('missing', False), ('letter', True)]:
        path = output/f'{name}.pdf'
        write(path, explicit_letter=explicit)
        with path.open('rb') as stream:
            identity = hashlib.file_digest(stream, 'sha256').hexdigest()
        rows.append({'path': str(path), 'sha256': identity, 'pages': PAGES,
                     'explicit_letter': explicit, 'size': path.stat().st_size})
    (output/'manifest.json').write_text(json.dumps(rows, indent=2)+'\n')
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    generate(parser.parse_args().output)
