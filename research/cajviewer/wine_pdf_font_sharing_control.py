#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Original minimal text/ornament input for Wine PDF resource discriminators.

This control did not reproduce the actual document's failure. It establishes
that shared font resources plus an ornament do not invariably fail.
"""
import argparse
from pathlib import Path

from c8_style_fixture import document


def control():
    return document(
        [(0x10a5, 0, 6)],
        codes=tuple(0xa080 + code for code in b"AM1am234"),
        run_words=[0x8010, 117, 4756, 5103, 9756, 5103],
        first_y=4800,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    path = parser.parse_args().output
    with path.open("xb") as output:
        output.write(control())
