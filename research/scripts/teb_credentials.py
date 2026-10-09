#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Inventory measured TEB certificate/opaque fields without exporting their values.

This is research, not a decryption API, credential validator or impossibility
classifier. OpenSSL reads the certificate locally; no endpoint is contacted.
"""
import argparse
import base64
import binascii
import json
from pathlib import Path
import re
import subprocess

from teb_inventory import CHUNK, MAX_SOURCE, digest, inspect, read, require, xml_metadata

TOKENS = (b'%PDF-', b' obj', b'endobj', b'stream', b'%%EOF', b'/Type', b'PK\x03\x04')
CERT_PATH = './protect/auth/permit/cert'


def decode_field(text, expected):
    require(isinstance(text, str) and len(text) <= CHUNK, 'field size/type')
    try:
        encoded = text.encode('ascii')
        value = base64.b64decode(encoded, validate=True)
    except (UnicodeEncodeError, binascii.Error):
        raise ValueError('invalid base64 field') from None
    require(base64.b64encode(value) == encoded and len(value) == expected,
            'noncanonical or unmeasured base64 field')
    return value


def openssl(args, data):
    require(len(data) <= CHUNK, 'certificate command input limit')
    try:
        result = subprocess.run(['openssl', *args], input=data, capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError('certificate command unavailable or timed out') from None
    require(result.returncode == 0 and len(result.stdout) <= 2 * CHUNK,
            'certificate command refused or output limit')
    return result.stdout


def certificate(text):
    require(isinstance(text, str) and len(text) <= CHUNK, 'certificate size/type')
    try:
        pem = text.strip().encode('ascii')
    except UnicodeEncodeError:
        raise ValueError('invalid certificate encoding') from None
    armor = re.fullmatch(rb'-----BEGIN CERTIFICATE-----\s*([A-Za-z0-9+/=\r\n]+)\s*'
                         rb'-----END CERTIFICATE-----', pem)
    require(armor is not None, 'unmeasured certificate armor')
    encoded = re.sub(rb'\s', b'', armor[1])
    try:
        der = base64.b64decode(encoded, validate=True)
    except binascii.Error:
        raise ValueError('invalid certificate base64') from None
    require(base64.b64encode(der) == encoded and len(der) <= 8192, 'certificate DER limit/encoding')
    # Round-tripping detects trailing objects/data accepted by a permissive reader.
    require(openssl(['x509', '-inform', 'DER', '-outform', 'DER'], der) == der,
            'certificate DER roundtrip mismatch')
    modulus = openssl(['x509', '-inform', 'DER', '-modulus', '-noout'], der)
    matched = re.fullmatch(rb'Modulus=([A-Fa-f0-9]{256})\r?\n?', modulus)
    require(matched is not None, 'unmeasured certificate public key')
    n = int(matched[1], 16)
    pub = openssl(['x509', '-inform', 'DER', '-pubkey', '-noout'], der)
    description = openssl(['pkey', '-pubin', '-text', '-noout'], pub)
    exponent = re.search(rb'Exponent: (\d+) ', description)
    require(exponent is not None and n.bit_length() == 1024, 'unmeasured RSA public key')
    e = int(exponent[1]); require(e == 65537, 'unmeasured RSA exponent')
    return {'armor': 'CERTIFICATE', 'der_bytes': len(der), 'der_roundtrip': True,
            'public_key_bits': n.bit_length(), 'public_exponent': e,
            'scope': 'Parsed X.509 public key; certificate trust, validity and signature not verified'}, (n, e)


def public_operation(block, key):
    n, e = key
    require(n.bit_length() == 1024 and e == 65537 and len(block) == 128,
            'unmeasured public-operation operands')
    value = int.from_bytes(block, 'big')
    require(value < n, 'public-operation integer out of range')
    encoded = pow(value, e, n).to_bytes(128, 'big')
    end = encoded.find(b'\0', 2)
    type1 = encoded[:2] == b'\0\1' and end >= 10 and all(x == 255 for x in encoded[2:end])
    type2 = encoded[:2] == b'\0\2' and end >= 10  # find() proves nonzero padding.
    return {'input_integer_in_range': True, 'type1_padding_like': type1,
            'type2_padding_like': type2, 'suffix_bytes': len(encoded) - end - 1 if type1 or type2 else None,
            'scope': 'Direct RSA public operation and padding shape only; no decrypted key or signature validation'}


def scan_payload(source, offset, length):
    require(0 <= offset < MAX_SOURCE and 0 < length <= MAX_SOURCE - offset, 'payload scan extent')
    source.seek(offset)
    remaining, position, carry = length, 0, b''
    counts = {token: 0 for token in TOKENS}
    overlap = max(map(len, TOKENS)) - 1
    while remaining:
        block = source.read(min(CHUNK, remaining)); require(block, 'short payload scan')
        combined = carry + block
        for token in TOKENS:
            at = 0
            while (at := combined.find(token, at)) >= 0:
                if at + len(token) > len(carry):
                    counts[token] += 1
                at += 1
        remaining -= len(block); position += len(block); carry = combined[-overlap:]
    return {'scanned_bytes': position, 'length_modulo_16': length % 16,
            'literal_token_counts': {token.decode('ascii'): count for token, count in counts.items()},
            'scope': 'Literal syntax scan only; absence is not an encryption or irrecoverability proof'}


def inventory(path, expected_sha):
    container = inspect(path, expected_sha)
    with path.open('rb') as source:
        root, _ = xml_metadata(read(source, container['rights_offset'],
                                    container['rights_xml_element_extent']), 'right-meta')
        def only(location):
            nodes = root.findall(location)
            require(len(nodes) == 1 and len(nodes[0]) == 0, 'missing or ambiguous credential field')
            return nodes[0].text
        cert, key = certificate(only(CERT_PATH + '/cert'))
        password = decode_field(only(CERT_PATH + '/password'), 128)
        fields = [('file-app', './file-app', 80), ('iv', './protect/auth/iv', 32), ('rights', './rights', 496)]
        sizes = {name: len(decode_field(only(location), size)) for name, location, size in fields}
        sizes['password'] = len(password)
        payload = next(e for e in container['entries'] if e['kind'] == 'declared-pdf')
        scan = scan_payload(source, payload['payload_offset'], payload['stored_bytes'])
    require(digest(path) == expected_sha, 'credential inventory source changed')
    return {'source_sha256': expected_sha, 'source_bytes': container['source_bytes'],
            'source_unchanged': True, 'certificate': cert, 'base64_decoded_field_bytes': sizes,
            'password_public_operation': public_operation(password, key), 'declared_pdf_scan': scan,
            'scope': 'Structural observations and one explicit failed-or-matching hypothesis; actual wrapping and credentials remain unknown'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(inventory(args.source, args.sha256), indent=2))
