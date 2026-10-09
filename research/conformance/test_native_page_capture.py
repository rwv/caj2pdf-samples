# SPDX-License-Identifier: MIT
"""Original controls reject stale, partial and adjacent-page paint observations."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cajviewer'))
from native_page_capture import select_page


def record(number=10, **changes):
    # Authored trace, not captured document pixels. 1003 x 1464 is the integer
    # raster for the existing 5168 x 7546 source extent at the observed zoom.
    fields = [str(number), 'pixmap-rect', '0x1', '1', '791', '1014', '123',
              '1003', '1464', '10', '10', '1002', '1464', '0', '0', '1003', '1464',
              '1', '0', '0', '1', '0', '0', '0', '1', '0', '0', '0', '0', '0', '1']
    for index, value in changes.items():
        fields[int(index)] = str(value)
    return '\t'.join(fields)


class PageCaptureTests(unittest.TestCase):
    def test_current_page_wins_over_later_adjacent_page_draw(self):
        expected = select_page([record()], [5168, 7546], 10)
        for later in (record(11, **{'10': 1484}), record(11, **{'10': -1464})):
            self.assertEqual(select_page([record(), later], [5168, 7546], 10), expected)
        self.assertEqual(expected['cache_key'], '000000000000007b')

    def test_stale_small_cropped_scaled_or_wrong_widget_is_not_a_page(self):
        invalid = [record(9), record(**{'3': 2}), record(**{'4': 400}),
                   record(**{'5': 600}), record(**{'7': 388, '8': 466}),
                   record(**{'13': 1}), record(**{'15': 1002}),
                   record(**{'11': 900}), record(**{'12': 900}),
                   record(**{'30': 0}), record(**{'23': 2}), record(**{'24': 0.5})]
        for line in invalid:
            with self.subTest(line=line), self.assertRaises(ValueError):
                select_page([line], [5168, 7546], 10)

    def test_both_observed_scrollbar_states_and_missing_records(self):
        for height in (1014, 1031):
            self.assertEqual(select_page([record(**{'5': height})], [5168, 7546], 10)['event'], 10)
        for lines in ([], ['LIMIT'], [record()[:-2]]):
            with self.assertRaises(ValueError):
                select_page(lines, [5168, 7546], 10)

    def test_newest_valid_event_is_chosen_without_order_assumption(self):
        self.assertEqual(select_page([record(12), record(10)], [5168, 7546], 10)['event'], 12)

    def test_integer_target_intervals_instead_of_fitted_pixmap_tolerance(self):
        # Independent arithmetic: any common scale in [.19412, .19420]
        # truncates 5132 x 7552 to 996 x 1466. A raster can include the final
        # partially covered column and therefore be 997 pixels wide.
        line = record(**{'7': 997, '8': 1466, '11': 996, '12': 1466, '15': 997, '16': 1466})
        self.assertEqual(select_page([line], [5132, 7552], 10)['size'], [997, 1466])
        with self.assertRaises(ValueError):
            select_page([line], [5132, 7452], 10)


if __name__ == '__main__':
    unittest.main()
