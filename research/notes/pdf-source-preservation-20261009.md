<!-- SPDX-License-Identifier: MIT -->
# PDF-family selected-object preservation, 2026-10-09

The complete **279-source** PDF-family cohort was acquired and checked under
[samples #65](https://github.com/rwv/caj2pdf-samples/issues/65) and
[Rust #406](https://github.com/rwv/caj2pdf-rust/issues/406): 176 CAJ, 71 KDH and
32 PDF originals, totaling **19,039 pages**. The
[per-source receipt](pdf-source-preservation-20261009.json) records all original
and reviewed-output identities, reader results, differences and proof outcomes.
**269 sources pass their stated preservation scope; ten remain NOT_VERIFIED.**
The verified scopes cover 18,100 pages, 216,276 selected original objects,
109,132 raw streams and 11,288 outline nodes.
These are audit outcomes. No conversion is rerun or added to the existing
1,252 PASS / 18 FAIL / 27 UNSUPPORTED ledger.

## Method and scope

The original MIT [runner](../scripts/pdf_source_preservation.py) checks source
and output hashes before acquisition and after reading. PDFs are read directly.
KDH uses an independent sequential FZHMEI transform from offset 254, retaining
and verifying the entire decoded tail. CAJ body bytes are copied through EOF,
followed by three fresh inventory-only objects and an index. The blank inventory
page is not a source rendering reference. Navigation is checked independently
against the original page table and bounded 308-byte bookmark records.

External qpdf 12.2.0 emits JSON v2 and raw encoded stream files with
`--json-output=2 --json-stream-data=file --decode-level=none`. Its documented
[`calledgetallpages` and `pushedinheritedpageresources` flags](https://qpdf.readthedocs.io/en/stable/json.html)
must both be false. JSON v2 omits stream Length; raw sizes and hashes are
compared separately. Exact Decimal parsing preserves every digit, including
changes beyond ordinary floating-point precision. Tagged values distinguish
booleans, integers and reals. Reader warnings and failures remain visible.

Verification rehashes JSON, warning logs and raw artifacts, reconstructs every
difference and checks counts. It checks page order/parents, outline hierarchy,
destinations/backlinks, candidate indirect references, and exact added Catalog,
Pages, Outlines and trailer fields. Resource/geometry values are included in
selected-object comparison. Checking generated fallback geometry against the
measured profile does not establish a new source-viewer geometry rule.

| Verified scope | Sources | Qualification |
| --- | ---: | --- |
| PDF/KDH selected values, streams and graphs | 103 | Only proved backlink/parent, equivalent opacity, trailer and exact-source empty-Form repairs are allowed. |
| CAJ selected values/streams and source navigation | 158 | Original differences are only checked missing-Parent insertions; generated framing has exact allowed fields. |
| CAJ with reviewed source-selection/recovery profiles | 8 | Source offsets, source/output/report hashes, stream extents and generated xref slots are checked again. Earlier omission/repair limits remain applicable. |
| Not yet verified | 10 | All differences are retained; no broad exclusion turns these into passes. |

All 176 CAJ page sequences and 10,876 title/page/depth records retain their
earlier independent navigation proof against the same output identities.
That measurement is not relabeled as new all-page rendering.

## Reviewed complex selections

Qpdf recovery can select interrupted copies or infer incorrect stream extents.
Eight cases instead use complete source offsets from previously reviewed
reports, never candidate PDF bodies or offsets:

- [Interrupted copies](interrupted-copies-20261008.md): `cb6f5e781f37`, `f26570f28a20`, `f65742f37f10`.
- [Indirect lengths](indirect-length-replays-20261008.md): `c41cd7306591`.
- [Interrupted metadata/parents](interrupted-metadata-parents-20261008.md): `50c8c55b978a`.
- [Retained catalog](retained-catalog-20261008.md): `eacbcd00c35a`; its bounded original Catalog and unchanged label tree also prove the PageLabels connection.
- [Redundant framing](redundant-caj-framing-20261008.md): `dc3c3a651d4a`.
- [Thirteen-site recovery](stream-substitution-recovery-20261008.md): `5a4432ed4878`; the exact transform is rebuilt and hash-checked.

Fresh references keep the entire source tail. Xref slots must select exactly
the reviewed offsets and three authored objects. Stream extents/hashes and
available complete-object hashes are rechecked. The 13-site reference is
**reconstructed recovery evidence**, not an independently obtained intact
alternative. Prior complete-prefix, omission, catalog-role and rendering proofs
apply to identical source/output hashes; they are not newly executed here.

## Ten remaining profile proofs

These are not new demonstrated conversion failures. The generic audit still
needs individual proof integration for these repairs or reader differences.

| Original SHA-256 prefix | Pages | Remaining boundary |
| --- | ---: | --- |
| `2423e0b8e640` | 163 | Three malformed Pattern Matrix fallbacks; [existing report](pattern-matrix-fallback-20261008.md). |
| `f08947012a48` | 101 | One Matrix fallback, same report. |
| `d3d8a89dc8ac` | 109 | Two missing Link appearance removals; [existing report](missing-link-appearance-20261008.md). |
| `b206e40da6df` | 139 | Two malformed paths/restored QITE references; [existing report](qite-source-path-strings-20261008.md). |
| `2508ca0e325b` | 85 | Invalid Link destination removal and emptied indirect array. |
| `52c98a3112c7` | 60 | Invalid direct Link destination removal. |
| `964975c2d326` | 65 | Three invalid direct Link destination removals. |
| `fc8a5c20626b` | 84 | Invalid Link destination removal and emptied indirect array. |
| `49be4cec9ac6` | 58 | Source-recovery object/stream selection differs. |
| `5d988d74a6e6` | 75 | Source-recovery object/stream selection differs. |

The four destination cases need original-reference and target/role proof beyond
qpdf's null rendering of unresolved targets. The last two need complete source
selection proof independent of converter output. Samples #65 and Rust #406
remain open.

## Reproduction and original controls

Supply an external JSON array containing `source`, `source_sha256`, `pdf`,
`pdf_sha256`, `format` and positive `pages` fields. Paths are local external
artifacts; the output directory must not exist:

```sh
python3 research/scripts/pdf_source_preservation.py \
  --manifest /external/manifest.json --output /external/new-audit
PYTHONPATH=research/scripts python3 -m unittest discover \
  -s research/conformance -p 'test_pdf_source_*.py' -v
```

Without external arguments, the runner reports NOT_RUN and zero attempts.
An explicit incomplete audit exits nonzero and preserves every result. This
complete measured run exits 1 because ten profiles are NOT_VERIFIED; it did
not crash or omit an acquisition. Public evidence contains identities, counts,
object IDs and hashes; document values and artifacts stay external.

Thirty-one original tests pass with zero skips. They cover changed streams,
resources, page order, omissions, a 32nd-decimal-digit mutation, graph cycles,
backlinks, metadata bounds, extra generated semantics, altered JSON/count/delta
receipts, raw-artifact tampering, incorrect xref slots, source-range limits and
site reconstruction. KDH checks reject changed/missing/extra decoded-tail
bytes. A CAJ fixture places a stream and later object beyond the table hint;
both must survive. Original bodies are generated in temporary directories,
without external corpus or vendor-font fixtures.

## Bounds, retained attempts and provenance

Documents/references and each reader output file are capped at 512 MiB, JSON
at 32 MiB, and objects at one million. Graph depth is at most 128; pages and
outline nodes at most 100,000. Ordinary copies/hashes use 64 KiB chunks. Each
qpdf child has 2 GiB address space, 110 CPU seconds, 120 wall seconds and no
core dumps. POSIX resource limits are required. These are per-file/process
bounds, not a global temporary-disk quota or a production conversion API.

Earlier attempts remain retained. An overstrict post-NUL zero-fill assumption
first rejected four bookmark tables; bounded-prefix handling and negative
controls correct it. Earlier CAJ framing stopped at a table hint; 32 full-tail
reacquisitions corrected two apparent stream differences. This run acquires
all 279 afresh and retains those historical outcomes separately.
Final simplification removes five unused imports; every non-import AST node
matches the frozen acquisition source. Final controls are rerun, and both
as-run and reviewed source hashes are retained in the receipt.

New Python and generated controls are original MIT work from documented wrapper
facts, public qpdf documentation and this project's independent source reports.
Python/qpdf remain external research dependencies. No foreign converter,
private HN/JBIG, vendor implementation or vendor font programs/outlines were
inspected, copied or migrated. Ordinary stream bodies, including embedded
document fonts, are copied/hashed opaquely. Documents, PDFs, titles, stream/font
bodies, rasters and binaries stay external. No production API, I/O, output,
supported-format or release change follows.

Selected-object agreement does not prove that recovery found every source
object or establish full visual fidelity. Original fonts/ornaments, viewer
readiness, unknown C8/HN-B outlines and refusal recovery remain separate.
