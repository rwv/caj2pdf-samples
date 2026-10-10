# SPDX-License-Identifier: MIT
"""Use public FreeType and an original geometric font; no viewer is required."""
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'cajviewer'))
from c8_geometric_font import font

CALLER = r'''
#include <ft2build.h>
#include FT_FREETYPE_H
#include <stdio.h>
#include <string.h>
int main(int argc, char **argv) {
    FT_Library library; FT_Face face;
    if (argc != 3 || FT_Init_FreeType(&library) ||
        FT_New_Face(library, argv[1], 0, &face) || FT_Set_Pixel_Sizes(face, 0, 20)) return 2;
    FT_UInt gid = FT_Get_Char_Index(face, 65);
    if (!strcmp(argv[2], "limit")) {
        for (int i = 0; i < 100001; ++i) FT_Get_Char_Index(face, 65);
    } else {
        FT_Error error = FT_Load_Glyph(face, gid, FT_LOAD_RENDER);
        unsigned checksum = 0;
        for (unsigned y = 0; y < face->glyph->bitmap.rows; ++y)
            for (unsigned x = 0; x < face->glyph->bitmap.width; ++x)
                checksum = checksum * 33 + face->glyph->bitmap.buffer[y * face->glyph->bitmap.pitch + x];
        printf("%u %d %ld %u\n", gid, error, face->glyph->advance.x, checksum);
        printf("%d\n", FT_Load_Glyph(face, (FT_UInt)face->num_glyphs + 100, 0));
    }
    FT_Done_Face(face); FT_Done_FreeType(library); return 0;
}
'''
BRIDGE = r'''
#define _GNU_SOURCE
#include <ft2build.h>
#include FT_FREETYPE_H
#include <dlfcn.h>
FT_Error FT_Load_Glyph(FT_Face face, FT_UInt gid, FT_Int32 flags) {
    FT_Error (*next)(FT_Face, FT_UInt, FT_Int32) = dlsym(RTLD_NEXT, "FT_Load_Glyph");
    FT_Get_Char_Index(face, 66); /* Original deliberate nested public call. */
    return next(face, gid, flags);
}
'''


class ObserverTests(unittest.TestCase):
    def test_forwarding_nested_depth_filter_and_bounded_logging(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'caller.c').write_text(CALLER); (root / 'bridge.c').write_text(BRIDGE)
            flags = shlex.split(subprocess.check_output(['pkg-config', '--cflags', 'freetype2'], text=True))
            libs = shlex.split(subprocess.check_output(['pkg-config', '--libs', 'freetype2'], text=True))
            common = ['gcc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', *flags]
            subprocess.run([*common, str(root / 'caller.c'), *libs, '-o', str(root / 'caller')], check=True)
            subprocess.run([*common, '-shared', '-fPIC', str(root / 'bridge.c'), '-ldl',
                            '-o', str(root / 'bridge.so')], check=True)
            subprocess.run([*common, '-shared', '-fPIC', '-DFT_OBSERVE_DIRECTORY="' + str(root) + '"',
                            str(ROOT / 'cajviewer/ft_glyph_observe.c'), '-ldl',
                            '-o', str(root / 'observe.so')], check=True)
            native = root / 'original.ttf'; font(native, 'HGBZ_CNKI')
            def run(mode='normal', observed=True, source=native):
                env = dict(os.environ); env.pop('LD_PRELOAD', None)
                if observed:
                    env['LD_PRELOAD'] = str(root / 'observe.so') + ':' + str(root / 'bridge.so')
                return subprocess.check_output([str(root / 'caller'), str(source), mode], env=env, timeout=20)
            baseline = run(observed=False)
            self.assertEqual(run(), baseline)
            trace = root / 'ft-events.tsv'
            rows = [line.split('\t') for line in trace.read_text().splitlines()]
            self.assertTrue(all(len(row) == 13 for row in rows))
            self.assertEqual([int(row[0]) for row in rows], list(range(len(rows))))
            self.assertTrue(any(row[4] == 'cmap' and row[7] == '66' and row[12] == '1' for row in rows))
            self.assertTrue(any(row[4] == 'load' and int(row[9]) != 0 and row[12] == '0' for row in rows))
            self.assertTrue(any(row[4] == 'load' and int(row[8]) & 4 and row[9] == '0' for row in rows))
            trace.unlink(); plain = root / 'plain.ttf'; font(plain, 'OriginalPlain')
            run(source=plain); self.assertFalse(trace.exists())
            run(mode='limit')
            with trace.open() as stream:
                self.assertEqual(sum(1 for _ in stream), 100000)
            self.assertEqual((root / 'ft-limit').read_text(), 'event limit\n')


if __name__ == '__main__':
    unittest.main()
