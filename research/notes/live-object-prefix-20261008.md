<!-- SPDX-License-Identifier: MIT -->

# Interrupted live PDF object prefixes

[rust #410](https://github.com/rwv/caj2pdf-rust/issues/410) and
[PR #411](https://github.com/rwv/caj2pdf-rust/pull/411) recover the unchanged
seven-page KDH original `6cf520441256d3d0e8749cb4b49275bbfc57ff962839cd7e131055c99cca992e`.
The [receipt](live-object-prefix-20261008.json) pins its origin, converter commit,
native/WASM hashes, all original/render/stream identities and a 1,277-input
native ledger.

Independent KDH decoding preserves every original PDF byte through its actual
CRLF-terminated EOF. Twelve gaps of 8–68 bytes contain interrupted object
headers, integers/terminators and page dictionaries. All trimmed prefixes
exactly match their xref-selected complete counterpart. The implementation
uses the existing bounded object parser and gap-copy patches, with a 128-byte
cap for exact live dictionary/integer prefixes. The older 64-byte free/adjacent
orphan rule is unchanged. Streams, other scalar profiles, complete objects and
conflicts do not qualify for this new rule.

All seven page identities, text, boxes, rotations and 72 dpi RGB pixels match
the independent source PDF; all 22 raw stream bytes and object numbers match.
Both files have zero outline items. Qpdf checks source and output without
warnings. Native, Node and Chromium hashes agree, and browser OPFS is empty
afterward. The original body is unchanged except for the 12 gap patches and
existing lone-CR stream-separator normalization. Seven preexisting stale Page
parents are repaired only against validated Kids; each changes only Parent.

The full **1,277-original / 2,126-attempt** native rerun yields **1,233 PASS,
34 FAIL and 10 UNSUPPORTED**, exactly one improvement and no changed previously
passing PDF hash. Every source hash is unchanged. Qpdf reports 1,232 clean
outputs and the same single inherited source-content warning.

Final self-review changed prefix trimming from generic ASCII whitespace to the
exact PDF set: NUL is admitted and vertical TAB is rejected by original controls.
At final candidate `ab2c23738ca360f1444e79a8ea07c00d07095c5a`, all **296 PDF/KDH/CAJ
originals** were rerun; every status and output hash equals the full-run candidate.
HN/C8 does not use this PDF-input gap checker. The recovered original again
passes native/Node/Chromium with the newly rebuilt WASM; the receipt preserves
both runtime runs and distinguishes the final affected-cohort check from the
earlier full-corpus run.

The frozen regression harness retains 26 historical order failures; the separate
corrected checks in PRs #16/#17 and [complete native-glyph evidence](native-content-completion-20261008.md)
resolve their applicable scope. This receipt does not rewrite the old checker
history. The missing 936 bitmap oracles, broader source geometry/render checks,
source-outline research and 44 refusals remain under rust #406. The prior 1,232
accepted originals have complete three-runtime parity at PR #408; this new
candidate checks the newly recovered original in both JavaScript runtimes.
It is not a full JavaScript rerun at the new candidate.

Original MIT tests and metadata only; no new dependency or committed external
document/PDF/font/render bytes. No release is published.
