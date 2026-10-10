# SPDX-License-Identifier: MIT
"""Independent original shapes check measurements without external font data."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib import TTFont

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'cajviewer'))
from c8_geometric_font import font


class ShapeProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory=tempfile.TemporaryDirectory();cls.root=Path(cls.directory.name)
        flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','freetype2','openssl'],text=True))
        cls.probe=cls.root/'probe'
        subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror',
            str(ROOT/'cajviewer/ft_shape_probe.c'),*flags,'-o',str(cls.probe)],check=True,timeout=30)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def run_probe(self,path,*queries,sha=None,success=True):
        expected=hashlib.sha256(path.read_bytes()).hexdigest()
        result=subprocess.run([str(self.probe),str(path),sha or expected,*queries],
                              capture_output=True,text=True,timeout=10)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),expected)
        if not success:
            self.assertNotEqual(result.returncode,0);return result
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertLess(len(result.stdout),1024*1024)
        value=json.loads(result.stdout)
        self.assertEqual(value['font_sha256'],expected)
        return value['glyphs']

    def test_known_rectangles_and_aliases_measure_identically(self):
        p=self.root/'rect.ttf';font(p,'OriginalShapes')
        a,b,c,missing=self.run_probe(p,'u:41','u:31','g:1','u:2019')
        for field in ('gid','bbox_units','advance_units','commands','outline_sha256','rasters'):
            self.assertEqual(a[field],b[field]);self.assertEqual(a[field],c[field])
        self.assertEqual(a['bbox_units'],[0,0,1000,1000])
        self.assertEqual(a['advance_units'],1000)
        for raster in a['rasters']:
            n=raster['ppem'];self.assertEqual(raster['size'],[n,n])
            self.assertEqual(raster['nonzero'],n*n);self.assertEqual(raster['coverage_sum'],255*n*n)
        self.assertEqual(missing,{'query_kind':'u','query':0x2019,'gid':0,'missing':True})

    def test_equal_bounds_and_advances_do_not_hide_different_shapes(self):
        rows=[]
        for family in ('HGHT_CNKI','HGBZ_CNKI'):
            p=self.root/(family+'.ttf');font(p,family,role_markers=True)
            rows.append(self.run_probe(p,'u:41')[0])
        a,b=rows
        self.assertEqual(a['bbox_units'],b['bbox_units'])
        self.assertEqual(a['advance_units'],b['advance_units'])
        self.assertNotEqual(a['outline_sha256'],b['outline_sha256'])
        for x,y in zip(a['rasters'],b['rasters']):
            self.assertEqual(x['size'],y['size'])
            self.assertNotEqual(x['pixels_sha256'],y['pixels_sha256'])

    def test_curve_extrema_and_translated_geometry_are_measured(self):
        p=self.root/'curve.ttf';font(p,'OriginalCurve')
        with TTFont(p,recalcTimestamp=False) as f:
            pen=TTGlyphPen(None);pen.moveTo((0,0));pen.qCurveTo((500,1000),(1000,0));pen.closePath()
            f['glyf']['square']=pen.glyph();f.save(p)
        row=self.run_probe(p,'u:41')[0]
        self.assertEqual(row['bbox_units'],[0,0,1000,500])
        self.assertGreater(row['commands'][2],0)
        p=self.root/'shift.ttf';font(p,'OriginalShift',outline_shift=250)
        row=self.run_probe(p,'u:41')[0]
        self.assertEqual(row['bbox_units'],[0,250,1000,1250])
        for raster in row['rasters']:
            self.assertEqual(raster['bearing'],[0,raster['ppem']*5//4])
        builder=FontBuilder(1000,isTTF=False);builder.setupGlyphOrder(['.notdef','curve'])
        builder.setupCharacterMap({65:'curve'})
        builder.setupHorizontalMetrics({'.notdef':(1000,0),'curve':(1000,0)})
        builder.setupHorizontalHeader(ascent=1000,descent=0)
        builder.setupNameTable({'familyName':'OriginalCubic','styleName':'Regular',
                               'psName':'OriginalCubic','fullName':'OriginalCubic'})
        builder.setupOS2(sTypoAscender=1000,sTypoDescender=0,usWinAscent=1000,usWinDescent=0)
        pen=T2CharStringPen(1000,None);pen.moveTo((0,0))
        pen.curveTo((0,1000),(1000,1000),(1000,0));pen.closePath()
        builder.setupCFF('OriginalCubic',{'FullName':'OriginalCubic','FamilyName':'OriginalCubic','Weight':'Regular'},
                         {'.notdef':T2CharStringPen(1000,None).getCharString(),'curve':pen.getCharString()}, {})
        builder.setupPost();p=self.root/'curve.otf';builder.save(p)
        row=self.run_probe(p,'u:41')[0]
        self.assertEqual(row['bbox_units'],[0,0,1000,750])
        self.assertGreater(row['commands'][3],0)

    def test_wrong_identity_malformed_requests_and_limits_fail(self):
        p=self.root/'limits.ttf';font(p,'OriginalLimits')
        self.run_probe(p,'u:41',sha='a'*64,success=False)
        for query in ('g:9999','g: 1','g:-1','g:1x','u:110000','u:xyz','q:41'):
            with self.subTest(query=query):self.run_probe(p,query,success=False)
        self.run_probe(p,*(['u:41']*129),success=False)


if __name__=='__main__':
    unittest.main()
