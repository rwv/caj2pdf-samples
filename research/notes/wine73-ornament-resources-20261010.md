<!-- SPDX-License-Identifier: MIT -->

# Wine 7.3 C8 ornament resource selection

The triangles in [Rust #532](https://github.com/rwv/caj2pdf-rust/issues/532)
are the converter's documented default U+25BA substitute. The original C8
`8010` drawing record requests a font ornament. Its value distinguishes
**different glyphs**, so a single guessed arrow cannot preserve all patterns.
Existing explicit decoration-font/character options can reproduce each measured
pattern when a document uses one of these values. No converter code change or
font redistribution is required for those documents.

The [receipt](wine73-ornament-resources-20261010.json) records identities,
all observations, failed attempts, per-page scope, subset and runtime checks.
Raw sources, fonts, PDFs and captures remain external under
`~/.cache/cajviewer73-fixes-20261010/532-ornament/`.

## Resource and raw-record evidence

The unchanged Wine 7.3 prefix supplies `HGBZ_CNKI.ttf`, SHA-256
`c44abe24684e5c0ea849b43116dc97a97d2eeda5b36eb33d490090f7d0723758`,
PostScript name `HGBZ_CNKI`, face 0, 2,048 units/em. These are **cmap aliases**,
not document Unicode; decorations retain empty ActualText inside an Artifact.
No alias is inferred from visual similarity or an arithmetic mapping formula.

| `8010` value | Measured resource cmap alias | GID | Actual source/page |
| ---: | --- | ---: | --- |
| 1 | U+5D04 (23812) | 1862 | `90e7b47716c3`, page 6 |
| 2 | U+5D05 (23813) | 1863 | `d6a23a9cfd0f`, page 5 |
| 46 | U+5D41 (23873) | 1909 | `7e3f2c0faebb`, page 10 |
| 117 | U+5D95 (23957) | 1981 | `b9a64bf99e4b`, page 1 |

All four advances are 2,048 units. A bounded source-record visitor finds exactly
one ornament record in each original. The main case has value 46 at offset
8,480,070, points `(4753,5819)`–`(9717,5819)`, explicit axes 38/38, `801d/0`,
`80ce/1` and style `0x1063`. It is not an embedded picture or an ordinary text
character. Source/PDF paint order is checked independently below.

Exploratory original controls under the existing Linux public-FreeType observer
record one outer cmap/load pair at each of five observed sizes for every value:
5, 4, 6, 12 and 20 ppem. Their aliases/GIDs are those above, consistent with the
hash-pinned font's cmap. These four Linux sessions **failed complete-page raster
navigation** and remain NOT_CONFIRMED for that purpose. They supply API metadata,
not a Linux visual pass or evidence of native Windows equivalence.

## Wine discriminators

The independently authored
[`ornament_resource_controls.py`](../cajviewer/ornament_resource_controls.py)
reuses the project's MIT C8 and geometric-font builders. Each source has three
horizontal spans of 500/1,000/3,000 source units plus an unchanged neighboring
line. Only the ornament value varies. Each generated font contains the same
original quarter-em rectangle at **one** candidate ornament alias; the other
three aliases are absent. No vendor outline is read by the generator.

Wine 7.3 draws different normal patterns for the four values. A control font
containing only the value-1 alias yields rectangles for value 1 and no ornament
for the other values. Giving each value its measured single alias makes all
four Wine crops **exactly identical**, including the unchanged neighboring line.
This independently verifies slot selection without guessing from the normal
pattern. Source cold repeats also match exactly.

The first controls used neighboring `8006/0`: Wine displays it, but the core
correctly refuses that unadmitted record at byte 152. Final controls change only
that neighbor to the already admitted `8006/a383`. All four final sources and
four generated marker fonts reproduce byte for byte from the committed builder.
The final Wine source/repeat/marker/PDF runs are retained separately; no failed
attempt is replaced or counted as a pass.

The reference profile is CAJViewer 7.3.151 Simple / Wine 8.0 32-bit, image
`sha256:6c9f5ec0610a7ff8bc45fe8e0a87dffd0ff17e42466c90b80237a1712847b95c`,
the same font/MSXML prefix and protocol as the
[orientation study](wine73-jpeg-orientation-20261010.md). Each session is cold,
maximized, single-page, 75%, 1600 × 1200 at 96 DPI, with numeric page/zoom gates
and two captures per page. Read-only inputs/root, offline execution, nonroot
UID, dropped capabilities, memory/CPU/PID/file/lifetime limits and container
cleanup remain in force. Only a generated HGBZ resource is replaced for a
marker session. No source document is edited for the actual comparisons.

## Exact configuration and verification

The pinned current implementation is merged Rust #535,
`e6343aa785547f5e34bb499dfda56be2d5dc595d`. Its CLI/WASM artifacts are the identical
Wine-tested artifacts from the orientation report. All four original baseline
PDFs remain byte-identical to historical #459 without the new font options.
For the main value-46 case, the explicit recipe is:

```sh
caj2pdf original.caj -o output.pdf --no-system-fonts \
  --font-cjk '/external/NotoSerifCJK-Regular.ttc#2' \
  --font-latin /external/FreeSerif.ttf \
  --font-decoration /external/HGBZ_CNKI.ttf --decoration-char '嵁'
```

Here `嵁` is the literal U+5D41 **nonsemantic alias**, not extracted text. Supply
only an externally obtained resource you are entitled to use and verify the
hash above. Installing SimSun in Wine does not change an embedded PDF glyph.
Node/browser use `decoration: { source: fontSource, character: '\u5d41' }` in
`hnc8.fonts`, alongside the same CJK/Latin inputs and collection face.

The 10-page main source is
`7e3f2c0faebb8ddac2f4feff3cfc9249476ab170b43250ac00610b10aa46c74b`.
Its historical/main PDF is
`db0859192313afc1879f3b2bf941c9978251ef01ebeec28d446a16a4992bff23`;
the configured PDF is
`fa2d31c5f32f0baf6876392ecd060652ccf4074d41b21b4abde5ce89727c08bf`.
Wine now displays the intended repeated small pattern on page 10. Every fresh
original page crop matches its historical cold repeat. **Pages 1–9 are image-only**:
their configured PDF crops exactly equal the baseline PDF crops. They still
have source/PDF raster differences and are not relabeled exact fidelity passes.
Page 10's text/style differences remain #531, and pattern sampling/repetition
and other raster differences remain #534.

An independent actual case, `90e7…` page 6, displays its own value-1 pattern
with U+5D04. The value-2 and value-117 actual PDF pages also display their
respective patterns. The previously unavailable `b9a6…` PDF now opens all four
pages under this recipe; its font-sharing/window interaction is investigated
separately in #533 rather than claimed solved by one successful configuration.

Across the four actual PDFs (**25 pages**), independent PDF inspection verifies:
all page boxes, image bytes/dimensions, paint-kind order, ordinary glyph outlines,
advances, semantic text, transforms, gray and clipping are unchanged. Only the
ornament font/glyph selections differ; the 63/45/47/57 nonsemantic ornament
counts remain unchanged. The nine image-only page content streams are identical.
For all eight synthetic PDFs and four actual PDFs, fontTools checks the chosen
subset outline, font/PDF advance, exact alias, empty ActualText and Artifact
scope against the selected external/original font. Metadata contains only
outline hashes, not outlines.

**All 12 native/Node/real Chromium outputs match byte for byte.** Font and source
hashes remain stable; ranged/OPFS input, sequential output and empty browser OPFS
cleanup are verified. This is resource/transport preservation, not full-page
pixel parity. At 75%, the four original resource controls still differ from
their PDFs by 1,983/1,817/2,038/1,661 pixels. The original rectangle controls
all differ by 1,691 pixels. These residuals are retained, without resampling,
registration, lossy normalization or tolerance fitting.

## Scope and review boundaries

The existing API takes one decoration alias per document. A document with
multiple distinct ornament values cannot request separate glyphs through that
single field; this study does not invent a universal alias or claim arbitrary
ornament support. Every measured actual document here has one value. Future
mixed-value support needs separate bounded API/format evidence under #406.
The default U+25BA remains a deliberate substitution when no resource is given.

The generator, tests and documentation are original MIT source. Two original
control tests validate the source parser's 43 nonsemantic marks followed by the
neighboring vector, descriptor-only differences, four isolated cmap slots and
identical original rectangle geometry. They require no corpus or viewer.
The catalog is unchanged. No private HN/JBIG or foreign converter implementation
was read or copied. External font programs, source documents, PDFs, screenshots
and vendor binaries are not committed. No release or broad #406/source-font/
full-raster completion is claimed.
