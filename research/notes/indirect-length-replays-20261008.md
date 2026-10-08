# Indirect-Length ordering and same-row CAJ replays, 2026-10-08

[Rust #444](https://github.com/rwv/caj2pdf-rust/issues/444) and
[PR #445](https://github.com/rwv/caj2pdf-rust/pull/445) recover the unchanged
141-page Lambertian CAJ. The [metadata receipt](indirect-length-replays-20261008.json)
records independent framing, every interrupted range, page/resource paths,
Length dependencies, all-page comparisons, scoped original-viewer checks,
runtimes and regression results. Parent [#406](https://github.com/rwv/caj2pdf-rust/issues/406)
remains open; other failures are not declared impossible.

Reviewed production head: `6b06130b8ffe8eb2328e7e569ed54b7e6838a194`, based on
merged `8ba530357d200a341626fbdb4cbbc0ab1840e71c` (#443). Locked native and WASM
artifacts were frozen externally before regression. No release.

## Source and independent framing

[CAJSamples issue-30/Lambertian.caj](https://github.com/caj2pdf/CAJSamples/blob/7e1c35e7b6de34e21972fcd1752c2a7e99b4ad07/issue-30/Lambertian.caj)
has SHA-256 `c41cd7306591e0a4fc40728617b2d42d7302ba57413591de00f18bcf63023743`,
3,875,504 bytes, 141 pages and 31 bookmarks. Independent declared-Length and
complete-tail framing finds 15,525 complete unique objects, 7,623 raw streams,
31 complete duplicate occurrences and 158 interruptions. Every interruption
is an exact proper prefix of a retained same-ID object. The independent PDF
retains the entire source body verbatim and adds only missing page-tree,
catalog and xref framing. Qpdf exits 0.

The first independent framer used a 64 KiB metadata probe and missed the
70,053-byte Resources dictionary 7563. The complete gap inventory exposed
that omission. Its qpdf success was insufficient evidence and is retained as
a superseded result. The corrected bounded framing includes the dictionary
and has no unexplained gap. All 7,623 indirect Length dependencies are checked
against source integer objects. The structural graph records 284 paths covering
all 158 interrupted targets. Scalar Length edges are read from original stream
headers because the PDF library resolves indirect integers. Reachability does
not establish that every resource is executed.

## Cause and bounded recovery

Stream 7566 has a 78-byte prefix at 1,819,698 and a complete copy 583,921 bytes
later, in the same long page-table row. Image streams 15446 and 15491 have
207- and 221-byte proper prefixes. Their provisional unknown-Length extents
reach later terminators, incorrectly appearing to be complete conflicting
objects. Length 15558 is present at 189,264 with value 114,224, but another
provisional stream extent hides it. Resolving the known later Length 3 exposes
that integer on a new scan. Independent JPEG decoding confirms its complete
image payload; the diagnostic does not establish image corruption.

The fix resolves observed Length constraints in a bounded batch before using
provisional spans to validate duplicates, anchored candidates or missing
integers. Sorted hints have bounded metadata and binary lookup. The existing
16-rescan limit stays unchanged, and final integer objects remain mandatory.

A known Length and later terminator can propose a same-row copy within 1 MiB.
It must have the same header, an exact tail, a proper matching prefix containing
payload, and a parsed adjacent next-object boundary. The complete scan must
reach the exact proposed counterpart, including when another complete same-ID
prefix exists elsewhere. Prefix comparison reuses two at-most-256-byte buffers,
with a 64 KiB prefix cap and at most 64 non-NUL spacing bytes. No whole gap is
buffered. Conflicting anchored candidates, complete duplicates, changed sources
and unproved boundaries remain errors. No codec is reinterpreted; ordinary
indexed PDFs retain their existing scope.

Earlier equal-width diagnostic omissions of one, two and three prefixes all
failed. Their inputs, ranges, hashes and errors remain distinct from conversion
of the unchanged original. No modified diagnostic is counted as a compatibility
pass.

## Content, runtime and original-viewer checks

Final native conversion passes qpdf with no stderr. Every complete object
value and raw stream agrees with corrected independent source framing:
**15,525 objects and 7,623 streams**. All **141** page identities/order, boxes,
rotation, text, links and Poppler RGB72 renders agree, as do all **31** source
bookmarks. No MuPDF warning or Poppler stderr was observed.

Native, Node and Chromium produce the same 4,100,130-byte PDF, SHA-256
`01e138e904710100e75f39de16d2101a1b80fed345eaf5bceba1565a12e14efb`.
Chromium uses ranged OPFS input and sequential output, and removes all temporary
entries. This is one-original runtime evidence, separate from the full native
regression.

Eighteen fresh offline CAJViewer sessions compare original-source pages
**2, 30, 46, 58, 93 and 133**, their native PDFs, and deliberate black-rectangle
controls. The visually checked full frames show the requested pages at 50%;
crop `[626,156,1023,718]` includes the complete current page. Captures at 3,
10 and 12 seconds agree. All six source/native crops match exactly; every
changed-content control differs by **1,980 pixels**.

Each session uses the pinned image, network none, read-only root/input,
non-root user, dropped capabilities, 2 GiB memory/swap, two CPUs, 256 pids and
a 90-second hard lifetime. Source hashes stay intact, no OOM occurs, and all
containers are removed and verified absent. Screenshots remain external.
These selected pages do not establish whole-document vendor fidelity or
resolve the cold-session repeatability observation in [#441](https://github.com/rwv/caj2pdf-rust/issues/441).

## Validation and remaining limits

The final **1,277-original / 2,126-attempt** native run has **1,247 PASS,
21 FAIL and nine UNSUPPORTED**. Only this original changes from FAIL to PASS.
All **2,095** prior successful attempts retain their PDF hashes; no conversion
regresses. All 1,247 primary outputs pass qpdf. Source integrity and failed-output
cleanup pass throughout. Source `50c8c55b978a` remains FAIL without output; its
diagnostic changes from an unproved prefix at 599,216 to an unrepairable stream
Length at 220,188. That changed diagnostic is not a compatibility pass.

The older ancillary checker reports 285 page-order PASS, 26 FAIL and 936 NOT_RUN;
outlines have 297 PASS and 950 NOT_RUN. The 26 prior independent native-page
checks and 936 bitmap-oracle checks retain their scopes through fresh PDF byte
identity, not rerun decoders or new viewer evidence. Their pinned receipts and
all exclusions remain in the JSON.

The separate extended catalog retains its identical 433-page NH PDF and
18 unsupported offline CAA descriptors. No opaque CAA target is decoded,
logged or resolved; the added NH has no original-viewer pixel claim.

Final local validation: **1,347 Rust tests pass**, seven optional-corpus tests
are ignored; **166 JavaScript tests pass**, zero skipped. Seven new original
control groups exercise ordering, many constraints, missing/conflicting
integers, source changes, fake copies, finite distance/prefix/tail bounds,
short I/O, cancellation and metadata limits. Formatting, strict Clippy,
source inventory, doc links and locked native/WASM builds pass. All eight
required exact-head quality/Linux CI statuses pass. Line coverage is
**98.63% (29,358/29,767)**, above the configured 90% floor.

Self-review combined repeated candidate paths, reused the existing exact-range
confirmation loop and prefix comparison, and removed a redundant error match.
Existing tests caught anchored evidence being bypassed by the longer search;
that regression was corrected before final validation. No new parser/graph/
writer abstraction, public API or dependency was added. All implementation and
synthetic tests are original MIT. No foreign converter/vendor implementation,
private HN/JBIG code or external document/PDF/text/pixel/font bytes enter Git.
