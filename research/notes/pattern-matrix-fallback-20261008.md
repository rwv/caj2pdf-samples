<!-- SPDX-License-Identifier: MIT -->

# Measured CAJ tiling-pattern Matrix fallback

[Rust #414](https://github.com/rwv/caj2pdf-rust/issues/414) and
[PR #427](https://github.com/rwv/caj2pdf-rust/pull/427) recover two unchanged
CAJ originals with four malformed Pattern matrices. The
[receipt](pattern-matrix-fallback-20261008.json) pins the original sources,
full measurement candidate `dfb539573fb37b7145ba6f6d2eb1a205946cb93d`,
final integrated candidate `4308d424587486b57d303d317b3fededbf1223e7`, source comparisons,
viewer controls, runtime hashes and 1,277 original inputs / 2,126 native attempts.

| Original SHA-256 prefix | Pages | Source bookmarks | Raw streams | Pattern objects | Affected page |
| --- | ---: | ---: | ---: | --- | ---: |
| `2423e0b8e640` | 163 | 116 | 259 | 615, 620, 625 | 20 |
| `f08947012a48` | 101 | 91 | 1,107 | 1307 | 23 |

All four arrays are `[0.72 0 0 -0.719999 -5e-006 842]`, allowing observed
whitespace. PDF numbers do not admit this exponent token. The
[Adobe PDF reference](https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/pdfreference1.6.pdf)
defines the optional Matrix's identity default but does not prescribe recovery
of malformed arrays. The recovery choice therefore needs observed source
behavior, not a decimal expansion inferred from the token's mathematical value.

Original asymmetric patterns with a nonidentity basis, small and amplified
invalid exponents, valid decimals, zero and identity distinguish the behaviors.
CAJViewer 9.0.0 and Poppler use whole-Matrix identity; MuPDF substitutes zero
for the invalid element while retaining the other basis operands. Decimal
expansion and zero-element substitution change the first original's appearance.
The earliest otherwise-identity controls could not distinguish these cases;
their initial zero interpretation was superseded explicitly.

Nine fresh offline viewer sessions open one document each. The unchanged CAJ,
independently framed source PDF and identity diagnostic agree on each affected
source page at 50% zoom. Two settled captures give identical complete-page
crops without alignment or rescaling. Original controls use 100% zoom. Each
container stays below 748 MB, avoids OOM, preserves input hashes and is removed
after measurement. The receipt pins the cached viewer image and containment;
vendor implementation code was not inspected or instrumented. These are two
affected-page observations, not an all-page vendor or universal-resolution claim.

The earlier multi-tab session exceeded its 2 GiB limit. Its later black desktop
captures are invalid and excluded. An initial identity-control screenshot had
a wider sidebar, so a fresh isolated same-input session supplies that comparison.
Other shifted, overwritten, blank and failed exploratory captures remain external
and are not compatibility passes. Agreement between tools does not establish
that their implementations are independent.

Independent framing copies the source bodies verbatim, measures 667 and 1,377
unique object headers, builds explicit xrefs and supplies only absent Pages
ancestors and a Catalog. Parent/Kids links and the source page table establish
the exact page order. Qpdf's four source numeric warnings are retained. All
**264 Poppler RGB72 pages, page IDs, text, effective boxes/rotation, 1,366 raw
stream payloads and page link destinations** match the identity result. Every
other actual source object value remains unchanged. Separate source-outline
checks preserve all **207 bookmarks**, including destinations and hierarchy.
Production output from both unchanged originals is byte-identical to the
measured diagnostic output and passes qpdf without warnings.

The original MIT implementation writes explicit `[1 0 0 1 0 0]` with equal-width
padding only for the measured eleven-key Pattern dictionary. A 32-byte probe
precedes a 512-byte header bound. Generation zero, exact profile values and the
complete direct 45-byte Flate stream boundary are required. It reuses ranged
metadata patches and sequential output, accounts retained patch allocations,
and preserves source rechecks and cancellation. Pattern and other stream bytes
are never rewritten. Other invalid profiles remain errors; correct transforms
and ordinary indexed PDF syntax retain their existing behavior.

Final native, Node and Chromium outputs have matching PDF hashes, and browser
OPFS cleanup passes. The complete native regression records **1,239 PASS /
28 FAIL / 10 UNSUPPORTED**: exactly these two improvements, with all previously
passing PDF hashes unchanged. Source inventories and failed-output cleanup pass.
One inherited qpdf warning remains elsewhere. This candidate's JavaScript
original-document checks cover the two recovered inputs; earlier full-corpus
JavaScript verification retains its separate candidate pins. This is the frozen
GitHub sweep shared with #419; the newer CAA/NH catalog expansion in samples
PR #29 is outside this ledger and needs separate follow-up.

After main merged CAA/NH recognition (#428) and registry documentation (#429),
the final candidate was rebased onto `8fe81ffee05c640991f1ca73776c7178dd0e9658`.
Only the conformance-document append conflicted; both sections were retained.
PDF recovery and CAJ conversion tests are byte-identical to the fully measured
candidate. A fresh **1,277-original / 2,126-attempt** conversion run verifies
all statuses, source integrity, cleanup and every successful output hash again.
Earlier structural/content/render checks apply to those identical PDF bytes;
they are not claimed as freshly rerun validators or vendor sessions. Fresh
Node/Chromium verification, local suites, builds, clippy and all eight required
CI checks pass on the final integrated head.


The final integrated workspace records **1,299 passing tests and seven ignored optional-corpus
tests**; JavaScript records **166 passes without skips**. Original controls cover
visible asymmetric patterns, exact output/stream preservation, correct transforms,
mixed Matrix/Length repairs, strict indexed PDF parsing, unmeasured neighbors,
short reads, cancellation, changing sources and allocation/offset bounds.
Final review found and fixed a possible offset overflow for caller-configured
sources near `u64::MAX`, with a virtual ranged-source regression test. Locked
native/WASM builds and strict clippy pass. An initial local JavaScript setup
failure lacked the expected build-artifact path; the final run uses the actual
tested WASM. Rebase preserved main's v0.5.0 release-preparation changes.

The frozen native harness's 26 historic order failures and 936 NOT_RUN bitmap
checks remain visible. Separate samples PRs #16/#17/#20/#24 cover their recorded
scopes without rewriting those old results. Rust #406 remains open for 38
refusals and broader fidelity work; those inputs are not classified as
irrecoverable. External documents, PDFs, font/pixel bytes and vendor executables
are not committed. This work does not publish a release.
