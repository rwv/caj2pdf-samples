# SPDX-License-Identifier: MIT
"""Original controls for reviewed selections, framed offsets and site recovery."""
from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile
import unittest

from pdf_source_inventory import digest
from caj_reviewed_framing import frame_selected, substitution_source
from caj_reviewed_selection import check_selection, check_xref, range_hash


class ReviewedSelectionControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.source = self.directory/'original.caj'
        self.reference = self.directory/'reference.pdf'
        body = b'original header'.ljust(64, b'\x00')
        selected, streams = {}, []
        raw = b'original opaque body with 97 0 obj in payload'
        one = b'1 0 obj\n<< /Length '+str(len(raw)).encode()+b' >>\nstream\n'
        data_start = len(body)+len(one)
        end = data_start+len(raw)+len(b'\nendstream\nendobj')
        selected['1'] = {'offset': len(body), 'end': end}
        streams.append({'object': 1, 'offset': len(body), 'data_start': data_start,
                        'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
        body += one+raw+b'\nendstream\nendobj\n'
        two = b'2 0 obj\n<< /Original true /Data 1 0 R >>\nendobj'
        selected['2'] = {'offset': len(body), 'end': len(body)+len(two),
                         'sha256': hashlib.sha256(two).hexdigest()}
        body += two
        self.facts = {'body_range': [64, len(body)], 'selected': selected, 'streams': streams}
        # Keep the full tail, while selection is supplied separately by a
        # reviewed proof. This unselected marker must not become an xref slot.
        body += b'\n97 0 obj\n(null marker in original control tail)\nendobj\n'
        self.source.write_bytes(body)
        self.framing = frame_selected(self.source, self.reference, self.facts)
        self.left = {'obj:1 0 R': {'kind': 'stream', 'raw_bytes': len(raw),
                                  'raw_sha256': hashlib.sha256(raw).hexdigest()},
                     'obj:2 0 R': {'kind': 'value'}}

    def check(self):
        check_selection(self.source, self.reference, self.framing, self.facts, self.left)

    def test_original_complete_tail_and_selection(self):
        self.check()
        with self.reference.open('rb') as stream:
            self.assertEqual(stream.read(9), b'%PDF-1.7\n')
            self.assertEqual(stream.read(self.source.stat().st_size-64), self.source.read_bytes()[64:])

    def test_membership_extent_and_raw_corruption_rejected(self):
        baseline = deepcopy((self.facts, self.left, self.framing))
        mutations = [
            lambda: self.left.pop('obj:1 0 R'),
            lambda: self.left.update({'obj:97 0 R': {'kind': 'value'}}),
            lambda: self.left['obj:1 0 R'].update(raw_bytes=1),
            lambda: self.left['obj:1 0 R'].update(raw_sha256='0'*64),
            lambda: self.facts['selected']['1'].update(offset=65),
            lambda: self.facts['selected']['1'].update(end=10**10),
            lambda: self.facts['selected']['2'].update(sha256='0'*64),
            lambda: self.facts['streams'].clear(),
            lambda: self.facts['streams'][0].update(data_start=0),
            lambda: self.framing.update(reviewed_body_end=65),
            lambda: self.framing.update(synthetic_catalog=1),
            lambda: self.framing.update(xref_size=1000002),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                self.facts, self.left, self.framing = deepcopy(baseline)
                mutate()
                with self.assertRaises(ValueError):
                    self.check()

    def test_bad_xref_refuses_recovery(self):
        original = self.reference.read_bytes()
        for index, changed in enumerate([
            original.replace(b'0000000009 00000 n', b'0000000010 00000 n'),
            original.replace(b'0000000000 00000 f', b'0000000009 00000 n', 1),
            original[:-3],
            original.replace(b'/Root ', b'/RootX '),
        ]):
            with self.subTest(index=index):
                self.reference.write_bytes(changed)
                with self.assertRaises(ValueError):
                    check_xref(self.reference, self.framing, self.facts['selected'])

    def test_range_and_framer_bounds(self):
        for begin, end in [(-1, 10), (10, 10), (0, 10**9)]:
            with self.subTest(begin=begin, end=end), self.assertRaises(ValueError):
                range_hash(self.source, begin, end)
        for index, mutation in enumerate([
            {'body_range': [0, 10**9]}, {'selected': {}},
            {'selected': {'0': {'offset': 64, 'end': 100}}},
            {'selected': {'1000001': {'offset': 64, 'end': 100}}},
            {'selected': {'1': {'offset': 65, 'end': 100}}},
        ]):
            with self.subTest(index=index), self.assertRaises(ValueError):
                frame_selected(self.source, self.directory/f'bad-{index}.pdf', {**self.facts, **mutation})

    def test_original_site_transform_and_negative_controls(self):
        source = self.directory/'sites-original.caj'
        data = b'original prefix\n'
        occurrences = []
        for index in range(13):
            occurrences.append({'source_offset': len(data)})
            data += bytes.fromhex('caa7c2e4')+bytes([65+index])
        data += b'untouched tail'
        source.write_bytes(data)
        transformed = data.replace(bytes.fromhex('caa7c2e4'), bytes.fromhex('b5f4'))
        facts = {'original_sha256': digest(source), 'from_hex': 'caa7c2e4', 'to_hex': 'b5f4',
                 'occurrences': occurrences, 'candidate_bytes': len(transformed),
                 'candidate_sha256': hashlib.sha256(transformed).hexdigest()}
        destination = self.directory/'sites-transformed.caj'
        substitution_source(source, destination, facts)
        self.assertEqual(destination.read_bytes(), transformed)
        mutations = [
            lambda f: f.update(original_sha256='0'*64),
            lambda f: f.update(candidate_sha256='0'*64),
            lambda f: f.update(candidate_bytes=1),
            lambda f: f.update(from_hex='0000'),
            lambda f: f.update(to_hex='00'),
            lambda f: f['occurrences'].pop(),
            lambda f: f['occurrences'][0].update(source_offset=-1),
            lambda f: f['occurrences'][1].update(source_offset=0),
            lambda f: f['occurrences'][0].update(source_offset=17),
            lambda f: f['occurrences'][-1].update(source_offset=len(data)+1),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                changed = deepcopy(facts)
                mutate(changed)
                with self.assertRaises(ValueError):
                    substitution_source(source, self.directory/f'bad-site-{index}.caj', changed)


if __name__ == '__main__':
    unittest.main()
