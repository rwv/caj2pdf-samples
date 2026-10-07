# HN-B magnesium article profile (#381)

This checkpoint addresses [caj2pdf-rust#381](https://github.com/rwv/caj2pdf-rust/issues/381),
independently of the missing-outline investigation #303. It uses the unchanged
12-page `tests/hn_src.caj` in `zombie110year/caj2pdf-restructured` at
`d34eaf586b40e21989ea9308e9afd2fd5e23e216`: 163,779 bytes, SHA-256
`166d0014792326570d9e8ca42fe13a4a44329e4ad095d3ac8dfd73c8ddb9f20e`.
The original, PDFs, rasterizations, screenshots and fonts stay outside Git.
The [metadata-only receipt](hnb-magnesium-evidence.json) records the measurements.

## Independent controls and provenance

The original MIT [control generator](../cajviewer/hnb381_controls.py) authors
new native records using existing MIT synthetic wrappers. It does not read
source documents. The [bilevel generator](../examples/hnb381_type3.rs) uses only
the Rust project's original arithmetic encoder and five-segment fixtures,
with its already-audited built-in MQ states. No decoder algorithm or numeric
state table is introduced by this work. No Python/Go converter, vendor
implementation, private module or external font outline was copied.

Run the Rust generator as an example in a **temporary current Rust worktree**,
then pass its external output directory to the Python generator:

```sh
cp /path/to/caj2pdf-samples/research/examples/hnb381_type3.rs crates/caj2pdf-core/examples/
cargo run --locked -p caj2pdf-core --example hnb381_type3 -- /external/new-payloads
python3 /path/to/caj2pdf-samples/research/cajviewer/hnb381_controls.py \
  /external/new-controls --bilevel-dir /external/new-payloads
```

The five 32x24 payloads and 21 image/order controls were independently regenerated
byte for byte. The geometric marker fonts are the project's original full-em
rectangles with a white hole identifying the selected resource. HGBX is a renamed
copy of the original alternate marker font, not a vendor font migration.
CAJViewer Linux 9 ran in a network-disabled, read-only container based on image
`cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de`.
An original, external-only FreeType interposer observed public cmap/load calls;
it did not extract outlines or inspect vendor implementation code.

Rejected evidence is excluded: an early image generator retained one byte of
old MQ data after the generic header, yielding noise. The corrected generic
header has exactly 20 bytes. Old `bi-*` captures are invalid; only the reproduced
`bi2-*` suite supports the image rule. Initial captures with stale page navigation
or an unreplaced HGBX font were repeated before measuring resource state.

## Observed rules

- Size field 9: `0929` equals `1129`; nominal size 72, Latin offset -1 in the
  existing empirical point model. `1000` has the existing C8 square size 21
  and Latin offset 11. Unmeasured rectangular zero-field HN-B forms remain errors.
- Style `1021` square brackets match paired C8 controls exactly in the viewer:
  x offset 21 and downward y offset 3 source units. Other newly unverified
  small punctuation styles are not admitted by this result.
- `8067/18` preserves resources. Independently varied `8072`, `8073`, `8074`
  value words preserve glyph state, including zero, observed page-number
  values, extremes, and record-marker-like values. These remain atomic four-byte
  records; this finding does not admit new opcodes or mode-0 records.
- `a1b4/a1b5/a1c0/a1c1/a1c3/a1e4/a2f2/a6b8/a6c4/a6cc/a6d2`
  retain the current Latin resource, CJK x origin and ordinary symbol baseline.
  `a1d6/a1dd` reset to the ordinary Latin resource, including the following letter.
  Single-symbol and following-letter controls distinguish this persistent reset
  from an atlas affected by an earlier symbol.
- `a6c2` (beta) at style `10a5` matches a comma shifted downward by 25 source
  units: the isolated first-glyph crop is identical. State 0 and state 3 agree.
  Only this measured beta style is admitted; other sizes remain unsupported.
- The first image selects the persistent HN-B raster operation. If text precedes
  it, black pixels cover and white pixels preserve earlier content. If the page
  begins with an image, later images replace prior content, including after
  intervening text. Controls use white, black, left, top and checker patterns;
  `TA`, `AT`, `TAB`, `TBA`, `ATB`, `ABT`, `TATB` distinguish ordering and persistence.
  All ten compared stable-interior masks have zero differences from the rule.
  Full-image differences remain on antialiased edges (not a pixel-parity claim).
  The PDF writer uses Multiply only for verified 1-bit resources. Colored/JPEG
  images after text and all mode-0 images remain rejected.

PDF Multiply is grounded in Adobe PDF Reference 1.7 §7.2.4/Table 7.2,
not in a viewer implementation. For binary source samples it gives the observed
black-cover/white-preserve behavior. Replacement text uses §10.8.3 and UTF-16BE
text strings (§3.8.1). The [specification archive](https://pdfa.org/resource/pdf-specification-archive/)
links the primary document; the stale Adobe-hosted URLs returned 404 during this
run, so the same Adobe-authored specification was read from a
[PDF mirror](https://zxyle.github.io/PDF-Explained/resources/pdf_reference_1.7.pdf).
No specification text is included in source code.

## Private code A661: preserve identity and disclose approximation

At page 10, byte 129455, raw `a661` maps to private-use `U+E6C7` under the
existing GB18030 table. The ordinary viewer paints an acute-accented Gamma-like
shape; an isolated control's Copy operation returns a bullet. Its public font
API requests the obfuscated HGBZ cmap entry U+6A83, which does not establish a
semantic Unicode identity. See the [Unicode GB18030 FAQ](https://www.unicode.org/L2/L2001/01314-FAQ-GB18030.htm)
for private-use mappings; private-use is not permission to infer an author's name.

The converter retains U+E6C7. A supplied Latin font containing that code is used
directly. Otherwise it draws the caller font's U+0403 glyph as an explicitly
reported **visual approximation**, while a Span's ActualText remains U+E6C7.
This does **not** assert that A661 means U+0403 or infer `ü` from surrounding text.
If neither glyph is available, conversion fails. The CLI warns, and Rust/JS
reports expose the substitution count. General private-use decoding remains
rejected; the character-only helper still returns None for A661.

Poppler extraction from the complete PDF contains one U+E6C7 and no U+0403.
Extractors that ignore ActualText can expose the display alias; no tagged-PDF,
PDF/UA, original-font or semantic-identification claim is made.

## Complete conversion and scoped fidelity

With NotoSerifCJK-Regular.ttc face 2 and FreeSerif.ttf, CLI, Node and a real
Chromium Worker each convert 12 pages with one reported visual substitution.
All outputs are 726,141 bytes, SHA-256
`24cddad85ed48f6af74eec6c5dadfb18d95e6a9ecf31c22d3ef127e60564981b`.
qpdf finds no syntax/stream errors. Per-page glyph counts retain all 20,693
native glyph records; all 12 type-3 images are drawn. Three image draws use the
text-first overlay operation. Node/browser maximum output chunks are 16,384
bytes; this is an I/O observation, not a peak-memory measurement. Browser OPFS
has no remaining entries after cleanup.

Selected original pages 1, 2, 9 and 10 were inspected against the rendered PDF:
title/columns, the three page-2 charts, page-9 curves and page-10 reference
placement agree at this scope. Original marker controls for field 9, zero size,
beta, small brackets and A661 have PDF/viewer bounds within 3 pixels at about
1241% viewer zoom. Font weight, Latin spacing, fullwidth punctuation shape and
some overlaps differ with the substitute fonts. This is not full-document
pixel parity or an independently verified Unicode identity for the private code.

Rust regression tests exercise resource resets, metadata values and truncation,
private-glyph retention/missing-font failures, type-3 admission, malformed DIBs,
paint order, PDF resources, and failure poisoning. Original Node and Chromium
controls verify the new profile and substitution report. Full locked native
checks and 158 JS tests pass locally. Required PR gates are recorded by the
implementation PR. The optional external full-corpus suite is **NOT_RUN**, not
counted as compatibility success. This single document does not resolve #303:
its contents panel remains empty and stored HN-B/C8 outlines remain unverified.
