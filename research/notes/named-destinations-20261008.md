# Named local destinations, 2026-10-08

[Rust #449](https://github.com/rwv/caj2pdf-rust/issues/449) / [PR #451](https://github.com/rwv/caj2pdf-rust/pull/451)
adds a bounded standard-PDF destination profile. A valid 139-page PDF previously
failed at outline object 3602 because its local GoTo destination was a byte
string. The unchanged original now converts on native, Node and Chromium to
**exactly its original bytes**, preserving every page and bookmark. The
[metadata receipt](named-destinations-20261008.json) contains the independent
source inventory, scoped navigation negative, runtime/build identities and
full baseline regression.

## Separate source and provenance

The [public archive of the author-hosted thesis PDF](https://web.archive.org/web/20220119135502id_/http://ise.thss.tsinghua.edu.cn/~mlong/doc/phd-thesis-mingsheng-long.pdf)
is **12,742,695 bytes**, SHA-256
`0720aeb03613751b5675ca02d4e8ce85ecee4312b691f9f32b071229f57d1cd1`.
It has **139 pages and 97 outlines**, is unencrypted, and passes qpdf. This
identity is newly added to the catalog, outside the **1,277-original GitHub
baseline** and the 19-input NH/CAA extension. The total catalog is now **1,297**
identities: 1,279 document candidates and 18 CAA descriptors.

This is not a byte-equivalent replacement for the truncated 134-page CAJ in
[#448](https://github.com/rwv/caj2pdf-rust/issues/448), nor proof of edition
equivalence. That original remains a refused missing-data exception. The
[prior search report](truncated-caj-20261008.md) retains the current author URL's
38-byte missing-page HTML response, archive provenance and other scoped search
attempts. No source identity is silently replaced.

Independent inspection finds Catalog **1**, Names **3600**, and Dests root
**3595**. The tree has **341 nodes**, depth **four**, and **747 byte-string keys**
with indirect XYZ destination arrays. Every node's lexical order and non-root
Limits are checked. All 97 outlines and **889 named annotation links** resolve
to the expected live pages and non-null XYZ coordinates; null zoom is preserved
as the independent reader's zero value. All 747 arrays have three finite numeric
or null arguments. Another **29 URI and two launch actions** are inventoried
without execution or external contact.

Qpdf's xref and MuPDF identify **4,006 original objects / 563 streams**. Pikepdf
exposes an additional in-memory MediaBox array at object 4007 already on open;
it is absent from the original xref and excluded from source counts. Its
library-internal normalization cause was not investigated.

## Implementation and controls

Reviewed Rust head **53466a898d1ae157fe6354bc3f3900cfe51f5f1a** follows
ISO 32000-1:2008 §§7.3.4, 7.9.6/Table 36, 12.3.2.2/Table 151, 12.3.2.3 and
12.6.4.2. Original MIT code reuses the existing indexed/object-stream reader,
parser, page-target validation and fallible allocation helpers. No foreign
converter or vendor implementation was read, and no private module migrated.

The measured profile admits indirect Names/Dests dictionary nodes and indirect
XYZ arrays, with decoded byte-string keys. One traversal validates the complete
name tree before binary-search lookups. Conflicting order/Limits, duplicate or
missing keys, cycles/shared nodes, invalid page targets, unsupported views and
remote/chained actions remain errors. Existing direct outline-array behavior
is retained. Nothing in the original tree, page or action is rewritten.

Tree depth is capped at the existing 64-level syntax limit. Visited storage is
bounded by admitted xref slots. Index, stack and cumulative reserved key/Limit
bytes each use at most an allocation-derived one-eighth budget; cumulative
loaded destination metadata has the allocation-byte ceiling. Ranged reads,
sequential copying, per-object syntax bounds and cancellation remain in place.
Callers must keep source bytes stable throughout inspection and copying.

Seven original test groups cover literal/hex escapes and byte comparison,
root/leaf/internal and compressed nodes, ordering/Limits conflicts, missing or
wrong targets/actions/views, depth 64/65, separate work/name/index limits,
short I/O, cancellation and an invalid target after a source change. Initial
fixture setup failures are preserved in the JSON; the final controls reach the
intended limits. Exact-head CI runs **1,361 Rust tests**, with **seven optional
corpus tests ignored**, not compatibility passes. **166 JS tests pass with no
skips**. Required Clippy/format/license/build gates pass; line coverage is
**98.58% (29,893/30,324)** against the configured 90% floor.

## Unchanged-source results and limits

Native, Node and Chromium output hashes equal the original source SHA-256.
Qpdf exits zero, inputs stay intact, and browser OPFS cleanup leaves no entries.
Committed-head rebuilds reproduce the frozen native and WASM binaries exactly.
The receipt retains the earlier uncommitted harness label alongside this verified
build mapping rather than silently relabeling it.

Independent comparison matches all **139 page references, geometry, text/link
inventories and Poppler RGB renders**, all **4,006 object values**, all **563 raw
streams**, and all **97 outline entries**. A separate wrong-target PDF changes
the first named outline from page 1 to page 2 in the independent reader while
preserving page text. That diagnostic passes qpdf and is not counted as another
original source or compatibility pass. This establishes scoped reader navigation;
no vendor-viewer run or resolution of #441 is claimed.

The fresh **1,277-original / 2,126-attempt** native baseline remains **1,248 PASS,
20 FAIL, nine UNSUPPORTED**. All **2,097 previously successful attempt hashes**
are unchanged, with zero conversion regressions and unchanged refusal diagnostics.
All 1,248 primary outputs pass qpdf. Ancillary page-order checks remain
286 PASS / 26 FAIL / 936 NOT_RUN; outline checks remain 297 PASS / 951 NOT_RUN.
These states are preserved, not promoted to fidelity passes.

All **19 extended inputs** retain results: one 433-page NH output with the same
hash and 18 CAA refusals, without resolving opaque targets. Earlier 936 bitmap
and 26 native-content oracle receipts remain applicable by fresh PDF-hash
comparison; their decoders were not rerun. The earlier **1,247-input Node/Chromium
run used reviewed #444 WASM**, retains its original interruption/build evidence,
and matches the fresh native hashes. It is not a full-corpus run of #449 WASM.

Final review/simplification is self-review, not independent approval. No native,
CLI or JavaScript API change, new dependency or release is involved. The catalog
and receipts contain metadata only; source/PDF/text/pixel/font/vendor bytes stay
outside Git. Remaining refusals and fidelity gaps stay open under #406.
