# SPDX-License-Identifier: MIT
"""Original reader, receipt-tampering, wrapper and full-tail controls."""
from copy import deepcopy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from pdf_source_inventory import digest, probe, frame_caj, inventory, value_hash, decode_kdh
from pdf_source_graphs import verify, check_kdh_reference


def document(*, digit='2', payload=b'10 20 30 40 re f', resource=7, order='3 0 R 5 0 R', omit=False):
    first = b'q /G gs '+payload+b' Q\n'
    second = b'q 20 10 15 25 re f Q\n'
    objects = {
        1: b'<< /Type /Catalog /Pages 2 0 R >>',
        2: ('<< /Type /Pages /Count 2 /Kids ['+order+'] >>').encode(),
        3: ('<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] /Resources '
            '<< /ExtGState << /G '+str(resource)+' 0 R >> >> /Contents 4 0 R >>').encode(),
        4: b'<< /Length '+str(len(first)).encode()+b' >>\nstream\n'+first+b'endstream',
        5: b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] /Resources << >> /Contents 6 0 R >>',
        6: b'<< /Length '+str(len(second)).encode()+b' >>\nstream\n'+second+b'endstream',
        7: ('<< /Type /ExtGState /ca 0.5 /OriginalPrecise 0.1234567890123456789012345678901'+digit+' >>').encode(),
        8: b'<< /Type /ExtGState /ca 0.75 >>',
    }
    if omit:
        del objects[7]
    output = bytearray(b'%PDF-1.7\n')
    offsets = {}
    for number, body in objects.items():
        offsets[number] = len(output)
        output += str(number).encode()+b' 0 obj\n'+body+b'\nendobj\n'
    xref = len(output)
    output += b'xref\n0 9\n0000000000 65535 f \n'
    for number in range(1, 9):
        output += (f'{offsets[number]:010d} 00000 n \n'.encode() if number in offsets
                   else b'0000000000 00000 f \n')
    output += b'trailer\n<< /Size 9 /Root 1 0 R >>\nstartxref\n'+str(xref).encode()+b'\n%%EOF\n'
    return bytes(output)


class SourcePipelineControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def acquire(self, name, **changes):
        directory = self.root/name
        directory.mkdir()
        source, candidate = directory/'source.pdf', directory/'candidate.pdf'
        source.write_bytes(document())
        candidate.write_bytes(document(**changes))
        return probe({'source': str(source), 'source_sha256': digest(source),
                      'pdf': str(candidate), 'pdf_sha256': digest(candidate),
                      'format': 'PDF', 'pages': 2}, directory)

    def test_reader_detects_real_semantic_changes_and_hidden_receipts(self):
        row = self.acquire('identical')
        self.assertEqual(verify(row)['status'], 'VERIFIED_SCOPED_PRESERVATION')
        cases = [('stream', {'payload': b'11 20 30 40 re f'}), ('precision', {'digit': '3'}),
                 ('resource', {'resource': 8}), ('order', {'order': '5 0 R 3 0 R'}),
                 ('omission', {'omit': True})]
        for name, changes in cases:
            with self.subTest(name=name):
                row = self.acquire(name, **changes)
                self.assertEqual(row['status'], 'REQUIRES_REVIEW')
                with self.assertRaises((ValueError, KeyError)):
                    verify(row)
                row.update(missing=[], added=[], changed=[])
                with self.assertRaisesRegex(ValueError, 'difference receipt mismatch'):
                    verify(row)

    def test_raw_artifact_counts_and_metadata_identity(self):
        row = self.acquire('tamper')
        verify(row)
        changed = deepcopy(row)
        changed['source_objects'] += 1
        with self.assertRaisesRegex(ValueError, 'count receipt mismatch'):
            verify(changed)
        changed = deepcopy(row)
        changed['candidate_reader']['json_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'metadata receipt changed'):
            verify(changed)
        raw = next((Path(row['inventory_directory'])/'candidate').glob('raw-*'))
        with raw.open('ab') as stream:
            stream.write(b'changed original control body')
        with self.assertRaisesRegex(ValueError, 'difference receipt mismatch'):
            verify(row)

    def test_full_tail_keeps_late_stream_and_following_object(self):
        pdf = document()
        body = pdf[9:pdf.index(b'xref\n')]+b'63 0 obj\n<< /Length 7 >>\nstream\nq  Q  \nendstream\nendobj\n'
        hint = body.index(b'q  Q  ')+2
        tail = b'64 0 obj\n<< /Original 123 >>\nendobj\n'
        header = bytearray(80)
        header[:4] = b'CAJ\0'
        struct.pack_into('<II', header, 16, 2, 32)
        struct.pack_into('<III', header, 32, 80, hint, 3)
        struct.pack_into('<III', header, 44, 80+hint, 0, 5)
        source, reference = self.root/'source.caj', self.root/'reference.pdf'
        source.write_bytes(header+body+tail)
        framing = frame_caj(source, reference, 2)
        self.assertEqual(framing['body_range'], [80, source.stat().st_size])
        self.assertEqual(framing['table_hint_end'], 80+hint)
        self.assertEqual(reference.read_bytes()[9:9+len(body+tail)], body+tail)
        got = inventory(reference, self.root/'framed')['objects']
        self.assertEqual(got['obj:63 0 R']['raw_bytes'], 7)
        self.assertEqual(got['obj:64 0 R'], {'kind': 'value', 'value_sha256': value_hash({'/Original': 123})})
        baseline = self.root/'baseline.pdf'
        baseline.write_bytes(pdf)
        expected = inventory(baseline, self.root/'baseline')['objects']
        for key, value in expected.items():
            if key != 'trailer':
                self.assertEqual(got[key], value)
        for index, (at, replacement) in enumerate([(16, 0), (16, 100001), (20, 0xffffffff), (36, 0xffffffff)]):
            changed = bytearray(source.read_bytes())
            struct.pack_into('<I', changed, at, replacement)
            invalid = self.root/f'invalid-{index}.caj'
            invalid.write_bytes(changed)
            with self.subTest(index=index), self.assertRaises(ValueError):
                frame_caj(invalid, self.root/f'invalid-{index}.pdf', 2)

    def test_kdh_reference_must_equal_entire_original_decoded_tail(self):
        decoded = document()+b' '*(65536+19)+b'original tail'
        encoded = bytes(value ^ b'FZHMEI'[index % 6] for index, value in enumerate(decoded))
        source, target = self.root/'source.kdh', self.root/'decoded.pdf'
        source.write_bytes(b'KDH 2.00 Copyright(C) 2000 CAJCD'.ljust(254, b'\0')+encoded)
        decode_kdh(source, target)
        check_kdh_reference(source, target)
        self.assertEqual(target.read_bytes(), decoded)
        for index, changed in enumerate([decoded[:-1], decoded+b'extra', decoded[:-1]+b'X']):
            with self.subTest(index=index):
                target.write_bytes(changed)
                with self.assertRaises(ValueError):
                    check_kdh_reference(source, target)

    def test_unrequested_corpus_is_not_run(self):
        script = Path(__file__).resolve().parents[1]/'scripts/pdf_source_preservation.py'
        result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)['status'], 'NOT_RUN')
        self.assertEqual(json.loads(result.stdout)['attempted'], 0)

    def test_canonical_metadata_depth_bound(self):
        value = 1
        for _ in range(128):
            value = [value]
        value_hash(value)
        with self.assertRaisesRegex(ValueError, 'metadata nesting bound'):
            value_hash([value])


if __name__ == '__main__':
    unittest.main()
