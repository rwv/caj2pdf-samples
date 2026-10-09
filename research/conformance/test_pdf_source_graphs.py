# SPDX-License-Identifier: MIT
"""Original controls for proof rules, with no corpus or vendor dependency."""
from copy import deepcopy
from decimal import Decimal
import hashlib
import tempfile
import unittest
from pathlib import Path

from pdf_source_inventory import value_hash
from pdf_source_graphs import Graph, differences, references, verify_graphs


def original_objects():
    values = {
        1: {'/Type': '/Catalog', '/Pages': '2 0 R', '/Outlines': '9 0 R'},
        2: {'/Type': '/Pages', '/Count': 2, '/Kids': ['3 0 R', '5 0 R']},
        3: {'/Type': '/Page', '/Parent': '2 0 R', '/MediaBox': [0, 0, 100, 100],
            '/Contents': '4 0 R', '/Resources': {'/ExtGState': {'/GSP1': '7 0 R'}}},
        5: {'/Type': '/Page', '/Parent': '2 0 R', '/MediaBox': [0, 0, 100, 100],
            '/Contents': '6 0 R', '/Resources': {}},
        7: {'/CA': Decimal('0.08'), '/ca': Decimal('0.08')},
        8: {'/CA': Decimal('0.08000'), '/ca': Decimal('0.08000')},
        9: {'/Type': '/Outlines', '/First': '10 0 R', '/Last': '11 0 R'},
        10: {'/Title': 'u:First', '/Parent': '9 0 R', '/Next': '11 0 R',
             '/First': '12 0 R', '/Last': '13 0 R', '/Dest': ['3 0 R', '/Fit']},
        11: {'/Title': 'u:Second', '/Parent': '9 0 R', '/Prev': '10 0 R', '/Dest': ['5 0 R', '/Fit']},
        12: {'/Title': 'u:Child A', '/Parent': '10 0 R', '/Next': '13 0 R', '/Dest': ['3 0 R', '/Fit']},
        13: {'/Title': 'u:Child B', '/Parent': '10 0 R', '/Prev': '12 0 R', '/Dest': ['5 0 R', '/Fit']},
    }
    objects = {'obj:'+str(n)+' 0 R': {'value': v} for n, v in values.items()}
    for n in (4, 6):
        objects['obj:'+str(n)+' 0 R'] = {'stream': {'dict': {}, 'original_control_body': b'q Q\n'}}
    objects['trailer'] = {'value': {'/Root': '1 0 R', '/Size': 14,
                                   '/ID': ['b:'+'01'*16, 'b:'+'02'*16]}}
    return objects


def metadata_records(objects):
    result = {}
    for key, wrapper in objects.items():
        if 'value' in wrapper:
            result[key] = {'kind': 'value', 'value_sha256': value_hash(wrapper['value'])}
        else:
            stream = wrapper['stream']
            body = stream['original_control_body']
            result[key] = {'kind': 'stream', 'value_sha256': value_hash(stream['dict']),
                           'raw_sha256': hashlib.sha256(body).hexdigest(), 'raw_bytes': len(body)}
    return result


def value(objects, number):
    return objects['obj:'+str(number)+' 0 R']['value']


class ProofControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.reference = Path(self.temp.name)/'source.pdf'
        self.reference.write_bytes(b'%PDF-1.7\nstartxref\n42\n%%EOF\n')
        self.a = original_objects()
        self.b = deepcopy(self.a)

    def check(self):
        left, right = metadata_records(self.a), metadata_records(self.b)
        missing, added, changed = differences(left, right)
        row = {'source_sha256': 'original-control', 'pdf_sha256': 'original-candidate', 'format': 'PDF',
               'pages': 2, 'source_objects': len(left), 'source_streams': 2,
               'source_reader': {'exit': 0}, 'candidate_reader': {'exit': 0},
               'missing': missing, 'added': added, 'changed': changed}
        return verify_graphs(row, [self.a, self.b], self.reference)

    def test_identical_original(self):
        result = self.check()
        self.assertEqual(result['pages'], 2)
        self.assertEqual(result['outline_nodes'], 4)
        self.assertEqual(result['unresolved_references'], 0)
        self.assertEqual(result['events'], [])

    def test_proved_repairs(self):
        del value(self.a, 3)['/Parent']
        del value(self.a, 11)['/Prev']
        value(self.a, 9)['/Last'] = '10 0 R'
        value(self.b, 3)['/Resources']['/ExtGState']['/GSP1'] = '8 0 R'
        result = self.check()
        self.assertEqual({r['object'] for r in result['events']}, {'obj:3 0 R', 'obj:9 0 R', 'obj:11 0 R'})

    def test_precise_alpha_change_is_rejected(self):
        value(self.b, 3)['/Resources']['/ExtGState']['/GSP1'] = '8 0 R'
        for objects in (self.a, self.b):
            value(objects, 8)['/ca'] = Decimal('0.08000000000000000000000000000001')
        with self.assertRaisesRegex(ValueError, 'non-equivalent alpha'):
            self.check()

    def test_extra_extgstate_property_is_rejected(self):
        value(self.b, 3)['/Resources']['/ExtGState']['/GSP1'] = '8 0 R'
        for objects in (self.a, self.b):
            value(objects, 8)['/BM'] = '/Multiply'
        with self.assertRaisesRegex(ValueError, 'non-alpha'):
            self.check()

    def test_semantic_mutations_are_rejected(self):
        mutations = [
            lambda b: value(b, 2)['/Kids'].reverse(),
            lambda b: value(b, 2).update({'/Count': 1}),
            lambda b: value(b, 3).update({'/Parent': '1 0 R'}),
            lambda b: value(b, 3).update({'/MediaBox': [0, 0, 101, 100]}),
            lambda b: value(b, 11).update({'/Prev': '12 0 R'}),
            lambda b: value(b, 9).update({'/Last': '10 0 R'}),
            lambda b: value(b, 9).update({'/First': '11 0 R'}),
            lambda b: value(b, 11).update({'/Parent': '10 0 R'}),
            lambda b: value(b, 11).update({'/Title': 'u:Changed'}),
            lambda b: value(b, 11).update({'/Dest': ['3 0 R', '/Fit']}),
            lambda b: value(b, 11).update({'/Next': '10 0 R'}),
            lambda b: value(b, 7).update({'/Prev': '8 0 R'}),
            lambda b: b.pop('obj:8 0 R'),
            lambda b: b.update({'obj:14 0 R': {'value': 1}}),
            lambda b: b['obj:4 0 R']['stream'].update({'original_control_body': b'q q Q Q\n'}),
            lambda b: b['obj:4 0 R']['stream']['dict'].update({'/Filter': '/FlateDecode'}),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                self.b = deepcopy(self.a)
                mutate(self.b)
                with self.assertRaises((ValueError, KeyError)):
                    self.check()

    def test_dangling_or_null_reference_is_not_preservation(self):
        for target in ('99 0 R', '8 0 R'):
            with self.subTest(target=target):
                self.a = original_objects()
                value(self.a, 3)['/Resources']['/Unresolved'] = target
                if target == '8 0 R':
                    self.a['obj:8 0 R'] = {'value': None}
                self.b = deepcopy(self.a)
                with self.assertRaisesRegex(ValueError, 'missing or null'):
                    self.check()

    def test_second_identifier_and_original_xref_pointer(self):
        self.b['trailer']['value']['/ID'][1] = 'b:'+'03'*16
        self.b['trailer']['value']['/Prev'] = 42
        self.assertEqual(len(self.check()['events']), 1)
        for wrong in (41, 43, True):
            self.b['trailer']['value']['/Prev'] = wrong
            with self.assertRaisesRegex(ValueError, 'incremental Prev'):
                self.check()

    def test_first_identifier_is_preserved(self):
        self.b['trailer']['value']['/ID'][0] = 'b:'+'03'*16
        with self.assertRaisesRegex(ValueError, 'first document ID'):
            self.check()

    def test_only_xref_stream_framing_can_be_removed(self):
        self.a['trailer']['value'].update({'/Type': '/XRef', '/W': [1, 4, 2], '/Filter': '/FlateDecode'})
        self.assertEqual(len(self.check()['events']), 1)
        del self.a['trailer']['value']['/Type']
        with self.assertRaisesRegex(ValueError, 'non-xref trailer'):
            self.check()

    def test_recursive_and_long_indirect_metadata_is_rejected(self):
        for count in (1, 17):
            with self.subTest(count=count):
                objects = original_objects()
                for i in range(count):
                    objects[f'obj:{100+i} 0 R'] = {'value': f'{100+i+1} 0 R'}
                objects[f'obj:{99+count} 0 R'] = {'value': '100 0 R' if count == 1 else {}}
                graph = Graph(objects)
                with self.assertRaisesRegex(ValueError, 'recursive/long scalar'):
                    graph.resolve('100 0 R')

    def test_metadata_depth_is_bounded(self):
        nested = '1 0 R'
        for _ in range(129):
            nested = [nested]
        with self.assertRaisesRegex(ValueError, 'nesting bound'):
            list(references(nested))


if __name__ == '__main__':
    unittest.main()
