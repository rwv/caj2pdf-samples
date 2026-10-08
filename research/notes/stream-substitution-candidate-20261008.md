<!-- SPDX-License-Identifier: MIT -->

# A checksum-confirmed candidate for the issue-20 damage

Follow-up to [the original damaged-stream inventory](damaged-source-streams-20261008.md)
for [Rust #436](https://github.com/rwv/caj2pdf-rust/issues/436). A new diagnostic
candidate restores all six original Flate checksums and all 63 original page
offsets. This advances the earlier unknown-reconstruction result, but is not
yet a production repair or an unchanged-input compatibility pass.

The [metadata receipt](stream-substitution-candidate-20261008.json) pins all
source/diagnostic hashes, byte offsets, codec results, font table checks,
viewer observations and unrun scopes. Source SHA-256 remains
`5a4432ed4878944c4aaa17f591b2a93d00014ea0bdacc9162bed1d88f8d61127`.
All document, PDF, text, pixel and font bytes remain external.

## Candidate and independent constraints

The four-byte sequence `ca a7 c2 e4` occurs **13 times**, exclusively inside
the six damaged streams: once in 4, once in 9, three times in 13, five times
in 53, twice in 269 and once in 142. The counts account for every extra byte
relative to their original Length values when each occurrence is replaced
by two bytes. No occurrence is in a previously valid stream or metadata.

For stream 142, an exhaustive diagnostic tries all **65,536** possible
two-byte replacements at its one occurrence, preserving every other byte
and the original stored Adler-32. Strict zlib EOF/checksum and a 1 MiB decoded
cap admit exactly one candidate: `b5 f4`. Uniqueness is proved only within
this explicitly delimited candidate family, not among arbitrary edits.

Applying that same candidate to all 13 occurrences gives six strict zlib
passes without changing any stored checksum or length. Each complete encoded
frame plus LF exactly equals its original declared Length. Decoded images
4/9/13 have exactly their measured 8-bit, one-component Width × Height sizes:
3,010,434 / 2,903,865 / 2,926,720 bytes. Fonts 53 and 269 have exactly their
original Length1 values, 485,792 and 139,576; all **22 stored sfnt table
checksums** agree independently. The fonts load with 22,141 and 22,021 glyphs.
Content 142 becomes 17,762 decoded bytes and no longer produces qpdf syntax
warnings.

The diagnostic CAJ changes only those 13 occurrences. It leaves the header,
page table, object dictionaries, lengths and checksums untouched, shrinks
from 983,523 to **983,497 bytes**, and has SHA-256
`d5a23e59ad27807d8b8fbc9271dd9e4857d7c01c31a2682b014a13861b340a15`.
Every one of the **63 original page-table offsets** now points exactly to
its original page object header. No table offsets were recomputed to make
the diagnostic agree.

This is a measured four-to-two-byte substitution hypothesis. The process
that originally damaged the file is not established. It does not authorize
unconditional replacement of these bytes in other files or valid streams.

## Observed recovery and remaining production work

The existing converter accepts the diagnostic CAJ and produces a 968,994-byte
PDF, SHA-256
`cb4e6a918e633a57c6bb76f0a984cf9c3b8b0155ae55cac7171f14a94ba04ec4`.
Qpdf exits **0** without warnings. Poppler renders all **63 pages**, exits
zero and produces **zero stderr bytes**, compared with thousands of source
errors before the substitution. The converter itself has not changed.

The six changed stream hashes match the measured substitutions; all other
**81 stream payloads** are byte-identical to the original conversion. All
63 page IDs, boxes, rotations and links, plus all **93 bookmarks**, remain
identical to that conversion. This is an explicit change to damaged data,
not raw-payload identity for all 87 streams.

Six fresh offline CAJViewer sessions compare the diagnostic CAJ with its PDF
on pages **3, 5 and 39**. They use the same pinned image and containment as
the original inventory. Filenames, page indicators and complete page edges
were visually inspected; two captures per session are stable, input hashes
unchanged, no OOM occurs and all containers are removed. All three paired
page crops `[626,156,1023,718]` at 50% zoom agree without alignment or
rescaling. Page 39 now navigates successfully and shows the chart absent in
the damaged output. These are modified-source comparisons, not observations
of an independently obtained intact alternative or all-page vendor proof.

#436 remains open for a bounded, reviewed recovery policy. Before production
use, positive original MIT controls and strict neighboring refusals must
establish that valid payloads, wrong replacement candidates, incomplete
checksums, ambiguous or excessive occurrences, changed sources, limits and
cancellation cannot trigger an unsafe transformation. Required validation
also includes unchanged-original native/Node/Chromium conversion, full corpus
regression and CI. None is replaced by this diagnostic result. Diagnostic
Node/Chromium parity is NOT_RUN; only native conversion is measured here.

This report and receipt are original MIT work. No foreign converter or
vendor implementation, private HN/JBIG code or document-derived source code
was used. Self-review checks the 13/6/63/81/93/22 counts and distinguishes
original metadata constraints from manufactured expectations. There is no
new production/API/dependency/output policy or release in this evidence PR.
