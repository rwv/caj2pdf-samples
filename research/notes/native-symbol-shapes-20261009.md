# Native symbols need separate glyph and semantic identities

The [opened-resource observations](opened-font-resources-20261009.md) exposed
different GIDs for two native codes with the same modeled Unicode character.
This follow-up confirms **different glyph geometry and raster data**, then
reproduces the current converter's loss of that distinction using entirely
original geometric controls. It opens the implementation work in
[Rust #518](https://github.com/rwv/caj2pdf-rust/issues/518), under #406.
[Samples #106](https://github.com/rwv/caj2pdf-samples/issues/106) remains open.

The [metadata receipt](native-symbol-shapes-20261009.json) has SHA-256
`67ab448f2045627df2ab551b4ebd841701ee2f1c048f6d4bf93b2c774b9f6a73`.
It contains measurements and hashes only. External font programs, outlines,
pixels, document bodies and derived PDFs are not committed or distributed.
Catalog status remains **1,408 identities: 1,361 conversion PASS, 20 FAIL,
27 UNSUPPORTED**. These original controls are not additional corpus documents.

## Actual resource measurements

The pinned HGFX_CNKI resource has 2,048 units/em and SHA-256
`4ef6bcbe9c48ebff552a57e0bca245554dcb4d5bb12d580b95e0babdd736036c`.
The original [probe](../cajviewer/ft_shape_probe.c) uses public FreeType APIs
to measure explicit GIDs and cmap arguments. All **21 previously observed
symbol-code mappings** select the expected GIDs. The run makes 43 explicit
queries including ordinary Unicode comparisons and direct-GID cross-checks;
missing ordinary slots remain recorded as missing.

| Native code | Modeled character | Observed cmap argument | GID | Exact unscaled bounds | Advance |
| --- | --- | ---: | ---: | --- | ---: |
| `a1af` | U+2019 | 26270 | 671 | 432,939,656,1385 | 1024 |
| `a3a7` | U+2019 | 24518 | 374 | 200,864,478,1471 | 681 |
| `a1aa` | U+2014 | 25962 | 481 | 344,956,1664,1104 | 2048 |
| `a3ad` | U+FF0D | 25962 | 481 | 344,956,1664,1104 | 2048 |

The two U+2019 choices have different bounds, advances, decomposed outline
hashes and unhinted grayscale raster hashes at both 64 and 128 ppem. At 64
ppem their bitmap sizes are respectively 8×15 and 10×20. Thus their difference
is not just a GID numbering distinction. Conversely, the two dash codes select
the same glyph while retaining different modeled semantic characters.

Ordinary U+2019 in this resource selects GID 103, with different measurements
from either source choice. A caller's ordinary Unicode-font contract does not
make an unchanged obfuscated viewer resource a suitable semantic font. More
generally, a single character lookup cannot choose both observed source glyphs,
even when the supplied font contains both. This is a representational gap to
address with explicit glyph selection, not a reason to change the character
decoder or guess a Unicode replacement from visual similarity.

The probe loads scalable, non-variable, non-tricky outlines without hinting or
embedded bitmaps, measures the exact bounds, and hashes canonical public
decomposition callbacks. It separately renders at fixed sizes without hinting.
See FreeType's [glyph retrieval contracts](https://freetype.org/freetype2/docs/reference/ft2-glyph_retrieval.html)
and [outline measurement/decomposition API](https://freetype.org/freetype2/docs/reference/ft2-outline_processing.html).
Outline segment coordinates and pixel rows are fed to hashes in memory;
neither is exported.
Command counts and metrics alone are not the shape proof: original equal-bounds
controls and both raster measurements also distinguish the shapes.
Different command hashes by themselves can represent equivalent visible paths.

## Original controls reproduce the limitation

[`native_symbol_pair_controls.py`](../cajviewer/native_symbol_pair_controls.py)
creates an original MIT font with a full square at U+2019, an upper half at
the observed `a1af` alias and a lower half at the observed `a3a7` alias.
Four authored one-page HN-B mode-0 inputs contain the separate codes and both
orders of the pair. Style `10a4`, positions and other framing are fixed; no
vendor glyph shape or external document is used in these fixtures.

The viewer's successful face-constructor hash binds calls to this original
font. The separate and forward/reverse controls select the expected GID
sequences (2 and 3) at **all five observed sizes**. Their final page captures
show the expected upper/lower regions in the correct order. For example, the
isolated dark-component bounds are `[100,97,121,106]` and `[100,105,120,114]`.
All four source hashes remain unchanged and all containers are removed.
The committed generator exactly reproduces the launched source and font hashes.

All four baseline native conversions succeed and pass qpdf. Extracted text
retains U+2019, but both codes use the same `/F4` CID `2019`, whose subset
outline is the full square. The two isolated outputs are **byte-identical**;
the forward/reverse outputs are also **byte-identical**, despite distinct
viewer page pixels in each pair. The baseline program SHA-256 is
`dfad3f1734ee25305923e21566f1523cdbc17df2d5e56d4109312875e3637c27`.
Its core/CLI trees, workspace manifest and lockfile equal current Rust main
`6b184250ab8d51e5be6215e17169d6c39e33ac2c`; the receipt pins each Git object.
The PDF resource dictionary's eight role names reference one font object;
they are not eight distinct embedded font programs.

## Validation, bounds and provenance

Four new original tests cover equal rectangles/aliases, identical bounds with
different interior shapes, exact quadratic/cubic extrema, translated geometry,
known pixel coverage, missing slots, wrong hashes and invalid/oversized queries.
Together with existing font, page-capture and catalog checks, **40 tests pass,
zero skipped**. Required CI includes the new probe tests and needs no viewer,
font or corpus download.

The source probe streams fonts through 64 KiB buffers with a 32 MiB limit,
accepts at most 128 queries, caps each callback kind at 65,536 operations and
coordinates at ±2²⁴, and limits grayscale rasters to 2,048 pixels per side.
Both probe runs use the pinned offline image, read-only inputs, an unprivileged
user, dropped capabilities, 256 MiB memory/swap, one CPU, 16 PIDs and a
45-second host timeout. Both exit zero and are removed. Tightening request
syntax in review produced the final probe; its output equals the first run
byte-for-byte. Both source/binary versions and outcomes are retained externally.

The four viewer controls use the existing bounded offline page driver and
90-second lifetimes. An initial component-analysis import failed because scipy
was unavailable, before reading any capture. The final analysis uses a bounded
walk over at most 100,000 dark pixels; no viewer retry followed. All successful
and failed analysis attempts remain explicit in the receipt. STABLE cached
page captures still do not close the general viewer-readiness issue #441.

All added source is independently authored MIT work using documented APIs and
this project's original framing/geometric-font generators. FreeType/OpenSSL
and fontTools are existing external research dependencies; none of their
implementation source is copied. No vendor or foreign converter implementation,
private HN/JBIG module, external outline, font program or image is imported.
This note supplements the [historical provenance archive](provenance-archive.md).
Font metadata and public availability are not redistribution grants.

To reproduce the original fixture and measurements with permitted resources:

```sh
python3 research/cajviewer/native_symbol_pair_controls.py /external/new-controls
gcc -std=c11 -O2 -Wall -Wextra -Werror \
  $(pkg-config --cflags freetype2 openssl) research/cajviewer/ft_shape_probe.c \
  $(pkg-config --libs freetype2 openssl) -o /external/ft-shape
/external/ft-shape /external/HGFX_CNKI.ttf \
  4ef6bcbe9c48ebff552a57e0bca245554dcb4d5bb12d580b95e0babdd736036c \
  g:671 g:374 u:669e u:5fc6 u:2019
```

The full query list and exact offline commands are pinned by the receipt's
external ledgers. Run `cases.json` through the existing page driver with
`--font-directory /external/new-controls/fonts`, then convert with that original
font assigned to the CJK, Latin and symbols roles to reproduce the collapse.

No production fix, new compatibility pass, full-original font/geometry
verification or release is claimed here. Unhinted resource measurements are
not an exact oracle for the viewer's auto-hinted page pixels. Rust #518 requires
separate visual/semantic glyph selection, all 21 measured symbol mappings,
bounded invalid-case handling and native/Node/Chromium validation before its
implementation can be considered complete. Full repertoire/cache/ornament
work stays in samples #106. Rust #475 remains research-only; no font bundling
or browser font integration is implemented.
