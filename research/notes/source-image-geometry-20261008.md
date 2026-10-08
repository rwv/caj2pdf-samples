<!-- SPDX-License-Identifier: MIT -->

# Source page and ordered image geometry

[samples #49](https://github.com/rwv/caj2pdf-samples/issues/49) verifies the
declared page extents and applicable image draws of all 973 accepted HN/C8/NH
originals in the current catalog: 845 C8, 127 HN and one NH, totaling 16,548
pages. The [per-input/page receipt](source-image-geometry-20261008.json)
records the result against the unchanged reviewed #457 native PDFs. The
new [NH bitmap receipt](nh-bitmap-oracle-20261008.json) supplies previously
missing independent bitmap identities for the 433-page NH original.

All 16,548 pages pass the scoped check, with 18,808 image draws bound to
19,258 source descriptors and 450 byte-verified aliases. The 31 image-free
native pages pass only their page-box/empty-image checks here; they are not
counted as bitmap evidence. There are no parser warnings or incomplete pages.
The largest page-box residual is below 0.0000005 point, and the largest image
matrix residual is below 0.000000000001 point. The final guarded rerun retains
exactly the preceding complete run's per-input/page result hash.

This is a scoped source-record comparison. It does not establish authoritative
physical units, native glyph/vector placement, font appearance, complete page
rendering or C8/HN-B outlines. The known viewer raster difference remains open
in [Rust #441](https://github.com/rwv/caj2pdf-rust/issues/441), and the overall
correctness criteria remain open in [#406](https://github.com/rwv/caj2pdf-rust/issues/406).

## Measurement and provenance

The original MIT checker uses seekable `FileInput` and `SourceExtractor`,
bounded source records, and independent bitmap receipts. The expected page
box and image coordinates come from source fields, never candidate PDF
dimensions or an input-specific lookup. The empirical `240/2473` point scale
and `1/20000` point serialization tolerance were fixed before the corpus run.
Exact fractions are used for expected values, matrix composition and residuals.

The measured profiles follow the existing independently authored field and
viewer-control notes:

- [Page extents and image dimensions](cajviewer-hnc8-kdh.md), including the
  separate page-size and image-size controls.
- [Raw and paired HN-A fields](hnc8-uncompressed-text.md), including per-page
  paired-prefix extent overrides and scoped `c000` marker bits in `d300`
  placement records. Direct C8 compressed coordinates are not masked.
- [Direct compressed framing](hnc8-direct-text.md), fixed glyph/image framing
  and measured non-rendering HN-A regions from
  [Rust #388](https://github.com/rwv/caj2pdf-rust/issues/388#issuecomment-6044235268).
- [Repeated image groups](hnc8-repeated-groups.md): type, length and hash
  equality is followed by byte-for-byte payload comparison in bounded chunks.
  Repeated descriptors are not automatically treated as additional draws.
- [C8 image records](c8-image-references.md) and
  [HN-B origins/canvas fields](hnb-compact-index.md). Native record framing
  reuses the existing glyph walk through an optional image callback; existing
  glyph checks are unchanged. The measured mode-0 HN-B canvas adds 100 source
  units on each axis.

The project's own original MIT Rust implementation was consulted to locate
existing observations. This is an independent measurement tool following the
documented model, not a claim of a blind implementation or independent proof
of that model's physical interpretation. No foreign converter, vendor decoder
or private HN/JBIG implementation was read or migrated.

For each PDF page, bounded content parsing tracks the graphics matrix stack,
then checks the six affine coefficients and the ordered resource identity of
each image. JPEG identity is the unchanged encoded payload hash; bitmap
identity is dimensions plus normalized visible bits from an independent
source receipt. Type-0 row reversal is chosen from its documented bottom-up
DIB convention, not by accepting whichever orientation matches. Masks and
unmeasured bitmap decode parameters are refused. The checker does not prove
JPEG color rendering or later native text/vector overpainting.

Measured native `/Normal` and `/Multiply` blend states are recorded. Only an
exact ExtGState containing `Type` and `BM` is accepted; opacity or other state
keys cannot silently pass. Multiply is admitted only for native bilevel draws.
Its source appearance remains backed by the separate
[HN-B overlap controls](hnb-magnesium-profile.md), not re-proved here. Images
under an unverified clipping path are explicitly incomplete.

Input/PDF sizes are capped at 512 MiB and streamed for hashes before and after
inspection. Source text and decoded PDF page content are capped at 1 MiB;
source reads request at most 64 KiB. Individual normalized bitmaps are capped
at 16 MiB, JPEG payloads at 64 MiB, images at 8,192 per page and graphics stack
depth at 64. The POSIX CLI has a 1 GiB address-space cap, a bounded manifest,
duplicate-source rejection, one flushed JSONL record per original and an
exclusive external output directory. An error, missing input, unsupported
profile, warning or incomplete page prevents an overall PASS. There is no
whole-document payload conversion buffer.

## NH bitmap evidence

The unchanged NH SHA-256 is
`16b1a3b1cb7177cc3d327f749f7f273d806b153ded5fe11d9261bac030ec66ac`;
the current 433-page PDF SHA-256 is
`b12385a8a53a811ac245dd6f65b410a5c1b1be526292b42e94594a6b75c4add3`.
Its 434 source descriptors comprise three type-0 bitmaps, 427 type-3 bitmaps
and four JPEGs. All 434 payload identities are distinct within their types,
and all 433 pages pass the existing independent bitmap/order runner. Source,
PDF and oracle-library hashes remain unchanged.

Type 0 uses the [existing black-box protocol](jbig1-oracle.md): the pinned
external library SHA-256
`d370d071a4b7abdf7db4565c2bc85ac881470ee1a212459dd658d70974128de6`,
two fresh guarded workers with different prefills, bounded encoded/decoded
buffers and timeouts. Its foreign implementation was not inspected.
Type 3 uses the original minimal PDF wrapper around untouched source payloads
and [Poppler/MuPDF agreement](jbig2-oracle.md). The external tools' decoder
implementation independence remains unverified. No Rust-decoded pixels are
used as expected source pixels. Exact script/tool hashes and versions are
included in the geometry receipt.

## Controls and retained incomplete attempts

Twelve original control groups cover authored source/PDF geometry and JPEG
identities; page-size, position, scale, resource-order, omission and duplication
mutations; truncated/unknown framing and zlib limits; paired per-page extents;
non-rendering region constraints; actual alias bytes despite forged hash
metadata; bitmap polarity, row orientation, padding and changed visible bits;
noninteger dimensions and stencil masks;
native origins/canvas framing; matrix composition and clipping; blend-state
restore and rejected opacity; bitmap receipt span/hash binding; and CLI
missing-input retention with a nonzero incomplete exit. The Catalog workflow
runs 69 selected tests without external corpus or decoder downloads. These
synthetic tests are separate from the 973-original measurement.

The receipt retains the unsuccessful exploratory passes. The first omitted
the already documented HN-A per-page extent override and consequently reported
2,166 geometry mismatches; these were checker omissions, not demonstrated
converter defects. Later passes added the documented native and blend-state
profiles. Once independent bitmap identities were required, 430 NH pages
correctly became `NOT_CHECKED` until the new source oracle supplied them.
The earlier apparent geometry-only passes are not relabeled as content proof.
Initial authored-test errors (an allowed region flag used as a negative, an
unsaved PDF stream lacking `Length`, and an omitted test import path) remain
in the external logs; the corrected controls pass. No real conversion defect
or production behavior change was demonstrated by this investigation.

## Reproduction

From this samples checkout, use Python 3.11+ on POSIX and `pikepdf==10.5.1`.
The receipt pins Python, pikepdf's linked qpdf and zlib versions. The four
committed source-bitmap metadata receipts supply expected identities; the
external decoder is needed only to reproduce those source-oracle measurements.
The NH oracle command uses `github_bitmap_oracle.py` as documented in the
[earlier 936-source report](github-bitmap-oracles-20261008.md).

Create an external JSON array with one object per input, using absolute paths
or paths relative to the manifest:

```json
{
  "source_path": "input.caj",
  "pdf_path": "output.pdf",
  "source_sha256": "SOURCE_SHA256",
  "pdf_sha256": "PDF_SHA256",
  "pages": 433,
  "native": false
}
```

`native` selects the already classified native-text source framing; it is not
inferred from expected geometry. The public receipt identifies the ten native
originals (60 pages). All other 963 originals comprise 16,488 image-only pages.

```sh
python3 research/scripts/source_image_geometry.py \
  --manifest /external/manifest.json --output-dir /external/new-geometry-run
```

`results.jsonl` retains full per-page coordinates, resource identities and
residuals. `summary.json` pins scripts, oracle receipts, manifest and result
hashes. The public receipt retains each page's counts, residuals, source extent
and canonical detailed-record hash; it also pins the complete external JSONL.
Documents, PDFs, pixels, fonts and decoder binaries remain outside Git. No
release, API/support change or full vendor-fidelity claim follows from this
measurement.
