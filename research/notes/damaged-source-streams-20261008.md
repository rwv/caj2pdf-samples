<!-- SPDX-License-Identifier: MIT -->

# Damaged source streams behind the issue-20 warning

Later evidence: a [checksum-confirmed substitution candidate](stream-substitution-candidate-20261008.md)
restores all six original checksums and page-table offsets. The observations
below retain the earlier unchanged-source baseline; production recovery is
still unimplemented and #436 remains open.

[Rust #436](https://github.com/rwv/caj2pdf-rust/issues/436), under
[#406](https://github.com/rwv/caj2pdf-rust/issues/406), remains open. The
accepted 63-page conversion preserves six already damaged source streams.
This investigation establishes their original bytes and affected resource
paths, but does not establish a deterministic repair or intact intended
content. Conversion exit zero is not a complete fidelity pass.

The [measurement receipt](damaged-source-streams-20261008.json) records the
pinned CAJSamples `issue-20/文件名未知.caj`, upstream revision
`7e1c35e7b6de34e21972fcd1752c2a7e99b4ad07`, SHA-256
`5a4432ed4878944c4aaa17f591b2a93d00014ea0bdacc9162bed1d88f8d61127`,
983,523 bytes. All source, PDF, decoded content, fonts, pixels and vendor
executable bytes remain outside Git.

## Independent framing and codec inventory

An original MIT probe independently locates all 260 generation-zero object
headers and 87 streams. It copies source body `[37868,983323)` verbatim,
including original declared lengths, and gives every original object an
explicit xref slot. No object is omitted or replaced. The CAJ page table's
last nominal end, 983295, cuts into the final stream: it is not a valid body
boundary. The final complete stream/object terminator precedes the source
XML trailer at 983323.

Original Parent relationships and table page IDs determine two missing
Pages ancestors, 229 and 230. The probe adds only these, their common root
271 and Catalog 272. All 63 page IDs and order match the source table. No
converter output informs object selection, codec extents or page order.

Of 84 Flate streams, **78 pass strict zlib decoding**, five reach raw
DEFLATE EOF but fail their stored Adler-32 checksum, and one fails before
EOF with invalid code lengths. Three DCT streams have complete JPEG extents
and decode without Pillow warnings. Their bytes, dimensions and decoded
hashes are retained in the receipt.

| Source stream | Declared Length | Complete zlib extent | Decoded bytes | Source defect and registered resource scope |
| --- | ---: | ---: | ---: | --- |
| 4 | 40,020 | 40,021 | 3,010,630 | Bad checksum; page 2 image |
| 9 | 67,215 | 67,216 | 2,904,204 | Bad checksum; page 3 image |
| 13 | 103,841 | 103,846 | 2,928,237 | Bad checksum; page 4 image |
| 53 | 212,747 | Not established | Not established | Invalid DEFLATE code lengths; font resource on pages 5–63 |
| 269 | 18,383 | 18,386 | 139,680 | Bad checksum; font resource on page 5 |
| 142 | 4,585 | 4,586 | 17,738 | Bad checksum and malformed content operators; page 39 |

Resource paths come from parsed original page/content/font references,
excluding Parent/P backedges. Registration alone does not prove that every
font executes on every listed page. The content stream 142 is directly used
by page object 140; its resources reference fonts 59, 49 and 47 and graphics
state 46.

Stream 142 begins at source offset **880636**. Raw DEFLATE consumes 4,580
bytes after the two-byte zlib header and reaches EOF. Its stored Adler-32 is
`deae043d`; the independently computed value is `4dd63b40`. The complete
4,586-byte zlib frame is followed by LF, CR, LF and the exact stream/object
terminator. The converter's 4,587-byte payload is exactly the source frame
plus LF. Its decoded hash matches the independent raw-DEFLATE result.
The checksum failure and malformed operators are present before conversion.

Qpdf exits **3** for both independently framed and produced PDFs. The former
also recovers six incorrect declared lengths. Both report the same 24
`unexpected )` content warnings on page 39 at decoded offsets
11018–17384. Qpdf's warning inventory alone did not reveal all six codec
defects; its original one-warning-output corpus classification remains
unchanged rather than becoming a clean validation result.

Acceptance follows the deliberately codec-free framing introduced by
[Rust PR #369](https://github.com/rwv/caj2pdf-rust/pull/369): a confirmed
Length or the bounded understated-Length rule frames opaque payload bytes
without inflating them. That breaking change explicitly permits codec-only
defects previously rejected by v0.4.0. This investigation neither reinstates
that historical policy nor attributes the existing outcome to PR #435.

A bounded diagnostic tried deletion of each adjacent two-byte span at 4,579
positions inside stream 142, requiring strict checksum/EOF and at most 1 MiB
of decoded output. It found no candidate. This rejects only that narrow
diagnostic hypothesis; it is neither a repair policy nor proof that all
recovery is impossible. No source bytes were changed.

## Viewer evidence and its limits

Seven fresh offline CAJViewer 9.0.0 sessions use one document per container.
The receipt pins the cached image and containment: no network, read-only,
non-root, dropped capabilities, no new privileges, 2 GiB memory/swap, two
CPUs, 256 PIDs and a 90-second external deadline. All captures are stable,
input hashes unchanged, no OOM occurs and every container is removed.

The original CAJ fails to reach requested page 39 in **three attempts**,
including longer settling time and a capture showing `39` entered before
Return. It settles at displayed page 2 with part of the cover. A next-page
click does not advance that display. These are failed navigation attempts,
not source-viewer fidelity passes. A separate unchanged 60-page CAJ control
(`dc3c3a…`) reaches page 39 using the same workflow.

The independently framed and produced PDFs both reach page 39. Their
complete first-page crops `[626,156,1023,718]` at 50% zoom match exactly,
with no rescaling or alignment. A deliberate diagnostic replaces only
content stream 142 with an empty stream before saving an external PDF. Its
page 39 is visibly blank and differs from the framed source by **20,839
pixels / 62,517 RGB channels**. This validates sensitivity to content removal,
but cannot supply the missing intact source-page expectation.

The [upstream report from 2018](https://github.com/caj2pdf/caj2pdf/issues/20#issuecomment-419617601)
also describes the attachment as damaged in CAJCloudViewer for Mac and says
a freshly downloaded version converted successfully. This is historical
context, not a fresh test or a verified intact alternative. No alternative
document bytes were obtained here, and no access-controlled endpoint was
contacted.

## Whole-document preservation and runtime parity

Against independent framing, all **260 original object values** agree after
excluding only stream Length fields. All **87 output stream payloads** equal
the original source bytes at their independently located offsets; each is
followed by the same CRLF before `endstream`. All 63 page identities,
effective boxes/rotations, MuPDF-extracted texts and links agree. Extracted
text equality includes the source's damage and font fallback; warnings on
five raw-framing pages and two output pages remain recorded as counts/hashes.
Shared renderer caches mean these warning counts are not resource-use counts.

All **63 Poppler RGB72 page images** are equal. Both rendering commands exit
zero while emitting errors: **11,546** raw-framing and **6,908** output
`Syntax Error` lines. Full stderr stays external; the receipt records its
byte counts and hashes. Identical damaged renders do not establish the
intended images, fonts, glyphs or content.

A fresh native conversion at the previously tested production revision
`20292ab805a9d2cef066270af549635dce753dc5` exits zero and produces 969,020
bytes, SHA-256
`58fc31644f1363fa695112bf2deb71e4069e990f53199e610938b31dc8052e6d`.
Fresh Node and Chromium conversions produce exactly these bytes and 63
pages; Chromium removes its OPFS input/output artifacts. The output has 93
bookmarks. Their independent source comparison passed in the
[pinned full regression](https://github.com/rwv/caj2pdf-samples/blob/26720c5d76fbb05b39400a65b35b3974b31c1931/research/notes/redundant-caj-framing-20261008.json);
that proof applies to the identical current output bytes. The source
bookmark decoder was not re-executed in this investigation.

There is no production change. The full 1,277-original / 2,126-attempt corpus
was not rerun here; its counts remain 1,240 PASS, 28 FAIL and nine UNSUPPORTED,
with this output's warning and missing original-viewer proof retained.
This sample adds no new compatibility pass.

## Review and remaining work

This is original MIT observation, framing and reporting work. No foreign
converter implementation, private HN/JBIG code, vendor implementation or
document-derived source code was read, copied or translated. Tools operate
on externally stored source/diagnostic files; public receipts contain
metadata and hashes. No dependency, production/API/output policy or supported
format changes are proposed.

Self-review reconciles every object/stream/page count and runtime hash with
the receipt. It keeps the three failed source-viewer attempts, codec failures,
renderer diagnostics and absent full regression explicit. This is self-review,
not independent approval. #436 stays open: an intact alternative or another
independent semantic oracle is still needed to justify recovery. These six
concrete source defects do not prove the whole document irrecoverable.
