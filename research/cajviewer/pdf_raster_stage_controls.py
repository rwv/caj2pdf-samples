#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate one bounded original font-free raster-stage PDF outside Git.

Six pages match the earlier navigation control's page boxes and marker counts.
Pages 1/5/6 add independently authored grayscale, vector and image panels.
No document, font, viewer implementation or raster input is read.
"""
import argparse
import hashlib
import json
from pathlib import Path

PANELS = {
    'solid_gray_cells': [32, 530, 269, 767],
    'fractional_vector_edges': [315, 530, 537, 752],
    'opaque_gray_image': [32, 330, 544, 394],
    'black_image_soft_mask': [32, 150, 544, 214],
}


def content(page):
    if type(page) is not int or not 1 <= page <= 6:
        raise ValueError('original control page outside 1 through 6')
    rows = ['0.2666666666666667 g']
    rows.extend(f'{32+i*16} 810 7 9 re f' for i in range(page))
    if page not in (2, 3, 4):
        for n in range(256):
            x, y = 32+15*(n % 16), 530+15*(n//16)
            rows.extend([f'{n/255:.9f} g', f'{x} {y} 12 12 re f'])
        rows.append('0.2666666666666667 g')
        for n in range(256):
            # Fixed decimal coordinates, never fitted to a viewer raster.
            x, y = 315+14*(n % 16), 530+14*(n//16)
            rows.append(f'{x}.125 {y}.25 m {x+11}.5 {y+2}.75 l {x+3}.875 {y+11}.5 l h f')
        rows.extend(['q 512 0 0 64 32 330 cm /Gray Do Q',
                     'q 512 0 0 64 32 150 cm /Alpha Do Q'])
    return ('\n'.join(rows)+'\n').encode('ascii')


def stream(dictionary, body):
    return (b'<< '+dictionary+b' /Length '+str(len(body)).encode()+b' >>\nstream\n'+body+b'\nendstream')


def write(path):
    ramp = bytes(range(256))*16
    image = b'/Type /XObject /Subtype /Image /Width 256 /Height 16 /BitsPerComponent 8 /Interpolate false '
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'',
               stream(image+b'/ColorSpace /DeviceGray', ramp),
               stream(image+b'/ColorSpace /DeviceGray', ramp),
               stream(image+b'/ColorSpace /DeviceRGB /SMask 4 0 R', bytes(256*16*3))]
    kids = []
    for page in range(1, 7):
        number = len(objects)+1
        kids.append(f'{number} 0 R')
        resources = '<< >>' if page in (2, 3, 4) else '<< /XObject << /Gray 3 0 R /Alpha 5 0 R >> >>'
        objects.extend([f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.2756 841.8898] '
                        f'/Resources {resources} /Contents {number+1} 0 R >>'.encode(),
                        stream(b'', content(page))])
    objects[1] = f'<< /Type /Pages /Count 6 /Kids [{" ".join(kids)}] >>'.encode()
    with path.open('xb') as output:
        output.write(b'%PDF-1.7\n% original font-free control\n')
        offsets = []
        for number, obj in enumerate(objects, 1):
            offsets.append(output.tell())
            output.write(f'{number} 0 obj\n'.encode()+obj+b'\nendobj\n')
        xref = output.tell()
        output.write(f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode())
        for offset in offsets:
            output.write(f'{offset:010d} 00000 n \n'.encode())
        output.write(f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())


def generate(output):
    output = output.resolve()
    checkout = Path(__file__).resolve().parents[2]
    if output == checkout or checkout in output.parents:
        raise ValueError('generated PDF bodies must remain outside checkout')
    output.mkdir(exist_ok=False)
    path = output/'original-font-free-6-pages.pdf'
    write(path)
    with path.open('rb') as file:
        sha = hashlib.file_digest(file, 'sha256').hexdigest()
    receipt = {'path': str(path), 'sha256': sha, 'pages': 6, 'target_page': 5,
               'target_stream_sha256': hashlib.sha256(content(5)).hexdigest(), 'panels_pdf_points': PANELS,
               'scope': 'Original font-free discriminator; no readiness or fidelity acceptance criterion.'}
    (output/'manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    generate(parser.parse_args().output)
