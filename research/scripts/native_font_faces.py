#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Bind observed glyph API events to hash-pinned public face-constructor inputs.

This identifies resources for observed calls, not document characters, cached
draws, glyph shapes or source/PDF fidelity. No call is synthesized for a cache
hit. Successful constructors/references/disposals define observed lifetimes.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re


def require(value, message):
    if not value:
        raise ValueError(message)


def read_trace(path, marker, maximum_events, maximum_line):
    require(not path.with_name(marker).exists(), 'observer event limit')
    require(0 < path.stat().st_size <= 64 * 1024 * 1024, 'trace byte limit or empty trace')
    rows, counters, digest = [], defaultdict(set), hashlib.sha256()
    with path.open('rb') as stream:
        for line in stream:
            require(len(rows) < maximum_events and len(line) <= maximum_line and line.endswith(b'\n'),
                    'trace record limit or truncation')
            digest.update(line)
            fields = line.decode('ascii').rstrip('\n').split('\t')
            require(len(fields) == 13, 'trace field count')
            event, clock, pid, tid = map(int, fields[:4])
            require(0 <= event < maximum_events and 0 < clock < 2**63
                    and 0 < pid < 2**31 and 0 < tid < 2**31, 'event identity range')
            require(re.fullmatch('0x[0-9a-f]+', fields[5]) and int(fields[5], 16) > 0
                    and re.fullmatch('[ -~]{1,80}', fields[6]) and '_CNKI' in fields[6],
                    'face identity or family')
            require(event not in counters[pid], 'duplicate event number')
            counters[pid].add(event)
            rows.append((clock, pid, tid, fields))
    for values in counters.values():
        require(values == set(range(len(values))), 'missing process event numbers')
    return rows, digest.hexdigest()


def bind(face_trace, glyph_trace, resources):
    require(1 <= len(resources) <= 84, 'resource inventory limit')
    known = {}
    for resource in resources:
        sha = resource['sha256']
        require(re.fullmatch('[0-9a-f]{64}', sha) and sha not in known
                and resource['freetype_error'] == 0 and resource['face_index'] == 0
                and resource['num_faces'] == 1 and 0 < resource['num_glyphs'] <= 65535
                and 0 < resource['bytes'] <= 32 * 1024 * 1024, 'unmeasured resource inventory')
        known[sha] = resource
    faces, face_sha = read_trace(face_trace, 'ft-face-limit', 10000, 1536)
    glyphs, glyph_sha = read_trace(glyph_trace, 'ft-limit', 100000, 512)
    events = [(clock, pid, tid, 'face', f) for clock, pid, tid, f in faces]
    events.extend((clock, pid, tid, 'glyph', f) for clock, pid, tid, f in glyphs)
    events.sort(key=lambda row: row[:3])
    live, uses, times = {}, {}, set()
    face_operations = Counter()
    for clock, pid, tid, kind, f in events:
        key = (pid, f[5])
        # Equal timestamps for one face cannot order two separate event files.
        identity = (pid, f[5], clock)
        require(identity not in times, 'ambiguous face event timestamp')
        times.add(identity)
        if kind == 'face':
            operation, index, error, source_kind, size = f[4], int(f[7]), int(f[8]), f[9], int(f[10])
            require(index == 0 and error == 0, 'unmeasured face index or API error')
            face_operations[operation] += 1
            if operation == 'open':
                require(key not in live and source_kind in ('file', 'memory') and f[11] in known,
                        'unmeasured, opaque or overlapping face source')
                resource = known[f[11]]
                require(resource['family'] == f[6] and resource['bytes'] == size,
                        'face source metadata differs from pinned resource')
                if source_kind == 'file':
                    require(re.fullmatch('(?:[0-9a-f]{2}){1,512}', f[12]), 'unmeasured file pathname')
                else:
                    require(f[12] == '-', 'memory source has a pathname')
                live[key] = [1, f[11], f[6]]
            else:
                require(operation in ('reference', 'done') and key in live
                        and live[key][2] == f[6] and f[9:] == ['-', '0', '-', '-'],
                        'unmatched face lifetime event')
                live[key][0] += 1 if operation == 'reference' else -1
                require(live[key][0] <= 65536, 'face reference limit')
                if not live[key][0]:
                    del live[key]
            continue
        op, a, b, error, x, y, depth = f[4], *map(int, f[7:])
        require(op in ('cmap', 'load') and error == 0 and 0 <= depth <= 32
                and 0 <= x <= 65535 and 0 <= y <= 65535 and 0 <= b < 2**31,
                'glyph event profile or FreeType error')
        require(key in live and live[key][2] == f[6], 'glyph call without a live observed resource')
        sha = live[key][1]; resource = known[sha]
        gid = b if op == 'cmap' else a
        require(0 <= gid < resource['num_glyphs'] and (op != 'cmap' or 0 <= a < 2**32),
                'glyph/code outside resource bounds')
        use = uses.setdefault(sha, {'resource': resource['resource'], 'family': resource['family'],
            'sha256': sha, 'face_index': 0, 'all_glyph_api_events': 0,
            'outer_cmap_calls': 0, 'outer_render_loads': 0, 'nested_events': 0,
            'rendered_glyph_ids': set(), 'render_sizes': Counter(), 'faces': set()})
        use['all_glyph_api_events'] += 1; use['faces'].add(key)
        if depth:
            use['nested_events'] += 1
        elif op == 'cmap':
            use['outer_cmap_calls'] += 1
        elif b & 4:
            require(gid > 0, 'outer render requests missing glyph zero')
            use['outer_render_loads'] += 1
            use['rendered_glyph_ids'].add(gid); use['render_sizes'][(x, y)] += 1
    require(uses and sum(u['outer_render_loads'] for u in uses.values()) > 0, 'no observed render loads')
    for use in uses.values():
        use['rendered_glyph_ids'] = sorted(use['rendered_glyph_ids'])
        use['render_sizes'] = [{'x': x, 'y': y, 'loads': count}
                               for (x, y), count in sorted(use['render_sizes'].items())]
        use['distinct_face_addresses'] = len(use.pop('faces'))
    return {'status': 'OBSERVED_CALLS_BOUND', 'face_trace_sha256': face_sha,
            'glyph_trace_sha256': glyph_sha, 'face_events': len(faces), 'glyph_events': len(glyphs),
            'face_processes': len({pid for _, pid, _, _ in faces}),
            'face_operations': dict(sorted(face_operations.items())),
            'live_faces_at_trace_end': len(live),
            'resources': [uses[key] for key in sorted(uses)],
            'source_font_fidelity': 'UNVERIFIED', 'cached_draw_coverage': 'UNVERIFIED'}


def isolated_mapping(glyph_trace, binding):
    """Associate calls only for an independently verified one-glyph control.

    Unlike native_font_trace's five-size C8 protocol, this reports the sizes
    actually observed. It cannot establish missing-size or cached-draw coverage.
    The caller must establish the control's sole source code separately.
    """
    require(binding['status'] == 'OBSERVED_CALLS_BOUND' and len(binding['resources']) == 1,
            'isolated control needs one bound resource')
    rows, sha = read_trace(glyph_trace, 'ft-limit', 100000, 512)
    require(sha == binding['glyph_trace_sha256'], 'binding belongs to a different glyph trace')
    previous, pairs, sizes = {}, [], set()
    for _, pid, tid, f in sorted(rows, key=lambda row: row[:3]):
        if int(f[12]):
            continue
        op, a, b, x, y = f[4], int(f[7]), int(f[8]), int(f[10]), int(f[11])
        key = (pid, tid, f[5]); recent = previous.get(key)
        if op == 'load' and b & 4:
            require(recent is not None and recent[0] == 'cmap' and recent[2:] == (a, x, y),
                    'unpaired isolated render load')
            require(x > 0 and y > 0 and (x, y) not in sizes, 'extra or invalid isolated glyph/size')
            sizes.add((x, y)); pairs.append((recent[1], a))
        previous[key] = (op, a, b, x, y)
    resource = binding['resources'][0]
    require(pairs and len(set(pairs)) == 1 and len(pairs) == resource['outer_cmap_calls']
            == resource['outer_render_loads'], 'ambiguous isolated mapping or unmatched cmap')
    alias, gid = pairs[0]
    return {'status': 'ISOLATED_CALLS_AGREE', 'resource_sha256': resource['sha256'],
            'family': resource['family'], 'cmap_argument': alias, 'glyph_id': gid,
            'observed_sizes': [list(size) for size in sorted(sizes)],
            'render_loads': len(pairs), 'missing_size_coverage': 'UNVERIFIED'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('faces', type=Path)
    parser.add_argument('glyphs', type=Path)
    parser.add_argument('resources', type=Path)
    parser.add_argument('--isolated-glyph', action='store_true',
                        help='only for independently verified one-glyph authored controls')
    args = parser.parse_args()
    require(args.resources.stat().st_size <= 1024 * 1024, 'resource manifest byte limit')
    result = bind(args.faces, args.glyphs, json.loads(args.resources.read_text())['resources'])
    if args.isolated_glyph:
        result['isolated_mapping'] = isolated_mapping(args.glyphs, result)
    print(json.dumps(result, indent=2))
