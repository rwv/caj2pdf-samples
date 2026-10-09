# Native glyph, font-role and ornament model verification

Follow-up to [samples #51](https://github.com/rwv/caj2pdf-samples/issues/51)
and [Rust #406](https://github.com/rwv/caj2pdf-rust/issues/406). All ten accepted
native originals pass the existing glyph models on both their normal and
original-marker PDFs: **60 pages, 83,432 ordinary glyphs and 212 ornament
marks from four source records per PDF set**. Positions, dimensions, shear,
grayscale, semantic order and complete paint-kind order match. Marker PDFs
also match the expected diagnostic font roles. This establishes consistency
with the published original-control models, not original-font or raster fidelity.

The [per-page receipt](native-glyph-model-20261009.json), recorded on
2026-10-09 UTC, pins every source/PDF/font and checker dependency SHA-256.
Its SHA-256 is `869470f8666ee34dcf51c635ebc7de63de538a7f1f91201f66bed380ef6c618c`.
Production remains `5f3cf7fb08297ddadfb1cff05e8dcdfe17c037dc`, CLI SHA-256
`d213898ee16a32f0d5304dc96438ffde2402d8135af3b0728a764c1ae8ea41a0`.
Conversion totals remain **1,252 PASS / 18 FAIL / 27 UNSUPPORTED**. No new
converter defect or unavoidable source exception is demonstrated.

| Source SHA-256 prefix | Pages | Ordinary glyphs | Ornament marks |
| --- | ---: | ---: | ---: |
| `03770ea1cdeb` | 5 | 7,721 | 0 |
| `166d00147923` | 12 | 20,693 | 0 |
| `1b9aa912e0bc` | 4 | 6,579 | 0 |
| `3f3b9b57d692` | 4 | 5,969 | 0 |
| `63870d12f206` | 4 | 7,929 | 0 |
| `7e3f2c0faebb` | 10 | 1,977 | 63 |
| `90e7b47716c3` | 6 | 6,638 | 45 |
| `b9a64bf99e4b` | 4 | 7,565 | 47 |
| `d6a23a9cfd0f` | 5 | 10,277 | 57 |
| `e1b17805a87f` | 6 | 8,084 | 0 |

## Model and PDF checks

[`native_glyph_model.py`](../scripts/native_glyph_model.py) evaluates source
records with rational arithmetic. Its inputs are the published original controls
in [C8 native records](c8-native-records.md),
[C8 native controls](c8-native-controls.md),
[additional C8 profiles](c8-additional-profiles.md),
[HN-B legacy controls](hnb-compact-index.md),
[magnesium controls](hnb-magnesium-profile.md) and the
[original #391 provenance](https://github.com/rwv/caj2pdf-rust/blob/082f00fef4093ecd5f3f2f29f4b9f4821797eca1/docs/provenance.md#c8-four-page-article-records-391).
Original MIT Rust code was consulted for coverage. These are existing measured
rules, not a newly independent determination of physical units or geometry.

The model retains source style resets, independent width/height fields,
explicit axes, class-specific baselines and offsets, persistent font/CJK state,
shear and gray. Mode-0 digit, alphabet, symbol and hyphen rules remain distinct.
The source-record framing and semantic character mapping reuse the earlier
bounded [text-order check](native-content-order-20261008.md). Unmeasured classes,
styles, dimensions and ornament directions within the checker's admitted
profiles raise an error; this tool is not a general format-admission validator.

[`native_glyph_geometry.py`](../scripts/native_glyph_geometry.py) reads actual
PDF text matrices, gray and identity Unicode mappings. It checks inherited
page/crop boxes, identity text graphics transforms and normal blending, and
rejects unsupported operators, clipping on ordinary text, transparency groups
and unbalanced contexts. All six matrix entries are compared with the existing
`1/20000` point serialization tolerance. Gray uses `1/1000000`; neither tolerance
was fitted to these outputs. Maximum matrix residual is
`2.8106339160609e-13` point in each PDF set.

The marker check inspects only this project's original geometric fonts. Actual
CID-to-glyph mapping, embedded original contours, em units, advances and PDF
widths identify roles independently of PDF resource names. Seven generated
roles cover the measured CJK, Latin, alternate Latin, three additional Latin
states and symbols. The ornament role is the explicitly supplied Latin marker
font in these pinned diagnostic PDFs. Normal PDFs have no marker-role or real
font-outline check. Their single known magnesium private-use visual replacement
retains U+E6C7 in ActualText; the marker PDFs contain that code and need no
replacement. Neither case identifies the source symbol's meaning.

Each ornament is a clipped, nonsemantic Artifact containing an empty ActualText
span. Source spans use the measured nominal em for repetition, including a
partially clipped final mark, rather than rounding down or changing spacing.
All 212 matrices, black fill colors, endpoint clips and marker roles match.
The default arrow remains an explicit substitute for the vendor ornament;
this result says nothing about equality of those outlines.

The complete sequence contains **84,028 paint-kind events** per PDF set:
83,432 ordinary glyphs, 212 ornament marks, 57 images and 327 vectors. This
checks where ornaments and other kinds occur among one another. Image and vector
geometry/resource correctness still use their respective
[image](source-image-geometry-20261008.md) and
[vector](native-vector-geometry-20261008.md) reports. Ten image-only pages have
zero ordinary glyphs; their empty glyph results add no font-fidelity evidence.

## Original controls, bounds and reproduction

Nine new original MIT test groups include a literal-coordinate source/PDF pair
that is authored separately from the evaluator, generated diagnostic fonts,
and a 90-source-unit ornament that extends slightly beyond one em. Changes to
position, size, shear, gray, semantic identity, font resource, CID mapping,
advance width, order, omission and duplication fail. Ornament negatives change
spacing, clipping, gray, mark count and order relative to glyphs/vectors.
Nonempty ornament semantics, incorrect encoding, unknown transforms and nearby
unmeasured source profiles are refused. All **96 selected Catalog tests** pass
locally with zero skips, including the nine added groups; Catalog CI runs the
same original controls without the external document corpus.

Each pair is checked before and after reading by hash. Processing is sequential,
one page at a time: source text at most 1 MiB/65,536 records, expanded paint
sequence at most 131,072 events, decoded PDF page at most 1 MiB/131,072 operators,
graphics stack depth 32 and marked-content depth two. Diagnostic font data is
bounded to 4 MiB per program, 64 used font resources per document, eight subset
glyphs and bounded CID maps/width arrays. Dependencies are pikepdf 10.5.1,
PyMuPDF 1.27.2.2 and fonttools 4.62.1; Python was 3.13.5. The final 20-pair run
used one process with a 2 GiB address-space cap; VmHWM was 89,444 KiB and VmPeak
147,652 KiB. Elapsed time was 45.21 seconds. No optional skip counts as a pass.

```sh
python3 research/scripts/native_glyph_geometry.py /external/source.caj \
  /external/reviewed.pdf --source-sha256 SOURCE_SHA256 --pdf-sha256 PDF_SHA256
# Only for this project's generated diagnostic fonts and their pinned PDFs:
python3 research/scripts/native_glyph_geometry.py /external/source.caj \
  /external/markers.pdf --source-sha256 SOURCE_SHA256 --pdf-sha256 PDF_SHA256 \
  --original-marker-directory /external/original-marker-fonts/pdf
```

The initial complete glyph run passed. Review added explicit PDF-width checks,
stricter neighboring profiles, then ornament clipping/repetition/order before
the bounded run; each complete run passed. Final self-review also refused direct
font resources to prevent cache-key aliasing, added a negative control and reran
all nine affected groups and all 20 pinned pairs successfully. A separate public-API probe
of two QPainter drawImage entry points observed no calls on a new original
two-glyph control. Existing pixmap observations were unchanged. This repeats
the earlier observer limitation and supplies no new corpus fidelity evidence.
An initial probe manifest used the wrong variant's page-count offset and was
refused before viewer launch; both corrected sessions retained source integrity
and confirmed cleanup. Failed attempts and intermediate receipts stay external.

## Provenance and remaining acceptance

All added code/controls are original MIT work. Public PDF syntax, existing
project-authored controls and original MIT Rust were consulted. Only generated
geometric marker outlines were inspected. No vendor font outlines, foreign
converter implementation, private HN/JBIG code, document bytes/text, fonts,
pixels or derived PDFs enter this repository. Existing pinned dependencies are
reused. Production APIs, native/Node/browser behavior and output bytes do not
change; no release is requested.

The [60-page viewer observations](native-page-composition-20261008.md) still
have source/PDF raster differences and one normal-font cold-session disagreement
tracked in [Rust #441](https://github.com/rwv/caj2pdf-rust/issues/441). Font and
ornament appearance, complete raster fidelity, unknown C8/HN-B outlines and
remaining exception evidence are unresolved. This advances model coverage for
samples #51 and Rust #406; their incomplete acceptance criteria remain open.
