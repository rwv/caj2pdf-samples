<!-- SPDX-License-Identifier: MIT -->

# Correct the type-0 image oracle row convention

Partial progress on [issue #12](https://github.com/rwv/caj2pdf-samples/issues/12).
The [pinned type-0 oracle](jbig1-oracle.md) hashes visible DIB memory rows without
reversing them. The [independent row-model evidence](jbig1-type0-rows.md) explicitly
requires reverse-row hashing for display-order decoder output. Poppler extracts
PBM images in display order, but the old corpus comparator hashed them in that
order against the bottom-up manifest.

The comparator now selects bottom-up hashing only when the source descriptor is
type 0. It seeks one PBM row at a time and masks only unused row bits, preserving
bounded memory. Type 3 keeps its normalized display-order hash; JPEG comparison
still uses exact payload identity. It never tries both orientations to obtain a
match. Original tests reject actual row reversal, changed/missing images, page
swaps, malformed/truncated bitmaps and source/oracle identity mismatches.

## Reproduction and scope

The [receipt](image-order-row-convention-20261008.json) preserves all 26 original
results and records checks against the same unchanged source/PDF hashes:
**18 PASS, 7 FAIL, 1 HARNESS_ERROR**. All source identities were verified before
and after comparison. Native PDFs come from the complete #402 regression;
all were confirmed byte-identical by the #407 full native regression.

Every mismatching page in the seven remaining FAIL cases has zero source images.
A bitmap-only comparator is insufficient there. The harness error is the archived
source extractor interpreting a record at source byte 12886, page 2 of
`3f3b9b57d692…`, as image type 32797. That parsing limitation is not proof of a
converter failure. These eight cases remain unresolved under #12 pending
applicable source text/descriptor checks. Historical FAIL receipts are unchanged.

This change verifies page/image identity and order only, not placement, geometry,
alias coordinates, glyph outlines or full rendered-page parity. It does not add
new Node/browser compatibility claims. External documents, extracted bitmaps and
converted PDFs are not committed. All harness changes and controls are original MIT.
