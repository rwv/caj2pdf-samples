<!-- SPDX-License-Identifier: MIT -->

# Complete accepted-corpus Node and Chromium parity

Part of [rwv/caj2pdf-rust#406](https://github.com/rwv/caj2pdf-rust/issues/406).
All **1,232 accepted originals** in the 1,277-original GitHub corpus pass Node
and Chromium conversion with **exactly the native PDF SHA-256, size and page count**.
Browser OPFS cleanup passes for every original. The
[per-source receipt](full-runtime-parity-20261008.json) records identities, timing,
variant, font configuration, runtime hashes and cleanup results.

The converter candidate is `277d4229931ce156e5d7b62159fdd6722fa0f1b6`, merged as
`c31ac81a659d3a15fa3e048785e4e0c7885a0a6a` in PR #408. The WASM identity is checked
before/after the run. Native baseline results remain **1,232 PASS, 35 FAIL and
10 UNSUPPORTED**; this runtime run covers every accepted original, not the 45
refused sources. Seven synthetic fixtures are excluded from these corpus counts.

Ten native-text inputs use the same fonts selected by the CLI: NotoSerifCJK-Regular
face 2 and FreeSerif. The other 1,222 use ordinary image/PDF conversion options.
The receipt pins font hashes and retains initial missing-font configuration
refusals; those attempts were rerun correctly and never counted as passes.
All final inputs produce identical PDF bytes in all three runtimes.

Node hashes sequential sink writes and checks each original source SHA before and
after conversion. A browser Worker spools each input and its explicitly required
fonts to OPFS, writes output to one temporary OPFS file, and submits that file to
a localhost streaming SHA-256 sink. Temporary source/font/output entries are
removed before the next result is accepted. Neither the whole corpus nor all
converted PDFs is retained in memory. Native/WASM converter logic is unchanged.

Output parity is not an independent source-content or visual-fidelity oracle.
The [26-case image/text-order work](https://github.com/rwv/caj2pdf-samples/issues/12)
provides separate applicable checks. The remaining 936 missing bitmap-oracle
checks, source geometry/content coverage, C8/HN-B outline research and recovery
of refused sources remain within #406. These limitations are not waived by
2,464 successful JavaScript conversions. No release or package publication is
part of this checkpoint.

Metadata and original MIT measurement code only; no external documents, derived
PDFs, fonts or screenshots are committed. Existing historical FAIL/NOT_RUN
receipts remain intact.
