# SPDX-License-Identifier: MIT
"""Re-acquire selected originals from previously reviewed independent offsets.

No candidate object/byte selects a source offset. Previously measured omissions,
prefix proofs and rendering limits stay in the pinned source report.
"""
import mmap
import re

from pdf_source_inventory import FILE_LIMIT, digest
from pdf_source_graphs import require

def copy_bytes(source, target, count):
    while count:
        block = source.read(min(65536, count))
        require(block, 'truncated original range')
        target.write(block)
        count -= len(block)


def substitution_source(source, target, facts):
    require(digest(source) == facts['original_sha256'], 'substitution original identity')
    old, new = bytes.fromhex(facts['from_hex']), bytes.fromhex(facts['to_hex'])
    require(old == bytes.fromhex('caa7c2e4') and new == bytes.fromhex('b5f4')
            and len(facts['occurrences']) == 13, 'unmeasured substitution profile')
    with source.open('rb') as src, target.open('xb') as dst:
        for occurrence in facts['occurrences']:
            count = occurrence['source_offset']-src.tell()
            require(count >= 0, 'overlapping substitutions')
            copy_bytes(src, dst, count)
            require(src.read(len(old)) == old, 'substitution site changed')
            dst.write(new)
        copy_bytes(src, dst, source.stat().st_size-src.tell())
    require(target.stat().st_size == facts['candidate_bytes'] and digest(target) == facts['candidate_sha256'],
            'reconstructed diagnostic differs from reviewed source')


def frame_selected(source, target, facts):
    begin, prior_end = facts['body_range']
    end = source.stat().st_size
    require(0 <= begin < prior_end <= end <= FILE_LIMIT, 'source bounds')
    selected = facts.get('selected', facts.get('objects'))
    require(isinstance(selected, dict) and 0 < len(selected) < 1000000, 'selection bound')
    offsets = {}
    with source.open('rb') as src:
        for key, span in selected.items():
            number, at = int(key), span['offset']
            require(0 < number <= 1000000 and begin <= at < span['end'] <= prior_end,
                    'selected original span bound')
            src.seek(at)
            require(re.match(str(number).encode()+rb'[\x00\t\n\x0c\r ]+0[\x00\t\n\x0c\r ]+obj\b', src.read(128)),
                    'selected offset is not its original object header')
            offsets[number] = at-begin+9
        ids = []
        with mmap.mmap(src.fileno(), 0, access=mmap.ACCESS_READ) as data:
            for n in [n for start in (32,1000,10000,100000) for n in range(start,start+32)]:
                if data.find(str(n).encode(), begin, end) < 0:
                    ids.append(n)
                    if len(ids) == 3:
                        break
        require(len(ids) == 3, 'fresh framing identity bound')
        catalog, tree, blank = ids
        authored = {
            catalog: f'<< /Type /Catalog /Pages {tree} 0 R >>',
            tree: f'<< /Type /Pages /Count 1 /Kids [{blank} 0 R] >>',
            blank: f'<< /Type /Page /Parent {tree} 0 R /MediaBox [0 0 1 1] /Resources << >> >>',
        }
        with target.open('xb') as dst:
            dst.write(b'%PDF-1.7\n')
            src.seek(begin)
            copy_bytes(src, dst, end-begin)
            dst.write(b'\n')
            for n, value in authored.items():
                offsets[n] = dst.tell()
                dst.write(f'{n} 0 obj\n{value}\nendobj\n'.encode())
            maximum = max(offsets)
            require(dst.tell()+20*(maximum+1)+256 <= FILE_LIMIT, 'reference size bound')
            at = dst.tell()
            dst.write(f'xref\n0 {maximum+1}\n0000000000 65535 f \n'.encode())
            for n in range(1,maximum+1):
                dst.write(f'{offsets[n]:010d} 00000 n \n'.encode() if n in offsets else b'0000000000 00000 f \n')
            dst.write(f'trailer\n<< /Size {maximum+1} /Root {catalog} 0 R >>\nstartxref\n{at}\n%%EOF\n'.encode())
    return {'body_range': [begin,end], 'reviewed_body_end': prior_end,
            'synthetic_catalog': catalog, 'synthetic_pages': tree, 'synthetic_blank': blank,
            'xref_size': maximum+1, 'selected_original_objects': len(selected)}
