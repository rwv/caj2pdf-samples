# SPDX-License-Identifier: MIT
"""Verify unchanged selected objects plus independently checked CAJ navigation."""
from decimal import Decimal
import json
from pathlib import Path

from pdf_source_inventory import FILE_LIMIT, JSON_LIMIT, digest, value_hash
from pdf_source_graphs import Graph, changed_keys, differences, records, references, require
from caj_source_navigation import source_navigation, compare


def check_objects(source, candidate, left, right, navigation, *, catalog_properties=None):
    catalog_properties = {} if catalog_properties is None else catalog_properties
    missing, added, changed = differences(left, right)
    require(not missing, 'selected original object omitted')
    graph = Graph(candidate)
    result = compare(*navigation, candidate)
    pages, parents = graph.page_tree()
    outlines, _, _, outline_parents = graph.outlines()
    for wrapper in candidate.values():
        value = wrapper['value'] if 'value' in wrapper else wrapper['stream']['dict']
        for ref in references(value):
            require('obj:'+ref in candidate and candidate['obj:'+ref] != {'value': None},
                    'missing or null candidate indirect reference')
    for change in changed:
        identity = change['object']
        require(change['source']['kind'] == change['candidate']['kind'] == 'value',
                'unproved original stream/kind change: '+identity)
        a, b = source[identity]['value'], candidate[identity]['value']
        ref = identity.removeprefix('obj:')
        require(isinstance(a, dict) and isinstance(b, dict) and a.get('/Type') in ('/Page', '/Pages')
                and '/Parent' not in a and changed_keys(a, b) == {'/Parent'}
                and ref in parents and b['/Parent'] == parents[ref],
                'unproved original value change: '+identity)
    for identity in added:
        require(right[identity]['kind'] == 'value', 'added stream is not navigation framing')
        node = candidate[identity]['value']
        require(isinstance(node, dict), 'added scalar is not navigation framing')
        ref = identity.removeprefix('obj:')
        if identity == 'trailer':
            require(set(node) == {'/Root', '/Size'} and node['/Root'] == graph.root_ref
                    and type(node['/Size']) is int
                    and node['/Size'] == 1+max(int(k.split()[0][4:]) for k in right if k != 'trailer'),
                    'unmeasured generated trailer')
        elif ref == graph.root_ref:
            require(set(node) == {'/Type', '/Pages', '/Outlines'} | catalog_properties.keys(),
                    'unmeasured generated Catalog property')
            require(all(value_hash(node[key]) == value_hash(value)
                        for key, value in catalog_properties.items()), 'source Catalog property changed')
        elif ref in parents:
            require(node['/Type'] == '/Pages', 'added Page is not source-table content')
            if parents[ref] is None:
                require(set(node) == {'/Type', '/Count', '/Kids', '/MediaBox'}
                        and node['/MediaBox'] == [0, 0, 612, 792], 'unmeasured root fallback')
            else:
                require(set(node) == {'/Type', '/Count', '/Kids', '/Parent'},
                        'unmeasured intermediate Pages property')
        elif ref == graph.root['/Outlines']:
            require(set(node) == {'/Type', '/Count', '/First', '/Last'} and node['/Type'] == '/Outlines',
                    'unmeasured generated Outlines property')
        else:
            require(ref in outline_parents, 'added object is outside verified navigation')
            # compare() verifies all title/page/depth/Count and backlink fields,
            # and refuses every unmeasured outline property.
    result.update(selected_original_objects=len(left), selected_original_streams=sum(
        x['kind'] == 'stream' for x in left.values()), parent_insertions=len(changed),
        added_navigation_objects=len(added)-1, candidate_unresolved_references=0)
    return result


def load_inventory(directory, receipt):
    path = directory/'objects.json'
    require(path.stat().st_size <= JSON_LIMIT and digest(path) == receipt['json_sha256'],
            'metadata identity or size mismatch')
    require(receipt['exit'] in (0, 3) and digest(directory/'stderr.log') == receipt['warnings_sha256'],
            'reader failure or changed warning log')
    parsed = json.loads(path.read_text(), parse_float=Decimal)
    require(set(parsed) == {'qpdf'} and len(parsed['qpdf']) == 2, 'unexpected JSON envelope')
    header, objects = parsed['qpdf']
    require(header == receipt['header'] and header['jsonversion'] == 2
            and header['calledgetallpages'] is False and header['pushedinheritedpageresources'] is False,
            'reader changed page inheritance')
    require(len(objects) <= 1000000, 'object count bound')
    return objects, records(objects, directory)


def acquired_objects(row, *, reference_source=None):
    directory = Path(row['inventory_directory'])
    source, candidate = Path(row['source']), Path(row['pdf'])
    for path, expected in ((source, row['source_sha256']), (candidate, row['pdf_sha256'])):
        require(path.stat().st_size <= FILE_LIMIT and digest(path) == expected, 'source/output identity changed')
    reference = directory/'source-body-inventory.pdf'
    require(reference.stat().st_size == row['reference_bytes'] <= FILE_LIMIT
            and digest(reference) == row['reference_sha256'], 'reference identity changed')
    framing = row['reference_framing']
    source = source if reference_source is None else reference_source
    begin, end = framing['body_range']
    require(0 <= begin < end == source.stat().st_size, 'source body must retain complete tail')
    with source.open('rb') as original, reference.open('rb') as framed:
        require(framed.read(9) == b'%PDF-1.7\n', 'unexpected framing prefix')
        original.seek(begin)
        remaining = end-begin
        while remaining:
            chunk = original.read(min(65536, remaining))
            require(chunk and framed.read(len(chunk)) == chunk, 'reference body is not verbatim source')
            remaining -= len(chunk)
    a, left = load_inventory(directory/'source', row['source_reader'])
    b, right = load_inventory(directory/'candidate', row['candidate_reader'])
    catalog, tree, blank = (framing[k] for k in ('synthetic_catalog','synthetic_pages','synthetic_blank'))
    authored = {f'obj:{catalog} 0 R': {'/Type': '/Catalog', '/Pages': f'{tree} 0 R'},
                f'obj:{tree} 0 R': {'/Type': '/Pages', '/Count': 1, '/Kids': [f'{blank} 0 R']},
                f'obj:{blank} 0 R': {'/Type': '/Page', '/Parent': f'{tree} 0 R',
                                    '/MediaBox': [0, 0, 1, 1], '/Resources': {}},
                'trailer': {'/Size': framing['xref_size'], '/Root': f'{catalog} 0 R'}}
    require(row['excluded_source_synthetic_only'] == list(authored), 'unexpected source exclusion')
    for identity, value in authored.items():
        require(left.pop(identity) == {'kind': 'value', 'value_sha256': value_hash(value)},
                'source exclusion is not authored inventory framing')
    require(differences(left, right) == (row['missing'], row['added'], row['changed']),
            'acquired difference receipt changed')
    for label, inventory in [('source', left), ('candidate', right)]:
        require(len(inventory) == row[label+'_objects'] and sum(x['kind'] == 'stream' for x in inventory.values())
                == row[label+'_streams'], 'object/stream count changed')
    return a, b, left, right


def verify(row):
    a, b, left, right = acquired_objects(row)
    result = check_objects(a, b, left, right, source_navigation(Path(row['source'])))
    return {**result, 'status': 'VERIFIED_SELECTED_OBJECTS_AND_NAVIGATION',
            'source_reader_exit': row['source_reader']['exit'],
            'candidate_reader_exit': row['candidate_reader']['exit'],
            'scope': 'Complete acquired selected-object/raw-stream preservation, independently sourced page/outline navigation and explicitly checked generated framing; not a rendering oracle or proof that reader recovery found every original object.'}
