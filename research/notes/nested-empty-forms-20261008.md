# Nested duplicate empty Forms, 2026-10-08

[Rust #439](https://github.com/rwv/caj2pdf-rust/issues/439) and
[PR #440](https://github.com/rwv/caj2pdf-rust/pull/440) recover three unchanged
CAJs that contain a complete empty Form inside an equivalent same-number
empty Form wrapper. This note and its [per-input receipt](nested-empty-forms-20261008.json)
record bounded recovery, independent content comparisons and remaining
source-viewer limits. The parent [#406](https://github.com/rwv/caj2pdf-rust/issues/406)
remains open; other refusals are not declared impossible.

Production head: `849e421ef34bf0706da028ff33b8b0f5e3b95e26`, based on merged
`edafd3006ad72745538e6b630d9f28311793c276` (#438). The production implementation
is unchanged from `5f33e28e29d03ff7b7e6589afa425c3e33d1dad9`; the last commit
only records provenance and verification limits. Native/WASM binaries were
frozen externally and their hashes are included in the receipt. No release.

## Measured profile

All three originals come from `CatTalk2/Face-recognition` at revision
`9d9e9ab77e7703c10b53fdae140ef283c2d9a3d0`. The receipt and catalog retain
pinned source/download URLs and full input/output hashes.

| Original SHA-256 prefix | Bytes | Pages / bookmarks | Form | Outer / inner header offsets |
| --- | ---: | ---: | ---: | ---: |
| `0374e70b8fe0` | 4,012,590 | 66 / 54 | 9418 | 1,291,424 / 1,291,547 |
| `76e306d87586` | 2,210,533 | 81 / 90 | 182 | 1,280,865 / 1,280,988 |
| `7797fd3c7d6c` | 2,113,453 | 64 / 22 | 29 | 115,059 / 115,179 |

Each pair has generation zero, direct Length zero and exactly Type XObject,
Subtype Form, Length, BBox and Matrix. All numeric tokens agree exactly;
whitespace differs. The inner object starts at the outer data boundary and
has its complete tail, followed by another complete outer tail. The scanner
retains the complete inner object's bytes and omits only redundant framing.

Each header is bounded to 256 bytes. Two tails are checked in a 287-byte
window, allowing at most 64 PDF whitespace bytes before each keyword.
Additional keys, conflicting geometry/ID/generation, nonzero or indirect
Lengths, content bytes, gaps, incomplete tails and recursion do not qualify.
Both headers and tails are rechecked before selection. Ordinary object
indexing, duplicate checks, graph validation and sequential copying remain
in use; indexed PDFs retain strict framing. No whole-input API or new codec,
dependency, platform adapter or public API is involved.

An initial diagnostic removed only the outer header and failed; the corrected
diagnostic removed the outer header and tail using equal-width whitespace.
Both attempts are retained. That diagnostic isolation is separate from the
subsequent successful conversion of every unchanged original.

## Independent checks

An independently constructed PDF keeps the original CAJ body verbatim,
including the redundant wrapper. Its xref selects all complete source objects
and the inner Form, omitting only the redundant outer declaration's xref entry.
It supplies only missing page-tree/catalog framing, using original page-table
order and Parent links. No external converter implementation is used.

| Original prefix | Complete object values | Raw stream payloads | All-page Poppler RGB72 / geometry / text / links |
| --- | ---: | ---: | ---: |
| `0374e70b8fe0` | 640 equal | 262 equal | 66 equal |
| `76e306d87586` | 736 equal | 373 equal | 81 equal |
| `7797fd3c7d6c` | 348 equal | 119 equal | 64 equal |

All 1,724 selected object values and 754 payloads match. All 211 page IDs,
order, boxes, rotation, text/link inventories and RGB renders agree. All 166
source bookmarks agree; qpdf accepts every output and independent framing.
Poppler emits no stderr during these render comparisons. MuPDF reports a
non-embedded SimSun identity-encoding warning on the 66-page source; its
verbatim warning is retained, not interpreted as a new repaired font feature.

The first comparison harness accidentally reused bookmark count as page
count. It compared only 54 and 22 pages on two sources and overran the 81-page
source at page 82. Those partial/error attempts are explicitly superseded.
The corrected harness uses an independent `page_count`, asserts complete
coverage and reruns all 211 pages in fresh directories. Only the complete
rerun supplies the all-page result above.

Native, Node.js and Chromium produce byte-identical PDFs on all three
unchanged originals. Chromium uses ranged OPFS input/sequential output and
removes temporary entries. This is three-original runtime evidence, separate
from the full native regression below.

## Original-viewer scope and disagreement

Original content streams execute the empty Forms directly 15 times across
11 pages: pages 30/35; 31/51/56/60/61/62/63/64; and page 3, respectively.
Resource registrations and actual `Do` executions are recorded separately.

Sixteen fresh offline contained CAJViewer sessions cover selected affected
pages 30, 31 and 3 at 50%, including one painted Form negative control per
source and follow-up controls. Full screen captures were inspected for the
requested page, state and page edges. The comparison crop `[626,156,1023,718]`
contains the complete current page. First and second source/PDF crops are
identical. Painted controls change 88, 77 and 110 pixels against their
original-source baselines, demonstrating sensitivity to the executed Form.

The first third-source PDF session differs from the unchanged CAJ by 5,169
pixels, despite two consecutive captures being identical. Three fresh
sessions of the **identical PDF bytes** then match exactly: two waited 10
seconds; another used the original filename and matched at 3, 4, 10 and 20
seconds. Independent source-body PDF, diagnostic CAJ, no-bookmark PDF and
source-order PDF controls also match, but these confounded controls do not
establish a causal bookmark/order defect. No workaround is inferred.

All attempts, including the first disagreement, remain in the receipt.
Cause and a reliable readiness/repeatability criterion remain open in
[#441](https://github.com/rwv/caj2pdf-rust/issues/441). These are scoped viewer
observations; stable whole-document vendor fidelity is **not established**.

Every session uses the pinned image, network none, read-only root/inputs,
non-root user, dropped capabilities, 2 GiB memory/swap, two CPUs, 256 pids and
a 90-second hard lifetime. Input hashes remain intact, no OOM occurred, and
all containers were removed and verified absent. Pixels stay external.

## Regression, tests and review

The fresh 1,277-original / 2,126-attempt native run has **1,243 PASS, 25 FAIL
and nine UNSUPPORTED**. Exactly these three originals become PASS. All 2,089
previous successful attempts retain their PDF hashes; no conversion regresses.
All 1,243 primary outputs pass qpdf. Source integrity and failed-output cleanup
pass throughout.

The older ancillary checker still reports 281 page-order PASS, 26 FAIL and
936 NOT_RUN, plus 293 outline PASS and 950 NOT_RUN. Those statuses remain
visible. The separately pinned applicable checks for the 26 native documents
and 936 bitmap/glyph documents apply to freshly verified identical PDF hashes;
they were not rerun and do not become new whole-page viewer proof. Other
refusals, encrypted-input requirements and HN-B/C8 outline gaps remain open.

The extended catalog rerun preserves the added 433-page NH PDF hash and
18 unsupported CAA offline target descriptors. No descriptor target value is
decoded, logged or contacted. The added NH's original-viewer pixels remain
NOT_RUN.

Local validation: 1,331 Rust tests pass; seven optional corpus tests are
ignored and are not compatibility passes. All 166 JavaScript tests pass with
zero skips. Eight new authored MIT test groups cover the measured profile,
neighboring refusals, short/chunked I/O, cancellation/allocation limits,
source changes/errors, conflicting complete copies and strict indexed PDFs.
Strict clippy, rustdoc, format, source inventory, documentation links and
locked native/WASM builds pass. The final required quality/Linux checks are
recorded individually in the receipt. Measured line coverage is 98.67%
(28,639/29,026), above the configured 90% floor; the job's historical label
is not a claim of 100% coverage. One native quality job was cancelled after
its external package download stalled for over ten minutes and rerun without
source changes; the cancelled attempt is not a passing check.

[Final self-review](https://github.com/rwv/caj2pdf-rust/pull/440#issuecomment-6059800569)
resolved exact-adjacency and evidence-harness findings, reduced the recovery
result to the selected object plus resume offset, and reused the validated
structural inspection and existing writer. This is self-review, not an
independent approval. #439's bounded recovery and scoped evidence are separate
from #441's unresolved repeatability and #406's remaining fidelity work.

Only original MIT code, authored synthetic controls and observation metadata
are committed. No external document bytes, PDFs, document text/pixels, fonts,
vendor binaries or foreign/private converter implementation enter Git.

## Original page-3 viewer follow-up (2026-10-09)

The [actual-document JPEG report](viewer-original7797-jpeg-20261009.md) and
[receipt](viewer-original7797-jpeg-20261009.json) reproduce both historical
`7797…` crop values with unchanged CAJ/PDF bytes. The old differing PDF crop
corresponds to the observed pre-JPEG value; the old original reference matches
the decoded JPEG value. Seven confirmed buffer sessions share the same
pre-encoding target hash across source and PDF, and one observed CAJ session
links encoding input, encoded bytes, returned rows and the selected QImage value.
All twelve sessions are retained, including one unconfirmed viewer abort and
the first collector's corrected timestamp-field assumption. Historical calls
were not instrumented and are not retroactively claimed observed.

This explains the scoped page-3 discrepancy and updates its evidence limit.
It does not establish general readiness or complete all-page original-viewer
coverage. The initial mismatch, old receipts and other original documents are
unchanged evidence; no recovery behavior, conversion counts or release changes.
