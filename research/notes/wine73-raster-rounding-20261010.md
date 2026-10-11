<!-- SPDX-License-Identifier: MIT -->

# Wine 7.3 raster and page-width classification

[Rust #534](https://github.com/rwv/caj2pdf-rust/issues/534) has **72 explicit
unresolved display cases**: 58 page-width differences and 14 selected image-only
raster differences. Fresh current-main displays reproduce the historical
observations. Independent image and geometry evidence does not demonstrate
corrupt payloads or justify deleting a pixel column. Original controls show
that page-width equality changes at display-rounding boundaries even when the
source extents are correctly serialized into the PDF's existing empirical model.
No production correction or blanket raster tolerance is introduced.

The [per-page receipt](wine73-raster-rounding-20261010.json) records all 72
classifications, exact identities, current/historical comparisons, independent
content/geometry evidence, 21 original control sessions and 145 retained exact
CAJ/KDH/PDF controls. Raw sources, PDFs, fonts and screenshots remain external.

## Rechecked actual pages

The pinned implementation is merged #535,
`e6343aa785547f5e34bb499dfda56be2d5dc595d`. Later #536/#537 changes are documentation
only. Current CLI/Node/Chromium outputs already agree for all 17 audit documents;
16 retain the historical #459 PDF hashes, while #530 changes four JPEG matrices
in the long HN original. Page 217's stream, image identities and geometry remain
unchanged. The frozen artifact/resource identities are in the
[orientation study](wine73-jpeg-orientation-20261010.md).

The fresh actual cohort uses 20 cold sessions: 12 PDFs and original/repeat sessions
for `0110…`, `0377…`, `166d…` and `3dc7…`. All **96 available PDF page crops equal
the historical PDF crops**. Every one of the **57 freshly repeated original
pages equals both its new cold repeat and the historical source crop**. Four
`b9a6…` PDF observations remain unavailable in single-page/75%; they are outside
the 72 cases here and retained separately under #533. This cohort also preserves
the distinction between native and image-only pages for #531.

| Actual source prefix | Selected pages | Retained outcome |
| --- | --- | --- |
| `03770ea1cdeb` | 1–5 | PDF width +1; native typography also differs |
| `166d00147923` | 1–12 | PDF width +1; native typography also differs |
| `1b9aa912e0bc` | 1–4 | PDF width +1; native typography also differs |
| `3dc7f393740d` | 1–37 | Image-only PDF width +1 |
| `0110e749332c` | 1–3 | Equal-size image raster differences |
| `7e3f2c0faebb` | 1–9 | Equal-size image-only raster differences |
| `e1b17805a87f` | 6 | Equal-size image-only raster difference |
| `16b1a3b1cb71` | 217 | Equal-size upright image raster difference |

All width cases have equal heights. A width difference does not imply that only
the border differs; native typography remains #531. The four inverted JPEG
pages fixed by #530 are excluded. The correct #532 ornament configuration's
newly observed `b9a6…` width and the distinct continuous-mode width in #533 are
separate observations, not retroactive additions to the original 58 cases.

## Independent content and geometry evidence

The [bounded source-image study](source-image-geometry-20261008.md) supplies
source extents, descriptor/draw counts, ordered image identities and page/image
transform checks independently of screenshot borders. Its recorded source and
PDF hashes agree with every applicable current output here. For page 217 the
#530 whole-document preservation check bridges the changed PDF hash: all 433
page boxes and 434 image payloads/dictionaries are unchanged, with only four
other page matrices corrected.

Bilevel identities use the previously documented opaque external JBIG-1
oracle and independent minimal-wrapper JBIG-2 decodes; implementation independence
of external tools remains unverified. JPEG payload identity is byte identity,
not proof of identical color conversion or rendering. Image order/orientation
and the declared placement model are distinct from final viewer resampling.
The `240/2473` point unit and fixed serialization precision predate this run.
They remain an **empirical model**, not newly proven authoritative physical
units. None of these facts makes a nonzero screenshot difference a fidelity pass.

## Original zoom and placement discriminators

[`wine_raster_rounding_controls.py`](../cajviewer/wine_raster_rounding_controls.py)
authors three native C8 pages using the existing original asymmetric JPEG:
black top/left bars, blue lower-left and red lower-right regions. The baseline
extent is 5105 × 4800 source units; image position is `(400,500)` and image extent
3500 × 2500. The second control changes only page width to 5106. The third moves
only image x/y by +20 source units. All three have the identical type-1 JPEG
payload, also byte-identical in each generated PDF. The original descriptor
type's top-first orientation is independently established by #530.

Zooms **50%, 75%, 100%** were declared before observation. Each source/PDF pair
has an isolated cold session; the baseline source also has a cold repeat at
each zoom. All 21 numeric-gated, complete-page observations succeed and every
same-visit/source-repeat pair is exact. The Wine 8.0 / CAJViewer 7.3.151 Simple
image, font/MSXML prefix, 1600 × 1200 at 96 DPI, single-page protocol and offline
read-only resource limits are unchanged from the orientation report.

| Declared width | Zoom | Source crop | PDF crop |
| ---: | ---: | --- | --- |
| 5105 | 50% | 334 × 316 | 334 × 316 |
| 5105 | 75% | 499 × 471 | 499 × 471 |
| 5105 | 100% | 664 × 626 | 665 × 626 |
| 5106 | 50% | 334 × 316 | 334 × 316 |
| 5106 | 75% | 499 × 471 | 500 × 471 |
| 5106 | 100% | 665 × 626 | 665 × 626 |

These measured transitions localize a source/PDF **display-rounding difference**
in the original controls. A universal minus-one-pixel correction would damage
the equal-width cases. Image placement changes leave the page bounds unchanged.
The fixed +20 displacement changes the observed image origin by `(2,1)`, `(2,2)`
and `(3,3)` pixels at the three zooms in both source and PDF. The predeclared
model predicts approximately 1.294/1.941/2.588 pixels before rounding. This
supports the placement scale within these controls; it does not prove exact
physical geometry or every real page's rounding path.

The image paint often ends one pixel farther right/below in the source, despite
the identical JPEG and preserved PDF matrix. Baseline equal-size crops differ
by 532 pixels at 50% and 702 at 75%. The width-5106 control at 100% differs by
1,336 pixels. These residuals stay nonzero; decoder color conversion, endpoint
rounding and resampling contributions have not been individually isolated.
Strong red/blue and nonwhite bounding boxes are auxiliary original-control
measurements with fixed thresholds; they are not normalized comparison images
or acceptance tolerances. Full page comparisons preserve all native pixels,
including the page border, without resizing, alignment or column removal.

## Classification and limits

Each of the 58 width cases and 14 image-only cases is explicitly classified
`UNRESOLVED_DISPLAY_DIFFERENCE_WITH_PRESERVED_CONTENT_AND_MODEL_GEOMETRY` in the
receipt. The controls demonstrate a rounding mechanism, but do not assign every
actual difference to harmless antialiasing. No new production defect is proven
by this study and none is hidden by a fitted offset or tolerance.

The **139 CAJ plus six KDH/PDF exact selected-page controls** retain their
historical observed pairs and byte-identical current PDFs. They were not freshly
rerun in the viewer here and are not relabeled as new sessions. The 428 other
long-document pages not visually inspected by #530 remain uninspected.

All three committed controls reproduce the observed input bytes exactly. One
original independent-parser test confirms the single type-1 image, identical
payload and isolated width/placement changes; it passes with zero skips.
The catalog is unchanged. The first font-free C8 conversion attempt was refused
at byte 100 before output/viewer startup; native C8 control conversion then
supplied the same explicit DejaVu role resource used by #530, although these
pages paint no text. That failed attempt remains recorded.

Source, generator and test are original MIT work using the existing MIT helpers.
No external document, derived PDF, screenshot, font program, vendor binary or
private HN/JBIG/foreign-converter implementation is copied into the repository.
This completes #534's explicit per-case classification path after review/CI;
it does not close #406/#441 or claim full visual equivalence. No production API,
default output, memory bound, dependency or release behavior changes.
