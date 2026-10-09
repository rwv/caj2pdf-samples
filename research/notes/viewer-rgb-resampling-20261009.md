# Original RGB raster variation and interpolation controls (2026-10-09)

An original font-free PDF produces two CAJViewer page-buffer variants with
**71,650 changed pixels**, including changes in both vector and image panels.
The complete displayed page differs at **79,837 pixels**. Both displayed
variants also occur without the observer. Swapping only the four image
`Interpolate` flags produces equal rasters in all **40 same-route comparisons**
(8 buffer and 32 screenshot pairs). These observations locate the variation
before the observed Qt display transform, but do not establish its internal
cause or a general readiness rule under [Rust #441](https://github.com/rwv/caj2pdf-rust/issues/441).

This is the scoped experiment for [samples #72](https://github.com/rwv/caj2pdf-samples/issues/72).
The [metadata receipt](viewer-rgb-resampling-20261009.json) contains all 18
sessions, all 150 final comparisons, three analysis versions and the two
earlier state-check rejection sets. Acquisition was never repeated. No
converter run, new real-document acquisition or compatibility pass is added.

## Original inputs and predeclared acquisition

[`pdf_rgb_controls.py`](../cajviewer/pdf_rgb_controls.py) writes two original
six-page PDFs, each 830,627 bytes, with a maximum image row of 1,536 bytes.
The documents have identical parsed object graphs and raw streams except for
four explicit `Interpolate` booleans. Their SHA-256 identities are:

| Control | SHA-256 |
| --- | --- |
| Default flags | `7d82f80dbcce37079324630ef063e6a5b4a90537ca81b09e82deeb1d6b58e60d` |
| Swapped flags | `473215fb55a41f7d39e3ba030618913a6b4923ef87c92e799c57d88683207eb8` |

Every page has an A4 MediaBox and independently authored black marker bars
whose count identifies its page. Pages 1, 5 and 6 additionally paint 64 solid
RGB cells, 64 fractional RGB triangles, two 64×32 RGB images and two 512×256
images. The larger images repeat each small-image sample exactly 8×8 times;
both resolutions occupy the same 240×120-point size. The original pattern
contains color bands, checker cells, RGB ramps and thin colored bars. The
default document sets left-image interpolation false and right-image
interpolation true; the second document reverses all four flags at the same
positions. Neither PDF uses fonts, text operators, filters, masks, alpha,
Decode arrays or ICC profiles.

Graph, operator, resource, marker, pixel-replication and flag checks passed
before acquisition. A first single-document design, which confounded flag
and position, was replaced before launch and is retained as NOT_LAUNCHED.
The initial graph-comparison test also exposed recursive dictionary equality
following references into intentionally changed image flags. The corrected
test compares each indirect object's syntax, stream dictionary and raw bytes;
that test correction did not change the generator.

The immutable acquisition plan has SHA-256
`0ce2a0eaf773565260a3d2b939ee586d8eba07e3ac39073dba6d1d652dac66f7`.
All 18 fresh sessions, their order, inputs, routes, observer conditions,
full-page grids and six source-coordinate panel boxes were frozen before the
first launch. The unchanged [gray control](viewer-raster-stages-20261009.md)
brackets the eight instrumented RGB sessions.

| Session | Control | Route | Observer | Final variant |
| --- | --- | --- | --- | --- |
| 01 | Gray | 5 | Yes | Gray A |
| 02 | Default | 5 | Yes | RGB A |
| 03 | Swapped | 5 | Yes | RGB A |
| 04 | Default | 3→5 | Yes | RGB B |
| 05 | Swapped | 3→5 | Yes | RGB B |
| 06 | Swapped | 3→5 | Yes | RGB B |
| 07 | Default | 3→5 | Yes | RGB B |
| 08 | Swapped | 5 | Yes | RGB A |
| 09 | Default | 5 | Yes | RGB A |
| 10 | Gray | 3→5 | Yes | Gray B |
| 11 | Default | 5 | No | Display A |
| 12 | Swapped | 5 | No | Display A |
| 13 | Default | 3→5 | No | Display B |
| 14 | Swapped | 3→5 | No | Display B |
| 15 | Swapped | 3→5 | No | Display B |
| 16 | Default | 3→5 | No | Display B |
| 17 | Swapped | 5 | No | Display A |
| 18 | Default | 5 | No | Display A |

Each session uses a 1600×1200 desktop, maximized viewer, 50% zoom and page
5 of 6. Startup waits five seconds, maximization and zoom two seconds each,
and each route step three seconds. Two final screenshots are one second
apart. All 18 pairs are equal within their session. Page/zoom OCR, original
markers, fixed exterior frame probes, input hashes, logs and cleanup are
checked independently of pixel equality. This route grouping is an observation
of this experiment: earlier native repeats already show that route alone does
not determine a raster, and consecutive equal frames do not prove readiness.

All sessions use image
`sha256:cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de`,
network none, read-only root/input, uid 1000, dropped capabilities,
no-new-privileges, 2 GiB memory/swap, two CPUs, 256 PIDs, bounded tmpfs/file
sizes and a 90-second lifetime. No application abort or OOM was observed;
peak container memory ranges from 316,223,488 to 327,417,856 bytes. Every
source remains intact and every container was removed. All 613 retained
session-file hashes were rechecked before publication.

## State-check corrections retained with the measurements

The initial frozen marker rule required exactly black occupied patches and
an exactly white absent patch. This incorrectly coupled original page-ID
decoding to the photometric variation being measured. Analysis v1 rejected
four prior-page instrumented buffers whose occupied patches contain grayscale
0 and 1; their screenshots had already passed. Its flat observation status
also excluded those otherwise confirmed screenshot endpoints from that
version's pair table. Analysis v2 instead allowed nonwhite occupied patches
but required exactly white neighboring guards. Guards containing 254 and 255
then rejected eight prior-page RGB observations, including four plain sessions.

The final v3 rule decodes the authored black/white bits at their source-level
midpoint, 128: five dark grayscale marker patches, one light absent patch and
light neighboring guard patches at fixed positions. This is a logical page-ID
decoder, **not a pixel-match tolerance**. Independent controls exercise endpoint,
interior and 127/128 boundary classes, missing/extra/colored markers and corrupt
guards. Every pixel, including all marker pixels, still enters exact RGB
comparison without normalization, alignment, resizing or tolerance.

| Analysis | Confirmed buffer observations | Confirmed screenshot-only observations | NOT_CONFIRMED observations | Measured pairs |
| --- | ---: | ---: | ---: | ---: |
| v1 | 6 | 8 | 4 | 74 |
| v2 | 6 | 4 | 8 | 36 |
| v3 | 10 | 8 | 0 | 150 |

Both rejection sets, analysis plans, source hashes and pair-status tables
remain in the receipt. They are analysis failures, not viewer crashes or
missing acquisition. Every previously measured pair is byte-for-byte identical
to its final record. No session, source, route, selected raster, grid or panel
was changed. The final rule admits additional differing evidence rather than
making the rasters equal.

An earlier unexecuted collector draft also borrowed exterior-frame colors
from the unrelated 75-page/80% profile. Seven retained original six-page/50%
frames disproved that assumption before any new-session validation; all seven
have the same four RGB corner values. The draft, independent historical
checks and correction remain pinned. No new candidate frame selected a crop,
alignment or tolerance.

## Exact buffer and screenshot measurements

The final original MIT observer combines the public `QPainter` and `QImage`
API probes, with binary SHA-256
`8c2e0bc0afb3e5ee9e2fc09fa80b82791dd5f5f3d2a65c3dc369aede8ea9e557`.
This is the finalized combined build, distinct from the earlier gray report's
prototype. All ten selected 397×561 pixmaps match a public constructor buffer
RGB hash. They share target rectangle `[560,10,396,561]`, source rectangle
`[0,0,397,561]` and Qt transform `[1.00077819824,0,0,1.00077819824,0,0]`.
Observed constructors are `mutable_tight`, format 13, stride 1192;
`fegetround=0`, `mxcsr=1fa3` and `x87_control=37f` at the public observation
point. Those values do not describe an unobserved internal rendering stage.

Each displayed page is independently measured at crop `[626,156,1023,718]`,
a 397×562 grid. Buffer and screenshot measurements must remain separate.
The observer caps traces and pixel captures; a missing/limited trace invalidates
the observation. No limit was hit. No-observer sessions have no preload,
observer mount or paint/buffer trace, and match the instrumented display
variants exactly. This establishes that the observer is not necessary for
these differences, without proving timing noninterference.

| Complete comparison inventory | EQUAL | DIFFERENT | NOT_COMPARABLE |
| --- | ---: | ---: | ---: |
| RGB buffers | 12 | 16 | 0 |
| RGB screenshots | 56 | 64 | 0 |
| Gray bracket, two stages | 0 | 2 | 0 |

For default direct session 02 → default prior-page session 04:

| Stage | Changed / total pixels | Global channel delta | R / G / B delta ranges | Changed pixels involving color |
| --- | ---: | --- | --- | ---: |
| Buffer | 71,650 / 222,717 | -239…+255 | -227…+206 / -125…+121 / -239…+255 | 70,997 |
| Screenshot | 79,837 / 223,114 | -195…+214 | -195…+166 / -107…+102 / -193…+214 | 78,157 |

The receipt retains exact RGB hashes, bounds, signed ranges and complete
maximum-channel-delta histograms. A pixel is classified as involving color
when either endpoint has unequal R/G/B channels. This describes the changed
pixels; it is not an acceptance threshold. All cross-variant pairs have the
same changed-pixel counts, with signed ranges dependent on comparison order.

The predeclared PDF panel boxes project with fixed floor/ceiling arithmetic:

| Buffer region | Changed pixels | Channel delta |
| --- | ---: | --- |
| Solid RGB cells | 13,349 | -130…+130 |
| Fractional RGB edges | 15,560 | -95…+106 |
| Low-resolution left image | 9,762 | -233…+230 |
| Low-resolution right image | 9,594 | -207…+217 |
| High-resolution left image | 10,042 | -239…+230 |
| High-resolution right image | 9,943 | -239…+255 |
| Outside the six panels | 3,400 | See whole-grid metrics |
| Entire buffer | 71,650 | -239…+255 |

These regions describe the unchanged grid; they do not assert exact internal
geometric registration. The substantial vector-panel differences mean that
an explanation confined to image interpolation flags cannot account for all
observations. No internal mechanism is identified. The gray bracket reproduces
the previous 3,655-buffer/6,037-display differences with deltas -1…+1.

A separate read-only analysis of four previously retained real-document pairs
adds color counts without reacquisition: page 42 has 46,577 changed pixels
involving color among its 56,826 changes; page 34 has none among 1,518; unchanged
CAJ repeats on pages 57 and 59 have 2,321/17,424 and 9,366/19,869 respectively.
The [prior report](viewer-page-box-coverage-20261009.md) remains authoritative
for their acquisition and incomplete page-34 comparison. Similar symptoms
do not establish a common cause.

## Validation and provenance

```sh
python3 research/cajviewer/pdf_rgb_controls.py /external/new-rgb-controls
python3 -m unittest discover -s research/conformance -p 'test_pdf_rgb_controls.py' -v
python3 -m unittest discover -s research/conformance -p 'test_raster_rgb_comparison.py' -v
python3 research/scripts/raster_rgb_comparison.py /external/a.png /external/b.png \
  --first-sha256 FIRST_PINNED_SHA256 --second-sha256 SECOND_PINNED_SHA256
```

Four fixture tests and three RGB/marker tests pass with zero skips and run
in Catalog CI. The three existing public QImage API controls also pass with
the external public Qt development runtime. The generator writes sequentially
and refuses existing destinations or generated output inside the checkout.
The comparison reader hashes and decodes the same bounded PNG bytes, limited
to 16 MiB and 4 Mi pixels, and rejects different grids. The metadata receipt
deduplicates identical measurement records by canonical JSON SHA-256 while
retaining every endpoint and analysis status. The external desktop driver is
specific to this pinned environment; it is not a portable capture runner.

All new source, fixtures and patterns are original MIT. Image semantics follow
the primary [Adobe PDF Reference 1.7, Image Interpolation, printed pages 346–347](https://github.com/adobe/dc-acrobat-sdk-docs/blob/master/docs/pdfstandards/pdfreference1.7old.pdf).
Interpolation defaults false; the algorithm is implementation-dependent and
may not apply to every image/device class. Equal flag results here therefore
do not establish universal flag disregard or a specification violation. The
indexed Adobe website PDF link returned 404; the primary Adobe GitHub copy
was retrieved and its identity retained. No specification text, foreign
converter, private HN/JBIG code, vendor implementation or vendor font
program/outline was copied or inspected. Document bodies, pixels, fonts,
binaries and raw logs remain outside Git.

The original `7797…` discrepancy, reliable readiness, original native fonts
and ornaments and remaining full-page fidelity stay unresolved. Rust #441/#406
and samples #51 remain open. The corpus ledger remains **1,252 PASS / 18 FAIL /
27 UNSUPPORTED across 1,297 originals**, with 35,587 accepted pages. This work
changes no production API, PDF output or supported format and proposes no release.
