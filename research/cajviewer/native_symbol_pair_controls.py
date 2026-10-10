#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Original same-Unicode/different-glyph controls with geometric font data.

The observed public cmap arguments identify slots only. Every outline in the
generated font is this project's original square or upper/lower rectangle.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from fontTools.ttLib import TTFont
from c8_geometric_font import font
from c8_style_fixture import document
from hnb_geometry_fixture import hn_container


def generate(output):
    output.mkdir(exist_ok=False)
    fonts=output/'fonts';fonts.mkdir();inputs=output/'inputs';inputs.mkdir()
    path=fonts/'HGFX_CNKI.ttf';font(path,'HGFX_CNKI')
    with TTFont(path,recalcTimestamp=False) as original:
        for table in original['cmap'].tables:
            if table.isUnicode():
                table.cmap.update({0x2019:'square',26270:'upper',24518:'lower'})
        original.save(path)
    cases=[]
    for name,codes in [('curly',(0xa1af,)),('apostrophe',(0xa3a7,)),
                       ('forward',(0xa1af,0xa3a7)),('reverse',(0xa3a7,0xa1af))]:
        data=bytearray(hn_container(document([(0x10a4,0,6)],codes=codes,width=4200,height=6000,
            first_x=500,first_y=500,omit_controls=(0x801d,0x8067))))
        struct.pack_into('<I',data,148,0)
        struct.pack_into('<10H',data,152,0x8003,4200,0x8003,6000,0x8003,0,0,1,4200,6000)
        source=inputs/(name+'.caj');source.write_bytes(data)
        cases.append({'label':name,'source_path':str(source.resolve()),
            'source_sha256':hashlib.sha256(data).hexdigest(),'pages':1,
            'native_codes':[f'{code:04x}' for code in codes]})
    (output/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    (output/'font.json').write_text(json.dumps({'path':str(path.resolve()),
        'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'license':'MIT; original geometric controls'},indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path,help='new output directory')
    generate(parser.parse_args().output)
