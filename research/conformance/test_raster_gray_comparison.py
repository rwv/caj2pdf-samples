# SPDX-License-Identifier: MIT
"""Original discriminators for exact equality and gray-lookup ambiguity."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from raster_gray_comparison import compare, read


def rgb(values):
    return np.repeat(np.array(values,dtype=np.uint8)[:, :, None],3,axis=2)


class GrayComparisonControls(unittest.TestCase):
    def test_equal_and_deterministic_many_to_one_mapping(self):
        original=rgb([[0,10],[10,255]])
        result=compare(original,original.copy())
        self.assertEqual(result['changed_pixels'],0)
        self.assertIsNone(result['bounds_exclusive'])
        self.assertTrue(result['coordinate_independent_lookup_possible'])
        result=compare(original,rgb([[1,1],[1,254]]))
        self.assertEqual(result['changed_pixels'],4)
        self.assertTrue(result['coordinate_independent_lookup_possible'])
        self.assertEqual(result['second_values_with_multiple_first'],1)
        self.assertEqual(result['channel_delta'],[-9,1])

    def test_single_source_gray_has_conflicting_targets(self):
        result=compare(rgb([[0,10],[10,255]]),rgb([[0,9],[11,254]]))
        self.assertFalse(result['coordinate_independent_lookup_possible'])
        self.assertEqual(result['first_values_with_multiple_second'],1)
        self.assertEqual(result['maximum_second_levels_per_first'],2)
        self.assertEqual(result['changed_pixels'],3)
        self.assertEqual(result['first_white_pixels_changed'],1)
        self.assertEqual(result['first_black_pixels_changed'],0)
        self.assertEqual(result['bounds_exclusive'],[0,0,2,2])

    def test_shape_type_and_color_refusals(self):
        original=rgb([[0,10],[10,255]])
        bad=[original.astype(float),original[:1],np.empty((0,2,3),dtype=np.uint8),original[:,:,0]]
        color=original.copy();color[0,0,1]=1;bad.append(color)
        for image in bad:
            with self.subTest(shape=image.shape),self.assertRaises(ValueError):compare(original,image)

    def test_pinned_image_identity_is_required(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'control.png';original=rgb([[0,10],[10,255]]);Image.fromarray(original).save(path)
            sha=hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertTrue(np.array_equal(read(path,sha),original))
            with patch('raster_gray_comparison.MAX_FILE_BYTES', 10):
                with self.assertRaisesRegex(ValueError,'byte bound'):read(path,sha)
            with patch('raster_gray_comparison.MAX_PIXELS', 3):
                with self.assertRaisesRegex(ValueError,'pixel/format bound'):read(path,sha)
            with self.assertRaisesRegex(ValueError,'identity'):read(path,'0'*64)
            Image.fromarray(rgb([[0,10],[11,255]])).save(path)
            with self.assertRaisesRegex(ValueError,'identity'):read(path,sha)


if __name__ == '__main__':unittest.main()
