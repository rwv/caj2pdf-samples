<!-- SPDX-License-Identifier: MIT -->

# Source bitmap coverage for the GitHub sweep

[samples #23](https://github.com/rwv/caj2pdf-samples/issues/23) fills the missing
source-image oracles tracked by [rust #406](https://github.com/rwv/caj2pdf-rust/issues/406).
The selected cohort is the 936 accepted originals whose frozen native harness
reports `page_order_check: NOT_RUN`. This note keeps that original result,
the new bitmap evidence and any complementary native-text evidence separate.

The native PDFs come from Rust candidate
`d6e23c3dd02ed1609e2ffee3da05313b8441231a`, subsequently merged through #413.
Every input/PDF identity is pinned in the receipt. The independent original MIT
source extractor discovers 13,991 pages and 15,708 image descriptors: 10,077
type 0, 3,150 type 3, 2,421 type 2 and 60 type 1. It checks complete source hashes
before/after and reads ranged source metadata, bounded image spans and one page
at a time. The native converter's image decoder never supplies expected pixels.
Within each document, identical source payload hashes/types/dimensions reuse
one oracle result; every descriptor still has independently checked source
framing and participates in its page's ordered comparison.

For type 0, the established external black-box protocol uses two fresh workers,
20-second timeouts, different buffer prefills and guards. Its pinned library
was reproduced exactly: SHA-256
`d370d071a4b7abdf7db4565c2bc85ac881470ee1a212459dd658d70974128de6`, from external
revision `8cbc3c5721acb762f739434eb3d206171dbb022a`, with Debian C++ 14.2.0 driver
`6b3696e4dcb85e1c949c732a02befa50e3983ecf94ce7e8e58d9d503b954b79d`.
Its source was not read or imported; the binary is only an external behavioral
oracle. The [existing protocol](jbig1-oracle.md) documents the ABI, provenance,
64 MiB encoded / 128 MiB decoded caps and exact hash conventions.

For type 3, an independently written minimal PDF wrapper copies the untouched
source JBIG2 payload following the measured DIB header. Qpdf validates the
wrapper, and Poppler extraction and MuPDF rendering must agree on every visible
bit. The two external tools' decoder implementation independence is unverified;
this is tool agreement, not proof of separate decoder code. The wrapper,
limits and normalization reuse the [existing protocol](jbig2-oracle.md).
JPEG types 1/2 are checked through their unchanged encoded payload hashes.

Each candidate PDF page is extracted separately. Hashes, dimensions and ordered
images must match. Type-0 expected pixels use bottom-up DIB rows, so only those
source descriptors select the measured reversal of Poppler's top-down PBM rows.
The checker never chooses whichever orientation matches. Repeated, byte-identical
source image groups are counted separately; their placement/alias semantics are
not proved by image identity. Empty expected images cannot pass against unexpected
output images. Empty source/output image lists are `NOT_APPLICABLE` and cannot
by themselves produce a complete document-level bitmap PASS.

Original two-page PDF unit controls verify the row convention and detect swapped
pages, removed images and a changed visible bit. External real-sample controls
also detect those changes and an extra empty page. CI installs qpdf and Poppler
for original controls; no corpus, external CAJ decoder or font is downloaded by CI.

This scoped check does not prove placement, page geometry, native font appearance,
vectors, source outlines or complete rendered-page fidelity. All external document,
PDF, raster, font and decoder bytes remain outside both repositories. The receipt
will record final counts and every failure without silently dropping inputs.

Run a single pinned input from the samples checkout (Python 3.11+):

```sh
python3 research/scripts/github_bitmap_oracle.py \
  --source /external/input.caj --source-sha256 SOURCE_SHA256 \
  --pdf /external/output.pdf --pdf-sha256 OUTPUT_SHA256 \
  --oracle-lib /external/libjbigdec.so --output /external/new-receipt.json
```

The output must be a new external path. Qpdf, Poppler `pdfimages` and MuPDF
`mutool` are required. A missing/different oracle or input hash refuses the check.
This command does not run the native-text oracle for image-free pages; its
strict document status remains incomplete until separate native-text evidence
is supplied. No `NOT_APPLICABLE`, missing or skipped check is a bitmap PASS.
