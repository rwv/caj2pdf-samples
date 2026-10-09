# SPDX-License-Identifier: MIT
"""Original containers exercise framing, CRCs, redaction and damage evidence."""
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import teb_inventory as t


def fixture(reverse=False, metadata_url=None):
    # Literal measured framing; the checker never supplies these structures.
    content_name = b'content\\CAJbeef.pdf'
    metadata = (b'<document-meta><structure><content page-count="2"><item>'
                b'<url>' + (content_name if metadata_url is None else metadata_url)
                + b'</url></item></content></structure></document-meta>')
    compressor = zlib.compressobj(wbits=-15)
    compressed = compressor.compress(metadata) + compressor.flush()
    authored = b'Original opaque payload: this is not a decoded PDF.' * 20
    items = [(b'document.xml', compressed, metadata, 8, 2), (content_name, authored, authored, 0, 0)]
    if reverse:
        items.reverse()
    header = bytearray(160); header[:8] = b'TEB\0\x04\0\0\0'
    producer = b'Tongfang Knowledge Network Technology(Beijing) Co., Ltd.'
    header[32:32 + len(producer)] = producer
    locals_, directory = bytearray(), bytearray()
    offsets = []
    for name, data, plain, method, flags in items:
        offset = 16 + len(locals_); crc = zlib.crc32(plain)
        offsets.append(160 + offset + 28)
        locals_ += struct.pack('<4s5H3IH', b'PK\x03\x04', 20, flags, method, 0, 0,
                              crc, len(data), len(plain), len(name)) + data
        directory += struct.pack('<4s6H3I4HI', b'PK\x01\x02', 0, 20, flags, method, 0, 0,
                                 crc, len(data), len(plain), len(name), 0, 0, 0, offset)
        directory += bytes(b ^ i for i, b in enumerate(name))
    data = header + struct.pack('<4s3I', b'PK\x08\x08', 2, len(directory), 16 + len(locals_)) + locals_ + directory
    rights = (b'<?xml version="1.0" encoding="utf-8"?><right-meta><version>2.1</version>'
              b'<protect><encrypt meta="1" catalog="1" notes="1" content="1"/></protect>'
              b'<password>PRIVATE_VALUE</password><cert no-binding="PRIVATE_ATTRIBUTE">'
              b'PRIVATE_CERTIFICATE</cert></right-meta>\r\n\t')
    data += rights + f'startrights {len(data)},{len(rights)}\r\n'.encode()
    return bytes(data), offsets


class TebInventoryTests(unittest.TestCase):
    def inspect(self, data):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'original.teb'; source.write_bytes(data)
            return t.inspect(source, t.digest(source))

    def test_both_entry_orders_crcs_redaction_and_cli(self):
        for reverse in (False, True):
            data, _ = fixture(reverse); report = self.inspect(data)
            self.assertEqual(report['status'], 'INVENTORIED')
            self.assertEqual(report['declared_pages_not_decoded'], 2)
            for entry in report['entries']:
                self.assertTrue(entry['decoded_crc_matches'] if entry['method'] == 8 else entry['raw_crc_matches'])
            self.assertNotIn('PRIVATE_', json.dumps(report))
            self.assertNotIn('content\\CAJbeef.pdf', json.dumps(report))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'original.teb'; path.write_bytes(data)
            result = subprocess.run([sys.executable, t.__file__, str(path), '--sha256', t.digest(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'INVENTORIED')
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_payload_corruption_is_detected_for_both_methods(self):
        data, offsets = fixture()
        for offset in offsets:
            changed = bytearray(data); changed[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                self.inspect(changed)

    def test_directory_local_extent_and_storage_neighbors_are_refused(self):
        data, _ = fixture(); directory = 160 + struct.unpack_from('<I', data, 172)[0]
        for offset, fmt, value in ((164, '<I', 3), (168, '<I', 65537), (172, '<I', len(data)),
                                  (directory, '<I', 0), (directory + 36, '<I', 0),
                                  (directory + 20, '<I', len(data)), (directory + 10, '<H', 99),
                                  (directory + 30, '<H', 1), (176 + 6, '<H', 0)):
            changed = bytearray(data); struct.pack_into(fmt, changed, offset, value)
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                self.inspect(changed)

    def test_xml_and_footer_guards_do_not_reveal_values(self):
        for url in (b'document.xml', b'content\\CAJdead.pdf'):
            with self.assertRaisesRegex(ValueError, 'metadata content reference'):
                self.inspect(fixture(metadata_url=url)[0])
        data, _ = fixture()
        for old, new in ((b'<version>2.1', b'<version>2.2'),
                         (b'meta="1"', b'meta="2"'), (b'startrights ', b'startrights 1')):
            with self.assertRaises(ValueError): self.inspect(data.replace(old, new))
        for value in (b'<!DOCTYPE x [<!ENTITY e "SECRET">]><x>&e;</x>', '<x/>'.encode('utf-16'), b'<x>\xff</x>'):
            with self.assertRaises(ValueError) as error: t.xml_metadata(value, 'x')
            self.assertNotIn('SECRET', str(error.exception))

    def test_deflate_completion_trailing_data_and_limits(self):
        value = b'<original/>'; compressor = zlib.compressobj(wbits=-15)
        raw = compressor.compress(value) + compressor.flush(); crc = zlib.crc32(value)
        report, decoded = t.payload(io.BytesIO(raw), 0, len(raw), 8, len(value), crc)
        self.assertEqual(decoded, value); self.assertTrue(report['decoded_crc_matches'])
        for data, size in ((raw[:-1], len(value)), (raw + b'EXTRA', len(value)), (raw, len(value) + 1), (raw, 65537)):
            with self.assertRaises(ValueError): t.payload(io.BytesIO(data), 0, len(data), 8, size, crc)
        with self.assertRaises(ValueError): t.read(io.BytesIO(b'partial'), 0, 10)
        with self.assertRaises(ValueError): t.read(io.BytesIO(), 0, 65537)

    def test_source_hash_truncation_and_no_output_on_failure(self):
        data, _ = fixture()
        self.assertEqual(self.inspect(data.rstrip(b'\r\n'))['status'], 'INVENTORIED')
        for short in (data[:159], data[:175], data[:-5], data[:400]):
            with self.assertRaises(ValueError): self.inspect(short)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'original.teb'; path.write_bytes(data)
            with self.assertRaisesRegex(ValueError, 'hash mismatch'): t.inspect(path, '0' * 64)
            result = subprocess.run([sys.executable, t.__file__, str(path), '--sha256', '0' * 64], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0); self.assertEqual(result.stdout, '')

    def test_zero_suffix_requires_identical_prefix_and_no_nonzero_tail(self):
        data, _ = fixture(); boundary = data.index(b'<right-meta>')
        with tempfile.TemporaryDirectory() as directory:
            good, bad = Path(directory) / 'good.teb', Path(directory) / 'bad.teb'
            good.write_bytes(data); bad.write_bytes(data[:boundary] + bytes(len(data) - boundary))
            report = t.compare_zero_suffix(bad, good, t.digest(bad), t.digest(good))
            self.assertEqual(report['identical_prefix_bytes'], boundary)
            self.assertEqual(report['zero_suffix_bytes'], len(data) - boundary)
            with self.assertRaises(ValueError): t.inspect(bad, t.digest(bad))
            changed = bytearray(bad.read_bytes()); changed[-1] = 1; bad.write_bytes(changed)
            with self.assertRaises(ValueError): t.compare_zero_suffix(bad, good, t.digest(bad), t.digest(good))
            bad.write_bytes(data)
            with self.assertRaises(ValueError): t.compare_zero_suffix(bad, good, t.digest(bad), t.digest(good))


if __name__ == '__main__':
    unittest.main()
