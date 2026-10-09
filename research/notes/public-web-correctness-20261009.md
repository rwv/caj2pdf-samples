<!-- SPDX-License-Identifier: MIT -->

# Source correctness checks for the public-web cohort

This follows [collection #81](https://github.com/rwv/caj2pdf-samples/issues/81)
and completes [samples #83](https://github.com/rwv/caj2pdf-samples/issues/83)'s
scoped verification, under [Rust #406](https://github.com/rwv/caj2pdf-rust/issues/406).
The [per-input/page receipt](public-web-correctness-20261009.json) supplements
the [87-original acquisition/runtime report](public-web-sweep-20261009.md).
No conversion, source file or production code changes in this follow-up.

| New evidence | Coverage | Result |
| --- | ---: | --- |
| Independent bitmap/JPEG identity, page and image order | 4 HN/C8 originals, 203 pages, 236 image descriptors | All pass |
| Source-declared page extents and image placement | The same 203 pages | All pass |
| Independently unwrapped KDH PDF preservation | 20 pages, 122 selected objects, 60 raw streams | Scoped checks pass |
| Selected C8 contents panel in the pinned viewer | 2 new originals | Both display empty contents |
| Exact compressed framing of incomplete PDF content | 7 originals, 11 streams | Complete compression; incomplete PDF tokens remain |

## HN/C8 source content and geometry

The existing [independent bitmap protocol](github-bitmap-oracles-20261008.md)
checks all four newly acquired HN/C8 originals. The 31 type-0 images use the
pinned external black-box decoder, with two fresh guarded workers and distinct
prefills. The 168 type-3 images use original source-payload PDF wrappers and
Poppler/MuPDF agreement; decoder implementation independence remains unverified.
The 37 JPEGs retain exact encoded payload hashes. No candidate-decoded image
is used as expected source pixels, and no external implementation is inspected.

Every page is image-bearing and passes the page/image order check. There are
no skipped, incomplete or image-free pages in this cohort. Type-0 row direction
follows the documented DIB convention, rather than choosing the orientation
that matches. Original source, PDF and oracle binary hashes remain unchanged.

The existing [source geometry checker](source-image-geometry-20261008.md)
then checks all 203 page boxes and image draws. The new source-derived bitmap
receipts are passed directly to its existing `inspect(..., oracles=...)` API.
The checker requires complete measured image-only record syntax; it does not
silently reinterpret native or unknown records. Source fields determine expected
coordinates and resource identities. All page and transform residuals fit the
pre-existing tolerance; there are no parser warnings or incomplete pages.
The JSON includes every page's profile, coordinates, identity and residual.

The already published HN-A bookmark comparison still supplies 71 and 24
matching source/output outline nodes. Bitmap identity does not establish JPEG
color rendering, unknown source outlines, native glyph/font appearance or all
viewer rendering behavior.

## KDH preservation

The new KDH original `d36f91dee22d4ab527dd7a713e017d4679d0e6f9663605b3286100bb08ccc8cd`
is independently unwrapped sequentially using the existing measured wrapper
protocol. The whole decoded tail is retained; the reference boundary is not
taken from the candidate output. The existing PDF source preservation runner
checks all 122 selected object values, 60 raw streams, 20 pages, the page tree
and zero outline nodes. There are no unresolved references, added or missing
selected objects. Only the trailer's xref/identity fields differ under the
existing individually checked rule.

The source reader warns about duplicate `/MediaBox` keys in Pages object 1;
the candidate reader is clean. A separate bounded read at the source xref offset
confirms that **both raw occurrences equal `[0 0 612 792]`**. This retains the
warning and proves the duplicate's identical values instead of relying only
on a reader's last-key selection. The receipt pins the raw object, independently
decoded reference and both inventories. Stream bodies are opaque hashed bytes;
no font program/outline is inspected. Selected-object preservation is not a
new complete-page rendering oracle.

## C8 displayed contents

The unchanged [contents-panel protocol](viewer-outline-protocol-20261009.md)
runs once for each new C8 source, in separate offline contained processes.
Both show zero nodes and the empty caption at three separated checkpoints and
every intervening sample. The known 132-page HN-A control brackets these runs;
both fresh controls show 81 nodes, 13 roots and depth three. All four sessions
have intact sources, acknowledged observer stops, no OOM, and removed containers.
There are no retries or discarded attempts. A separate receipt audit rehashes
the captures/traces and reproduces checkpoint and intervening-sample selections.

This extends the previous 849-source inventory to **851 distinct C8/HN-B
originals with observed empty contents**, across separately pinned runs. It
does not prove that no other stored representation exists, resolve later
asynchronous/viewer behavior, or establish full-page readiness. No positive
C8/HN-B outline source was found; [Rust #303](https://github.com/rwv/caj2pdf-rust/issues/303)
remains open.

## Seven unresolved PDF content defects

For every one of [Rust #499](https://github.com/rwv/caj2pdf-rust/issues/499)'s
11 warning streams, the direct source xref offset and dictionary establish the
declared compressed length. Those exact bytes match the independently read
stream, are followed by `endstream`, and form a complete checksum-valid zlib
stream with no unused or unconsumed bytes. Bounded independent inflation agrees
with the previous qpdf decoded-stream hash.

Each affected page has exactly one Contents stream. Thus none of these 11
tokens continues into another Contents array member. The incomplete tokens
are already present inside complete compressed payloads; increasing the
declared compressed length or appending a second compressed member does not
provide a demonstrated recovery. This does not exclude another intact edition
or prove that missing content is unrecoverable.

The earlier source/output byte and all-65-page raster equality still establishes
preservation only. No guessed terminator, text-showing operator or discarded
content is applied. The seven remain conversion successes with unresolved
qpdf warnings, not full compatibility passes.

## Reproduction, provenance and remaining work

The receipt pins the unchanged research tools at samples commit
`541745102686ce8ecc145b99f8a6e6c7f96a4b83`, external driver hashes, tool/library
versions and every source/output identity. The PDFs are the previously reviewed
Rust `d2bf82e8aec6fba5e8f3783e4953606c02ab1374` tree's outputs. The bitmap and
geometry commands/APIs are documented in the linked protocols; the KDH check
uses `pdf_source_preservation.py --manifest ... --output ...`, with the one
original's recorded hashes, format and page count. The C8 CLI uses the existing
two-entry manifest, two workers and the exact observer/image identities in
the JSON; populated controls reuse the existing capture API and protocol.

Existing bounded source readers, per-page extraction and child-process limits
are reused. The bitmap/geometry driver has a 1 GiB address-space limit; selected
content-stream inspection caps raw and decoded data at 1 MiB. All acquisition,
runtime, image and source bodies remain external. Public files contain original
MIT prose and metadata only. No new dependencies, production support promises,
API changes or release are introduced.

The catalog remains **1,339 conversion PASS / 18 FAIL / 27 UNSUPPORTED** across
1,384 identities, with revision-scoped evidence. All older refusals, unresolved
source/font/ornament fidelity, viewer readiness and outline obligations remain
under #406. This report adds required source checks for the new cohort; it
does not close that parent or establish unavoidable exceptions.
