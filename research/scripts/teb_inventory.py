#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Bounded metadata inventory of measured TEB containers; no content recovery.

Original byte observations and public ZIP framing only. Names, XML text,
credentials and payload bytes are never written to the report or extracted.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET
import zlib

CHUNK = 65536
MAX_SOURCE = 512 * 1024 * 1024
BASE = 160
LOCAL = struct.Struct('<4s5H3IH')
CENTRAL = struct.Struct('<4s6H3I4HI')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as source:
        while value := source.read(CHUNK):
            result.update(value)
    return result.hexdigest()


def read(source, offset, length):
    require(0 <= length <= CHUNK and offset >= 0, 'metadata read limit')
    source.seek(offset)
    value = source.read(length)
    require(len(value) == length, 'short source read')
    return value


def xml_metadata(data, root_name):
    require(len(data) <= CHUNK and b'\0' not in data and b'<!DOCTYPE' not in data.upper()
            and b'<!ENTITY' not in data.upper(), 'XML size/entity boundary')
    try:
        data.decode('utf-8')
        root = ET.fromstring(data)
    except (ET.ParseError, UnicodeDecodeError):
        raise ValueError('invalid UTF-8 XML structure') from None
    require(root.tag == root_name, 'unmeasured XML root')
    nodes = list(root.iter())
    require(len(nodes) <= 128, 'XML element limit')
    shape = []
    for node in nodes:
        names = [node.tag, *node.attrib]
        require(all(re.fullmatch(r'[a-zA-Z][a-zA-Z0-9-]{0,63}', n) for n in names), 'XML name profile')
        shape.append({'tag': node.tag, 'attribute_names': sorted(node.attrib),
                      'text_bytes': len((node.text or '').encode('utf-8'))})
    return root, shape


def payload(source, offset, stored, method, plain, crc):
    require(method in (0, 8) and (method != 0 or stored == plain), 'unmeasured storage method')
    require(method != 8 or max(stored, plain) <= CHUNK, 'deflate metadata size limit')
    remaining, checksum, sha = stored, 0, hashlib.sha256()
    prefix, compressed = b'', bytearray()
    source.seek(offset)
    while remaining:
        value = source.read(min(CHUNK, remaining))
        require(value, 'short payload')
        remaining -= len(value); checksum = zlib.crc32(value, checksum); sha.update(value)
        if not prefix:
            prefix = value[:1024]
        if method == 8:
            compressed.extend(value)
    result = {'payload_sha256': sha.hexdigest(), 'raw_crc_matches': checksum == crc,
              'pdf_header_in_first_1024_bytes': b'%PDF-' in prefix}
    decoded = None
    if method == 8:
        decoder = zlib.decompressobj(-15)
        try:
            decoded = decoder.decompress(compressed, CHUNK + 1)
        except zlib.error as error:
            raise ValueError('invalid raw deflate metadata') from error
        require(len(decoded) == plain and decoder.eof and not decoder.unused_data
                and not decoder.unconsumed_tail, 'deflate extent/termination mismatch')
        require(zlib.crc32(decoded) == crc, 'decoded metadata CRC mismatch')
        result['decoded_crc_matches'] = True
        result['decoded_sha256'] = hashlib.sha256(decoded).hexdigest()
    else:
        require(checksum == crc, 'stored payload CRC mismatch')
    return result, decoded


def inspect(path, expected_sha):
    size = path.stat().st_size
    require(BASE + 16 <= size <= MAX_SOURCE and digest(path) == expected_sha, 'source size/hash mismatch')
    with path.open('rb') as source:
        header = read(source, 0, BASE)
        require(header[:8] == b'TEB\0\x04\0\0\0' and not any(header[8:32]), 'unmeasured TEB header')
        require(header[32:].rstrip(b'\0') == b'Tongfang Knowledge Network Technology(Beijing) Co., Ltd.',
                'unmeasured producer field')
        sig, count, directory_size, relative = struct.unpack('<4s3I', read(source, BASE, 16))
        require(sig == b'PK\x08\x08' and count == 2, 'unmeasured archive header')
        directory_at = BASE + relative
        require(BASE + 16 <= directory_at < size and 80 <= directory_size <= CHUNK
                and directory_at + directory_size < size, 'directory extent')
        directory = read(source, directory_at, directory_size)
        at, entries, spans, metadata, names = 0, [], [], None, []
        for _ in range(count):
            require(at + CENTRAL.size <= len(directory), 'short central record')
            fields = CENTRAL.unpack_from(directory, at)
            sig, made, version, flags, method, mtime, date, crc, stored, plain, nlen, extra, comment, disk, local = fields
            require(sig == b'PK\x01\x02' and made == 0 and version == 20
                    and extra == comment == disk == 0, 'unmeasured central record')
            require(1 <= nlen <= 255 and at + CENTRAL.size + nlen <= len(directory), 'central name limit')
            name = bytes(b ^ i for i, b in enumerate(directory[at + CENTRAL.size:at + CENTRAL.size + nlen]))
            require(name not in names, 'duplicate internal name'); names.append(name)
            kind = 'metadata' if name == b'document.xml' else 'declared-pdf'
            require(kind == 'metadata' or re.fullmatch(rb'content\\CAJ[0-9A-Fa-f]+\.pdf', name), 'unmeasured internal name')
            require((kind, method, flags) in (('metadata', 8, 2), ('declared-pdf', 0, 0)), 'entry storage profile')
            local_at = BASE + local; data_at = local_at + LOCAL.size
            require(BASE + 16 <= local_at and data_at <= directory_at
                    and 0 < stored <= directory_at - data_at, 'local payload extent')
            actual = LOCAL.unpack(read(source, local_at, LOCAL.size))
            require(actual == (b'PK\x03\x04', version, flags, method, mtime, date, crc, stored, plain, nlen),
                    'local/central disagreement')
            checks, decoded = payload(source, data_at, stored, method, plain, crc)
            entry = {'kind': kind, 'local_header_offset': local_at, 'payload_offset': data_at,
                     'stored_bytes': stored, 'declared_uncompressed_bytes': plain, 'method': method,
                     'flags': flags, 'declared_crc32': crc, **checks}
            if decoded is not None:
                metadata, shape = xml_metadata(decoded, 'document-meta')
                entry['xml_structure'] = shape
            entries.append(entry); spans.append((local_at, data_at + stored)); at += CENTRAL.size + nlen
        require(at == len(directory) and {e['kind'] for e in entries} == {'metadata', 'declared-pdf'}, 'entry inventory')
        spans.sort()
        require(spans[0][0] == BASE + 16 and spans[0][1] == spans[1][0]
                and spans[1][1] == directory_at, 'entry gap/overlap')
        content = metadata.findall('./structure/content')
        urls = metadata.findall('./structure/content/item/url')
        require(len(content) == len(urls) == 1 and urls[0].text is not None
                and urls[0].text in [name.decode('ascii') for name in names if name != b'document.xml'],
                'metadata content reference')
        pages = content[0].get('page-count', '')
        require(re.fullmatch(r'[0-9]{1,6}', pages) and 0 < int(pages) <= 100000, 'declared page count')
        wrapper_at = directory_at + directory_size
        tail = read(source, wrapper_at, size - wrapper_at)
        closing = tail.find(b'</right-meta>')
        require(closing >= 0, 'missing rights wrapper')
        xml_end = closing + len(b'</right-meta>')
        rights, shape = xml_metadata(tail[:xml_end], 'right-meta')
        footer = re.fullmatch(rb'([ \t\r\n]*)startrights ([0-9]+),([0-9]+)\s*', tail[xml_end:])
        require(footer is not None and int(footer[2]) == wrapper_at
                and int(footer[3]) == xml_end + len(footer[1]),
                'rights footer extent')
        require(rights.findtext('version') == '2.1', 'unmeasured rights version')
        encrypt = rights.findall('./protect/encrypt')
        require(len(encrypt) == 1 and encrypt[0].attrib == dict.fromkeys(('meta', 'catalog', 'notes', 'content'), '1'),
                'unmeasured protection declaration')
    require(digest(path) == expected_sha, 'source changed')
    return {'source_sha256': expected_sha, 'source_bytes': size, 'source_unchanged': True,
            'status': 'INVENTORIED', 'archive_offset': BASE, 'directory_offset': directory_at,
            'directory_bytes': directory_size, 'entries': entries, 'declared_pages_not_decoded': int(pages),
            'rights_offset': wrapper_at, 'rights_xml_element_extent': xml_end,
            'rights_declared_bytes_including_whitespace': int(footer[3]), 'rights_version': '2.1',
            'encryption_declarations': dict(encrypt[0].attrib), 'rights_xml_structure': shape,
            'scope': 'Container integrity and declared metadata only; no PDF recovery, decryption or irrecoverability proof'}


def compare_zero_suffix(damaged, intact, damaged_sha, intact_sha):
    size = damaged.stat().st_size
    require(size == intact.stat().st_size and 0 < size <= MAX_SOURCE, 'comparison size')
    require(digest(damaged) == damaged_sha and digest(intact) == intact_sha, 'comparison hash')
    first, changed, at = None, 0, 0
    with damaged.open('rb') as bad, intact.open('rb') as good:
        while a := bad.read(CHUNK):
            b = good.read(len(a)); require(len(a) == len(b), 'short comparison read')
            for i, (x, y) in enumerate(zip(a, b)):
                if x != y:
                    first = at + i if first is None else first
                    changed += 1
                if first is not None:
                    require(x == 0, 'nonzero byte after divergence')
            at += len(a)
    require(first is not None and at == size, 'no divergent zero suffix')
    require(digest(damaged) == damaged_sha and digest(intact) == intact_sha, 'comparison source changed')
    return {'damaged_sha256': damaged_sha, 'intact_candidate_sha256': intact_sha, 'source_bytes': size,
            'identical_prefix_bytes': first, 'zero_suffix_bytes': size - first,
            'different_byte_count': changed, 'both_sources_unchanged': True,
            'scope': 'Separate candidate matches the surviving prefix; no automatic substitution or recovered-source claim'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.source, args.sha256), indent=2))
