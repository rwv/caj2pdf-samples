#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Write original descriptor-only JPEG orientation pairs outside the repository."""

import argparse
import hashlib
import json
from pathlib import Path
import struct

import c8_image_fixture as c8
import hna_image_fixture as hna


def controls():
    payload = c8.jpeg(8)
    for variant in ("hna", "c8"):
        if variant == "hna":
            data = bytearray(hna.document(
                payload, x=400, y=500, width=3500, height=2500,
                prefix_size=(6400, 4800)))
            struct.pack_into("<HH", data, 168, 6400, 4800)
            index = 348
        else:
            data = bytearray(c8.document(
                payload, dx=370, dy=460, dw=3420, dh=2450,
                page_size=(6400, 4800)))
            index = 80
        text_at, text_length = struct.unpack_from("<II", data, index)
        descriptor = text_at + text_length
        for kind in (1, 2):
            struct.pack_into("<I", data, descriptor, kind)
            yield f"{variant}-type{kind}", bytes(data), descriptor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="new external output directory")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    rows = []
    for name, data, descriptor in controls():
        path = args.output / f"{name}.caj"
        path.write_bytes(data)
        rows.append({"name": name, "file": path.name, "bytes": len(data),
                     "sha256": hashlib.sha256(data).hexdigest(),
                     "descriptor_offset": descriptor})
    (args.output / "manifest.json").write_text(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
