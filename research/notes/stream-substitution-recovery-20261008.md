<!-- SPDX-License-Identifier: MIT -->

# Bounded recovery of the issue-20 stream damage

[Rust PR #438](https://github.com/rwv/caj2pdf-rust/pull/438), for
[#436](https://github.com/rwv/caj2pdf-rust/issues/436), turns the
[previously measured candidate](stream-substitution-candidate-20261008.md)
into a bounded production recovery. The unchanged original now yields the
same clean 63-page PDF as that diagnostic. This is a correctness improvement
to an already accepted input, not another newly convertible document.

The [metadata receipt](stream-substitution-recovery-20261008.json) pins final
code `f2e88c3721e65bfa376853f99cc6151f6cf785d1`, native/WASM hashes,
all-page comparisons, full native outcomes, required CI and review. External
CAJ/PDF, text, pixels, fonts and vendor binaries are not included.

## Admission and implementation

Only uniquely framed, understated direct-Length streams with exactly a
simple FlateDecode filter qualify. The original codec must fail; a valid
prefix, even with trailing bytes, forbids substitution. Replacing every
admitted `ca a7 c2 e4` by `b5 f4` must recover the unchanged zlib checksum and
exact original Length including LF. Sites cannot overlap the zlib header or
checksum. Ambiguous, incomplete, parameterized and external stream profiles
cannot enable rewriting.

The complete scan must still select all candidate objects and contain no
unresolved damage. Every original page-table anchor must match the shortened
view, and at least one offset must move. No metadata, Length, checksum or
page-table entry is edited to manufacture evidence. Only admitted stream
sites change; the identical marker in unrelated metadata is preserved.

The core retains positions and SHA-256 digests, never whole streams or input.
Each codec/hash buffer is 4 KiB and requests honor the caller's chunk limit.
The profile caps encoded extents at 256 KiB, decoded work at 4 MiB and
candidate streams at 64, with the existing 64-byte Length-repair bound.
Caller allocation limits also apply. Source digests are rechecked after
recognition, before conversion and after successful emission; marker bytes
are checked on every read. Cancellation and source error kinds/physical
offsets survive the sparse view. Initial indexes are released before its one
ordinary rescan and graph reconstruction. Input must remain stable and
callers must discard partial output on error.

Seventeen original MIT controls cover positive pixel recovery, exact
clean/damaged output equality, metadata preservation, one-byte/short reads,
4 KiB window boundaries, candidate/filter/generation exclusions, all-page
anchors, unresolved objects, encoded/decoded/document budgets, complete
cancellation checkpoints and persistent non-marker changes during output.
No foreign converter or vendor implementation was consulted or migrated.
The existing flate2 dependency supplies standard zlib decoding.

## Unchanged original and independent comparisons

Source SHA-256 remains
`5a4432ed4878944c4aaa17f591b2a93d00014ea0bdacc9162bed1d88f8d61127`,
983,523 bytes. Native, Node and Chromium all produce **968,994 bytes**, SHA-256
`cb4e6a918e633a57c6bb76f0a984cf9c3b8b0155ae55cac7171f14a94ba04ec4`,
with **63 pages and 93 bookmarks**. Browser OPFS cleanup passes. Qpdf exits
zero without warnings.

A fresh independently framed PDF of the established diagnostic source has
**260 objects and 87 streams**, all 84 Flate checksums valid. It agrees with
the unchanged-original production output on all object values except stream
Length, all expected payloads, page identities/order, geometry, extracted
text and links. Both **63-page Poppler RGB72 runs** have zero stderr and
identical page pixels. Six payloads explicitly change at the measured 13
sites; the other **81 streams** retain original bytes. The fresh corpus
harness independently confirms the source's 93 bookmarks.

This framing expectation comes from the earlier source measurements, not
from converter output. It is still a reconstructed candidate, not an
independently obtained intact original. Six previously pinned vendor sessions
cover only modified-source/PDF pages **3, 5 and 39**, and apply to the
byte-identical PDF; those sessions were not rerun. Original damaged-source
navigation never reached page 39. Those failed scopes remain recorded, and
no full-document vendor-render proof or corruption-cause claim follows.

## Final regression and review

The fresh final-build run covers **1,277 original files and 2,126 attempts**:
**1,240 PASS, 28 FAIL and nine UNSUPPORTED**. Every previous conversion
classification is unchanged. Only issue-20's PDF bytes change; its qpdf
warning becomes PASS, giving **1,240 qpdf passes** among accepted originals.
All other successful PDFs are byte-identical. Every input hash is stable,
and failed attempts leave no PDF. Skipped checks are not compatibility passes.

The extra catalog inputs also retain their outcomes: one 433-page NH yields
the identical PDF, and 18 CAA files remain unsupported offline descriptors.
No opaque target value is decoded, logged or resolved. The NH's source-viewer
pixels remain NOT_RUN. These 19 inputs are separate from the frozen ledger.

The ledger deliberately retains old ancillary states: 278 source-order PASS,
26 legacy FAIL and 936 NOT_RUN, and 290 outline PASS / 950 NOT_RUN. The
[26 applicable native-content rechecks](native-content-order-20261008.md) and
[936 bitmap/glyph checks](github-bitmap-oracles-20261008.md) are separately
pinned. Every associated PDF hash still matches the final run; this is fresh
byte identity, not a new external-oracle execution or whole-page fidelity
claim. Remaining refusals are not classified as impossible.

Local validation: **1,323 Rust tests pass**, with **seven optional-corpus
cases ignored and excluded**; all **166 JavaScript tests pass with no skips**.
Format, strict clippy, rustdoc, documentation links, source inventory and
locked native/WASM builds pass. The receipt records all eight required
quality/Linux checks for the final head. Its review is explicit self-review,
not independent approval: I/O clipping, error preservation and index lifetime
findings were resolved before the final run. No API, dependency or release
change is included.
