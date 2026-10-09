# SPDX-License-Identifier: MIT
"""Validate each measured PDF/KDH change; no content is taken from the candidate."""
from decimal import Decimal
import json
from pathlib import Path
import re

from pdf_source_inventory import FILE_LIMIT, JSON_LIMIT, canonical, digest, value_hash

REF = re.compile(r'[1-9][0-9]* [0-9]+ R')
EMPTY_FORM_SOURCE = 'ece0be828c95350ed2d48c83fb8a5255f13c935d91da5c7c99448ffec99287a9'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def equal(a, b):
    return canonical(a) == canonical(b)


class Graph:
    def __init__(self, objects):
        self.objects = objects
        self.trailer = objects['trailer']['value']
        self.root_ref = self.trailer['/Root']
        self.root = self.dictionary(self.root_ref)
        require(self.root['/Type'] == '/Catalog', 'missing source/candidate Catalog')

    def resolve(self, value):
        seen = set()
        while isinstance(value, str) and REF.fullmatch(value):
            require(value not in seen and len(seen) < 16, 'recursive/long scalar reference')
            seen.add(value)
            wrapper = self.objects['obj:'+value]
            require(set(wrapper) == {'value'}, 'stream used as metadata container')
            value = wrapper['value']
        return value

    def dictionary(self, value):
        value = self.resolve(value)
        require(isinstance(value, dict), 'expected dictionary')
        return value

    def page_tree(self):
        parents, leaves = {}, []

        def walk(ref, parent, depth):
            require(isinstance(ref, str) and REF.fullmatch(ref), 'direct/invalid Page tree child')
            require(ref not in parents and depth <= 128 and len(parents) < 100000, 'Page tree cycle/limit')
            parents[ref] = parent
            node = self.dictionary(ref)
            kind = node['/Type']
            require(kind in ('/Page', '/Pages'), 'unknown Page tree type')
            if kind == '/Page':
                leaves.append(ref)
                return 1
            kids = self.resolve(node['/Kids'])
            require(isinstance(kids, list), 'non-array Kids')
            count = sum(walk(child, ref, depth+1) for child in kids)
            require(type(node['/Count']) is int and node['/Count'] == count, 'source/candidate Count mismatch')
            return count

        walk(self.root['/Pages'], None, 0)
        return leaves, parents

    def outlines(self):
        root = self.root.get('/Outlines')
        if root is None:
            return [], {}, {}, {}
        require(isinstance(root, str) and REF.fullmatch(root), 'direct/invalid Outlines root')
        ordered, previous, last, parents = [], {}, {}, {}
        active = {root}

        def children(parent, depth):
            require(depth <= 128, 'outline depth bound')
            current = self.dictionary(parent).get('/First')
            prior = None
            while current is not None:
                require(isinstance(current, str) and REF.fullmatch(current), 'invalid outline edge')
                require(current not in active and len(active) < 100000, 'outline cycle/shared node/limit')
                active.add(current)
                node = self.dictionary(current)
                ordered.append((current, parent))
                parents[current] = parent
                previous[current] = prior
                children(current, depth+1)
                prior = current
                current = node.get('/Next')
            last[parent] = prior

        children(root, 0)
        return ordered, previous, last, parents


def changed_keys(a, b):
    return {key for key in a.keys() | b.keys() if key not in a or key not in b or not equal(a[key], b[key])}


def latest_startxref(path):
    with path.open('rb') as stream:
        stream.seek(max(0, path.stat().st_size-65536))
        tail = stream.read(65536)
    matches = list(re.finditer(rb'startxref[\x00\t\n\x0c\r ]+([0-9]+)[\x00\t\n\x0c\r ]+%%EOF', tail))
    require(matches, 'no bounded original startxref')
    return int(matches[-1][1])


def trailer_changes(source, candidate, reference):
    a, b = source.trailer, candidate.trailer
    keys = changed_keys(a, b)
    structural = {'/Type', '/W', '/Index', '/Length', '/Filter', '/DecodeParms'}
    removed = {key for key in keys if key not in b}
    require(not removed or (a.get('/Type') == '/XRef' and removed <= structural),
            'non-xref trailer field removal')
    require(keys-removed <= {'/ID', '/Prev'}, 'unclassified trailer change')
    if '/ID' in keys:
        require(isinstance(a['/ID'], list) and isinstance(b['/ID'], list)
                and len(a['/ID']) == len(b['/ID']) == 2 and equal(a['/ID'][0], b['/ID'][0]),
                'first document ID changed')
        require(isinstance(b['/ID'][1], str) and re.fullmatch(r'b:[0-9a-fA-F]{32}', b['/ID'][1]),
                'unmeasured updated document identifier')
    if '/Prev' in keys:
        require(type(b['/Prev']) is int and b['/Prev'] == latest_startxref(reference),
                'incremental Prev does not point at original latest xref')
    return sorted(keys)


def equivalent_opacity(a, b, source, candidate):
    require(isinstance(a, dict) and isinstance(b, dict), 'non-direct Page resources')
    require(changed_keys(a, b) == {'/ExtGState'}, 'non-opacity resource change')
    left, right = a['/ExtGState'], b['/ExtGState']
    require(isinstance(left, dict) and isinstance(right, dict) and changed_keys(left, right) == {'/GSP1'},
            'unmeasured opacity resource name')
    x, y = source.dictionary(left['/GSP1']), candidate.dictionary(right['/GSP1'])
    require(set(x) == set(y) == {'/CA', '/ca'}, 'non-alpha ExtGState property')
    for key in x:
        require(type(x[key]) in (int, Decimal) and type(y[key]) in (int, Decimal)
                and 0 <= x[key] <= 1 and x[key] == y[key], 'non-equivalent alpha')


def references(value, depth=0):
    require(depth <= 128, 'metadata nesting bound')
    if isinstance(value, str) and REF.fullmatch(value):
        yield value
    elif isinstance(value, (dict, list)):
        for child in value.values() if isinstance(value, dict) else value:
            yield from references(child, depth+1)


def records(objects, directory):
    result = {}
    for identity, wrapper in objects.items():
        require(identity == 'trailer' or (identity.startswith('obj:') and REF.fullmatch(identity[4:])),
                'invalid object identity')
        if set(wrapper) == {'value'}:
            result[identity] = {'kind': 'value', 'value_sha256': value_hash(wrapper['value'])}
        else:
            require(set(wrapper) == {'stream'}, 'unexpected object envelope')
            stream = wrapper['stream']
            require(set(stream) == {'dict', 'datafile'} and isinstance(stream['dict'], dict),
                    'unexpected stream envelope')
            path = Path(stream['datafile'])
            require(path.parent == directory and path.name.startswith('raw-')
                    and not path.is_symlink() and path.stat().st_size <= FILE_LIMIT,
                    'stream artifact path/size')
            result[identity] = {'kind': 'stream', 'value_sha256': value_hash(stream['dict']),
                                'raw_sha256': digest(path), 'raw_bytes': path.stat().st_size}
    return result


def differences(left, right):
    return (sorted(left.keys()-right.keys()), sorted(right.keys()-left.keys()),
            [{'object': identity, 'source': left[identity], 'candidate': right[identity]}
             for identity in sorted(left.keys() & right.keys()) if left[identity] != right[identity]])


def verify_graphs(row, metadata, reference):
    source, candidate = map(Graph, metadata)
    for objects in metadata:
        for wrapper in objects.values():
            value = wrapper.get('value') if 'value' in wrapper else wrapper['stream']['dict']
            for ref in references(value):
                require('obj:'+ref in objects and objects['obj:'+ref] != {'value': None},
                        'missing or null indirect reference')
    pages, page_parents = source.page_tree()
    final_pages, final_parents = candidate.page_tree()
    require(pages == final_pages and len(pages) == row['pages'] and page_parents == final_parents,
            'Page tree/order changed')
    for ref, expected in final_parents.items():
        require(candidate.dictionary(ref).get('/Parent') == expected, 'candidate Page parent disagrees with Kids')
    outlines, previous, last, outline_parents = source.outlines()
    final_outlines, final_previous, final_last, final_outline_parents = candidate.outlines()
    require((outlines, previous, last, outline_parents) ==
            (final_outlines, final_previous, final_last, final_outline_parents), 'forward outline hierarchy changed')
    for ref, expected in previous.items():
        require(candidate.dictionary(ref).get('/Prev') == expected, 'candidate outline Prev is not prior sibling')
    for ref, expected in last.items():
        require(candidate.dictionary(ref).get('/Last') == expected, 'candidate outline Last is not last child')
    for ref, expected in outline_parents.items():
        require(candidate.dictionary(ref).get('/Parent') == expected, 'candidate outline Parent is not traversed parent')
    require(not row['missing'] and not row['added'], 'added or missing original object')
    events = []
    for change in row['changed']:
        identity = change['object']
        if identity == 'trailer':
            events.append({'object': identity, 'proof': 'xref-only trailer fields and incremental identity',
                           'fields': trailer_changes(source, candidate, reference)})
            continue
        if change['source'].get('raw_sha256') != change['candidate'].get('raw_sha256'):
            require(row['source_sha256'] == EMPTY_FORM_SOURCE and identity == 'obj:485 0 R'
                    and row['pdf_sha256'] == '6c32efe1fc0abf3b9f7f4737428b73dc3e0a82f2973ae6ac147564cf6300b2aa'
                    and change['source']['raw_bytes'] == 112 and change['candidate']['raw_bytes'] == 0
                    and change['source']['raw_sha256'] == '9991ded5751c13b6b223a8662aec00d29410f2364e3a526d7570ede97a760fdc'
                    and change['candidate']['raw_sha256'] == 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
                    and change['source']['value_sha256'] == change['candidate']['value_sha256']
                    == '3e4ff51f49baed6eba56cd3f837eab78ab5b62a0d9c46dbb8bc0d73524f96a41',
                    'unclassified raw stream change')
            events.append({'object': identity, 'proof': 'Existing exact-source indexed empty-Form proof, Rust#446/447',
                           'evidence': 'research/notes/indexed-empty-form-20261008.json'})
            continue
        require(change['source']['kind'] == change['candidate']['kind'] == 'value', 'unclassified stream dictionary change')
        ref = identity.removeprefix('obj:')
        a, b = source.dictionary(ref), candidate.dictionary(ref)
        keys = changed_keys(a, b)
        for key in keys:
            if key == '/Prev':
                require(ref in previous and b[key] == previous[ref] and previous[ref] is not None,
                        'Prev change is not an established outline backlink')
            elif key == '/Last':
                require(ref in last and b[key] == last[ref] and last[ref] is not None,
                        'Last change is not an established outline last child')
            elif key == '/Parent':
                require(ref in page_parents and a['/Type'] == '/Page' and b[key] == page_parents[ref],
                        'Parent change is not a validated Page edge')
            elif key == '/Resources':
                require(ref in pages, 'non-Page resource repair')
                equivalent_opacity(a[key], b[key], source, candidate)
            else:
                raise ValueError('unclassified object field '+key)
        events.append({'object': identity, 'proof': 'validated forward tree or exactly equivalent opacity',
                       'fields': sorted(keys)})
    return {'source_sha256': row['source_sha256'], 'pdf_sha256': row['pdf_sha256'], 'format': row['format'],
            'pages': len(pages), 'outline_nodes': len(outlines), 'page_tree_nodes': len(page_parents),
            'source_streams': row['source_streams'], 'source_objects': row['source_objects'],
            'status': 'VERIFIED_SCOPED_PRESERVATION', 'events': events,
            'source_reader_exit': row['source_reader']['exit'], 'candidate_reader_exit': row['candidate_reader']['exit'],
            'unresolved_references': 0,
            'scope': 'Selected object values/raw streams, page tree and forward outlines with individually proved changes; not a new rendering oracle.'}


def verify(row, directory=None):
    directory = Path(row['inventory_directory']) if directory is None else directory
    require(row['format'] in ('PDF', 'KDH'), 'unsupported proof family')
    metadata, inventories = [], []
    for label, receipt in [('source', row['source_reader']), ('candidate', row['candidate_reader'])]:
        path = directory/label/'objects.json'
        require(path.stat().st_size <= JSON_LIMIT and digest(path) == receipt['json_sha256'],
                'metadata receipt changed or size bound')
        require(receipt['exit'] in (0, 3), 'reader acquisition failure')
        require(digest(directory/label/'stderr.log') == receipt['warnings_sha256'],
                'reader warning receipt changed')
        parsed = json.loads(path.read_text(), parse_float=Decimal)
        require(set(parsed) == {'qpdf'} and len(parsed['qpdf']) == 2, 'unexpected JSON envelope')
        header, objects = parsed['qpdf']
        require(header == receipt['header'] and header['jsonversion'] == 2
                and header['calledgetallpages'] is False and header['pushedinheritedpageresources'] is False,
                'reader mutated page inheritance')
        require(len(objects) <= 1_000_000, 'object count bound')
        inventory = records(objects, directory/label)
        require(len(inventory) == row[label+'_objects']
                and sum(x['kind'] == 'stream' for x in inventory.values()) == row[label+'_streams'],
                'object/stream count receipt mismatch')
        metadata.append(objects)
        inventories.append(inventory)
    require(differences(*inventories) == (row['missing'], row['added'], row['changed']),
            'difference receipt mismatch')
    reference = directory/'decoded-full-tail.pdf' if row['format'] == 'KDH' else Path(row['source'])
    require(reference.stat().st_size == row['reference_bytes'] <= FILE_LIMIT
            and digest(reference) == row['reference_sha256'], 'source reference changed')
    for key, expected in [('source', row['source_sha256']), ('pdf', row['pdf_sha256'])]:
        path = Path(row[key])
        require(path.stat().st_size <= FILE_LIMIT and digest(path) == expected, 'source/output identity changed')
    if row['format'] == 'KDH':
        check_kdh_reference(Path(row['source']), reference)
    return verify_graphs(row, metadata, reference)


def check_kdh_reference(source, reference):
    with source.open('rb') as original, reference.open('rb') as decoded:
        require(original.read(32) == b'KDH 2.00 Copyright(C) 2000 CAJCD', 'KDH signature changed')
        original.seek(254)
        offset = 0
        while block := original.read(65536):
            expected = bytes(value ^ b'FZHMEI'[(offset+i) % 6] for i, value in enumerate(block))
            require(decoded.read(len(expected)) == expected, 'KDH reference is not unchanged decoded source')
            offset += len(block)
        require(decoded.read(1) == b'', 'extra decoded source tail')
