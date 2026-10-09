# SPDX-License-Identifier: MIT
"""Independent graph, paint and exact pixel checks for original RGB controls."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import pikepdf

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH/'cajviewer'))
from pdf_rgb_controls import content, generate, image_rows, write


class RgbControls(unittest.TestCase):
    def test_complete_graph_markers_and_paint_inventory(self):
        with tempfile.TemporaryDirectory() as temp:
            case = generate(Path(temp)/'control')
            path = Path(case['cases'][0]['path'])
            self.assertLess(path.stat().st_size, 1024*1024)
            subprocess.run(['qpdf', '--check', str(path)], check=True, capture_output=True, timeout=20)
            with pikepdf.open(path) as pdf:
                self.assertEqual(len(pdf.pages), 6)
                for ordinal, page in enumerate(pdf.pages, 1):
                    self.assertEqual(list(map(float, page.MediaBox)), [0, 0, 595.2756, 841.8898])
                    self.assertNotIn('/Font', page.Resources)
                    ops = list(pikepdf.parse_content_stream(page))
                    names = [str(op.operator) for op in ops]
                    rectangles = [list(map(float, op.operands)) for op in ops if str(op.operator) == 're']
                    self.assertEqual(rectangles[:ordinal], [[32+16*i, 810, 7, 9] for i in range(ordinal)])
                    rich = ordinal in (1, 5, 6)
                    self.assertEqual(len(rectangles), ordinal+(64 if rich else 0))
                    self.assertEqual(names.count('m'), 64 if rich else 0)
                    self.assertEqual(names.count('l'), 128 if rich else 0)
                    self.assertEqual(names.count('Do'), 4 if rich else 0)
                    self.assertEqual(names.count('rg'), 128 if rich else 0)
                    self.assertFalse({'Tj', 'TJ', 'BT', 'Tf'} & set(names))
                    matrices = [list(map(int, op.operands)) for op in ops if str(op.operator) == 'cm']
                    self.assertEqual(matrices, [[240,0,0,120,32,330], [240,0,0,120,315,330],
                                                [240,0,0,120,32,150], [240,0,0,120,315,150]] if rich else [])

    def test_rgb_samples_replication_and_interpolation_flags(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'control.pdf'
            write(path)
            with pikepdf.open(path) as pdf:
                objects = pdf.pages[4].Resources.XObject
                self.assertEqual(set(map(str, objects)), {'/LowLeft', '/LowRight', '/HighLeft', '/HighRight'})
                low, high = objects.LowLeft.read_bytes(), objects.HighLeft.read_bytes()
                self.assertEqual(low, objects.LowRight.read_bytes())
                self.assertEqual(high, objects.HighRight.read_bytes())
                for name, width, height, flag in [('LowLeft',64,32,False), ('LowRight',64,32,True),
                                                   ('HighLeft',512,256,False), ('HighRight',512,256,True)]:
                    image = objects['/'+name]
                    self.assertEqual((int(image.Width),int(image.Height),int(image.BitsPerComponent)), (width,height,8))
                    self.assertEqual(str(image.ColorSpace), '/DeviceRGB')
                    self.assertEqual(bool(image.Interpolate), flag)
                    self.assertEqual(len(image.read_bytes()), width*height*3)
                    for forbidden in ('/Filter','/SMask','/Mask','/Decode'):
                        self.assertNotIn(forbidden, image)
                palette = [b'\x00\x00\x00', b'\xff\x00\x00', b'\x00\xff\x00', b'\x00\x00\xff',
                           b'\x00\xff\xff', b'\xff\x00\xff', b'\xff\xff\x00', b'\xff\xff\xff']
                self.assertEqual(low[:192], b''.join(p*8 for p in palette))
                self.assertEqual(low[8*192:9*192], b''.join(palette)*8)
                for x, rgb in [(0, (0,252,0)), (1, (4,248,68)), (63, (252,0,188))]:
                    self.assertEqual(low[(16*64+x)*3:(16*64+x+1)*3], bytes(rgb))
                self.assertEqual(low[(24*64)*3:(24*64+1)*3], b'\xff\x00\x00')
                self.assertEqual(low[(24*64+1)*3:(24*64+2)*3], b'\xff\xff\xff')
                for y in range(32):
                    row = low[y*192:(y+1)*192]
                    expanded = b''.join(row[x:x+3]*8 for x in range(0,192,3))
                    self.assertEqual(high[y*8*1536:(y+1)*8*1536], expanded*8)

    def test_second_document_changes_only_interpolation_in_parsed_graph(self):
        with tempfile.TemporaryDirectory() as temp:
            cases = generate(Path(temp)/'control')['cases']
            with pikepdf.open(cases[0]['path']) as first, pikepdf.open(cases[1]['path']) as second:
                self.assertEqual(len(first.objects), len(second.objects))
                for left, right in zip(first.objects, second.objects):
                    self.assertEqual(left.objgen, right.objgen)
                    if isinstance(left, pikepdf.Stream):
                        self.assertEqual(left.read_raw_bytes(), right.read_raw_bytes())
                        ld, rd = dict(left.stream_dict), dict(right.stream_dict)
                        if '/Interpolate' in ld:
                            self.assertNotEqual(bool(ld.pop('/Interpolate')), bool(rd.pop('/Interpolate')))
                        self.assertEqual(ld, rd)
                    else:
                        # Compare this object's syntax without recursively walking
                        # its references into the intentionally changed images.
                        self.assertEqual(left.unparse(), right.unparse())
            subprocess.run(['qpdf', '--check', cases[1]['path']], check=True, capture_output=True, timeout=20)

    def test_bounded_rows_and_non_overwrite(self):
        for bad in (0,7,True,5.0):
            with self.assertRaises(ValueError): content(bad)
        for bad in (0,2,True,1.0):
            with self.assertRaises(ValueError): list(image_rows(bad))
        self.assertEqual([len(row) for row in image_rows(8)], [1536]*256)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'sentinel.pdf'
            path.write_bytes(b'unchanged')
            with self.assertRaises(ValueError): write(path, swap_interpolation=1)
            with self.assertRaises(FileExistsError): write(path)
            with self.assertRaises(FileExistsError): generate(Path(temp))
            self.assertEqual(path.read_bytes(), b'unchanged')
        with self.assertRaises(ValueError): generate(RESEARCH/'must-not-create-rgb-controls')


if __name__ == '__main__':
    unittest.main()
