#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Original asymmetric image controls for fixed Wine zoom/placement trials."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from c8_image_fixture import document, jpeg


CASES = {"baseline": (5105, 370, 460), "width-plus1": (5106, 370, 460),
         "placement-plus20": (5105, 390, 480)}


def control(width, dx, dy):
    data = bytearray(document(jpeg(8), dx=dx, dy=dy, dw=3420, dh=2450,
                             page_size=(width, 4800)))
    start, length = struct.unpack_from("<II", data, 80)
    struct.pack_into("<I", data, start + length, 1)
    return bytes(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="new external directory")
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for name, parameters in CASES.items():
        data = control(*parameters)
        (output / f"{name}.caj").write_bytes(data)
        rows.append({"name": name, "width": parameters[0], "dx": parameters[1],
                     "dy": parameters[2], "bytes": len(data),
                     "sha256": hashlib.sha256(data).hexdigest()})
    (output / "manifest.json").write_text(json.dumps(rows, indent=2) + "\n")
