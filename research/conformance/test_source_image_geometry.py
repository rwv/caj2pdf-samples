# SPDX-License-Identifier: MIT
"""Original source/PDF controls, including changes that qpdf alone accepts."""
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

import pikepdf
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import source_image_geometry as g
from source_bitmap_identities import bitmap_identity, expected_identity


def jpeg(level):
    out = io.BytesIO()
    image = Image.new("L", (7, 5), level)
    image.putpixel((2, 1), 255 - level)
    image.save(out, format="JPEG")
    return out.getvalue()


def record(x, y, width, height, flag=0):
    return struct.pack("<14H", 0x800A, flag, x, y, width, height, *([0] * 8))


def fixture(root):
    images = [jpeg(30), jpeg(180)]
    positions = [[12, 23, 53, 41], [110, 70, 35, 47]]
    data = b"".join(record(*p) for p in positions) + struct.pack("<HH", 0x8004, 0)
    text = b"COMPRESSTEXT" + struct.pack("<I", len(data)) + zlib.compress(data)
    source = bytearray(100)
    source[:4] = b"\xc8\0\0\0"
    struct.pack_into("<II", source, 8, 1, 2)
    struct.pack_into("<HH", source, 0x20, 300, 200)
    struct.pack_into("<iihHII", source, 0x50, 100, len(text), 2, 0, 0, 0)
    source.extend(text)
    for payload in images:
        source.extend(struct.pack("<iii", 2, len(source) + 12, len(payload)))
        source.extend(payload)
    src = root / "original.caj"
    src.write_bytes(source)
    pdf = root / "original.pdf"
    with pikepdf.new() as doc:
        page = doc.add_blank_page(page_size=(float(300 * g.UNIT), float(200 * g.UNIT)))
        resources = pikepdf.Dictionary()
        operations = []
        for i, (payload, pos) in enumerate(zip(images, positions)):
            resources["/I" + str(i)] = doc.make_stream(
                payload,
                Type=pikepdf.Name("/XObject"),
                Subtype=pikepdf.Name("/Image"),
                Width=7,
                Height=5,
                BitsPerComponent=8,
                ColorSpace=pikepdf.Name("/DeviceGray"),
                Filter=pikepdf.Name("/DCTDecode"),
            )
            x, y, w, h = pos
            matrix = [w * g.UNIT, 0, 0, -h * g.UNIT, x * g.UNIT, (200 - y) * g.UNIT]
            operations.append(
                "q " + " ".join(str(float(v)) for v in matrix) + f" cm /I{i} Do Q\n"
            )
        page.Resources.XObject = resources
        page.Contents = doc.make_stream("".join(operations).encode())
        doc.save(pdf)
    return src, pdf


class GeometryTests(unittest.TestCase):
    def test_complete_authored_source_geometry_and_jpeg_identity(self):
        with tempfile.TemporaryDirectory() as name:
            source, pdf = fixture(Path(name))
            report = g.inspect(source, pdf, g.digest(source), g.digest(pdf), oracles={})
            self.assertEqual(report["counts"], {"PASS": 1})
            self.assertTrue(
                all(x["resource_identity_match"] for x in report["pages"][0]["draws"])
            )
            self.assertTrue(report["source_and_pdf_unchanged"])

    def test_changed_box_position_scale_order_omission_and_duplicates_fail(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source, original = fixture(root)
            for mutation in (
                "box",
                "position",
                "scale",
                "order",
                "omission",
                "duplicate",
            ):
                with self.subTest(mutation=mutation), pikepdf.open(original) as doc:
                    page = doc.pages[0]
                    data = page.Contents.read_bytes()
                    if mutation == "box":
                        page.MediaBox = [0, 0, 100, 100]
                    elif mutation == "position":
                        data = b"1 0 0 1 3 0 cm\n" + data
                    elif mutation == "scale":
                        data = b"2 0 0 1 0 0 cm\n" + data
                    elif mutation == "order":
                        a = page.Resources.XObject.I0
                        b = page.Resources.XObject.I1
                        page.Resources.XObject.I0 = b
                        page.Resources.XObject.I1 = a
                    elif mutation == "omission":
                        data = data.splitlines(keepends=True)[0]
                    else:
                        data += data.splitlines(keepends=True)[0]
                    page.Contents = doc.make_stream(data)
                    changed = root / (mutation + ".pdf")
                    doc.save(changed)
                report = g.inspect(
                    source, changed, g.digest(source), g.digest(changed), oracles={}
                )
                self.assertEqual(report["counts"], {"FAIL": 1}, mutation)
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                g.inspect(source, original, "0" * 64, g.digest(original), oracles={})

    def test_compact_framing_and_marker_scope(self):
        data = record(0xC012, 23, 0xC035, 41, 0xD300) + struct.pack("<HH", 0x8004, 0)
        self.assertEqual(g.compact_records(data, "HN-A", True), [[18, 23, 53, 41]])
        self.assertEqual(
            g.compact_records(data, "C8", False), [[0xC012, 23, 0xC035, 41]]
        )
        for bad in (data[:25], data[:-4], struct.pack("<HH", 0x8123, 0) + data):
            with self.assertRaises(ValueError):
                g.compact_records(bad, "HN-A", True)
        packed = zlib.compress(data)
        self.assertEqual(g.inflate(packed, len(data)), data)
        for raw, size in (
            (packed[:-1], len(data)),
            (packed + b"x", len(data)),
            (packed, len(data) - 1),
        ):
            with self.assertRaises(ValueError):
                g.inflate(raw, size)

    def test_paired_dimensions_are_source_fields_not_document_defaults(self):
        data = (
            struct.pack("<4H", 0x8003, 410, 0x8003, 270)
            + record(0, 0, 300, 200)
            + struct.pack("<HH", 0x8004, 0)
        )
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "records"
            path.write_bytes(data)
            with g.FileInput(path) as source:
                pos, profile, extent = g.source_positions(
                    source,
                    {"text_offset": 0, "text_length": len(data), "image_count": 1},
                    "HN-A",
                    (300, 200),
                )
                self.assertEqual(extent, (410, 270))
                self.assertEqual(pos, [[0, 0, 300, 200]])
                self.assertEqual(profile, "raw")

    def test_fixed_region_constraints_and_original_primary(self):
        page = {"images": [{"record_type": 2}], "page_number": 3}
        data = (
            struct.pack("<4H", 0x801C, 0, 0x80CE, 0)
            + record(0, 0, 300, 200)
            + record(5, 10, 30, 40)
            + struct.pack("<HH", 0x8004, 2)
        )
        self.assertEqual(
            g.fixed_records(data, 1, "HN-A", page, (300, 200)), [[0, 0, 300, 200]]
        )
        for index in (10, 12, 22, 32, 64):
            bad = bytearray(data)
            bad[index] ^= 1
            with self.subTest(index=index), self.assertRaises(ValueError):
                g.fixed_records(bytes(bad), 1, "HN-A", page, (300, 200))

    def test_aliases_check_actual_bytes_even_if_metadata_lies(self):
        with tempfile.TemporaryDirectory() as name:
            p = Path(name) / "images"
            p.write_bytes(b"abababax")
            images = [
                {
                    "record_type": 2,
                    "payload_length": 2,
                    "payload_sha256": "same",
                    "payload_offset": i,
                }
                for i in (0, 2, 4, 6)
            ]
            with g.FileInput(p) as source:
                self.assertEqual(
                    len(g.check_aliases(source, images[:3], [[0, 0, 1, 1]])), 1
                )
                with self.assertRaisesRegex(ValueError, "different alias bytes"):
                    g.check_aliases(source, images, [[0, 0, 1, 1]])
                with self.assertRaises(ValueError):
                    g.read_span(source, 0, g.MAX_TEXT + 1)

    def test_bitmap_decode_rows_padding_and_visible_mutation(self):
        # Authored five-pixel rows: 10000, 00100, 11110 (one means black).
        with pikepdf.new() as pdf:

            def measured(stream, kind):
                pdf.Root.Control = stream
                output = io.BytesIO()
                pdf.save(output)
                with pikepdf.open(output) as loaded:
                    return bitmap_identity(loaded.Root.Control, kind)

            for decode, data in (([1, 0], b"\x87\x27\xf7"), ([0, 1], b"\x78\xd8\x08")):
                stream = pdf.make_stream(
                    zlib.compress(data),
                    Width=5,
                    Height=3,
                    BitsPerComponent=1,
                    ColorSpace=pikepdf.Name("/DeviceGray"),
                    Decode=pikepdf.Array(decode),
                    Filter=pikepdf.Name("/FlateDecode"),
                )
                self.assertEqual(
                    measured(stream, 3),
                    ("bits", 5, 3, hashlib.sha256(b"\x80\x20\xf0").hexdigest()),
                )
                self.assertEqual(
                    measured(stream, 0),
                    ("bits", 5, 3, hashlib.sha256(b"\xf0\x20\x80").hexdigest()),
                )
            stream = pdf.make_stream(
                zlib.compress(b"\x80\x20\xe0"),
                Width=5,
                Height=3,
                BitsPerComponent=1,
                ColorSpace=pikepdf.Name("/DeviceGray"),
                Decode=pikepdf.Array([1, 0]),
                Filter=pikepdf.Name("/FlateDecode"),
            )
            self.assertNotEqual(
                measured(stream, 3)[-1], hashlib.sha256(b"\x80\x20\xf0").hexdigest()
            )
            stream.ImageMask = True
            with self.assertRaisesRegex(ValueError, "mask/parameters"):
                measured(stream, 3)
            del stream.ImageMask
            stream.Width = 5.5
            with self.assertRaisesRegex(ValueError, "noninteger"):
                measured(stream, 3)
            stream.Width = 100001
            with self.assertRaises(ValueError):
                bitmap_identity(stream, 3)
        with self.assertRaisesRegex(ValueError, "missing independent"):
            expected_identity({}, "source", 1, {"image_number": 1})

    def test_native_origin_markers_callback_and_mode_zero_canvas(self):
        with tempfile.TemporaryDirectory() as name:
            p = Path(name) / "native"
            header = bytearray(64)
            struct.pack_into("<I", header, 12, 2)
            struct.pack_into("<HH", header, 28, 100, 200)
            data = (
                struct.pack("<HH", 37, 0xA0C1)
                + record(0xC070, 223, 0xC035, 41, 0xD300)
                + struct.pack("<HH", 0x8004, 0)
            )
            p.write_bytes(header + data)
            with g.FileInput(p) as source:
                positions, profile, extent = g.native_positions(
                    source,
                    {"text_offset": 64, "text_length": len(data), "images": [{}]},
                    "C8",
                    (300, 200),
                )
                self.assertEqual(positions, [[12, 23, 53, 41]])
                self.assertEqual(profile, "native-mode-2")
                self.assertEqual(extent, (300, 200))
            header = bytearray(200)
            data = struct.pack("<HHH", 37, 0xA3C1, 0x8004)
            p.write_bytes(header + data)
            with g.FileInput(p) as source:
                positions, profile, extent = g.native_positions(
                    source,
                    {"text_offset": 200, "text_length": len(data), "images": []},
                    "HN-B",
                    (300, 200),
                )
                self.assertEqual(positions, [])
                self.assertEqual(extent, [400, 300])
                self.assertEqual(profile, "native-mode-0")

    def test_graphics_state_composition_and_clip_guard(self):
        with tempfile.TemporaryDirectory() as name:
            _, path = fixture(Path(name))
            with pikepdf.open(path) as pdf:
                page = pdf.pages[0]
                data = page.Contents.read_bytes()
                original = g.pdf_draws(page)[0][0]
                page.Contents = pdf.make_stream(b"q 1 0 0 1 4 7 cm\n" + data + b"Q\n")
                translated = g.pdf_draws(page)[0][0]
                self.assertEqual(translated[:4], original[:4])
                self.assertEqual(translated[4:], [original[4] + 4, original[5] + 7])
                page.Contents = pdf.make_stream(b"q 0 0 1 1 re W n\n" + data + b"Q\n")
                with self.assertRaises(ValueError):
                    g.pdf_draws(page, native=True)

    def test_blend_state_restore_and_opacity_rejection(self):
        with tempfile.TemporaryDirectory() as name:
            _, path = fixture(Path(name))
            with pikepdf.open(path) as pdf:
                page = pdf.pages[0]
                page.Resources.ExtGState = pikepdf.Dictionary(
                    M=pikepdf.Dictionary(
                        Type=pikepdf.Name("/ExtGState"), BM=pikepdf.Name("/Multiply")
                    )
                )
                page.Contents = pdf.make_stream(b"q /M gs /I0 Do Q /I1 Do")
                self.assertEqual(
                    [x[2] for x in g.pdf_draws(page, native=True)],
                    ["/Multiply", "/Normal"],
                )
                page.Resources.ExtGState.M.ca = 0
                with self.assertRaisesRegex(
                    ValueError, "unmeasured graphics parameters"
                ):
                    g.pdf_draws(page, native=True)

    def test_bitmap_receipt_binds_source_span_and_hash(self):
        image = {
            "image_number": 1,
            "payload_offset": 20,
            "payload_length": 4,
            "payload_sha256": "b" * 64,
        }
        identity = ("bits", 5, 3, hashlib.sha256(b"\x80\x20\xf0").hexdigest())
        receipts = {
            ("a" * 64, 1, 1): {
                "offset": 20,
                "length": 4,
                "encoded_sha256": "b" * 64,
                "identity": identity,
            }
        }
        self.assertEqual(expected_identity(receipts, "a" * 64, 1, image), identity)
        for key, value in (
            ("payload_offset", 21),
            ("payload_length", 3),
            ("payload_sha256", "c" * 64),
        ):
            with self.subTest(key=key), self.assertRaisesRegex(
                ValueError, "span/hash differs"
            ):
                expected_identity(receipts, "a" * 64, 1, {**image, key: value})

    def test_cli_retains_missing_input_and_nonzero_incomplete_result(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source, pdf = fixture(root)
            case = {
                "source_path": source.name,
                "pdf_path": pdf.name,
                "source_sha256": g.digest(source),
                "pdf_sha256": g.digest(pdf),
                "pages": 1,
                "native": False,
            }
            manifest = root / "manifest.json"
            for label, rows, expected in (
                ("complete", [case], 0),
                (
                    "missing",
                    [
                        case,
                        {**case, "source_path": "missing", "source_sha256": "0" * 64},
                    ],
                    1,
                ),
            ):
                manifest.write_text(json.dumps(rows))
                output = root / label
                result = subprocess.run(
                    [
                        sys.executable,
                        g.__file__,
                        "--manifest",
                        str(manifest),
                        "--output-dir",
                        str(output),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(result.returncode, expected, result.stderr)
                receipt = json.loads((output / "summary.json").read_text())
                self.assertEqual(receipt["input_counts"].get("PASS"), 1)
                self.assertTrue(receipt["measurement_inputs_unchanged"])
                if expected:
                    self.assertEqual(receipt["input_counts"]["ERROR"], 1)
                    self.assertEqual(receipt["page_counts"]["NOT_CHECKED"], 1)
                    self.assertEqual(
                        len((output / "results.jsonl").read_text().splitlines()), 2
                    )


if __name__ == "__main__":
    unittest.main()
