# Incomplete PDF content tokens, 2026-10-09

The seven originals in [Rust #499](https://github.com/rwv/caj2pdf-rust/issues/499)
contain 11 unfinished hexadecimal string operands. The surviving bytes do not
uniquely specify the missing text. Two explicit diagnostic completions for each
stream pass qpdf but produce different text traces; five pairs also produce
different pixels in both independent renderers. This is evidence against a
unique automatic repair, not proof that no intact original can be found.

This follows [samples #99](https://github.com/rwv/caj2pdf-samples/issues/99).
The [receipt](content-eof-ambiguity-20261009.json) records all 11 boundaries,
resource identities, diagnostic hashes, independent checks, repeated-content
searches and scoped viewer observations. Catalog counts and converter behavior
remain unchanged. The seven conversion passes retain their source warnings;
complete text recovery and broader fidelity remain unresolved.

## Exact lexical scope

The [original bounded observer](../scripts/pdf_incomplete_hex.py) distinguishes
comments, escaped/nested literal strings, names, arrays, dictionaries and hex
strings. It refuses inline images and unmeasured or malformed constructs rather
than treating arbitrary trailing bytes as text. Input is limited to 1 MiB and
nesting to 256. It is a research lexer, not a complete PDF validator or repair.

All 11 measured EOFs are top-level hex operands inside one open text object
and one saved graphics state, with exactly two trailing whitespace bytes
(CRLF). No text-show operator follows them. The [earlier framing checks](public-web-correctness-20261009.md)
established complete Flate/checksum framing, exact stream lengths, and one
content stream per affected page. Neither a next content-array member nor
extra compressed bytes supply a continuation.

| Source SHA-256 prefix | Page | Object | Surviving hex digits | A/B different pixels, MuPDF / Poppler |
| --- | ---: | ---: | ---: | ---: |
| `10a3bf259d47` | 3 | 24 | 2 | 0 / 0 |
| `14cfdbc3d826` | 6 | 78 | 2 | 5 / 5 |
| `14cfdbc3d826` | 7 | 79 | 0 | 64 / 62 |
| `275f836ce276` | 2 | 48 | 4 | 58 / 58 |
| `275f836ce276` | 4 | 50 | 4 | 0 / 0 |
| `275f836ce276` | 6 | 52 | 4 | 62 / 62 |
| `86366e9a0c17` | 6 | 46 | 0 | 6 / 6 |
| `866cab1d8d00` | 6 | 28 | 2 | 0 / 0 |
| `defdf17b6e2e` | 7 | 53 | 1 | 0 / 0 |
| `defdf17b6e2e` | 9 | 55 | 4 | 0 / 0 |
| `f260112bcd69` | 6 | 41 | 0 | 0 / 0 |

The repeated-content probe compares at most 4,096 suffix bytes against other
page streams in each same source. The three `275f836ce276` endings share 414
bytes, but every copy stops at the same missing suffix. Other matches are
shorter generic content fragments (32–135 bytes), sometimes with different
font resource identities; they are not missing-text evidence. No unique
restoration was recovered from this finite comparison.

## Diagnostic alternatives and independent checks

For each affected page, an extracted baseline retains the exact decoded
content and page resources. Its 72-dpi RGB pixels equal the corresponding
unchanged original page separately in MuPDF and Poppler. All 11 baselines
retain qpdf exit 3. The diagnostic `omitted` variant removes only the unfinished
operand and closes the open text/graphics state. All 11 are qpdf-clean and
pixel-identical to the baseline in both renderers; MuPDF word geometry also
matches. This describes observed error handling, not an acceptable repair.

For alternatives A and B, the entire malformed decoded stream, including its
CRLF, remains an exact prefix. A appends zero digits to a two-nibble unit
(four for the measured Type0 font), then closes the operand, shows it, and
closes the open states. B inserts one additional previously occurring nonzero
text operand for the same active font before the closure. The first distinct
prior operand of at most eight bytes is selected before rendering. It is a
counterexample, not a guess at the author's intended missing text.

All 22 alternatives are qpdf-clean, and every B has one more MuPDF text-trace
glyph than A. The table gives exact same-renderer pixel differences at 72 dpi;
no cross-renderer equality is asserted. Five zero-pixel pairs have explicit
`3 Tr` and ignored-text traces. The remaining zero-pixel pair is object 50;
its added glyph has abnormal measured width, so no visual distinction is
claimed there. Font-substitution warnings remain recorded, and text traces
do not establish correct font outlines or recovered text.

The [wholly authored generator](../cajviewer/pdf_incomplete_hex_controls.py)
produces 16 small PDF controls (13 unique identities): 0/1/2/4 hex digits,
each with broken, omitted, A and B endings. Their common visible text and
rectangle precede the unfinished operand; Helvetica is a Standard 14 reference,
not an imported font program. Independent qpdf, MuPDF and Poppler checks show
broken/omitted pixel equality and visible A/B differences for every digit count.
All generated PDFs remain outside Git.

## Offline viewer observations

There are 35 completed sessions and 39 page observations: seven unchanged
originals / 11 affected pages, 13 unique original controls, 11 omitted
one-page derivatives, and four focused context observations. Every selected
page yields two equal cached captures; input hashes and container cleanup
are confirmed for every session. For each control digit count, broken and
omitted pixels agree while A and B visibly differ.

Nine original/omitted page pairs agree exactly. The initial original page 7
of `14cfdbc3d826` and page 6 of `275f836ce276` instead differ by 30,393 and
25,742 pixels respectively. These were reached after other affected pages
in their initial sessions. The two extracted **unchanged-content baselines**
agree exactly with their omitted counterparts, so the observed discrepancy
does not require deleting the unfinished operand.

A new process visiting only each target page in the unchanged original also
agrees exactly with its extracted baseline and omitted counterpart. The
initial different observations remain in the receipt; they are not replaced
by the later matches. This establishes a session/route-dependent observation
boundary, not its cause. Navigation order, reader resource state and timing
are not isolated by this small follow-up. In particular, repeated cached
captures alone are insufficient as a fidelity oracle.

The opaque image is pinned to
`sha256:cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de`.
The viewer runs offline as UID 1000 with read-only root/input, dropped
capabilities, no new privileges, 2 GiB memory/swap, two CPUs, 256 PIDs,
bounded temporary storage, a 600-second case lifetime and action timeouts.
The original Qt public-API observer selects a complete current-page pixmap
after page/150%-zoom verification, then records it twice two seconds apart.
No document font programs are inspected or replaced. Captures and derived
PDFs remain external. Repeated cached pixels do not prove render completion;
[Rust #441](https://github.com/rwv/caj2pdf-rust/issues/441) remains open.

## Reproduction, provenance and remaining criteria

From the samples checkout, with qpdf, Poppler, pikepdf, PyMuPDF and Pillow:

```sh
python3 research/cajviewer/pdf_incomplete_hex_controls.py /external/new-controls
python3 -m unittest discover -s research/conformance -p 'test_pdf_incomplete_hex.py' -v
python3 tools/check_catalog.py
python3 -m unittest discover -s tests -v
```

Five original-control tests cover lexical boundaries, malformed/inline-image
refusals, allocation/nesting limits, non-overwrite behavior, identical surviving
prefixes, independent parser acceptance and discriminating text/raster results.
CI runs them without a corpus download or proprietary viewer. The receipt pins
external source-specific drivers, their inputs/results and the viewer adapter;
the adapter retains the existing current-page observer and adds PDF page-box,
rotation, page-count and route checks. Source-specific observations are opt-in
external evidence, not tests silently skipped into compatibility passes.

All new code and controls were independently authored under MIT. Format facts
come from the acquired original bytes, existing project-owned tools and opaque
PDF/viewer observations; no foreign converter or proprietary implementation was
read or copied. Existing third-party tools are research executables, not copied
source. Document provenance remains in the catalog and original acquisition
report. No documents, decoded text, font programs, screenshots or diagnostic
PDFs are committed.

Rust #499 remains open: this establishes the measured lexical/error-treatment
boundary and non-unique completions, but neither an intact alternate nor the
intended missing content. Its conditional product-repair/runtime criterion is
not exercised because no justified product repair was found. Existing
native/Node/Chromium byte-preservation evidence remains the earlier checkpoint;
this follow-up does not claim a new runtime or full-catalog conversion run.
