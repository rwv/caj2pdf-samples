# Collection research

The [2026-10-09 historical Windows CAA investigation](research/notes/caa-windows-boundary-20261009.md)
adds primary institutional link-file guidance and offline observations for all
18 descriptors, with original controls and retained Wine/installation limits.
This updates the older link-file lead below; remote availability, credentials
and actual target-document conversion remain unverified.

The [2026-10-08 CAA/NH discovery](research/notes/caa-nh-discovery-20261008.md) adds 18 descriptors and one
original-extension HN-A document, with offline viewer and complete
CLI/Node/Chromium results. It supersedes the earlier CAA/NH sample gaps;
CAS remains open in [#28](https://github.com/rwv/caj2pdf-samples/issues/28).

## Initial discovery, 2026-10-04

- Existing corpus: https://github.com/caj2pdf/CAJSamples at
  `7e1c35e7b6de34e21972fcd1752c2a7e99b4ad07`.
- Catalog metadata imported from the original MIT project's
  `tests/conformance/matrix.json` at `c3c9d8757468b32ab50ed5a982019a6336ea9d5f`.
  Historical conversion outcomes were deliberately not imported as current passes.
- Searched public web results for TEB, CAA, CAS and NH document samples, and
  reviewed all current upstream issue bodies for document attachment links.
  Many CAS/CAA results concern unrelated software; none establishes a CNKI sample.
- Upstream issues 109/110 attach screenshots, not source documents.
- Upstream issue 111 is a new document lead outside the pinned collection:
  https://github.com/caj2pdf/caj2pdf/issues/111 . Its Dropbox document was downloaded completely and SHA-256 verified
  (238,910,818 bytes). Inspection reports HN-A, 738 pages and 1,450 bookmarks.
  An initial 128 MiB capped download was incomplete and excluded; the complete
  retry used 256 KiB reads with a 512 MiB cap. No CAA/CAS/NH-extension discovery
  is claimed.
- Original `.nh` bytes have not been established by finding `.nh` identifiers
  in CNKI bibliographic URLs; those URLs are not themselves document downloads.

## Historical evidence

The June 2002 KNS3.5 manual, authored by Tsinghua Tongfang, lists CAJViewer 5.0
support for CAJ, NH, KDH, CAS, CAA and PDF:
https://staatsbibliothek-berlin.de/fileadmin/user_upload/zentrale_Seiten/ostasienabteilung/pdf/UserGuide35.pdf

Later CNKI training materials list TEB, CAJ, NH, KDH and PDF:
https://libo.xmu.edu.cn/contentfiles/wendang/jiangzuo/2013-1-cnki2013.pdf

These establish historical names, not binary specifications or equal support
across viewer versions/platforms. CAA being a link file is an unverified lead,
not an implemented classification. No new decoder is justified by an extension.

## New HN-A initial conversion attempt

- Input: issue-111/56.caj, SHA-256 in catalog.json.
- Converter source checkout: `4910da982f60ae6f09470a3fd78499470a25faa5` (clean).
- CLI SHA-256: `d3eebe3e80e6ac87efc570f1584b3826f95087a33fd73a8ff38bb0b8ecdfd07d`.
- Command: `caj2pdf INPUT -o OUTPUT`, default bookmarks, no supplied fonts.
- Initial local Linux conversion reached a 90-second limit and was terminated.
  Status: INCOMPLETE_TIMEOUT. No complete PDF, memory result, viewer comparison
  or cross-runtime compatibility pass is claimed. Retry with a recorded larger
  budget before concluding that this represents a converter defect.
- Follow-up: https://github.com/rwv/caj2pdf-rust/issues/284 .

## TEB characterization: corrected 2026-10-09

The [nine-source follow-up](research/notes/teb-container-boundary-20261009.md)
supersedes the 2026-10-04 framing and CRC interpretation. The earlier refusal
observations remain historical, but did not prove that all TEB input was
irrecoverable or that every entry was encrypted.

Eight intact sources have a 16-byte archive header at `0xA0`, two 28-byte
local records without filename bytes, and 40-byte central records with
index-XOR names. The words at `0xA8`/`0xAC` are directory byte length and
directory offset relative to `0xA0`, not a type and archive length. Both stored
payload CRCs and inflated `document.xml` CRCs match. The XML metadata is readable;
the declared PDF payload's wrapping/key semantics remain unknown.

The ninth identity is a separately uploaded `6.teb` with a verified 1,507,965-byte
zero-filled suffix. Its outer ZIP CRC and a fresh download match, so this is
source damage, not an interrupted local acquisition. A separately cataloged
intact file has the same 4 MiB prefix; it is not silently substituted.

All nine originals now have offline viewer observations: eight validation-server
connection errors and one unknown error. An original two-page PDF control opens.
No TEB source is newly converted. Actual recovery/credential requirements remain
open in [Rust #468](https://github.com/rwv/caj2pdf-rust/issues/468); the overly
certain CLI/JavaScript diagnostic is addressed separately in
[#469](https://github.com/rwv/caj2pdf-rust/issues/469). Captures, source/payload
bytes, XML values, fonts and credentials remain external.

## CAA, CAS and NH search log (issue 2), 2026-10-04

Repeated searches, results reviewed but no authenticated sample bytes found:

- Web: `CNKI ".caa" CAJViewer 链接文件`, `CAJViewer ".cas" 文件格式 CNKI`,
  `".nh" 文件 CNKI 硕博 学位论文 nh格式`, and an English GitHub query for
  `.nh/.caa/.cas` samples.
- Extension directories (the-x.cn `CAA.aspx`, fileinfo.com `extension/caa`)
  describe CAA as a CNKI shortcut holding an HTTP link that CAJViewer opens
  by downloading the referenced item. This is secondary, unsourced
  description: it supports the link/descriptor hypothesis but is not byte evidence.
- CAS: no result described the bytes or offered a file; results concerned
  CAJ or unrelated software.
- NH: library/help pages state NH is used for CNKI theses and opens in
  CAJViewer; none links an original `.nh` download. The pinned CAJSamples tree
  has only `.caj`, `.teb`, `.pdf` and `.dat` files, so its HN rows were all
  delivered as `.caj`.

Unresolved gaps: no authenticated CAA, CAS or original-extension NH file exists
in this catalog. No new layout is confirmed, so no implementation issue is
opened in the main project. Future leads need source URL, original extension,
size, SHA-256 and redistribution evidence before cataloging.

## New HN-A complete conversion (main issue 284), 2026-10-04

- Input: `issue-111/56.caj`, identity PASS (catalog SHA-256).
- Converter: caj2pdf-rust main `509bb6e`, clean checkout, Linux x86_64 release
  CLI built with the pinned toolchain; default options and bookmarks.
- Native: PASS in 105 s (single run, 4 vCPU), 10.1 MiB peak RSS (`wait4`),
  output 268,737,204 bytes, SHA-256
  `db8f4a970e0d51a985b4e807a19dac853f15fd75efb2d5ac26ed768dc3be0888`.
  The earlier 90-second budget was too short; that INCOMPLETE run remains
  a timeout, not a defect.
- PDF: `qpdf --check` clean, 738 pages; MuPDF renders all 738 pages; all 1,450
  outline entries match the source titles, levels and pages exactly. The
  shared-catalog runner reports conversion, PDF, page-count and source-outline
  PASS; its page-image order check is NOT_RUN because no pinned pixel oracle
  covers this new document.
- Node 22 WASM, ranged file: byte-identical output, 368 s, 102 MiB RSS.
  Node 22 WASM, standard input spooled to a temporary file: byte-identical,
  286 s, 103 MiB RSS. Durations are single observations; the spooled Node and
  browser runs overlapped on the same 4 vCPU host.
- Chromium (Playwright headless shell 1194) Dedicated Worker, release WASM,
  ranged Blob input, four 256 MiB-capped OPFS scratch stores, sequential OPFS
  output: byte-identical, 738 pages and 1,450 bookmarks in 499 s; 430,981,910
  input bytes read, 256 KiB maximum output chunk, scratch extents zero and no
  OPFS entries left. Browser process memory was not measured.
- CAJViewer comparison: NOT_RUN. Full-page CAJViewer capture is still an open
  capability in the main project; a structural pass is not pixel parity.

## Open leads

No tracked collection issue remains open. Reopen work only with a new authentic
CAA/CAS/NH file or a new CAJ/HN/C8/KDH structure or failure.
