# Missing data in a 134-page CAJ, 2026-10-08

[Rust #448](https://github.com/rwv/caj2pdf-rust/issues/448) records a bounded,
independently evidenced exception to the full-conversion goal in
[#406](https://github.com/rwv/caj2pdf-rust/issues/406). The unchanged original
lacks required source bytes. It remains a refused original, **not a conversion
pass**. The [metadata receipt](truncated-caj-20261008.json) preserves the source
identity, measured spans, search attempts, runtime refusal and viewer evidence.
No converter behavior is relaxed to invent or silently omit missing content.

## Original identity and missing spans

[AnguoCYF/caj2pdf-actions/file.caj](https://github.com/AnguoCYF/caj2pdf-actions/blob/a166a7c4b093bb24de4d92f8c15841b9f123d3ab/file.caj)
is **4,669,461 bytes**, SHA-256
`48960fa0d3ac6b9e531baf1193510263f75b8d1f472312cb89c2a406204c1970`.
Hashing the local bytes as a Git blob gives
`5d6ff7a27d2b2fbb1753cb0a397b3f12c36e196b`, exactly the public repository's
blob identity. This is not a local incomplete download.

The header declares **134 pages and 94 bookmarks**. Its page table starts at
**61428**, its body at **63036**, and its declared body ends at **12991530**,
**8,322,069 bytes beyond EOF**. All 37 in-file row offsets begin at their
expected object headers. Row 37 is partial, and rows **38–134** begin beyond
the available file. Header agreement does not prove that the first 36 pages
are independently renderable: their complete resource dependencies have not
been established.

The last object is image **973**, at **3750728**. Its Flate payload starts at
**3750893**, declares Length **1058306**, and has only **918568** available
bytes. The payload alone lacks **139738** bytes, before its endstream/endobj
and later rows. Bounded standard zlib decoding produces **2233675** bytes of
prefix data with no decoder error, but **never reaches zlib EOF** and has no
unused trailing bytes. Only counts and hashes of those bytes are retained.
This independently corroborates truncation within a stream, not just an
unsupported parser diagnostic or a bad row-table number.

## Refusal and original-viewer behavior

On reviewed #447 code `ce4ba751aa6088745a2311f8055c3f7e4e04cfb7` (equivalent
merged `ee98198f3acc8d3baef00f812c87755dc1e82b63`), native conversion refuses:
`malformed CAJ at byte 61864, record 37: CAJ page span extends beyond source`.
No output is published. Node and Chromium return the same located
`MALFORMED_CAJ`, write **zero bytes**, preserve source hashes, and remove all
browser OPFS entries. These are **expected-refusal checks**, not accepted
compatibility tests. The original remains among the 20 failures in the
[pinned 1,277-original baseline](indexed-empty-form-20261008.md).

Two fresh contained CAJViewer sessions display the title page at **1/134** and
a **blank page at 37/134**, at 50%. Full 1600×1200 frames were visually checked;
3/10/12-second captures agree within each session. Inputs remain intact,
no OOM occurs and container removal is verified. The viewer uses the same
pinned, network-disabled, read-only, non-root, 2 GiB / two-CPU / 90-second
containment as the #446 report. Blank damage behavior does not establish that
the authored page is blank. Other viewer pages were not run and #441's general
readiness limitation remains open.

The existing original `malformed_header_and_page_table_report_the_field_location`
core test and integration malformed-container controls already exercise
out-of-source page spans. No redundant test or recovery workaround is added
for an input whose declared data is absent.

## Alternative search and separate recoverable gap

The three uploaded versions dated 2022-01-11 and 2022-01-20 contain the same
truncated Git blob. The earlier 2021-09-04 upload is only 555291 bytes. No
repository-history version is a complete same-prefix alternative. Comparing
the exact **63036-byte header/table prefix** against **189 larger collected
originals** finds no match. This is a scoped local search, not proof that no
intact edition exists anywhere.

The title page identifies Mingsheng Long's 2014 thesis, *Transfer Learning:
Problems and Methods*, corroborated by the [Tsinghua library record](https://newetds.lib.tsinghua.edu.cn/qh/paper/summary?dbCode=ETDQH&sysId=219351).
Public title/filename searches found an indexed author-hosted PDF URL, but its
[current response](https://ise.thss.tsinghua.edu.cn/~mlong/doc/phd-thesis-mingsheng-long.pdf)
is a **38-byte HTML missing-page message**. The transfer returned success;
the PDF signature check correctly rejected it before any PDF parsing or
conversion. The failed attempt remains in the receipt.

A [public 2022 archive of the author-hosted PDF](https://web.archive.org/web/20220119135502id_/http://ise.thss.tsinghua.edu.cn/~mlong/doc/phd-thesis-mingsheng-long.pdf)
was downloaded successfully: **12,742,695 bytes**, SHA-256
`0720aeb03613751b5675ca02d4e8ce85ecee4312b691f9f32b071229f57d1cd1`,
**139 pages and 97 outlines**, with qpdf exit 0. That inventory differs from
the original CAJ. It is a separate source identity, not a byte-equivalent
replacement or proof of edition equivalence. Its complete named-destination
inventory has **341 tree nodes**, maximum depth four, and **747 indirect XYZ
arrays** resolving all 97 outline items. Only hashes of name/title strings
and structural metadata are retained.

Current native conversion of this clean archived PDF fails at object 3602:
`outline destination must be a direct page array`. This is the independent
recoverable standard-PDF gap in [#449](https://github.com/rwv/caj2pdf-rust/issues/449),
not evidence that the archived PDF lacks content. That additional source is
**outside the 1,277-original GitHub baseline** and is not silently substituted
for the truncated CAJ.

The exception applies to recovering the original's complete declared content
from its available bytes. It does not rule out intact alternative editions
elsewhere or explicitly labeled future partial salvage. No arbitrary pixels,
text, fonts or pages are fabricated. Source documents, PDFs, decoded content,
viewer binaries and screenshots stay external; no foreign converter source,
private migration, new dependency or release is involved.
