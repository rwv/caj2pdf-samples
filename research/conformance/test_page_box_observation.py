# SPDX-License-Identifier: MIT
"""Original frame controls detect stale state, wrong grid and changed pixels."""
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from page_box_observation import page_pixels, difference


def frame():
    image=np.full((1200,1600,3),255,dtype=np.uint8)
    for x,y in [(498,244),(1150,244),(498,1088),(1150,1088)]:image[y,x]=209
    return image


class PageBoxObservations(unittest.TestCase):
    def test_full_grid_and_every_pixel_are_compared(self):
        a=page_pixels(frame(),page_field='75/75',zoom_field='80%',page=75,total=75)
        self.assertEqual(a.shape,(843,651,3))
        self.assertEqual(difference(a,a)['changed_pixels'],0)
        b=a.copy();b[0,0]=[0,1,2];b[-1,-1]=[254,255,255]
        result=difference(a,b)
        self.assertEqual(result['changed_pixels'],2)
        self.assertEqual(result['bounds_exclusive'],[0,0,651,843])
        self.assertEqual(result['channel_delta'],[-255,0])
        self.assertNotEqual(result['first_rgb_sha256'],result['second_rgb_sha256'])
        with self.assertRaises(ValueError):difference(a,b[:-1])

    def test_wrong_page_zoom_size_and_frame_corners_are_refused(self):
        good=frame();args=dict(page_field='1/75',zoom_field='80%',page=1,total=75)
        for override in [{'page_field':'2/75'},{'page_field':'1/74'},{'zoom_field':'79%'},{'page':True},{'total':76}]:
            with self.subTest(override=override),self.assertRaises(ValueError):page_pixels(good,**(args|override))
        for image in [good[:1199],good.astype(float)]:
            with self.assertRaises(ValueError):page_pixels(image,**args)
        for x,y in [(498,244),(1150,244),(498,1088),(1150,1088)]:
            bad=good.copy();bad[y,x]=208
            with self.assertRaisesRegex(ValueError,'frame'):page_pixels(bad,**args)

    def test_original_binary_page_markers_reject_stale_content(self):
        a=frame()
        # Independently calculated centers for bits 0, 1 and 6: page 67.
        for x in (548,569,676):a[293:296,x-1:x+2]=0
        args=dict(page_field='67/75',zoom_field='80%',page=67,total=75,markers=True)
        page_pixels(a,**args)
        with self.assertRaisesRegex(ValueError,'identity'):page_pixels(a,**(args|{'page_field':'66/75','page':66}))
        a[294,548]=128
        with self.assertRaisesRegex(ValueError,'marker'):page_pixels(a,**args)

    def test_continuous_profile_covers_full_pages_and_last_page_clamp(self):
        for page, top, bottom, bits in [(2,157,1000,(569,)),(75,325,1168,(548,569,612,676))]:
            image=np.full((1200,1600,3),255,dtype=np.uint8)
            for x,y in [(498,top-1),(1150,top-1),(498,bottom),(1150,bottom)]:image[y,x]=209
            for x in bits:image[top+48:top+51,x-1:x+2]=0
            args=dict(page_field=f'{page}/75',zoom_field='80%',page=page,total=75,markers=True,mode='continuous')
            result=page_pixels(image,**args)
            self.assertEqual(result.shape,(843,651,3))
            self.assertTrue(np.array_equal(result,image[top:bottom,499:1150]))
            with self.assertRaisesRegex(ValueError,'frame'):page_pixels(image,**(args|{'mode':'single'}))
            with self.assertRaises(ValueError):page_pixels(image,**(args|{'total':74}))
            with self.assertRaisesRegex(ValueError,'profile'):page_pixels(image,**(args|{'mode':'fit'}))
            image[top+48:top+51,547:550]=255 if page == 75 else 0
            with self.assertRaisesRegex(ValueError,'identity'):page_pixels(image,**args)


if __name__=='__main__':unittest.main()
