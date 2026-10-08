<!-- SPDX-License-Identifier: MIT -->

# Unescaped QITE source-file paths

[rust #419](https://github.com/rwv/caj2pdf-rust/issues/419) and
[PR #421](https://github.com/rwv/caj2pdf-rust/pull/421) recover an unchanged
139-page CAJ original whose malformed metadata strings made parsing continue
into otherwise correctly bounded image data. The [receipt](qite-source-path-strings-20261008.json)
pins the original, candidate, all-page/source-stream measurements, runtime
parity and all 1,277 inputs / 2,126 native attempts.

Objects 25588 and 25357 contain single-line source-file paths with unescaped
ASCII opening parentheses and GBK full-width closing parentheses. All 138
incoming references (one and 137) are sole target occurrences in retained
Pages' direct QITE_pageid/F metadata. The repair preserves the raw 52-byte and
56-byte payloads as hexadecimal strings; their identities are verified and
only hashes/lengths are published. The converter never opens these paths.
[Adobe's string documentation](https://opensource.adobe.com/dc-acrobat-sdk-docs/library/plugin/Plugins_Cos.html#literal-strings)
provides the public syntax. No foreign implementation was used.

A 32-byte prefix probe precedes a 640-byte complete-object bound; at most 64
candidates may require complete graph validation, and retained bytes obey
Limits. Correctly escaped strings remain unchanged. Rendering/shared/indirect
references, ambiguous framing and unmeasured strings remain ineligible; partial
mode explicitly blanks dependent damaged pages. Source checks, cancellation
and existing sequential reconstruction remain in force.

The independent oracle copies body `[218836,13028326)` verbatim, creates an
explicit classic xref from 538 unique measured source headers, and adds only
missing Pages root 2 (children 25525/25524 from source parent links) and Catalog
25608. This avoids repair scanning through malformed strings. Original path
parse warnings remain recorded. The earlier minimal-xref/qpdf probe's warnings
and stopped bad-xref behavior are not treated as successful validation.

All **139 page IDs, 258 raw streams, text, page boxes/rotation, link destinations
and RGB renders at 72 dpi** match the framed source in PyMuPDF 1.27.2.2. All
**35 source bookmarks** pass a separate independent outline identity check.
The two metadata payloads are byte-identical after hexadecimal decoding.
Every other actual source nonstream value is unchanged. The synthetic root's
converter fallback MediaBox and synthetic Catalog's added container outlines
are recorded separately; all effective page boxes still match. Qpdf checks
the converted output clean. This is scoped source-PDF evidence, not a universal
renderer/resolution or CAJViewer claim.

Native, Node and Chromium PDFs have identical hashes and browser OPFS is empty
afterward. The full native rerun records **1,237 PASS / 30 FAIL / 10 UNSUPPORTED**,
exactly one improvement with every previously passing PDF hash unchanged.
All source inventories and failure-output cleanup pass; one inherited qpdf
warning remains. This candidate's JavaScript verification covers the recovered
original; previous full parity retains its own candidate pins.

The workspace has 1,288 passing tests and seven ignored optional-corpus tests;
JavaScript has 164 passes without skips. Original controls cover byte retention,
correct strings, strict reference contexts, partial damage, cancellation,
source changes and allocation/read/count bounds. The frozen native harness's
26 old order failures and 936 NOT_RUN bitmap checks remain visible alongside
the separate verification in samples PRs #16/#17/#20/#24. Rust #406 stays open
for 40 refusals and broader content/layout/outline work. No external documents,
PDFs, raster/font bytes or foreign binaries are committed. No release.
