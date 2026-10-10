#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Fail-closed interpretation of original unique-code controls, not real pages.

FT_LOAD_RENDER selects candidates, not proof of document use. Each measured
candidate must have its same-thread/face outer cmap immediately before it.
Nested lookups and loads remain counted, but cannot supply that mapping.
The entire five-size sequence, reverse order and isolated controls
are additional protocol requirements. Cached/repeated real text is not covered.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

MAX_EVENTS = 100000
FAMILIES = {0: 'HGBZ_CNKI', 4: 'HGHZ_CNKI', 3: 'HGBX_CNKI',
            28: 'HGB1_CNKI', 31: 'HGB1X_CNKI'}
SIZES = (5, 6, 9, 19, 20)


def analyze(path, codes, family):
    if (not 1 <= len(codes) <= 62 or len(set(codes)) != len(codes)
            or any(not re.fullmatch('[a-f0-9]{4}', code) for code in codes)
            or family not in (*FAMILIES.values(), 'HGHT_CNKI')):
        raise ValueError('unmeasured control codes or family')
    if path.with_name('ft-limit').exists() or not 0 < path.stat().st_size <= 64 * 1024 * 1024:
        raise ValueError('trace limit or empty trace')
    previous, groups, operations = {}, defaultdict(list), Counter()
    nested_events = 0
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for count, line in enumerate(stream, 1):
            digest.update(line)
            if count > MAX_EVENTS or len(line) > 512 or not line.endswith(b'\n'):
                raise ValueError('trace record limit or truncation')
            fields = line.decode('ascii').rstrip('\n').split('\t')
            if len(fields) != 13:
                raise ValueError('trace field count')
            event, clock, pid, tid = map(int, fields[:4])
            op, face, name = fields[4:7]
            a, b, error, x, y, depth = map(int, fields[7:])
            if (event != count - 1 or not 0 <= clock < 2**63
                    or not 0 < pid < 2**31 or not 0 < tid < 2**31
                    or not re.fullmatch('0x[0-9a-f]+', face) or name != family
                    or op not in ('cmap', 'load') or error != 0
                    or not 0 <= a < 2**32 or not 0 <= b < 2**31
                    or not 0 <= x <= 65535 or not 0 <= y <= 65535
                    or not 0 <= depth <= 32):
                raise ValueError('unmeasured event or FreeType error')
            operations[(op, b if op == 'load' else None)] += 1
            if depth:
                nested_events += 1
                continue
            key = (pid, tid, face)
            recent = previous.get(key)
            current = (op, a, b, x, y)
            if op == 'load' and b & 4:
                if (x != y or x not in SIZES or not a or recent is None
                        or recent[0] != 'cmap' or recent[2] != a
                        or recent[3:] != (x, y)):
                    raise ValueError('unpaired or ambiguous render load')
                groups[x].append((recent[1], a))
            previous[key] = current
    if set(groups) != set(SIZES) or any(len(v) != len(codes) for v in groups.values()):
        raise ValueError('missing or extra control glyph/size')
    reference = groups[SIZES[0]]
    if any(v != reference for v in groups.values()):
        raise ValueError('glyph sequence changes across sizes')
    return {'trace_sha256': digest.hexdigest(), 'events': count, 'family': family,
            'sizes': list(SIZES), 'render_loads': len(codes) * len(SIZES),
            'nested_events': nested_events,
            'operations': [{'operation': op, 'flags': flags, 'count': n}
                           for (op, flags), n in sorted(operations.items())],
            'mappings': [{'native_code': code, 'cmap_argument': alias, 'glyph_id': gid}
                         for code, (alias, gid) in zip(codes, reference)]}


def agree(observations):
    """Compare explicit measured slots; never extrapolate a mapping formula."""
    mappings = {}
    for observation in observations:
        for row in observation['mappings']:
            key = (observation['family'], row['native_code'])
            value = (row['cmap_argument'], row['glyph_id'])
            if key in mappings and mappings[key] != value:
                raise ValueError('reordered/isolated mapping disagreement')
            mappings[key] = value
    return len(mappings)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument('--codes', required=True, nargs='+')
    parser.add_argument('--family', required=True, choices=(*FAMILIES.values(), 'HGHT_CNKI'))
    args = parser.parse_args()
    print(json.dumps(analyze(args.trace, args.codes, args.family), indent=2))
