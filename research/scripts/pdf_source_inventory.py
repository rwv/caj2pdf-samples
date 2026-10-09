# SPDX-License-Identifier: MIT
"""Initial independent qpdf JSON/raw-stream inventory, not a fidelity verdict."""
from decimal import Decimal
import hashlib
import json
import mmap
from pathlib import Path
import resource
import re
import subprocess
import struct
import time

FILE_LIMIT = 512*1024*1024
JSON_LIMIT = 32*1024*1024


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def limits():
    resource.setrlimit(resource.RLIMIT_AS, (2*1024**3, 2*1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (FILE_LIMIT, FILE_LIMIT))
    resource.setrlimit(resource.RLIMIT_CPU, (110, 110))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def decode_kdh(source, target):
    # Documented wrapper facts, independent sequential transform. Preserve the
    # entire decoded tail; do not invent an EOF boundary from converter output.
    key = b'FZHMEI'
    with source.open('rb') as src, target.open('xb') as dst:
        if src.read(32) != b'KDH 2.00 Copyright(C) 2000 CAJCD':
            raise ValueError('unmeasured KDH signature')
        src.seek(254)
        offset = 0
        while block := src.read(65536):
            dst.write(bytes(byte ^ key[(offset+i) % 6] for i, byte in enumerate(block)))
            offset += len(block)
    with target.open('rb') as stream:
        if not stream.read(8).startswith(b'%PDF-'):
            raise ValueError('decoded KDH header mismatch')


def frame_caj(source, target, pages):
    """Preserve the body through EOF and add only fresh inventory framing.

    This wrapper enables object inventory without inventing a source hierarchy.
    It is not a rendered-page reference. Actual catalog/page reachability still
    needs its own source/table proof. No candidate byte or object is consulted.
    """
    size = source.stat().st_size
    with source.open('rb') as src:
        header = src.read(32)
        if len(header) != 32 or header[:4] != b'CAJ\0':
            raise ValueError('unmeasured CAJ header')
        count, table = struct.unpack_from('<II', header, 16)
        if not (count == pages and 1 <= count <= 100000 and 32 <= table <= size-12*count):
            raise ValueError('CAJ table bounds/count')
        src.seek(table)
        rows = [struct.unpack('<III', src.read(12)) for _ in range(count)]
        if not all(table+12*count <= start <= start+length <= size and page > 0
                   for start, length, page in rows):
            raise ValueError('CAJ fragment range/page identity')
        begin, hint_end = min(x[0] for x in rows), max(x[0]+x[1] for x in rows)
        if begin == hint_end:
            raise ValueError('empty CAJ body')
        # The table endpoint is only a hint: documented originals include
        # final stream bytes after it. Retain even opaque container tails;
        # reader recovery remains an observation, not a trusted source parser.
        end = size
        # An absent decimal substring cannot be an existing indirect object or
        # reference, even with signs/leading zeros/comments between tokens.
        # This is conservative byte occupancy, not an object-header parser.
        ids = []
        with mmap.mmap(src.fileno(), 0, access=mmap.ACCESS_READ) as data:
            candidates = [n for start in (32, 1000, 10000, 100000) for n in range(start, start+32)]
            for number in candidates:
                if data.find(str(number).encode(), begin, end) < 0:
                    ids.append(number)
                    if len(ids) == 3:
                        break
        if len(ids) != 3:
            raise ValueError('no bounded fresh framing identifiers')
        catalog, tree, blank = ids
        with target.open('xb') as dst:
            dst.write(b'%PDF-1.7\n')
            src.seek(begin)
            remaining = end-begin
            while remaining:
                block = src.read(min(65536, remaining))
                if not block:
                    raise ValueError('truncated CAJ body')
                dst.write(block)
                remaining -= len(block)
            dst.write((f'\n{catalog} 0 obj\n<< /Type /Catalog /Pages {tree} 0 R >>\nendobj\n'
                       f'{tree} 0 obj\n<< /Type /Pages /Count 1 /Kids [{blank} 0 R] >>\nendobj\n'
                       f'{blank} 0 obj\n<< /Type /Page /Parent {tree} 0 R /MediaBox [0 0 1 1]'
                       ' /Resources << >> >>\nendobj\n'
                       f'xref\n0 1\n0000000000 65535 f \ntrailer\n<< /Size {max(ids)+1}'
                       f' /Root {catalog} 0 R >>\nstartxref\n0\n%%EOF\n').encode())
        # Obtain only source-derived offsets from qpdf recovery. Then append a
        # complete index pointing at those same original bytes. Never save a
        # reserialized body: that could round numbers or repair Page values.
        command = ['qpdf', '--show-xref', str(target)]
        with (target.parent/'recovery-xref.txt').open('wb') as stdout, (target.parent/'recovery.log').open('wb') as stderr:
            recovered = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=120, preexec_fn=limits)
        if recovered.returncode not in (0, 3):
            raise ValueError('qpdf source index recovery exit '+str(recovered.returncode))
        offsets = {}
        xref_text = target.parent/'recovery-xref.txt'
        if xref_text.stat().st_size > JSON_LIMIT:
            raise ValueError('recovered xref size bound')
        with target.open('rb') as check, xref_text.open() as index:
            for line in index:
                match = re.fullmatch(r'(\d+)/(\d+): uncompressed; offset = (\d+)\n', line)
                if not match:
                    raise ValueError('unmeasured recovered xref entry')
                number, generation, offset = map(int, match.groups())
                if not (0 < number <= 1_000_000 and generation == 0 and number not in offsets):
                    raise ValueError('recovered object bound/generation/duplicate')
                check.seek(offset)
                prefix = check.read(128)
                if not re.match(str(number).encode()+rb'[\x00\t\n\x0c\r ]+0[\x00\t\n\x0c\r ]+obj\b', prefix):
                    raise ValueError('recovered offset not an original header')
                offsets[number] = offset
        maximum = max(offsets)
        if not all(n in offsets for n in ids):
            raise ValueError('source reader omitted inventory framing')
        if target.stat().st_size + 20*(maximum+1) + 256 > FILE_LIMIT:
            raise ValueError('reference PDF byte bound')
        with target.open('ab') as dst:
            at = dst.tell()
            dst.write(f'xref\n0 {maximum+1}\n0000000000 65535 f \n'.encode())
            for n in range(1, maximum+1):
                dst.write(f'{offsets[n]:010d} 00000 n \n'.encode() if n in offsets
                          else b'0000000000 00000 f \n')
            dst.write(f'trailer\n<< /Size {maximum+1} /Root {catalog} 0 R >>\nstartxref\n{at}\n%%EOF\n'.encode())
        return {'body_range': [begin, end], 'table_hint_end': hint_end,
                'bytes_after_table_hint': end-hint_end, 'page_ids': [x[2] for x in rows],
                'zero_length_rows': sum(x[1] == 0 for x in rows),
                'synthetic_catalog': catalog, 'synthetic_pages': tree, 'synthetic_blank': blank,
                'recovered_objects': len(offsets), 'xref_size': maximum+1,
                'recovery_exit': recovered.returncode, 'recovery_xref_sha256': digest(xref_text),
                'recovery_warnings_sha256': digest(target.parent/'recovery.log'),
                'scope': 'Unchanged body through source EOF, including any opaque container tail, and source-reader offset replay for object inventory only; synthetic blank page is not a source page reference.'}


def canonical(value, depth=0):
    if depth > 128:
        raise ValueError('metadata nesting bound')
    if value is None:
        return ['null']
    if isinstance(value, bool):
        return ['boolean', value]
    if isinstance(value, int):
        return ['integer', str(value)]
    if isinstance(value, Decimal):
        # Preserve all digits. Decimal.normalize() would round through the
        # current arithmetic context and could hide a change after digit 28.
        return ['real', str(value)]
    if isinstance(value, str):
        return ['string', value]
    if isinstance(value, list):
        return ['array', [canonical(v, depth+1) for v in value]]
    if isinstance(value, dict):
        return ['dictionary', [[k, canonical(v, depth+1)] for k, v in sorted(value.items())]]
    raise TypeError(type(value))


def value_hash(value):
    return hashlib.sha256(json.dumps(canonical(value), separators=(',', ':')).encode()).hexdigest()


def inventory(pdf, directory):
    directory.mkdir()
    output = directory/'objects.json'
    command = ['qpdf', '--json-output=2', '--json-stream-data=file', '--decode-level=none',
               '--json-stream-prefix='+str(directory/'raw'), str(pdf), str(output)]
    start = time.monotonic()
    with (directory/'stdout.log').open('wb') as stdout, (directory/'stderr.log').open('wb') as stderr:
        result = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=120, preexec_fn=limits)
    (directory/'command.json').write_text(json.dumps({'command': command, 'exit': result.returncode,
        'seconds': time.monotonic()-start}, indent=2)+'\n')
    if result.returncode not in (0, 3):
        raise ValueError('qpdf inventory exit '+str(result.returncode))
    if output.stat().st_size > JSON_LIMIT:
        raise ValueError('metadata exceeds 32 MiB')
    parsed = json.loads(output.read_text(), parse_float=Decimal)
    if set(parsed) != {'qpdf'} or len(parsed['qpdf']) != 2:
        raise ValueError('unexpected qpdf JSON envelope')
    header, raw_objects = parsed['qpdf']
    if header['jsonversion'] != 2 or header.get('calledgetallpages') or header.get('pushedinheritedpageresources'):
        raise ValueError('qpdf mutated page inheritance before inventory')
    if len(raw_objects) > 1_000_000:
        raise ValueError('object count bound')
    objects = {}
    for identity, wrapper in raw_objects.items():
        if 'stream' in wrapper:
            stream = wrapper['stream']
            body = Path(stream['datafile'])
            if body.parent != directory or not body.name.startswith('raw-') or body.stat().st_size > FILE_LIMIT:
                raise ValueError('unmeasured stream artifact path/size')
            record = {'kind': 'stream', 'value_sha256': value_hash(stream['dict']),
                      'raw_sha256': digest(body), 'raw_bytes': body.stat().st_size}
        elif set(wrapper) == {'value'}:
            record = {'kind': 'value', 'value_sha256': value_hash(wrapper['value'])}
        else:
            raise ValueError('unexpected object envelope')
        objects[identity] = record
    return {'exit': result.returncode, 'objects': objects, 'json_sha256': digest(output),
            'warnings_sha256': digest(directory/'stderr.log'), 'warnings_bytes': (directory/'stderr.log').stat().st_size,
            'header': header}


def probe(case, output, *, build_reference=None):
    source, pdf = Path(case['source']), Path(case['pdf'])
    if not (source.stat().st_size <= FILE_LIMIT and pdf.stat().st_size <= FILE_LIMIT
            and digest(source) == case['source_sha256'] and digest(pdf) == case['pdf_sha256']):
        raise ValueError('input identity/size mismatch')
    directory = output/case['source_sha256']
    directory.mkdir()
    result = {**case, 'inventory_directory': str(directory), 'status': 'NOT_CONFIRMED'}
    try:
        reference = source
        framing = None
        if build_reference is not None:
            reference, framing, prior_proof = build_reference(case, directory)
            result['prior_proof'] = prior_proof
        elif case['format'] == 'KDH':
            reference = directory/'decoded-full-tail.pdf'
            decode_kdh(source, reference)
        elif case['format'] == 'CAJ':
            reference = directory/'source-body-inventory.pdf'
            framing = frame_caj(source, reference, case['pages'])
        if framing is not None:
            result['reference_framing'] = framing
        result['reference_sha256'] = digest(reference)
        result['reference_bytes'] = reference.stat().st_size
        a, b = inventory(reference, directory/'source'), inventory(pdf, directory/'candidate')
        left, right = a.pop('objects'), b.pop('objects')
        if framing:
            catalog, tree, blank = framing['synthetic_catalog'], framing['synthetic_pages'], framing['synthetic_blank']
            expected = {f'obj:{catalog} 0 R': {'/Type': '/Catalog', '/Pages': f'{tree} 0 R'},
                        f'obj:{tree} 0 R': {'/Type': '/Pages', '/Count': 1, '/Kids': [f'{blank} 0 R']},
                        f'obj:{blank} 0 R': {'/Type': '/Page', '/Parent': f'{tree} 0 R',
                                            '/MediaBox': [0, 0, 1, 1], '/Resources': {}},
                        'trailer': {'/Size': framing['xref_size'], '/Root': f'{catalog} 0 R'}}
            for identity, value in expected.items():
                if left.pop(identity) != {'kind': 'value', 'value_sha256': value_hash(value)}:
                    raise ValueError('synthetic framing not read as authored')
            result['excluded_source_synthetic_only'] = list(expected)
        missing, added = sorted(left.keys()-right.keys()), sorted(right.keys()-left.keys())
        changed = []
        for identity in sorted(left.keys() & right.keys()):
            if left[identity] != right[identity]:
                changed.append({'object': identity, 'source': left[identity], 'candidate': right[identity]})
        result.update(source_reader=a, candidate_reader=b, source_objects=len(left), candidate_objects=len(right),
                      source_streams=sum(x['kind']=='stream' for x in left.values()),
                      candidate_streams=sum(x['kind']=='stream' for x in right.values()),
                      missing=missing, added=added, changed=changed,
                      status='IDENTICAL_INVENTORY' if not (missing or added or changed or a['exit'] or b['exit'])
                             else 'REQUIRES_REVIEW')
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        result['reason'] = str(error)
    result['source_unchanged'] = digest(source) == case['source_sha256']
    result['pdf_unchanged'] = digest(pdf) == case['pdf_sha256']
    if not result['source_unchanged'] or not result['pdf_unchanged']:
        result['status'] = 'NOT_CONFIRMED'
    (directory/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    return result
