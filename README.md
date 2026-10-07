# caj2pdf-samples

Real-document catalog and regression inputs for [caj2pdf-rust](https://github.com/rwv/caj2pdf-rust).

## Current collection

**1,277 distinct document candidates** are indexed, including 1,217 new
SHA-256 identities from the [2026-10-07 GitHub sweep](research/notes/github-sample-sweep-20261007.md).
After the [profile fixes and full native rerun](research/notes/github-sweep-fixes-20261007.md)
(caj2pdf-rust `a199539`, identical tree to the tested `18417d8`), **1,227 convert,
39 fail and 11 are explicitly unsupported**: 99 new conversion passes and no
conversion regressions. Of the outputs, 1,226 pass qpdf without warnings;
one retains its source-content warning. All 50 refusals are classified, including
16 encrypted PDFs and nine encrypted TEB containers. Seven synthetic fixtures
are excluded. Conversion/qpdf results do not establish full fidelity: 26 ancillary
image-order failures remain visible, and full-corpus JavaScript/visual checks
are NOT_RUN.

The `external/github/` rows record pinned download URLs or archive members.
Acquire their bytes in an external cache; this repository contains metadata only.
See the [current per-input receipt](research/notes/github-sweep-fixes-20261007.json)
for all attempts and classifications, and the unchanged
[baseline receipt](research/notes/github-sweep-20261007.json) for collection
boundaries and original failures.

## Initial collection

60 distinct documents indexed: the 56 existing samples below, three
[C8/HN-B search candidates](research/notes/hnc8-outline-sample-search.md), and a newly
collected 238,910,818-byte HN-A document from upstream issue 111 (738 pages,
1,450 bookmarks). Its complete native, Node and browser conversions are recorded
in [the research notes](RESEARCH.md); viewer comparison remains NOT_RUN.

56 distinct real documents from the pinned upstream CAJSamples collection:
17 CAJ, 22 HN, 5 C8, 3 KDH, 2 PDF and 7 TEB. All 56 local files were checked
against their SHA-256 and byte size during initial import. Aliases are retained;
identical content is not counted twice. These are existing samples, not 56 newly
discovered documents. Format labels are imported observations, not proof that
all layouts in a family are supported.

The public catalog records provenance, hashes and locations. Upstream has not
declared document redistribution permission, so its document bytes are not
mirrored here. Code and original documentation are MIT; that license does not
relicense third-party documents. Original or explicitly MIT-licensed contributed
real documents may be stored under `samples/` after provenance review.

## Use

Obtain the upstream corpus separately at revision
`7e1c35e7b6de34e21972fcd1752c2a7e99b4ad07`:
https://github.com/caj2pdf/CAJSamples

```sh
python3 tools/verify.py /path/to/local-corpus
```

For the additional sample, obtain the document linked from upstream issue 111
and place it at `issue-111/56.caj` beneath the local corpus root.
The three C8/HN-B candidates have pinned source URLs and canonical `external/`
paths in `catalog.json`; their recorded failures refer to the stated converter
revision, with later C8 results in the [follow-up note](research/notes/c8-additional-profiles.md).

The verifier reads in bounded chunks, checks every catalog entry and exits
nonzero for missing or changed files. It does not execute converters or count
integrity checks as compatibility passes. Store downloads in an external cache.

## Collection priorities

1. CAA and CAS: obtain authentic files; determine whether each is a document,
   link/descriptor or container before proposing a decoder.
2. NH: obtain files with their original extension and identify their bytes;
   do not assume the extension maps one-to-one to an HN layout.
3. New CAJ/HN/C8/KDH failures: prefer a new structure or reproducible failure
   over another copy of an already represented document.

The original seven TEB files share one encrypted DRM container layout (see
[research notes](RESEARCH.md)); more TEB copies add no format evidence. The
CAA/CAS/NH search log is recorded there with the remaining sample gaps.

See [research notes](RESEARCH.md) and repository issues. Public issue reports
should contain a source URL and hash, not attachments with unknown rights.

## Checks

`python3 tools/check_catalog.py` validates `catalog.json` structure (fields,
hashes, unique paths and digests, status values, formatting) without the
corpus; CI runs it on every pull request. After reviewing a catalog change,
pin its committed revision and catalog SHA-256 in
[`research/scripts/sample_catalog.py`](research/scripts/sample_catalog.py).

## Adding a sample

Record source URL/revision, original path/extension, byte size, SHA-256,
observed format, and redistribution evidence. Deduplicate by SHA-256. For a
public binary contribution, include the author's explicit MIT grant and remove
personal or confidential material before submission. Do not call a renamed or
synthetic document a real historical sample.

For a regression result, record converter commit, options/resources, status,
page count and the exact failing page/error. Viewer comparisons also need the
viewer version, fonts, rendering settings and selected pages. Missing inputs
are `NOT_RUN`; successful opening is not pixel or text equivalence. Keep raw
renders/text external unless their redistribution is established. Reuse the
research runners in [`research/`](research/README.md); no second conversion or
oracle framework.

## Research tooling

[`research/`](research/README.md) holds the oracles, conformance harnesses,
CAJViewer automation, archived Rust parity examples and investigation notes
moved out of caj2pdf-rust
([#360](https://github.com/rwv/caj2pdf-rust/issues/360)), pinned to
caj2pdf-rust commit `0abee3862f01756ee15f69a1b174a35208fc1e41`. Its README
explains each directory and how to run the Python harnesses against a caj2pdf
CLI and a local corpus.
