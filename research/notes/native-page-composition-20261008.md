# Native page composition and font fidelity boundaries

This checkpoint inventories and observes all ten accepted native C8/HN-B
originals: 60 pages, 83,432 semantic glyphs, 57 source image descriptors/draws,
and 327 output vector paths. The [per-page receipt](native-page-composition-20261008.json)
retains source/PDF identities, numeric source state coverage, font resources,
page rasters, comparisons and failed attempts. It extends
[native content completion](native-content-completion-20261008.md) and
[page/image geometry](source-image-geometry-20261008.md).

The complete corpus runtime result remains **1,252 PASS / 18 FAIL / 27
UNSUPPORTED**. No converter behavior, font policy, output PDF, runtime API or
supported format changes here. Runtime PASS is not complete source fidelity.
This is progress on [samples #51](https://github.com/rwv/caj2pdf-samples/issues/51),
not completion of [Rust #406](https://github.com/rwv/caj2pdf-rust/issues/406).

## Independent observation

An original MIT interposer observes the documented Qt 5
[QPainter drawing API](https://doc.qt.io/qt-5/qpainter.html) and
[QPixmap cache identity, dimensions and saving API](https://doc.qt.io/qt-5/qpixmap.html).
It captures the complete public page raster passed for display, including
the portion below/right of the viewport. It does not inspect vendor code,
native glyph instructions or font outlines. The early broader paint-call
pilot could not observe individual native glyph draws; that failed hypothesis
is retained. The final implementation has only two pixmap drawing hooks.

The pinned opaque Linux viewer image is
`sha256:cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de`.
Every native-document session is fresh, non-root, network-disabled and has
a read-only root and inputs, dropped capabilities, 2 GiB memory/swap limits,
two CPUs, 256 pids and a 600-second hard lifetime. Raw documents, fonts,
screenshots, complete page images and PDFs remain external. Each receipt
records input integrity, limits, observed memory, stop/remove results and
the final container-presence query.

The observer permits at most 128 unique pixmaps, 4 Mi pixels per pixmap,
64 Mi captured pixels and 100,000 bounded metadata records per process.
Any missing file, limit marker, ambiguous capture or page/zoom mismatch is
unconfirmed. Two equal repeated captures mean only that the displayed cached
raster stayed equal; they are not a generic viewer readiness criterion.

At the fixed 1600×1200 desktop and confirmed 150% zoom, selection requires
the complete source rectangle, the observed document widget and navigation
origin, full opacity, an affine transform and a page larger than the viewport.
Both scrollbar states are explicitly admitted. Source-derived aspect checks
use intersecting integer target-dimension quantization intervals, not a
per-document fitted error threshold. Compact continuous-page views are refused.

## Original controls and retained failures

The new 12-page original fixture places exactly N separated geometric glyphs
on page N. All 12 final captures have the independently counted expected
components, 78 in total. This detects adjacent-page association errors. The
original two-glyph control has identical full-screen pixels with observation
disabled, enabled and in two fresh observed cold sessions. These controls
establish scoped acquisition behavior, not correctness of every source page.

Earlier attempts remain in the receipt:

- The real four-page pilot's last page visibly says `4/4`, but OCR including
  the field border read `/4`. It was retained as unconfirmed; the inner field
  crop is now used and is checked across the 12-page original control.
- Compact navigation controls exposed a false association with later pages
  drawn in the same continuous view, and a last-page scroll clamp. Their
  repeated hashes do not make them valid page observations.
- The first large control assumed a scrollbar-free widget height, rejecting
  pages after navigation. The corrected final selector admits both measured
  heights and rejects adjacent, stale, partial and scaled cached rasters.
- The initial full normal-font run rejected three mode-0 pages using an
  arbitrary one-pixel pixmap-aspect threshold, and selected an earlier zoom
  raster on that input's first page. All four are superseded by fresh complete
  captures using source/target quantization intervals and post-navigation
  events. The old receipts are retained, not relabeled as passes.
- An early font-resource filename guard rejected three uppercase `.TTF`
  names before generation. The generator preserves their observed spelling.

## Same-resource diagnostic fonts

`composition_marker_fonts.py` generates all 84 resource substitutes from
original geometric outlines. Only resource filenames are reused. Earlier
independent controls identify HGHT/HGBZ/HGHZ/HGBX/HGB1/HGB1X as the CJK,
ordinary Latin, alternate Latin and states 3/28/31 resources. Six different
hole markers retain these identities; other resources share a seventh marker.
That group does not identify each individual original symbol font.

Each corresponding PDF font has identical outline, advance and metric tables.
The viewer's format-13 cmap maps its BMP aliases to the original marker; the
PDF's format-12 cmap maps semantic BMP scalar values to that same marker.
Surrogates are excluded from the PDF cmap. The ordinary Latin resource also
supplies the previously identified decoration role. All font bytes are generated
externally; hashes and table-identity checks are in the receipt. These fonts
intentionally paint spaces and private-use characters as geometry and cannot
establish original text appearance or resolve the source meaning of A661.

The unchanged ten originals also convert with these explicit roles through
the already reviewed CLI; qpdf accepts all ten diagnostic PDFs. This changes
only the externally supplied fonts. The normal-font PDFs remain the reviewed
production outputs and retain their existing private-use substitution report.

## Comparison and limits

All 60 normal-font pages and all 60 marker-font pages are measured against
their corresponding PDF renders. One uniform PDF scale comes from the source
raster width and PDF page width. There is no registration, translation,
per-document correction, threshold fitting or resampling of the reference.
PDF raster grids have zero, one or two extra rows from integer rounding;
all nonoverlapping rows contain no threshold-128 ink. Grid sizes and all
differences are retained. Every one of the 120 comparisons has pixel differences.

All 60 marker pages have identical hashes in two independent cold sessions.
59 normal-font pages match repeated cold observations; the remaining page's
disagreement is retained below. These are scoped repeated observations, not
a complete or general readiness guarantee.

The receipt provides grayscale differences and symmetric distances between
threshold-128 ink pixels, including quantiles and counts beyond 1/2/4 pixels.
These are descriptive measurements, not acceptance tolerances. In particular,
this threshold omits faint PDF hairlines; large distances to remaining text
are not evidence that a vector was dropped. Existing original segment controls
already document source/PDF renderer sensitivity. Crowding with default fonts,
stroke darkness and the source ornament's appearance remain visible limits.
Even a close marker raster does not individually verify overlapping glyphs,
every resource identity, original font appearance or complete vector semantics.

The normal-font magnesium input `166d00147923…`, page 5, differs by 23,901
pixels between two cold sessions at identical 1003×1506 dimensions. Both
sessions' repeated captures are equal. A third cold session matches the second;
the initial disagreement remains unresolved. The first and second sessions
used observer v3 and v4 respectively (v4 changes only failure handling when
the limit-marker file cannot be opened). A further fresh session using the
same v3 binary as the first also matches the later raster, so the observer
revision difference alone does not establish a cause. Per-session observer
hashes and the differing acquisition iterations are explicit. This remains
evidence for investigation under
[Rust #441](https://github.com/rwv/caj2pdf-rust/issues/441). No majority vote or
retry-to-match rule converts it into a verified original-viewer page.

No new converter defect is established by these measurements alone. Source-font
substitution and viewer uncertainty are not declared unavoidable input damage.
Samples #51 remains open for causal geometry/painting analysis and any resulting
focused fixes; #406's full fidelity, outline and exception criteria remain open.

## Reproduction and provenance

Use the checked-in `native_composition_inventory.py` for metadata and
`native_page_capture.py --help` for opt-in capture. Its manifest entries are
`source_sha256`, external `source_path`, and `pages` (at most ten inputs,
1–12 pages each). Provide the pinned local viewer image and compile the
original interposer against public Qt 5 development headers:

```sh
c++ -std=c++17 -shared -fPIC -O2 -Wall -Wextra -Werror \
  -DQT_NO_VERSION_TAGGING $(pkg-config --cflags Qt5Gui) \
  research/cajviewer/qpaint_observe.cpp -ldl -o /external/observer.so
python3 research/cajviewer/native_page_capture.py \
  /external/cases.json /external/new-run --observer /external/observer.so \
  --image sha256:cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de
```

The measured build used Debian Qt 5.15.15 development headers, package SHA-256
`826476bc3bce54d20e1a168c089b05a27aa7ff153fe892bdc75d629102a48a63`,
and GCC 14.2.0. Header version is not asserted to be the opaque viewer's Qt
runtime version; its complete image identity is pinned separately. The receipt
lists Python/Pillow/Tesseract/PyMuPDF/NumPy/SciPy/fontTools versions, observer
and source hashes, font manifests and exact per-input PDF hashes.

Metadata extraction uses the independent bounded source parser; the new visitor
receives only complete nonterminal records and excludes opaque HN-B tails.
PDF streams are bounded and pages are processed sequentially. Raster analysis
was repeated with a 2 GiB address-space cap and one numerical-library thread;
all recorded measurements reproduce exactly. Linux `/proc/self/status` records
the analysis process high-water mark. The initial `ru_maxrss` value inherited
a pre-exec parent maximum and is explicitly excluded as an operation peak.

All new implementation and original controls are MIT. No differently licensed
converter, private HN/JBIG module or vendor implementation was consulted,
copied or translated. No production dependency, release or source-font
redistribution is introduced. Catalog CI compiles the observer and tests
original controls; it neither downloads nor launches the viewer or corpus.
External Qt, Python/font/rendering libraries and the opaque viewer retain
their upstream licenses; none is vendored or relabeled as project-owned MIT
source. The new selected controls bring Catalog validation to 80 tests,
with zero skipped tests; external viewer observations are reported separately.
