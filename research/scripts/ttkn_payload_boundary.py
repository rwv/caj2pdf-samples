# SPDX-License-Identifier: MIT
"""Measure TTKN payloads after disabling handler selection in external copies.

This is a destructive diagnostic on copies, never a recovery or converter.
Only structural metadata and hashes are exported; payload bytes stay external.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import resource
import subprocess
import zlib

import pikepdf

CHUNK = 65536
MAX_SOURCE = 512 * 1024 * 1024
MAX_STREAM = 16 * 1024 * 1024
MAX_OBJECTS = 100000


def require(condition):
    if not condition:
        raise ValueError("outside the bounded measured diagnostic profile")


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def copy_bytes(source, target, count):
    while count:
        chunk = source.read(min(CHUNK, count))
        require(bool(chunk))
        target.write(chunk)
        count -= len(chunk)


def disable_handler(source_path, expected, pdf_end, output):
    """Rename exactly one final-trailer key without moving any PDF object."""
    require(digest(source_path) == expected)
    require(0 < pdf_end <= source_path.stat().st_size <= MAX_SOURCE)
    with source_path.open("rb") as source:
        start = max(0, pdf_end - CHUNK)
        source.seek(start)
        tail = source.read(pdf_end - start)
        ending = re.search(rb"startxref\s+(\d+)\s+%%EOF[\r\n]*\Z", tail)
        require(ending is not None)
        trailer = tail.rfind(b"trailer", 0, ending.start())
        require(trailer >= 0)
        dictionary = tail[trailer + 7:ending.start()]
        require(len(dictionary) <= 4096)
        require(b"/Prev" not in dictionary and b"/XRefStm" not in dictionary)
        require(b"/Xncrypt" not in dictionary)
        matches = list(re.finditer(rb"/Encrypt\s+(\d+)\s+(\d+)\s+R", dictionary))
        require(len(matches) == 1)
        selected = matches[0]
        key_offset = start + trailer + 7 + selected.start()
        xref_at = int(ending[1])
        require(0 < xref_at < start + trailer)
        source.seek(xref_at)
        require(source.read(4) == b"xref")
        source.seek(0)
        with output.open("xb") as target:
            copy_bytes(source, target, key_offset)
            require(source.read(8) == b"/Encrypt")
            target.write(b"/Xncrypt")
            copy_bytes(source, target, pdf_end - source.tell())
    require(digest(source_path) == expected)
    require(output.stat().st_size == pdf_end)
    return {"trailer_key_offset": key_offset,
            "original_encrypt_reference": [int(selected[1]), int(selected[2])],
            "diagnostic_sha256": digest(output), "diagnostic_bytes": pdf_end}


def flate_boundary(raw, limit=MAX_STREAM):
    """Distinguish complete zlib data, failure, trailing data and limits."""
    require(len(raw) <= MAX_STREAM and 0 < limit <= MAX_STREAM)
    decoder = zlib.decompressobj()
    try:
        decoded = decoder.decompress(raw, limit + 1)
    except zlib.error:
        return {"status": "INVALID_ZLIB"}
    if len(decoded) > limit or decoder.unconsumed_tail:
        return {"status": "OUTPUT_LIMIT"}
    if not decoder.eof:
        return {"status": "INCOMPLETE_ZLIB"}
    if decoder.unused_data:
        return {"status": "TRAILING_DATA"}
    return {"status": "VALID_COMPLETE_ZLIB", "decoded_bytes": len(decoded)}


def payload_inventory(path):
    rows = []
    with pikepdf.open(path) as pdf:
        require(len(pdf.objects) <= MAX_OBJECTS)
        require("/Encrypt" not in pdf.trailer)
        for obj in pdf.objects:
            if not isinstance(obj, pikepdf.Stream):
                continue
            length = obj.get("/Length")
            require(isinstance(length, int) and 0 <= length <= MAX_STREAM)
            raw = obj.read_raw_bytes()
            require(len(raw) == length)
            value = obj.get("/Filter")
            if value is None:
                filters = []
            elif isinstance(value, pikepdf.Name):
                filters = [str(value)]
            elif isinstance(value, pikepdf.Array):
                require(len(value) <= 8 and all(isinstance(f, pikepdf.Name) for f in value))
                filters = [str(f) for f in value]
            else:
                raise ValueError("unmeasured filter value")
            require(all(f in {"/FlateDecode", "/DCTDecode", "/JPXDecode", "/JBIG2Decode", "/CCITTFaxDecode"}
                        for f in filters))
            # Non-Flate filters require their own decoders. A raw read or a
            # library's unsupported-filter error says nothing about plaintext.
            check = flate_boundary(raw) if filters == ["/FlateDecode"] else {
                "status": "NOT_CHECKED", "reason": "not a single Flate stream",
            }
            rows.append({"object": list(obj.objgen), "raw_bytes": length,
                         "length_modulo_16": length % 16, "filters": filters,
                         "flate_check": check})
        warnings = pdf.get_warnings()
        result = {"pages_in_plaintext_object_graph": len(pdf.pages),
                  "objects": len(pdf.objects), "parser_warning_count": len(warnings),
                  "parser_warnings": warnings,
                  "streams": rows}
    result["stream_counts"] = {
        "total": len(rows),
        "length_modulo_16": dict(collections.Counter(r["length_modulo_16"] for r in rows)),
        "filters": dict(collections.Counter("+".join(r["filters"]) or "NONE" for r in rows)),
        "flate_check": dict(collections.Counter(r["flate_check"]["status"] for r in rows)),
    }
    return result


def qpdf_limits():
    resource.setrlimit(resource.RLIMIT_AS, (1024 ** 3, 1024 ** 3))
    resource.setrlimit(resource.RLIMIT_CPU, (40, 40))
    resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024 ** 2, 8 * 1024 ** 2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path, help="pinned ttkn_inventory JSON with sources")
    parser.add_argument("documents", type=Path, help="external SHA256.caj originals")
    parser.add_argument("output", type=Path, help="new external diagnostic directory")
    args = parser.parse_args()
    sources = json.loads(args.inventory.read_text())["sources"]
    require(0 < len(sources) <= 100)
    require(len({r["source_sha256"] for r in sources}) == len(sources))
    resource.setrlimit(resource.RLIMIT_AS, (1024 ** 3, 1024 ** 3))
    args.output.mkdir(exist_ok=False)
    rows = []
    for entry in sources:
        sha = entry["source_sha256"]
        require(re.fullmatch(r"[0-9a-f]{64}", sha))
        source = args.documents / (sha + ".caj")
        target = args.output / (sha + ".pdf")
        copy = disable_handler(source, sha, entry["pdf"]["extent"][1], target)
        payloads = payload_inventory(target)
        log = args.output / (sha + ".qpdf.log")
        with log.open("xb") as output:
            completed = subprocess.run(["qpdf", "--check", str(target)], stdout=output,
                                       stderr=subprocess.STDOUT, timeout=50,
                                       preexec_fn=qpdf_limits)
        require(completed.returncode in {0, 2, 3})
        require(digest(source) == sha and digest(target) == copy["diagnostic_sha256"])
        row = {"source_sha256": sha, "source_unchanged": True,
               "wrapper_profile": entry["wrapper"]["profile"], "diagnostic": copy,
               "qpdf_exit": completed.returncode, "qpdf_log_sha256": digest(log),
               **payloads}
        rows.append(row)
        print(json.dumps({"source": sha, "qpdf_exit": completed.returncode,
                          "counts": row["stream_counts"]}), flush=True)
    report = {"scope": __doc__, "script_sha256": digest(Path(__file__)),
              "inventory_sha256": digest(args.inventory), "pikepdf_version": pikepdf.__version__,
              "zlib_version": zlib.ZLIB_RUNTIME_VERSION, "rows": rows}
    (args.output / "receipt.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
