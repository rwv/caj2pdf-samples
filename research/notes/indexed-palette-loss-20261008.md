<!-- SPDX-License-Identifier: MIT -->

# Missing Indexed colors and the accepted-output audit

Follow-up to [Rust #420](https://github.com/rwv/caj2pdf-rust/issues/420), under
[#406](https://github.com/rwv/caj2pdf-rust/issues/406). The
[receipt](indexed-palette-loss-20261008.json) separates a source-data ambiguity
from a read-only lookup-length audit of the 1,252 accepted output PDFs.
No production repair, new conversion pass or release is claimed.

## What the unchanged failed original cannot determine

The [earlier inventory and viewer report](indexed-palette-boundary-20261008.md)
locates 64 short DeviceCMYK lookups in the 80-page original, SHA-256
`5e1ea482a56a2df02a2a452ac97949824c726471c88157e78441a1201b3d8697`.
All 64 are used on source page 24. Together they lack **at least 12,405
component bytes** relative to their declared Indexed bases and hival values.
This lower bound treats every apparent raw byte as available; literal decoding
cannot supply the missing bytes. None of the six complete explicit CMYK tables
has both sufficient length and a matching short-table prefix. The comparison
includes tables with larger hival; one malformed literal has no valid decoded
prefix to compare. Arbitrary stream bytes are not treated as implicit palettes.

The new [source-specific diagnostic](../scripts/indexed_palette_loss_probe.py)
uses syntactically complete object 319, avoiding the malformed terminator in
neighbor 320. It requires the exact original hash, reads measured object spans,
and independently inflates Form 386 and its 33 × 15 inline image with bounded
zlib output. All **495 original indices** survive, and all **44 index values**
occur. The lookup declares DeviceCMYK/hival 43 but contains only **3 of 176**
required decoded bytes.

Two diagnostic PDFs preserve those three bytes and all original indices.
They differ only in invented missing components: one sets all missing black
components to zero, the other to 255. Both pass qpdf. At RGB72 they differ by
**49,981 pixels in Poppler** and **49,500 in MuPDF**. Neither completion is a
repair or an assertion about intended colors. This demonstrates that the
surviving prefix and indices do not uniquely determine the missing colors.
The standalone rerun reproduces the previous palette/index/render hashes.
Derived PDFs, palettes and pixels remain external.

Three pinned GitHub file entries—the original reporter's YanB25/caj2pdf
commit, CAJSamples' initial issue-39 commit and the current corpus pin—share
Git blob `fe7728e20573b17f490022685b6d5dd877f07991`, matching the local original.
The receipt links each exact file and records its size. The returned
path-specific histories each contain one adding commit. Scoped Chinese-title,
title/author/PDF, and English-title web searches found no intact document;
the [patent citation](https://patents.google.com/patent/CN103986738A/zh) is
bibliographic evidence only. Neither search indexing nor these checked paths
prove that no intact external edition exists.

The existing 16-session viewer evidence, 80-page/615-stream/72-bookmark
diagnostics and renderer disagreements remain as previously recorded; they
were not rerun or relabeled as successful conversion. In particular, reproducing
one viewer's omission of an image does not recover that image's missing colors.

## Read-only audit of accepted output PDFs

[indexed_lookup_audit.py](../scripts/indexed_lookup_audit.py) checks every
indirect object and nested direct value, plus inline-image dictionaries in
each complete page content sequence, Form and tiling-pattern stream. It checks
base component counts, hival and decoded lookup lengths. Flate decoding is
bounded and independently compared with qpdf; a measured trailing whitespace
byte is recorded. PDF ASCII85 is also independently decoded and compared.
Unknown filters, decoding boundaries and content parser warnings do not count
as completed checks. The report does not prove which palettes execute or that
all image indices, colors, geometry, text or outlines are correct.

The audit hashes each PDF before and after inspection. Those are output-PDF
integrity checks, not fresh hashes of all original CAJ files. Inputs are the
1,250 primary successful outputs from the reviewed #457 native regression,
one extended NH output and the separately cataloged #449 archived PDF. They
cover 35,587 pages. The converter executable and reviewed source/WASM identities
are pinned in the receipt; intervening #458 changes only documentation.

All 1,252 inspections complete with **13,004 exact-length lookups, 475 extra-length
lookups and no short or unresolved lookup**. There are 7,684 inline images and
no content parser warning; one pre-existing duplicate-annotation warning remains.
Per-input outcomes are in the receipt. Extra lookup bytes are retained as
`EXTRA`, not silently truncated or treated as intended colors.
The duplicate-annotation warning is retained separately from content parsing.
No new whole-document compatibility pass follows from a sufficient lookup length.

The first exploratory audit failed on 996 documents because an indirect PDF
integer is exposed as a Python integer, not a pikepdf Object. Later exploration
left 1,281 Flate tails and 34 ASCII85 lookups unexamined until independent
decoding controls established their boundaries. Review then found that parsing
each member of a page's Contents array separately produced six content warnings
in two documents. Page content is now parsed as one logical sequence; nonfatal
parser warnings explicitly make inspection incomplete. Earlier runs and their
hashes remain in the receipt and are not compatibility evidence.
The first grouped-content run also aborted one 137-page document within the
worker limits. Review found the previous page's parsed instruction list still
held during parsing of the next page. Releasing it before advancing lets that
document complete under the same limits; the failed attempt is retained.

## Runtime refusal, reproduction and scope

The reviewed #457 CLI still rejects the unchanged #420 original at source byte
898,312 with `invalid PDF value token`, exit 1, publishing no PDF or temporary
file. Fresh Node and Chromium runs with the same reviewed WASM return
`MALFORMED_PDF`, the same byte/message and zero output bytes. Source hashes
remain unchanged; the browser OPFS directory is empty after cleanup. These are
expected-refusal checks, not conversion passes or proof of irrecoverability.

The general audit requires Python 3.11+ on a POSIX host and pikepdf 10.5.1.
Its JSON manifest is an array of `source_sha256`, `format`, `pdf` (external
path) and `pdf_sha256`. It creates a new external output directory. Two workers
each have a 1 GiB address-space limit, 40 CPU seconds and 50 seconds wall time;
graph, instruction and lookup limits are explicit in the source. pikepdf may
materialize a content stream within that process cap; this is not the
converter's streaming I/O implementation.

```sh
python3 research/scripts/indexed_lookup_audit.py manifest.json /external/new-audit
python3 -m unittest discover -s research/conformance -p 'test_indexed_lookup_audit.py' -v
python3 research/scripts/indexed_palette_loss_probe.py /external/original.caj /external/new-diagnostic
```

The source-specific diagnostic additionally uses external qpdf 12.2.0,
Poppler 25.03.0, PyMuPDF 1.27.2.2, NumPy 2.4.3 and Pillow 12.1.1. The
pikepdf wheel uses libqpdf 12.3.2, distinct from the command-line qpdf. Its output is
document-derived and must stay outside Git. Eight original control groups cover
short/exact/extra tables, inline images, independent Flate/ASCII85 decoding,
truncation/limits, PDF identity, split content sequences and nonfatal warnings.
CI runs only synthetic controls, without downloading the corpus.

All committed code is original MIT research, based on public PDF syntax and
source observations. No converter or vendor implementation was inspected,
copied or translated. Production dependencies, APIs, support and release
behavior do not change. The concrete missing-color boundary satisfies #420's
document-a-boundary alternative; intended-color recovery and complete accepted
whole-original conversion remain unmet. #420 and #406 stay open. Review is
self-review, not independent approval.
