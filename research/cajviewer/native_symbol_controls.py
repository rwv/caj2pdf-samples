#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Author isolated HN-B mode-0 symbols from explicit numeric source profiles.

No source document or font is read. This covers only the measured legacy
symbol profiles with absent 801d/8067 and absent-or-one 80ce, not general HN-B.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

from c8_style_fixture import document
from hnb_geometry_fixture import hn_container

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from hnc8_layout_source import FileInput, SourceExtractor
from native_glyph_model import source_model


def generate(profiles, output):
    if not 1 <= len(profiles) <= 128:
        raise ValueError('profile count limit')
    for p in profiles:
        if (not re.fullmatch('[0-9a-f]{4}', p['code'])
                or not re.fullmatch('[0-9a-f]{4}', p['style'])
                or p['state'] is not None or p['font_word'] is not None
                or p['axes'] not in ([None, None], [36, 36])
                or p['cjk_switch'] not in (None, 1)):
            raise ValueError('outside measured symbol profile')
    output.mkdir(exist_ok=False)
    cases = []
    for i, profile in enumerate(profiles):
        code, style = int(profile['code'], 16), int(profile['style'], 16)
        words = [0x8070, 36, 0x8071, 36] if profile['axes'] == [36, 36] else []
        if profile['cjk_switch'] is not None:
            words += [0x80ce, 1]
        data = bytearray(hn_container(document([(style, 0, 6)], codes=(code,),
            width=4200, height=6000, first_x=500, first_y=500,
            omit_controls=(0x801d, 0x8067), run_words=words)))
        struct.pack_into('<I', data, 148, 0)
        struct.pack_into('<10H', data, 152, 0x8003, 4200, 0x8003, 6000, 0x8003, 0, 0, 1, 4200, 6000)
        path = output / f'{i:02d}-{code:04x}-{style:04x}.caj'; path.write_bytes(data)
        sha = hashlib.sha256(data).hexdigest()
        with FileInput(path) as source:
            page = next(SourceExtractor(source, sha).iter_pages())
            glyphs, painting = source_model(source, page, 'HN-B', 0, (0, 1), 6100)
            if len(glyphs) != 1 or glyphs[0]['role'] != 'symbols' or painting != ['g']:
                raise ValueError('control is not exactly one modeled symbol')
        cases.append({'label': path.stem, 'source_path': str(path.resolve()),
            'source_sha256': sha, 'pages': 1, 'profile': profile,
            'semantic_unicode': f'U+{ord(glyphs[0]["character"]):04X}'})
    if len({c['source_sha256'] for c in cases}) != len(cases):
        raise ValueError('duplicate control identity')
    for group, start in enumerate(range(0, len(cases), 10)):
        (output / f'cases-{group}.json').write_text(json.dumps(cases[start:start+10], indent=2) + '\n')
    return cases


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profiles', type=Path, help='JSON object with a profiles array')
    parser.add_argument('output', type=Path, help='new directory')
    args = parser.parse_args()
    if args.profiles.stat().st_size > 65536:
        parser.error('profile manifest exceeds 64 KiB')
    generate(json.loads(args.profiles.read_text())['profiles'], args.output)
