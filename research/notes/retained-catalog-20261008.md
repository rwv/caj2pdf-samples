# Retained CAJ catalog and incomplete page tree, 2026-10-08

[Rust #456](https://github.com/rwv/caj2pdf-rust/issues/456) and
[PR #457](https://github.com/rwv/caj2pdf-rust/pull/457) recover the unchanged
78-page CAJ previously rejected at an interrupted metadata declaration.
The [metadata receipt](retained-catalog-20261008.json) retains all source,
build, regression, runtime, independent-reader and scoped-viewer evidence,
including unsuccessful diagnostic attempts and the initial CI installation
failure. The existing identity is updated; the catalog remains **1,297 sources**.

## Source and measured boundary

The [pinned original](https://github.com/caj2pdf/CAJSamples/blob/7e1c35e7b6de34e21972fcd1752c2a7e99b4ad07/issue-25/2.caj)
has SHA-256 `eacbcd00c35a93f049350970d6b5a38010ca5633bdd615deb86db2ce03559444`,
Git blob `393747f96a21852e3d5c42df2a8d1217b2997c6b`, 2,424,052 bytes,
78 pages and 40 source bookmarks. GitHub content metadata and the local Git
blob agree; all original hashes remain unchanged.

Independent framing inventories 423 distinct complete original objects,
201 streams, 12 exact complete duplicates and all 78 table-listed Page objects.
Of 60 full-header interruptions, 56 are exact proper prefixes of complete
copies before the framing CRLF. Of 33 separate non-whitespace gaps, 26 likewise
repeat complete-object prefixes. The other spans include metadata 450, bare or
dictionary parent openers, and parent 209's Count/Kids list ending inside its
fifth child's number. Every affected leaf supplies MediaBox, CropBox, Rotate
and Resources explicitly. The complete graph has no opaque object/xref stream.

Catalog 16 references Pages 12, PageLabels 10, absent AcroForm 434 and
incomplete Metadata 450. Root 12 lists absent nodes 325, 433 and 324. The old
framing script's error about 325 therefore concerns a missing tree node,
not an extra leaf. Nodes 183 and 291 each retain five independent children.
All 78 pages lack annotations. Available labels form one decimal range from
index zero and remain connected to the generated catalog.

[ISO 32000-1:2008](https://raw.githubusercontent.com/adobe/dc-acrobat-sdk-docs/master/docs/standards/pdfstandards/pdf/PDF32000_2008.pdf)
7.3.9–7.3.10 gives undefined optional references null semantics. Complete graph
and incoming-edge checks establish the measured absent targets; this does not
recover unavailable historical form or XML bytes or authorize dropping live
values. Four-, five-, six- and seven-span-muted diagnostics retain later
failures. The eight-span diagnostic passes qpdf but loses the PageLabels
connection, so it is not a correct original compatibility pass.

## Implementation and independent verification

Original MIT code retains the existing ranged scanner, parent reconstruction
and sequential object writer. Catalog/root/label headers and metadata framing
are each bounded to 256 bytes; parent prefixes have the existing 64-byte and
64-record limits. A partial Count/Kids list must match all complete independent
children and stop strictly inside its final number. One complete intermediate
level has at most 64 distinct independent leaves. No inherited value, palette,
stream payload or arbitrary catalog property is guessed. Extra keys, live
optional values, opaque streams and unproved neighboring cases still fail.

The private reconstruction plan carries the retained PageLabels reference.
Public APIs and the existing no-label output path are unchanged. Synthetic
controls cover every successful-path read failure/cancellation, short/changed
reads, role/reference/label guards, 256/257 and 64/65 boundaries, table-order
permutation, labels with and without bookmarks, and failure before output.

Reviewed head is `5f3cf7fb08297ddadfb1cff05e8dcdfe17c037dc`. Frozen CLI SHA-256 is
`d213898ee16a32f0d5304dc96438ffde2402d8135af3b0728a764c1ae8ea41a0`; WASM SHA-256 is
`7e8d90aef49fa4d15e3b95ccc0bc3b207e325b19d777548c81c5cc2665a5e77b`. The unchanged original's output is
`03f312509d1ce5427beabdeed0a5dbfe016e832eab2d6838c9c5ac5296a191d9` on native, Node and Chromium; qpdf and
browser temporary-file cleanup pass. Both previous #452 and separate #449
originals also pass fresh native/Node/Chromium checks with unchanged bytes.

All **421 retained original object values, 201 raw streams, and 78 page
references/geometries/text/link inventories/Poppler RGB renders** match the
independently framed source body. Catalog/root replacement is explicit and
excluded from the retained-object count. All 78 labels agree. An independent
fixed-record CAJ TOC decoder confirms all 40 bookmark titles, depths, order
and targets against MuPDF outline traversal. The complete comparison ran on
the first candidate and applies to the reviewed output by exact PDF hash;
it is not relabeled as a reader rerun.

Seven fresh isolated source-viewer sessions cover original CAJ and independent
PDF pages 1, 53 and 78, plus a painted page-53 negative. Three captures per
session remain available; positive crops agree and the negative changes
484 pixels. Last-page cropping accounts for the scroll limit. Source hashes
stay unchanged, no OOM occurs, and all containers are removed. The full frames
were inspected together and the last-page geometry separately. Other viewer
pages remain NOT_RUN; catalog viewer status remains NOT_RUN for full-document
vendor fidelity and #441 stays open.

## Complete regression and CI

The frozen reviewed-build baseline is **1,277 originals / 2,126 attempts:
1,250 PASS, 18 FAIL, nine UNSUPPORTED**. Only eacbcd changes to PASS.
All **2,098 previous successful attempt hashes** remain identical; all other
refusal diagnostics and cleanup/integrity checks are unchanged. All 1,250
primary successful PDFs pass qpdf. Ancillary order checks remain 288 PASS /
26 FAIL / 936 NOT_RUN; source-outline checks are 299 PASS / 951 NOT_RUN.

The separate 19-input extension is unchanged: one 433-page NH pass and
18 offline CAA unsupported descriptors. The separately cataloged #449 archive
PDF remains byte-identical. Across all **1,297 identities: 1,252 conversion
PASS, 18 FAIL, 27 UNSUPPORTED**. These are conversion statuses, not universal
fidelity or irrecoverability claims; other catalog rows may retain explicitly
pinned older conversion revisions. Prior bitmap/native-text and 1,247-input
JavaScript sweeps retain their actual builds and scoped limitations. Their
fresh output hashes match; no new full-corpus WASM sweep is claimed.

All eight required checks pass at the reviewed head: **1,375 Rust tests**,
seven ignored optional-corpus tests, and **171 JS tests** with no skips.
Coverage is **98.51% (30370/30828)** against the
configured 90% floor. The initial x86_64 musl job timed
out before compilation while apt-get downloaded mupdf-tools. The failed log
and job remain recorded; one targeted same-head rerun passes without changing
code, timeout or gates. The initial parent-space unit-test failures are also
retained separately; the final boundary and control tests pass.

Review is documented self-review and simplification, not independent human
approval. No external document/PDF/text/render/font bytes, foreign converter,
private HN/JBIG or vendor implementation code is committed. No release occurs.
The remaining palette, credential, truncated-input, unsupported-format,
C8/HN-B outline and general viewer evidence boundaries remain separate.
