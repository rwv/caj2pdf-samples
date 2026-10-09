# Public Geodata CAJ document attachments, 2026-10-09

Seven anonymous public attachment downloads yield **five new identities and
two duplicate URLs**, totaling 19,030,325 unique input bytes. Their original
filenames end in `.caj`, while their signatures are `%PDF-1.6`. All five
convert with the current native, Node and Vite IIFE Chromium implementation,
with identical output hashes, sizes and page counts: **67 pages**.

This follows [samples #102](https://github.com/rwv/caj2pdf-samples/issues/102)
and the wider public-web collection requested under
[Rust #406](https://github.com/rwv/caj2pdf-rust/issues/406).
The [receipt](geodata-public-attachments-20261009.json) contains each public
source page, component-metadata identity, download URL, size/hash/signature,
duplicate relationship, runtime outcome and independent preservation/render
check. The full 1,403-original run in [#101](https://github.com/rwv/caj2pdf-samples/issues/101)
is a separate frozen cohort; these five sources are not inserted into that
already-running manifest.

## Public acquisition and deduplication

The [Geodata entry page](https://www.geodata.cn/main/face_science_detail?guid=6577425&publisherGuid=126744287495912)
lists a CAJ document attachment. Its public component metadata and ordinary
page link construction identify the document CDN at `img.data.ac.cn`.
Anonymous HTTPS downloads match all declared attachment sizes. Dataset IDs
5707255, 8985854, 5117332 and 1870599 supply the other initial documents.
The dataset itself uses a separate order workflow; no dataset order, account,
payment or credential is used to fetch these public document attachments.

Two additional indexed pages, IDs 6316101 and 3571396, link to identical bytes
already obtained from 1870599, despite different attachment filenames. They
are retained as source aliases in the receipt and do not increase the count.
A bounded expansion checks 100 public search-result rows and those two indexed
pages, for 102 additional component-list requests with no failed responses.
The search API reports 13,078 results; only its first 100 were visited.
A publisher filter was requested, but its enforcement was not established,
so no publisher-specific or whole-site coverage is claimed.

The catalog records only metadata. Public access does not establish document
redistribution rights or grant the project's MIT license to the papers.
Raw documents, derived PDFs, renders and external web UI assets remain outside
Git. The public web UI was inspected only to follow its listed metadata and
attachment links; no such implementation code is copied into this project.

## Existing normalization and independent evidence

All five originals trigger qpdf's duplicate `/MediaBox` warning. A bounded
raw-object observation locates object 1 through qpdf's source xref and checks
the two literal arrays before a PDF reader collapses duplicate dictionary
keys. Each pair contains exactly equal four-number page boxes. The current
converter's existing bounded normalization handles this measured case;
all five output PDFs are qpdf-clean. No converter change is needed.

The existing independent PDF-family preservation tools verify **736 selected
objects and 362 raw streams**, page trees and zero forward outline entries.
Only the measured incremental trailer `/ID` and `/Prev` changes remain in
that semantic comparison. Output bytes are neither identical to the input
nor a complete original-byte prefix; the receipt retains that negative
comparison rather than calling this byte preservation.

All **67 page pairs** have equal same-renderer pixels in MuPDF (72 dpi RGB)
and Poppler (RGB, longest side scaled to 1,600 pixels). MuPDF page boxes and
word geometry also match on every page. There are no MuPDF warnings or
nonempty Poppler rendering logs. This is independent source/output rendering
and selected-object evidence, not comparison with a proprietary viewer or
proof that an unembedded font matches its author's original environment.

## Additional web and Archive search

The remaining 1,133 entries in the finite Archive metadata queue were all
attempted: 1,122 succeeded and 11 had retained network failures. No successful
response listed a direct original `.caj`, `.nh`, `.kdh`, `.teb`, `.caa` or `.cas`
file. This adds no original and does not scan nested archive members or prove
format absence. A separate earlier local snapshot scan inspected 1,294
metadata files for `.cas` names and found none; these scopes overlap and
are not added together.

Two public [Aspose forum attachment links](https://forum.aspose.com/t/how-convert-caj-kdh-nh-into-pdf-or-jpg/242493)
returned HTTP 401. Both Wayback availability requests returned HTTP 429; no
archival copy was acquired and no absence is inferred. All outcomes remain
in the receipt. An external search-summary script initially had a trailing
heredoc syntax error; fixing that aggregation did not repeat any acquisition
or conversion.

## Runtime and provenance

The package uses reviewed JavaScript head
`6e432cd43e9a3f89930b94f0b566084c1ea27944`, merged as
`6b184250ab8d51e5be6215e17169d6c39e33ac2c` with an identical tree. Native/WASM
artifacts come from `f4cd0166b1acefbd302fbe6e90bdb019fc982cea`; Rust sources
and locked build inputs are unchanged. The receipt pins the executable,
WASM, package, generated Vite assets, tools and external drivers. No caller
font or explicit TTKN response is needed for this cohort.

Native conversion, Node's seekable input/sequential hash sink and Chromium's
bounded OPFS input/output path each process every original once. Source
hashes remain unchanged before/after conversion, output hashes/sizes/page
counts agree, browser errors are empty and every final OPFS inventory is
empty. No conversion failure is discarded or retried. Existing 512 MiB and
180-second external bounds apply; full-corpus refusals and seven known
source-content warnings remain in their separate receipts.

The drivers are original MIT orchestration of existing public project APIs,
qpdf and the established research tools. No private HN/JBIG, foreign converter
or proprietary reader implementation is inspected or copied. No new product
dependency, conversion behavior or supported-format claim is introduced.
Review, catalog checks and CI precede merging. No release is performed, and
the parent correctness, font, outline and viewer-readiness issues remain open.
