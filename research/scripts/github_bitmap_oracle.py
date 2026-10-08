#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Opt-in source bitmap checks; external documents, pixels and tools stay external.

This reuses the original source extractor and existing external black-box
protocols. It checks image identity/order, not placement or full-page fidelity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from hnc8_layout_source import FileInput, SourceExtractor
from current_format_order import extracted_image, images_match
import jbig1_oracle
import jbig2_oracle


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def source_image(source: Path, image: dict, library: Path, tools: dict) -> dict:
    kind = image["record_type"]
    if kind in (1, 2):
        return {"status": "PASS", "identity": ["jpeg", image["payload_sha256"]],
                "method": "unchanged JPEG payload"}
    case = {"source_path": source, "offset": image["payload_offset"],
            "length": image["payload_length"], "width": image["width"],
            "height": image["height"], "encoded_sha256": image["payload_sha256"],
            "stride": image["dib_stride"]}
    if kind == 0:
        # decode_image launches two fresh timed workers with distinct prefills
        # and guarded buffers; neither is the Rust converter's decoder.
        result = jbig1_oracle.decode_image(library, source, case, 20, 64 << 20, 128 << 20)
        if result["status"] != "PASS":
            raise ValueError(result.get("reason", "type-0 oracle failed"))
        return {**result, "identity": ["bits", case["width"], case["height"],
                                       result["visible_bits_sha256"]],
                "method": "pinned external type-0 decoder, two guarded prefills"}
    if kind == 3:
        # The independently written wrapper copies the entire source payload
        # after its measured DIB. No candidate-decoded pixels enter the oracle.
        digest, black_bits, pdf_bytes = jbig2_oracle.decode_case(
            case, tools, image["payload_sha256"])
        return {"status": "PASS", "identity": ["bits", case["width"], case["height"], digest],
                "black_pixels": black_bits, "wrapper_bytes": pdf_bytes,
                "method": "source JBIG2 wrapper, Poppler/MuPDF agreement",
                "decoder_implementation_independence": "UNVERIFIED"}
    raise ValueError(f"no independent decoder for image type {kind}")


def check_page(pdf: Path, page: int, images: list[dict], expected: list[tuple],
               tools: dict) -> dict:
    with tempfile.TemporaryDirectory(prefix="caj2pdf-bitmap-page-") as directory:
        temporary = Path(directory)
        jbig2_oracle.run_tool(
            [str(tools["pdfimages"]), "-f", str(page), "-l", str(page), "-j",
             str(pdf), str(temporary / "image")], temporary / "extract.log")
        files = sorted(temporary.glob("image-*"),
                       key=lambda path: int(path.stem.rsplit("-", 1)[1]))
        if len(files) > 8192:
            raise ValueError("extracted image count exceeds page limit")
        actual = [extracted_image(path, bottom_up=index < len(images)
                                  and images[index]["record_type"] == 0)
                  for index, path in enumerate(files)]
    # No expected/actual images is not a bitmap proof of a native-text page.
    status = "NOT_APPLICABLE" if not expected and not actual else (
        "PASS" if images_match(expected, actual) else "FAIL")
    return {"status": status, "actual": actual, "images": len(actual),
            "repeated_source_descriptors": len(expected) - len(actual)
            if status == "PASS" else 0}


def verify(source: Path, pdf: Path, source_sha: str, pdf_sha: str,
           library: Path, tools: dict) -> dict:
    if sha256(library) != jbig1_oracle.PINNED_LIBRARY_SHA256:
        raise ValueError("external type-0 decoder differs from the pinned build")
    if sha256(source) != source_sha or sha256(pdf) != pdf_sha:
        raise ValueError("source or candidate PDF differs from the pinned input")
    report = {"source_sha256": source_sha, "output_sha256": pdf_sha,
              "status": "PASS", "pages": [], "scope": "source bitmap identity and page/image order"}
    # A page count check prevents an extra empty/native-text page from escaping
    # per-page image checks. qpdf's bounded metadata is parsed independently.
    with tempfile.TemporaryDirectory(prefix="caj2pdf-bitmap-count-") as directory:
        log = Path(directory) / "pages.txt"
        jbig2_oracle.run_tool([str(tools["qpdf"]), "--show-npages", str(pdf)], log)
        if log.stat().st_size > 64:
            raise ValueError("unexpected page count response")
        output_pages = int(log.read_text().strip())
    cache = {}
    with FileInput(source) as stream:
        extractor = SourceExtractor(stream, source_sha)
        if output_pages != extractor.header["page_count"]:
            raise ValueError("source and output page counts differ")
        report["header"] = extractor.header
        for page in extractor.iter_pages():
            entry = {"page": page["page_number"], "images": []}
            expected = []
            for image in page["images"]:
                key = (image["record_type"], image["payload_sha256"], image["width"], image["height"])
                try:
                    if key not in cache:
                        cache[key] = source_image(source, image, library, tools)
                    oracle = cache[key]
                    expected.append(tuple(oracle["identity"]))
                except (ValueError, OSError, jbig1_oracle.OracleError, jbig2_oracle.OracleError) as error:
                    oracle = {"status": "FAIL", "reason": str(error)}
                entry["images"].append({**image, "oracle": oracle})
            if any(image["oracle"]["status"] != "PASS" for image in entry["images"]):
                entry["output"] = {"status": "NOT_RUN", "reason": "source image oracle failed"}
            else:
                try:
                    entry["output"] = check_page(pdf, page["page_number"], page["images"], expected, tools)
                except (ValueError, OSError, jbig2_oracle.OracleError) as error:
                    entry["output"] = {"status": "FAIL", "reason": str(error)}
            if entry["output"]["status"] != "PASS":
                report["status"] = "FAIL"  # An incomplete bitmap proof is never PASS.
            report["pages"].append(entry)
    report["source_integrity"] = sha256(source) == source_sha
    report["output_integrity"] = sha256(pdf) == pdf_sha
    report["oracle_integrity"] = sha256(library) == jbig1_oracle.PINNED_LIBRARY_SHA256
    if not all(report[key] for key in ("source_integrity", "output_integrity", "oracle_integrity")):
        report["status"] = "FAIL"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--pdf-sha256", required=True)
    parser.add_argument("--oracle-lib", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    if args.output.resolve().is_relative_to(root):
        parser.error("measurement output must stay outside the repository")
    tools = {name: Path(shutil.which(name) or name) for name in ("qpdf", "pdfimages", "mutool")}
    report = verify(args.source, args.pdf, args.source_sha256, args.pdf_sha256, args.oracle_lib, tools)
    # Refuse overwrite, including any accidental alias to a source/PDF.
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
