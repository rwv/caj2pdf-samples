<!-- SPDX-License-Identifier: MIT -->

# Equivalent opacity resource references

[rust #412](https://github.com/rwv/caj2pdf-rust/issues/412) and
[PR #413](https://github.com/rwv/caj2pdf-rust/pull/413) recover two unchanged KDH
originals by proving that a repeated ExtGState resource name refers to exactly
equal direct CA/ca values. The [receipt](equivalent-opacity-resources-20261008.json)
pins origins, source/decoder/output identities, all-page evidence, runtimes and
a complete native per-input ledger.

The nine-page source repeats targets 3/43 on eight pages; both opacity pairs
are 0.08/0.08. The five-page source repeats targets 3/9 on every page, using
0.08/0.08 and 0.08000/0.08000. The implementation compares decimal digits
exactly. Only one duplicate reference pair at a non-stream Page's direct
Resources/ExtGState path qualifies; both live generation-zero targets must
contain just direct CA/ca values in [0, 1], with a 256-byte target bound and at
most 64 fractional digits. Unknown/conflicting profiles remain errors.
[Adobe's field documentation](https://opensource.adobe.com/dc-acrobat-sdk-docs/acrobatsdk/apireference/PDFEdit_Layer/PDEExtGState.html)
provides the public alpha semantics. No foreign converter source was used.

All **14 pages, 151 raw streams and 13 changed Page resource maps** are verified
against independently decoded original PDF bytes. Page identities, text, all
boxes, rotation and RGB pixels at 72 dpi match; stream identities/bytes match.
Both original and output outline inventories are empty. Original body bytes
remain present except existing CR stream-separator normalization; the resource
repair adds incremental Page revisions. Qpdf's original duplicate-key warnings
are retained (exit 3); both outputs pass without warnings. These are scoped
source-PDF comparisons, not CAJViewer or every-renderer/resolution claims.

Native, Node and Chromium PDF hashes agree for both recovered originals, with
empty browser OPFS storage after each. The full **1,277-original / 2,126-attempt**
native rerun yields **1,235 PASS / 32 FAIL / 10 UNSUPPORTED**, exactly two
improvements and no changed previously passing PDF hash. All source hashes
remain intact, and every refused default conversion leaves no output file.
Qpdf reports 1,234 clean outputs and the same inherited source-content warning.

The baseline full run and its final PDF-whitespace cohort are pinned separately;
all 296 affected originals had identical baseline hashes after that final change.
The current candidate's full native run is direct evidence. Earlier JavaScript
parity retains its own candidate identities; this is not a full latest-candidate
JavaScript rerun. The frozen harness still records 26 historical order failures,
whose applicable checks were independently corrected by samples PRs #16/#17/#20.
The missing 936 bitmap oracles, broader source geometry/content/render/outlines
and 42 refusals remain under rust #406. No release is published.

Original MIT tests cover strict neighboring references/types/paths, decimal
precision, target bounds, one-byte reads, cancellation, visible opacity controls
and resource repairs combined with stale parents and inactive object prefixes.
Source/PDF/font/render bytes and external tools stay outside the repositories.
