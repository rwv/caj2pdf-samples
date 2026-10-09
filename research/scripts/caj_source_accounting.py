# SPDX-License-Identifier: MIT
"""Account for complete measured CAJ PDF bodies without parsing stream programs.

Uses this repository's original bounded PDF display-value grammar as a syntax
subset, adding raw-source CR comments, opaque non-ASCII names and bounded larger
arrays. The source tree/stream bytes, not converter output, define every span.
"""
from decimal import Decimal
import hashlib
import re
import struct

from hnc8_outline_observation import PdfValueParser, Ref, ObservationError, MAX_DEPTH
from pdf_source_inventory import FILE_LIMIT
from pdf_source_graphs import require

WHITE = b'\x00\t\n\x0c\r '
MAX_METADATA = 16384


class SourceValueParser(PdfValueParser):
    def __init__(self, data):
        require(type(data) is bytes and len(data) <= MAX_METADATA, 'source metadata byte bound')
        super().__init__(data)

    def complete(self):
        try:
            return super().complete()
        except ObservationError as error:
            raise ValueError('source metadata syntax: '+str(error)) from error

    def space(self):
        while self.cursor < len(self.data):
            byte = self.data[self.cursor]
            if byte in WHITE:
                self.cursor += 1
            elif byte == 37:
                end = re.search(rb'[\r\n]', self.data[self.cursor:])
                self.cursor = len(self.data) if end is None else self.cursor+end.start()+1
            else:
                break

    def value(self, depth=0):
        self.space()
        require(depth <= MAX_DEPTH and self.cursor < len(self.data), 'source syntax depth/truncation')
        if self.data[self.cursor] == 47:
            self.cursor += 1
            start = self.cursor
            while self.cursor < len(self.data) and self.data[self.cursor] not in WHITE+b'()<>[]{}/%':
                self.cursor += 1
            raw = self.data[start:self.cursor]
            require(len(raw) <= 128 and not re.search(rb'#(?![0-9A-Fa-f]{2})', raw), 'source name syntax/bound')
            raw = re.sub(rb'#([0-9A-Fa-f]{2})', lambda m: bytes([int(m[1], 16)]), raw)
            # A reversible opaque name, not a font-name encoding hypothesis.
            return '/'+raw.decode('latin1')
        if self.data[self.cursor] == 91:
            self.cursor += 1
            result = []
            while True:
                self.space()
                if self.data[self.cursor:self.cursor+1] == b']':
                    self.cursor += 1
                    return result
                require(len(result) < 4096, 'source array item bound')
                result.append(self.value(depth+1))
        return super().value(depth)


def source_references(value, path=()):
    require(len(path) <= MAX_DEPTH, 'source reference depth bound')
    if isinstance(value, Ref):
        yield value.number, path
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from source_references(child, path+(key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from source_references(child, path+(index,))


def read_range(source, begin, end, *, cap=MAX_METADATA):
    require(type(begin) is int and type(end) is int and 0 <= begin <= end <= source.stat().st_size <= FILE_LIMIT
            and end-begin <= cap, 'source read range bound')
    with source.open('rb') as stream:
        stream.seek(begin)
        data = stream.read(end-begin)
    require(len(data) == end-begin, 'truncated source range')
    return data


def range_hash(source, begin, end):
    require(0 <= begin <= end <= source.stat().st_size <= FILE_LIMIT, 'source hash range bound')
    result = hashlib.sha256()
    with source.open('rb') as stream:
        stream.seek(begin)
        while begin < end:
            chunk = stream.read(min(65536, end-begin))
            require(chunk, 'truncated source hash range')
            result.update(chunk)
            begin += len(chunk)
    return result.hexdigest()


def equal_ranges(source, a, b, size):
    require(0 <= size and 0 <= min(a, b) and max(a, b)+size <= source.stat().st_size <= FILE_LIMIT, 'source equality range bound')
    with source.open('rb') as first, source.open('rb') as second:
        first.seek(a)
        second.seek(b)
        while size:
            count = min(65536, size)
            block = first.read(count)
            require(len(block) == count and second.read(count) == block, 'source counterpart bytes differ')
            size -= count


def source_layout(source):
    header = read_range(source, 0, 32)
    require(header[:4] == b'CAJ\0', 'source CAJ signature')
    count, table = struct.unpack_from('<II', header, 16)
    require(0 < count <= 100000 and 32 <= table <= source.stat().st_size-12*count, 'source table bound')
    start = source.stat().st_size
    page_ids = []
    with source.open('rb') as stream:
        stream.seek(table)
        for _ in range(count):
            offset, length, page = struct.unpack('<III', stream.read(12))
            require(table+12*count <= offset <= offset+length <= source.stat().st_size and page > 0,
                    'source fragment range')
            start = min(start, offset)
            page_ids.append(page)
    require(len(set(page_ids)) == count, 'repeated source table page identity')
    return start, page_ids


def partial_header(source, begin, end, selected):
    raw = read_range(source, begin, end, cap=256)
    if not raw.strip(WHITE):
        return None
    prefix = raw.lstrip(WHITE)
    require(prefix.endswith(b'\r\n'), 'unexplained source gap delimiter')
    prefix = prefix[:-2]
    match = re.match(rb'([1-9][0-9]*) ', prefix)
    require(match and match[1].decode() in selected, 'unproved partial header identity')
    number = match[1].decode()
    full = f'{number} 0 obj'.encode()
    require(len(number)+1 <= len(prefix) < len(full) and full.startswith(prefix), 'gap is not a strict object-header prefix')
    span = selected[number]
    require(read_range(source, span['offset'], span['offset']+len(full)) == full, 'partial-header counterpart changed')
    return {'object': int(number), 'range': [begin, end], 'bytes': len(prefix),
            'sha256': hashlib.sha256(raw).hexdigest()}


def account_source(source, facts, left):
    begin, end = facts['body_range']
    start, page_ids = source_layout(source)
    require(begin == start and end == source.stat().st_size, 'source body range differs from table/EOF')
    selected = facts['selected']
    require(0 < len(selected) <= 1000000 and set(left) == {f'obj:{n} 0 R' for n in selected},
            'selected source identity set differs')
    streams = {item['offset']: item for item in facts['streams']}
    require(len(streams) == len(facts['streams']), 'duplicate stream extent entry')
    values, spans = {}, []
    for number, span in selected.items():
        at, finish = span['offset'], span['end']
        require(str(int(number)) == number and 0 < int(number) <= 1000000
                and begin <= at < finish <= end, 'selected object range/identity')
        stream = streams.get(at)
        record = left[f'obj:{number} 0 R']
        if stream is None:
            require(record['kind'] == 'value', 'source stream absent from selected framing')
            raw = read_range(source, at, finish)
            require(raw.endswith(b'endobj'), 'source metadata terminator')
            raw = raw[:-6]
        else:
            require(record['kind'] == 'stream' and stream['object'] == int(number)
                    and stream['end'] == finish, 'source stream identity/end')
            data_start, size = stream['data_start'], stream['bytes']
            raw = read_range(source, at, data_start)
            marker = re.search(rb'stream(?:\r\n|\r|\n)$', raw)
            require(marker, 'source stream opener')
            raw = raw[:marker.start()]
            require(data_start <= data_start+size < finish, 'source stream extent')
            tail = read_range(source, data_start+size, finish, cap=96)
            require(re.fullmatch(rb'[\x00\t\n\x0c\r ]{0,64}endstream[\x00\t\n\x0c\r ]+endobj', tail),
                    'source stream exact terminator')
            require(record['raw_bytes'] == size and record['raw_sha256'] == stream['sha256']
                    == range_hash(source, data_start, data_start+size), 'source raw extent/hash differs')
        header = re.match(number.encode()+rb' 0 obj\b', raw)
        require(header, 'source object header')
        value = SourceValueParser(raw[header.end():]).complete()
        if stream is not None:
            require(isinstance(value, dict) and value.get('/Type') not in ('/ObjStm', '/XRef'),
                    'opaque metadata stream prevents complete-reference proof')
        values[int(number)] = value
        spans.append((at, finish, 'selected'))
    for number, span in selected.items():
        if span['offset'] not in streams:
            continue
        item = streams[span['offset']]
        length = values[int(number)].get('/Length')
        if isinstance(length, Ref):
            require(length.number in values, 'missing source Length object')
            length = values[length.number]
        require(isinstance(length, Decimal) and length.as_tuple().exponent == 0
                and 0 <= length == item['bytes'], 'declared source Length differs from encoded extent')
    require(all(number in values and isinstance(values[number], dict)
                and values[number].get('/Type') == '/Page' for number in page_ids),
            'source table Page missing from complete selection')
    incoming = {}
    for owner, value in values.items():
        for target, path in source_references(value):
            incoming.setdefault(target, []).append((owner, path))
    stream_ids = {int(number) for number, span in selected.items() if span['offset'] in streams}
    for item in facts['duplicates']:
        span = selected[str(item['object'])]
        require(item['first_offset'] == span['offset'] and item['bytes'] == span['end']-span['offset'],
                'duplicate counterpart range differs')
        equal_ranges(source, item['duplicate_offset'], span['offset'], item['bytes'])
        spans.append((item['duplicate_offset'], item['duplicate_offset']+item['bytes'], 'duplicate'))
    require(set(streams) <= {span['offset'] for span in selected.values()} |
            {item['duplicate_offset'] for item in facts['duplicates']}, 'unaccounted stream extent entry')
    for item in facts['omitted']:
        span = selected[str(item['object'])]
        at, finish = item['offset'], item['apparent_next_header']
        size = finish-at-2
        require(len(f'{item["object"]} 0 obj') <= size < span['end']-span['offset']
                and read_range(source, finish-2, finish) == b'\r\n'
                and re.match(rb'[1-9][0-9]* 0 obj\b', read_range(source, finish, min(end, finish+128))),
                'unproved interrupted counterpart profile')
        equal_ranges(source, at, span['offset'], size)
        spans.append((at, finish, 'proper_prefix'))
    cursor = begin
    gaps = []
    for at, finish, kind in sorted(spans)+[(end, end, 'end')]:
        require(cursor <= at <= finish <= end, 'source accounting overlap/bound')
        if at > cursor:
            gap = partial_header(source, cursor, at, selected)
            if gap is not None:
                require(kind != 'end', 'unanchored trailing partial header')
                number = gap['object']
                value = values[number]
                if isinstance(value, dict) and value.get('/Type') == '/Page':
                    require(number in page_ids, 'partial Page header outside source table')
                    gap['role'] = 'source table Page'
                else:
                    edges = incoming.get(number, [])
                    require(isinstance(value, Decimal) and value.as_tuple().exponent == 0 and value >= 0
                            and edges and all(owner in stream_ids and path == ('/Length',) for owner, path in edges),
                            'partial scalar header is not exclusively a validated stream Length')
                    gap['role'] = 'validated indirect stream Length only'
                gaps.append(gap)
        cursor = finish
    return values, {'selected_objects': len(selected),
                    'selected_streams': sum(v['kind'] == 'stream' for v in left.values()),
                    'complete_duplicates': len(facts['duplicates']), 'proper_prefixes': len(facts['omitted']),
                    'partial_headers': gaps, 'unexplained_source_bytes': 0,
                    'opaque_metadata_streams': 0, 'body_range': [begin, end]}
