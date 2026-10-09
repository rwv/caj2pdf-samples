# SPDX-License-Identifier: MIT
"""Original negative controls for unregistered raster difference measurements."""
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from native_raster_comparison import metrics


class RasterComparisonTests(unittest.TestCase):
    def test_displacement_is_retained_without_registration(self):
        first, second = np.full((16, 16), 255), np.full((16, 16), 255)
        first[1, 1], second[5, 4] = 0, 0
        result = metrics(first, second)
        self.assertEqual(result['common_mask_differences'], 2)
        self.assertEqual(result['source_to_pdf']['distance_quantiles']['max'], 5)
        self.assertEqual(result['pdf_to_source']['distance_gt_4'], 1)
        self.assertEqual(metrics(first, first)['common_grayscale_differences'], 0)

    def test_blank_and_nonoverlapping_content_are_not_success(self):
        first, second = np.full((16, 16), 255), np.full((17, 16), 255)
        second[16, 5] = 0
        result = metrics(first, second)
        self.assertEqual(result['common_grayscale_differences'], 0)
        self.assertEqual(result['pdf_nonoverlapping_ink'], 1)
        self.assertTrue(result['pdf_to_source']['opposite_is_blank'])
        self.assertEqual(result['status'], 'MEASURED_NO_FIDELITY_VERDICT')


if __name__ == '__main__':
    unittest.main()
