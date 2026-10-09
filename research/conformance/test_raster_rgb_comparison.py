# SPDX-License-Identifier: MIT
"""Exact multichannel changes, endpoint deltas and refusal of fitted grids."""
from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from raster_rgb_comparison import compare, confirm_original_page_five


class RgbComparison(unittest.TestCase):
    def test_exact_gray_chromatic_and_full_range_differences(self):
        first = np.array([[[0,0,0], [10,20,30], [255,255,255]],
                          [[64,64,64], [255,0,255], [0,255,0]]], dtype=np.uint8)
        same = compare(first, first)
        self.assertEqual(same['changed_pixels'], 0)
        self.assertEqual(same['maximum_absolute_delta_counts'], {'0':6})
        self.assertEqual(same['first_rgb_sha256'], same['second_rgb_sha256'])
        second = first.copy()
        second[0,0] = [0,1,0]
        second[0,1] = [9,22,28]
        second[1,0] = [65,65,65]
        second[1,1] = [0,255,0]
        result = compare(first, second)
        self.assertEqual(result['changed_pixels'], 4)
        self.assertEqual(result['changed_involving_chromatic_pixels'], 3)
        self.assertEqual(result['changed_gray_in_both'], 1)
        self.assertEqual(result['maximum_absolute_delta_counts'], {'0':2, '1':2, '2':1, '255':1})
        self.assertEqual(result['channel_delta'], [-255,255])
        self.assertEqual(result['per_channel_delta'], [[-255,1], [0,255], [-255,1]])
        self.assertEqual(result['bounds_exclusive'], [0,0,2,2])
        self.assertNotEqual(result['first_rgb_sha256'], result['second_rgb_sha256'])

    def test_wrong_type_shape_empty_and_excessive_grids_are_refused(self):
        good = np.zeros((2,3,3), dtype=np.uint8)
        for bad in [good.astype(float), good.astype(np.int16), good[:, :, 0],
                    good[:0], np.zeros((2,3,4), dtype=np.uint8),
                    np.zeros((1,4*1024*1024+1,3), dtype=np.uint8), []]:
            with self.assertRaises(ValueError): compare(bad, good)
        with self.assertRaisesRegex(ValueError, 'dimensions'): compare(good, good[:1])

    def test_original_marker_inventory_does_not_hide_pixel_differences(self):
        for height in (561, 562):
            for shade, background in ((0,255), (1,254), (67,255), (127,128)):
                page = np.full((height,397,3), background, dtype=np.uint8)
                # Independent fixed projections of the five original marker centers.
                for x in (24,34,45,56,66): page[17:20,x-1:x+2] = shade
                confirm_original_page_five(page)
                original = page.copy()
                page[18,24] = (shade+1) % 128
                confirm_original_page_five(page)
                self.assertEqual(compare(original,page)['changed_pixels'], 1)
                for x, y, rgb in [(66,18,128), (77,18,127), (29,18,127), (24,28,127), (24,18,(0,1,0))]:
                    bad = original.copy(); bad[y,x] = rgb
                    with self.assertRaises(ValueError): confirm_original_page_five(bad)
        for bad in (page[:560], page.astype(float), []):
            with self.assertRaises(ValueError): confirm_original_page_five(bad)


if __name__ == '__main__':
    unittest.main()
