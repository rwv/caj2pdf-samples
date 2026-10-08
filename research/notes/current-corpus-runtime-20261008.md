<!-- SPDX-License-Identifier: MIT -->

# Current complete corpus runtime checkpoint

Part of [Rust #406](https://github.com/rwv/caj2pdf-rust/issues/406). Fresh
Node.js and actual Chromium conversions of **all 1,252 accepted originals**
match the reviewed native PDF hashes, byte sizes and page counts, covering
**35,587 pages**. All 45 remaining originals pass fresh expected-refusal and
cleanup checks on native, Node and Chromium. Refusal checks are not conversion
passes or evidence that recovery is impossible. The
[per-source receipt](current-corpus-runtime-20261008.json) covers the exact
1,297 identities in the catalog; no source is added or replaced.

## Build and coverage

The converter source is reviewed #457 head
`5f3cf7fb08297ddadfb1cff05e8dcdfe17c037dc`, merged as
`aaedf57de1e3789347113bdc7ca6687a9987e164`. Native SHA-256 is
`d213898ee16a32f0d5304dc96438ffde2402d8135af3b0728a764c1ae8ea41a0`;
WASM is `7e8d90aef49fa4d15e3b95ccc0bc3b207e325b19d777548c81c5cc2665a5e77b`.
The Rust/JS production sources, manifests and lockfile are unchanged through
documentation successor `b3833a61f3128de6d97531f9932b57426f70ed02`.

Native references are the existing frozen #457 regression: 1,277 primary
originals / 2,126 attempts, plus 19 extended inputs and the separately
cataloged archived PDF. They are not relabeled as another fresh native sweep.
The new JavaScript runs use a frozen package extracted from that reviewed
commit, with all 41 package/WASM file hashes checked again after completion.
The executable and font hashes also remain unchanged.

| Collection | Conversion PASS | FAIL | UNSUPPORTED |
| --- | ---: | ---: | ---: |
| Primary 1,277 originals | 1,250 | 18 | 9 |
| Extended NH/CAA collection | 1 | 0 | 18 |
| Separate #449 archived PDF | 1 | 0 | 0 |
| Total 1,297 identities | **1,252** | **18** | **27** |

The catalog now points every conversion status to this common current-build
receipt. Historical receipts remain unchanged. The separate 139-page archive
does not repair or replace the truncated 134-page #448 source.

The runs use Node v24.13.0 and Chromium 154.0.8037.92. Ten originals use
NotoSerifCJK-Regular face 2 and FreeSerif, matching the native font selection;
font identities are pinned. The 12-page HN-B source `166d0014…` retains its
one documented private-use visual substitution and original ActualText code.
Matching output bytes do not recover the original glyph's appearance.

## Integrity, output and cleanup checks

Node reads seekable originals and hashes sequential sink writes. Chromium
uses a module DedicatedWorker and the public browser adapter, spooling inputs
and required fonts to temporary OPFS entries and writing one temporary PDF.
A localhost streaming sink hashes that PDF. The worker removes source, font
and output entries before reporting the final OPFS directory inventory.
Every original is hashed before and after its runtime operation.

Each accepted runtime has exactly 1,252 outcomes, in the manifest's source
order; the final aggregation independently checks the source set, uniqueness,
order and hash/size/page mapping, rather than relying on the harness's match
flag. Both runs finish without a runtime restart, discarded failure or retry.
Deliberate in-memory duplicate, exchanged identity, changed hash and retained
OPFS-entry controls are all detected by aggregation.

All 45 refusals have unchanged source hashes, matching prior diagnostics,
native exit 1 with no published PDF, zero JavaScript sink bytes, and empty
Chromium OPFS after cleanup. The refusal inventory is:

- 16 TTKN-wrapped PDFs: current conversion stops at `AMBIGUOUS_PDF_REPAIR`
  because bytes after PDF EOF are not a recognized CAJ footer. The live
  custom encryption handler is established separately by #415; it is not
  misreported as the current conversion error.
- One #420 original with missing Indexed colors: `MALFORMED_PDF` at byte
  898,312. Its ambiguity evidence is in the [palette report](indexed-palette-loss-20261008.md).
- One #448 truncated CAJ: `MALFORMED_CAJ` at byte 61,864, record 37.
- Nine TEB originals and 18 CAA target descriptors: `UNSUPPORTED_FORMAT`.

The native output directory and all 1,297 browser final OPFS inventories are
empty. Node's measurement sink writes no files; zero bytes on refusal is the
applicable sink check. Corpus and output bodies are never committed. Source
and output streams have the existing converter limits; the external browser
runner caps spooling/upload at 512 MiB and each case at 180 seconds. This is
not a new peak-memory benchmark.

An initial preparation lookup incorrectly assumed a hash-named NH file.
Preparation stopped before any runtime conversion. The actual `energy-1989.nh`
was independently hashed, then included under its existing catalog identity.
The preparation failure is retained. Historical runtime runs keep their
original builds, failures and limits; no earlier result is overwritten.

## What remains open

This completes #406's runtime-parity/source-integrity/failed-output-cleanup
criterion. The full correctness goal remains open: matching runtimes are not
an independent source-content or visual oracle. The generic native report
still records 26 ancillary image-order failures and 936 unexecuted bitmap
checks; [applicable native-text checks](native-content-completion-20261008.md)
and [independent bitmap checks](github-bitmap-oracles-20261008.md) are separate
evidence with their own limitations. C8/HN-B outlines remain unknown; the
[expanded 849-source investigation](hnc8-outline-inventory-20261008.md)
corrects a historical HN-A misclassification without inventing outlines.

TTKN wrapper/credential semantics, missing-color recovery, unsupported
containers/descriptors and general viewer readiness retain their own open
boundaries. No blanket irrecoverability, complete vendor fidelity, API or
format-support change is claimed. The paired PRs document self-review and
simplification, not independent approval. Optional-corpus skips are never
compatibility passes. No foreign converter, private HN/JBIG or vendor
implementation is read or copied, and no release is performed.
