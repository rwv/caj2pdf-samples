# SPDX-License-Identifier: MIT
"""Bounded C8/HN-B header and explicit application-info inventory.

This locates no outline format and does not prove outlines absent elsewhere.
Only structure, counts and hashes are exported, never XML text or link values.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET
import zlib

LIMIT = 1048576


def require(condition):
    if not condition:
        raise ValueError("input is outside the bounded measured profile")


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def application_info(source, size, index_end):
    source.seek(max(0, size - 64))
    tail = source.read(64)
    match = re.search(rb"APPINFOSIGN (\d+)\Z", tail)
    if not match:
        return {"status": "NO_FINAL_MARKER",
                "marker_name_elsewhere_in_tail": b"APPINFOSIGN" in tail}
    marker = size - len(tail) + match.start()
    start = int(match[1])
    result = {"status": "PRESENT", "offset": start, "marker_offset": marker}
    try:
        require(index_end <= start <= marker - 8)
        source.seek(start)
        declared, encoded = struct.unpack("<II", source.read(8))
        result.update(declared_decoded_bytes=declared, encoded_bytes=encoded)
        require(0 < declared <= LIMIT and encoded <= LIMIT)
        require(start + 8 + encoded == marker)
        decoder = zlib.decompressobj()
        xml = decoder.decompress(source.read(encoded), declared + 1)
        require(len(xml) == declared and decoder.eof)
        require(not decoder.unused_data and not decoder.unconsumed_tail)
        xml_text = xml.decode("utf-8")
        require("\0" not in xml_text and "<!DOCTYPE" not in xml_text and "<!ENTITY" not in xml_text)
        root = ET.fromstring(xml_text)
        nodes = list(root.iter())
        require(len(nodes) <= 100000)
        tags = collections.Counter(node.tag for node in nodes)
        attributes = collections.Counter(key for node in nodes for key in node.attrib)
        known = {"Link", "UrlLink", "Bookmark", "Outline", "TOC", "Contents", "BookMark"}
        types = collections.Counter(node.attrib["Type"] for node in nodes
                                    if node.attrib.get("Type") in known)
        result.update(
            status="PARSED", xml_sha256=hashlib.sha256(xml).hexdigest(),
            element_counts=dict(tags), attribute_name_counts=dict(attributes),
            known_structural_type_counts=dict(types),
            outline_named_elements=[tag for tag in tags if re.search(r"bookmark|outline|toc|contents", tag, re.I)],
            outline_named_attributes=[key for key in attributes if re.search(r"bookmark|outline|toc|contents", key, re.I)],
        )
    except (ValueError, struct.error, ET.ParseError, zlib.error) as error:
        result.update(status="UNRESOLVED", reason=type(error).__name__)
    return result


def inspect(path, expected):
    require(digest(path) == expected)
    size = path.stat().st_size
    with path.open("rb") as source:
        head = source.read(0xd8)
        require(len(head) >= 0x50)
        if head[:4] == b"\xc8\0\0\0":
            variant, count_at, index_start, row_bytes = "C8", 8, 0x50, 20
        else:
            require(head[:8] == b"HN\0\0\xc8\0\0\0" and len(head) == 0xd8)
            marker = struct.unpack_from("<I", head, 0x88)[0]
            require(marker in {0, 200})
            variant, count_at, index_start = "HN-B", 0x90, 0xd8
            row_bytes = 12 if marker == 0 else 20
        pages = struct.unpack_from("<i", head, count_at)[0]
        require(0 < pages <= 100000)
        index_end = index_start + pages * row_bytes
        require(index_end <= size)
        source.seek(index_start)
        first = source.read(row_bytes)
        text_at, text_length = struct.unpack_from("<II", first)
        require(index_end <= text_at <= size and text_length <= size - text_at)
        result = {
            "source_sha256": expected, "variant": variant, "pages": pages,
            "size_bytes": size, "page_index_offset": index_start,
            "page_row_bytes": row_bytes, "page_index_end": index_end,
            "first_text_offset": text_at, "first_text_length": text_length,
            "first_text_immediately_after_index": text_at == index_end,
            "application_info": application_info(source, size, index_end),
        }
    require(digest(path) == expected)
    return {**result, "source_unchanged": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path,
                        help="JSON array: source_sha256, variant, pages and source_id")
    parser.add_argument("documents", type=Path, help="external SHA256.caj inputs")
    parser.add_argument("output", type=Path, help="new metadata-only receipt file")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    require(0 < len(manifest) <= 10000)
    require(len({row["source_sha256"] for row in manifest}) == len(manifest))
    rows = []
    for entry in manifest:
        sha = entry["source_sha256"]
        require(re.fullmatch(r"[0-9a-f]{64}", sha))
        row = inspect(args.documents / (sha + ".caj"), sha)
        require(row["variant"] == entry["variant"] and row["pages"] == entry["pages"])
        rows.append({**row, "source_id": entry["source_id"]})
    result = {
        "scope": __doc__, "script_sha256": digest(Path(__file__)),
        "counts": {
            "documents": len(rows), "variants": dict(collections.Counter(r["variant"] for r in rows)),
            "pages": sum(r["pages"] for r in rows),
            "first_text_immediately_after_index": sum(r["first_text_immediately_after_index"] for r in rows),
            "application_info": dict(collections.Counter(r["application_info"]["status"] for r in rows)),
        }, "rows": rows,
    }
    with args.output.open("x") as output:
        output.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["counts"]))
    return int(any(r["application_info"]["status"] == "UNRESOLVED" for r in rows))


if __name__ == "__main__":
    raise SystemExit(main())
