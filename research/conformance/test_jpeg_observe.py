# SPDX-License-Identifier: MIT
"""Independent public JPEG forwarding, row identities and explicit refusal controls."""
import hashlib
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest
from PIL import Image

RESEARCH = Path(__file__).resolve().parents[1]


class JpegObserver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.log = cls.root/'jpeg.tsv'
        cls.observer = cls.root/'observer.so'
        cls.control = cls.root/'control'
        flags = shlex.split(subprocess.check_output(['pkg-config','--cflags','Qt5Core'],text=True))
        libs = shlex.split(subprocess.check_output(['pkg-config','--libs','Qt5Core'],text=True))
        compiler = ['c++','-std=c++17','-fPIC','-O2','-Wall','-Wextra','-Werror']
        subprocess.run(compiler+flags+['-shared','-DQT_NO_VERSION_TAGGING',
            '-DJPEG_OBSERVE_OUTPUT="'+str(cls.log)+'"',str(RESEARCH/'cajviewer/jpeg_observe.cpp'),
            '-ldl','-o',str(cls.observer)],check=True,timeout=60)
        subprocess.run(compiler+flags+[str(RESEARCH/'conformance/jpeg_observe_control.cpp'),
            '-o',str(cls.control),'-ljpeg']+libs,check=True,timeout=60)
        # An original fake public-API provider accepts a deliberately incompatible
        # layout. The observer must forward and refuse without dereferencing it.
        fake = cls.root/'fake.cpp'
        fake.write_text('''#include <cstddef>
extern "C" void jpeg_CreateCompress(void*,int,size_t) {}
extern "C" void jpeg_start_compress(void*,int) {}
extern "C" unsigned jpeg_write_scanlines(void*,void*,unsigned n) { return n; }
extern "C" void jpeg_finish_compress(void*) {}
''')
        caller = cls.root/'abi.cpp'
        caller.write_text('''#include <cstddef>
extern "C" void jpeg_CreateCompress(void*,int,size_t);
extern "C" void jpeg_start_compress(void*,int);
extern "C" unsigned jpeg_write_scanlines(void*,void*,unsigned);
extern "C" void jpeg_finish_compress(void*);
int main() { void *p=reinterpret_cast<void*>(1); jpeg_CreateCompress(p,999,1);
jpeg_start_compress(p,1); if(jpeg_write_scanlines(p,nullptr,3)!=3) return 1;
jpeg_finish_compress(p); }
''')
        subprocess.run(compiler+['-shared',str(fake),'-o',str(cls.root/'libfake.so')],check=True,timeout=60)
        subprocess.run(compiler+[str(caller),'-L'+str(cls.root),'-lfake','-Wl,-rpath,'+str(cls.root),
            '-o',str(cls.root/'abi'),'-Wl,--no-as-needed']+libs,check=True,timeout=60)

    def setUp(self):
        self.log.unlink(missing_ok=True)

    def run_control(self, mode, *, observe=True, output=None):
        env = dict(os.environ)
        if observe: env['LD_PRELOAD'] = str(self.observer)
        args = [str(self.control),mode]+([str(output)] if output else [])
        return subprocess.run(args,env=env,capture_output=True,timeout=20)

    def test_rows_padding_parameters_and_exact_forwarding(self):
        off = self.run_control('normal',observe=False,output=self.root/'off.jpg')
        on = self.run_control('normal',output=self.root/'on.jpg')
        self.assertEqual((off.returncode,on.returncode),(0,0),(off.stderr,on.stderr))
        self.assertEqual(off.stdout,on.stdout)  # Includes errno and floating exception state.
        self.assertEqual((self.root/'off.jpg').read_bytes(),(self.root/'on.jpg').read_bytes())
        expected = hashlib.sha256(bytes(v for y in range(101) for x in range(201)
            for v in ((x*7+y*19)%256,(x*3+y*11)%256,(x*13+y*5)%256))).hexdigest()
        with Image.open(self.root/'on.jpg') as image:
            decoded = hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()
        self.assertEqual(on.stdout.decode().split()[:2],[expected,decoded])
        rows = [line.split('\t') for line in self.log.read_text().splitlines()]
        self.assertTrue(all(len(row)==18 for row in rows))
        final = [row for row in rows if row[3]=='FINISH_RGB']
        self.assertEqual([row[15] for row in final],[expected,decoded])
        encoded = hashlib.sha256((self.root/'on.jpg').read_bytes()).hexdigest()
        self.assertEqual([row[16] for row in final],[encoded,encoded])
        self.assertEqual([row[5] for row in final],['1','0'])
        self.assertEqual([row[6:11] for row in final],[['201','101','101','3','2']]*2)
        self.assertEqual(final[0][11:15],['100','0','221111','1'])
        self.assertFalse(any('LIMIT' in row[3] or 'INCOMPLETE' in row[3] or 'UNSUPPORTED' in row[3] for row in rows))

    def test_small_gray_wide_and_pixel_limit_are_explicit(self):
        for mode in ('small','gray','wide','pixels'):
            with self.subTest(mode=mode):
                self.log.unlink(missing_ok=True)
                result = self.run_control(mode)
                self.assertEqual(result.returncode,0,result.stderr)
                text = self.log.read_text()
                self.assertIn('UNSUPPORTED_GRID_OR_COLOR',text)
                # A gray encoder is not hashed; its forced-RGB decoder may be.
                final = [line.split('\t') for line in text.splitlines() if '\tFINISH_RGB\t' in line]
                self.assertEqual(len(final),1 if mode=='gray' else 0)

    def test_context_and_event_caps_are_explicit_and_forwarded(self):
        for mode,marker,size in [('contexts','LIMIT_CONTEXTS',33),('events','LIMIT_EVENTS',10001)]:
            self.log.unlink(missing_ok=True)
            result = self.run_control(mode)
            self.assertEqual(result.returncode,0,result.stderr)
            lines = self.log.read_text().splitlines()
            self.assertEqual(len(lines),size)
            self.assertEqual(sum(marker in line for line in lines),1)
            self.assertLess(self.log.stat().st_size,512*10001)

    def test_compressed_input_hash_byte_limit_is_explicit(self):
        result = self.run_control('encodedlimit')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('UNSUPPORTED_ENCODED_SIZE',self.log.read_text())
        self.assertNotIn('FINISH_RGB',self.log.read_text())

    def test_incompatible_abi_is_never_dereferenced(self):
        result = subprocess.run([str(self.root/'abi')],env=dict(os.environ,LD_PRELOAD=str(self.observer)),
                                capture_output=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)
        rows = [line.split('\t')[3] for line in self.log.read_text().splitlines()]
        self.assertEqual(rows,['UNSUPPORTED_ABI','UNSUPPORTED_UNTRACKED_START','UNSUPPORTED_UNTRACKED_FINISH'])

    def test_log_failure_cannot_be_silent_success(self):
        self.log.mkdir()
        try: self.assertEqual(self.run_control('normal').returncode,126)
        finally: self.log.rmdir()

    def test_plain_launcher_does_not_require_Qt(self):
        result = subprocess.run(['/bin/true'],env=dict(os.environ,LD_PRELOAD=str(self.observer)),
                                capture_output=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(self.log.exists())

    def test_completed_rows_at_destroy_are_distinct_from_partial_or_finish(self):
        for mode,kind in [('no-finish','RGB_ROWS_AT_DESTROY'),('partial','INCOMPLETE_DESTROY')]:
            self.log.unlink(missing_ok=True)
            off = self.run_control(mode,observe=False)
            on = self.run_control(mode)
            self.assertEqual((off.returncode,on.returncode),(0,0),(off.stderr,on.stderr))
            self.assertEqual(off.stdout,on.stdout)
            rows = [line.split('\t') for line in self.log.read_text().splitlines()]
            outcome = [row for row in rows if row[3]==kind]
            self.assertEqual(len(outcome),1)
            self.assertEqual(outcome[0][5],'0')
            self.assertEqual(outcome[0][15],on.stdout.decode().split()[1] if mode=='no-finish' else '')
            self.assertFalse(any(row[3]=='FINISH_RGB' and row[5]=='0' for row in rows))

    def test_separate_process_sequences_have_explicit_namespaces(self):
        for _ in range(2):
            result = self.run_control('normal')
            self.assertEqual(result.returncode,0,result.stderr)
        rows = [line.split('\t') for line in self.log.read_text().splitlines()]
        processes = {row[17] for row in rows}
        self.assertEqual(len(processes),2)
        for process in processes:
            self.assertGreater(int(process),0)
            ids = [int(row[0]) for row in rows if row[17]==process]
            self.assertEqual(ids,list(range(len(ids))))

    def test_different_original_rows_can_have_identical_lossy_outputs(self):
        outputs = []
        for mode in ('lossy-base','lossy-one'):
            result = self.run_control(mode,output=self.root/(mode+'.jpg'))
            self.assertEqual(result.returncode,0,result.stderr)
            outputs.append(result.stdout.decode().split())
        self.assertNotEqual(outputs[0][0],outputs[1][0])
        self.assertEqual(outputs[0][1],outputs[1][1])
        self.assertEqual((self.root/'lossy-base.jpg').read_bytes(),(self.root/'lossy-one.jpg').read_bytes())
        rows = [line.split('\t') for line in self.log.read_text().splitlines()]
        encoding = [r for r in rows if r[3]=='FINISH_RGB' and r[5]=='1']
        self.assertEqual([r[15] for r in encoding],[r[0] for r in outputs])
        self.assertEqual(encoding[0][16],encoding[1][16])


if __name__ == '__main__': unittest.main()
