# SPDX-License-Identifier: MIT
"""Original counterexamples for individually scoped metadata repairs."""
from copy import deepcopy
from decimal import Decimal
import hashlib
from pathlib import Path
import tempfile
import unittest

from caj_field_proofs import (bounded_bytes, matrix_value, missing_appearance,
                              path_value, path_owners, replace_expected)
from caj_source_preservation import check_objects
import test_pdf_source_preservation as preservation_controls
from test_pdf_source_graphs import metadata_records, value


class FieldControls(unittest.TestCase):
    def test_matrix_is_only_the_measured_malformed_profile(self):
        source = {'/Type': '/Pattern', '/PatternType': 1, '/PaintType': 1, '/TilingType': 1,
                  '/Matrix': [Decimal('0.72'), 0, 0, Decimal('-0.719999'), 'u:-5e-006', 842],
                  '/Resources': {'/ExtGState': {'/Original': '7 0 R'}}}
        expected = matrix_value(source)
        self.assertEqual(expected['/Matrix'], [1, 0, 0, 1, 0, 0])
        self.assertEqual(expected['/Resources'], source['/Resources'])
        self.assertEqual(source['/Matrix'][4], 'u:-5e-006')
        for field, bad in [('/Matrix', [1, 0, 0, 1, 0, 0]),
                           ('/Matrix', [Decimal('0.72'), 0, 0, Decimal('-0.719999'), Decimal('-0.000005'), 842]),
                           ('/Matrix', [Decimal('0.72'), 0, 0, Decimal('-0.719999'), 'u:-6e-006', 842]),
                           ('/PatternType', 2), ('/PaintType', 2), ('/Type', '/XObject')]:
            with self.subTest(field=field, bad=bad), self.assertRaises(ValueError):
                matrix_value({**source, field: bad})

    def test_optional_appearance_needs_missing_target_and_original_role(self):
        original = b'9 0 obj<</Subtype/Link/BS<</W 0>>/AP<</N 99 0 R>>>>endobj'
        source = {'/Subtype': '/Link', '/BS': {'/W': 0}, '/AP': {}, '/Dest': ['3 0 R', '/Fit']}
        expected = missing_appearance(source, 99, original, {})
        self.assertEqual(expected, {'/Subtype': '/Link', '/BS': {'/W': 0}, '/Dest': ['3 0 R', '/Fit']})
        self.assertIn('/AP', source)
        bad = [({**source, '/Subtype': '/Widget'}, original, {}),
               ({**source, '/BS': {'/W': 1}}, original, {}),
               ({**source, '/AP': {'/N': '99 0 R'}}, original, {}),
               (source, original, {'obj:99 0 R': {'stream': {'dict': {}}}}),
               (source, original.replace(b'/N 99', b'/N 98'), {}),
               (source, original.replace(b'/N 99 0 R', b'/N 99 0 R/R 100 0 R'), {}),
               (source, original.replace(b'/AP', b'/AP null/AP'), {})]
        for index, args in enumerate(bad):
            with self.subTest(index=index), self.assertRaises(ValueError):
                missing_appearance(args[0], 99, args[1], args[2])

    def test_literal_path_bytes_never_use_pdf_escape_interpretation(self):
        payload = b'C:\\original\\(unbalanced-control.pdf'
        raw = b'23 0 obj\r('+payload+b')\rendobj'
        expected_hash = hashlib.sha256(payload).hexdigest()
        self.assertEqual(path_value(raw, 23, len(payload), expected_hash), 'b:'+payload.hex())
        for args in [(raw, 24, len(payload), expected_hash), (raw, 23, len(payload)+1, expected_hash),
                     (raw, 23, len(payload), '0'*64), (raw[:-1], 23, len(payload), expected_hash)]:
            with self.subTest(args=args[:3]), self.assertRaises(ValueError):
                path_value(*args)

    def test_path_reference_cannot_hide_a_rendering_or_other_metadata_role(self):
        base = {'obj:3 0 R': {'value': {'/Type': '/Page', '/QITE_pageid': {'/F': '23 0 R'}}},
                'obj:23 0 R': {'value': 'b:010203'}}
        path_owners(base, '23 0 R', [3])
        changes = [
            lambda x: x['obj:3 0 R']['value'].update({'/Contents': '23 0 R'}),
            lambda x: x['obj:3 0 R']['value'].update({'/Other': '23 0 R'}),
            lambda x: x['obj:3 0 R']['value'].update({'/Type': '/Font'}),
            lambda x: x['obj:3 0 R']['value']['/QITE_pageid'].update({'/F': '24 0 R'}),
            lambda x: x.update({'obj:8 0 R': {'value': '23 0 R'}}),
            lambda x: x.update({'obj:8 0 R': {'stream': {'dict': {'/Other': '23 0 R'}}}}),
            lambda x: x.update({'trailer': {'value': {'/Other': '23 0 R'}}}),
        ]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                objects = deepcopy(base)
                change(objects)
                with self.assertRaises(ValueError):
                    path_owners(objects, '23 0 R', [3])

    def test_witness_reads_are_bounded(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)/'original'
            source.write_bytes(b'original witness'+b' '*5000)
            self.assertEqual(bounded_bytes(source, 0, 8), b'original')
            for at, count in [(-1, 2), (0, 0), (0, 4097), (5000, 100), (False, 4)]:
                with self.subTest(at=at, count=count), self.assertRaises(ValueError):
                    bounded_bytes(source, at, count)

    def test_expected_metadata_rewrite_never_authorizes_raw_or_other_value_changes(self):
        # Reuse the original two-page graph, adding one opaque unreferenced
        # Pattern. Only its proved Matrix can change, even after normalization.
        original = preservation_controls.PreservationControls()
        original.setUp()
        self.addCleanup(original.doCleanups)
        source, candidate = deepcopy(original.source), deepcopy(original.candidate)
        dictionary = {'/Type': '/Pattern', '/PatternType': 1, '/PaintType': 1, '/TilingType': 1,
                      '/Matrix': [Decimal('0.72'), 0, 0, Decimal('-0.719999'), 'u:-5e-006', 842]}
        source['obj:14 0 R'] = {'stream': {'dict': dictionary, 'original_control_body': b'original opaque payload'}}
        candidate['obj:14 0 R'] = {'stream': {'dict': matrix_value(dictionary), 'original_control_body': b'original opaque payload'}}
        candidate['trailer']['value']['/Size'] = 15
        left, right = metadata_records(source), metadata_records(candidate)
        events = []
        replace_expected(source, left, 'obj:14 0 R', matrix_value(dictionary), events, 'original control')
        check_objects(source, candidate, left, right, original.navigation)
        self.assertEqual(len(events), 1)
        self.assertEqual(left['obj:14 0 R']['raw_sha256'], right['obj:14 0 R']['raw_sha256'])
        for kind in ('raw', 'resource'):
            changed = deepcopy(candidate)
            if kind == 'raw':
                changed['obj:14 0 R']['stream']['original_control_body'] += b'changed'
            else:
                value(changed, 3)['/Resources']['/OriginalChanged'] = True
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                check_objects(source, changed, left, metadata_records(changed), original.navigation)


if __name__ == '__main__':
    unittest.main()
