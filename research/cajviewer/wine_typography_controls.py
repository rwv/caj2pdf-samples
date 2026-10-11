#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Original Wine typography, native-alias and advance-only discriminators.

No external font, source document or vendor program is an input. Write generated
controls outside the repository; external resources are not redistributed.
"""
import argparse
import hashlib
import json
from pathlib import Path

from fontTools.ttLib import TTFont

from c8_geometric_font import font
from c8_style_fixture import document


STYLES = {"baseline": 0x1084, "wide": 0x10a5, "highbits": 0x0884, "small": 0x1063}


def typography(style, *, width=6400, height=4800):
    words = []
    for y in (4800, 5400):
        words += [0x8001, y]
        for x, code in zip((4900, 5250, 5600, 5950, 6300, 6650, 7000),
                           (0xd6d0, 0xa0c1, 0xa0cd, 0xa0b1, 0xa3a8, 0xa0b2, 0xa3a9)):
            words += [x, code]
    return document([(style, 0, 6)], codes=(), run_words=words, width=width, height=height)


def alias_control():
    return document([(0x1084, 0, 6)], codes=(0xa0c1, 0xa0cd, 0xa0b1),
                    width=6400, height=4800)


def alias_font(path, variant):
    removed = {"both": (), "native": (65, 77, 49), "unicode": (31908, 37213, 25969),
               "a": (65, 77, 49, 37213, 25969), "m": (65, 77, 49, 31908, 25969),
               "one": (65, 77, 49, 31908, 37213)}[variant]
    font(path, "HGBZ_CNKI")
    with TTFont(path, recalcTimestamp=False) as original:
        for table in original["cmap"].tables:
            if table.isUnicode():
                for code in removed:
                    table.cmap.pop(code, None)
        original.save(path)


def generate(output):
    output.mkdir(parents=True, exist_ok=False)
    for name, style in STYLES.items():
        (output / f"type-{name}.caj").write_bytes(typography(style))
        (output / f"compact-{name}.caj").write_bytes(typography(style, width=4000, height=2400))
    (output / "alias-AM1.caj").write_bytes(alias_control())
    for family in ("HGHT_CNKI", "HGBZ_CNKI", "HGHZ_CNKI"):
        font(output / f"marker-{family}.ttf", family, role_markers=True)
    for variant in ("both", "native", "unicode", "a", "m", "one"):
        alias_font(output / f"alias-{variant}.ttf", variant)
    with TTFont(output / "marker-HGBZ_CNKI.ttf", recalcTimestamp=False) as original:
        for name, (advance, lsb) in list(original["hmtx"].metrics.items()):
            original["hmtx"].metrics[name] = (advance * 2, lsb)
        original.save(output / "double-advance-HGBZ_CNKI.ttf")
    manifest = [{"file": p.name, "bytes": p.stat().st_size,
                 "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                for p in sorted(output.iterdir())]
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="new external directory")
    generate(parser.parse_args().output)
