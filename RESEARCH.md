# Collection research

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

## Tracked next work

- TEB characterization: https://github.com/rwv/caj2pdf-samples/issues/1
- Historical CAA/CAS/NH collection: https://github.com/rwv/caj2pdf-samples/issues/2
- Optional runner integration: https://github.com/rwv/caj2pdf-rust/issues/283
