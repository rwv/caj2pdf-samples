# Proved interrupted CAJ copies, 2026-10-08

[Rust #442](https://github.com/rwv/caj2pdf-rust/issues/442) and
[PR #443](https://github.com/rwv/caj2pdf-rust/pull/443) recover three unchanged
originals with complete counterparts for interrupted object copies. The
[per-input receipt](interrupted-copies-20261008.json) records source identities,
all-page comparisons, graph proof, runtime checks and the native regression.
The parent [#406](https://github.com/rwv/caj2pdf-rust/issues/406) remains open;
other refusals are not declared impossible.

Reviewed production head: `c88cc8d44c4a8eadfe9f77020c3fc56d71107aef`, based on
merged `d9049b6ea34c3933b7f559a3b8d6c0ac59d6a141` (#440). Locked release native
and WASM artifacts were frozen externally before the final regression. Their
hashes and exact-head CI are in the receipt. No release.

## Measured sources and recovery

| Original SHA-256 prefix | Source | Bytes | Pages / bookmarks | Complete objects / raw streams |
| --- | --- | ---: | ---: | ---: |
| `cb6f5e781f37` | ZERO-A-ONE/FZU-IS-404 | 1,370,800 | 182 / 30 | 586 / 195 |
| `f65742f37f10` | qinzc1993/caj2pdf-actions | 1,127,592 | 47 / 24 | 179 / 65 |
| `f26570f28a20` | CAJSamples issue-85 Mingtang | 5,990,802 | 234 / 111 | 857 / 344 |

Pinned revisions and source URLs accompany full hashes in the receipt. The
first source requires partial-boolean recovery for ExtGState 593 and a
487-byte stream-606 prefix. The second requires a 360-byte stream-4 prefix
and a partial negative number in FontDescriptor 157. The third requires nine
stream prefixes, the terminal header `792 0`, and the unused payload-free
unfinished declaration 853. Its font 792 has a retained complete object;
it is not treated as an unused object.

Every non-whitespace gap between independently framed complete objects is
inventoried: 445 exact proper prefixes and the sole unmatched declaration 853.
There are also 47 complete duplicate occurrences. Complete stream counterparts
have declared/resolved Lengths and exact terminators. The new stream prefixes
repeat complete headers and actual payload bytes, not just matching IDs.

Recovery compares at most 64 KiB through two at-most-256-byte buffers, honors
smaller I/O chunks, and validates the adjacent next object after at most 64
non-NUL spacing bytes. It accepts either an already framed copy or a unique
later page-row candidate. Rows are collected once each, from last to first;
the complete scan must reach every used candidate at its exact range. Distant
copies use positioned reads without widening ordinary syntax/search windows.
Conflicting copies, hidden candidates, changed sources and unproved boundaries
remain errors. Existing graph reconstruction and sequential output are reused.

The one unused declaration is strictly limited to the measured unfinished
Length/Filter syntax, with no stream keyword or payload. Complete-graph checks
reject incoming references, complete same-ID objects, damaged/uninspectable
objects and opaque metadata streams. Additional keys, content and unmeasured
endings do not qualify. Ordinary indexed PDFs remain strict.

## Independent content and graph evidence

An independent PDF framing retains the entire original CAJ body verbatim,
including interruptions, and xref-selects complete objects. Only missing page
tree/catalog/xref framing is synthesized from original Parent links and the
CAJ page table. Every retained object value and raw payload agrees with
conversion of the unchanged original: **1,622 objects and 604 streams**.
All **463** page identities, boxes, rotation, text, links and Poppler RGB72
renders agree; all **165** original bookmarks agree. Qpdf accepts every output
and independent framing. These runs record no MuPDF warnings or Poppler stderr.

An independent structural walk proves no incoming reference to missing ID
853. A separate external diagnostic first adds a sentinel at that ID, preventing
missing references from silently becoming null during parsing. A deliberately
injected nested indirect reference is detected by the same walk. No encrypted
or opaque metadata stream is present. Page/resource paths are also inventoried;
reachability is not presented as proof that every resource is executed.

Early equal-width omission experiments remain diagnostic isolation, separate
from unchanged-source conversion. Incomplete attempts are retained as failures.
An unrelated declaration-chain experiment misread suffixes of object numbers
because it searched a sliced probe; the corrected full-probe experiment still
fails, and neither source is promoted to PASS. Incorrect preliminary bookmark
fields are excluded; the source-derived 165-bookmark check is authoritative.

Native, Node.js and Chromium produce byte-identical PDFs for all three
unchanged originals on the final reviewed build. Chromium uses ranged OPFS
input and sequential output, and removes all temporary entries. This is
three-original runtime evidence, separate from the full native regression.

## Scoped original-viewer comparisons

Nine fresh offline CAJViewer sessions compare original-source pages **1, 64
and 2**, their native PDFs, and deliberate black-rectangle controls. Visually
checked 1600x1200 frames show the requested pages at 50%; crop
`[626,156,1023,718]` includes the complete current page and its edges. Captures
at 3, 10 and 12 seconds agree. All three original/native page crops match
exactly; each changed-content control differs by **1,980 pixels**.

All sessions use the pinned image, network none, read-only root/inputs,
non-root user, dropped capabilities, 2 GiB memory/swap, two CPUs, 256 pids and
a 90-second hard lifetime. Source hashes stay intact, no OOM occurs, and every
container is removed and verified absent. Screenshots remain external.
These selected-page checks do not establish whole-document vendor fidelity
or resolve the earlier cold-session repeatability limitation in
[#441](https://github.com/rwv/caj2pdf-rust/issues/441).

## Regression, review and limitations

The final **1,277-original / 2,126-attempt** native run has **1,246 PASS,
22 FAIL and nine UNSUPPORTED**. Exactly these three originals become PASS.
All **2,092** previously successful attempts retain their PDF hashes; no
conversion regresses. All 1,246 primary outputs pass qpdf. Source integrity
and failed-output cleanup pass throughout. Remaining refusal diagnostics
are retained individually.

The older ancillary checker reports 284 page-order PASS, 26 FAIL and
936 NOT_RUN; outlines have 296 PASS and 950 NOT_RUN. The separate pinned
26-document native and 936-document bitmap/glyph oracle evidence applies to
freshly verified identical PDF hashes. Those decoders were not rerun and do
not become new whole-document viewer proof. Their prior limits remain.
The extended rerun preserves the added 433-page NH PDF and 18 unsupported CAA
offline descriptors; no opaque target value is decoded, logged or contacted.
That NH's original-viewer pixels remain NOT_RUN.

Nine new original MIT test groups cover earlier/later copies, chained anchors,
hidden candidates, boundaries, source changes, short I/O, cancellation/limits,
partial syntax/EOF, unused declaration neighbors and indexed PDFs. The final
exact-head CI passes **1,340 Rust tests**, with **seven optional corpus tests
ignored**, and all eight required quality/Linux checks. Measured line coverage
is **98.67% (29,224/29,619)** against the configured 90% floor; the historical
job label does not imply 100%. All **166 JavaScript tests pass with zero skips**.
An initial local JS run lacked the helper's default target path; staging the
same frozen WASM and rerunning resolved that harness setup failure without
changing code. It is not counted as a pass.

[Final self-review](https://github.com/rwv/caj2pdf-rust/pull/443#issuecomment-6061481873)
preserved rejection of a changed NUL byte, consolidated prefix
comparison, and kept distant-copy reads separate from ordinary syntax windows.
Final simplification avoids repeatedly resetting/traversing accumulated
candidate flags during row pre-scans; only complete scans need that bookkeeping.
Affected core tests, builds, runtime checks, exact-head CI and the full corpus
were rerun afterward. This is self-review, not independent approval.

Only original MIT code, authored synthetic controls and observation metadata
are committed. No external document/PDF/text/pixel/font/vendor bytes or foreign
converter implementation enter Git. Other #406 failures and fidelity gaps
remain open; parser refusal alone is not proof that conversion is impossible.
