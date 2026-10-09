# Frozen catalog through Vite IIFE Workers, 2026-10-09

This follows [samples #101](https://github.com/rwv/caj2pdf-samples/issues/101)
and the startup fix in [Rust #517](https://github.com/rwv/caj2pdf-rust/pull/517).
The [per-input receipt](vite-current-corpus-20261009.json) covers every original
in catalog commit `2b8a84f8854c226a3cc778b614c91c8d5669d24d`: 1,403 distinct
identities, 2,930,895,692 input bytes. The subsequent [Geodata collection](geodata-public-attachments-20261009.md)
adds five separately verified originals; it is not retroactively inserted into
this frozen manifest. Documents remain external.

All three fresh runtime runs finish with **1,356 conversions and 47 refusals**.
Every accepted output matches the historical PDF hash, byte size and page
count: **37,155 pages / 3,404,911,697 output bytes** per runtime. Native qpdf
checks are **1,349 clean and seven source-content warnings**; the seven
warning identities are exactly the existing #499 cohort. No accepted result
regresses, no refusal changes code, and no runtime failure is retried or
discarded. Every source-integrity and browser OPFS cleanup check passes.
The receipt retains 20 catalog FAIL and 27 UNSUPPORTED inputs, separate
from the conversion passes.

## Frozen implementation and configurations

The JavaScript package is copied from reviewed head
`6e432cd43e9a3f89930b94f0b566084c1ea27944`, merged as
`6b184250ab8d51e5be6215e17169d6c39e33ac2c` with the same Git tree. The startup
change removes top-level await from the Worker module graph. Vite's default
IIFE build failed before that change and succeeds afterward. The regression
queues a request before module loading and checks its normal reply. All 183
JavaScript tests pass without skips in CI, including Node, Chromium and actual
packed-package tests; the four quality and four required Linux gates passed.

The native executable and WASM were built at reviewed #516 head
`b32672796dd2c4bd374d172df3271dc64930b7a4`, merged as
`f4cd0166b1acefbd302fbe6e90bdb019fc982cea` with an identical tree. Rust sources and locked build inputs
are unchanged by #517; the receipt verifies that identity and pins the native
executable, WASM, all 13 package files and four Vite output assets. It also
records the external driver hashes, Node v24.13.0, Chromium 154.0.8037.92,
qpdf 12.2.0, Vite 8.0.0 and caller font identities. These are local artifacts,
not hashes of a released or CI-built distribution.

Eighteen cases explicitly supply NotoSerifCJK-Regular TTC face 2 and
FreeSerif, matching their historical configuration. This is a caller-option
count; image-only inputs do not necessarily consume those fonts. One measured TTKN original
(`074cb4d57181…`) uses its matching author-disclosed response, explicitly
supplied through the CLI file or JavaScript option. The value is neither
logged nor published. It is not applied to any other protected source;
embedded external targets are never contacted. Browser documents, fonts and
that one explicit response are served only from a loopback server.

## Fresh operations and independent reconciliation

Native conversion runs once per source, with three concurrent processes;
Node and Chromium each visit the same fixed source order once. Node uses
seekable file paths and a sequential SHA-256 sink. Chromium runs the actual
Vite-produced IIFE Worker, with cross-origin isolation enabled. Inputs and
required fonts are streamed into temporary OPFS entries; sequential output
goes into one temporary PDF and is streamed to a loopback digest endpoint.
Source, font and output entries are disposed before checking the final OPFS
inventory. No whole-document in-memory input/output path is introduced.

Every operation checks its source hash before and after conversion. Each
native accepted output is independently checked by qpdf, with its page count
recorded. Aggregation checks exact catalog membership, uniqueness, order,
source sizes, output hashes/sizes/page counts, refusal diagnostics, zero
failed sink bytes, absence of native failed outputs and empty browser OPFS.
The zero-filled unknown header and nine TEB inputs have different CLI and
JavaScript wording in the reviewed
[CLI adapter](https://github.com/rwv/caj2pdf-rust/blob/6e432cd43e9a3f89930b94f0b566084c1ea27944/crates/caj2pdf-cli/src/document.rs)
and [JavaScript adapter](https://github.com/rwv/caj2pdf-rust/blob/6e432cd43e9a3f89930b94f0b566084c1ea27944/js/io.mjs);
both exact messages are checked explicitly. Other refusals retain the same
core message. Aggregation does not trust the drivers'
`historical_match` flags. In-memory controls
inject duplicate/missing identities, a changed PDF hash, a retained OPFS
entry, a nonzero refusal sink and a changed refusal code; all must be detected.
Package, bundled asset, executable and font hashes are checked again afterward.

External native limits are 2 GiB address space, 512 MiB output, 120 CPU seconds
and 180 wall seconds per conversion; qpdf has separate 60 CPU/90 wall-second
limits. Browser spooling/upload and the Node sink have a 512 MiB cap. Conversion
cancellation is 180 seconds, with a 195-second external browser observation
limit. This is bounded runtime evidence, not a peak-memory benchmark.

## Retained attempts and limitations

The initial external Vite invocation used the wrong build root and failed
before finding an application entry. The first five-format smoke harness
used distinct Node font objects versus one shared browser font object, causing
a native-C8 PDF resource-deduplication mismatch. Equivalent caller resource
identities corrected that harness configuration; ten isolated/non-isolated
Chromium controls then matched Node. Both earlier attempts remain recorded.

Native full-catalog preparation initially selected the debug executable;
its hash check stopped the driver before any conversion. Selecting the pinned
release executable resolved that preparation error. No failed original is
silently retried or reclassified as a conversion pass.

The first final aggregator assumed identical CLI/JavaScript TEB wording and
stopped on a TEB refusal. After verifying both messages against the reviewed
adapter source, the aggregator checks their exact distinct wording. Its
earlier failure log and script hash are retained; no conversion ledger was
changed or conversion retried.

The 47 refused inputs remain 16 protected TTKN sources, nine TEB containers,
18 CAA descriptors and four damaged originals (missing palette data, truncated
CAJ, zero-filled header and zero-filled PDF body). Refusal/cleanup checks do
not establish irrecoverability. The successful TTKN case does not validate
credentials or wrapping profiles of the other 16 sources.

Matching three runtimes and accepting qpdf output do not establish full
source content or visual fidelity. The seven source-content cases in
[Rust #499](https://github.com/rwv/caj2pdf-rust/issues/499), historical source
warnings, caller-font/ornament fidelity, unknown C8/HN-B outlines and
[viewer readiness](https://github.com/rwv/caj2pdf-rust/issues/441) retain their
scoped evidence and open limits. [Rust #406](https://github.com/rwv/caj2pdf-rust/issues/406)
remains open. Optional-corpus skips are never conversion passes.

All added tooling is independently authored MIT code, using existing public
project APIs and the original browser harness. Vite/Rolldown are external MIT
validation tools, not new product dependencies. No private HN/JBIG, foreign
converter or proprietary implementation was read or copied. No documents,
PDF bodies, fonts, decoded text, screenshots or response values are committed.
This is a verification report and metadata receipt; it changes no conversion
rule and publishes no release. #433's patch-release criterion remains open.
