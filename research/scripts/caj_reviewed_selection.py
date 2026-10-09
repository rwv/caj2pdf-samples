# SPDX-License-Identifier: MIT
"""Recheck pinned source selections; previous omission/repair proofs stay scoped."""
import hashlib
import json
from pathlib import Path
import re
import tempfile

from pdf_source_inventory import FILE_LIMIT, JSON_LIMIT, digest
from caj_reviewed_framing import substitution_source
from caj_source_preservation import acquired_objects, check_objects
from caj_source_navigation import source_navigation
from pdf_source_graphs import require


REPORTS = {
    'interrupted-copies-20261008.json': ('2c75415cf15b0669abd3f7d4081786214a82721120191b787b4267286817abce', 'independent_original_framing', 'native_originals'),
    'indirect-length-replays-20261008.json': ('408611733278841a1a76cfd8e74842f9a58a0aa5d2e03b81171360114a976f5c', 'independent_original_framing', 'native_original'),
    'interrupted-metadata-parents-20261008.json': ('242e4e7c2a2a7f96a46b179339ad7e807cf56f8cef576b6bc6173ab363488684', 'original_framing', 'native'),
    'retained-catalog-20261008.json': ('d966fd88c1e90779bf765e5feea4d98edb2dbb63338c99a214e3fb6fd389e64d', 'original_framing', 'native'),
    'redundant-caj-framing-20261008.json': ('9fd62b07957116221982617bc0501fdcbf9de101a0c2f5163a8bad2cb2000f6b', 'independent_framing', 'original_native'),
    'stream-substitution-recovery-20261008.json': ('992e8bf0ed3dbf8e0c79e108a0574f095e906b66f7d4a12fd9c7fb72f76fa1ac', 'independent_diagnostic_framing', 'original_native'),
}


def range_hash(source, begin, end):
    require(0 <= begin < end <= source.stat().st_size <= FILE_LIMIT, 'hash range bound')
    result = hashlib.sha256()
    with source.open('rb') as stream:
        stream.seek(begin)
        while begin < end:
            block = stream.read(min(65536, end-begin))
            require(block, 'truncated source hash range')
            result.update(block)
            begin += len(block)
    return result.hexdigest()


def check_xref(reference, framing, selected):
    """Check all generated slots, without asking recovery to select anything."""
    begin, end = framing['body_range']
    size = framing['xref_size']
    require(type(size) is int and 1 < size <= 1000001, 'xref count bound')
    expected = {int(n): entry['offset']-begin+9 for n, entry in selected.items()}
    authored = {framing[key] for key in ('synthetic_catalog', 'synthetic_pages', 'synthetic_blank')}
    require(len(authored) == 3 and not authored & expected.keys(), 'framing identity collision')
    with reference.open('rb') as stream:
        stream.seek(max(0, reference.stat().st_size-256))
        match = re.search(rb'startxref\n([0-9]+)\n%%EOF\n\Z', stream.read(256))
        require(match, 'missing final generated startxref')
        at = int(match[1])
        require(end-begin+9 <= at < reference.stat().st_size, 'xref location bound')
        stream.seek(at)
        require(stream.readline(32) == b'xref\n'
                and stream.readline(32) == f'0 {size}\n'.encode()
                and stream.readline(32) == b'0000000000 65535 f \n', 'xref header changed')
        seen = set()
        for number in range(1, size):
            line = stream.readline(32)
            if number in expected:
                require(line == f'{expected[number]:010d} 00000 n \n'.encode(), 'selected source offset changed')
                seen.add(number)
            elif number in authored:
                entry = re.fullmatch(rb'([0-9]{10}) 00000 n \n', line)
                require(entry and end-begin+9 <= int(entry[1]) < at, 'authored object offset changed')
                seen.add(number)
            else:
                require(line == b'0000000000 00000 f \n', 'unreviewed source selection')
        require(seen == expected.keys() | authored, 'selected identity outside xref')
        tail = (f'trailer\n<< /Size {size} /Root {framing["synthetic_catalog"]} 0 R >>\n'
                f'startxref\n{at}\n%%EOF\n').encode()
        require(stream.read(256) == tail, 'generated trailer differs')


def check_selection(source, reference, framing, facts, left):
    begin, prior_end = facts['body_range']
    require(framing['body_range'] == [begin, source.stat().st_size]
            and framing['reviewed_body_end'] == prior_end, 'reviewed framing range changed')
    selected = facts.get('selected', facts.get('objects'))
    require(isinstance(selected, dict) and 0 < len(selected) < 1000000, 'selection count bound')
    require(set(left) == {f'obj:{n} 0 R' for n in selected}, 'selected object set changed')
    with source.open('rb') as stream:
        for number, span in selected.items():
            require(0 < int(number) <= 1000000 and begin <= span['offset'] < span['end'] <= prior_end,
                    'reviewed object range changed')
            stream.seek(span['offset'])
            require(re.match(number.encode()+rb'[\x00\t\n\x0c\r ]+0[\x00\t\n\x0c\r ]+obj\b',
                             stream.read(128)), 'reviewed header changed')
            if 'sha256' in span:
                require(range_hash(source, span['offset'], span['end']) == span['sha256'],
                        'reviewed original span changed')
    streams = {}
    for item in facts['streams']:
        number = str(item['object'])
        if number in selected and item['offset'] == selected[number]['offset']:
            streams[number] = item
    require(set(streams) == {key[4:].split()[0] for key, val in left.items() if val['kind'] == 'stream'},
            'reviewed stream membership changed')
    for number, item in streams.items():
        if 'bytes' not in item:
            # The 13-site recovery report uses codec-specific extents. Its
            # selected complete-object hashes were verified above instead.
            require('sha256' in selected[number], 'unproved stream range')
            continue
        start, count = item['data_start'], item['bytes']
        require(selected[number]['offset'] <= start < start+count <= selected[number]['end'],
                'reviewed stream extent bound')
        record = left[f'obj:{number} 0 R']
        require(record['raw_bytes'] == count and record['raw_sha256'] == item['sha256']
                and range_hash(source, start, start+count) == item['sha256'], 'reviewed raw stream changed')
    check_xref(reference, framing, selected)


def retained_catalog(source, facts, objects):
    require(set(facts['excluded_originals']) == {'12', '16'}, 'unexpected catalog exclusions')
    span = facts['excluded_originals']['16']
    expected = (b'16 0 obj<</Pages 12 0 R/Type/Catalog/PageLabels 10 0 R'
                b'/AcroForm 434 0 R/Metadata 450 0 R>>\rendobj')
    require(span['end']-span['offset'] == len(expected), 'catalog range changed')
    with source.open('rb') as stream:
        stream.seek(span['offset'])
        require(stream.read(len(expected)) == expected, 'source catalog fields changed')
    require(objects['obj:10 0 R'] == {'value': {'/Nums': [0, '11 0 R']}}
            and objects['obj:11 0 R'] == {'value': {'/S': '/D'}}, 'source label range changed')
    return {'/PageLabels': '10 0 R'}


def verify(row):
    proof = row['prior_proof']
    path = Path(proof['file'])
    require(path.name in REPORTS and path.stat().st_size <= JSON_LIMIT, 'unknown or oversized prior proof')
    report_hash, framing_key, native_key = REPORTS[path.name]
    require(digest(path) == proof['sha256'] == report_hash and proof['framing_key'] == framing_key,
            'prior reviewed proof changed')
    report = json.loads(path.read_text())
    native = report[native_key]
    if 'cases' in native:
        native = next(x for x in native['cases'] if x['source_sha256'] == row['source_sha256'])
    require(native['source_sha256'] == row['source_sha256'] and native['source_unchanged'] is True
            and native.get('output_sha256', native.get('pdf_sha256')) == row['pdf_sha256'],
            'reviewed original/output pair changed')
    frames = report[framing_key]
    facts = next(x for x in frames if x['source_sha256'] == row['source_sha256']) if isinstance(frames, list) else frames
    source = Path(row['source'])
    reconstructed = framing_key == 'independent_diagnostic_framing'
    with tempfile.TemporaryDirectory(prefix='caj-reviewed-source-') as temp:
        if reconstructed:
            original = source
            source = Path(temp)/'diagnostic.caj'
            substitution_source(original, source, report['candidate_evidence']['source_constraints'])
        require(digest(source) == facts['source_sha256'] == proof['source_sha256'], 'reviewed source changed')
        a, b, left, right = acquired_objects(row, reference_source=source)
        require(row['source_reader']['exit'] == 0, 'fresh selection has unresolved reader warning')
        check_selection(source, Path(row['inventory_directory'])/'source-body-inventory.pdf',
                        row['reference_framing'], facts, left)
        props = retained_catalog(source, facts, a) if path.name == 'retained-catalog-20261008.json' else {}
        result = check_objects(a, b, left, right, source_navigation(Path(row['source'])), catalog_properties=props)
    return {**result, 'status': 'VERIFIED_WITH_REVIEWED_SOURCE_PROFILE',
            'prior_report': path.name, 'prior_report_sha256': report_hash,
            'prior_selection_scope': facts['scope'], 'source_body_reconstructed': reconstructed,
            'scope': 'Fresh selected-object/raw-stream and navigation comparison using reviewed source offsets; prior omission/repair proof and rendering limits are inherited for identical source/output bytes. No fresh rendering or intact-alternative claim.'}
