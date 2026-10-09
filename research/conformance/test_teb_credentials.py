# SPDX-License-Identifier: MIT
"""Original certificates/containers exercise structural evidence and redaction."""
import base64
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import teb_credentials as c
import teb_inventory as t
from test_teb_inventory import fixture


class TebCredentialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        cls.key_path = Path(cls.directory.name) / 'original.key'
        cert_path = Path(cls.directory.name) / 'original.pem'
        result = subprocess.run(['openssl', 'req', '-new', '-newkey', 'rsa:1024', '-nodes', '-x509',
                                 '-sha256', '-days', '1', '-subj', '/CN=Original TEB control',
                                 '-keyout', str(cls.key_path), '-out', str(cert_path)],
                                capture_output=True, timeout=15)
        if result.returncode:
            raise RuntimeError('original certificate generation failed')
        cls.pem = cert_path.read_text()
        cls.description, cls.public_key = c.certificate(cls.pem)

    def private_operation(self, encoded):
        result = subprocess.run(['openssl', 'pkeyutl', '-decrypt', '-inkey', str(self.key_path),
                                 '-pkeyopt', 'rsa_padding_mode:none'], input=encoded,
                                capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, 'original private-operation control failed')
        self.assertEqual(len(result.stdout), 128)
        return result.stdout

    def container(self, pem=None, password=None):
        data, _ = fixture()
        start = data.index(b'<?xml')
        password = bytes(128) if password is None else password
        value = lambda b: base64.b64encode(b).decode()
        rights = ('<?xml version="1.0" encoding="utf-8"?><right-meta><version>2.1</version>'
                  f'<file-app>{value(b"A" * 80)}</file-app><protect>'
                  '<encrypt meta="1" catalog="1" notes="1" content="1"/>'
                  '<auth><permit><cert><cert>' + (self.pem if pem is None else pem)
                  + '</cert><password>' + value(password) + '</password></cert></permit>'
                  f'<iv>{value(b"I" * 32)}</iv></auth></protect>'
                  f'<rights>{value(b"R" * 496)}</rights></right-meta>\r\n\t').encode()
        return data[:start] + rights + f'startrights {start},{len(rights)}\n'.encode()

    def inspect(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'original.teb'; path.write_bytes(data)
            return c.inventory(path, t.digest(path))

    def test_original_certificate_and_complete_container_are_redacted(self):
        report = self.inspect(self.container())
        self.assertEqual(report['certificate']['public_key_bits'], 1024)
        self.assertEqual(report['base64_decoded_field_bytes'],
                         {'file-app': 80, 'password': 128, 'iv': 32, 'rights': 496})
        text = json.dumps(report)
        for value in (self.pem.splitlines()[1], 'Original TEB control', base64.b64encode(b'I' * 32).decode()):
            self.assertNotIn(value, text)
        self.assertFalse(report['password_public_operation']['type1_padding_like'])
        self.assertFalse(report['password_public_operation']['type2_padding_like'])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'original.teb'; path.write_bytes(self.container())
            run = subprocess.run([sys.executable, c.__file__, str(path), '--sha256', t.digest(path)],
                                 capture_output=True, text=True, timeout=15)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)['source_sha256'], t.digest(path))
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_private_operation_controls_both_public_padding_shapes(self):
        message = b'Original control suffix'
        for kind, byte in ((1, 255), (2, 127)):
            encoded = bytes([0, kind]) + bytes([byte]) * (125 - len(message)) + b'\0' + message
            block = self.private_operation(encoded)
            result = c.public_operation(block, self.public_key)
            self.assertEqual(result['type1_padding_like'], kind == 1)
            self.assertEqual(result['type2_padding_like'], kind == 2)
            self.assertEqual(result['suffix_bytes'], len(message))
            self.assertNotIn(message.decode(), json.dumps(result))

    def test_public_operation_rejects_range_size_and_invalid_padding_neighbors(self):
        n, e = self.public_key
        for block, key in ((bytes(127), (n, e)), (n.to_bytes(128, 'big'), (n, e)),
                           (bytes(128), (n, 3)), (bytes(128), (n << 1, e))):
            with self.assertRaises(ValueError): c.public_operation(block, key)
        for encoded in (b'\0\1' + b'\xff' * 7 + b'\0' + b'A' * 118,
                        b'\0\1' + b'\xff' * 50 + b'X' + b'\xff' * 50 + b'\0' + b'A' * 24,
                        b'\0\2' + b'A' * 7 + b'\0' + b'B' * 118):
            self.assertEqual(len(encoded), 128)
            result = c.public_operation(self.private_operation(encoded), self.public_key)
            self.assertFalse(result['type1_padding_like'] or result['type2_padding_like'])

    def test_certificate_armor_der_and_command_failures_are_bounded(self):
        bad = (self.pem.replace('CERTIFICATE', 'PRIVATE KEY'), self.pem + 'EXTRA',
               self.pem.replace('-----END', '!-----END'), self.pem + self.pem, 'SENSITIVE' * 10000)
        for pem in bad:
            with self.subTest(length=len(pem)), self.assertRaises(ValueError) as error:
                c.certificate(pem)
            self.assertNotIn('SENSITIVE', str(error.exception))
        lines = self.pem.splitlines(); der = base64.b64decode(''.join(lines[1:-1]))
        trailing = '-----BEGIN CERTIFICATE-----\n' + base64.b64encode(der + b'EXTRA').decode() + '\n-----END CERTIFICATE-----'
        with self.assertRaisesRegex(ValueError, 'roundtrip'): c.certificate(trailing)
        with patch.object(c.subprocess, 'run', side_effect=subprocess.TimeoutExpired('openssl', 10)):
            with self.assertRaisesRegex(ValueError, 'timed out'): c.certificate(self.pem)
        with patch.object(c.subprocess, 'run', return_value=subprocess.CompletedProcess('openssl', 1, b'', b'SENSITIVE')):
            with self.assertRaises(ValueError) as error: c.certificate(self.pem)
            self.assertNotIn('SENSITIVE', str(error.exception))

    def test_base64_profile_and_xml_field_ambiguity_fail_closed(self):
        for text, size in (('QQ==\n', 1), ('QR==', 1), ('!!!', 1), ('☃', 1), ('QQ==', 2), (None, 1)):
            with self.assertRaises(ValueError): c.decode_field(text, size)
        self.assertEqual(c.decode_field('QQ==', 1), b'A')
        for data in (self.container(password=bytes(127)),
                     self.container().replace(b'<password>', b'<password></password><password>'),
                     self.container().replace(b'<iv>', b'<iv><extra/>')):
            # Rebuild the measured footer after changing XML length, so field
            # validation, rather than an unrelated extent error, is exercised.
            at = data.index(b'<?xml'); end = data.index(b'startrights ')
            data = data[:end] + f'startrights {at},{end-at}\n'.encode()
            with self.assertRaises(ValueError): self.inspect(data)

    def test_payload_scan_counts_cross_chunk_tokens_once_and_stops_at_extent(self):
        class Bounded(io.BytesIO):
            def read(self, size=-1):
                if not 0 <= size <= t.CHUNK: raise AssertionError('unbounded read')
                return super().read(size)
        for token in c.TOKENS:
            for split in range(1, len(token)):
                data = b'X' * (t.CHUNK - split) + token + b'Y' * 9
                result = c.scan_payload(Bounded(data + token), 0, len(data))
                self.assertEqual(result['literal_token_counts'][token.decode()], 1)
                self.assertEqual(result['scanned_bytes'], len(data))
        with self.assertRaises(ValueError): c.scan_payload(io.BytesIO(b'X'), 0, 2)
        with self.assertRaises(ValueError): c.scan_payload(io.BytesIO(), 1, t.MAX_SOURCE)


if __name__ == '__main__':
    unittest.main()
