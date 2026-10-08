# SPDX-License-Identifier: MIT
"""Two diagnostic completions preserve the same available source palette prefix.

The externally derived pixels/palettes/PDFs are never product fixes or fixtures
to commit. Only hashes/counts are emitted in the metadata receipt.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zlib

import fitz
import numpy as np
import pikepdf
from PIL import Image

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("source", type=Path, help="unchanged external #420 original")
parser.add_argument("output", type=Path, help="new external diagnostic directory")
args = parser.parse_args()
SOURCE = args.source
D = args.output
D.mkdir(parents=True, exist_ok=False)
SHA = "5e1ea482a56a2df02a2a452ac97949824c726471c88157e78441a1201b3d8697"
# Measured extents in this exact original, not a generalized PDF object scanner.
spans = {319: (889144, 889194), 386: (908159, 1009805)}
INDEX_SHA256 = "ce4f26f23bb48d2963186f4f4ebc347c64667a84ebf123c7902d04b6dc57a171"


def require(condition):
    if not condition:
        raise ValueError("input is outside the exact measured diagnostic profile")


def H(data):
    return hashlib.sha256(data).hexdigest()


def filehash(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


require(filehash(SOURCE) == SHA)
with SOURCE.open("rb") as f:
    a, b = spans[319]
    f.seek(a)
    raw = f.read(b - a)
    match = re.fullmatch(rb"319 0 obj\r(\[/Indexed /DeviceCMYK 43 .* \])\rendobj\r", raw, re.S)
    require(match)
    value = pikepdf.Object.parse(match[1])
    prefix = bytes(value[3])
    require(len(prefix) == 3)
    form_a, form_b = spans[386]
    f.seek(form_a)
    form = f.read(form_b - form_a)
    marker = re.search(rb"stream\r?\n", form)
    require(marker and marker.start() < 2048)
    length = int(re.search(rb"/Length\s+(\d+)(?=[/\s>])", form[:marker.start()])[1])
    encoded = form[marker.end():marker.end() + length]
    require(re.fullmatch(rb"\s*endstream\s+endobj\s*", form[marker.end() + length:]))
    decoder = zlib.decompressobj()
    content = decoder.decompress(encoded, 4000001)
    require(len(content) <= 4000000 and decoder.eof and not decoder.unconsumed_tail)
    require(not decoder.unused_data)
at = 222733
data_at = content.index(b"ID ", at, at + 512) + 3
require(b"/DP" not in content[at:data_at])
decoder = zlib.decompressobj()
indices = decoder.decompress(content[data_at:], 4000001)
require(decoder.eof and not decoder.unconsumed_tail)
require(re.match(rb"\s+EI\b", decoder.unused_data))
require(H(indices) == INDEX_SHA256)
require(len(indices) == 33 * 15 and set(indices) == set(range(44)))

outputs = []
images = {}
for label, black in [("completion-a", 0), ("completion-b", 255)]:
    lookup = bytearray(176)
    lookup[:3] = prefix
    for index in range(44):
        lookup[index * 4 + 3] = black
    require(bytes(lookup[:3]) == prefix)
    pdf = pikepdf.Pdf.new()
    page = pdf.add_blank_page(page_size=(350, 170))
    im = pikepdf.Stream(pdf, indices)
    im.Type = pikepdf.Name.XObject
    im.Subtype = pikepdf.Name.Image
    im.Width = 33
    im.Height = 15
    im.BitsPerComponent = 8
    im.ColorSpace = pikepdf.Array([
        pikepdf.Name.Indexed, pikepdf.Name.DeviceCMYK, 43, pikepdf.String(bytes(lookup))
    ])
    page.Resources = pikepdf.Dictionary(XObject=pikepdf.Dictionary(Im=im))
    page.Contents = pikepdf.Stream(pdf, b"q 330 0 0 150 10 10 cm /Im Do Q\n")
    target = D / (label + ".pdf")
    pdf.save(target)
    q = subprocess.run(["qpdf", "--check", str(target)], capture_output=True, timeout=20)
    require(q.returncode == 0)
    rendered = D / label
    p = subprocess.run(["pdftoppm", "-r", "72", "-singlefile", "-png", str(target), str(rendered)],
                       capture_output=True, timeout=20)
    require(p.returncode == 0 and not p.stderr)
    rgb = np.array(Image.open(rendered.with_suffix(".png")).convert("RGB"))
    with fitz.open(target) as doc:
        pix = doc[0].get_pixmap(colorspace=fitz.csRGB, alpha=False)
        mupdf = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, 3))
    images[label] = (rgb, mupdf)
    outputs.append({
        "label": label, "pdf_sha256": filehash(target), "lookup_bytes": len(lookup),
        "lookup_sha256": H(lookup), "available_prefix_bytes_preserved": 3,
        "index_bytes_preserved": len(indices), "index_sha256": H(indices),
        "qpdf_exit": q.returncode, "poppler_exit": p.returncode,
        "poppler_rgb_sha256": H(rgb.tobytes()), "mupdf_rgb_sha256": H(mupdf.tobytes()),
    })
comparisons = []
for i, renderer in enumerate(["Poppler", "MuPDF"]):
    a, b = images["completion-a"][i], images["completion-b"][i]
    require(a.shape == b.shape)
    changed = np.any(a != b, axis=2)
    ys, xs = np.where(changed)
    require(changed.sum() > 0)
    comparisons.append({"renderer": renderer, "changed_pixels": int(changed.sum()),
                        "changed_channels": int((a != b).sum()),
                        "bounds": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]})
require(filehash(SOURCE) == SHA)
receipt = {
    "scope": "Information-loss diagnostic for a syntactically complete source lookup, not a repair or recovered intended colors.",
    "source_sha256": SHA, "source_unchanged": True,
    "palette_object": 319, "palette_extent": list(spans[319]),
    "base": "DeviceCMYK", "hival": 43, "required_bytes": 176,
    "available_decoded_bytes": 3, "missing_bytes": 173,
    "available_sha256": H(prefix), "executed_source_page": 24,
    "source_form": 386, "inline_image_offset": at, "image_width": 33, "image_height": 15,
    "original_unchanged_indices": {"bytes": len(indices), "sha256": H(indices), "used_indices": 44},
    "outputs": outputs, "comparisons": comparisons,
    "conclusion": "Both well-formed diagnostic tables preserve every available component byte and the entire original index image, yet render differently in both tools. The surviving prefix and indices do not uniquely determine the missing source colors. Neither completion is proposed for conversion.",
}
(D / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({"outputs": len(outputs), "comparisons": comparisons}, indent=2))
