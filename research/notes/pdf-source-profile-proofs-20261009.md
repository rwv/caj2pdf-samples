<!-- SPDX-License-Identifier: MIT -->
# Individual PDF source-profile proofs, 2026-10-09

The ten unverified profiles in the [previous checkpoint](pdf-source-preservation-20261009.md)
now have individual source/field proofs. A fresh complete **279-original**
acquisition verifies each selected-object, opaque raw-stream and navigation
scope under [samples #65](https://github.com/rwv/caj2pdf-samples/issues/65).
The [per-source receipt](pdf-source-profile-proofs-20261009.json) preserves every
original/output identity, acquired difference and reader result. The previous
269/10 checkpoint remains unchanged and hash-pinned.

The complete verified scopes cover **19,039 pages, 222,640 selected original
objects, 112,410 raw streams and 11,976 outline nodes**. The ten new proofs
account for 939 pages, 6,364 objects, 3,278 streams and 688 outline nodes.
These are preservation audits: the conversion ledger remains **1,252 PASS /
18 FAIL / 27 UNSUPPORTED**, and [Rust #406](https://github.com/rwv/caj2pdf-rust/issues/406)
remains open for broader fidelity and refusal questions.

## Individually justified changes

| Original prefix | Pages | Proof |
| --- | ---: | --- |
| `2423e0b8e640` | 163 | Three measured malformed Pattern Matrix values become the previously measured identity fallback. |
| `f08947012a48` | 101 | One Matrix fallback with the same strict profile. |
| `d3d8a89dc8ac` | 109 | Remove two optional Link AP dictionaries whose original single N references are missing; preserve destinations and every other field. |
| `b206e40da6df` | 139 | Preserve two literal QITE path payloads as exact bytes and restore 137 original QITE/F edges; every incoming reference has the exclusive proved Page metadata role. |
| `2508ca0e325b` | 85 | Remove one Link Dest to absent target 226; null its exclusively used indirect destination array. |
| `52c98a3112c7` | 60 | Remove one direct Link Dest to absent target 154. |
| `964975c2d326` | 65 | Remove three direct Link Dests to absent target 214. |
| `fc8a5c20626b` | 84 | Remove one Link Dest to absent target 316; null its exclusively used indirect destination array. |
| `49be4cec9ac6` | 58 | Complete source accounting verifies the independent 215-object selection and all 75 original streams. |
| `5d988d74a6e6` | 75 | Complete source accounting verifies the independent 291-object selection and all 87 original streams; source-viewer geometry remains separate. |

The first four cases use [Matrix](pattern-matrix-fallback-20261008.md),
[appearance](missing-link-appearance-20261008.md) and
[QITE](qite-source-path-strings-20261008.md) reports pinned by SHA-256. Source and
output identities must match those reports. The code rechecks bounded original
metadata witnesses, measured field values and reference roles before constructing
expected values. It then compares every selected object and raw stream again.
No field name is globally excluded. Scientific-notation interpretation is not
substituted for the measured Matrix fallback. Paths are never opened or used
as filesystem paths. Prior rendering and proof limitations remain applicable.

The four missing-destination cases additionally account for their entire
original PDF body. Raw bounded syntax proves each destination's original
reference; absence is not inferred from qpdf's serialized null. The target
has no definition and is not a table Page. Only measured Link annotations
with zero border width, no other action/appearance and an XYZ destination
qualify. An indirect array can become null only if all incoming references
are the removed Link Dest fields. Every other annotation value is preserved.

## Complete source accounting for six originals

The [source-only plans](caj-source-accounting-plan-20261009.json) contain original
offsets, stream extents/hashes, duplicate and interrupted-copy locations. They
are inputs to validation, not accepted proof results. They contain no document
bodies or candidate-derived offsets. The checker requires the selected identities
to match the independent reader inventory, checks the exact generated xref,
and parses each complete non-stream value or stream dictionary from its original
bounded range. Stream programs and embedded font bodies remain opaque.

Every byte from the independently read page-table body start through EOF must
belong to a checked selected object, identical complete duplicate, identical
proper prefix, tightly scoped partial header, or bounded whitespace gap. It
rejects overlaps, unexplained bytes and ObjStm/XRef streams that could hide
additional metadata references. Direct or selected indirect Length must equal
the hashed encoded stream extent. Every table Page has a complete definition.

The four destination bodies contain no interruptions or non-whitespace gaps.
The two recovery bodies together contain **13 identical complete duplicates,
40 strict proper prefixes and 67 partial headers**. A proper prefix must match
a longer complete copy of the same object, end with the measured CRLF separator,
and be followed by a recognized full object header. Each partial header must
match a selected source-table Page (26 occurrences) or a nonnegative scalar
used exclusively as Length by validated streams (41 occurrences). A trailing
unanchored header is rejected. No source object or stream is invented to fill
an interruption.

The original MIT syntax subset reuses this repository's bounded display-value
grammar, adding CR comment termination, reversible opaque non-ASCII PDF names
and arrays up to 4,096 items. Per-object metadata stays at 16 KiB, nesting at 64,
dictionary keys at 64 and names at 128 bytes; gaps are at most 256 bytes.
Copies, comparisons and hashes use at most 64 KiB per chunk. Existing document,
reader, graph and JSON ceilings remain in force. This is a research verifier,
not a new production parser or a universal source-recovery claim.

## Verification, retained failures and limits

The public runner now selects these ten exact-source profiles automatically:

```sh
python3 research/scripts/pdf_source_preservation.py \
  --manifest /external/manifest.json --output /external/new-audit
PYTHONPATH=research/scripts python3 -m unittest discover \
  -s research/conformance -p 'test_pdf_source_*.py' -v
```

The complete fresh run exits 0 with 103 PDF/KDH graph proofs, 158 ordinary CAJ
proofs, eight earlier reviewed CAJ selections, four individual field proofs
and six complete source-accounting proofs. It does not run the converter.
Reader warnings are retained in the receipt, even for verified profiles.

All **46 original PDF-family controls pass, with zero skips**, including 15 new
tests. New negatives cover live destination targets, other array consumers,
visible borders/actions, altered raw streams/resources, wrong duplicates or
prefixes, hidden metadata streams, unknown gaps, incorrect declared lengths,
wrong roles, unanchored headers and syntax limits. The first control run exposed
a mistaken literal length in a corruption setup; the setup assertion failed
before exercising the checker. The corrected setup and final full suite pass.
Earlier syntax-limit and bare-ID-prefix refusals remain retained, alongside
the earlier unreviewed two-source selection probes. The receipt hashes these
attempts and the unchanged as-run/reviewed source files.

The earlier `5d988d74a6e6` **page-reference** diagnostic exits 3: its 75 leaves
lack MediaBox and qpdf supplies letter/ANSI A. The new **blank inventory** reads
without warnings, but cannot resolve or replace that source-viewer geometry
question. Matching generated fallback fields establishes only the recorded
profile. The six complete source-body proofs do not extend recovery completeness
to the other 273 inputs. Original viewer fonts/ornaments, rendering readiness,
unknown native-format outlines and refusal recovery remain separate.

New Python and generated controls are original MIT work using only public
project grammar and independently reviewed source facts. No foreign converter,
private HN/JBIG, vendor implementation or vendor font programs/outlines were
inspected or migrated. Documents, PDFs, titles, stream/font bodies, rasters and
binaries remain external. No production code, API, output PDF, supported format
or release changes result from this evidence update.
