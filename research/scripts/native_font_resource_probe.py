#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check observed cmap aliases against explicitly supplied, hash-pinned fonts.

Only documented FreeType character mapping APIs are called. No glyph outline,
bitmap, font program export, embedding or license decision is produced. A cmap
match identifies this resource's slots; it does not prove the viewer opened
this path or establish source/PDF visual equality.
"""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import re

FAMILIES = ('HGHT_CNKI', 'HGBZ_CNKI', 'HGHZ_CNKI', 'HGBX_CNKI', 'HGB1_CNKI', 'HGB1X_CNKI')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def probe(resources, directory, library_path):
    if not 1 <= len(resources) <= 6 or len({r['family'] for r in resources}) != len(resources):
        raise ValueError('resource count or duplicate family')
    # Preflight the entire input before loading any supplied resource.
    for resource in resources:
        family, mappings = resource['family'], resource['mappings']
        if family not in FAMILIES or not re.fullmatch('[0-9a-f]{64}', resource['sha256']):
            raise ValueError('unmeasured resource identity')
        path = directory / (family + '.ttf')
        if not 0 < path.stat().st_size <= 16 * 1024 * 1024 or digest(path) != resource['sha256']:
            raise ValueError('resource hash or size mismatch')
        if (not 1 <= len(mappings) <= 62
                or len({m['native_code'] for m in mappings}) != len(mappings)
                or any(not re.fullmatch('[0-9a-f]{4}', m['native_code'])
                       or type(m['cmap_argument']) is not int or not 0 <= m['cmap_argument'] <= 0xffff
                       or type(m['glyph_id']) is not int or not 1 <= m['glyph_id'] <= 0xffff
                       for m in mappings)):
            raise ValueError('mapping limit or ambiguous native code')
        if family != 'HGHT_CNKI':
            for mapping in mappings:
                ordinary = int(mapping['native_code'], 16) - 0xa080
                if not (48 <= ordinary <= 57 or 65 <= ordinary <= 90 or 97 <= ordinary <= 122):
                    raise ValueError('ordinary Unicode comparison outside authored ASCII controls')
    library_sha = digest(library_path)
    api = C.CDLL(str(library_path))
    for name, arguments, result in [
        ('FT_Init_FreeType', [C.POINTER(C.c_void_p)], C.c_int),
        ('FT_New_Face', [C.c_void_p, C.c_char_p, C.c_long, C.POINTER(C.c_void_p)], C.c_int),
        ('FT_Select_Charmap', [C.c_void_p, C.c_uint], C.c_int),
        ('FT_Get_Char_Index', [C.c_void_p, C.c_ulong], C.c_uint),
        ('FT_Done_Face', [C.c_void_p], C.c_int),
        ('FT_Done_FreeType', [C.c_void_p], C.c_int),
        ('FT_Library_Version', [C.c_void_p, C.POINTER(C.c_int), C.POINTER(C.c_int), C.POINTER(C.c_int)], None),
    ]:
        function = getattr(api, name); function.argtypes = arguments; function.restype = result
    library = C.c_void_p()
    if api.FT_Init_FreeType(C.byref(library)):
        raise ValueError('FreeType initialization failed')
    rows = []
    try:
        version = [C.c_int() for _ in range(3)]
        api.FT_Library_Version(library, *(C.byref(v) for v in version))
        for resource in resources:
            path = directory / (resource['family'] + '.ttf'); face = C.c_void_p()
            if api.FT_New_Face(library, str(path).encode(), 0, C.byref(face)):
                raise ValueError('font face could not be opened')
            try:
                if api.FT_Select_Charmap(face, 0x756e6963):  # documented FT_ENCODING_UNICODE
                    raise ValueError('Unicode charmap unavailable')
                for mapping in resource['mappings']:
                    gid = api.FT_Get_Char_Index(face, mapping['cmap_argument'])
                    if gid != mapping['glyph_id']:
                        raise ValueError('resource cmap differs from observed alias')
                    raw = int(mapping['native_code'], 16)
                    ordinary = raw - 0xa080 if resource['family'] != 'HGHT_CNKI' else None
                    rows.append({'family': resource['family'], **mapping,
                                 'ordinary_unicode': ordinary,
                                 'ordinary_glyph_id': api.FT_Get_Char_Index(face, ordinary) if ordinary is not None else None})
            finally:
                api.FT_Done_Face(face)
            if digest(path) != resource['sha256']:
                raise ValueError('resource changed during observation')
    finally:
        api.FT_Done_FreeType(library)
    if digest(library_path) != library_sha:
        raise ValueError('FreeType library changed')
    return {'freetype_version': [v.value for v in version], 'library_sha256': library_sha,
            'resources': [{'family': r['family'], 'sha256': r['sha256']} for r in resources],
            'mappings': rows, 'status': 'CMAP_MATCH', 'font_fidelity': 'UNVERIFIED'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('font_directory', type=Path)
    parser.add_argument('--library', type=Path, required=True)
    args = parser.parse_args()
    if args.manifest.stat().st_size > 1024 * 1024:
        parser.error('resource manifest exceeds 1 MiB')
    print(json.dumps(probe(json.loads(args.manifest.read_text()), args.font_directory, args.library), indent=2))
