# SPDX-License-Identifier: MIT
"""Independent CAJ table/outline checks; no stream preservation verdict."""
import struct
from pdf_source_inventory import value_hash
from pdf_source_graphs import Graph, require


def source_navigation(path):
    size = path.stat().st_size
    with path.open('rb') as stream:
        header = stream.read(0x114)
        require(len(header) == 0x114 and header[:4] == b'CAJ\0', 'CAJ navigation header')
        pages, table = struct.unpack_from('<II', header, 16)
        count, = struct.unpack_from('<I', header, 0x110)
        require(0 < pages <= 100000 and count <= 100000 and
                0x114+308*count <= table <= size-12*pages, 'CAJ navigation bounds')
        outlines = []
        prior_level = 0
        for _ in range(count):
            record = stream.read(308)
            # These are bounded NUL-terminated fields. Initial ten-file
            # observations of zero-filled suffixes were not a format rule;
            # four expanded originals retain nonzero bytes after terminators.
            title, separator, _ = record[:256].partition(b'\0')
            require(separator and title, 'invalid bounded outline title')
            destination, separator, _ = record[280:292].partition(b'\0')
            require(separator and destination.isdigit(), 'invalid outline page field')
            page = int(destination)
            level, = struct.unpack_from('<i', record, 304)
            require(1 <= page <= pages and 1 <= level <= prior_level+1, 'outline page/depth')
            outlines.append((title.decode('gb18030', errors='strict'), page, level))
            prior_level = level
        stream.seek(table)
        page_ids = []
        for _ in range(pages):
            start, length, identity = struct.unpack('<III', stream.read(12))
            require(table+12*pages <= start <= start+length <= size and identity > 0, 'page table bounds')
            page_ids.append(str(identity)+' 0 R')
        require(len(set(page_ids)) == len(page_ids), 'repeated table page identity')
    return page_ids, outlines


def compare(page_ids, expected_outlines, objects):
    graph = Graph(objects)
    pages, parents = graph.page_tree()
    require(pages == page_ids, 'source table page order differs')
    for ref, parent in parents.items():
        require(graph.dictionary(ref).get('/Parent') == parent, 'page parent disagrees with Kids')
    ordered, previous, last, outline_parents = graph.outlines()
    require(len(ordered) == len(expected_outlines), 'source outline count differs')
    levels = {graph.root['/Outlines']: 0}
    descendants = {ref: 0 for ref in last}
    for (ref, parent), (title, page, level) in zip(ordered, expected_outlines):
        node = graph.dictionary(ref)
        levels[ref] = levels[parent]+1
        require(levels[ref] == level and node['/Title'] == 'u:'+title
                and node['/Dest'] == [page_ids[page-1], '/XYZ', None, None, None],
                'source outline title/page/hierarchy differs')
        require(node.get('/Parent') == parent and node.get('/Prev') == previous[ref]
                and node.get('/Last') == last[ref], 'incorrect outline backlink/last child')
        require(set(node) <= {'/Title', '/Dest', '/Parent', '/Prev', '/Next', '/First', '/Last', '/Count'},
                'unmeasured generated outline property')
    for ref, parent in reversed(ordered):
        descendants[parent] += 1+descendants[ref]
    for ref, count in descendants.items():
        require(graph.dictionary(ref).get('/Count', 0) == count, 'outline descendant Count mismatch')
        require(graph.dictionary(ref).get('/Last') == last[ref], 'outline root Last mismatch')
    return {'pages': len(pages), 'outline_nodes': len(ordered),
            'source_navigation_sha256': value_hash([page_ids, [list(x) for x in expected_outlines]])}
