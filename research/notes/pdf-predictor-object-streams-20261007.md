<!-- SPDX-License-Identifier: MIT -->

# PNG Up xrefs and object streams — #402/#404

The unchanged [#402 original](https://github.com/rwv/caj2pdf-rust/issues/402)
now converts all 10 pages on native, Node.js and Chromium. The necessary
[object-stream dependency #404](https://github.com/rwv/caj2pdf-rust/issues/404)
is included in [PR #405](https://github.com/rwv/caj2pdf-rust/pull/405).
The [JSON receipt](pdf-predictor-object-streams-20261007.json) records the
source identity, measured xrefs, output hashes, page-oracle checks and full
native regression sweep. External document and derived PDF/render bytes
remain outside both repositories.

## Source and measured profile

- Repository/path: `FuryMartin/caj2pdf-actions / file.caj`,
  [commit 456a85d](https://github.com/FuryMartin/caj2pdf-actions/blob/456a85d9a55690302e4dd10a95b6456afc1ceda6/file.caj).
- Original: 79,463 bytes; SHA-256
  `77b2ebe0a8d6cf9023b1427a0a5c4b3ff0f92b254bdee449c9a80cbc428e9fe3`.
- Unchanged KDH-decoded PDF: 79,208 bytes; SHA-256
  `a5626ac265c7e543e2a59dfefc4ad05851c902299b344679ac346613ad5947c5`.
- Xref object 64 at PDF offset 116: 87 encoded bytes, 155 inflated bytes,
  31 rows, four bytes per row plus the PNG algorithm byte.
- Xref object 32 at PDF offset 78,843: 110 encoded bytes, 276 inflated bytes,
  46 rows, five bytes per row plus the algorithm byte.
- All 77 rows carry algorithm 2. Type-2 entries reference 24 compressed
  metadata objects (33–45 and 65–75) in 13 Flate object streams.

The previous converter explicitly rejected DecodeParms, with no output.
Predictor support alone then exposed the compressed-object refusal, so the
original cannot pass without both changes. Source bytes were not patched.

The implementation is independent MIT code based on Adobe PDF Reference 1.7,
[sections 3.3, 3.4.6 and 3.4.7](https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/pdfreference1.7old.pdf),
and [PNG's Up definition](https://www.w3.org/TR/PNG-Filters.html). Predictor
12 is an encoding hint; the actual row tag controls decoding. The admitted
profile requires tag 2, one color, 8-bit components and Columns equal to the
sum of W. Byte addition wraps modulo 256. Row state carries across Index
subsections and resets at the start of each xref stream.

ObjStm loading checks direct N/First/Length, a single FlateDecode filter,
member numbers, ordered byte offsets, xref ordinals, exactly one direct
value per member and live references. Final xref revisions control member
selection. Bounded metadata is separate from physical source spans; public
object_location refuses a standalone span for a compressed member. Original
stream bytes are preserved. Other PNG algorithms, indirect object-stream
lengths, Extends, external streams and other unmeasured profiles remain
explicit errors. No foreign converter implementation or private-source
migration was used.

## Original and synthetic checks

The tested production commit is `73d62a62db672ef5d85adf69911aa6aa551d4f41`;
reviewed PR head `8aa29a113284a4f974e63e94b5ab2d000ca9a0b7` differs only in
documentation. CLI SHA-256 is
`b0a6fc6503ae0375be3edebbca0bbe5ee4f3867eeb8248c4a0def83492518b65`;
WASM SHA-256 is
`f147a0a93e282ed6918d9cca2911694331f8bf3c38413e41d2b9ea1becbe3a03`.
These are local validation builds, not published release artifacts.

Native, Node 24.13.0 and Chromium 154.0.8037.92 produce identical 79,483-byte
PDFs, SHA-256
`ff827dfd3e13a6c27f9e3a55a1b03745fe192d3526a5ad90afeed9776f17f82c`.
The browser uses an OPFS spool; cleanup leaves zero entries. Both the raw
PDF oracle and converted output pass qpdf 12.2.0 without warnings. The
existing incremental Catalog update retires the source's linearization
hint while retaining all original stream payloads.

PyMuPDF 1.27.2.2 comparisons cover:

- All 10 page-object identities, rectangles, rotations and extracted texts.
- All 10 RGB page renders at 72 dpi with annotations enabled: exact pixels.
- All 40 raw PDF stream payloads, including both xrefs and all 13 ObjStm
  containers: exact bytes.
- Source and output outline inventories: both zero, an actual empty-inventory
  comparison rather than an unexecuted directory test.

A separate original two-page nested-outline fixture is encoded by qpdf in a
committed Rust integration test. It exercises compressed Catalog/page/outline
metadata, Up-predicted xrefs, one-byte reads, byte-identical copy, independent
PDF validation and both rendered pages. Original unit controls cover header
reordering, duplicate/truncated/overflow members, invalid ordinals, row
algorithms and geometry, resource limits, cancellation and a later standalone
revision superseding a compressed member.

Local workspace tests passed 1,271 tests; seven optional tests were ignored
and are not compatibility passes. The affected PDF unit tests were rerun
after the final fallible-allocation refinement. Clippy and native/WASM
release builds passed, as did all 164 JavaScript tests without skips. An
initial JS test invocation lacked the worktree's shared-target link; after
correcting that local build path, the full suite passed. Review and
simplification are self-review, not independent approval. Hosted checks and
merge status are on the PR.

## Full native regression sweep

All 1,277 original candidates were rerun using the previous pinned harness,
four workers and its 180-second / 1-GiB address-space / 512-MiB output-file
limits. Both bookmark modes run where applicable. All source hashes and
sizes pass before and after; the candidate binary is unchanged. The result
is 1,228 converted, 39 failed/strict refusals and 10 explicitly unsupported.
Only #402 changes conversion status. Every previously converted attempt
retains its PDF SHA-256; there are no conversion regressions or output-hash
changes. All refused conversions publish no PDF.

Qpdf reports 1,227 clean converted documents and the same one source-content
warning as the [previous checkpoint](github-sweep-fixes-20261007.md).
The 26 existing ancillary image-order failures remain visible and are not
waived; [samples #12](https://github.com/rwv/caj2pdf-samples/issues/12) tracks
them. The receipt preserves all 2,126 attempts and their ancillary statuses.
Full-corpus JavaScript and rendered-page comparisons remain NOT_RUN; only
the #402 original has the new all-target and whole-document render evidence
above. That rendering evidence is scoped to its stated renderer and
resolution, not every PDF profile or viewer. Historical collection and
refusal-classification receipts remain unchanged.
