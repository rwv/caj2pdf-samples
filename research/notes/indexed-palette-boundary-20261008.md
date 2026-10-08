<!-- SPDX-License-Identifier: MIT -->

# Indexed palettes: syntax repair is not color recovery

[Rust #420](https://github.com/rwv/caj2pdf-rust/issues/420), under
[#406](https://github.com/rwv/caj2pdf-rust/issues/406), remains unresolved.
The unchanged 80-page CAJ original has missing palette components as well as
malformed PDF strings. Two syntactic substitutions permit conversion, but
they change the original viewer's appearance. There is no production repair
or new compatibility pass in this investigation.

The [measurement receipt](indexed-palette-boundary-20261008.json) identifies
the pinned CAJSamples `issue-39` source, SHA-256
`5e1ea482a56a2df02a2a452ac97949824c726471c88157e78441a1201b3d8697`,
2,623,476 bytes, and the external diagnostic hashes. All document, PDF,
palette, font, image and vendor executable bytes remain outside Git.

## Complete inventory and actual use

The source PDF body `[39796, 2623476)` contains 1,525 unique measured
generation-zero object headers and 110 Indexed color spaces: 70 DeviceCMYK
and 40 ICCBased. The lookup forms are 68 literals, 41 hexadecimal strings
and one Flate stream. All four ICC base profiles have three RGB components
and identical 13,572-byte decoded profile hashes. Lookup stream 445 has the
expected 438 decoded bytes for palette 446.

The [Adobe PDF reference](https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/pdfreference1.7old.pdf)
requires `components * (hival + 1)` lookup bytes. Its literal-string rules
also distinguish raw bytes from decoded bytes; hexadecimal encoding of an
apparent raw span is not necessarily preservation of its interpreted value.

| Profile | Measured bytes | Actual use |
| --- | --- | --- |
| 64 short CMYK lookups | 61 have 3 raw bytes, one has 2, two have 1 | All 64 are used on page 24, through Form 386 |
| Palette 320, CMYK hival 43 | 3 raw bytes instead of 176; final backslash escapes the apparent terminator | 28 × 25 image uses every index 0–43 |
| Palette 397, RGB hival 220 | 663 raw bytes but 661 decoded bytes; backslashes at raw offsets 51 and 84 introduce unknown escapes and are discarded | Page 25, Form 409; 47 × 46 image uses every index 0–220 |
| Palette 471, RGB hival 235 | 708 apparent raw bytes; the first unescaped closing parenthesis ends an 18-byte prefix, leaving invalid array tokens | Page 27, Form 513; 40 × 52 image uses every index 0–235 |

Incoming references are recorded for every palette. qpdf 12.2.0 externalizes
inline images in the two-object diagnostic; an original lexer then follows
executed `Do`, color-space and pattern operators through all 80 pages, Forms
and tiling patterns. This finds 137 content visits, 162 Indexed image objects
and **109 used palettes**, on pages 24, 25, 27 and 31. Palette 482 is present
in Form 513's resource dictionary but has no observed executed use. Annotation
appearances and optional-content state interpretation are outside this trace.
Every affected short/malformed palette above has a measured content path.

The earlier direct bounded zlib probe frames all 322 inline images in Form
386. Its 123 unpredicted Indexed image payloads agree with the later qpdf
inventory. Form 513 has 70 inline images, including 31 CCITT masks; the
earlier Flate-only probe correctly failed there. The complete inventory uses
qpdf framing and never treats those masks as Flate or palette indices.

## Source viewer and deliberate controls

Ten fresh offline CAJViewer 9.0.0 sessions compare the unchanged original,
verbatim-body PDF framing and deliberately modified controls on pages 24,
25 and 27. Six more sessions open original synthetic palette grids. Every
session opens one document, has two stable captures, preserves input hashes,
avoids OOM and removes its container. Active filename, page, zoom and complete
page edges were visually checked. Vendor code was not inspected or instrumented.
Tool agreement does not establish implementation independence.

Containment is pinned in the receipt: cached image
`cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de`,
offline/read-only/non-root, dropped capabilities, no new privileges, 2 GiB
memory/swap, two CPUs, 256 PIDs, bounded temporary storage and a 90-second
external deadline. Each session peaks below 595 MB.

The synthetic grid has 236 independently generated grayscale triplets and
240 image indices on a 200 × 200 point page. An unescaped literal closes after
six entries. Complete hexadecimal, short-prefix, zero-padded-prefix, empty
and all-zero lookups distinguish observable policies without copying source
palette bytes. At 100% zoom, the malformed, short-prefix and empty controls
all leave the grid white in CAJViewer. Complete and padded tables paint
different visible grids. Poppler likewise rejects the short tables with
warnings. MuPDF instead renders its short-prefix control identically to the
zero-padded control, and its empty control identically to the zero table.
MuPDF exits 1 on the malformed control; its emitted blank image is not a pass.

Original/control full-page crops use `[626,156,1023,718]` at 50%, without
alignment or rescaling:

| Source page | Comparison with unchanged original | Differing pixels / RGB channels |
| --- | --- | ---: |
| 24 | Verbatim framing; palette 320's three raw bytes encoded as hex | 0 / 0 |
| 25 | Verbatim framing | 0 / 0 |
| 25 | Palette 397's full 663 raw bytes encoded as hex | 78 / 219 |
| 27 | Verbatim framing | 0 / 0 |
| 27 | Palette 471's full 708 raw bytes encoded as hex | 29 / 85 |
| 27 | Only palette 471's first 18-byte literal prefix selected | 0 / 0 |

These distinguish observed omission of image content from recovery of its
missing colors. Retaining the prefix reproduces one viewer's tolerance, but
discards the effective use of later raw bytes and leaves a short table with
different behavior in other renderers. It is a diagnostic, not a proposed
portable normalization. Raw-to-hex of palette 397 also changes appearance
despite the original literal being syntactically complete.

## Whole-document diagnostics and limits

Independent framing copies the original body verbatim, adds explicit xrefs,
four absent Pages ancestors and a new Pages root/Catalog. Original
Parent/Kids relationships and the CAJ page table determine all 80 page IDs
and their order. The first framing omitted Parent links on the four
synthetic ancestors: qpdf and viewers tolerated that, but the converter's
ordinary-PDF validation rejected it. Version 2 adds only those four synthetic
links; the source body remains unchanged. Previous viewer receipts retain
their original framing hashes; the full-page comparison uses version 2.

A mutated CAJ diagnostic changes only the literals in 320/471 to raw-byte
hexadecimal and adjusts shifted page-row extents. The existing converter
then exits 0 and qpdf passes. This exposes no further whole-converter blocker,
but **is not conversion of the unchanged original**. Its other container
offsets were not rederived, so it is not a CAJViewer source reference.

The 80-page comparison retains all **615 original raw stream payloads**, page
IDs and effective geometry. A separate CAJ bookmark decoder agrees with all
**72 output bookmarks**, including hierarchy and destinations. At RGB72,
Poppler's source framing equals the prefix diagnostic on 80/80 pages, and the
raw-to-hex diagnostic output on 79/80; page 27 differs by 243 RGB channels.
Warnings remain on the original and short-table controls. MuPDF text extraction
matches on 79/80 pages: malformed source palette 471 interrupts its Form
parsing, while the diagnostics yield 38 additional text characters on page 27.
No complete text-extraction agreement is claimed.

The unchanged original still fails strict conversion without publishing a
PDF. Explicit `--allow-damaged` exits 3, emits an 80-page qpdf-readable PDF and
blanks pages **24, 25, 27 and 31**. That is partial recovery, not a successful
compatibility result. The observed shared resource dependencies are retained
in the receipt; the reason for each partial-mode propagation edge has not
been separately verified.

The missing CMYK components cannot be supplied by escaping strings. No
evidence currently identifies their intended values or an intact alternative
palette/document. This is a concrete unresolved source-data boundary, not
proof that every possible reconstruction is impossible. Runtime parity and a
full native regression for a production fix are **NOT_RUN**, because no
evidence-supported fix is proposed. Existing corpus totals are unchanged.

## Review and provenance

This is original MIT measurement/reporting work based on public PDF syntax,
unchanged source observations, independently authored controls and external
tool behavior. No Python/Go converter, private HN/JBIG implementation or
vendor implementation was copied, translated or inspected. No dependency,
production code, public API, output policy or support claim changes.

Self-review checks every count against the receipt and retains nonzero exits,
warnings and missing scopes. Initial exploratory assumptions about predictor
absence, Flate-only inline images and universal renderer success failed closed;
they are not passing checks. The source-framing Parent omission is corrected
only in a separately hashed version. Review is self-review, not independent
approval. Rust #420 stays open for an evidence-supported recovery policy.
