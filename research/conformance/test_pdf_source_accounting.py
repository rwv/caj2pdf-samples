# SPDX-License-Identifier: MIT
"""Original raw-source syntax, complete-body and interruption controls."""
from copy import deepcopy
from decimal import Decimal
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest

from caj_source_accounting import SourceValueParser, Ref, account_source, source_references


def original(directory, *, page_extra=b'', gap=b'\r\n3 \r\n', tail=b'\r\n', stream_type=b''):
    source = directory/'original.caj'
    raw = b'opaque stream: 99 0 obj << /Type /Page >> endobj; 88 0 R'
    bodies = {
        1: b'1 0 obj <</Type/Page/Contents 2 0 R'+page_extra+b'>> endobj',
        2: b'2 0 obj <</Length 3 0 R'+stream_type+b'>>\nstream\n'+raw+b'\nendstream\nendobj',
        3: b'3 0 obj '+str(len(raw)).encode()+b' endobj',
        4: b'4 0 obj <</Subtype/Link/BS<</W 0>>/Dest[99 0 R/XYZ 0 0 0]>> endobj',
        5: b'5 0 obj (endobj (99 0 obj) 88 0 R) endobj',
    }
    data = bytearray(64)
    data[:4] = b'CAJ\0'
    struct.pack_into('<II', data, 16, 1, 32)
    selected, streams, left = {}, [], {}
    for number, body in bodies.items():
        at = len(data)
        selected[str(number)] = {'offset': at, 'end': at+len(body)}
        data.extend(body+b'\n')
        left[f'obj:{number} 0 R'] = {'kind': 'value'}
        if number == 2:
            item = {'object': 2, 'offset': at, 'end': at+len(body), 'data_start': at+body.index(b'stream\n')+7,
                    'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
            streams.append(item)
            left['obj:2 0 R'] = {'kind': 'stream', 'raw_bytes': len(raw), 'raw_sha256': item['sha256']}
    duplicate = len(data)
    data.extend(bodies[1]+b'\n')
    omitted = len(data)
    data.extend(bodies[2][:21]+b'\r\n')
    next_header = len(data)
    data.extend(bodies[3]+b'\n'+gap)
    last = len(data)
    data.extend(bodies[1]+tail)
    struct.pack_into('<III', data, 32, 64, len(data)-64, 1)
    facts = {'body_range': [64, len(data)], 'selected': selected, 'streams': streams,
             'duplicates': [{'object': 1, 'first_offset': selected['1']['offset'], 'duplicate_offset': duplicate, 'bytes': len(bodies[1])},
                            {'object': 3, 'first_offset': selected['3']['offset'], 'duplicate_offset': next_header, 'bytes': len(bodies[3])},
                            {'object': 1, 'first_offset': selected['1']['offset'], 'duplicate_offset': last, 'bytes': len(bodies[1])}],
             'omitted': [{'object': 2, 'offset': omitted, 'apparent_next_header': next_header}]}
    source.write_bytes(data)
    return source, facts, left


class SourceSyntaxControls(unittest.TestCase):
    def test_comments_names_strings_and_reference_roles(self):
        data = b'<</N/\xff#80/Ref 7 0% ignored 8 0 R\rR/S(endobj (8 0 obj) 9 0 R)/A[true null 2.5]>>'
        parsed = SourceValueParser(data).complete()
        self.assertEqual(parsed['/N'], '/\xff\x80')
        self.assertEqual(parsed['/Ref'], Ref(7))
        self.assertEqual(list(source_references(parsed)), [(7, ('/Ref',))])
        self.assertEqual(parsed['/A'], [True, None, Decimal('2.5')])

    def test_strict_syntax_and_bounds(self):
        for count in (513, 4096):
            self.assertEqual(len(SourceValueParser(b'['+b'0 '*count+b']').complete()), count)
        cases = [b'['+b'0 '*4097+b']', b' '*16385, b'/bad#x0', b'/' + b'x'*129,
                 b'<< /A 1 /A 2 >>', b'<<'+b''.join(b'/A'+str(n).encode()+b' 1 ' for n in range(65))+b'>>',
                 b'['*66+b'0'+b']'*66, b'(unterminated', b'7 1 R', b'1 endobj', b'[1', b'<0z>']
        for index, data in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(ValueError):
                SourceValueParser(data).complete()


class SourceAccountingControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def test_complete_body_opaque_stream_and_interrupted_counterparts(self):
        source, facts, left = original(self.directory)
        values, proof = account_source(source, facts, left)
        self.assertEqual(set(values), {1, 2, 3, 4, 5})
        self.assertEqual(proof['complete_duplicates'], 3)
        self.assertEqual(proof['proper_prefixes'], 1)
        self.assertEqual(proof['partial_headers'][0]['role'], 'validated indirect stream Length only')
        self.assertEqual(proof['unexplained_source_bytes'], 0)
        self.assertEqual(list(source_references(values[5])), [])
        source, facts, left = original(self.directory, gap=b'\r\n1 0 ob\r\n')
        self.assertEqual(account_source(source, facts, left)[1]['partial_headers'][0]['role'], 'source table Page')

    def test_corrupt_duplicate_prefix_or_stream_refused(self):
        for location in ('duplicate', 'prefix', 'stream'):
            with self.subTest(location=location):
                source, facts, left = original(self.directory)
                offset = {'duplicate': facts['duplicates'][0]['duplicate_offset']+15,
                          'prefix': facts['omitted'][0]['offset']+15,
                          'stream': facts['streams'][0]['data_start']+3}[location]
                with source.open('r+b') as file:
                    file.seek(offset); byte = file.read(1); file.seek(offset); file.write(bytes([byte[0]^1]))
                with self.assertRaises(ValueError):
                    account_source(source, facts, left)

    def test_wrong_extents_membership_lengths_and_overlap_refused(self):
        mutations = [lambda f,l: f['body_range'].__setitem__(0,65),
                     lambda f,l: f['body_range'].__setitem__(1,f['body_range'][1]-1),
                     lambda f,l: f['selected'].pop('5'), lambda f,l: l.pop('obj:5 0 R'),
                     lambda f,l: f['duplicates'].clear(),
                     lambda f,l: f['duplicates'][0].update(duplicate_offset=64),
                     lambda f,l: f['omitted'][0].update(apparent_next_header=f['omitted'][0]['apparent_next_header']-1),
                     lambda f,l: f['streams'][0].update(bytes=f['streams'][0]['bytes']-1),
                     lambda f,l: l['obj:2 0 R'].update(raw_sha256='0'*64),
                     lambda f,l: f['streams'].append(deepcopy(f['streams'][0])),
                     lambda f,l: f['selected']['2'].update(end=f['selected']['2']['end']+1)]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                source, facts, left = original(self.directory)
                mutate(facts,left)
                with self.assertRaises((ValueError,KeyError)):
                    account_source(source,facts,left)
        source, facts, left = original(self.directory)
        # Keep every repeated scalar consistent, but make all declared Lengths
        # wrong. A raw extent hash alone must not authorize this framing.
        data = source.read_bytes().replace(b'3 0 obj 56 endobj',b'3 0 obj 55 endobj')
        self.assertNotEqual(data, source.read_bytes())
        source.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'declared source Length'):
            account_source(source,facts,left)

    def test_unknown_gaps_hidden_metadata_and_unanchored_headers_refused(self):
        cases = [{'gap': b'garbage\r\n'}, {'gap': b'\r\n9 \r\n'}, {'gap': b'\r\n3 0 obj\r\n'},
                 {'gap': b'\r\n5 \r\n'}, {'page_extra': b'/Other 3 0 R'},
                 {'tail': b'\r\n3 \r\n'}, {'stream_type': b'/Type/ObjStm'}, {'stream_type': b'/Type/XRef'}]
        for index, kwargs in enumerate(cases):
            with self.subTest(index=index):
                source, facts, left = original(self.directory, **kwargs)
                with self.assertRaises(ValueError):
                    account_source(source,facts,left)


if __name__ == '__main__':
    unittest.main()
