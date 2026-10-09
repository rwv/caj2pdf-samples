# SPDX-License-Identifier: MIT
"""Original controls reject stale, partial and adjacent-page paint observations."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cajviewer'))
from native_page_capture import navigation_route, observe, select_page


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
    def test_navigation_defaults_and_explicit_order(self):
        self.assertEqual(navigation_route(12, None), tuple(range(1, 13)))
        self.assertEqual(navigation_route(12, [5]), (5,))
        self.assertEqual(navigation_route(12, [3, 5]), (3, 5))
        self.assertEqual(navigation_route(12, [10, 5]), (10, 5))

    def test_invalid_routes_fail_before_io_or_container_launch(self):
        for route in ([], [0], [13], [5, 5], [True], ['5'], list(range(1, 14))):
            with self.subTest(route=route), patch('native_page_capture.digest') as digest, \
                    patch('native_page_capture.subprocess.run') as run:
                with self.assertRaises(ValueError):
                    observe(SimpleNamespace(route=route), {'pages': 12})
                digest.assert_not_called()
                run.assert_not_called()
        for count in (0, 13, True, '12'):
            with self.assertRaises(ValueError):
                navigation_route(count, None)

    def test_cli_preflights_every_case_before_creating_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps([{'pages': 12, 'source_sha256': 'a' * 64},
                                            {'pages': 5, 'source_sha256': 'b' * 64}]))
            script = Path(__file__).resolve().parents[1] / 'cajviewer/native_page_capture.py'
            result = subprocess.run([sys.executable, str(script), str(manifest), str(root / 'output'),
                '--observer', str(root / 'absent.so'), '--image', 'sha256:' + 'c' * 64,
                '--route', '6'], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn('distinct in-range pages', result.stderr)
            self.assertFalse((root / 'output').exists())

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
