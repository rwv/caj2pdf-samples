# SPDX-License-Identifier: MIT
"""Bounded comparison of measured HN/C8 page extents and ordered image placement.

This checks the established empirical coordinate model, not vendor pixels or
an authoritative physical source unit. Native glyph/vector placement is excluded.
"""
import argparse
import collections
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import re
import resource
import struct
import time
import zlib

import pikepdf

from hnc8_layout_source import FileInput, SourceExtractor
from hnc8_text_frame import MARKER_SHA256
from native_text_order import source_glyphs
from source_bitmap_identities import bitmap_identity, expected_identity, load_oracles

MAX_TEXT = 1024 * 1024
MAX_IMAGES = 8192
UNIT = Fraction(240, 2473)
TOLERANCE = Fraction(1, 20000)
CONTROLS = {0x8001, 0x801C, 0x801D, 0x80FF, 0x8070, 0x8071, 0x80CE}


def require(test, reason):
    if not test:
        raise ValueError(reason)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def words(data, at, count):
    require(0 <= at and at + count * 2 <= len(data), "truncated record")
    return struct.unpack_from("<" + "H" * count, data, at)


def inflate(data, declared):
    require(0 < declared <= MAX_TEXT and len(data) <= MAX_TEXT, "text byte limit")
    decoder = zlib.decompressobj()
    plain = decoder.decompress(data, declared + 1)
    require(
        len(plain) == declared
        and decoder.eof
        and not decoder.unused_data
        and not decoder.unconsumed_tail,
        "incomplete/oversized zlib frame",
    )
    return plain


def compact_records(data, variant, raw):
    at = 0
    if data[:2] == b"\x03\x80":
        require(
            raw and variant == "HN-A" and data[4:6] == b"\x03\x80", "unknown prefix"
        )
        at = 8
    positions = []
    for _ in range(65536):
        tag, flag = words(data, at, 2)
        if tag == 0x8004:
            require(positions, "no image placement")
            return positions
        if tag == 0x800A:
            require(at + 28 <= len(data), "truncated image record")
            x, y, width, height = words(data, at + 4, 4)
            if raw and variant == "HN-A" and flag == 0xD300:
                if x & 0xC000 == 0xC000 and width & 0xC000 == 0xC000:
                    x &= 0x3FFF
                    width &= 0x3FFF
            require(
                width and height and len(positions) < MAX_IMAGES, "image extent/count"
            )
            positions.append([x, y, width, height])
            at += 28
        else:
            require(tag < 0x8000 or tag in CONTROLS, "unmeasured compact record")
            require(tag != 0x80CE or flag == 0, "unmeasured compact control")
            at += 4
    raise ValueError("record limit")


def fixed_records(data, count, variant, page, extent):
    candidates = [(n, len(data) - 12 - 28 * (count + n)) for n in range(3)]
    candidates = [(n, size) for n, size in candidates if size >= 0 and size % 16 == 0]
    require(len(candidates) == 1, "unmeasured fixed/region layout")
    regions, body = candidates[0]
    require(
        not regions
        or (variant == "HN-A" and count == 1 and page["images"][0]["record_type"] == 2),
        "unmeasured image regions",
    )
    require(
        words(data, 0, 1)[0] == 0x801C and words(data, 4, 1)[0] == 0x80CE,
        "unmeasured fixed prefix",
    )
    for at in range(8, 8 + body, 16):
        markers = data[at : at + 2] + data[at + 4 : at + 6] + data[at + 8 : at + 10]
        require(
            hashlib.sha256(markers).hexdigest() == MARKER_SHA256, "fixed glyph markers"
        )
    positions = []
    for index, at in enumerate(range(8 + body, len(data) - 4, 28)):
        fields = words(data, at, 14)
        require(fields[0] == 0x800A, "fixed image marker")
        value = list(fields[2:6])
        if regions:
            require(fields[1] == 0 and not any(fields[7:]), "region reserved fields")
            require(
                fields[6] in (0, 1) if index == 0 else fields[6] == index - 1,
                "region ordinal/primary flag",
            )
            if index == 0:
                require(
                    value == [0, 0, *extent], "region primary is not a complete page"
                )
            else:
                continue
        if (
            variant == "HN-A"
            and fields[1] == 0xD300
            and value[0] & 0xC000 == 0xC000
            and value[2] & 0xC000 == 0xC000
        ):
            value[0] &= 0x3FFF
            value[2] &= 0x3FFF
        require(value[2] and value[3], "zero image extent")
        positions.append(value)
    ending = words(data, len(data) - 4, 2)
    require(ending[0] == 0x8004, "fixed end marker")
    require(not regions or ending[1] == page["page_number"] - 1, "region page ordinal")
    return positions


def source_positions(source, page, variant, extent):
    require(0 < page["text_length"] <= MAX_TEXT, "text byte limit")
    data = read_span(source, page["text_offset"], page["text_length"])
    if variant == "HN-A" and data[:2] == b"\x03\x80" and data[4:6] == b"\x03\x80":
        extent = (words(data, 2, 1)[0], words(data, 6, 1)[0])
        require(all(extent), "zero paired page extent")
    count = page["image_count"]
    require(0 < count <= MAX_IMAGES, "image count limit")
    if data.startswith(b"COMPRESSTEXT"):
        require(len(data) >= 16, "short compressed header")
        return (
            compact_records(
                inflate(data[16:], int.from_bytes(data[12:16], "little")),
                variant,
                False,
            ),
            "direct-zlib",
            extent,
        )
    if data[8:20] == b"COMPRESSTEXT":
        require(data[:2] == b"\x03\x80" and data[4:6] == b"\x03\x80", "tagged header")
        return (
            fixed_records(
                inflate(data[24:], int.from_bytes(data[20:24], "little")),
                count,
                variant,
                page,
                extent,
            ),
            "tagged-zlib",
            extent,
        )
    require(
        variant == "HN-A"
        or (variant == "C8" and count == 1 and data[:4] == b"\x0a\x80\0\0"),
        "native text or unmeasured raw profile",
    )
    return compact_records(data, variant, True), "raw", extent


def read_span(source, offset, length):
    require(
        0 <= offset <= source.size
        and 0 <= length <= MAX_TEXT
        and offset + length <= source.size,
        "source span limit",
    )
    result = bytearray()
    while len(result) < length:
        count = min(65536, length - len(result))
        chunk = source.read_at(offset + len(result), count)
        require(
            isinstance(chunk, bytes) and 0 < len(chunk) <= count, "source read failed"
        )
        result.extend(chunk)
    return bytes(result)


def check_aliases(source, images, positions):
    require(
        images and positions and len(images) % len(positions) == 0,
        "incomplete image groups",
    )
    first = images[: len(positions)]
    keys = ("record_type", "payload_length", "payload_sha256")
    for i, image in enumerate(images):
        original = first[i % len(first)]
        require(all(image[k] == original[k] for k in keys), "conflicting image alias")
        if i >= len(first):
            for offset in range(0, image["payload_length"], 65536):
                length = min(65536, image["payload_length"] - offset)
                require(
                    read_span(source, image["payload_offset"] + offset, length)
                    == read_span(source, original["payload_offset"] + offset, length),
                    "different alias bytes",
                )
    return first


def pdf_content(page):
    contents = page.get("/Contents")
    streams = list(contents) if isinstance(contents, pikepdf.Array) else [contents]
    require(0 < len(streams) <= 16, "content stream count")
    parts = []
    size = 0
    for stream in streams:
        require(isinstance(stream, pikepdf.Stream), "content stream required")
        length = stream.get("/Length")
        require(
            isinstance(length, int) and 0 <= length <= MAX_TEXT, "content byte limit"
        )
        raw = stream.read_raw_bytes()
        require(len(raw) == length, "content length mismatch")
        value = stream.get("/Filter")
        if value == pikepdf.Name("/FlateDecode"):
            require(stream.get("/DecodeParms") is None, "content decode parameters")
            decoder = zlib.decompressobj()
            raw = decoder.decompress(raw, MAX_TEXT + 1)
            require(
                len(raw) <= MAX_TEXT
                and decoder.eof
                and not decoder.unused_data
                and not decoder.unconsumed_tail,
                "content inflate bound/framing",
            )
        else:
            require(value is None, "unmeasured content filter")
        size += len(raw) + 1
        require(size <= MAX_TEXT, "total page content byte limit")
        parts.append(raw)
    return b"\n".join(parts)


def multiply(left, right):
    a, b, c, d, e, f = left
    g, h, i, j, k, l = right
    return [
        a * g + c * h,
        b * g + d * h,
        a * i + c * j,
        b * i + d * j,
        a * k + c * l + e,
        b * k + d * l + f,
    ]


def pdf_draws(page, native=False):
    pdf_content(page)  # Validate bounded, complete inflate before library parsing.
    matrix = list(map(Fraction, [1, 0, 0, 1, 0, 0]))
    stack = []
    draws = []
    clipped = False
    blend = "/Normal"
    passive = {
        "BT",
        "ET",
        "Tf",
        "Tm",
        "Tj",
        "TJ",
        "Tr",
        "Td",
        "TD",
        "T*",
        "Tc",
        "Tw",
        "Tz",
        "TL",
        "Ts",
        "g",
        "G",
        "rg",
        "RG",
        "k",
        "K",
        "w",
        "J",
        "j",
        "M",
        "d",
        "m",
        "l",
        "c",
        "v",
        "y",
        "h",
        "re",
        "S",
        "s",
        "f",
        "F",
        "f*",
        "B",
        "B*",
        "b",
        "b*",
        "n",
        "BMC",
        "BDC",
        "EMC",
    }
    operations = pikepdf.parse_content_stream(page)
    require(len(operations) <= 200000, "PDF operation limit")
    for args, operator in operations:
        op = str(operator)
        if op == "q":
            require(not args and len(stack) < 64, "graphics stack limit")
            stack.append((matrix[:], clipped, blend))
        elif op == "Q":
            require(not args and stack, "unbalanced graphics state")
            matrix, clipped, blend = stack.pop()
        elif op == "cm":
            require(len(args) == 6, "matrix arity")
            values = [Fraction(str(x)) for x in args]
            require(all(abs(x) <= 100000 for x in values), "PDF coordinate limit")
            matrix = multiply(matrix, values)
        elif op == "Do":
            require(len(args) == 1 and not clipped, "clipped or malformed image draw")
            resource = page.Resources.XObject[str(args[0])]
            require(
                resource.get("/Subtype") == pikepdf.Name("/Image"), "non-image draw"
            )
            require(len(draws) < MAX_IMAGES, "PDF image count limit")
            draws.append((matrix[:], resource, blend))
        elif op == "gs":
            require(native and len(args) == 1, "unexpected graphics parameters")
            state = page.Resources.ExtGState[str(args[0])]
            require(
                set(state.keys()) == {"/Type", "/BM"}
                and state.Type == pikepdf.Name("/ExtGState")
                and state.BM in (pikepdf.Name("/Normal"), pikepdf.Name("/Multiply")),
                "unmeasured graphics parameters",
            )
            blend = str(state.BM)
        elif op in ("W", "W*"):
            require(native, "unexpected clipping")
            clipped = True
        else:
            require(native and op in passive, "unmeasured PDF graphics syntax")
    require(not stack, "unbalanced graphics state")
    return draws


def native_positions(source, page, variant, extent):
    require(variant in ("C8", "HN-B"), "native variant")
    base = 0 if variant == "C8" else 136
    mode = int.from_bytes(read_span(source, base + 12, 4), "little")
    require(mode in (0, 2), "native mode")
    origin = words(read_span(source, base + 28, 4), 0, 2)
    positions = []

    def image(at, tag, size):
        x, y, width, height = words(read_span(source, at + 4, 8), 0, 4)
        if tag == 0x800A:
            require(
                x & 0xC000 == 0xC000 and width & 0xC000 == 0xC000,
                "native image marker bits",
            )
            x &= 0x3FFF
            width &= 0x3FFF
        require(width and height, "native image extent")
        positions.append([x - origin[0], y - origin[1], width, height])

    source_glyphs(source, page, variant, mode, image_visitor=image)
    require(len(positions) == len(page["images"]), "native image count")
    if mode == 0:
        require(variant == "HN-B" and not positions, "unmeasured mode-0 image")
        extent = [x + 100 for x in extent]
    return positions, "native-mode-" + str(mode), extent


def residual(actual, expected):
    require(len(actual) == len(expected), "geometry arity")
    values = [abs(Fraction(str(a)) - b) for a, b in zip(actual, expected)]
    return max(values, default=Fraction(0))


def compare_page(
    page,
    extent,
    positions,
    images,
    *,
    native=False,
    oracles=None,
    source_sha=None,
    page_number=None,
):
    expected_box = [Fraction(0), Fraction(0), extent[0] * UNIT, extent[1] * UNIT]
    errors = []
    box_delta = residual(page.MediaBox, expected_box)
    if box_delta > TOLERANCE:
        errors.append("page box")
    require(
        page.get("/Rotate", 0) == 0 and page.get("/UserUnit", 1) == 1,
        "rotated/scaled PDF page",
    )
    crop = page.get("/CropBox")
    require(
        crop is None or residual(crop, expected_box) <= TOLERANCE, "different crop box"
    )
    actual = pdf_draws(page, native)
    if len(actual) != len(positions):
        errors.append("draw count mismatch")
    rows = []
    for number, ((matrix, resource, blend), pos, image) in enumerate(
        zip(actual, positions, images), 1
    ):
        x, y, width, height = pos
        top = expected_box[3] - y * UNIT
        jpeg = image["record_type"] in (1, 2)
        expected = [
            width * UNIT,
            Fraction(0),
            Fraction(0),
            (-height if jpeg else height) * UNIT,
            x * UNIT,
            top if jpeg else top - height * UNIT,
        ]
        delta = residual(matrix, expected)
        valid = delta <= TOLERANCE
        if not valid:
            errors.append(f"image {number} transform")
        # Identity is deliberately separate from layout, and cannot be replaced
        # by matching dimensions or by an output resource name.
        if jpeg:
            require(
                resource.get("/Filter") == pikepdf.Name("/DCTDecode"),
                "JPEG representation",
            )
            length = resource.get("/Length")
            require(
                isinstance(length, int) and 0 < length <= 64 * 1024 * 1024,
                "JPEG byte limit",
            )
            actual_identity = ("jpeg", digest_bytes(resource.read_raw_bytes()))
            expected = ("jpeg", image["payload_sha256"])
        else:
            expected = expected_identity(oracles, source_sha, page_number, image)
            actual_identity = bitmap_identity(resource, image["record_type"])
        identity = actual_identity == expected
        if not identity:
            errors.append(f"image {number} resource identity")
        require(
            blend == "/Normal" or (native and image["record_type"] in (0, 3)),
            "unmeasured image blend profile",
        )
        rows.append(
            {
                "image": number,
                "type": image["record_type"],
                "source_coordinates": pos,
                "source_payload_sha256": image["payload_sha256"],
                "pdf_object": list(resource.objgen),
                "matrix": [float(v) for v in matrix],
                "maximum_residual_points": float(delta),
                "transform_match": valid,
                "resource_identity_match": identity,
                "expected_identity": list(expected),
                "actual_identity": list(actual_identity),
                "pdf_blend_mode": blend,
            }
        )
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "page_box_maximum_residual_points": float(box_delta),
        "draws": rows,
    }


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def inspect(source_path, pdf_path, source_sha, pdf_sha, *, native=False, oracles=None):
    require(
        0 < Path(source_path).stat().st_size <= 512 * 1024 * 1024
        and 0 < Path(pdf_path).stat().st_size <= 512 * 1024 * 1024,
        "source/PDF size limit",
    )
    require(
        digest(source_path) == source_sha and digest(pdf_path) == pdf_sha,
        "input hash mismatch",
    )
    rows = []
    with FileInput(source_path) as source, pikepdf.open(pdf_path) as pdf:
        extractor = SourceExtractor(source, source_sha)
        variant = extractor.header["variant"]
        require(len(pdf.pages) == extractor.header["page_count"], "page count mismatch")
        size_at = 0x20 if variant == "C8" else 0xA8
        extent = words(source.read_at(size_at, 4), 0, 2)
        require(all(extent), "zero page extent")
        for record, page in zip(extractor.iter_pages(), pdf.pages):
            row = {
                "page": record["page_number"],
                "source_descriptors": record["image_count"],
            }
            try:
                positions, profile, page_extent = (
                    native_positions if native else source_positions
                )(source, record, variant, extent)
                images = (
                    record["images"]
                    if native
                    else check_aliases(source, record["images"], positions)
                )
                row.update(
                    compare_page(
                        page,
                        page_extent,
                        positions,
                        images,
                        native=native,
                        oracles=oracles,
                        source_sha=source_sha,
                        page_number=record["page_number"],
                    )
                )
                row["source_page_extent"] = list(page_extent)
                row.update(
                    profile=profile,
                    alias_descriptors=len(record["images"]) - len(images),
                )
            except (ValueError, zlib.error) as error:
                row.update(status="NOT_CHECKED", reason=str(error))
            rows.append(row)
        warnings = pdf.get_warnings()
    require(
        digest(source_path) == source_sha and digest(pdf_path) == pdf_sha,
        "inputs changed",
    )
    return {
        "source_sha256": source_sha,
        "pdf_sha256": pdf_sha,
        "variant": variant,
        "source_page_extent": extent,
        "pages": rows,
        "source_and_pdf_unchanged": True,
        "parser_warnings": warnings,
        "counts": dict(collections.Counter(r["status"] for r in rows)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="JSON list: source_path, pdf_path, source_sha256, pdf_sha256, pages, native",
    )
    parser.add_argument(
        "--output-dir", type=Path, required=True, help="new external directory"
    )
    args = parser.parse_args()
    research = Path(__file__).resolve().parents[1]
    require(
        not args.output_dir.resolve().is_relative_to(research.parent),
        "measurement output must stay outside the repository",
    )
    resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
    require(args.manifest.stat().st_size <= 16 * 1024 * 1024, "manifest byte limit")
    manifest = args.manifest.read_bytes()
    cases = json.loads(manifest)
    require(isinstance(cases, list) and 0 < len(cases) <= 10000, "manifest case count")
    seen = set()
    for case in cases:
        require(
            all(
                re.fullmatch("[0-9a-f]{64}", case[key])
                for key in ("source_sha256", "pdf_sha256")
            ),
            "manifest hash syntax",
        )
        require(case["source_sha256"] not in seen, "duplicate source identity")
        seen.add(case["source_sha256"])
        require(
            type(case["native"]) is bool
            and type(case["pages"]) is int
            and 0 < case["pages"] <= 100000,
            "manifest page/native fields",
        )
        for key in ("source_path", "pdf_path"):
            require(isinstance(case[key], str) and case[key], "manifest path")
    # Pin all local modules that supply parsing, framing or bitmap evidence.
    scripts = (
        "source_image_geometry.py",
        "source_bitmap_identities.py",
        "hnc8_layout_source.py",
        "hnc8_text_frame.py",
        "native_text_order.py",
    )
    dependencies = [
        {"path": "scripts/" + name, "sha256": digest(research / "scripts" / name)}
        for name in scripts
    ]
    oracles, oracle_inputs = load_oracles(research)
    args.output_dir.mkdir(parents=False, exist_ok=False)
    start = time.monotonic()
    page_counts = collections.Counter()
    input_counts = collections.Counter()
    with (args.output_dir / "results.jsonl").open("x") as output:
        for case in cases:
            try:
                row = inspect(
                    args.manifest.parent / case["source_path"],
                    args.manifest.parent / case["pdf_path"],
                    case["source_sha256"],
                    case["pdf_sha256"],
                    native=case["native"],
                    oracles=oracles,
                )
                require(
                    len(row["pages"]) == case["pages"], "manifest page count differs"
                )
                row["status"] = (
                    "PASS"
                    if row["counts"] == {"PASS": case["pages"]}
                    and not row["parser_warnings"]
                    else "INCOMPLETE"
                )
                page_counts.update(row["counts"])
            except (
                ValueError,
                OSError,
                KeyError,
                TypeError,
                pikepdf.PdfError,
            ) as error:
                row = {
                    "source_sha256": case["source_sha256"],
                    "pdf_sha256": case["pdf_sha256"],
                    "status": "ERROR",
                    "reason": str(error),
                    "pages": [],
                    "expected_pages": case["pages"],
                }
                page_counts["NOT_CHECKED"] += case["pages"]
            input_counts[row["status"]] += 1
            output.write(json.dumps(row, separators=(",", ":")) + "\n")
            output.flush()
            print(
                json.dumps(
                    {
                        "completed": sum(input_counts.values()),
                        "source_sha256": case["source_sha256"],
                        "status": row["status"],
                    }
                ),
                flush=True,
            )
    unchanged = digest(args.manifest) == digest_bytes(manifest) and all(
        digest(research / item["path"]) == item["sha256"]
        for item in dependencies + oracle_inputs
    )
    summary = {
        "schema": "source-image-geometry-v1",
        "status": (
            "PASS"
            if input_counts == {"PASS": len(cases)} and unchanged
            else "INCOMPLETE"
        ),
        "manifest_sha256": digest_bytes(manifest),
        "dependencies": dependencies,
        "oracle_receipts": oracle_inputs,
        "measurement_inputs_unchanged": unchanged,
        "python_version": platform.python_version(),
        "pikepdf_version": pikepdf.__version__,
        "qpdf_library_version": pikepdf.__libqpdf_version__,
        "zlib_version": zlib.ZLIB_RUNTIME_VERSION,
        "source_unit_points": str(UNIT),
        "tolerance_points": str(TOLERANCE),
        "input_counts": dict(input_counts),
        "page_counts": dict(page_counts),
        "results_sha256": digest(args.output_dir / "results.jsonl"),
        "seconds": time.monotonic() - start,
    }
    with (args.output_dir / "summary.json").open("x") as output:
        json.dump(summary, output, indent=2)
        output.write("\n")
    print(json.dumps(summary), flush=True)
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
