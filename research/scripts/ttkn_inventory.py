# SPDX-License-Identifier: MIT
"""Read-only inventory of the measured TTKN PDF/rights-wrapper profile.

Requires pikepdf and cryptography as external research tools. Outputs only
allowlisted structure, lengths and document hashes. It neither decrypts data
nor exports credential fields. This is not a general PDF or rights parser.
"""

import argparse
import base64
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import cryptography
import pikepdf
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import rsa

WINDOW = 65536
OBJECT_LIMIT = 4096
XREF_LIMIT = 100000
TAGS = {
    "right-meta", "file-id", "file-app", "o-name", "version", "protect",
    "auth", "update-url", "reg-machine-url", "permit", "cert", "password",
    "pfx", "iv", "rights", "url", "server",
}
ATTRIBUTES = {"type", "no-binding"}


def require(condition):
    if not condition:
        raise ValueError("input is outside the measured structural profile")


def digest(source, length):
    source.seek(0)
    h = hashlib.sha256()
    remaining = length
    while remaining:
        chunk = source.read(min(WINDOW, remaining))
        require(bool(chunk))
        h.update(chunk)
        remaining -= len(chunk)
    return h.hexdigest()


def encryption_profile(raw):
    d = pikepdf.Object.parse(raw)
    expected = {
        "/Filter": "/TTKN.PubSec", "/SubFilter": "/TTKN.PubSec.s1",
        "/StmF": "/DefaultCryptFilter", "/StrF": "/DefaultCryptFilter",
    }
    require(set(d.keys()) == set(expected) | {
        "/Length", "/R", "/V", "/EncryptMetadata", "/CF",
    })
    require(all(str(d[k]) == v for k, v in expected.items()))
    require(all(d[k] == v for k, v in {
        "/Length": 40, "/R": 2, "/V": 2, "/EncryptMetadata": True,
    }.items()))
    require(set(d.CF.keys()) == {"/DefaultCryptFilter"})
    cf = d.CF.DefaultCryptFilter
    require(set(cf.keys()) == {"/CFM", "/Recipients"})
    require(str(cf.CFM) == "/AESV2" and len(cf.Recipients) == 1)
    require(bytes(cf.Recipients[0]) == b"AppendCA")
    return {
        **{k[1:]: v[1:] for k, v in expected.items()},
        "Length": 40, "R": 2, "V": 2, "EncryptMetadata": True,
        "CF": {"DefaultCryptFilter": {
            "CFM": "AESV2", "recipient_count": 1,
            "recipient_bytes": 8, "recipient_is_fixed_AppendCA_marker": True,
            "recipient_is_pkcs7_sequence": False,
        }},
    }


def xref_entry(source, offset, object_number):
    source.seek(offset)
    require(source.read(4) == b"xref")
    selected = None
    total = 0
    while True:
        require(source.tell() - offset <= XREF_LIMIT * 128 + OBJECT_LIMIT)
        line_start = source.tell()
        line = source.readline(128)
        require(bool(line) and len(line) < 128)
        line = line.strip()
        if not line:
            continue
        if line == b"trailer":
            return selected, total, line_start
        m = re.fullmatch(rb"(\d+)\s+(\d+)", line)
        require(m is not None)
        start, count = map(int, m.groups())
        total += count
        require(total <= XREF_LIMIT and start + count <= XREF_LIMIT)
        for number in range(start, start + count):
            line = source.readline(128)
            require(len(line) < 128)
            m = re.fullmatch(rb"(\d{10}) (\d{5}) ([nf])\s*", line)
            require(m is not None)
            if number == object_number:
                require(selected is None and m[3] == b"n")
                selected = (int(m[1]), int(m[2]))


def wrapper_fields(xml):
    require(len(xml) <= WINDOW)
    require(b"<!DOCTYPE" not in xml and b"<!ENTITY" not in xml)
    root = ET.fromstring(xml)
    require(root.tag == "right-meta")
    fields = []
    for e in root.iter():
        require(e.tag in TAGS and set(e.attrib) <= ATTRIBUTES)
        require(len(fields) < 64)
        raw = (e.text or "").strip().encode("utf-8")
        item = {
            "tag": e.tag, "children": len(e), "text_utf8_bytes": len(raw),
            "attribute_value_lengths": {k: len(v) for k, v in e.attrib.items()},
        }
        if not len(e) and e.tag in {"password", "pfx", "iv", "rights"}:
            decoded = base64.b64decode(raw, validate=True)
            item["base64_decoded_bytes"] = len(decoded)
            item["starts_as_asn1_sequence"] = decoded[:1] == b"\x30"
            item["decoded_length_modulo_16"] = len(decoded) % 16
            if e.tag == "pfx":
                item["decoded_is_ascii_base64"] = all(
                    c in b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\r\n"
                    for c in decoded
                )
        elif not len(e) and e.tag == "cert":
            cert = x509.load_pem_x509_certificate(raw)
            key = cert.public_key()
            require(isinstance(key, rsa.RSAPublicKey))
            item["certificate"] = {
                "encoding": "PEM X.509", "public_key_algorithm": "RSA",
                "public_key_bits": key.key_size,
                "signature_algorithm_oid": cert.signature_algorithm_oid.dotted_string,
                "private_key_material": "NOT PROVIDED BY X.509 CERTIFICATE",
                "trust_or_current_validity_checked": False,
            }
        fields.append(item)
    return fields


def inventory(path, expected_hash, origin):
    size = path.stat().st_size
    with path.open("rb") as source:
        require(digest(source, size) == expected_hash)
        source.seek(0)
        header = source.read(16)
        version = re.match(rb"%PDF-(1\.\d)", header)
        require(version is not None)
        tail_offset = max(0, size - WINDOW)
        source.seek(tail_offset)
        tail = source.read(WINDOW)
        endings = list(re.finditer(rb"startxref\s+(\d+)\s+%%EOF[\r\n]*", tail))
        require(len(endings) == 1)
        ending = endings[0]
        pdf_end = tail_offset + ending.end()
        xref_offset = int(ending[1])
        require(0 < xref_offset < pdf_end)
        trailer_start = tail.rfind(b"trailer", 0, ending.start())
        require(trailer_start >= 0)
        trailer = tail[trailer_start + 7:ending.start()].strip()
        require(len(trailer) <= OBJECT_LIMIT and b"/Prev" not in trailer)
        require(b"/XRefStm" not in trailer)
        enc_refs = re.findall(rb"/Encrypt\s+(\d+)\s+(\d+)\s+R", trailer)
        require(len(enc_refs) == 1)
        enc_number, enc_generation = map(int, enc_refs[0])
        entry, entries, parsed_trailer_offset = xref_entry(source, xref_offset, enc_number)
        require(entry is not None and entry[1] == enc_generation)
        require(parsed_trailer_offset == tail_offset + trailer_start)
        source.seek(entry[0])
        object_bytes = source.read(OBJECT_LIMIT)
        head = re.match(rb"(\d+)\s+(\d+)\s+obj\s*", object_bytes)
        require(head is not None and tuple(map(int, head.groups())) == (enc_number, enc_generation))
        end = object_bytes.find(b"endobj", head.end())
        require(end >= 0 and entry[0] + end + 6 <= xref_offset)
        profile = encryption_profile(object_bytes[head.end():end])
        suffix = tail[ending.end():]
        require(suffix.startswith(b"WebFastLoad\0"))
        xml_at = len(b"WebFastLoad\0")
        xml_end = suffix.find(b"</right-meta>") + len(b"</right-meta>")
        require(xml_end > xml_at and suffix[xml_at:].startswith(b"<right-meta>"))
        xml = suffix[xml_at:xml_end]
        fields = wrapper_fields(xml)
        declared = re.search(rb"startrights (\d+),(\d+)", suffix[xml_end:])
        require(declared is not None)
        declared_offset, declared_length = map(int, declared.groups())
        require(declared_offset == pdf_end + xml_at)
        certs = sum("certificate" in f for f in fields)
        pfx_count = sum(f["tag"] == "pfx" for f in fields)
        require((certs, pfx_count) in {(1, 1), (0, 0)})
        profile_id = "embedded-certificate-and-opaque-pfx" if pfx_count else "auth-url-without-certificate-or-pfx"
        result = {
            "source_sha256": expected_hash, "size_bytes": size, "origin": origin,
            "pdf": {"version": version[1].decode(), "extent": [0, pdf_end],
                    "sha256": digest(source, pdf_end), "xref_offset": xref_offset,
                    "xref_entry_count": entries, "incremental_or_hybrid_xref": False,
                    "encryption_object": [enc_number, enc_generation],
                    "encryption_object_extent": [entry[0], entry[0] + end + 6],
                    "encryption_profile": profile},
            "wrapper": {
                "profile": profile_id, "marker": "WebFastLoad NUL",
                "xml_extent": [pdf_end + xml_at, pdf_end + xml_end],
                "declared_xml_offset": declared_offset,
                "declared_xml_length": declared_length,
                "actual_xml_bytes": len(xml), "tail_bytes": len(suffix),
                "bytes_after_xml": len(suffix) - xml_end, "fields": fields,
            },
            "missing_information": [
                "TTKN.PubSec.s1 handler and wrapper semantics, including mapping the AppendCA marker to key material",
                "Validated credential/key unwrapping and file-key derivation for this wrapper profile",
                "Whole-document recovery and independent content verification",
            ],
            "recovery_status": "UNRESOLVED; NOT PROVEN IRRECOVERABLE",
        }
        require(digest(source, size) == expected_hash)
        result["source_unchanged"] = True
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--sha256", action="append", required=True)
    args = parser.parse_args()
    require(len(args.sha256) <= 64 and len(set(args.sha256)) == len(args.sha256))
    catalog = json.loads(args.catalog.read_text())["samples"]
    rows = []
    for sha in args.sha256:
        require(re.fullmatch("[0-9a-f]{64}", sha) is not None)
        matches = [row for row in catalog if row["sha256"] == sha]
        require(len(matches) == 1)
        row = matches[0]
        origin = {k: row[k] for k in ("path", "source_repository", "source_revision")}
        rows.append(inventory(args.source_dir / (sha + ".caj"), sha, origin))
    print(json.dumps({
        "scope": "Bounded read-only original-source structure; no key, credential, XML value, document payload or embedded URL is exported or contacted.",
        "limits": {"read_chunk_and_tail_bytes": WINDOW, "object_bytes": OBJECT_LIMIT,
                   "xref_entries": XREF_LIMIT, "xref_line_bytes": 128, "xml_elements": 64},
        "tools": {"pikepdf": pikepdf.__version__, "cryptography": cryptography.__version__},
        "sources": rows,
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, ET.ParseError):
        # Library exception text may contain supplied bytes; never echo it.
        raise SystemExit("inventory refused input outside the measured profile") from None
