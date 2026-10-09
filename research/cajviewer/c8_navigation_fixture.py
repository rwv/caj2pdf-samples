#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Original page-navigation control: page N contains N separated glyphs."""

import argparse
from pathlib import Path
import struct


def document(pages=12):
    if not 1 <= pages <= 12:
        raise ValueError("navigation control requires 1 through 12 pages")
    header = bytearray(80)
    struct.pack_into("<IIII", header, 0, 200, 0, pages, 2)
    header[16:28] = "北大二扫1.00".encode("gbk")
    # At the measured 150% viewer setting one page exceeds the viewport. A
    # compact control can instead display several pages and clamp its last
    # navigation request; that behavior is retained in the failed pilot.
    struct.pack_into("<HHHH", header, 28, 4652, 4274, 5168, 7546)
    index, content = bytearray(), bytearray()
    for page in range(1, pages + 1):
        words = [0x8002, 0x1084, 0x801D, 0, 0x8067, 6]
        for glyph in range(page):
            row, column = divmod(glyph, 4)
            words.extend((0x8001, 4474 + row * 400,
                          4752 + column * 400, 0xD6D0))
        words.extend((0x8004, page))
        records = struct.pack("<" + "H" * len(words), *words)
        offset = 80 + pages * 20 + len(content)
        index.extend(struct.pack("<IIIII", offset, len(records), 0, 0,
                                 offset + len(records)))
        content.extend(records)
    return bytes(header + index + content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with args.output.open("xb") as output:
        output.write(document())
