# SPDX-License-Identifier: MIT
"""Read existing independent bitmap receipts and normalize bounded PDF bits."""
import hashlib
import json
from pathlib import Path
import zlib

import pikepdf

MAX_BITMAP = 16 * 1024 * 1024
INVERT = bytes(255 - value for value in range(256))


def require(value, reason):
    if not value:
        raise ValueError(reason)


def load_oracles(research):
    """Use only explicitly passing original-source measurements, never PDF bits."""
    paths = [
        Path(research) / "notes/github-bitmap-oracles-20261008.json",
        Path(research) / "conformance/jbig1_oracle.json",
        Path(research) / "conformance/jbig2_oracle.json",
        Path(research) / "notes/nh-bitmap-oracle-20261008.json",
    ]
    records = {}
    inputs = []

    def add(sha, page, index, offset, length, encoded, identity):
        key = (sha, page, index)
        value = {
            "offset": offset,
            "length": length,
            "encoded_sha256": encoded,
            "identity": tuple(identity),
        }
        require(
            key not in records or records[key] == value,
            "conflicting source bitmap receipts",
        )
        records[key] = value

    for path in paths:
        require(path.stat().st_size <= 64 * 1024 * 1024, "oracle metadata byte limit")
        data = path.read_bytes()
        inputs.append(
            {
                "path": str(path.relative_to(research)),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
        report = json.loads(data)
        if "sources" in report:
            for row in report["sources"]:
                require(
                    row["source_integrity"] == "PASS"
                    and row["oracle_integrity"] == "PASS",
                    "source oracle integrity",
                )
                for page in row["page_records"]:
                    for image in page["images"]:
                        if image["type"] in (0, 3):
                            add(
                                row["source_sha256"],
                                page["page"],
                                image["image"],
                                image["offset"],
                                image["length"],
                                image["encoded_sha256"],
                                image["oracle_identity"],
                            )
        elif "pages" in report:
            require(
                report["status"] == "PASS"
                and all(
                    report[k] is True
                    for k in (
                        "source_integrity",
                        "output_integrity",
                        "oracle_integrity",
                    )
                ),
                "source oracle integrity",
            )
            for page in report["pages"]:
                for image in page["images"]:
                    if image["record_type"] in (0, 3):
                        require(
                            image["oracle"]["status"] == "PASS",
                            "source bitmap oracle failed",
                        )
                        add(
                            report["source_sha256"],
                            page["page"],
                            image["image_number"],
                            image["payload_offset"],
                            image["payload_length"],
                            image["payload_sha256"],
                            image["oracle"]["identity"],
                        )
        else:
            for row in report["samples"]:
                for image in row["images"]:
                    if image.get("decoder_result", image.get("status")) != "PASS":
                        continue
                    pixel = image.get(
                        "visible_bits_sha256", image.get("normalized_pixel_sha256")
                    )
                    add(
                        row["source_sha256"],
                        image["page"],
                        image["image"],
                        image["offset"],
                        image["length"],
                        image["encoded_sha256"],
                        ("bits", image["width"], image["height"], pixel),
                    )
    return records, inputs


def expected_identity(oracles, sha, page, image):
    key = (sha, page, image["image_number"])
    require(
        oracles is not None and key in oracles,
        "missing independent source bitmap identity",
    )
    oracle = oracles[key]
    require(
        (oracle["offset"], oracle["length"], oracle["encoded_sha256"])
        == (image["payload_offset"], image["payload_length"], image["payload_sha256"]),
        "source bitmap receipt span/hash differs",
    )
    return oracle["identity"]


def bitmap_identity(stream, kind):
    require(kind in (0, 3), "unmeasured source bitmap type")
    width, height = stream.Width, stream.Height
    require(type(width) is int and type(height) is int, "noninteger bitmap dimensions")
    require(
        0 < width <= 100000 and 0 < height <= 100000 and width * height <= 100000000,
        "bitmap dimensions",
    )
    require(
        stream.get("/ColorSpace") == pikepdf.Name("/DeviceGray")
        and stream.get("/BitsPerComponent") == 1,
        "unmeasured PDF bitmap samples",
    )
    require(
        stream.get("/ImageMask", False) is False
        and all(stream.get(k) is None for k in ("/Mask", "/SMask", "/DecodeParms")),
        "unmeasured PDF bitmap mask/parameters",
    )
    require(
        stream.get("/Filter") == pikepdf.Name("/FlateDecode"),
        "unmeasured bitmap filter",
    )
    decode = stream.get("/Decode")
    decode = [0, 1] if decode is None else list(decode)
    require(decode in ([0, 1], [1, 0]), "unmeasured bitmap Decode")
    row_bytes = (width + 7) // 8
    expected = row_bytes * height
    require(
        expected <= MAX_BITMAP and 0 < int(stream.Length) <= MAX_BITMAP,
        "bitmap byte limit",
    )
    encoded = stream.read_raw_bytes()
    require(len(encoded) == int(stream.Length), "bitmap encoded length")
    z = zlib.decompressobj()
    data = z.decompress(encoded, expected + 1)
    require(
        len(data) == expected and z.eof and not z.unused_data and not z.unconsumed_tail,
        "bitmap inflate framing/length",
    )
    if decode == [0, 1]:
        data = data.translate(INVERT)  # PBM has one for black; DeviceGray has zero.
    digest = hashlib.sha256()
    # The original type-0 oracle uses bottom-up DIB rows. Type 3 uses top-down
    # visible rows. The choice comes from the source type, never a hash match.
    rows = range(height - 1, -1, -1) if kind == 0 else range(height)
    view = memoryview(data)
    for y in rows:
        row = view[y * row_bytes : (y + 1) * row_bytes]
        if width % 8:
            digest.update(row[:-1])
            digest.update(bytes([row[-1] & (255 << (8 - width % 8) & 255)]))
        else:
            digest.update(row)
    return ("bits", width, height, digest.hexdigest())
