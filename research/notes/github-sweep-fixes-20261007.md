<!-- SPDX-License-Identifier: MIT -->

# GitHub sweep: post-fix validation — 2026-10-07

All **1,277 original document candidates** from the [collection](github-sample-sweep-20261007.md)
were rerun after the fixes for caj2pdf-rust #386–#394. There are **99 new
conversion passes and no conversion regressions**. This closes the focused
investigation in [#385](https://github.com/rwv/caj2pdf-rust/issues/385), not every
possible compatibility or fidelity gap.

| Native result | Before (`df6d023`) | After |
| --- | ---: | ---: |
| Converted | 1,128 | **1,227** |
| Failed / strict refusal | 123 | **39** |
| Explicitly unsupported | 26 | **11** |
| Total originals | 1,277 | **1,277** |
| qpdf clean outputs | 1,127 | **1,226** |
| qpdf warning outputs | 1 | **1** |

The [JSON receipt](github-sweep-fixes-20261007.json) records all 2,126 attempts,
source/download identities, SHA-256 values, byte sizes, diagnostics, PDF hashes,
qpdf results, ancillary failures and all 50 remaining refusal classifications.
The [catalog](../../catalog.json) points to this receipt. The historical
[baseline receipt](github-sweep-20261007.json) is preserved unchanged.

## Revision, method and scope

The frozen CLI was built from `18417d88a5896fc13d13c13be4964cb6434c4bd0`;
its SHA-256 is `b59cf2ba80492eb702307528b86cf4baa4d0988b4ab8e6b9e2cf3a0c611513f0`.
The subsequent rebase onto the squash merge of #400 has an identical complete
Git tree, also identical to the final merge `a19953921914b7cc794c1f58e5b5d33e6c1cd570`.
The receipt records both tested and merged revisions and tree equivalence.
Input hashes and sizes pass before and after each run; the binary is unchanged.
There were no timeout, missing-input or harness-error results. No refused
conversion published an output PDF. All 1,227 converted documents pass the
page-count check.

The existing `research/scripts/current_formats.py` runner at samples revision
`702c63b63817afd4860095811d01051c0d824ecb` was used, with four concurrent workers,
180 seconds per child, 1 GiB child address-space and 512 MiB output-file limits.
C8/HN-B inputs ran both default and `--no-bookmarks` modes. qpdf 12.2.0,
MuPDF 1.25.1 and Poppler 25.03.0 versions and the caller-provided Noto/FreeSerif
font hashes are in the receipt. The public catalog runner can export matrices
or rerun the same originals once acquired at their canonical catalog paths.

**Full-corpus Node/browser execution and whole-document visual parity are
NOT_RUN.** The affected profile groups below were actually run on native,
Node and real Chromium at their respective PR validation revisions. Those
groups overlap and must not be summed as distinct documents. C8/HN-B outlines
remain unverified (#303). Caller font substitution and the existing decoration
alias are explicit limits, not source-font or vendor-ornament fidelity claims.

The ancillary image identity/order check reports **265 PASS, 26 FAIL and
936 NOT_RUN** among converted documents. Twenty-five failures also occurred in
the baseline. The additional case is #391: its four text-only pages contain no
images; all 7,565 glyph identities and their per-page order pass a separate
applicable comparison. The other 25 failures are not waived by that observation.
Every original failure is retained in the receipt, with follow-up in
[samples #12](https://github.com/rwv/caj2pdf-samples/issues/12).
Source-outline checks report 281 PASS and 946 NOT_RUN. The runner's pixel check
is NOT_RUN for all converted documents; the explicitly scoped comparisons
below are separate evidence. Conversion or qpdf success is not full fidelity.

## Merged fixes and scoped evidence

| PR / issues | Actually executed evidence |
| --- | --- |
| [#395](https://github.com/rwv/caj2pdf-rust/pull/395), #386 | All 44 originals on native/Node/Chromium: 28 convert and pass qpdf; 16 encrypted PDFs remain refused, 14 also with HTML debris. Successful outputs match conversion of their bounded PDF prefixes. [Receipt](https://github.com/rwv/caj2pdf-rust/issues/386#issuecomment-6043362930). |
| [#396](https://github.com/rwv/caj2pdf-rust/pull/396), #387/#393/#394 | All 21 originals pass on all three targets and qpdf. All 1,504 page identities/geometries, 1,003 outlines and 9,648 raw streams match, plus 90 selected rendered pages. [Receipt](https://github.com/rwv/caj2pdf-rust/issues/387#issuecomment-6043759424). |
| [#397](https://github.com/rwv/caj2pdf-rust/pull/397), #388 | All 12 originals (1,610 pages) pass on all three targets and qpdf. All 177 affected JPEG pages match source payloads, geometry and reference renders. [Receipt](https://github.com/rwv/caj2pdf-rust/issues/388#issuecomment-6044235268). |
| [#398](https://github.com/rwv/caj2pdf-rust/pull/398), #389 | All 25 originals checked on all three targets: 15 convert at this checkpoint, two subsequently fixed by #390 and eight by #392. All 28 affected JBIG2 image bitmaps match both Poppler and MuPDF. [Receipt](https://github.com/rwv/caj2pdf-rust/issues/389#issuecomment-6044456714). |
| [#399](https://github.com/rwv/caj2pdf-rust/pull/399), #390 | All 13 affected originals (227 pages) pass on all three targets and qpdf; all 19 affected pages match geometry/reference renders and seven JPEG payloads match source bytes. [Receipt](https://github.com/rwv/caj2pdf-rust/issues/390#issuecomment-6044727003). |
| [#400](https://github.com/rwv/caj2pdf-rust/pull/400), #392 | All nine originals (224 pages) pass on all three targets and qpdf. Nine apparently blank images actually contain 19–123 black pixels; all match both image oracles, with 27 affected/adjacent page images compared. No blank substitution. [Receipt](https://github.com/rwv/caj2pdf-rust/issues/392#issuecomment-6044918811). |
| [#401](https://github.com/rwv/caj2pdf-rust/pull/401), #391 | The four-page article passes both bookmark modes, all three targets and qpdf. All 7,565 glyph identities/order positions, 5,870 selected glyph matrices, 40 segments and page extents pass. Original geometric viewer controls establish the admitted rules; vendor outlines/general visual parity are not claimed. [Receipt](https://github.com/rwv/caj2pdf-rust/issues/391#issuecomment-6045443866). |

All changes were independently authored under MIT and reviewed/simplified.
Unknown neighboring profiles remain explicit failures. Seekable/ranged input,
bounded decoding and sequential output remain intact. No document, PDF,
screenshot, font bytes or foreign converter implementation was committed.

## Remaining 50 refusals

Sixteen files have PDF encryption dictionaries (revision 2 confirmed by qpdf);
14 also contain HTML debris after EOF. Nine are the intentionally unsupported
DRM-encrypted TEB profile. These 25 files are not new decoder defects. The
remaining 25 are classified below; full hashes and diagnostics are in the JSON.
Offsets are source offsets except where explicitly marked as decoded KDH PDF
offsets (source offset minus 254).

| SHA-256 prefix | Evidence and retained classification |
| --- | --- |
| `7797fd3c7d6c`, `76e306d87586`, `0374e70b8fe0` | Zero-length Form objects 29, 182 and 9418 contain repeated object headers inside their declared streams. Unique bounded repair is unproven; partial output is not a pass. |
| `f26570f28a20`, `f65742f37f10` | Declared Flate spans cross later object headers. Independent zlib decoding fails after 776 / 775 input bytes. Keeping the damaged-stream refusal is justified. |
| `f08947012a48`, `2423e0b8e640` | Matrix numbers use exponential notation, which PDF numeric syntax does not admit. Partial mode substitutes blanks. |
| `dc3c3a651d4a` | Repairing the declared stream length 98 would write 100 and change field width. Explicit unsupported repair limit remains. |
| `ef0d77b2cdb2`, `1673e1153224` | Conflicting nested GSP1 references (3/9 and 3/43). qpdf warns and chooses the last key; the converter retains ambiguity rejection. |
| `6f30a4a0dc36`, `366f4d2f6652`, `acca38898dc3`, `9be1188adba1` | Duplicate identical MediaBox values. These are strict duplicate-key policy refusals, not evidence of different observed rectangles. |
| `48960fa0d3ac` | CAJ index row 37 ends at 4,816,464, beyond the 4,669,461-byte source; partial mode also rejects. |
| `b206e40da6df` | String-depth limit 64 is reached inside an apparent JPEG object's span. A valid deep string or exact corruption root cause is not established; bounded-parser refusal is retained, not silently relaxed. |
| `6cf520441256` | Interrupted unindexed object 132 prefix at decoded offset 28,005. qpdf tolerates it (exit 0); complete-object coverage is a stricter policy and safe recovery is unproven. |
| `50c8c55b978a`, `eacbcd00c35a` | Interrupted prefixes lack exact complete counterparts; diagnostic partial conversions replace pages with blanks. |
| `ece0be828c95` | Zero-length Form 485 contains Form 754 within its stream; qpdf emits recovery warnings, with duplicate MediaBox keys also present. |
| `c41cd7306591` | Indirect length ends within compressed bytes, 1,258 bytes before endstream; partial mode later finds a conflicting duplicate object. |
| `77b2ebe0a8d6` | Unencrypted PDF with Flate xref `Columns=4`, `Predictor=12`, qpdf exit 0. A genuine explicit feature gap, tracked in [#402](https://github.com/rwv/caj2pdf-rust/issues/402). |
| `5e1ea482a56a` | Invalid token within an apparent JPEG object's span. Partial mode blanks pages 24, 25, 27 and 31; exact reconstruction root cause is unproven. |
| `cb6f5e781f37` | An interrupted boolean in object 593 precedes object 605; partial mode substitutes blank pages. |
| `d3d8a89dc8ac` | Appearance reference 10887 has no declaration. Complete-reference inventory rejects it; this is not a claim that all unresolved references are forbidden by the PDF specification. |

The numeric-syntax reference is [ISO 32000-1:2008 §7.3.3](https://opensource.adobe.com/dc-acrobat-sdk-docs/standards/pdfstandards/pdf/PDF32000_2008.pdf).
Five KDH payloads were independently checked by qpdf after the already measured
wrapper decoding: two pass cleanly and three produce warnings. Headerless CAJ
fragments were not misrepresented as standalone PDFs for an oracle check.
`--allow-damaged` was run only as a diagnostic on the 20 CAJ cases; exit 3 and
blank-page replacement are **not compatibility passes**. Remaining unproven
repairs/strict profiles remain open research limits, with per-input evidence.

## Existing qpdf warning

`5a4432ed4878944c4aaa17f591b2a93d00014ea0bdacc9162bed1d88f8d61127`
(`issue-20/文件名未知.caj`) retains the baseline unexpected-closing-parenthesis
warnings in content stream 142. Its 4,587 raw stream bytes are identical to the
source payload at offset 880,636, SHA-256
`c10d8a7bd2b504beb27c5e5e5dcf920fe26f0a4768050f4eaac8169359ffb01e`.
This is a retained source-content syntax warning, not a new output mutation.
It is counted as converted with warnings, never as a clean structural pass.

## Collection boundaries

This rerun adds no sources and retains the original search limits: 8,442
repositories discovered, 7,437 complete trees, 1,000 unscanned/rate-limited,
one truncated and four empty. Seven synthetic fixtures remain excluded.
The corpus is 2,740,801,965 bytes stored externally; 47 inputs are already PDF
despite their extensions. No claim covers all GitHub history, branches,
private or nonindexed repositories. Source publication does not grant document
redistribution rights. Only metadata, hashes and original analysis are published.
