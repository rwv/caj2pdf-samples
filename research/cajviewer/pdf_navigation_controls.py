#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate two original PDF navigation controls outside this checkout.

Five/six pages, identical first five streams, no external document/font input.
Standard-14 Helvetica is referenced, never embedded. These bounded fixtures do
not establish viewer readiness or equivalence across different scroll origins.
"""
import argparse
import hashlib
import json
from pathlib import Path


def content(page):
    if type(page) is not int or not 1 <= page <= 6:
        raise ValueError('control page outside 1 through 6')
    rows = ['0.2666666666666667 g', 'BT /F1 9 Tf']
    for i in range(page):
        rows.append(f'1 0 0 1 {32+i*16} 810 Tm (M) Tj')
    if page not in (2, 3, 4):
        codes = 'ABMrg123NXYabc45'
        for y in range(40):
            for x in range(40):
                rows.append(f'1 0 0 1 {32+x*13} {780-y*18} Tm ({codes[x % len(codes)]}) Tj')
    rows.append('ET')
    return ('\n'.join(rows) + '\n').encode('ascii')


def write(path, pages):
    if type(pages) is not int or pages not in (5, 6):
        raise ValueError('measured controls require 5 or 6 pages')
    # Original fixed-size fixtures only, less than 160 KiB per document.
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', None,
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    kids = []
    for page in range(1, pages + 1):
        number = len(objects) + 1
        kids.append(f'{number} 0 R')
        objects.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.2756 841.8898] '
                       f'/Resources << /Font << /F1 3 0 R >> >> /Contents {number+1} 0 R >>'.encode('ascii'))
        data = content(page)
        objects.append(b'<< /Length ' + str(len(data)).encode() + b' >>\nstream\n' + data + b'endstream')
    objects[1] = f'<< /Type /Pages /Count {pages} /Kids [{" ".join(kids)}] >>'.encode('ascii')
    with path.open('xb') as out:
        out.write(b'%PDF-1.7\n% original control\n')
        offsets = []
        for number, obj in enumerate(objects, 1):
            offsets.append(out.tell())
            out.write(f'{number} 0 obj\n'.encode() + obj + b'\nendobj\n')
        xref = out.tell()
        out.write(f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode())
        for offset in offsets:
            out.write(f'{offset:010d} 00000 n \n'.encode())
        out.write(f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())


def generate(output):
    output = output.resolve()
    checkout = Path(__file__).resolve().parents[2]
    if output == checkout or checkout in output.parents:
        raise ValueError('generated controls must remain outside the checkout')
    output.mkdir(exist_ok=False)
    cases = []
    for pages in (5, 6):
        path = output / f'original-{pages}-pages.pdf'
        write(path, pages)
        with path.open('rb') as stream:
            sha = hashlib.file_digest(stream, 'sha256').hexdigest()
        cases.append({'path': str(path), 'sha256': sha, 'pages': pages, 'target_page': 5,
                      'target_stream_sha256': hashlib.sha256(content(5)).hexdigest()})
    (output / 'manifest.json').write_text(json.dumps(cases, indent=2) + '\n')
    return cases


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    generate(parser.parse_args().output)
