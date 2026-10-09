# SPDX-License-Identifier: MIT
"""Original preservation/framing controls without external document data."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from test_pdf_source_graphs import original_objects, metadata_records, value
from test_pdf_source_navigation import original_source
from caj_source_navigation import source_navigation
from caj_source_preservation import check_objects


class PreservationControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        path = Path(self.temp.name)/'source.caj'
        path.write_bytes(original_source())
        self.navigation = source_navigation(path)
        self.candidate = original_objects()
        value(self.candidate, 2)['/MediaBox'] = [0, 0, 612, 792]
        value(self.candidate, 9)['/Count'] = 4
        value(self.candidate, 10)['/Count'] = 2
        self.candidate['trailer']['value'].pop('/ID')
        for n in (10, 11, 12, 13):
            value(self.candidate, n)['/Dest'][1:] = ['/XYZ', None, None, None]
        self.source = {k: deepcopy(v) for k, v in self.candidate.items()
                       if k in {f'obj:{n} 0 R' for n in (3, 4, 5, 6, 7, 8)}}
        del value(self.source, 3)['/Parent']
        del value(self.source, 5)['/Parent']

    def check(self):
        return check_objects(self.source, self.candidate, metadata_records(self.source),
                             metadata_records(self.candidate), self.navigation)

    def test_original_framing_and_parent_insertions(self):
        result = self.check()
        self.assertEqual(result['selected_original_objects'], 6)
        self.assertEqual(result['selected_original_streams'], 2)
        self.assertEqual(result['parent_insertions'], 2)
        self.assertEqual(result['added_navigation_objects'], 7)
        self.assertEqual(result['candidate_unresolved_references'], 0)

    def test_changed_and_omitted_content_is_rejected(self):
        base = deepcopy(self.candidate)
        mutations = [
            lambda o: o.pop('obj:8 0 R'),
            lambda o: value(o, 3).update({'/MediaBox': [0, 0, 101, 100]}),
            lambda o: value(o, 3)['/Resources']['/ExtGState'].update({'/GSP1':'8 0 R'}),
            lambda o: value(o, 3).update({'/Contents': '6 0 R'}),
            lambda o: o['obj:4 0 R']['stream'].update({'original_control_body': b'q 1 0 0 1 9 0 cm Q\n'}),
            lambda o: value(o, 3).update({'/Parent': '1 0 R'}),
            lambda o: value(o, 3).update({'/Annots': ['99 0 R']}),
            lambda o: value(o, 10).update({'/Title': 'u:Wrong'}),
        ]
        for i, mutate in enumerate(mutations):
            with self.subTest(i=i):
                self.candidate = deepcopy(base)
                mutate(self.candidate)
                with self.assertRaises((ValueError, KeyError)):
                    self.check()

    def test_generated_framing_cannot_hide_extra_semantics(self):
        base = deepcopy(self.candidate)
        mutations = [
            lambda o: value(o, 1).update({'/OpenAction': ['3 0 R','/Fit']}),
            lambda o: value(o, 1).update({'/PageLabels': {}}),
            lambda o: value(o, 2).update({'/MediaBox': [0, 0, 613, 792]}),
            lambda o: value(o, 2).update({'/Resources': {'/Changed': True}}),
            lambda o: value(o, 2).update({'/Rotate': 90}),
            lambda o: value(o, 9).update({'/Unexpected': True}),
            lambda o: value(o, 10).update({'/C': [1, 0, 0]}),
            lambda o: o['trailer']['value'].update({'/Info': '8 0 R'}),
            lambda o: o['trailer']['value'].update({'/Size': 15}),
            lambda o: o.update({'obj:14 0 R': {'value': {}}}),
            lambda o: o.update({'obj:14 0 R': {'stream': {'dict': {}, 'original_control_body': b''}}}),
        ]
        for i, mutate in enumerate(mutations):
            with self.subTest(i=i):
                self.candidate = deepcopy(base)
                mutate(self.candidate)
                with self.assertRaises((ValueError, KeyError)):
                    self.check()

    def test_existing_parent_change_requires_a_separate_proof(self):
        value(self.source, 3)['/Parent'] = '1 0 R'
        with self.assertRaisesRegex(ValueError, 'unproved original value change'):
            self.check()

    def test_retained_catalog_field_requires_exact_source_proof(self):
        value(self.candidate, 1)['/PageLabels'] = {'/Nums': [0, {'/S': '/D'}]}
        source_property = deepcopy(value(self.candidate, 1)['/PageLabels'])
        with self.assertRaisesRegex(ValueError, 'unmeasured generated Catalog property'):
            self.check()
        check_objects(self.source, self.candidate, metadata_records(self.source),
                      metadata_records(self.candidate), self.navigation,
                      catalog_properties={'/PageLabels': source_property})
        value(self.candidate, 1)['/PageLabels']['/Nums'][0] = 1
        with self.assertRaisesRegex(ValueError, 'source Catalog property changed'):
            check_objects(self.source, self.candidate, metadata_records(self.source),
                          metadata_records(self.candidate), self.navigation,
                          catalog_properties={'/PageLabels': source_property})


if __name__ == '__main__':
    unittest.main()
