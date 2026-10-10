# Native font-slot observation protocol

[Issue #106](https://github.com/rwv/caj2pdf-samples/issues/106) remains open.
This first step establishes **336 resource/native-code slots in original
controls**, with reverse-order and isolated-character agreement. It does not
establish original-font appearance for converted documents or change any
conversion result. The catalog remains **1,408 identities: 1,361 PASS,
20 FAIL and 27 UNSUPPORTED**.

The [metadata receipt](native-font-observation-20261009.json) has SHA-256
`5f9164c9a657840d7a9c2bbd5afd1cc26824b1d7ff7f30644f044959703833c4`.
It retains the source/tool/resource hashes, all 48 session outcomes, prior
analysis failures, final process exits, capture hashes and repertoire counts.
No external document, font program, outline, rendered pixels or viewer binary
is committed. The original controls are reproducible from MIT source.

## What the controls establish

[`native_font_controls.py`](../cajviewer/native_font_controls.py) authors C8
mode-2 pages using previously measured framing. Each page has unique codes,
style `10a5` and font word `8067/6`. Five `801d` states each use the 62 ASCII
letters/digits in forward and reverse order with `80ce/1`, followed by separate
single-character `A` and `1` controls. The `80ce/0` pilot uses 26 raw native
codes in both orders and separate endpoint controls. Its initial plan called
these Latin letters incorrectly: the actual observed resource is HGHT. That
attempt is retained and is not used to infer Latin-mode behavior.

| State / mode | Observed family | Distinct native codes |
| --- | --- | ---: |
| `801d/0`, `80ce/1` | HGBZ_CNKI | 62 |
| `801d/4`, `80ce/1` | HGHZ_CNKI | 62 |
| `801d/3`, `80ce/1` | HGBX_CNKI | 62 |
| `801d/28`, `80ce/1` | HGB1_CNKI | 62 |
| `801d/31`, `80ce/1` | HGB1X_CNKI | 62 |
| `801d/0`, `80ce/0` | HGHT_CNKI | 26 |

The [original interposer](../cajviewer/ft_glyph_observe.c) forwards documented
`FT_Get_Char_Index` and `FT_Load_Glyph` calls and records their results, thread,
face, size and **nesting depth**. It does not read or export glyph outlines.
FreeType's [character mapping API](https://freetype.org/freetype2/docs/reference/ft2-character_mapping.html)
defines the code-to-glyph query; its
[load flags](https://freetype.org/freetype2/docs/reference/ft2-glyph_retrieval.html)
define `FT_LOAD_RENDER`. A render flag alone is not document-use evidence.

The first 24 sessions lacked depth information. Their first adjacency analysis
correctly refused an ambiguous first glyph: internal font probes occurred
inside the load. The next 24 sessions explicitly record nesting. An initial
analysis of these traces still expected the non-rendering `75785` load at the
outer level; it too is nested. That failed analyzer is retained. The final
[checker](../scripts/native_font_trace.py) requires the outer cmap query to
immediately precede its matching outer render load on the same thread/face,
with matching size. It excludes nested events from mapping candidates while
retaining and counting them. It requires complete, identical code/GID sequences
at 5, 6, 9, 19 and 20 ppem and agreement across reversed/isolated controls.
There is no nearest-code heuristic or inferred arithmetic alias formula.

All 24 final sessions pass these scoped checks: **48,228 events**, including
**41,388 nested events** and **3,420 outer render loads**. All source hashes
remain unchanged, all containers are removed, no trace limit is reached and
no recorded FreeType error is ignored. The page observations are STABLE only
in the existing sense of two equal complete cached pixmaps. They do not solve
[Rust #441](https://github.com/rwv/caj2pdf-rust/issues/441)'s readiness problem.

## Resource checks and remaining repertoire

[`native_font_resource_probe.py`](../scripts/native_font_resource_probe.py)
uses the public FreeType API to query these explicit slots in six hash-pinned
external resource files. All 336 match. The resource probe uses FreeType
2.12.1 with its library hash in the receipt. It loads no glyph outlines and
exports no font programs. A family name and matching cmap slots do not prove
which actual path a viewer opened, or whether two different GIDs have the
same shape. Font names, embedding flags and public availability are not license
grants; no font redistribution or product integration is proposed here.

For **305 of the 310 Latin slots**, ordinary Unicode selects a different GID.
`L` is the one identical slot in each of the five resources. For example,
HGBZ's authored `1` maps through cmap argument 25969 to GID 2578, whereas
ordinary U+0031 selects GID 18. This establishes a mapping distinction, not
an outline-difference claim. Semantic text must not be changed to these aliases.

The [bounded repertoire inventory](../scripts/native_font_repertoire.py)
checks the 18 cases supplied with font options in the frozen runtime cohort.
Thirteen are measured native originals: **77 pages, 113,418 ordinary glyph
draws and 212 ornaments**. The other five are outside this native model and
are explicitly listed; passing font options does not establish a requirement.
Roles below come from the existing published model, not new source-font
observations. No document text order is emitted.

| Model role | Ordinary draws | Distinct Unicode characters | Ornament draws |
| --- | ---: | ---: | ---: |
| CJK | 76,944 | 1,687 | 0 |
| Latin | 34,444 | 140 | 212 |
| Alternate Latin | 870 | 59 | 0 |
| Latin state 3 | 415 | 57 | 0 |
| Latin state 28 | 58 | 9 | 0 |
| Symbols | 687 | 20 | 0 |

These controls do **not** measure that full repertoire. Other styles, font
words, CJK characters, symbol resources, private-use characters, ornaments,
HN-B mode 0 and repeated-character caching remain unverified by this protocol.
Model roles and caller-font subset consistency are separate from original
resource/shape identity. The existing ActualText approximation and ornament
alias remain unresolved. No new converter defect or conversion pass is claimed.

## Bounds, checks and reproduction

The opt-in page driver adds `--font-observer` to its existing isolated viewer
workflow. The image is pinned, offline and read-only, with UID 1000, dropped
capabilities, no new privileges, 2 GiB memory/swap, two CPUs, 256 PIDs, bounded
tmpfs/file sizes and a 90-second lifetime per control. The observer caps each
process at 100,000 records and marks truncation; the checker refuses the marker,
malformed/old/truncated traces, errors, missing sizes and ambiguous sequences.
Its input is capped at 64 MiB. The separate font probe allows six resources,
16 MiB per font and 62 mappings per resource, under a 256 MiB/45-second offline
container limit. Repertoire parsing is per page with existing record bounds;
distinct repertoire and model-state combinations are each capped at 65,536.
The measured inventory also has a 512 MiB process address-space limit.

Ten new original control tests cover real public-FreeType forwarding and
bitmap-result preservation, explicit nested calls, nonmatching-family filtering,
the actual event cap, erroneous loads, trace corruption/ambiguity, reordered
disagreement, resource hashes/cmap mismatches and repertoire roles. They use
only this project's generated geometric font. All ten, six existing font-subset
tests, eight page-capture controls and four catalog tests pass locally:
**28 tests, zero skipped**.
Catalog CI runs the new controls with an explicit FreeType development package.

With externally supplied, permitted viewer resources and the existing compiled
Qt observer, generate a new output directory and run each manifest separately:

```sh
python3 research/cajviewer/native_font_controls.py /external/controls-new
gcc -std=c11 -shared -fPIC -O2 -Wall -Wextra -Werror \
  $(pkg-config --cflags freetype2) research/cajviewer/ft_glyph_observe.c \
  -ldl -o /external/ft-observe.so
python3 research/cajviewer/native_page_capture.py /external/controls-new/latin.json \
  /external/latin-observations-new --observer /external/qpaint-observe.so \
  --font-observer /external/ft-observe.so --lifetime-seconds 90 \
  --image sha256:cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de
```

Analyze each trace with its manifest's `expected_codes` and measured family,
then use `native_font_trace.agree` across all four cohorts. Extract the receipt's
`resource_manifest` for the separately bounded resource probe; supply the actual
external font directory and an absolute FreeType shared-library path. No tool
downloads fonts or viewer binaries. Do not apply this unique-code protocol to
real cached/repeated text without further controls.

All added source is original MIT work using public API descriptions and this
repository's MIT framing/model code. No private HN/JBIG module, differently
licensed converter source, vendor implementation or font outline was copied,
translated or inspected. Source/code licenses are distinct from the external
resources. Issue #106's observation-method criterion is addressed within this
explicit control scope; full resource/state coverage, source/font geometry and
semantic/visual verification remain open. There is no production dependency,
native/CLI/JS API, format support, PDF output or release change.
[Rust #475](https://github.com/rwv/caj2pdf-rust/issues/475) remains research-only.
