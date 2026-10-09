# SPDX-License-Identifier: MIT
"""Independent inspection of original font-free navigation discriminators."""
from decimal import Decimal
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import pikepdf

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH/'cajviewer'))
from pdf_raster_stage_controls import content, generate, write


class RasterStageControls(unittest.TestCase):
    def test_complete_font_free_graph_and_independent_paint_counts(self):
        with tempfile.TemporaryDirectory() as temp:
            case = generate(Path(temp)/'control')
            path = Path(case['path'])
            self.assertLess(path.stat().st_size, 160*1024)
            subprocess.run(['qpdf','--check',str(path)],check=True,capture_output=True,timeout=20)
            with pikepdf.open(path) as pdf:
                self.assertEqual(len(pdf.pages),6)
                self.assertFalse(any(isinstance(obj,pikepdf.Dictionary) and obj.get('/Type') == '/Font' for obj in pdf.objects))
                for ordinal,page in enumerate(pdf.pages,1):
                    self.assertNotIn('/Font',page.Resources)
                    self.assertEqual(list(map(float,page.MediaBox)),[0,0,595.2756,841.8898])
                    ops=list(pikepdf.parse_content_stream(page)); names=[str(op.operator) for op in ops]
                    rich=ordinal in (1,5,6)
                    self.assertEqual(names.count('re'),ordinal+(256 if rich else 0))
                    self.assertEqual(names.count('m'),256 if rich else 0)
                    self.assertEqual(names.count('l'),512 if rich else 0)
                    self.assertEqual(names.count('Do'),2 if rich else 0)
                    self.assertFalse({'Tj','TJ','BT','Tf'} & set(names))
                    if rich:
                        self.assertEqual({str(x) for x in page.Resources.XObject}, {'/Gray','/Alpha'})
                page=pdf.pages[4];ops=list(pikepdf.parse_content_stream(page))
                grays=[Decimal(str(op.operands[0])) for op in ops if str(op.operator)=='g'][1:-1]
                self.assertEqual(len(grays),256)
                self.assertEqual((grays[0],grays[-1]),(Decimal(0),Decimal(1)))
                self.assertTrue(all(x<y for x,y in zip(grays,grays[1:])))
                matrices=[list(map(int,op.operands)) for op in ops if str(op.operator)=='cm']
                self.assertEqual(matrices,[[512,0,0,64,32,330],[512,0,0,64,32,150]])

    def test_original_image_and_soft_mask_data_are_exact(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'control.pdf';write(path)
            with pikepdf.open(path) as pdf:
                resources=pdf.pages[4].Resources.XObject
                gray,alpha=resources.Gray,resources.Alpha
                for image in (gray,alpha,alpha.SMask):
                    self.assertEqual((int(image.Width),int(image.Height),int(image.BitsPerComponent)),(256,16,8))
                    self.assertFalse(bool(image.Interpolate))
                    self.assertNotIn('/Filter',image)
                    self.assertNotIn('/Matte',image)
                self.assertEqual(str(gray.ColorSpace),'/DeviceGray')
                self.assertEqual(str(alpha.ColorSpace),'/DeviceRGB')
                self.assertEqual(str(alpha.SMask.ColorSpace),'/DeviceGray')
                for y in range(16):
                    self.assertEqual(list(gray.read_bytes()[y*256:(y+1)*256]),list(range(256)))
                self.assertEqual(alpha.SMask.read_bytes(),gray.read_bytes())
                self.assertEqual(alpha.read_bytes(),bytes(12288))
                self.assertNotIn('/SMask',alpha.SMask)

    def test_fixed_bounds_and_preserve_existing_files(self):
        for page in (0,7,True,5.0):
            with self.assertRaises(ValueError):content(page)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'sentinel.pdf';path.write_bytes(b'original')
            with self.assertRaises(FileExistsError):write(path)
            with self.assertRaises(FileExistsError):generate(Path(temp))
            self.assertEqual(path.read_bytes(),b'original')
        with self.assertRaises(ValueError):generate(RESEARCH/'must-not-create-raster-controls')


if __name__ == '__main__':
    unittest.main()
