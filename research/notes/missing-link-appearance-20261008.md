<!-- SPDX-License-Identifier: MIT -->

# Missing optional Link appearances

[rust #417](https://github.com/rwv/caj2pdf-rust/issues/417) and
[PR #418](https://github.com/rwv/caj2pdf-rust/pull/418) recover an unchanged
109-page CAJ original containing two absent normal appearance targets.
The [receipt](missing-link-appearance-20261008.json) pins its immutable origin,
source/decoder/output identities, all-page measurements, runtime parity and
the complete 1,277-input / 2,126-attempt native ledger.

Of 75 direct Link appearance references, objects 82 and 518 target absent
objects 10887 and 10886. Both have live destination pages and a direct BS
containing only zero W. The bounded repair removes just the parsed AP pair
when N is the sole appearance entry and its missing generation-zero target
occurs once in the complete Link object. It preserves other bytes, live
appearances and required references. Other states, border profiles, actions,
missing destinations and unrelated annotations remain outside this repair.
[Adobe PDF 1.4, section 3.2.8](https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/pdfreference1.4.pdf)
specifies null semantics for nonexistent indirect references.

The independent source oracle copies body bytes `[154216, 6552931)` verbatim
and adds only a Catalog pointing to existing source Pages root 2, with minimal
repair framing. It uses no converter output to reconstruct source content.
Qpdf independently normalizes that source body; reconstruction warnings
(exit 3) remain recorded, while the normalized reference and converted PDF
check clean. Comparisons use the raw framed source, not qpdf output.

All **109 page IDs, 574 raw streams, 75 link destinations, text, page boxes,
rotation and RGB page renders at 72 dpi** match the framed source in PyMuPDF
1.27.2.2. All **70 source bookmarks** pass a separate independent CAJ outline
check. The only changed source nonstream objects are annotations 82 and 518;
Catalog 10976 is new framing, and the converter Catalog also includes the CAJ
container outline. This is scoped source-PDF evidence, not a CAJViewer or
all-renderers/resolutions claim.

Native, Node and Chromium outputs have identical hashes; browser temporary
storage is empty afterward. The full native rerun gives **1,236 PASS / 31 FAIL /
10 UNSUPPORTED**, exactly one improvement. Every previously passing PDF hash
is unchanged; source hashes are intact and every refused attempt leaves no
output. Earlier complete JavaScript parity retains its own candidate pins;
this candidate's JavaScript run covers the recovered original.

Original MIT controls cover live appearances, required missing targets, strict
neighboring profiles, source mutation, bounded reads/allocation and all
cancellation checkpoints. MuPDF does not paint Link AP in the synthetic
control: live Link references/stream bytes are checked structurally, and a
neighboring Square annotation supplies a visible appearance control.
The Rust workspace reports 1,282 passes and seven optional-corpus tests ignored;
JavaScript reports 164 passes. Ignored tests are not compatibility evidence.

The frozen native harness's 26 old order failures and 936 NOT_RUN bitmap checks
remain visible. Their separate corrections and bitmap/glyph evidence were
published in samples PRs #16/#17/#20/#24. Rust #406 remains open for 41 refusals
and broader content/layout/outline fidelity work. No source document, PDF,
pixel, font or foreign implementation bytes are committed. No release is
published.
