<!-- SPDX-License-Identifier: MIT -->

# Identical fragment page boxes: four-original verification

[rwv/caj2pdf-rust#407](https://github.com/rwv/caj2pdf-rust/issues/407) is implemented by
[PR #408](https://github.com/rwv/caj2pdf-rust/pull/408), candidate
`277d4229931ce156e5d7b62159fdd6722fa0f1b6`. The
[metadata receipt](fragment-mediabox-20261008.json) contains source/output hashes,
per-page geometry/text/render hashes, stream identities, runtime parity and
complete-corpus regression counts. Original documents and derived PDFs remain external.

The four unchanged CAJ originals contain exactly two equivalent direct MediaBox
values in a Page or Pages dictionary. Reconstruction blanks only the later pair,
preserving object widths and stream bytes. Conflicting, third, indirect or invalid
boxes, other duplicate names and stream dictionaries retain strict refusal.

## Evidence

All four complete originals pass native, Node and Chromium conversion with identical
output hashes, clean qpdf 12.2.0 checks and successful browser OPFS cleanup.
All 308 page identities, geometries, rotations and extracted texts match independently
framed original source bodies. All 308 RGB renders at 72 dpi match in PyMuPDF
1.27.2.2; 1,308 raw streams preserve object IDs and bytes. The existing independent
CAJ outline check passes all 218 source entries, including title, order and destination.

The reference preserves each original CAJ PDF body verbatim and adds only a Catalog
and missing page-tree ancestors inferred from source Parent links and the explicit
CAJ page table. MuPDF independently reconstructs the reference index. It does not
reuse converter-generated page content. A separate qpdf-normalized copy validates
cleanly but renders one page differently (page 69 of `6f30a4a0dc36…`); that discrepancy
is preserved in the receipt. Only the verbatim source-body reference is the pixel
oracle. This is neither CAJViewer parity nor proof for every renderer/resolution.

The full native regression runs 1,277 distinct originals and 2,126 attempts against
the #402 baseline. Results: **1,232 PASS, 35 FAIL, 10 UNSUPPORTED**. Only the four
listed sources improve; every previously passing output remains byte-identical.
Before/after source identity checks pass for every original. qpdf reports 1,231
clean results and one pre-existing warning. The archived page-order check still
reports 270 PASS, 26 FAIL and 936 NOT_RUN; source outlines report 285 PASS and
947 NOT_RUN. These incomplete ancillary checks remain separate from conversion.
[Issue #12](https://github.com/rwv/caj2pdf-samples/issues/12) tracks image-order
checker corrections; the historical receipts are not rewritten.

Local Rust workspace validation: 1,273 passed, zero failed and seven optional
corpus tests ignored (not compatibility passes). Clippy with warnings denied,
release native/WASM builds and all 164 JavaScript tests pass. The four required
quality statuses and four Linux native gates passed on the candidate commit.
Review was self-review, not independent approval.

The wider correctness goal remains open under
[rwv/caj2pdf-rust#406](https://github.com/rwv/caj2pdf-rust/issues/406). Full-corpus
JavaScript and visual checks are not claimed by this four-original receipt.
