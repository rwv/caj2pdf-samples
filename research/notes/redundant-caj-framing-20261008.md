<!-- SPDX-License-Identifier: MIT -->

# Recovering proved redundant CAJ framing

The unchanged 60-page original in [Rust #409](https://github.com/rwv/caj2pdf-rust/issues/409)
and [#434](https://github.com/rwv/caj2pdf-rust/issues/434) converts through
native, Node.js and Chromium with identical output bytes. The
[measurement receipt](redundant-caj-framing-20261008.json) records the exact
production commit, source identity, independent framing, full-page comparison,
source-viewer checks, regression ledger and required CI. The implementation is
[PR #435](https://github.com/rwv/caj2pdf-rust/pull/435), under the wider
[#406](https://github.com/rwv/caj2pdf-rust/issues/406) correctness work.

Source: [CAJSamples `issue-90/4-[6].caj`](https://github.com/caj2pdf/CAJSamples/blob/7e1c35e7b6de34e21972fcd1752c2a7e99b4ad07/issue-90/4-%5B6%5D.caj),
SHA-256 `dc3c3a651d4abaea61b8982e5165636f61b85f2c48f2eace3c6730e00dd963d3`,
3,491,634 bytes. Its source page table identifies 60 pages; the independently
decoded bookmark table has 36 entries. No document bytes are redistributed.

## Four distinct framing facts

1. Object 229 declares 98 bytes: 97 complete Flate bytes plus LF. CR and SPACE
   then precede the exact stream/object terminator. Retaining the declared
   payload avoids an unnecessary Length change from 98 to 100. The fix admits
   at most 64 PDF whitespace bytes at an already established extent.
2. A classic xref/trailer/startxref/EOF block occupies `[2911107,2911776)`.
   After its CR, **all 3,733 bytes** at `[2911777,2915510)` decode to original
   header `[144,3877)` under the measured FZHMEI cycle, phase 2. CRLF is followed
   by integer 4478 at 2915512, value 1592527. That equals complete image 4479's
   measured encoded extent. Old xref offsets and Root are stale; no old offset
   is treated as a current object boundary.
3. Image 4474 at 1314164 has a complete Image/Flate/RGB dictionary but only
   **3,276 payload bytes** before CRLF and integer 4468 at 1317618. Those bytes
   equal a proper prefix of complete image 4479; the dictionaries agree except
   for their Length references. The complete parsed graph has no incoming
   reference to 4474. This does not reconstruct or establish its absent tail.
4. `[2954967,2954978)` contains only the unfinished `4448 0 obj<` opener.
   CRLF then complete font 4459 follows. There is no complete 4448 or incoming
   reference. The later interrupted 4459 and 29 other metadata interruptions
   are exact prefixes of complete same-ID objects.

The missing tail of image 4474 is never invented. It is omitted only after
exact prefix/boundary proof, independently anchored counterpart confirmation
and complete-reference validation. A referenced interruption, meaningful
unmatched value, opaque metadata stream, partial graph, conflicting candidate,
changed source or unmeasured profile remains an error. This is not a general
policy of deleting unused malformed objects.

## Independent whole-document evidence

Original MIT framing copies the entire body `[47940,3491634)` verbatim,
including interrupted bytes and the old epilogue. A new xref selects **395
complete object identities**. Five complete duplicate occurrences agree.
Seven missing Pages ancestors and a new root/Catalog are generated solely
from original Parent links and CAJ page-table order. Qpdf accepts the framing
without warnings. Its SHA-256 is
`0c3103e5b518fbbb9270def606828a401a3e8088144dd503ea3477e9d6ea728e`.

Early diagnostics replaced only three measured redundant ranges with equal
width whitespace: `[1314164,1317618)`, `[2911107,2915512)` and
`[2954967,2954980)`. The receipt verifies that no other input byte changed.
Those diagnostic conversions isolated scanner behavior; they were not counted
as unchanged-original successes. Final native conversion of the unchanged CAJ
produces the identical 3,532,003-byte PDF, SHA-256
`743afde6eb64ea8673b066a5d4320beb4f227b7199f37e8bfc92374f75e27d23`.

Against independent framing:

- All 395 selected object values and **189 distinct raw streams** agree.
- All 60 page IDs/order, effective boxes, rotations, extracted text and links
  agree. Poppler RGB72 rendering agrees on **60/60 complete pages**.
- All 36 bookmark title hashes, hierarchy and destinations agree with the
  separate CAJ table decoder.
- Qpdf exits 0 on the final output. Native, Node and Chromium hashes agree;
  Chromium leaves no OPFS temporary files.

Two complete image extents were independently checked with bounded zlib
inflation. Image 4469 consumes 1,265,537 encoded bytes and yields 6,068,790;
4479 consumes 1,592,527 and yields 3,466,638. Image 4469's dictionary declares
1,183 × 1,706, while its decoded RGB byte count includes four additional rows.
This existing discrepancy is retained, not silently normalized. Image 4474
fails inflation at the interruption. An initial 4 MiB probe stopped at its
output bound; an 8 MiB probe establishes both complete streams. Neither the
bounded refusal nor interrupted-stream failure is counted as a codec pass.

## Source viewer and scope

Nine fresh, offline CAJViewer 9.0.0 sessions compare the unchanged original,
independently framed PDF and diagnostic PDF on pages 1–3 at 50% zoom. Each
session opens one document and captures two stable screenshots. Filename,
page number, zoom and page edges were visually inspected. All three document
forms have identical full-page RGB crops `[626,156,1023,718]` on all three pages.
Final unchanged-source output equals the diagnostic PDF byte for byte.

The cached viewer image is
`cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de`.
Every container is offline, read-only, non-root, capability-dropped, limited
to 2 GiB memory/swap, two CPUs and 256 PIDs, with bounded temporary storage and
a 90-second external deadline. All input hashes remain unchanged; no session
is OOM-killed and every container is removed. This is **three-page vendor
viewing**, combined with all-page independently framed PDF comparison. It is
not whole-document CAJViewer rendering or proof that rendering libraries have
independent implementations.

## Final implementation and regression

Production commit `20292ab805a9d2cef066270af549635dce753dc5` uses bounded ranged
reads and sequential output. The epilogue is limited to 4 KiB/128 entries and
five exact trailer fields. The duplicate header must match at least 128 and
fewer than 65,536 bytes. Image headers and adjacent metadata objects are capped
at 256 bytes; image prefixes must match at least 256 and fewer than 65,536
bytes. At most 64 eligible image candidates and 64 unused interruptions are
admitted. Prefix checks use at most 256-byte chunks and smaller configured
I/O sizes. Complete-graph proof rejects object/xref streams that could hide
unparsed references. Source/header/prefix checks are repeated before omission.

Original controls cover fake markers in opaque data, referenced orphans,
string lookalikes, hidden and duplicate candidates, incomplete graphs,
malformed/overflowing profiles, short reads, source mutation, bounds and every
cancellation checkpoint. **1,306 workspace tests pass**, with seven optional
corpus tests ignored and explicitly not counted as compatibility passes;
**166 JavaScript tests pass** with no skips. Formatting, strict Clippy, locked
native/WASM builds and all eight required CI statuses pass.

The first candidate incorrectly classified a fixed whitespace-recognition
bound as a resource-budget failure. Existing JavaScript replay controls
caught that when a bad Length landed in a later stream's whitespace payload.
The final rule still stops after 64 bytes but reports a framing mismatch,
allowing independently proved replay recovery. Caller resource-budget and
cancellation errors still propagate. The Rust replay control also now covers
opaque spaces. This review finding is resolved in the tested commit above.

The final receipt records a fresh **1,277-original, 2,126-attempt native run**,
including source integrity, failed-output cleanup and previous-success PDF
hash comparisons. The only conversion change is this original, from
UNSUPPORTED to PASS; all previously successful outputs are byte-identical.
The default conversion counts are **1,240 PASS, 28 FAIL and 9 UNSUPPORTED**.
Detailed qpdf/page-order/outline outcomes and unexecuted pixel checks remain
in the ledger and are not flattened into conversion PASS.

The frozen harness still labels 26 page-order checks FAIL and 936 NOT_RUN.
Those labels are preserved alongside the prior
[26 applicable ordering checks](https://github.com/rwv/caj2pdf-samples/blob/f765b4b8bc552cc130f8b9c7d4cb8f287d92077c/research/notes/native-content-order-20261008.md)
and [936-source image/text evidence](https://github.com/rwv/caj2pdf-samples/blob/38a9bd62b32e198444e6596106e6e2db309834c4/research/notes/github-bitmap-oracles-20261008.md).
A fresh identity check confirms every corresponding final PDF hash matches
those pinned receipts. Their scoped proofs and exclusions apply to these same
bytes; this does not claim another execution of their external decoders or
new placement/font/vector/rendering proof. Qpdf reports 1,239 PASS and one
unchanged WARNING among successful conversions. The raw outline checker
reports 290 PASS and 950 NOT_RUN, not universal source-outline verification.

The newer catalog adds 18 CAA target descriptors and one NH document outside
that frozen ledger. Fresh native checks retain all 18 intentional descriptor
refusals without decoding/resolving opaque values. The 433-page NH still has
identical native/Node/Chromium output, qpdf passes and OPFS cleanup succeeds.
Its source-viewer pixels remain NOT_RUN. These 19 entries remain separately
identified; descriptors are not counted as successful document conversions.

Review and simplification are self-review, not independent approval. The
unchanged-source success does not resolve all remaining #406 samples or prove
that every other refusal is impossible. No release is performed here. All
committed Rust, synthetic controls and measurements are original MIT; external
documents, derived PDFs, page text, pixels, fonts, vendor binaries, credentials
and foreign converter implementation remain outside the repositories.
