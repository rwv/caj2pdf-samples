# Font-free viewer raster controls (2026-10-09)

An independently authored PDF with no fonts or text operators reproduces two
CAJViewer page-buffer variants: **3,655 pixels differ**, with channel deltas
of -1 through +1. The complete displayed page differs at **6,037 pixels**.
Two subsequent sessions without an observer reproduce both displayed variants
exactly. Fonts and text operators therefore are not required for this observed
variation. Its internal cause and a reliable comparison-readiness criterion
remain unknown under [Rust #441](https://github.com/rwv/caj2pdf-rust/issues/441).

This completes the scoped discriminator in [samples #68](https://github.com/rwv/caj2pdf-samples/issues/68).
The [metadata receipt](viewer-raster-stages-20261009.json) retains all ten
sessions, including the first baseline session's abort. None was replaced or
retried. There is no converter run, corpus compatibility pass or release here.

## Original controls and fixed protocol

[`pdf_raster_stage_controls.py`](../cajviewer/pdf_raster_stage_controls.py)
writes a fixed six-page PDF 1.7 below 160 KiB. Its SHA-256 is
`ec76ddfc28489b701947de36c47348d3309fe654f12f976963f083c6d03a3a2b`.
All pages have the same A4 box and an original page-marker count. Pages 1, 5
and 6 additionally contain four independently authored panels:

- 256 solid DeviceGray rectangles, with values from 0 through 1.
- 256 filled triangles with fractional coordinates and a fixed gray value.
- An opaque 256×16, 8-bit DeviceGray ramp image.
- A black DeviceRGB image with an 8-bit DeviceGray ramp as its soft mask.

Both images disable interpolation; the soft mask has no Matte entry. No
external document, font, raster, viewer implementation or font outline is
read by the generator. The existing six-page Standard-14 Helvetica/ASCII
control provides a contemporaneous baseline; its identity is unchanged at
`164f598498d6d722aaf243592d7535d73f0b628818dba05a65c64b3d2c3921e8`.
Its font reference is separate from the new font-free fixture.

The initial plan freezes eight fresh sessions in the order below, before
launching any. The two-session no-observer extension was separately frozen
after the first eight, to test whether both screenshot variants also occur
without the observer. It does not replace the failed first bracket.

| Session | Original control | Route | Outcome |
| --- | --- | --- | --- |
| 01 | Standard-14 baseline | 5 | NOT_CONFIRMED: application aborted |
| 02 | Font-free | 5 | Buffer variant A |
| 03 | Font-free | 3→5 | Buffer variant B |
| 04 | Standard-14 baseline | 3→5 | Baseline variant B |
| 05 | Standard-14 baseline | 3→5 | Baseline variant B |
| 06 | Font-free | 3→5 | Buffer variant B |
| 07 | Font-free | 5 | Buffer variant A |
| 08 | Standard-14 baseline | 5 | Baseline variant A |
| 09, no observer | Font-free | 5 | Display bytes equal to sessions 02/07 |
| 10, no observer | Font-free | 3→5 | Display bytes equal to sessions 03/06 |

The desktop is 1600×1200 at 96 dpi, maximized, with 50% zoom and target page
5 of 6. Startup waits five seconds plus two after maximization; zoom waits
two seconds. Each route step waits three seconds before capture, then one
second before a second capture. Page/zoom field OCR, full-page placement,
source hashes, logs and cleanup are checked. The nine confirmed sessions have
identical consecutive screenshots within each session. This is an observation,
not a general readiness test. Earlier original native repetitions already
showed that route alone does not determine the raster variant.

Session 01 has black full-frame captures and ordinary application diagnostics
`free(): invalid pointer`, `realloc(): invalid pointer`, and `Aborted`. Its
container remained alive because desktop processes survived; container liveness
is not application success. No OOM occurred, the source was intact and cleanup
completed. The cause is unestablished. All three pair comparisons involving
that session remain NOT_COMPARABLE.

All ten sessions use image
`sha256:cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de`,
network none, read-only root/input, uid 1000, dropped capabilities,
no-new-privileges, 2 GiB memory/swap, two CPUs, 256 PIDs, bounded tmpfs/file
sizes and a 90-second container lifetime. Every input remains unchanged;
all containers are removed. Raw logs, commands, timing records, images and
binaries remain outside Git and have identities in the receipt.

## Exact measurements and scope

Seven instrumented sessions have a selected 397×561 page-5 display pixmap
whose RGB digest matches a public `QImage` constructor observation. Target
and source rectangles and the Qt transform are equal across these sessions;
the following page is excluded. The prototype observer binary is pinned at
`1cfcddaa7d469caac728b4c25e93658146206896d7735f891e5ccea26c4747ea`.
This is the earlier prototype from the [buffer report](viewer-page-buffer-20261009.md),
not a rerun of that report's later finalized source. The two no-observer
sessions have neither an observer mount nor `LD_PRELOAD`, and produce no buffer
or paint trace. Their full-page screenshot hashes match the two instrumented
font-free groups exactly; the observer is not required for these differences.
That does not prove the observer has no timing impact or explain session 01.

All six font-free pair comparisons and all three confirmed baseline pairs
are measured. Equal-variant comparisons are identical. Every font-free
cross-variant comparison changes the same 3,655 buffer pixels. The four
source-coordinate panel boxes were declared before launch; projecting them
with fixed floor/ceiling arithmetic, without fitted alignment, gives:

| Font-free region | Changed buffer pixels |
| --- | ---: |
| Solid gray cells | 2,043 |
| Fractional vector edges | 1,399 |
| Opaque gray image | 28 |
| Black image with soft mask | 45 |
| Outside the four panels | 140 |
| Entire buffer | 3,655 |

These are descriptive projected regions, not a claim about internal rendering
stages or exact geometric registration. The 397×562 displayed crop is a
separate measurement: Qt applies a small transform, so its 6,037-pixel
count must not be substituted for the buffer count. The contemporaneous
baseline gives the previously observed 8,254-buffer/21,073-display difference.

A separate exact grayscale contingency check tests whether one
coordinate-independent lookup could map each unchanged input raster to its
other variant. It counts every ordered grayscale pair, including unchanged
pixels. A single input gray with multiple output values rejects that limited
hypothesis. The retained earlier native pair has 112 such input values, and
the earlier PDF pair has 47. The new font-free pair has all 256. The final
bounded tool independently reproduces all prior counts and all nine measured
current buffer comparisons. No lookup is fitted or applied; this does not
rule out spatial, primitive-specific or earlier-stage effects and does not
identify a renderer mechanism.

## Validation, reproduction and provenance

```sh
python3 research/cajviewer/pdf_raster_stage_controls.py /external/new-raster-controls
python3 -m unittest discover -s research/conformance -p 'test_pdf_raster_stage_controls.py' -v
python3 -m unittest discover -s research/conformance -p 'test_raster_gray_comparison.py' -v
python3 research/scripts/raster_gray_comparison.py /external/first.png /external/second.png \
  --first-sha256 FIRST_PINNED_SHA256 --second-sha256 SECOND_PINNED_SHA256
```

Three independent fixture tests pass: qpdf/pikepdf graph, page-box, operator,
resource and exact image/mask checks, plus bounded generation and existing-file
preservation. Four comparison tests pass: equality and many-to-one mapping,
conflicting targets, shape/type/color rejection, and pinned PNG identity with
byte/pixel bounds. No tests skip. The final comparison reader decodes the
same bounded bytes it hashes, eliminating a reopen race; it admits at most
16 MiB per PNG and 4 Mi pixels, with no resizing or alignment. Both test
modules run in Catalog CI without a viewer or external corpus.

The metadata receipt contains both fixed plans, driver/tool identities, all
observations and comparisons. The contained desktop launch protocol is the
one described above and in the earlier buffer report; its external driver
is not a portable PDF capture runner. Validate the target page and full-page
placement when reproducing it. UI actions now retain Unix timestamps, while
buffer timestamps use a monotonic clock after hashing; no cross-clock timing
or prefetch cause is inferred.

All new committed code is original MIT. PDF image/soft-mask interfaces follow
the published [Adobe PDF Reference 1.6, §7.5.4](https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/pdfreference1.6.pdf)
and [public ISO 32000-2 image clarifications](https://pdf-issues.pdfa.org/32000-2-2020/clause08.html).
No specification text or external converter implementation is copied. No
private HN/JBIG migration, vendor implementation inspection or vendor font
program/outline inspection occurs. Generated PDFs, source/derived document
bodies, pixels, fonts, binaries and raw logs remain external.

The original `7797…` cold-session discrepancy, general readiness, original
native fonts/ornaments and remaining complete-page fidelity are unresolved.
Rust #441/#406 and samples #51 remain open. The conversion ledger remains
1,252 PASS / 18 FAIL / 27 UNSUPPORTED across 1,297 originals; this investigation
adds no conversion or runtime-parity evidence and changes no production API,
output or supported format.
