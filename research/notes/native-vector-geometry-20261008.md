# Native vector geometry and painting order

Follow-up to [samples #51](https://github.com/rwv/caj2pdf-samples/issues/51)
and [Rust #406](https://github.com/rwv/caj2pdf-rust/issues/406). All ten accepted
native originals pass the existing measured vector model: **60 pages, 327
ordered paths (321 segments and six five-point radicals)**. Their positions,
widths, grayscale stroke colors and order among ordinary glyph/image/vector
operations agree with the unchanged reviewed PDFs. This is new source-record
verification, not a raster or original-font fidelity pass.

The [per-page receipt](native-vector-geometry-20261008.json) pins every source
and PDF SHA-256 and the checker/parser hashes. Production remains the reviewed
`5f3cf7fb08297ddadfb1cff05e8dcdfe17c037dc` implementation, with CLI SHA-256
`d213898ee16a32f0d5304dc96438ffde2402d8135af3b0728a764c1ae8ea41a0`.
Conversion totals remain 1,252 PASS / 18 FAIL / 27 UNSUPPORTED. No new
production defect or unavoidable exception is demonstrated by this check.

| Source SHA-256 prefix | Pages | Paths |
| --- | ---: | ---: |
| `03770ea1cdeb` | 5 | 12 |
| `166d00147923` | 12 | 134 |
| `1b9aa912e0bc` | 4 | 14 |
| `3f3b9b57d692` | 4 | 5 |
| `63870d12f206` | 4 | 4 |
| `7e3f2c0faebb` | 10 | 1 |
| `90e7b47716c3` | 6 | 109 |
| `b9a64bf99e4b` | 4 | 40 |
| `d6a23a9cfd0f` | 5 | 6 |
| `e1b17805a87f` | 6 | 2 |

## What is checked

[`native_vector_geometry.py`](../scripts/native_vector_geometry.py) reuses the
independent bounded source-record framing from the semantic and image checks.
It evaluates source fields using already published original-control findings:

- Ordinary `8006` segments subtract the source origin and add 20 source units
  on both axes. Source endpoint order is retained, including reversed or
  off-page coordinates. For `a385`, only the first x word loses a paired
  `c000` marker in mode 2. See the segment controls in
  [C8 native records](c8-native-records.md).
- HN-B mode-0 `a385` removes paired markers on both x endpoints and uses a
  15-unit vertical margin. Its page extents include the measured 100-unit
  addition. The [legacy controls](hnb-compact-index.md) retain source/PDF
  edge residuals and renderer-dependent darkness; this check does not erase
  those limits.
- `8007/a380` and `/a382` use the same segment model established by shifted,
  reversed and diagonal original pairs in the
  [#391 provenance record](https://github.com/rwv/caj2pdf-rust/blob/082f00fef4093ecd5f3f2f29f4b9f4821797eca1/docs/provenance.md#c8-four-page-article-records-391).
- `8090` uses the five connected vertices, four-unit width and local gray
  established by the [radical controls](c8-native-controls.md). The opaque
  value word is retained in metadata. Marker, dimension and profile guards
  reject unmeasured cases.

Source coordinates use the existing empirical factor `240/2473` points per
unit. This is a check of that model, not a new physical-unit determination.
PDF path coordinates are read as decimal rational values via pikepdf 10.5.1;
there is no pixel registration, fitted offset or render threshold. The
pre-existing page/image serialization tolerance is `1/20000` point. Maximum
observed coordinate residual is `1.6473918317832592e-13` point. Gray comparison
allows `1/1000000` for the writer's six-place decimal serialization.

The parser checks page/crop extents, identity vector transforms, opaque normal
blending, open connected paths, butt caps, miter joins, miter limit 10 and
stroke width/color. It checks inherited page boxes/rotation and rejects transparency groups,
clipping, transformed vectors, unmeasured
operators and unbalanced contexts rather than silently discarding them.
Graphics-state restoration is respected around images and text.

There are 83,816 checked paint-kind events: 83,432 ordinary glyphs, 57 image
draws and 327 vectors. The category sequence preserves vector placement among
text and images. It does not identify glyphs or image resources by itself;
those have separate [semantic](native-content-order-20261008.md) and
[image identity/geometry](source-image-geometry-20261008.md) checks. Four
source ornament records and their repeated PDF Artifact glyphs are excluded
from this sequence. Their order, exact outlines and appearance remain open.

## Controls, bounds and retained attempts

Seven original control groups run in Catalog CI. An independently authored
source and literal-coordinate PDF pass. Valid-PDF changes to position, width,
color, vector order, omission and duplication fail. Moving a vector around a
glyph also fails. Other controls cover marker scope, mode-0 y placement,
radical vertices/color, short source reads, input hashes, page/crop changes,
operation limits and unmeasured or unbalanced graphics state.

Only one page is processed at a time: source reads are at most 64 KiB,
source text at most 1 MiB/65,536 records, decoded PDF page contents at most
1 MiB/131,072 operations, paths at most eight points and graphics depth at
most 32. The final sequential corpus run used a 2 GiB address-space limit;
`/proc/self/status` reported VmHWM 45,796 KiB and VmPeak 65,408 KiB. Input and
PDF hashes are checked before and after each document. No missing input or
optional skip is counted as a pass.

The initial checker completed six documents and refused four because PDF
ornament glyphs use an Artifact containing an empty ActualText span. The
checker now recognizes that bounded nesting while excluding ornaments from
its advertised order scope. These were measurement refusals, not converter
failures. A hand-calculated test expectation and an intermediate indentation
error were corrected before the final run. They are retained in the receipt;
no unsuccessful attempt is relabeled as a successful corpus run.

To inspect one pinned external pair:

```sh
python3 research/scripts/native_vector_geometry.py /external/source.caj \
  /external/reviewed.pdf --source-sha256 SOURCE_SHA256 --pdf-sha256 PDF_SHA256
```

## Provenance and remaining acceptance

All added source and fixtures are independently authored MIT research code.
Only existing original controls/notes, public PDF syntax and pikepdf APIs
inform the check. No foreign converter, vendor/private HN/JBIG implementation,
source-document text, font outlines, document bytes or pixels are imported.
Documents, fonts, captures and derived PDFs remain external. No new dependency,
production API/CLI/JavaScript behavior, output PDF or release changes.

The [60-page viewer report](native-page-composition-20261008.md) remains the
rendering evidence. Its pixel differences, normal-font cold-session disagreement,
font substitutions, glyph placement and ornament limits are not waived.
This advances the vector portion of samples #51 and Rust #406; neither parent
meets its full acceptance criteria yet. The next native correctness work is
same-resource glyph geometry/resource evidence and unresolved font/ornament
appearance, not tuning hairline width to one renderer.
