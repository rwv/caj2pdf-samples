# SPDX-License-Identifier: MIT
"""Individually proved CAJ metadata repairs; raw stream data remains unchanged."""
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

from pdf_source_inventory import JSON_LIMIT, digest, value_hash
from pdf_source_graphs import require
from caj_source_navigation import source_navigation
from caj_source_preservation import acquired_objects, check_objects


MATRIX_SOURCES = {
    '2423e0b8e64060bc55cf004da3c7f79b411739753e89e39ebefcea44b300b968',
    'f08947012a4882d3f62c9e3552f5a889d4bc7dee22f3a5119f22b7cb298b180f',
}
AP_SOURCE = 'd3d8a89dc8ac9212a445935c55e29ac93224df1d157e891aebb2fb1f652906b6'
PATH_SOURCE = 'b206e40da6df3fbe07ea6c7b40e900de5fe35b16f7e25029c3cfde38eb603d03'
FIELD_SOURCES = MATRIX_SOURCES | {AP_SOURCE, PATH_SOURCE}
REPORTS = {
    'pattern-matrix-fallback': '609611706bf9910bf74eb9a3c2b3d8e1372abd465372ec8b26b057d8dd7ddd01',
    'missing-link-appearance': '7498520036c3f3ca32eea442e31d1de8d4ca200051ddf4d3cd0b33e8b4b53c65',
    'qite-source-path-strings': 'e46a8746371a7a9afb09de26455f5953197aebde70d65631520ef11dd1a76940',
}


def bounded_bytes(source, at, count):
    require(type(at) is int and type(count) is int and 0 <= at < at+count <= source.stat().st_size
            and count <= 4096, 'metadata witness range bound')
    with source.open('rb') as stream:
        stream.seek(at)
        result = stream.read(count)
    require(len(result) == count, 'truncated metadata witness')
    return result


def read_report(notes, name):
    path = notes/(name+'-20261008.json')
    require(path.stat().st_size <= JSON_LIMIT and digest(path) == REPORTS[name], 'reviewed field proof changed')
    return json.loads(path.read_text())


def matrix_value(value):
    require(isinstance(value, dict) and value.get('/Type') == '/Pattern'
            and value.get('/PatternType') == value.get('/PaintType') == value.get('/TilingType') == 1,
            'unmeasured pattern kind')
    expected = [Decimal('0.72'), 0, 0, Decimal('-0.719999'), 'u:-5e-006', 842]
    require(value_hash(value.get('/Matrix')) == value_hash(expected), 'unmeasured malformed Matrix')
    return {**value, '/Matrix': [1, 0, 0, 1, 0, 0]}


def missing_appearance(value, target, original, objects):
    require(isinstance(value, dict) and value.get('/Subtype') == '/Link' and value.get('/BS') == {'/W': 0}
            and value.get('/AP') == {}, 'unmeasured missing Link appearance')
    require(f'obj:{target} 0 R' not in objects, 'appearance target is selected/live')
    pattern = rb'/AP\s*<<\s*/N\s+'+str(target).encode()+rb'\s+0\s+R\s*>>'
    require(len(re.findall(rb'/AP\b', original)) == 1 and re.search(pattern, original),
            'original AP is not the measured single missing N reference')
    return {key: item for key, item in value.items() if key != '/AP'}


def path_value(original, number, size, expected_hash):
    prefix, suffix = f'{number} 0 obj\r('.encode(), b')\rendobj'
    require(original.startswith(prefix) and original.endswith(suffix), 'unmeasured path object framing')
    payload = original[len(prefix):-len(suffix)]
    require(len(payload) == size and hashlib.sha256(payload).hexdigest() == expected_hash,
            'raw path payload differs from reviewed proof')
    # Retain the literal source payload exactly; never interpret or open it as
    # an OS path, and never use the reader's malformed-string interpretation.
    return 'b:'+payload.hex()


def reference_paths(value, target, path=()):
    require(len(path) <= 128, 'reference path depth bound')
    if value == target:
        yield path
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from reference_paths(child, target, path+(key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from reference_paths(child, target, path+(index,))


def path_owners(objects, target, owners):
    actual = {}
    for key, wrapper in objects.items():
        value = wrapper['value'] if 'value' in wrapper else wrapper['stream']['dict']
        paths = list(reference_paths(value, target))
        if paths:
            require(key != 'trailer' and 'value' in wrapper and isinstance(value, dict)
                    and value.get('/Type') == '/Page',
                    'path target used outside a Page')
            actual[key] = paths
    require(actual == {f'obj:{owner} 0 R': [('/QITE_pageid', '/F')] for owner in owners},
            'path reference has unproved owner/role')


def replace_expected(objects, records, key, value, events, proof):
    before = objects[key]
    if 'stream' in before:
        objects[key] = {'stream': {**before['stream'], 'dict': value}}
    else:
        objects[key] = {'value': value}
    prior = records[key]['value_sha256']
    expected = value_hash(value)
    records[key] = {**records[key], 'value_sha256': expected}
    if expected != prior:
        events.append({'object': key, 'proof': proof, 'source_value_sha256': prior,
                       'expected_value_sha256': expected})


def original_metadata(row, number):
    """Read a bounded non-stream witness at its source-derived recovered slot."""
    directory = Path(row['inventory_directory'])
    path = directory/'recovery-xref.txt'
    require(path.stat().st_size <= JSON_LIMIT, 'recovered xref witness bound')
    matches = []
    with path.open() as lines:
        for line in lines:
            match = re.fullmatch(str(number)+r'/0: uncompressed; offset = (\d+)\n', line)
            if match:
                matches.append(int(match[1]))
    require(len(matches) == 1, 'missing/duplicate original metadata slot')
    at = matches[0]+row['reference_framing']['body_range'][0]-9
    source = Path(row['source'])
    # Only this already selected non-stream dictionary/array is inspected.
    with source.open('rb') as stream:
        require(0 <= at < source.stat().st_size, 'metadata offset bound')
        stream.seek(at)
        value = bytearray()
        while len(value) < 4096 and not value.endswith(b'endobj'):
            byte = stream.read(1)
            require(byte, 'truncated original metadata')
            value.extend(byte)
    require(value.endswith(b'endobj') and b'stream' not in value
            and re.match(str(number).encode()+rb'\s+0\s+obj\b', value), 'unmeasured metadata witness')
    return bytes(value)


def verify(row, notes=None):
    notes = Path(__file__).resolve().parents[1]/'notes' if notes is None else notes
    sha = row['source_sha256']
    require(sha in FIELD_SOURCES, 'no individually reviewed field profile')
    source, candidate, left, right = acquired_objects(row)
    # Only new expected values are inserted. The immutable acquired receipt
    # still lists every real delta; every raw hash/size remains source-derived.
    normalized, expected = dict(source), dict(left)
    events = []
    if sha in MATRIX_SOURCES:
        name = 'pattern-matrix-fallback'
        report = read_report(notes, name)
        case = next(item for item in report['cases'] if item['source_sha256'] == sha)
        require(case['output_sha256'] == row['pdf_sha256'] and case['source_unchanged'], 'Matrix proof pair changed')
        for item in case['measured_matrices']:
            match = re.search(r'(\d+) 0 obj$', item['object_prefix'])
            require(match, 'unmeasured Matrix object witness')
            key = f'obj:{match[1]} 0 R'
            raw = item['matrix'].encode('ascii')
            require(bounded_bytes(Path(row['source']), item['offset'], len(raw)) == raw, 'Matrix source token changed')
            require(left[key]['kind'] == 'stream', 'Pattern is not an original stream')
            value = matrix_value(source[key]['stream']['dict'])
            replace_expected(normalized, expected, key, value, events, 'pinned measured identity Matrix fallback')
    elif sha == AP_SOURCE:
        name = 'missing-link-appearance'
        report = read_report(notes, name)
        require(report['origin']['sha256'] == sha
                and report['independent_source_comparison']['output_sha256'] == row['pdf_sha256'], 'AP proof pair changed')
        for item in report['source_framing']['facts']['links']:
            number, target = item['object'], item['target']
            require(item['target_object'] == 'null', 'reviewed AP target is live')
            key = f'obj:{number} 0 R'
            raw = original_metadata(row, number)
            value = missing_appearance(source[key]['value'], target, raw, source)
            replace_expected(normalized, expected, key, value, events, 'pinned missing optional Link N appearance')
    else:
        name = 'qite-source-path-strings'
        report = read_report(notes, name)
        require(report['origin']['sha256'] == sha
                and report['independent_source_comparison']['output_sha256'] == row['pdf_sha256'], 'path proof pair changed')
        incoming = report['independent_source_comparison']['facts']['incoming']
        for item in report['normalized_paths']:
            number = item['object']
            begin, end = item['source_range']
            raw = bounded_bytes(Path(row['source']), begin, end-begin)
            value = path_value(raw, number, item['raw_payload_bytes'], item['preserved_payload_sha256'])
            replace_expected(normalized, expected, f'obj:{number} 0 R', value, events, 'pinned raw QITE path payload')
            owners = []
            for owner in incoming[str(number)]:
                require(owner['source_page'] and owner['only_metadata_path'] and owner['occurrences'] == 1
                        and owner['qite_f'] == ['xref', f'{number} 0 R'], 'unproved original path role')
                identity = f'obj:{owner["owner"]} 0 R'
                page = deepcopy(source[identity]['value'])
                require(page.get('/Type') == '/Page' and isinstance(page.get('/QITE_pageid'), dict), 'unmeasured QITE Page')
                metadata = page['/QITE_pageid']
                require('/F' not in metadata or metadata['/F'] == f'{number} 0 R', 'conflicting original QITE path')
                metadata['/F'] = f'{number} 0 R'
                replace_expected(normalized, expected, identity, page, events, 'pinned original Page QITE/F edge')
                owners.append(owner['owner'])
            require(len(owners) == len(set(owners)) == item['incoming_references'], 'path owner count changed')
            path_owners(candidate, f'{number} 0 R', owners)
    result = check_objects(normalized, candidate, expected, right, source_navigation(Path(row['source'])))
    return {**result, 'status': 'VERIFIED_WITH_INDIVIDUAL_FIELD_PROOF', 'field_changes': events,
            'prior_report': name+'-20261008.json', 'prior_report_sha256': REPORTS[name],
            'scope': 'Fresh complete selected-object/raw-stream/navigation verification plus individually pinned measured field repairs. Prior rendering/absence/role limits apply to identical source/output bytes; no new full visual-fidelity claim.'}
