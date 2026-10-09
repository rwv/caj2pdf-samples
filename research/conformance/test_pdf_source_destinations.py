# SPDX-License-Identifier: MIT
"""Original missing-destination proofs reject live targets and other roles."""
from copy import deepcopy
from decimal import Decimal
import unittest

from caj_accounted_profiles import missing_destinations
from caj_source_accounting import SourceValueParser, Ref


class DestinationControls(unittest.TestCase):
    def setUp(self):
        self.direct = SourceValueParser(b'<</Subtype/Link/BS<</W 0>>/F 4/Rect[0 0 1 1]/Dest[99 0 R/XYZ 8.25 9 0]>>').complete()
        self.values = {1: {'/Type': '/Page'}, 2: self.direct, 3: [Ref(99), '/XYZ', Decimal('8.25'), Decimal(9), Decimal(0)]}

    def test_missing_direct_and_exclusively_used_indirect_array(self):
        proof = missing_destinations(self.values, [1], [2])
        self.assertEqual(proof[2], {'missing_target': 99, 'array_object': None,
                                   'reader_array': [None, '/XYZ', Decimal('8.25'), 9, 0]})
        self.values[2]['/Dest'] = Ref(3)
        self.values[4] = {**self.direct, '/Dest': Ref(3)}
        proof = missing_destinations(self.values, [1], [2, 4])
        self.assertEqual([proof[n]['array_object'] for n in (2, 4)], [3, 3])
        self.assertEqual(self.values[3][0], Ref(99))

    def test_live_target_page_identity_action_and_appearance_refused(self):
        mutations = [lambda v: v.update({99: {'/Type': '/Page'}}),
                     lambda v: v.update({99: None}),
                     lambda v: v[2].update({'/A': {'/S': '/URI', '/URI': b'original'}}),
                     lambda v: v[2].update({'/Subtype': '/Widget'}),
                     lambda v: v[2].update({'/AP': {'/N': Ref(1)}}),
                     lambda v: v[2].update({'/BS': {'/W': Decimal(1)}}),
                     lambda v: v[2].update({'/BS': {'/W': False}}),
                     lambda v: v[2].update({'/Dest': [Ref(99), '/Fit']}),
                     lambda v: v[2].update({'/Dest': [None, '/XYZ', Decimal(0), Decimal(0), Decimal(0)]}),
                     lambda v: v[2].update({'/Dest': [Ref(99), '/XYZ', Ref(5), Decimal(0), Decimal(0)]})]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                values = deepcopy(self.values)
                mutate(values)
                with self.assertRaises(ValueError):
                    missing_destinations(values, [1], [2])
        with self.assertRaises(ValueError):
            missing_destinations(self.values, [1, 99], [2])

    def test_unused_array_cannot_have_an_additional_consumer(self):
        self.values[2]['/Dest'] = Ref(3)
        for extra in [Ref(3), {'/Other': Ref(3)}, {'/Contents': Ref(3)}, {'/Dest': Ref(3)}]:
            with self.subTest(extra=extra):
                values = {**self.values, 4: extra}
                with self.assertRaisesRegex(ValueError, 'consumer/role'):
                    missing_destinations(values, [1], [2])


if __name__ == '__main__':
    unittest.main()
