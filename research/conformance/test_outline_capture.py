# SPDX-License-Identifier: MIT
"""Original receipt/source controls; no viewer or corpus in these tests."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH/'cajviewer'))
from outline_capture import TREE_NAME, check_closing, preflight, read_trace, snapshot
from native_navigation_controls import document


def rows():
    return [
        {'tick': 3, 'pid': 5, 'monotonic_ns': '10000000000', 'class': 'QTreeWidget',
         'name_sha256': TREE_NAME, 'model': 'QTreeModel', 'model_present': True,
         'visible': True, 'root_valid': False, 'x': 61, 'y': 187, 'width': 724, 'height': 989,
         'nodes': 0, 'root_rows': 0, 'depth': 0, 'can_fetch_more': False, 'limit': False, 'invalid': False},
        {'tick': 3, 'pid': 5, 'monotonic_ns': '10000000000', 'sample_complete': True, 'tree_count': 1,
         'page_fields': [{'current': 1, 'total': 5}], 'empty_contents_labels': 1},
    ]


class OutlineCaptureTests(unittest.TestCase):
    def test_empty_and_populated_observations(self):
        data = rows()
        self.assertEqual(snapshot(data, 5, 11_000_000_000)['status'], 'EMPTY_DISPLAYED')
        data[0].update(nodes=81, root_rows=13, depth=3)
        data[1]['empty_contents_labels'] = 0
        self.assertEqual(snapshot(data, 5, 11_000_000_000)['status'], 'NONEMPTY_DISPLAYED')

    def test_wrong_hidden_pending_partial_or_ambiguous_is_refused(self):
        for patch in [{'visible': False}, {'model_present': False}, {'root_valid': True}, {'x': 0},
                      {'can_fetch_more': True}, {'limit': True}, {'invalid': True}, {'nodes': True},
                      {'nodes': 4}, {'name_sha256': '0'*64}, {'model': 'UnknownModel'}]:
            data = rows()
            data[0].update(patch)
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                snapshot(data, 5, 11_000_000_000)
        for patch in [{'sample_complete': False}, {'tree_count': 2}, {'empty_contents_labels': 0},
                      {'page_fields': []}, {'page_fields': [{'current': True, 'total': 5}]},
                      {'page_fields': [{'current': 1, 'total': 6}]}]:
            data = rows()
            data[1].update(patch)
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                snapshot(data, 5, 11_000_000_000)
        data = rows()
        data.append(copy.deepcopy(data[0]))
        with self.assertRaises(ValueError):
            snapshot(data, 5, 11_000_000_000)

    def test_latest_sample_cannot_fall_back_to_an_earlier_match(self):
        data = rows()
        later = copy.deepcopy(data)
        for row in later:
            row.update(tick=4, monotonic_ns='11000000000')
        later[0]['visible'] = False
        with self.assertRaises(ValueError):
            snapshot(data+later, 5, 12_000_000_000)
        with self.assertRaises(ValueError):
            snapshot(rows(), 5, 14_000_000_000)

    def test_malformed_and_oversized_traces(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'trees.jsonl'
            path.write_text('{broken\n')
            with self.assertRaises(ValueError):
                read_trace(path)
            path.write_text(' '*2049+'\n')
            with self.assertRaises(ValueError):
                read_trace(path)
            with path.open('wb') as stream:
                stream.truncate(8*1024*1024+1)
            with self.assertRaises(ValueError):
                read_trace(path)

    def test_original_input_profile_and_identity_before_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = document(5, 20)
            sha = hashlib.sha256(data).hexdigest()
            path = root/(sha+'.caj')
            path.write_bytes(data)
            case = {'source_sha256': sha, 'variant': 'HN-B', 'pages': 5}
            preflight([case], root)
            for manifest in [[case, case], [{**case, 'pages': 6}], [{**case, 'pages': True}],
                             [{**case, 'source_sha256': '../bad'}]]:
                with self.subTest(manifest=manifest), self.assertRaises(ValueError):
                    preflight(manifest, root)
            path.write_bytes(data+b'changed')
            with self.assertRaises(ValueError):
                preflight([case], root)

    def test_cleanup_and_oom_are_separate_required_evidence(self):
        state = {'OOMKilled': False, 'Running': True, 'Error': ''}
        closing = [{'exit': 0, 'stdout': json.dumps(state)}, {'exit': 0, 'stdout': '1234'},
                   {'exit': 0}, {'exit': 0}, {'exit': 0}]
        self.assertEqual(check_closing(closing, True, True), 1234)
        for intact, absent in [(False, True), (True, False)]:
            with self.assertRaises(ValueError):
                check_closing(closing, intact, absent)
        closing[0]['stdout'] = json.dumps({**state, 'OOMKilled': True})
        with self.assertRaises(ValueError):
            check_closing(closing, True, True)
        closing[0]['stdout'] = json.dumps(state)
        closing[3]['exit'] = 1
        with self.assertRaises(ValueError):
            check_closing(closing, True, True)


if __name__ == '__main__':
    unittest.main()
