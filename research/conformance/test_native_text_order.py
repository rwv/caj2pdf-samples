# SPDX-License-Identifier: MIT
"""Original controls for scoped native source/PDF glyph-order measurements."""
import struct
import sys
from pathlib import Path
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import native_text_order as order


class Source:
    def __init__(self, data):
        self.data = data
        self.size = len(data)

    def read_at(self, offset, length):
        return self.data[offset:offset + min(length, 3)]


def record(tag, value):
    return struct.pack('<HH', tag, value)


def glyphs(data, variant='C8', mode=2):
    return order.source_glyphs(Source(data), {'text_offset': 0, 'text_length': len(data)}, variant, mode)


class NativeTextOrderTests(unittest.TestCase):
    def test_mode_specific_character_maps(self):
        for code, mode, expected in [(0xa980, 0, 'A'), (0xa99a, 0, 'a'), (0xa3c1, 0, 'A'),
                                     (0xa3c1, 2, 'Ａ'), (0xa3a8, 0, '（'), (0xa3b1, 0, '1'),
                                     (0xa0ad, 2, '－'), (0xaab1, 0, '.'), (0xaab1, 2, '∙'),
                                     (0x9ff5, 0, '／'), (0xa3a7, 0, '’'), (0xa1aa, 0, '—')]:
            self.assertEqual(order.character(code, mode), expected)
        with self.assertRaises(ValueError):
            order.character(0xd6d0, 1)

    def test_atomic_drawing_and_extended_payloads_do_not_create_glyphs(self):
        data = (record(0x8006, 0xa381) + record(10, 0xa0c1) + record(0x8004, 0)
                + record(0x81ff, 1) + record(12, 0xa0c2)
                + record(20, 0xa0c3) + record(0x8004, 0))
        self.assertEqual(glyphs(data), (['C'], 0))
        with self.assertRaises(ValueError):
            glyphs(record(0x8123, 0) + record(0x8004, 0))
        for end in range(1, 12):
            with self.assertRaises(ValueError):
                glyphs(data[:end])

    def test_hnb_terminal_semantics_and_c8_strict_tail(self):
        prefix = record(20, 0xa0c1)
        self.assertEqual(glyphs(prefix + b'\x04\x80', 'HN-B'), (['A'], 0))
        tail = record(20, 0xa0c2) + b'opaque'
        self.assertEqual(glyphs(prefix + record(0x8004, 44) + tail, 'HN-B'), (['A'], len(tail)))
        with self.assertRaises(ValueError):
            glyphs(prefix + record(0x8004, 0) + tail)

    def test_encoded_string_and_image_reference_boundaries(self):
        encoded = record(0x80cc, 0x0104) + struct.pack('<HH', 0xe041, 0xe042)
        image = record(0x810a, 0xd300) + struct.pack('<6H', 10, 20, 30, 40, 0, 3) + b'abc\0'
        ending = record(10, 0xa0c4) + record(0x8004, 0)
        self.assertEqual(glyphs(encoded + image + ending), (['D'], 0))
        for invalid in [encoded[:-1], record(0x80cc, 0x0103) + b'\x04\x80', image[:-1], image[:-1] + b'x']:
            with self.assertRaises(ValueError):
                glyphs(invalid + ending)

    def test_missing_reordered_and_extra_pdf_glyphs_differ(self):
        first, second = b'1 0 0 1 0 0 Tm <0041> Tj\n', b'1 0 0 1 0 0 Tm <0042> Tj\n'
        self.assertEqual(order.semantic_glyphs(first + second), ['A', 'B'])
        for changed in [second + first, first, first + second + first]:
            self.assertNotEqual(order.semantic_glyphs(changed), ['A', 'B'])
        with self.assertRaises(ValueError):
            order.semantic_glyphs(b'(A) Tj')

    def test_encoded_string_allows_only_a_terminal_nul(self):
        ending = record(10, 0xa0c4) + record(0x8004, 0)
        for words in [[], [0xe000], [0xe041, 0xe000], [0xe041, 0xe042]]:
            encoded = record(0x80cc, 0x0102 + len(words)) + struct.pack('<' + 'H' * len(words), *words)
            self.assertEqual(glyphs(encoded + ending), (['D'], 0))
        for words in [[0xe000, 0xe041], [0xe000, 0xe000], [0xe01f], [0xe07f], [0x8004]]:
            encoded = record(0x80cc, 0x0102 + len(words)) + struct.pack('<' + 'H' * len(words), *words)
            with self.assertRaisesRegex(ValueError, 'unmeasured encoded-string payload'):
                glyphs(encoded + ending)

    def test_aligned_image_names_allow_optional_zero_padding(self):
        ending = record(10, 0xa0c4) + record(0x8004, 0)
        for length in [0, 4, 8, 24, 260]:
            reference = record(0x810a, 0xd300) + struct.pack('<6H', 10, 20, 30, 40, 0, length) + b'x' * length
            for padding in [b'', b'\0' * 4]:
                self.assertEqual(glyphs(reference + padding + ending), (['D'], 0))
        reference = record(0x810a, 0xd300) + struct.pack('<6H', 10, 20, 30, 40, 0, 3) + b'abc'
        self.assertEqual(glyphs(reference + b'\0' + ending), (['D'], 0))
        for padding in [b'x', b'']:
            with self.assertRaisesRegex(ValueError, 'invalid image reference padding'):
                glyphs(reference + padding + ending)

    def test_artifacts_and_actual_text_are_distinct(self):
        data = (b'/Artifact BMC 1 0 0 1 0 0 Tm <25BA> Tj EMC\n'
                b'/Span << /ActualText <FEFFE000> >> BDC 1 0 0 1 0 0 Tm <0041> Tj EMC\n')
        self.assertEqual(order.semantic_glyphs(data), ['\ue000'])
        with self.assertRaises(ValueError):
            order.semantic_glyphs(b'/Other BMC 1 0 0 1 0 0 Tm <0041> Tj EMC')

    def test_unicode_map_must_cover_scalars_without_conflicts(self):
        data = b'2 beginbfrange\n<0000> <D7FF> <0000>\n<E000> <FFFF> <E000>\nendbfrange'
        self.assertTrue(order.identity_cmap(data))
        for changed in [data.replace(b'<0000>\n', b'<0001>\n'), data.replace(b'<FFFF>', b'<FFFE>'),
                        data.replace(b'2 begin', b'3 begin'), data + b' usecmap', data + data]:
            self.assertFalse(order.identity_cmap(changed))

    def test_pdf_inflation_is_bounded_and_requires_exact_streams(self):
        class Document:
            payload = zlib.compress(b'original')
            def xref_get_key(self, xref, key):
                return {'Length': ('xref', '2 0 R'), 'Filter': ('name', '/FlateDecode'),
                        'DecodeParms': ('null', 'null')}[key]
            def xref_object(self, xref):
                return str(len(self.payload))
            def xref_stream_raw(self, xref):
                return self.payload
        document = Document()
        self.assertEqual(order.raw_stream(document, 1, 8), b'original')
        for payload, limit in [(document.payload, 7), (document.payload + b'x', 20),
                               (document.payload[:-1], 20), (zlib.compress(b'x' * 10000), 20)]:
            document.payload = payload
            with self.assertRaises(ValueError):
                order.raw_stream(document, 1, limit)


if __name__ == '__main__':
    unittest.main()
