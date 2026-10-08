# Interrupted metadata and missing CAJ parents, 2026-10-08

[Rust #452](https://github.com/rwv/caj2pdf-rust/issues/452) /
[PR #453](https://github.com/rwv/caj2pdf-rust/pull/453) recovers the unchanged
53-page original previously refused at metadata object 318 and then at five
missing-parent openers. The [metadata receipt](interrupted-metadata-parents-20261008.json)
retains independent source framing, all-page comparisons, scoped viewer
controls, runtime/build identities, the complete regression, initial failed
attempts and a separately fixed CI cancellation race.

## Source and independent proof

The [pinned original](https://github.com/yizhihong1206/caj2pdf-actions/blob/10bd169615ef5cf7f3b9fcdbab9cdda108246184/file.caj)
is 795,662 bytes, SHA-256
`50c8c55b978aedce644fc2fba6246c0cb5babee3389e2b59fda7d4e7efdbf89c`,
Git blob `292b9f09f86a14833552acd63112535e8c595f7b`. It contains 53 pages and
56 bookmarks. This existing identity is updated, not added again; the catalog
remains **1,297 identities**.

Independent framing identifies 247 distinct complete original values,
84 raw streams, nine duplicate complete objects and 19 interrupted full-header
candidates. Sixteen candidates have exact proper-prefix complete counterparts.
Of 27 separate non-whitespace gaps, 24 repeat complete-object header prefixes.
Synthetic diagnostic objects are excluded from original counts.

The remaining spans contain the unused metadata opener 318, bare parent
headers 263/215/199, and payload-free dictionary openers 183/161. Metadata 318
has only Length/Type/Subtype and the interrupted XML packet opener before a
complete integer resolving an earlier stream. No parsed original value refers
to it. The only missing references in the complete original graph are 53 Parent
links to ten absent page-tree IDs. Every page explicitly supplies all four
inheritable properties: MediaBox, CropBox, Resources and Rotate. No ObjStm/XRef
stream can hide another incoming edge. No inherited page value is guessed.

An earlier diagnostic allocated root 318, reusing an omitted original ID;
that attempt is retained and excluded. Corrected framing keeps the original
body verbatim and allocates synthetic IDs above all observed original headers.
A metadata-only omission still fails at parent 263. An equal-width six-span
diagnostic matches independent complete-object/page evidence, but is never
counted as an unchanged-original pass.

## Recovery and original controls

The reviewed core uses bounded ranged reads and existing full-graph and CAJ
page-order reconstruction. Metadata needs an exact three-key header, fixed
packet prefix and pending-Length boundary; the complete scan must prove it
unreferenced. A missing-parent opener contains no key or value and precedes a
complete Page. Every incoming edge must be the sole Parent field of a leaf
with explicit valid inheritable properties. Opaque metadata, ambiguous or
referenced omissions, missing properties and unrelated profiles remain errors.

Metadata headers are capped at 256 bytes and parent openers at 64 bytes.
Existing unused interruptions and the local pending-parent list each have a
64-record cap under allocation limits. No whole-file conversion buffer,
API/dependency change, foreign converter/vendor code or private migration is
introduced by the core repair. Synthetic controls cover exact boundaries,
256/257 and 64/65 limits, invalid graph roles/inheritance, source changes,
every successful-path read failure and cancellation checkpoint, short reads,
allocation refusal, table order and extra out-of-table pages.

## Unchanged-original results

Native, Node and Chromium output SHA-256 is
`b47a462aff6c61bc3b7b22ced5cb6e6ca000e637ec4080fdc6800e75a0cf1c9b`.
Qpdf, source integrity and browser temporary-file cleanup pass. All 247 original
object values, 84 raw streams, 53 page references/geometry/text/link inventories
and Poppler RGB renders match independent source framing. All 56 source CAJ
bookmark titles, depths, order and destinations match. The first candidate's
complete comparison remains applicable because the frozen release output is
byte-identical; it is not relabeled as a reader rerun.

Seven fresh isolated source-viewer sessions cover original CAJ and independent
PDF pages 1, 20 and 53, plus a painted-content negative. All three captures per
session are retained. Original/diagnostic crops match; the negative changes
3,568 pixels. Page 53 uses its measured last-page viewport position. All
containers close without OOM and source hashes remain unchanged. Other viewer
pages are NOT_RUN; this does not resolve #441 or prove general viewer readiness.

The release baseline has **1,277 originals / 2,126 attempts: 1,249 PASS,
19 FAIL, nine UNSUPPORTED**. This is one new pass, no conversion regression,
unchanged refusal diagnostics and **2,097 identical prior-success attempt
hashes**. Every primary successful PDF passes qpdf. Ancillary page-order checks
are 287 PASS / 26 FAIL / 936 NOT_RUN; source-outline checks are 298 PASS /
951 NOT_RUN. Existing independent bitmap/native-text evidence retains its
original scope and applies by unchanged output hashes, not new decoder runs.

The 19-input extension remains one 433-page NH pass plus 18 offline CAA
unsupported descriptors. The separately archived #449 PDF remains exactly its
original bytes on native, Node and Chromium. Across all 1,297 identities this
is **1,251 conversion PASS, 19 FAIL and 27 UNSUPPORTED**. These are conversion
statuses, not universal fidelity or irrecoverability claims. They come from the
fresh per-input receipts; other catalog rows may retain older, explicitly
pinned conversion revisions. The prior
1,247-input Node/Chromium sweep retains its actual #444 build identity; it is
not a sweep of this new package. Seven ignored optional-corpus tests are not
compatibility passes.

## Failed attempts and CI integration

The exploratory native build was inadvertently a debug CLI. Its slow bulk run
was stopped after 48 complete reports; those reports and the interrupted
extension process are retained separately. The authoritative baseline uses a
frozen release binary. Committed-head rebuilds reproduce both native and WASM
artifacts exactly. Final integrated CI passes all eight required checks,
**1,369 Rust tests** (seven optional-corpus tests ignored), and **171 JS tests**
with no skips. Line coverage is **98.57% (30,052/30,488)** against the configured
90% floor.

Initial core head `fb8f800da082c019fe4f90bc1a128bdc9bac7c6d` twice failed a
real Chromium abort-cleanup check. Investigation produced child
[#454](https://github.com/rwv/caj2pdf-rust/issues/454) and reviewed
[PR #455](https://github.com/rwv/caj2pdf-rust/pull/455). A controlled schedule
reproduced a lost notification between the Worker's cancellation check and ACK
wait: 10.087 seconds and a remaining spool before the repair, 0.026 seconds and
empty OPFS after it. A visibility-only diagnostic exposed AbortError plus
NoModificationAllowedError. The permanent test asserts the wait result and
cleanup without a timing threshold. Historical size-limit issue #213 remains
unproved and open.

PR #455 merged as `29531a695b3e61d150e427948f840df4064f342b`, with all eight
required checks and 171 JS tests passing. Its separate breaking edge case makes
spooled conversion wrappers expose both conversion and removal errors through
AggregateError; callers inspect `cause` for the primary error. The core PR is
rebased at `a1781be5188d327f04239fc9d3e8ab54b8dd616c`, retaining both documentation
additions and byte-identical Rust source/tests and native/WASM binaries. Fresh
integrated runtime and CI results are recorded in the receipt; failed jobs are
not erased by the successful integration.

External documents, PDFs, text, pixel/font data and vendor implementations are
not committed. No release is performed. The related `eacbcd…` source, other
refused originals and remaining #406 fidelity gaps are not claimed resolved.
