# SPDX-License-Identifier: MIT
"""Exercise public Qt5 model observation with original models only."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

RESEARCH = Path(__file__).resolve().parents[1]


class TreeObserverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.log = cls.root/'trees.jsonl'
        cls.stop = cls.root/'stop-observer'
        cls.observer = cls.root/'observer.so'
        cls.control = cls.root/'control'
        flags = shlex.split(subprocess.check_output(['pkg-config', '--cflags', '--libs', 'Qt5Widgets'], text=True))
        compiler = ['c++', '-std=c++17', '-fPIC', '-O2', '-Wall', '-Wextra', '-Werror', '-DQT_NO_VERSION_TAGGING']
        subprocess.run(compiler + ['-shared', '-DTREE_OBSERVE_OUTPUT="'+str(cls.log)+'"',
                       '-DTREE_OBSERVE_STOP="'+str(cls.stop)+'"', str(RESEARCH/'cajviewer/qtree_observe.cpp'),
                       '-ldl', '-o', str(cls.observer)] + flags, check=True, timeout=60)
        subprocess.run(compiler + [str(RESEARCH/'conformance/qtree_control.cpp'), '-o', str(cls.control)] + flags,
                       check=True, timeout=60)

    def setUp(self):
        self.log.unlink(missing_ok=True)
        self.stop.unlink(missing_ok=True)

    def run_control(self, *args, observe=True):
        env = dict(os.environ, LD_PRELOAD=str(self.observer), QT_QPA_PLATFORM='offscreen',
                   XDG_RUNTIME_DIR=str(self.root), XDG_CACHE_HOME=str(self.root))
        if not observe:
            env.pop('LD_PRELOAD')
        result = subprocess.run([str(self.control), *args], env=env, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        return ([json.loads(line) for line in self.log.read_text().splitlines()] if observe else []), result.stdout

    def test_nested_empty_lazy_and_bounded_models(self):
        _, baseline = self.run_control(observe=False)
        self.assertFalse(self.log.exists())
        rows, observed = self.run_control()
        self.assertEqual(observed, baseline)
        def selected(name):
            sha = hashlib.sha256(name.encode()).hexdigest()
            return [row for row in rows if row.get('name_sha256') == sha]
        nested = selected('nested')
        self.assertTrue(any(row['nodes'] == 0 for row in nested))
        self.assertEqual((nested[-1]['nodes'], nested[-1]['root_rows'], nested[-1]['depth']), (6, 2, 2))
        self.assertEqual(selected('empty')[-1]['nodes'], 0)
        self.assertTrue(selected('lazy')[-1]['can_fetch_more'])
        self.assertTrue(selected('deep')[-1]['limit'])
        self.assertEqual(selected('deep')[-1]['nodes'], 128)
        self.assertTrue(selected('wide')[-1]['limit'])
        self.assertTrue(selected('invalid')[-1]['invalid'])
        self.assertNotIn('original A', self.log.read_text())

    def test_requested_stop_acknowledges_complete_record(self):
        rows, _ = self.run_control('stop', str(self.stop))
        self.assertEqual(rows[-1]['sampling_stopped'], 'requested')
        self.assertEqual(rows[-1]['last_tick'], max(row.get('tick', 0) for row in rows))
        self.assertEqual(sum('sampling_stopped' in row for row in rows), 1)

    def test_tree_inventory_limit_is_not_empty_success(self):
        rows, _ = self.run_control('many')
        self.assertTrue(any(row.get('tree_limit') is True for row in rows))
        self.assertTrue(all(row['sample_complete'] is False for row in rows if 'sample_complete' in row))


if __name__ == '__main__':
    unittest.main()
