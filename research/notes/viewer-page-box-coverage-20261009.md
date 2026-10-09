# Complete missing-box page observations (2026-10-09)

The complete two-round attempt yields **133 equal, 9 differing and 8
not-comparable source/output page pairs**. It does not establish full 75-page
visual fidelity. Repeated observations of unchanged inputs also differ, and
one output-viewer session aborts. Every result is retained in the
[metadata receipt](viewer-page-box-coverage-20261009.json); no session is retried.

This follows [samples #70](https://github.com/rwv/caj2pdf-samples/issues/70)
and extends the [earlier page-box report](cajviewer-page-boxes.md), which
compared only pages 1 and 75. The unchanged 75-page original is
`5d988d74a6e6a0c392eb58297e70d91ff2e1ad2c2887374a04adc67a253ac2ab`;
the unchanged, reviewed 536,962-byte PDF is
`17af66b3201925945c16cbfbda3b587cc3cd2369eafe9ddfcd2f71f15f72c1cf`.
There is no conversion rerun. The complete selected-object/body accounting
in the [profile proofs](pdf-source-profile-proofs-20261009.md) remains separate.

## Original controls and navigation failures

The original MIT [`pdf_page_box_controls.py`](../cajviewer/pdf_page_box_controls.py)
sequentially writes two PDFs below 32 KiB each. Every page contains the same
original red frame, blue diagonal and black square as the historical one-page
control, plus seven binary black-square positions encoding its page number.
All 75 content streams are distinct, and the corresponding streams are byte
identical across the pair. Neither PDF has fonts or text operators. One omits
MediaBox throughout; the other explicitly sets each page to `[0 0 612 792]`.

| Control | SHA-256 |
| --- | --- |
| Missing box | `e59935632c55f7e3c849fac5517b90f8efa9a78774c49305d5e5978869b5e0bc` |
| Explicit Letter | `9952a57d87284636e6b0af2dfc86a528ce701d47cc7729ba31f7c7cc55ed7781` |

A fresh one-page pilot exactly reproduces the historical control raster.
The first three multi-page preflights then expose a navigation limitation in
single-page mode. For the requested route 1→2→37→74→75, typing page numbers
produces displayed pages 1→75→37→75→75, both with and without explicitly
leaving the page field through the Hand tool. First/Next/Previous buttons
produce 1→75→75→75→75. This occurs in both original 75-page controls. A separate
debug session visibly retains the typed `2` before Return and `75/75` after
Return, with the binary marks of page 75. The internal cause is unknown.

All these attempts remain in the receipt. The three original one-page A4
controls correctly fail the Letter-frame check and are negative controls.
They are not continuous-mode observations. The single-page corpus plan was
never launched.

Changing only the mode selection to continuous display, while retaining the
page editor, 80% zoom and fixed waits, correctly visits all requested pages
1→2→3→4→37→74→75 of the original Letter control. A separately frozen paired
preflight then confirms all 14 missing-box/Letter observations, including
independent binary page identities and two equal consecutive frames. All
seven corresponding complete-page rasters match exactly.

## Fixed complete-page protocol

The desktop is 1600×1200 at 96 dpi, maximized, with the side panel closed and
80% zoom. The fixed complete-page crop is 651×843 RGB pixels. Coordinates
below are exclusive at the right/bottom; no translation, resizing, alignment
search or tolerance is applied.

| Profile | Complete page rectangle |
| --- | --- |
| Historical single-page control | `[499,245,1150,1088]` |
| Continuous, pages 1–74 | `[499,157,1150,1000]` |
| Continuous, last page 75 | `[499,325,1150,1168]` |

The final two positions were measured on the original controls before any
real source/output acquisition. The last page is clamped at the viewport
bottom. Four exterior gray frame corners, full desktop dimensions, page/total
and zoom field OCR are checked for each measured frame. Original controls
also require the correct seven-bit page marker. Frames are captured three
seconds after each page submission and one second later. Exact equality
within this interval is an observation, not general readiness under
[Rust #441](https://github.com/rwv/caj2pdf-rust/issues/441).

The corpus plan fixes two rounds of 75 pages per file: ascending in round 1,
with source before PDF, then descending in round 2, with PDF before source.
Each fresh session contains at most eight pages. Forty corpus sessions give
300 page observations and 600 frames. Two postflight sessions revisit the
original missing/Letter controls in route 75→74→37→2→1. They add ten page
observations and twenty frames. Retain all failed, unequal or unconfirmed
outcomes; do not reacquire to obtain a match.

The original plan bytes remain pinned. A contemporaneous metadata erratum
records two accidentally retained descriptions from the unlaunched single-page
plan: the old generic `grid` and `launch_requires` fields. Before launch,
the same plan already pinned the correct continuous driver, per-session mode,
fixed full-page grids, collector, successful v4 preflight and exact paired
comparisons. The launch check required all 14 observations and seven equal
pairs. The correction changes no action, page order, source, comparison grid
or tolerance, and triggers no restart.

Every session uses image
`sha256:cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de`,
network none, read-only root/input, uid 1000, dropped capabilities,
no-new-privileges, 2 GiB memory/swap, two CPUs, 256 PIDs, bounded temporary
files and a 90-second hard lifetime. No observer or LD_PRELOAD is used.
The caller-mounted UI font has SHA-256
`b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a`.
Input hashes, application logs, OOM state, peak memory and confirmed container
removal accompany each session. The receipt pins all launch/action/timing/log
and capture files, including failed attempts. Raw bodies remain external.

## Measured outcomes

All 300 real page observations were attempted in the 40 planned sessions.
Of these, 292 confirm the page/zoom/frame checks and exact equality of the two
consecutive frames. One output session (`r2-b06-pdf`, pages 35 down to 28)
contains `free(): invalid pointer` and `Aborted` diagnostics. Its sixteen
captures are entirely black; all eight page observations remain NOT_CONFIRMED.
The UI automation still returns successfully because the desktop survives:
driver completion and container liveness are not application success. There
is no OOM or input change, and no replacement session is launched.

| Exact comparison | Equal | Different | Not comparable |
| --- | ---: | ---: | ---: |
| Source/output, ascending round | 66 | 9 | 0 |
| Source/output, descending round | 67 | 0 | 8 |
| Same CAJ bytes, across rounds | 55 | 20 | 0 |
| Same PDF bytes, across rounds | 50 | 17 | 8 |
| Postflight missing-box/Letter pairs | 5 | 0 | 0 |

All nine source/output differences occur in the first round:

| Page | Changed pixels | Channel delta | Same two raster hashes recur in unchanged-input repetition |
| --- | ---: | --- | --- |
| 11 | 15,721 | -1 through 2 | pdf |
| 18 | 17,338 | -1 through 2 | source |
| 26 | 14,602 | -1 through 2 | source |
| 28 | 22,042 | -1 through 2 | source |
| 34 | 1,518 | -1 through 1 | Not established; second PDF session aborted |
| 42 | 56,826 | -135 through 48 | source |
| 58 | 22,814 | -1 through 2 | source |
| 66 | 16,876 | -2 through 1 | pdf |
| 74 | 2,254 | -1 through 1 | pdf |

Thus eight of nine differing source/output pairs have the identical two RGB
hashes in predeclared observations of one unchanged input. Page 42's larger
color differences recur exactly in the unchanged CAJ repetition; they are not
silently reduced to an antialiasing tolerance. Page 34 remains unresolved
because its second output observation is unavailable. These facts establish
observed variation without identifying its internal cause or proving every
conversion pixel correct. Route/order and fresh-session state vary together;
this experiment does not isolate their causal contribution.

The forty corpus and two postflight sessions all preserve their inputs,
avoid OOM and complete cleanup. Across all 56 retained sessions, measured
viewer/display peak memory ranges from 304,979,968 to 475,713,536 bytes; this
is not converter memory. All ten postflight page observations pass the
original marker/state checks and consecutive-frame equality. All five
corresponding complete-page pairs match exactly. None of this erases the
failed or differing real-document observations.


The 14 pre-corpus sessions contain 57 planned page observations: 39 confirmed
pairs of consecutive frames and 18 rejected observations (15 wrong-page
observations and three expected A4 frame negatives). This is original-control
evidence, not 39 successful corpus conversions.

## Validation and limits

```sh
python3 research/cajviewer/pdf_page_box_controls.py /external/new-page-controls
python3 -m unittest discover -s research/conformance -p 'test_*page_box*.py' -v
```

Two fixture tests independently check qpdf/pikepdf parsing, all 75 page IDs,
box omission, empty resources, paint operations, matching raw content and
bounded non-overwriting generation. Four observation tests reject wrong
state, full-frame dimensions/types, frame corners, unsupported profiles,
stale page markers and incomplete page grids, while detecting every changed
pixel including both page corners. All six pass without corpus or viewer
access and without skips; both modules are added to Catalog CI.

The existing bounded PNG reader hashes and decodes the same input bytes,
with 16 MiB file and 4 Mi-pixel limits. The page comparison uses bounded
651×843 arrays. Source copies/hashes and generated control writing remain
streamed; there is no whole-document conversion API or new product dependency.

The exploratory all-module local discovery is retained separately: baseline
701 versus branch 707 tests have exactly the same 26 failures and 53 errors.
These historical groups include missing old Rust-layout paths and unavailable
host dependencies. The local workflow selection has three unavailable groups
(Qt5 development metadata for two observer groups, and scipy for raster
comparison). These are not passing or skipped compatibility evidence.
The pull request records the exact-head Catalog CI result in its configured
environment; neither local failure set is described as a passing full suite.

The initial fixture inspections accidentally let pikepdf materialize missing
boxes. Both failed attempts remain recorded; final inspection disables page
attribute inheritance explicitly. A subsequent observation-test expectation
was corrected to accept the earlier page-inventory guard and test stale
content at the same fixed grid. Neither change alters generated PDF bytes.

All committed code is independently authored MIT, based on the earlier
original vector control and public PDF/X11 interfaces. No vendor implementation
or vendor font program/outline is inspected; no foreign converter or private
HN/JBIG source is copied or migrated. PDFs, source streams, pixels, fonts and
binaries remain outside Git.

Observed source clipping remains source behavior; matching its Letter fallback
does not recover absent inherited geometry. This protocol does not establish
a universal viewer-readiness rule, original native fonts/ornaments, unknown
C8/HN-B outlines or encrypted-payload recovery. Rust #441/#406 and broader
native fidelity work remain open. The ledger remains 1,252 PASS / 18 FAIL /
27 UNSUPPORTED across 1,297 originals. No API, CLI, JavaScript, production I/O,
output PDF, supported-format, release-note or release change follows.
