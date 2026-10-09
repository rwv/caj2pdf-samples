# Original #441 page discrepancy: JPEG representation (2026-10-09)

The two historical page-3 crops in [Rust #441](https://github.com/rwv/caj2pdf-rust/issues/441)
are reproduced with the unchanged real document. The crop originally labeled
as the **differing PDF** corresponds to the observed **pre-JPEG** page value A.
The historical **original CAJ** reference corresponds to the **decoded JPEG**
value B. A newly observed CAJ session connects A, encoded JPEG bytes and B
through public APIs. Thus the old differing PDF image is not evidence of a
converter content change: the source CAJ can display that identical image too.
Historical calls were not instrumented; this explains their exact raster values
using the new observations, without claiming to have observed those old calls.

The [metadata receipt](viewer-original7797-jpeg-20261009.json) records all
12 fixed sessions: **seven confirmed buffer observations, four confirmed
screenshot-only observations and one unconfirmed viewer abort**. All seven
observed target values have the same pre-encoding SHA-256 across CAJ and PDF.
This is page-3 evidence; general readiness and complete original-viewer coverage
remain open. The work is tracked in [samples #76](https://github.com/rwv/caj2pdf-samples/issues/76).

## Unchanged input and historical evidence

| Identity | Value |
| --- | --- |
| Source | `CatTalk2/Face-recognition`, revision `9d9e9ab77e7703c10b53fdae140ef283c2d9a3d0` |
| CAJ SHA-256 | `7797fd3c7d6ce8b1ae8203ff9957d6a52ef76c4290a8a777da66297f30c8fa78` |
| CAJ bytes | 2,113,453 |
| PDF SHA-256 | `d54f082daf364513529f46a7fe92b539512a498d2aec50e9dccb3078fa57e041` |
| PDF bytes | 2,201,598 |
| Pages / bookmarks | 64 / 22 |

The old #439 PDF is byte-identical to the accepted native/Node/Chromium entry
in the [current runtime receipt](https://github.com/rwv/caj2pdf-samples/blob/9b4e708581cd7bf6953cc19500adaad583a71aa9/research/notes/current-corpus-runtime-20261008.json).
No converter is rerun and no corpus original is downloaded. Source and retained
PDF/session inputs are checked before acquisition and again after each session.

The old full crop remains `[626,156,1023,718]`, 397×562 pixels at 50%:

| Historical crop | RGB SHA-256 | New observed representation |
| --- | --- | --- |
| Original CAJ / later matching PDF | `5606fc70c62dcafc62a3bb82a982a839d5ca1b97b0e2e1981d375e35c2eda239` | B, decoded JPEG |
| First differing PDF | `965a84261f2dd7d4c2a394d1932a0a0d1666e8b9f662d5a0da127c5890c5eeed` | A, before page JPEG encode |

The retained old images still differ at exactly **5,169 pixels**, with maximum
absolute channel difference two. Neither image is discarded or replaced.

## Frozen sessions and all outcomes

Plan SHA-256: `b70291e5078e347f3a00707282a73313a93bfa31fdb238f80296e3b261b8d9f5`.
The plan fixes all twelve source/PDF, route, repetition and observer choices
before the first launch. Target-page captures follow delays of three seconds,
another one second and another six seconds; exact action timestamps are retained.
Both earlier navigation captures and all target captures remain external.

| Session | Input / route | Observer | Final crop | Result |
| --- | --- | --- | --- | --- |
| 01 | CAJ, direct 3 | Yes | A | Confirmed buffer |
| 02 | PDF, direct 3 | Yes | A | Confirmed buffer |
| 03 | CAJ, 5→3 | Yes | A | Confirmed buffer |
| 04 | PDF, 5→3 | Yes | Unconfirmed | Viewer reports `free(): invalid pointer` |
| 05 | CAJ, direct 3, repeat | Yes | A | Confirmed buffer |
| 06 | PDF, direct 3, repeat | Yes | A | Confirmed buffer |
| 07 | CAJ, 5→3, repeat | Yes | B | Confirmed buffer and JPEG chain |
| 08 | PDF, 5→3, repeat | Yes | A | Confirmed buffer |
| 09 | CAJ, direct 3 | No | B | Confirmed screenshot |
| 10 | PDF, direct 3 | No | B | Confirmed screenshot |
| 11 | CAJ, 5→3 | No | B | Confirmed screenshot |
| 12 | PDF, 5→3 | No | B | Confirmed screenshot |

Every confirmed session has three equal complete target crops. All 33 confirmed
captures equal one of the two historical page-3 crops exactly: 18 A and 15 B.
Page `3/64`, zoom `50%` and fixed exterior frame corners also confirm. Known
full-crop identity, rather than OCR alone, supplies the page-content identity.
An unfamiliar crop would remain explicit pending identity review; none occurs.

The seven observed sessions yield six A page buffers and one B page buffer.
All four sessions without observation hooks display B; the historical first
PDF session already demonstrates A without these hooks. This does not establish
that observation has no timing effect. Sessions 03 and 07 follow the same CAJ
route yet produce different representations. Equal successive captures and a
fixed route therefore still do not establish a common comparison stage.

The aborted session is retained and not retried. Its raw JPEG trace has 15
readable events without a limit marker, but that does not verify its page state
or make the session successful. No cause for the abort is inferred.

## Observed values and order

| Stage | SHA-256 |
| --- | --- |
| RGB A, 397×561, before observed page JPEG encode | `f1a38043f9b248c635f3926029bf872dc13ce3e9adca6b1084f5329fca8844a9` |
| Encoded bytes, same digest at encoder and decoder interfaces | `68bb34e6f57790d5e67d03665946c56a639d0cfd69205c2f7c19521fe11f6dc2` |
| Returned RGB B, matching QImage and final target pixmap | `3e7a63e0a0af58d17a829c50e82c2252eda5df7cb73e7a6c9fde3d565149bf4a` |

Session 07 observes both JPEG contexts in process 21. The encoder uses quality
100, integer DCT, component sampling 2×2/1×1/1×1 and unit quantizers. The decoder
returns all 561 RGB rows with integer DCT. The encoded memory hashes agree.
The completed decoder-row hash is recorded at destroy, not a finish call;
it does not assert finish/EOI validation. The actual decoder upsampling option
is not logged. No new external JPEG candidate search or normalization is run.

The common monotonic clock records this strict order:

| Event | Monotonic nanoseconds |
| --- | ---: |
| Encoder completion | 20661463857794825 |
| All returned decoder rows, at destroy | 20661463873045140 |
| Matching public QImage constructor value | 20661463885890713 |

That QImage value precedes the final screenshot capture. Its RGB rows match the
selected final target pixmap exactly. **The older QPainter log has no timestamp
or process-ID fields**: its final target-sized value is retained, without
inventing a chronological paint join or a renderer call graph. The first two
captures receive screenshot evidence only; buffer correlation is scoped to the
final target value. The full trace and all matching alternatives remain in the
receipt rather than choosing an undocumented cache operation.

All seven confirmed buffer sessions identify exactly the same pre-encoding
target value A, whether A is directly displayed or B is decoded. The raw A/B
buffers differ at **2,499 pixels**, with maximum absolute channel difference
two. The 5,169-pixel historical difference is measured after display scaling;
these are different stages and their counts must not be conflated.

## Analysis correction, bounds and controls

The first collector incorrectly treated QPainter's textual `pixmap-rect` field
as a timestamp. It rejected seven observed sessions; one separate session was
rejected for the real viewer abort, and all four plain sessions confirmed.
That collector, its plan and all initial outcomes remain recorded. Read-only
reanalysis removes the false time-field assumption, scopes QPainter to its
final value and uses the genuine JPEG/QImage clocks before the final capture.
No pixel, crop, source file, observer or capture is changed or reacquired.

The original MIT [`jpeg_trace.py`](../scripts/jpeg_trace.py) reads at most
16 MiB, 40,000 records and 512 characters per record. It requires explicit
process namespaces, contiguous process-local event identities, valid digests
and complete bounded RGB rows. It correlates only equal encoded hashes with
matching dimensions in the same process and forward time order. Limit markers
prevent a confirmed chain; ambiguous encoders remain multiple candidates.
An index avoids unrelated encoder/decoder pairs, and exceeding 10,000 candidate
pairs refuses the correlation instead of expanding an unbounded result.
It does not turn equal lossy outputs into equal pre-encoding inputs.

Eight original test groups cover finish versus complete rows at destroy,
cross-process collisions, reversed/late events, dimensions and byte identity,
partial rows and missing digests, invalid process/sequence/grid evidence,
limits, ambiguous encoders and adversarial repeated-identity expansion.
Final review added the streaming-read/candidate bounds; read-only reanalysis
preserves all twelve observations, exact metrics, hashes and chain records
identically. Earlier analysis versions remain retained.
These tests run in Catalog CI without a viewer
or document download. The existing observer binary is unchanged from
[samples #75](https://github.com/rwv/caj2pdf-samples/pull/75), SHA-256
`6e8d3f6456a0ec512c9e77d3b5957a7bbc59a17dacc61fd54c02835655d2f8a9`.
Its original API forwarding/resource controls remain required in the same CI.

All sessions use the pinned viewer image
`sha256:cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de`,
network none, read-only root/inputs, uid 1000, dropped capabilities,
no-new-privileges, 2 GiB memory/swap, two CPUs, 256 PIDs, bounded tmpfs/files
and a 90-second lifetime. Inputs remain unchanged, no OOM occurs, all containers
are removed and **478 retained session-file hashes** are reverified. Peak
container memory is 208,613,376…405,995,520 bytes, separate from converter memory.

## What this resolves and what remains

The actual original page discrepancy is reproduced and its two exact raster
values are explained by an observed lossy JPEG representation change. The CAJ
and PDF pre-encoding target values agree in every confirmed observed session.
This supports completing #441's reproduce/explain criterion and updating the
scoped #439 receipt and #406 inventory. It does not establish a general readiness
rule, complete all 64 original-viewer pages, validate the aborted session or
prove every earlier renderer stage lossless. Original source fonts/ornaments
and the broader correctness/refusal obligations remain open.

The previously published one-component counterexample still applies: distinct
inputs can share identical JPEG and decoded output. Comparing lossy-normalized
outputs would hide real differences, so no such normalization is used. “A” is
before this observed encoding, without a general source-fidelity guarantee.

All new code is original MIT. No vendor/JPEG implementation, vendor font
program/outline, foreign converter or private HN/JBIG source is inspected or
migrated. Document, PDF, pixel, font, JPEG and binary bodies stay external.
Counts remain **1,252 PASS / 18 FAIL / 27 UNSUPPORTED across 1,297 originals**,
with 35,587 accepted pages. No production/API/output/support change or release.
