<!-- SPDX-License-Identifier: MIT -->

# Public SSE object-stream collection and continued web search

The newly acquired [Shanghai Stock Exchange attachment](https://www.sse.com.cn/aboutus/publication/actofcourt/law/list/c/10643464/files/9f66fd525ace4005b03ee2be1b60779b.pdf)
is PDF 1.7, despite its `.caj` title in the search index. It is 4,280,581 bytes,
SHA-256 `e7f78ebc47de69356e364a4c90e47a9e93f61855d47a6ac0230ba6ae06880da1`.
The [receipt](public-sse-collection-20261009.json) records acquisition,
baseline refusal, independent preservation checks and retained warnings.

Rust [#507 / PR #508](https://github.com/rwv/caj2pdf-rust/pull/508) admits the
standard `/Extends` link from object stream 302 to 301. Collection links are
validated for live generation-zero stream targets and bounded acyclicity;
each stream keeps its own member index. Original MIT positive/negative
controls use no external document bytes or foreign implementation.

The unchanged original converts to 26 pages. Native, Node and real Chromium
produce identical PDF SHA-256
`4d32c240b5ec61e462a6809979c78be207f3529c8821484aee7a9bc7798f4f65`.
The entire original byte prefix is preserved, as are the 455 live object
values and 295 raw stream byte sequences. Every page agrees in boxes,
rotation, word positions and 72-dpi MuPDF pixels. There are no outline entries.
Browser OPFS cleanup passes. All 203 earlier PDF/KDH identities also retain
the same native before/after outcome and successful output hash. Preserved
refusals are not compatibility passes; no response was supplied to TTKN
inputs in that comparison. Qpdf exits 3 on the original with four
linearization order/hint warnings; these remain in the receipt. Output qpdf
exits 0 after existing incremental normalization.

An equal-width self-cycle mutation is refused by native, Node and Chromium
without PDF writes or leftover staged/OPFS files. The first negative runtime
assessment used an incorrect expected error-code spelling; the corrected
assessment was rerun with the unchanged WASM. Both attempts are retained.
This external mutation supplements the required original MIT controls; no
mutated document is committed here.

Only one catalog row is added after the implementation merge. The earlier
1,385 rows remain unchanged, yielding 1,386 identities: 1,341 conversion PASS,
18 FAIL and 27 UNSUPPORTED. The additional 26 pages bring the previous
reconciled accepted-page total from 36,468 to 36,494. This is not a fresh
full-catalog run or a proprietary vendor-viewer comparison.

## Continued acquisition, including Web Archive

The continuation examined 600 additional Nanjing University page URLs,
bringing this site's bounded traversal to 1,300 distinct attempted URLs;
107 discovered URLs remain unvisited. Five new public archives downloaded
and passed bounded libarchive inspection, but contained no CAJ-family
members. They are acquisition leads, not five new document samples.

Five broader Archive.org searches and two batches of selected item metadata
cover 900 metadata requests (63 unavailable), recorded with receipt hashes. Keyword
matches include unrelated shelf codes, novels and papers. This continuation
found no additional direct original CAJ-family files in those selected
metadata lists. Three exact item checks distinguish a metadata-only CNKI
collection, a small archived website ZIP, and an ordinary conference PDF.
The website ZIP matches its Archive checksums; bounded inspection of its
178 entries finds no CAJ-family member. A separate retry of five previously
unavailable metadata endpoints succeeds and exposes nine direct CAJ links
in `360-temp`. All nine were acquired with matching Archive checksums via
the canonical URL or metadata-provided public storage server. Five are new
identities and four are known duplicates; [#92](https://github.com/rwv/caj2pdf-samples/issues/92)
handles their separate validation/catalog update. They are not counted in
this SSE-only catalog change.
This does not supersede the earlier successful 86 Archive.org transfers in
[the public-web sweep](public-web-sweep-20261009.md).

The exact NKOS Wayback CDX request timed out; the older URL's availability
request returned HTTP 429. No new Wayback document was acquired. These are
unavailable queries, not proof that snapshots do not exist. Archive.org's
ordinary item metadata/download service and Wayback are separate paths.
Two additional download-site links redirected to login and remain leads.

External documents, downloaded archives and rendered pages stay outside this
repository. Public availability does not grant redistribution rights. No
full-web exhaustion, new irrecoverability classification, other TTKN recovery,
or release is claimed.
