#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Write a bounded original RGB/vector/interpolation PDF outside the checkout."""
import argparse
import hashlib
import json
from pathlib import Path

COLORS = ((0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255),
          (0, 255, 255), (255, 0, 255), (255, 255, 0), (255, 255, 255))
PANELS = {
    'solid_rgb_cells': [32, 530, 266, 764],
    'fractional_rgb_edges': [315, 530, 536, 751],
    'low_resolution_left': [32, 330, 272, 450],
    'low_resolution_right': [315, 330, 555, 450],
    'high_resolution_left': [32, 150, 272, 270],
    'high_resolution_right': [315, 150, 555, 270],
}


def sample(x, y):
    """Original 64x32 pattern: solids, checker cells, ramps and thin bars."""
    if y < 8:
        return COLORS[x // 8]
    if y < 16:
        return COLORS[(x + y) % 8]
    if y < 24:
        return (4*x, 4*(63-x), 4*((17*x) % 64))
    return COLORS[(x//8+1) % 8] if x % 8 == (y-24) else (255, 255, 255)


def image_rows(scale):
    if type(scale) is not int or scale not in (1, 8):
        raise ValueError('only the two fixed image resolutions are supported')
    for y in range(32):
        row = b''.join(bytes(sample(x, y))*scale for x in range(64))
        for _ in range(scale):
            yield row


def content(page):
    if type(page) is not int or not 1 <= page <= 6:
        raise ValueError('page outside original six-page control')
    rows = ['0 g']
    rows.extend(f'{32+i*16} 810 7 9 re f' for i in range(page))
    if page in (1, 5, 6):
        for y in range(8):
            for x, color in enumerate(COLORS):
                rows.append(' '.join(f'{c*y/(255*7):.9f}' for c in color)+' rg')
                rows.append(f'{32+30*x} {530+30*y} 24 24 re f')
        for n in range(64):
            color = ((n*73+19) % 256, (n*37+53) % 256, (n*17+97) % 256)
            rows.append(' '.join(f'{c/255:.9f}' for c in color)+' rg')
            x, y = 315+28*(n % 8), 530+28*(n//8)
            rows.append(f'{x}.125 {y}.25 m {x+24}.5 {y+3}.75 l {x+4}.875 {y+24}.5 l h f')
        for name, x, y in [('LowLeft', 32, 330), ('LowRight', 315, 330),
                           ('HighLeft', 32, 150), ('HighRight', 315, 150)]:
            rows.append(f'q 240 0 0 120 {x} {y} cm /{name} Do Q')
    return ('\n'.join(rows)+'\n').encode('ascii')


def write(path, *, swap_interpolation=False):
    if type(swap_interpolation) is not bool:
        raise ValueError('swap_interpolation must be boolean')
    offsets = []
    with path.open('xb') as output:
        output.write(b'%PDF-1.7\n% original font-free RGB controls\n')

        def begin():
            offsets.append(output.tell())
            output.write(f'{len(offsets)} 0 obj\n'.encode())

        def obj(body):
            begin()
            output.write(body+b'\nendobj\n')

        obj(b'<< /Type /Catalog /Pages 2 0 R >>')
        kids = ' '.join(f'{7+2*n} 0 R' for n in range(6))
        obj(f'<< /Type /Pages /Count 6 /Kids [{kids}] >>'.encode())
        for scale, interpolate in [(1, False), (1, True), (8, False), (8, True)]:
            interpolate ^= swap_interpolation
            begin()
            output.write(f'<< /Type /XObject /Subtype /Image /Width {64*scale} /Height {32*scale} '
                         f'/ColorSpace /DeviceRGB /BitsPerComponent 8 /Interpolate {str(interpolate).lower()} '
                         f'/Length {64*32*3*scale*scale} >>\nstream\n'.encode())
            for row in image_rows(scale):
                output.write(row)
            output.write(b'\nendstream\nendobj\n')
        for page in range(1, 7):
            number = len(offsets)+1
            resources = '<< >>' if page in (2, 3, 4) else (
                '<< /XObject << /LowLeft 3 0 R /LowRight 4 0 R /HighLeft 5 0 R /HighRight 6 0 R >> >>')
            obj(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.2756 841.8898] '
                f'/Resources {resources} /Contents {number+1} 0 R >>'.encode())
            body = content(page)
            obj(b'<< /Length '+str(len(body)).encode()+b' >>\nstream\n'+body+b'endstream')
        xref = output.tell()
        output.write(f'xref\n0 {len(offsets)+1}\n0000000000 65535 f \n'.encode())
        for offset in offsets:
            output.write(f'{offset:010d} 00000 n \n'.encode())
        output.write(f'trailer\n<< /Size {len(offsets)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())


def generate(output):
    output = output.resolve()
    checkout = Path(__file__).resolve().parents[2]
    if output == checkout or checkout in output.parents:
        raise ValueError('generated PDFs must remain outside the checkout')
    output.mkdir(exist_ok=False)
    cases = []
    for name, swap in [('default', False), ('swapped', True)]:
        path = output/f'original-rgb-{name}-6-pages.pdf'
        write(path, swap_interpolation=swap)
        with path.open('rb') as source:
            identity = hashlib.file_digest(source, 'sha256').hexdigest()
        cases.append({'kind': name, 'path': str(path), 'sha256': identity,
                      'bytes': path.stat().st_size, 'swap_interpolation': swap})
    result = {'cases': cases, 'pages': 6, 'target': 5, 'panels_pdf_points': PANELS,
              'scope': 'Original font-free discriminator, not a readiness or fidelity verdict.'}
    (output/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    generate(parser.parse_args().output)
