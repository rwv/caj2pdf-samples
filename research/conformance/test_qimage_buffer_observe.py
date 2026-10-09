# SPDX-License-Identifier: MIT
"""Compile/run the original Qt5 control without a viewer, display or corpus."""
import hashlib
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

RESEARCH = Path(__file__).resolve().parents[1]


class BufferObserverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.log = cls.root / 'buffers.tsv'
        cls.observer = cls.root / 'observer.so'
        cls.control = cls.root / 'control'
        cflags = shlex.split(subprocess.check_output(['pkg-config', '--cflags', 'Qt5Gui'], text=True))
        libs = shlex.split(subprocess.check_output(['pkg-config', '--libs', 'Qt5Gui'], text=True))
        compiler = ['c++', '-std=c++17', '-fPIC', '-O2', '-Wall', '-Wextra', '-Werror']
        subprocess.run(compiler + cflags + ['-shared', '-DQT_NO_VERSION_TAGGING',
                       '-DQIMAGE_OBSERVE_OUTPUT="' + str(cls.log) + '"',
                       str(RESEARCH/'cajviewer/qimage_buffer_observe.cpp'), '-ldl', '-o', str(cls.observer)],
                       check=True, timeout=60)
        subprocess.run(compiler + cflags + [str(RESEARCH/'conformance/qimage_buffer_control.cpp'),
                       '-o', str(cls.control)] + libs, check=True, timeout=60)

    def setUp(self):
        self.log.unlink(missing_ok=True)

    def run_control(self, *args):
        env = dict(os.environ, LD_PRELOAD=str(self.observer))
        return subprocess.run([str(self.control), *args], env=env, capture_output=True, timeout=20)

    def test_forwarding_cleanup_padding_and_hash_bounds(self):
        result = self.run_control()
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = [line.split('\t') for line in self.log.read_text().splitlines()]
        self.assertEqual(len(rows), 10)
        expected = hashlib.sha256(bytes(value for y in range(101) for x in range(201)
                                  for value in ((x*17+y)%256, (x+y*13)%256, (x*3+y*5)%256))).hexdigest()
        self.assertEqual([row[3] for row in rows[:4]],
                         ['mutable_tight', 'const_tight', 'mutable_stride', 'const_stride'])
        self.assertEqual([row[7] for row in rows[:4]], ['604', '604', '608', '608'])
        self.assertEqual([row[-1] for row in rows[:4]], [expected]*4)
        self.assertEqual([row[-1] for row in rows[4:]], ['']*6)
        self.assertTrue(all(len(row) == 14 for row in rows))

    def test_event_cap_is_explicit(self):
        result = self.run_control('limit')
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = self.log.read_text().splitlines()
        self.assertEqual(len(lines), 10001)
        self.assertEqual(lines[-1], 'LIMIT')
        self.assertLess(self.log.stat().st_size, 512*10001)

    def test_log_failure_is_fatal_not_silent_success(self):
        self.log.mkdir()
        try:
            self.assertEqual(self.run_control().returncode, 126)
        finally:
            self.log.rmdir()


if __name__ == '__main__':
    unittest.main()
