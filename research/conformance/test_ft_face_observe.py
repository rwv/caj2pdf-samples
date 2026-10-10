# SPDX-License-Identifier: MIT
"""Original same-family fonts and documented file/memory/stream entry points."""
import hashlib
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'cajviewer'))
sys.path.insert(0, str(ROOT / 'scripts'))
from c8_geometric_font import font
from native_font_faces import bind

CALLER = r'''
#include <ft2build.h>
#include FT_FREETYPE_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned char *buffer;
static unsigned long size;
static unsigned long read_font(FT_Stream stream, unsigned long offset, unsigned char *out, unsigned long count) {
    (void)stream;
    if (offset > size || count > size - offset) return 0;
    if (count) memcpy(out, buffer + offset, count);
    return count;
}
int main(int argc, char **argv) {
    if (argc != 3) return 2;
    FT_Library library; FT_Face face;
    if (FT_Init_FreeType(&library)) return 3;
    FILE *file = fopen(argv[1], "rb");
    if (!file || fseek(file, 0, SEEK_END)) return 4;
    long length = ftell(file);
    if (length <= 0 || length > 1048576 || fseek(file, 0, SEEK_SET)) return 5;
    size = (unsigned long)length; buffer = malloc(size);
    if (!buffer || fread(buffer, 1, size, file) != size) return 6;
    fclose(file);
    if (!strcmp(argv[2], "limit")) {
        for (int i = 0; i < 1001; ++i)
            if (FT_New_Face(library, argv[1], 0, &face) || FT_Done_Face(face)) return 10;
        free(buffer); return FT_Done_FreeType(library);
    }
    FT_Open_Args args = {0}; FT_StreamRec stream = {0}; FT_Error error;
    if (!strcmp(argv[2], "file")) error = FT_New_Face(library, argv[1], 0, &face);
    else if (!strcmp(argv[2], "memory")) error = FT_New_Memory_Face(library, buffer, (FT_Long)size, 0, &face);
    else {
        if (!strcmp(argv[2], "open-file")) { args.flags = FT_OPEN_PATHNAME; args.pathname = argv[1]; }
        else if (!strcmp(argv[2], "open-memory")) { args.flags = FT_OPEN_MEMORY; args.memory_base = buffer; args.memory_size = (FT_Long)size; }
        else { args.flags = FT_OPEN_STREAM; stream.size = size; stream.read = read_font; args.stream = &stream; }
        error = FT_Open_Face(library, &args, 0, &face);
    }
    if (error || FT_Set_Pixel_Sizes(face, 0, 20) || FT_Reference_Face(face) || FT_Done_Face(face)) return 7;
    FT_UInt gid = FT_Get_Char_Index(face, 65);
    if (FT_Load_Glyph(face, gid, FT_LOAD_RENDER)) return 8;
    unsigned checksum = 0;
    for (unsigned y = 0; y < face->glyph->bitmap.rows; ++y)
        for (unsigned x = 0; x < face->glyph->bitmap.width; ++x)
            checksum = checksum * 33 + face->glyph->bitmap.buffer[y * face->glyph->bitmap.pitch + x];
    printf("%u %ld %u\n", gid, face->glyph->advance.x, checksum);
    if (FT_Done_Face(face) || FT_Done_FreeType(library)) return 9;
    free(buffer); return 0;
}
'''


class FaceObserverTests(unittest.TestCase):
    def test_source_hashes_distinguish_same_family_and_preserve_public_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / 'caller.c').write_text(CALLER)
            flags = shlex.split(subprocess.check_output(['pkg-config', '--cflags', 'freetype2', 'openssl'], text=True))
            libs = shlex.split(subprocess.check_output(['pkg-config', '--libs', 'freetype2'], text=True))
            common = ['gcc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', *flags]
            subprocess.run([*common, str(root / 'caller.c'), *libs, '-o', str(root / 'caller')], check=True)
            subprocess.run([*common, '-shared', '-fPIC', '-DFT_OBSERVE_DIRECTORY="' + str(root) + '"',
                str(ROOT / 'cajviewer/ft_face_observe.c'), str(ROOT / 'cajviewer/ft_glyph_observe.c'),
                '-ldl', '-lcrypto', '-o', str(root / 'observer.so')], check=True)
            first, second = root / 'one.ttf', root / 'two.ttf'; font(first, 'Original_CNKI')
            with TTFont(first, recalcTimestamp=False) as changed:
                name = changed.getBestCmap()[65]
                advance, bearing = changed['hmtx'][name]
                changed['hmtx'][name] = (advance + 100, bearing)
                changed.save(second)
            hashes = {hashlib.sha256(p.read_bytes()).hexdigest() for p in (first, second)}
            self.assertEqual(len(hashes), 2)
            for path in (first, second):
                for mode in ('file', 'memory', 'open-file', 'open-memory', 'stream'):
                    with self.subTest(path=path.name, mode=mode):
                        env = dict(os.environ); env.pop('LD_PRELOAD', None)
                        args = [str(root / 'caller'), str(path), mode]
                        baseline = subprocess.check_output(args, env=env, timeout=10)
                        env['LD_PRELOAD'] = str(root / 'observer.so')
                        self.assertEqual(subprocess.check_output(args, env=env, timeout=10), baseline)
                        trace = root / 'ft-faces.tsv'
                        rows = [line.split('\t') for line in trace.read_text().splitlines()]
                        self.assertEqual([r[4] for r in rows], ['open', 'reference', 'done', 'done'])
                        self.assertEqual([r[0] for r in rows], ['0', '1', '2', '3'])
                        self.assertTrue(all(len(r) == 13 and r[8] == '0' for r in rows))
                        self.assertEqual({r[5] for r in rows}, {rows[0][5]})
                        if mode == 'stream':
                            self.assertEqual(rows[0][9:12], ['opaque-stream', '0', 'unmeasured'])
                        else:
                            self.assertEqual(rows[0][11], hashlib.sha256(path.read_bytes()).hexdigest())
                            self.assertEqual(int(rows[0][10]), path.stat().st_size)
                            if mode.endswith('file'):
                                self.assertEqual(bytes.fromhex(rows[0][12]).decode(), str(path))
                            with TTFont(path) as original:
                                glyph_count = original['maxp'].numGlyphs
                            result = bind(trace, root / 'ft-events.tsv', [{'resource': path.name,
                                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                'family': 'Original_CNKI', 'bytes': path.stat().st_size,
                                'freetype_error': 0, 'face_index': 0, 'num_faces': 1,
                                'num_glyphs': glyph_count}])
                            self.assertEqual(result['live_faces_at_trace_end'], 0)
                            self.assertEqual(result['resources'][0]['outer_render_loads'], 1)
                        trace.unlink(); (root / 'ft-events.tsv').unlink()
            env = dict(os.environ); env['LD_PRELOAD'] = str(root / 'observer.so')
            plain = root / 'plain.ttf'; font(plain, 'OriginalPlain')
            subprocess.run([str(root / 'caller'), str(plain), 'file'], env=env,
                           capture_output=True, check=True, timeout=10)
            self.assertFalse((root / 'ft-faces.tsv').exists())
            self.assertFalse((root / 'ft-events.tsv').exists())
            subprocess.run([str(root / 'caller'), str(first), 'limit'], env=env,
                           capture_output=True, check=True, timeout=20)
            self.assertEqual(len((root / 'ft-faces.tsv').read_text().splitlines()), 2000)
            self.assertEqual((root / 'ft-face-limit').read_text(), 'event limit\n')


if __name__ == '__main__':
    unittest.main()
