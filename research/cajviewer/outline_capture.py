#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Opt-in displayed-contents inventory in the pinned offline Linux viewer.

No source title, private model role or font program is read. EMPTY_DISPLAYED is
an observation of this viewer, not proof of absent stored metadata or fidelity.
Every source gets a fresh process; failures are retained without auto-retry.
"""
import argparse
from concurrent.futures import CancelledError, ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from hnc8_layout_source import FileInput, SourceExtractor

TREE_NAME = '440a7e4c28b3209859cc4e008dbd77494c7b211d413e06546b47035202fd68ea'
START = '''#!/bin/sh
set -eu
Xvfb :99 -screen 0 1600x1200x24 -dpi 96 -nolisten tcp -noreset >/output/xvfb.log 2>&1 &
for i in $(seq 1 50); do xdpyinfo >/dev/null 2>&1 && break; sleep .1; done
openbox --sm-disable >/output/openbox.log 2>&1 &
LD_LIBRARY_PATH=/opt/cajviewer/lib LD_PRELOAD=/probe/observer.so /opt/cajviewer/bin/start.sh /input/source.caj >/output/viewer.log 2>&1 &
wait
'''


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def read_trace(path):
    require(path.stat().st_size <= 8*1024*1024, 'tree trace byte limit')
    with path.open() as stream:
        rows = []
        for line in stream:
            require(len(line) <= 2048 and len(rows) < 4000, 'tree trace record limit')
            rows.append(json.loads(line))
    return rows


def snapshot(rows, pages, before_ns):
    """Validate the latest complete sample, never search backward to a match."""
    require(type(pages) is int and 1 <= pages <= 100000, 'invalid expected pages')
    completed = [r for r in rows if 'sample_complete' in r]
    require(completed, 'no complete UI sample')
    eligible = [r for r in completed if int(r['monotonic_ns']) <= before_ns]
    require(eligible, 'no sample preceding capture')
    sample = max(eligible, key=lambda r: int(r['monotonic_ns']))
    require(0 <= before_ns-int(sample['monotonic_ns']) <= 3_000_000_000, 'stale UI sample')
    require(sample['sample_complete'] is True and sample['tree_count'] == 1, 'ambiguous tree inventory')
    fields = sample.get('page_fields')
    require(isinstance(fields, list) and len(fields) == 1, 'ambiguous page indicator')
    require(all(type(fields[0].get(k)) is int for k in ('current', 'total'))
            and fields[0]['current'] == 1 and fields[0]['total'] == pages, 'page indicator mismatch')
    tick, pid = sample['tick'], sample['pid']
    frame = [r for r in rows if r.get('tick') == tick and r.get('pid') == pid]
    require(not any(any(r.get(k) for k in ('widget_limit', 'tree_limit', 'name_limit')) for r in frame),
            'incomplete UI enumeration')
    trees = [r for r in frame if r.get('class') == 'QTreeWidget' and r.get('name_sha256') == TREE_NAME]
    require(len(trees) == 1, 'contents widget missing or ambiguous')
    tree = trees[0]
    require(tree['visible'] is True and tree['model_present'] is True and tree['root_valid'] is False,
            'contents not visible or rooted at a subset')
    require(tree['model'] == 'QTreeModel' and tree['x'] == 61 and tree['y'] == 187
            and 700 <= tree['width'] <= 750 and 980 <= tree['height'] <= 1000, 'unmeasured contents geometry/model')
    require(tree['can_fetch_more'] is False and tree['limit'] is False and tree['invalid'] is False,
            'pending, limited or invalid model')
    nodes, depth, roots = tree['nodes'], tree['depth'], tree['root_rows']
    require(all(type(v) is int for v in (nodes, depth, roots))
            and 0 <= roots <= nodes <= 10000 and 0 <= depth <= 128, 'invalid model counts')
    empty = nodes == roots == depth == 0
    require(empty or (nodes > 0 and roots > 0 and depth > 0), 'inconsistent model counts')
    require(sample['empty_contents_labels'] == (1 if empty else 0), 'empty caption contradicts model')
    return {'pid': pid, 'tick': tick, 'monotonic_ns': sample['monotonic_ns'],
            'status': 'EMPTY_DISPLAYED' if empty else 'NONEMPTY_DISPLAYED',
            'nodes': nodes, 'root_rows': roots, 'depth': depth,
            'page_current': 1, 'page_total': pages, 'empty_caption_visible': empty,
            'tree': {k: tree[k] for k in ('class', 'name_sha256', 'model', 'x', 'y', 'width', 'height')}}


def preflight(manifest, documents):
    require(isinstance(manifest, list) and 0 < len(manifest) <= 1000, 'manifest count limit')
    require(all(isinstance(row, dict) and re.fullmatch('[0-9a-f]{64}', row.get('source_sha256', ''))
                and type(row.get('pages')) is int and 1 <= row['pages'] <= 100000
                and row.get('variant') in ('C8', 'HN-B') for row in manifest), 'invalid manifest row')
    require(len({row['source_sha256'] for row in manifest}) == len(manifest), 'duplicate source')
    for row in manifest:
        path = documents / (row['source_sha256'] + '.caj')
        require(path.is_file() and path.stat().st_size <= 512*1024*1024, 'missing or oversized source')
        require(digest(path) == row['source_sha256'], 'source hash mismatch')
        with FileInput(path) as source:
            header = SourceExtractor(source, row['source_sha256']).header
        require(header['variant'] == row['variant'] and header['page_count'] == row['pages'], 'source profile mismatch')


def check_closing(closing, intact, absent):
    require(len(closing) == 5 and all(r['exit'] == 0 for r in closing)
            and intact is True and absent is True, 'unconfirmed input/cleanup')
    state = json.loads(closing[0]['stdout'])
    require(state['OOMKilled'] is False and not state['Error'] and state['Running'] is True,
            'viewer/container failure')
    peak = int(closing[1]['stdout'])
    require(peak > 0, 'missing memory peak')
    return peak


def capture(case, args):
    sha = case['source_sha256']
    source = args.documents / (sha + '.caj')
    output = args.output / sha
    output.mkdir()
    (output / 'input').mkdir()
    copy = output / 'input/source.caj'
    shutil.copyfile(source, copy)
    require(digest(copy) == digest(source) == sha, 'source changed before launch')
    (output / 'start.sh').write_text(START)
    name = 'caj2pdf-outline-' + sha[:12] + '-' + str(time.time_ns())
    command = ['docker', 'run', '-d', '--pull', 'never', '--name', name,
               '--network', 'none', '--read-only', '--user', '1000:1000',
               '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
               '--memory', '2g', '--memory-swap', '2g', '--cpus', '2', '--pids-limit', '256',
               '--shm-size', '128m', '--ulimit', 'core=0:0', '--ulimit', 'fsize=67108864:67108864',
               '--tmpfs', '/tmp:rw,size=128m',
               '--tmpfs', '/home/canary:rw,size=128m,uid=1000,gid=1000',
               '--tmpfs', '/runtime:rw,size=16m,uid=1000,gid=1000,mode=700', '-e', 'XDG_CACHE_HOME=/tmp']
    for path, destination, readonly in [
        (output/'input', '/input', True), (output, '/output', False),
        (output/'start.sh', '/start.sh', True), (Path(__file__).resolve().parent, '/tools', True),
        (args.observer, '/probe/observer.so', True),
        (args.ui_font, '/usr/share/fonts/truetype/NotoSansCJK-Regular.ttc', True)]:
        require(',' not in str(path), 'comma in bind path')
        command += ['--mount', f'type=bind,src={path},dst={destination}' + (',readonly' if readonly else '')]
    command += ['--entrypoint', '/usr/bin/timeout', args.image, '90', 'sh', '/start.sh']
    write_json(output/'launch.json', {'command': command, 'source_sha256': sha, 'pages': case['pages'],
               'observer_sha256': digest(args.observer), 'ui_font_sha256': digest(args.ui_font),
               'runner_sha256': digest(Path(__file__)), 'scope': __doc__})

    def run(words):
        start = time.monotonic_ns()
        result = subprocess.run(words, capture_output=True, timeout=20)
        with (output/'actions.jsonl').open('a') as log:
            log.write(json.dumps({'command': words, 'started_monotonic_ns': start,
                      'finished_monotonic_ns': time.monotonic_ns(), 'exit': result.returncode,
                      'stdout_bytes': len(result.stdout), 'stderr_bytes': len(result.stderr),
                      'stdout_sha256': hashlib.sha256(result.stdout).hexdigest(),
                      'stderr_sha256': hashlib.sha256(result.stderr).hexdigest()}) + '\n')
        result.check_returncode()
        return result.stdout

    def x(*words):
        return run(['docker', 'exec', name, 'xdotool', *words])

    frames = []
    def frame(label, validate=False):
        before = time.monotonic_ns()
        data = run(['docker', 'exec', name, 'python3', '-c',
                    'import sys;sys.path.insert(0,"/tools");from capability_x11 import X11;'
                    'x=X11();sys.stdout.buffer.write(x.image((0,0,1600,1200)));x.close()'])
        require(len(data) == 1600*1200*3, 'screenshot extent mismatch')
        with Image.frombytes('RGB', (1600, 1200), data) as image:
            image.save(output/(label+'.png'))
        row = {'label': label, 'before_monotonic_ns': before, 'after_monotonic_ns': time.monotonic_ns(),
               'png_sha256': digest(output/(label+'.png'))}
        frames.append(row)
        if validate:
            row['observation'] = snapshot(read_trace(output/'trees.jsonl'), case['pages'], before)

    result = {**case, 'status': 'NOT_CONFIRMED', 'frames': frames}
    try:
        run(command)
        time.sleep(5)
        frame('initial')
        x('mousemove', '1004', '217', 'click', '1')
        time.sleep(2)
        frame('maximized')
        trace = read_trace(output/'trees.jsonl')
        latest = max(r['tick'] for r in trace if 'sample_complete' in r)
        # Populated contents may already be selected. Clicking that tab again
        # would hide it; decide from the public widget visibility, not variant.
        selected = [r for r in trace if r.get('tick') == latest and r.get('name_sha256') == TREE_NAME
                    and r.get('visible') is True]
        if not selected:
            x('mousemove', '30', '175', 'click', '1')
        x('mousemove', '10', '1100')
        time.sleep(5)
        frame('contents-a', True)
        time.sleep(10)
        frame('contents-b', True)
        time.sleep(5)
        frame('contents-c', True)
        observed = [r['observation'] for r in frames if 'observation' in r]
        require(len(observed) == 3 and observed[0]['tick'] < observed[1]['tick'] < observed[2]['tick'],
                'checkpoints did not observe distinct timer samples')
        require(len({(r['pid'], r['status'], r['nodes'], r['root_rows'], r['depth']) for r in observed}) == 1,
                'contents changed between checkpoints')
        # Stop only our timer; wait for its complete-record acknowledgement.
        (output/'stop-observer').touch(exist_ok=False)
        for _ in range(20):
            trace = read_trace(output/'trees.jsonl')
            if any(r.get('sampling_stopped') == 'requested' and r['pid'] == observed[0]['pid'] for r in trace):
                break
            time.sleep(.1)
        else:
            raise ValueError('observer stop was not acknowledged')
        interval = [r for r in trace if 'sample_complete' in r and r['pid'] == observed[0]['pid']
                    and observed[0]['tick'] <= r['tick'] <= observed[-1]['tick']]
        require([r['tick'] for r in interval] == list(range(observed[0]['tick'], observed[-1]['tick']+1)),
                'missing intermediate UI sample')
        for sample in interval:
            check = snapshot(trace, case['pages'], int(sample['monotonic_ns']))
            require((check['status'], check['nodes'], check['root_rows'], check['depth']) ==
                    (observed[0]['status'], observed[0]['nodes'], observed[0]['root_rows'], observed[0]['depth']),
                    'contents changed within observation interval')
        result.update(status=observed[0]['status'], nodes=observed[0]['nodes'],
                      root_rows=observed[0]['root_rows'], depth=observed[0]['depth'],
                      consecutive_samples=len(interval), tree_trace_sha256=digest(output/'trees.jsonl'))
    except (OSError, ValueError, subprocess.SubprocessError, KeyError, TypeError) as error:
        result['reason'] = str(error)
    finally:
        closing = []
        for words in [['inspect', '--format', '{{json .State}}', name],
                      ['exec', name, 'cat', '/sys/fs/cgroup/memory.peak'], ['stop', '--time', '3', name],
                      ['rm', name], ['ps', '-a', '--filter', 'name=^/'+name+'$', '--format', '{{.ID}}']]:
            try:
                r = subprocess.run(['docker', *words], capture_output=True, text=True, timeout=20)
                closing.append({'command': words, 'exit': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr})
            except (OSError, subprocess.SubprocessError) as error:
                closing.append({'command': words, 'exit': None, 'stdout': '', 'stderr': str(error)})
        try:
            intact = digest(source) == digest(copy) == sha
        except OSError as error:
            intact = False
            result['integrity_error'] = str(error)
        absent = closing[-1]['exit'] == 0 and not closing[-1]['stdout'].strip()
        write_json(output/'closing.json', {'records': closing, 'source_unchanged': intact, 'container_absent': absent})
        result.update(source_unchanged=intact, container_absent=absent)
        try:
            peak = check_closing(closing, intact, absent)
            result.update(source_unchanged=True, container_absent=True, oom=False,
                          memory_peak_bytes=peak)
        except (ValueError, KeyError, TypeError) as error:
            result.update(status='NOT_CONFIRMED', cleanup_reason=str(error))
        write_json(output/'result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('documents', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--observer', type=Path, required=True)
    parser.add_argument('--ui-font', type=Path, required=True)
    parser.add_argument('--image', required=True)
    parser.add_argument('--workers', type=int, choices=(1, 2, 4, 6), default=1)
    args = parser.parse_args()
    require(re.fullmatch('sha256:[0-9a-f]{64}', args.image), 'pin the already supplied image digest')
    for key in ('manifest', 'documents', 'output', 'observer', 'ui_font'):
        setattr(args, key, getattr(args, key).resolve())
    checkout = Path(__file__).resolve().parents[2]
    require(checkout != args.output and checkout not in args.output.parents, 'captures must remain external')
    require(args.manifest.stat().st_size <= 1024*1024, 'manifest byte limit')
    require(args.observer.is_file() and args.ui_font.is_file(), 'missing observer or UI font')
    manifest = json.loads(args.manifest.read_text())
    preflight(manifest, args.documents)
    args.output.mkdir(exist_ok=False)
    write_json(args.output/'plan.json', {'manifest_sha256': digest(args.manifest), 'cases': len(manifest),
               'workers': args.workers, 'scope': __doc__, 'automatic_retries': False,
               'observer_sha256': digest(args.observer), 'runner_sha256': digest(Path(__file__))})
    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(capture, case, args): case for case in manifest}
        for future in as_completed(futures):
            try:
                row = future.result()
            except CancelledError:
                row = {**futures[future], 'status': 'NOT_CONFIRMED', 'launched': False,
                       'reason': 'not launched after an unconfirmed container cleanup'}
            except Exception as error:
                row = {**futures[future], 'status': 'NOT_CONFIRMED', 'runner_error': str(error)}
            if row.get('container_absent') is False:
                for pending in futures:
                    pending.cancel()  # Running sessions still finish their own cleanup.
            rows.append(row)
            write_json(args.output/'results.json', rows)
            print(len(rows), '/', len(manifest), row['source_sha256'][:12], row['status'],
                  row.get('reason', row.get('cleanup_reason', row.get('runner_error', ''))), flush=True)
    return int(any(row['status'] == 'NOT_CONFIRMED' for row in rows))


if __name__ == '__main__':
    raise SystemExit(main())
