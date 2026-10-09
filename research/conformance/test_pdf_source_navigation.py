# SPDX-License-Identifier: MIT
"""Original bounded CAJ records and independently authored output graph."""
from copy import deepcopy
from pathlib import Path
import struct
import tempfile
import unittest
from test_pdf_source_graphs import original_objects, value
from caj_source_navigation import source_navigation, compare


def original_source():
    entries = [('First', 1, 1), ('Child A', 1, 2), ('Child B', 2, 2), ('Second', 2, 1)]
    table = 0x114+308*len(entries)
    data = bytearray(table+24+4)
    data[:4] = b'CAJ\0'
    struct.pack_into('<II', data, 16, 2, table)
    struct.pack_into('<I', data, 0x110, len(entries))
    for i, (title, page, level) in enumerate(entries):
        at = 0x114+308*i
        title = title.encode('gb18030')
        data[at:at+len(title)] = title
        data[at+280] = ord(str(page))
        struct.pack_into('<i', data, at+304, level)
    struct.pack_into('<6I', data, table, table+24, 2, 3, table+26, 2, 5)
    return data


class NavigationControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'original.caj'
        self.data = original_source()
        self.path.write_bytes(self.data)
        self.objects = original_objects()
        value(self.objects, 9)['/Count'] = 4
        value(self.objects, 10)['/Count'] = 2
        for n in (10, 11, 12, 13):
            value(self.objects, n)['/Dest'][1:] = ['/XYZ', None, None, None]

    def test_original_records_and_graph_agree(self):
        result = compare(*source_navigation(self.path), self.objects)
        self.assertEqual((result['pages'], result['outline_nodes']), (2, 4))

    def test_source_bounds_and_invalid_records_are_rejected(self):
        mutations = [
            lambda d: struct.pack_into('<I', d, 0x110, 100001),
            lambda d: struct.pack_into('<I', d, 20, len(d)),
            lambda d: struct.pack_into('<i', d, 0x114+304, 2),
            lambda d: d.__setitem__(0x114+280, ord('3')),
            lambda d: d.__setitem__(0x114+280, ord('X')),
            lambda d: d.__setitem__(0x114, 0xff),
            lambda d: struct.pack_into('<I', d, len(d)-8, 3),
        ]
        for i, mutate in enumerate(mutations):
            with self.subTest(i=i):
                data = bytearray(self.data)
                mutate(data)
                self.path.write_bytes(data)
                with self.assertRaises(ValueError):
                    source_navigation(self.path)
        self.path.write_bytes(self.data[:-2])
        with self.assertRaises(ValueError):
            source_navigation(self.path)

    def test_nonzero_bytes_after_nul_do_not_extend_fields(self):
        self.data[0x114+100] = 0xff
        self.data[0x114+282] = ord('9')
        self.path.write_bytes(self.data)
        result = compare(*source_navigation(self.path), self.objects)
        self.assertEqual(result['outline_nodes'], 4)

    def test_title_page_hierarchy_counts_and_order_are_not_interchangeable(self):
        navigation = source_navigation(self.path)
        mutations = [
            lambda o: value(o, 12).update({'/Title': 'u:Child B'}),
            lambda o: value(o, 12).update({'/Dest': ['5 0 R', '/XYZ', None, None, None]}),
            lambda o: value(o, 12).update({'/Parent': '9 0 R'}),
            lambda o: value(o, 10).update({'/Count': 1}),
            lambda o: value(o, 9).update({'/Count': 3}),
            lambda o: value(o, 9).update({'/Last': '10 0 R'}),
            lambda o: value(o, 2)['/Kids'].reverse(),
        ]
        for i, mutate in enumerate(mutations):
            with self.subTest(i=i):
                objects = deepcopy(self.objects)
                mutate(objects)
                with self.assertRaises(ValueError):
                    compare(*navigation, objects)


if __name__ == '__main__':
    unittest.main()
