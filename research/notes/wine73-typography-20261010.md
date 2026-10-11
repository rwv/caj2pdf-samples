<!-- SPDX-License-Identifier: MIT -->

# Wine 7.3 native typography requirements and remaining mappings

[Rust #531](https://github.com/rwv/caj2pdf-rust/issues/531) is addressed through
its concrete caller-resource/unmeasured-mapping investigation path. The current
substitute-font recipe still differs from Wine on all 46 available native-text
pages. This is **not** a typography fix or a claim of original-font parity.
Installing Windows fonts in Wine cannot replace the fonts embedded in a PDF;
supplying a same-named font also cannot recover a missing native glyph mapping.
Original controls further show placement differences with identical glyph
outlines, so the problem cannot be attributed entirely to font substitution.

The [metadata receipt](wine73-typography-20261010.json) records all ten documents
and 60 selected pages, resource/output identities, native counts, fresh/historical
observations, original controls, failed hypotheses and exact remaining scope.
External documents, fonts, PDFs and screenshots remain under
`~/.cache/cajviewer73-fixes-20261010/531-typography/`.

## Current-main cohort

The pinned code is merged #535,
`e6343aa785547f5e34bb499dfda56be2d5dc595d`; #536/#537/#538 add documentation only.
The ten native-document PDFs remain byte-identical to the historical #459 recipe:
external Noto Serif CJK collection face 2 and FreeSerif, with no extra source
resource roles or raw-glyph mappings. Fresh native/Node/Chromium outputs for
all 17 audit documents agree, as recorded in the
[orientation study](wine73-jpeg-orientation-20261010.md).

The completed #518/#521/#522/#525/#526 work does not change this default recipe.
Its explicit raw-code mappings cover 21 measured HN-B mode-0 symbol codes when
the caller supplies the required resource/options. That separate opt-in evidence
does not establish ordinary C8/HN-B Latin, CJK style, digit, bracket or formula
parity. No new implicit glyph mapping is inferred here.

| Source prefix | Pages | Fresh single-page/75% category |
| --- | ---: | --- |
| `03770ea1cdeb` | 5 | Native typography plus width difference |
| `166d00147923` | 12 | Native typography plus width difference |
| `1b9aa912e0bc` | 4 | Native typography plus width difference |
| `3f3b9b57d692` | 4 | Native typography difference |
| `63870d12f206` | 4 | Native typography difference |
| `7e3f2c0faebb` | 10 | Pages 1–9 image-only; page 10 native typography |
| `90e7b47716c3` | 6 | Native typography difference |
| `b9a64bf99e4b` | 4 | PDF unavailable in this mode; retained #533 outcome |
| `d6a23a9cfd0f` | 5 | Native typography difference |
| `e1b17805a87f` | 6 | Pages 1–5 native typography; page 6 image-only |

The totals are 21 native pages with width differences, 25 equal-size native
pages with typography differences, ten image-only raster cases and four
unavailable PDF observations. Every available fresh PDF crop equals its
historical PDF crop. Fresh complete source/repeat sessions for the two main
named documents equal the historical source crops on all 17 pages. Other
source comparisons retain the audit's exact cold repeats; unavailable PDF
observations are not silently replaced by another recipe. #533 separately
confirms all four pages in continuous mode and with an explicit ornament font.

The English running title and equation-number collisions on `0377…` pages 1/2,
and the title/abstract/heading changes on `166d…` page 1, therefore persist on
current code. Original headers that already overlap are not newly attributed
to the converter. Image-only pages are excluded from font-based explanations.

## Resource and glyph identity

Reuse the [public resource observation work](native-font-observation-20261009.md)
and [opened-resource identities](opened-font-resources-20261009.md) under
[samples #106](https://github.com/rwv/caj2pdf-samples/issues/106), which stays open.
Those Linux observations identify HGBZ/HGHZ/HGBX/HGB1/HGB1X for measured Latin
states, plus distinct source glyph slots. Their finite state/resource scope is
not automatically a Wine or full-repertoire result.

New Wine controls use original generated HGBZ fonts with **only one candidate
native alias at a time** for the authored `A`, `M`, `1` positions. Keeping all
native aliases but deleting ordinary Unicode leaves the original crop unchanged;
keeping only ordinary Unicode makes the three marks disappear. The isolated
slots identify which authored position survives. This verifies the following
finite Wine mapping without guessing aliases from appearance:

| Authored raw code | Semantic text | HGBZ cmap argument | External resource GID |
| --- | --- | ---: | ---: |
| `a0c1` | A | 31908 | 4851 |
| `a0cd` | M | 37213 | 6485 |
| `a0b1` | 1 | 25969 | 2578 |

The external `HGBZ_CNKI.ttf` hash is
`c44abe24684e5c0ea849b43116dc97a97d2eeda5b36eb33d490090f7d0723758`,
2,048 units/em. Resource inspection exports only metrics/bounds/outline hashes.
Native `A` and `M` aliases have the same outlines/advances as their ordinary
Unicode slots in this file. Native `1` does **not**: its advance is 2,048 rather
than 1,024, and its outline bounds are `(664,288,1428,1672)` rather than ordinary
U+0031's `(216,0,792,1368)`. Selecting plain Unicode from that same file would
still choose the wrong digit. The aliases are lookup keys; semantic text stays
`A`, `M`, `1`, never those unrelated Unicode characters.

FreeSerif's normalized A/M advances are 0.721/0.881 em, compared with the source
resource's approximately 0.667/0.778 em, and their ink bounds also differ.
These are resource-width differences, not evidence of accumulated PDF pen drift.
Each emitted glyph uses its own text matrix. Original controls below specifically
separate advance-only changes from actual painted geometry.

For equation parentheses, both FreeSerif **and HGBZ lack ordinary U+FF08/U+FF09**.
The actual `0377…` page-2 PDF selects the Noto CJK resource for all 16 opening
and 16 closing fullwidth parentheses; the same fallback appears on page 1.
The original-control Wine parentheses select the HGBZ marker resource instead.
Thus ordinary Unicode coverage/fallback chooses a different resource for these
marks. Their exact native aliases in real formula contexts remain unmeasured;
changing the Latin font filename alone is insufficient, and replacing semantic
fullwidth parentheses with ASCII would silently change extracted text.

## Identical-outline controls separate placement from font choice

[`wine_typography_controls.py`](../cajviewer/wine_typography_controls.py)
authors two rows containing a Han marker, A/M/digits and fullwidth parentheses,
with fixed source x/y coordinates. Four styles are tested: `1084`, `10a5`, `0884`
and `1063`, all in the measured `801d/0`, `8067/6` context. Generated HGBZ/HGHT/HGHZ
fonts contain original geometric markers; no external glyph outline is copied.
The same generated resources are supplied to the converter and replaced in each
isolated Wine prefix. A complete-page numeric gate and two captures apply.

At 75%, all four source cold repeats are exact. Source/PDF crops still differ
by 402/782/402/416 pixels. The Latin/bracket markers identify the common resource;
the Han mark does **not** become the expected HGHT marker. That CJK resource
hypothesis is explicitly unconfirmed in Wine and supplies no same-font CJK proof.
Changing `1084` to `0884` changes that source Han mark while the supplied single
CJK font does not reproduce its style. Font/style selection is therefore a
separate unresolved requirement from Latin geometry.

The same four controls use a smaller declared canvas for predeclared 100%/200%
complete-page observations. At 200%, Latin marker widths/heights agree for the
tested styles, but positions can differ by several pixels. For example, baseline
first-row A/M/1 marker x origins are 162/252/341 in the source and 162/253/343 in
the PDF; the digit baseline also differs by two pixels. These are original
marker bounds in page pixels, not fitted correction constants. Some small-size
differences change with zoom, so a 75% bounding box alone does not justify a
physical-size correction. No per-character/page offset is added to production.
At 100%/200%, the individual Latin/bracket mark crops are identical across
source/PDF without resizing; their different page positions remain part of the
full-page difference. The failed Han-marker hypothesis is excluded from that
glyph-identity statement.

A further control doubles **only HGBZ advances**, keeping every outline, bearing
and cmap unchanged. Both the Wine source crop and its PDF crop remain exactly
equal to their respective originals at 200%. This separates accumulated advance
from the observed fixed-position differences. It does not prove what CAJViewer
uses internally for native glyph centering/baselines, or validate every style,
axis, mode, cached draw, fraction, superscript or equation operator.

All **nine** normal/compact/advance-only PDFs match across native, Node and real
Chromium, with source/font hashes stable and empty browser OPFS after cleanup.
That validates transport/resource preservation; it does not turn the Wine
source/PDF differences into fidelity passes. The controls do not introduce a
new production API, parser admission or font dependency.

## Concrete remaining requirements

1. Ordinary Latin/digit/bracket fidelity needs the correct external resource
   **and native glyph slots**, keyed by measured raw code and resource/state.
   Current HN-B mode-0 symbol options do not supply general C8 ordinary mappings.
   A Unicode-covered substitute or same family name cannot establish parity.
2. CJK titles, abstracts and body text need measured per-state resource/style
   selection. The current one-CJK-font recipe cannot reconstruct several original
   styles, and the attempted HGHT marker is unconfirmed in this Wine context.
3. The remaining same-outline Latin/bracket x/baseline and size-rounding behavior
   needs a Wine-specific positioning explanation and independent held-out cases.
   Original-marker and doubled-advance results rule out an all-font or accumulated
   advance explanation. Exact resource aliases do not by themselves solve it.
4. Formula brackets, symbols, superscripts and vector painting must preserve
   semantic Unicode separately from their resource/glyph/geometry. The three
   verified aliases and existing 21 mode-0 symbols do not cover all those contexts.

These obligations remain under samples #106 and the open Rust #406/#441 fidelity
work; no complete source-font or layout conclusion is asserted. This investigation
documents the resources and unmeasured mappings permitted by #531's acceptance
criteria. It must not be summarized as “install fonts and the spacing is fixed.”

All generated source/font controls reproduce their observed bytes. Two original
tests use the independent source parser to check two-row semantic order and
geometry across canvases/styles, and verify that cmap-only/advance-only mutations
preserve the authored outlines. Both pass with zero skips. An initial test
incorrectly expected ASCII parentheses; the preserved source codes decode to
fullwidth parentheses, and the assertion was corrected without changing source
or converter semantics. Low fixed font timestamps produce retained warnings.

All committed source is original MIT work. No vendor/private HN/JBIG or foreign
converter implementation was inspected/copied. External source documents,
fonts, outlines, derived PDFs and rendered pixels remain external. The catalog
is unchanged. Required review/CI applies; no production behavior or release
change, arbitrary-font parity or native-Windows equivalence is claimed.
