# SPDX-License-Identifier: MIT
"""Original read-only audit of Indexed lookup lengths in frozen output PDFs."""
import argparse
import base64
import concurrent.futures
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
import warnings
import zlib


def file_hash(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def inspect(path, expected):
    import pikepdf
    if file_hash(path) != expected:
        raise ValueError("PDF identity mismatch")
    lookups = []
    unknown = []
    seen = set()
    visits = 0
    instructions = 0
    inline_count = 0

    def components(base):
        if isinstance(base, pikepdf.Name):
            return {"/DeviceGray": 1, "/G": 1, "/DeviceRGB": 3, "/RGB": 3,
                    "/DeviceCMYK": 4, "/CMYK": 4}.get(str(base))
        if isinstance(base, pikepdf.Array) and len(base):
            kind = str(base[0])
            if kind in {"/CalGray", "/Separation"}:
                return 1
            if kind in {"/CalRGB", "/Lab"}:
                return 3
            if kind == "/ICCBased" and len(base) == 2:
                return int(base[1]["/N"])
            if kind == "/DeviceN" and len(base) >= 4:
                return len(base[1])
        return None

    def palette(value, context):
        row = {"context": context, "array_items": len(value)}
        if len(value) != 4:
            row["status"] = "MALFORMED_INDEXED_ARRAY"
            lookups.append(row)
            return
        count = components(value[1])
        high = int(value[2])
        row.update(components=count, hival=high)
        if count is None or not 1 <= count <= 32 or not 0 <= high <= 255:
            row["status"] = "UNSUPPORTED_BASE_OR_HIVAL"
            lookups.append(row)
            return
        lookup = value[3]
        row["expected_bytes"] = count * (high + 1)
        if isinstance(lookup, pikepdf.String):
            data = bytes(lookup)
            row["kind"] = "string"
        elif isinstance(lookup, pikepdf.Stream):
            row["kind"] = "stream"
            row["lookup_object"] = list(lookup.objgen)
            if int(lookup.get("/Length", 0)) > 1048576:
                row["status"] = "LOOKUP_STREAM_LIMIT"
                lookups.append(row)
                return
            data = lookup.read_raw_bytes()
            filters = lookup.get("/Filter")
            if filters is None:
                pass
            elif str(filters) == "/FlateDecode" and lookup.get("/DecodeParms") is None:
                decoder = zlib.decompressobj()
                data = decoder.decompress(data, 65537)
                if len(data) > 65536 or not decoder.eof or decoder.unconsumed_tail:
                    row["status"] = "LOOKUP_DECODE_LIMIT_OR_BOUNDARY"
                    lookups.append(row)
                    return
                row["encoded_trailing_bytes"] = len(decoder.unused_data)
                row["encoded_tail_whitespace_only"] = all(c in b" \t\r\n\x00\x0c" for c in decoder.unused_data)
                if len(decoder.unused_data) > 16 or not row["encoded_tail_whitespace_only"]:
                    row["status"] = "UNEXAMINED_ENCODED_TRAILER"
                    lookups.append(row)
                    return
                row["qpdf_decoded_bytes_agree"] = lookup.read_bytes() == data
                if not row["qpdf_decoded_bytes_agree"]:
                    row["status"] = "DECODE_DISAGREEMENT"
                    lookups.append(row)
                    return
            elif str(filters) == "/ASCII85Decode" and lookup.get("/DecodeParms") is None:
                data = base64.a85decode(data.strip(), adobe=True)
                row["qpdf_decoded_bytes_agree"] = lookup.read_bytes() == data
                if not row["qpdf_decoded_bytes_agree"]:
                    row["status"] = "DECODE_DISAGREEMENT"
                    lookups.append(row)
                    return
            else:
                row["status"] = "UNTESTED_LOOKUP_FILTER"
                lookups.append(row)
                return
        else:
            row["status"] = "INVALID_LOOKUP_TYPE"
            lookups.append(row)
            return
        if len(data) > 65536:
            row["status"] = "LOOKUP_DECODE_LIMIT_OR_BOUNDARY"
            lookups.append(row)
            return
        row.update(actual_bytes=len(data), lookup_sha256=hashlib.sha256(data).hexdigest())
        row["status"] = "SHORT" if len(data) < row["expected_bytes"] else (
            "EXACT" if len(data) == row["expected_bytes"] else "EXTRA")
        lookups.append(row)

    def walk(value, context, depth=0, top=False):
        nonlocal visits
        visits += 1
        if visits > 1000000 or depth > 64:
            raise ValueError("graph visit limit")
        if isinstance(value, pikepdf.Object) and value.is_indirect:
            # The complete objects enumeration visits each indirect value.
            if not top:
                return
            identity = value.objgen
            if identity in seen:
                return
            seen.add(identity)
        if isinstance(value, pikepdf.Array):
            if len(value) and isinstance(value[0], pikepdf.Name) and str(value[0]) in {"/Indexed", "/I"}:
                palette(value, context)
            for i, item in enumerate(value):
                walk(item, f"{context}[{i}]", depth + 1)
        elif isinstance(value, (pikepdf.Dictionary, pikepdf.Stream)):
            for key, item in value.items():
                walk(item, f"{context}/{str(key)[1:]}", depth + 1)

    with pikepdf.Pdf.open(path, suppress_warnings=True) as pdf:
        if pdf.is_encrypted or len(pdf.objects) > 250000:
            raise ValueError("encrypted input or object limit")
        content_sources = {}
        for i, page in enumerate(pdf.pages, 1):
            contents = page.obj.get("/Contents")
            parts = list(contents) if isinstance(contents, pikepdf.Array) else [contents]
            if contents is None:
                continue
            if not all(isinstance(part, pikepdf.Stream) for part in parts):
                unknown.append({"context": f"page:{i}", "reason": "NON_STREAM_CONTENTS"})
                continue
            # A page's array is one logical content sequence: a token may span
            # stream boundaries. Parsing each stream independently loses data.
            key = ("page", tuple(part.objgen for part in parts))
            content_sources[key] = (page, f"page:{i}")
        for obj in pdf.objects:
            if not isinstance(obj, pikepdf.Object):
                continue
            context = f"object:{obj.objgen[0]}:{obj.objgen[1]}"
            walk(obj, context, top=True)
            if isinstance(obj, pikepdf.Stream) and (
                str(obj.get("/Subtype")) == "/Form" or obj.get("/PatternType") == 1
            ):
                content_sources[("form-or-pattern", obj.objgen)] = (obj, context)
        pdf_warnings = pdf.get_warnings()
        python_warning_count = 0
        for stream, context in content_sources.values():
            try:
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    parsed = pikepdf.parse_content_stream(stream)
                python_warning_count += len(caught)
                if caught:
                    unknown.append({"context": context, "reason": "CONTENT_PARSER_WARNING",
                                    "count": len(caught)})
                for item in parsed:
                    instructions += 1
                    if instructions > 5000000:
                        raise ValueError("instruction limit")
                    if isinstance(item, pikepdf.ContentStreamInlineImage):
                        inline_count += 1
                        walk(item.iimage.obj, f"{context}/inline:{inline_count}")
                del parsed
            except Exception as exc:
                unknown.append({"context": context, "reason": type(exc).__name__})
            emitted = pdf.get_warnings()
            if emitted:
                unknown.append({"context": context, "reason": "QPDF_CONTENT_WARNING",
                                "count": len(emitted)})
                pdf_warnings.extend(emitted)
        pages = len(pdf.pages)
        objects = len(pdf.objects)
    if file_hash(path) != expected:
        raise ValueError("PDF identity mismatch")
    return {
        "pdf_sha256": expected, "pdf_unchanged": True,
        "scope": "All indirect objects and their direct dictionary/array values; inline palettes in each complete page content sequence, Form and tiling-pattern stream. Does not prove palette usage or visual fidelity.",
        "pages": pages, "objects": objects, "graph_visits": visits,
        "content_sequences": len(content_sources), "instructions": instructions,
        "inline_images": inline_count, "palettes": lookups,
        "incomplete_content_streams": unknown,
        "qpdf_warning_count": len(pdf_warnings),
        "qpdf_warnings_sha256": hashlib.sha256("\n".join(pdf_warnings).encode()).hexdigest(),
        "python_content_warning_count": python_warning_count,
        "status": "INCOMPLETE" if unknown else "COMPLETE",
        "pikepdf_version": pikepdf.__version__,
    }


def limited():
    resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (40, 40))


def run(row, output):
    start = time.monotonic()
    try:
        process = subprocess.run(
            [sys.executable, __file__, "--worker", row["pdf"], row["pdf_sha256"]],
            capture_output=True, timeout=50,
        )
        result = json.loads(process.stdout) if process.returncode == 0 else {
            "status": "PROCESS_FAILURE", "exit_code": process.returncode,
            "stderr_bytes": len(process.stderr),
            "stderr_sha256": hashlib.sha256(process.stderr).hexdigest(),
        }
    except subprocess.TimeoutExpired:
        result = {"status": "TIMEOUT", "timeout_seconds": 50}
    result.update(source_sha256=row["source_sha256"], pdf_sha256=row["pdf_sha256"],
                  format=row["format"], seconds=round(time.monotonic() - start, 3))
    (output / (row["source_sha256"] + ".json")).write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path,
                        help="JSON array of source_sha256, pdf, pdf_sha256 and format")
    parser.add_argument("output", type=Path, help="new external directory for receipts")
    args = parser.parse_args()
    rows = json.loads(args.manifest.read_text())
    if not rows or len(rows) > 10000:
        parser.error("manifest must contain 1..10000 documents")
    for row in rows:
        for key in ("source_sha256", "pdf_sha256"):
            value = row[key]
            if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                parser.error("invalid SHA-256")
    if len({row["source_sha256"] for row in rows}) != len(rows):
        parser.error("duplicate source identity")
    args.output.mkdir(parents=True, exist_ok=False)
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda row: run(row, args.output), rows))
    summary = {
        "script_sha256": file_hash(Path(__file__)),
        "manifest_sha256": file_hash(args.manifest),
        "count": len(results), "results": results,
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    complete = all(r["status"] == "COMPLETE" and all(
        p["status"] in {"EXACT", "EXTRA"} for p in r.get("palettes", [])
    ) for r in results)
    print(json.dumps({"count": len(results), "all_lookup_lengths_sufficient": complete}))
    return 0 if complete else 1


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        try:
            limited()
            print(json.dumps(inspect(Path(sys.argv[2]), sys.argv[3])))
        except Exception as exc:
            print(json.dumps({"status": "INSPECTION_FAILURE", "reason": type(exc).__name__}))
    else:
        sys.exit(main())
