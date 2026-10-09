#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Opt-in source/PDF glyph identity and order checks for measured native HN/C8.

Uses independent record measurements in the research notes, Python's standard
character codecs and PyMuPDF to open PDF objects. This checks semantic glyph
transport, not placement, font outlines, vectors or rendered-page parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zlib

from hnc8_layout_source import FileInput, SourceExtractor

MAX_TEXT_BYTES = 1024 * 1024
MAX_RECORDS = 65536
MAX_CONTENT_BYTES = 4 * 1024 * 1024
# Four-byte state records; their rendering effects are outside this check.
CONTROLS = {0x8001, 0x8002, 0x801d, 0x8067, 0x801c, 0x8072, 0x8073,
            0x8074, 0x8024, 0xc053, 0xc054, 0xffff, 0x8070, 0x8071,
            0x80ce, 0x8069, 0x8021, 0x80d0, 0x80d1, 0x80d2, 0x9002,
            0x80d5, 0x80d3}


def read_exact(source, offset: int, length: int) -> bytes:
    if offset < 0 or length < 0 or offset + length > source.size or length > 65536:
        raise ValueError("source read outside bounded range")
    data = bytearray()
    while len(data) < length:
        part = source.read_at(offset + len(data), length - len(data))
        if not isinstance(part, bytes) or not part or len(part) > length - len(data):
            raise ValueError("invalid source read")
        data.extend(part)
    return bytes(data)


def character(code: int, mode: int) -> str:
    if mode not in (0, 2):
        raise ValueError("unmeasured native character mode")
    if mode == 0:
        if 0xa980 <= code <= 0xa999:
            return chr(ord('A') + code - 0xa980)
        if 0xa99a <= code <= 0xa9b3:
            return chr(ord('a') + code - 0xa99a)
        aliases = {0xa3a7: '\u2019', 0xaab1: '.', 0x9ff5: '\uff0f', 0xa1a1: ' ', 0xaab2: '-'}
        if code in aliases:
            return aliases[code]
        if 0xa3b0 <= code <= 0xa3b9 or 0xa3c1 <= code <= 0xa3da or 0xa3e1 <= code <= 0xa3fa:
            return chr(code - 0xa380)
        code.to_bytes(2, 'big').decode('gb2312')  # Validate the admitted legacy repertoire.
        return code.to_bytes(2, 'big').decode('gb18030')
    aliases = {0xa0a6: '＆', 0xa0ad: '－', 0xa0ae: '．', 0xa0af: '／',
               0xa0ba: ':', 0xaab1: '∙', 0xaab2: '-', 0xaab3: '∗', 0xaca3: '►'}
    if code in aliases:
        return aliases[code]
    if code >> 8 == 0xa0 and 0xa0a0 <= code <= 0xa0fe:
        return chr((code & 255) - 128)
    if code in (0x006c, 0x0070):
        return chr(code)
    return code.to_bytes(2, 'big').decode('gb18030')


def source_glyphs(source, page: dict, variant: str, mode: int, *, image_visitor=None,
                  record_visitor=None) -> tuple[list[str], int]:
    start, length = page['text_offset'], page['text_length']
    if not 0 < length <= MAX_TEXT_BYTES:
        raise ValueError("native text span outside measured bound")
    at, end = start, start + length
    glyphs = []
    for _ in range(MAX_RECORDS):
        if at + 2 > end:
            raise ValueError("native text has no terminator")
        tag = int.from_bytes(read_exact(source, at, 2), 'little')
        if variant == 'HN-B' and at + 2 == end and tag == 0x8004:
            return glyphs, 0
        if at + 4 > end:
            raise ValueError("partial native record")
        value = int.from_bytes(read_exact(source, at + 2, 2), 'little')
        size = 4
        if tag < 0x8000:
            glyphs.append(character(value, mode))
        elif tag == 0x8004:
            if variant != 'HN-B' and at + 4 != end:
                raise ValueError("unmeasured C8 text tail")
            return glyphs, end - at - 4
        elif tag in CONTROLS:
            pass  # Fixed record boundary only; no geometry/state interpretation.
        elif tag == 0xc052 and variant == 'HN-B' and value == 0xa385:
            size = 8
        elif tag == 0x81ff and value in (1, 2, 3) or tag == 0x80cc and value == 0x0204:
            size = 8
        elif tag == 0x80cc and 0x0102 <= value <= 0x01ff:
            size = 2 * (value & 255)
            if at + size > end:
                raise ValueError("partial encoded-string record")
            payload = read_exact(source, at + 4, size - 4)
            # c8-additional-profiles.md: only the final word may be e000.
            if any(not 0xe020 <= word[0] <= 0xe07e
                   and not (word[0] == 0xe000 and 2 * (i + 1) == len(payload))
                   for i, word in enumerate(struct.iter_unpack('<H', payload))):
                raise ValueError("unmeasured encoded-string payload")
        elif tag in (0x8006, 0x8007, 0x8010, 0x8090):
            size = 12
        elif tag == 0x800a and value == 0xd300:
            size = 28
        elif tag == 0x810a and value == 0xd300:
            if at + 16 > end:
                raise ValueError("partial image reference")
            flags, name_bytes = struct.unpack('<HH', read_exact(source, at + 12, 4))
            size = (16 + name_bytes + 3) // 4 * 4
            if flags or at + size > end:
                raise ValueError("unmeasured image reference")
            padding = read_exact(source, at + 16 + name_bytes, size - 16 - name_bytes)
            if any(padding):
                raise ValueError("invalid image reference padding")
            # Aligned names may omit the older four-byte zero pad. Both forms
            # preserve the following record in c8-additional-profiles.md.
            if name_bytes % 4 == 0 and at + size + 4 <= end:
                if read_exact(source, at + size, 4) == b'\0' * 4:
                    size += 4
        else:
            raise ValueError(f"unmeasured native record {tag:04x}/{value:04x} at {at}")
        if at + size > end:
            raise ValueError("partial native payload")
        # Both observers receive only complete, nonterminal records. HN-B's
        # opaque bytes after the terminator are never interpreted as records.
        if record_visitor is not None:
            record_visitor(at, tag, value, size)
        if image_visitor is not None and tag in (0x800a, 0x810a):
            image_visitor(at, tag, size)
        at += size
    raise ValueError("native record budget exceeded")


def identity_cmap(data: bytes) -> bool:
    """Require the writer's unambiguous BMP scalar identity mapping."""
    if len(data) > 65536 or b'beginbfchar' in data or b'usecmap' in data:
        return False
    intervals = []
    blocks = re.findall(rb'(\d+)\s+beginbfrange\s+(.*?)\s+endbfrange', data, re.S)
    if data.count(b'beginbfrange') != len(blocks) or data.count(b'endbfrange') != len(blocks):
        return False
    for count, body in blocks:
        entries = re.findall(rb'<([0-9A-Fa-f]{4})>\s*<([0-9A-Fa-f]{4})>\s*<([0-9A-Fa-f]{4})>', body)
        if len(entries) != int(count) or re.sub(rb'<[0-9A-Fa-f]{4}>|\s', b'', body):
            return False
        intervals.extend(tuple(int(x, 16) for x in row) for row in entries)
    next_code = 0
    for first, last, target in sorted(intervals):
        if next_code == 0xd800 and first == 0xe000:
            next_code = 0xe000  # Surrogates are not Unicode scalar values.
        if first != next_code or target != first or last < first:
            return False
        next_code = last + 1
    return next_code == 65536


def semantic_glyphs(content: bytes) -> list[str]:
    if len(content) > MAX_CONTENT_BYTES:
        raise ValueError("PDF page content exceeds bound")
    plain = re.sub(rb'/Artifact\s+BMC.*?\bEMC\b', b'', content, flags=re.S)
    # ActualText preserves the semantic character when a visible substitute is used.
    plain = re.sub(rb'/Span\s*<<\s*/ActualText\s*<([A-Fa-f0-9]+)>\s*>>\s*BDC.*?\bEMC\b',
                   lambda m: b'Tm <' + m[1].removeprefix(b'FEFF') + b'> Tj', plain, flags=re.S)
    if any(word in plain for word in (b'BDC', b'BMC', b'TJ', b'ActualText')):
        raise ValueError("unmeasured PDF text syntax")
    strings = re.findall(rb'\bTm\s*<([A-Fa-f0-9]+)>\s*Tj\b', plain)
    if len(strings) != len(re.findall(rb'\bTj\b', plain)):
        raise ValueError("unmeasured PDF glyph operation")
    return [bytes.fromhex(value.decode('ascii')).decode('utf-16-be') for value in strings]


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def raw_stream(document, xref: int, limit: int) -> bytes:
    kind, length = document.xref_get_key(xref, 'Length')
    if kind == 'xref':
        length = document.xref_object(int(length.split()[0])).strip()
    elif kind != 'int':
        raise ValueError("PDF stream length is not an integer")
    if not re.fullmatch(r"[0-9]{1,10}", length) or int(length) > limit + 65536:
        raise ValueError("encoded PDF stream exceeds bound")
    data = document.xref_stream_raw(xref)
    if len(data) != int(length):
        raise ValueError("PDF stream length differs")
    filter_value = document.xref_get_key(xref, 'Filter')
    if filter_value == ('name', '/FlateDecode'):
        if document.xref_get_key(xref, 'DecodeParms')[0] != 'null':
            raise ValueError("unmeasured PDF decode parameters")
        decoder = zlib.decompressobj()
        data = decoder.decompress(data, limit + 1)
        if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
            raise ValueError("incomplete or oversized PDF Flate stream")
    elif filter_value[0] != 'null':
        raise ValueError("unmeasured PDF stream filter")
    if len(data) > limit:
        raise ValueError("decoded PDF stream exceeds bound")
    return data


def verify(source: Path, pdf: Path, expected_sha: str) -> dict:
    import fitz  # Optional research dependency; not imported for parser unit tests.
    if digest(source) != expected_sha:
        raise ValueError("source SHA-256 differs")
    pdf_sha = digest(pdf)
    pages = []
    with FileInput(source) as data, fitz.open(pdf) as output:
        reader = SourceExtractor(data, expected_sha)
        variant = reader.header['variant']
        if variant not in ('C8', 'HN-B') or len(output) != reader.header['page_count']:
            raise ValueError("native profile/page count differs")
        mode = int.from_bytes(read_exact(data, 12 if variant == 'C8' else 148, 2), 'little')
        checked_fonts = set()
        for page in reader.iter_pages():
            expected, opaque_tail = source_glyphs(data, page, variant, mode)
            actual_page = output[page['page_number'] - 1]
            for font in actual_page.get_fonts():
                if font[0] in checked_fonts:
                    continue
                encoding = output.xref_get_key(font[0], 'Encoding')
                kind, value = output.xref_get_key(font[0], 'ToUnicode')
                if encoding != ('name', '/Identity-H') or kind != 'xref':
                    raise ValueError("unmeasured PDF font encoding")
                if not identity_cmap(raw_stream(output, int(value.split()[0]), 65536)):
                    raise ValueError("PDF Unicode map is not the verified identity mapping")
                checked_fonts.add(font[0])
            parts = []
            size = 0
            for xref in actual_page.get_contents():
                block = raw_stream(output, xref, MAX_CONTENT_BYTES - size)
                size += len(block)
                if size > MAX_CONTENT_BYTES:
                    raise ValueError("PDF page content exceeds bound")
                parts.append(block)
            content = b''.join(parts)
            declared_fonts = {font[4].encode() for font in actual_page.get_fonts()}
            if any(name not in declared_fonts for name in re.findall(rb'/([A-Za-z0-9]+)\s+[\d.]+\s+Tf\b', content)):
                raise ValueError("PDF text uses an undeclared font")
            actual = semantic_glyphs(content)
            pages.append({'page': page['page_number'], 'source_glyphs': len(expected),
                          'pdf_glyphs': len(actual), 'unicode_order': 'PASS' if expected == actual else 'FAIL',
                          'glyph_sequence_sha256': hashlib.sha256(''.join(expected).encode()).hexdigest(),
                          'source_images': len(page['images']), 'ignored_hnb_tail_bytes': opaque_tail})
    if digest(source) != expected_sha or digest(pdf) != pdf_sha:
        raise ValueError("input changed during verification")
    return {'source_sha256': expected_sha, 'pdf_sha256': pdf_sha, 'pymupdf': fitz.VersionBind,
            'status': 'PASS' if all(p['unicode_order'] == 'PASS' for p in pages) else 'FAIL',
            'scope': 'All native glyph identities/order, including ActualText; not geometry, font outlines, vectors or pixel parity',
            'pages': pages}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    result = verify(args.source, args.pdf, args.sha256)
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
