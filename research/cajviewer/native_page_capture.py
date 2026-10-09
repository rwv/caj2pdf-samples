#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Opt-in complete-page raster observation for the measured Linux viewer setup.

Requires an externally supplied, already-built opaque viewer image and the
original qpaint_observe.cpp interposer. No image, documents, fonts or captures
are downloaded. Repeated cached rasters are observations, not fidelity passes.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import time

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from hnc8_layout_source import FileInput, SourceExtractor

DISPLAY = (1600, 1200)
START = '''#!/bin/sh
set -eu
Xvfb :99 -screen 0 1600x1200x24 -dpi 96 -nolisten tcp -noreset >/output/xvfb.log 2>&1 &
for i in $(seq 1 50); do xdpyinfo >/dev/null 2>&1 && break; sleep .1; done
openbox --sm-disable >/output/openbox.log 2>&1 &
LD_PRELOAD=/probe/observer.so /opt/cajviewer/bin/start.sh /input/source.caj >/output/viewer.log 2>&1 &
wait
'''


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def navigation_route(page_count, requested):
    if type(page_count) is not int or not 1 <= page_count <= 12:
        raise ValueError('unmeasured page count')
    if requested is None:
        return tuple(range(1, page_count + 1))
    if (not 1 <= len(requested) <= 12
            or any(type(page) is not int or not 1 <= page <= page_count for page in requested)
            or len(set(requested)) != len(requested)):
        raise ValueError('route requires 1 through 12 distinct in-range pages')
    return tuple(requested)


def trace(path):
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError('paint trace byte limit')
    lines = path.read_text().splitlines()
    if len(lines) > 100000 or 'LIMIT' in lines:
        raise ValueError('paint trace event limit')
    return lines


def select_page(lines, extent, minimum):
    """Require a complete page at the observed navigation origin, not prefetch.

    The pinned desktop's document widget is 791 pixels wide; its height is
    1031, or 1014 when its horizontal scrollbar is present. The source page
    must exceed both viewport heights. Compact/multiple-page views are refused.
    """
    candidates = []
    for line in lines:
        f = line.split('\t')
        if len(f) != 31:
            raise ValueError('unmeasured paint record')
        if int(f[0]) < minimum or not f[1].startswith('pixmap-'):
            continue
        width, height = map(int, f[7:9])
        target, source = [float(x) for x in f[9:13]], [float(x) for x in f[13:17]]
        error = abs(height - width * extent[1] / extent[0])
        # Integer target dimensions truncate a common source-to-display scale.
        # Test intersecting one-pixel quantization intervals in both axes;
        # do not fit a per-document residual threshold to the pixmap aspect.
        scale_low = max(Fraction(target[2]) / extent[0], Fraction(target[3]) / extent[1])
        scale_high = min(Fraction(target[2] + 1) / extent[0], Fraction(target[3] + 1) / extent[1])
        if (f[3:5] != ['1', '791'] or int(f[5]) not in (1014, 1031)
                or width < 200 or height <= 1031 or width * height > 4 * 1024 * 1024
                or scale_low >= scale_high or target[0] < 0 or target[1] != 10
                or source != [0, 0, width, height] or f[30] != '1'
                or f[23] != '0' or float(f[24]) != 1
                or abs(target[2] - width) > 1 or abs(target[3] - height) > 1):
            continue
        candidates.append({'event': int(f[0]), 'cache_key': f'{int(f[6]) & ((1 << 64) - 1):016x}',
                           'size': [width, height], 'target': target, 'source': source,
                           'source_aspect_error_pixels': error})
    if not candidates:
        raise ValueError('no complete current-page raster after navigation')
    return max(candidates, key=lambda row: row['event'])


def observe(args, case):
    route = navigation_route(case['pages'], args.route)
    sha = case['source_sha256']
    if not re.fullmatch('[0-9a-f]{64}', sha) or not 1 <= case['pages'] <= 12:
        raise ValueError('unmeasured case identity or page count')
    source = Path(case['source_path']).resolve()
    if digest(source) != sha:
        raise ValueError('source digest mismatch')
    output = args.output / sha
    output.mkdir(); (output / 'input').mkdir()
    copy = output / 'input/source.caj'
    shutil.copyfile(source, copy)
    if digest(copy) != sha:
        raise ValueError('source copy changed')
    with FileInput(copy) as data:
        header = SourceExtractor(data, sha).header
        if header['variant'] not in ('C8', 'HN-B') or header['page_count'] != case['pages']:
            raise ValueError('unmeasured source profile')
        c8 = header['variant'] == 'C8'
        mode = int.from_bytes(data.read_at(12 if c8 else 148, 4), 'little')
        extent = list(struct.unpack('<HH', data.read_at(32 if c8 else 168, 4)))
        if mode == 0:
            extent = [v + 100 for v in extent]
        if mode not in (0, 2) or not all(extent):
            raise ValueError('unmeasured native extent')
    name = 'caj2pdf-page-observer-' + sha[:12] + '-' + str(time.time_ns())
    (output / 'start.sh').write_text(START)
    command = ['docker', 'run', '-d', '--pull', 'never', '--name', name,
               '--network', 'none', '--read-only', '--user', '1000:1000',
               '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
               '--memory', '2g', '--memory-swap', '2g', '--cpus', '2',
               '--pids-limit', '256', '--shm-size', '128m',
               '--ulimit', 'core=0:0', '--ulimit', 'fsize=67108864:67108864',
               '--tmpfs', '/tmp:rw,size=128m',
               '--tmpfs', '/home/canary:rw,size=128m,uid=1000,gid=1000',
               '--tmpfs', '/runtime:rw,size=16m,uid=1000,gid=1000,mode=700',
               '-e', 'XDG_CACHE_HOME=/tmp']
    mounts = [(output / 'input', '/input', True), (output, '/output', False),
              (output / 'start.sh', '/start.sh', True),
              (Path(__file__).resolve().parent, '/tools', True),
              (args.observer, '/probe/observer.so', True)]
    fonts = {}
    if args.font_directory:
        paths = sorted(path for path in args.font_directory.iterdir() if path.suffix.lower() == '.ttf')
        if not 1 <= len(paths) <= 84:
            raise ValueError('font resource count outside measured limit')
        for path in paths:
            if not re.fullmatch('[A-Za-z0-9_-]+[.](ttf|TTF)', path.name):
                raise ValueError('unmeasured font resource filename')
            fonts[path.stem] = digest(path)
            mounts.append((path, '/opt/cajviewer/bin/Resource/cajfonts/' + path.name, True))
    for path, destination, readonly in mounts:
        if ',' in str(path):
            raise ValueError('commas in bind paths are not supported')
        command += ['--mount', f'type=bind,src={path},dst={destination}' + (',readonly' if readonly else '')]
    command += ['--entrypoint', '/usr/bin/timeout', args.image, str(args.lifetime_seconds), 'sh', '/start.sh']
    write_json(output / 'launch.json', {'command': command, 'source_sha256': sha, 'route': route,
               'source_extent': extent, 'observer_sha256': digest(args.observer), 'fonts': fonts})

    def run(command):
        started = time.monotonic()
        result = subprocess.run(command, capture_output=True, timeout=20)
        with (output / 'actions.jsonl').open('a') as ledger:
            ledger.write(json.dumps({'command': command, 'return_code': result.returncode,
                'wall_ms': round((time.monotonic() - started) * 1000),
                'stdout_bytes': len(result.stdout), 'stderr_bytes': len(result.stderr),
                'stdout_sha256': hashlib.sha256(result.stdout).hexdigest(),
                'stderr_sha256': hashlib.sha256(result.stderr).hexdigest()}) + '\n')
        result.check_returncode()
        return result.stdout

    def ui(*words):
        return run(['docker', 'exec', name, *words])

    def x(*words):
        ui('xdotool', *words)

    def field(image, box, stem, whitelist):
        crop = image.crop(box)
        path = output / (stem + '.png')
        crop.resize((crop.width * 4, crop.height * 4)).save(path)
        return run(['tesseract', str(path), 'stdout', '--psm', '7', '-c',
                    'tessedit_char_whitelist=' + whitelist]).decode().strip()

    def capture(page, suffix, minimum):
        stem = f'page-{page:03d}-{suffix}'
        data = ui('python3', '-c', 'import sys;sys.path.insert(0,"/tools");'
                  'from capability_x11 import X11;x=X11();'
                  'sys.stdout.buffer.write(x.image((0,0,1600,1200)));x.close()')
        if len(data) != DISPLAY[0] * DISPLAY[1] * 3:
            raise ValueError('unexpected screenshot byte count')
        with Image.frombytes('RGB', DISPLAY, data) as image:
            image.save(output / (stem + '.png'))
            observed = field(image, (360, 86, 440, 105), stem + '-page', '0123456789/')
            zoom = field(image, (598, 86, 655, 105), stem + '-zoom', '0123456789%')
        if observed != f'{page}/{case["pages"]}' or zoom != '150%':
            raise ValueError(f'page/zoom field mismatch: {observed}, {zoom}')
        if (output / 'capture-limit').exists():
            raise ValueError('pixmap capture limit')
        lines = trace(output / 'paint.tsv')
        chosen = select_page(lines, extent, minimum)
        files = list(output.glob('pixmap-*-' + chosen['cache_key'] + '.png'))
        if len(files) != 1:
            raise ValueError('missing/ambiguous pixmap file')
        with Image.open(files[0]) as image:
            if list(image.size) != chosen['size']:
                raise ValueError('pixmap dimensions changed')
        chosen.update(file=files[0].name, sha256=digest(files[0]))
        return {'field': observed, 'zoom': zoom, 'frame_sha256': digest(output / (stem + '.png')),
                'trace_last_event': max(int(line.split('\t')[0]) for line in lines), 'pixmap': chosen}

    rows = []
    try:
        run(command)
        time.sleep(5)
        x('mousemove', '800', '210', 'click', '--repeat', '2', '--delay', '120', '1')
        time.sleep(1)
        x('mousemove', '640', '95', 'click', '1', 'key', 'ctrl+a')
        x('type', '--clearmodifiers', '--delay', '40', '150%'); x('key', 'Return')
        x('mousemove', '211', '95', 'click', '1', 'mousemove', '10', '1100')
        time.sleep(2)
        for page in route:
            row = {'page': page}
            try:
                lines = trace(output / 'paint.tsv')
                minimum = 1 + max(int(line.split('\t')[0]) for line in lines)
                x('mousemove', '400', '95', 'click', '1', 'key', 'ctrl+a')
                x('type', '--clearmodifiers', '--delay', '40', str(page)); x('key', 'Return')
                x('mousemove', '211', '95', 'click', '1', 'mousemove', '10', '1100')
                time.sleep(2); row['first'] = capture(page, 'a', minimum)
                time.sleep(2); row['second'] = capture(page, 'b', minimum)
                row['status'] = ('STABLE' if row['first']['pixmap']['sha256'] == row['second']['pixmap']['sha256']
                                 else 'UNSTABLE')
            except (ValueError, OSError, subprocess.SubprocessError) as error:
                row.update(status='NOT_CONFIRMED', reason=str(error))
            rows.append(row); write_json(output / 'pages.json', rows)
            print(sha[:12], page, row['status'], row.get('reason', ''), flush=True)
    finally:
        closing = []
        for words in (['inspect', '--format', '{{json .State}}', name],
                      ['exec', name, 'cat', '/sys/fs/cgroup/memory.peak'],
                      ['stop', '--time', '3', name], ['rm', name],
                      ['ps', '-a', '--filter', 'name=^/' + name + '$', '--format', '{{.ID}}']):
            try:
                result = subprocess.run(['docker', *words], capture_output=True, text=True, timeout=20)
                closing.append({'command': words, 'exit': result.returncode,
                                'stdout': result.stdout, 'stderr': result.stderr})
            except (OSError, subprocess.SubprocessError) as error:
                # A failed observation must not prevent later stop/remove
                # attempts. The final presence query remains authoritative.
                closing.append({'command': words, 'exit': None, 'stdout': '', 'stderr': str(error)})
        intact = digest(source) == digest(copy) == sha
        absent = closing[-1]['exit'] == 0 and not closing[-1]['stdout'].strip()
        write_json(output / 'closing.json', {'records': closing, 'source_unchanged': intact,
                   'container_absent': absent, 'pages_observed': len(rows)})
        if not intact or not absent:
            raise ValueError('input integrity or cleanup could not be confirmed')
    return len(rows) == len(route) and all(row['status'] == 'STABLE' for row in rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--observer', required=True, type=Path)
    parser.add_argument('--image', required=True)
    parser.add_argument('--font-directory', type=Path)
    parser.add_argument('--route', type=int, nargs='+', help='distinct pages to visit; default: all pages')
    parser.add_argument('--lifetime-seconds', type=int, choices=(90, 600), default=600,
                        help='hard container lifetime; default: 600; short controls: 90')
    args = parser.parse_args()
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', args.image) or args.manifest.stat().st_size > 1024 * 1024:
        parser.error('require a pinned local image and a bounded manifest')
    for key in ('output', 'observer', 'font_directory'):
        if getattr(args, key) is not None:
            setattr(args, key, getattr(args, key).resolve())
    cases = json.loads(args.manifest.read_text())
    if not 1 <= len(cases) <= 10 or len({case['source_sha256'] for case in cases}) != len(cases):
        parser.error('require 1 through 10 unique cases')
    try:
        for case in cases:
            navigation_route(case['pages'], args.route)
    except ValueError as error:
        parser.error(str(error))
    args.output.mkdir(exist_ok=False)
    # Retain the executed research source before later worktree edits. Imported
    # framing/X11 modules remain pinned by the repository revision in reports.
    shutil.copyfile(__file__, args.output / 'runner.py')
    complete = True
    for case in cases:
        complete = observe(args, case) and complete
    raise SystemExit(0 if complete else 1)
