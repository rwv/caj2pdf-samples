# caj2pdf-samples

Real-document catalog and regression inputs for [caj2pdf-rust](https://github.com/rwv/caj2pdf-rust).

## Current collection

**1,297 unique inputs** are indexed: 1,279 document candidates and 18 CAA
target descriptors. The [2026-10-08 discovery](research/notes/caa-nh-discovery-20261008.md)
adds one original-extension NH document (433 pages/365 bookmarks, identical
CLI/Node/Chromium outputs) and 18 metadata-only CAA entries. CAA conversion
is unsupported; their target declarations are not document pages.

### Latest complete runtime checkpoint

The [current per-input receipt](research/notes/current-corpus-runtime-20261008.md)
records **1,252 conversion PASS, 18 FAIL and 27 UNSUPPORTED** across all 1,297
identities. Every accepted input now has fresh Node and Chromium output matching
the reviewed #457 native hashes, sizes and page counts (35,587 pages). All 45
remaining inputs have fresh three-runtime refusal, source-integrity and cleanup
checks; these are not conversion passes or proof of irrecoverability.
All catalog conversion statuses point to this common reviewed build.

The [source geometry report](research/notes/source-image-geometry-20261008.md)
adds independent declared-page and ordered-image checks for all 973 accepted
HN/C8/NH originals (16,548 pages), including new bitmap evidence for the
433-page NH. This scoped measurement does not establish native glyph/vector
placement, complete rendered-page fidelity or unknown C8/HN-B outlines.

The [native composition checkpoint](research/notes/native-page-composition-20261008.md)
adds all 60 native pages with normal and original marker fonts, per-page
text/vector/image inventories, bounded complete-page observations and retained
pixel differences. One normal-font page differs across cold viewer sessions;
these observations do not establish complete rendered-page fidelity.

The [849-source C8/HN-B outline investigation](research/notes/hnc8-outline-inventory-20261008.md)
retains unknown source-outline status and corrects an old 132-page example to
HN-A with 81 bookmarks. Full source correctness and general viewer readiness
remain open under [Rust #406](https://github.com/rwv/caj2pdf-rust/issues/406)
and [#441](https://github.com/rwv/caj2pdf-rust/issues/441).

### Earlier named-destination checkpoint

The [named-destination report](research/notes/named-destinations-20261008.md)
adds a separately collected 139-page archived author PDF. Native, Node and
Chromium preserve its bytes exactly; all 139 page renders, 97 outlines and
889 named links agree with independent readers. It is a distinct identity
outside the GitHub baseline and does not replace the truncated 134-page CAJ
in [Rust #448](https://github.com/rwv/caj2pdf-rust/issues/448).

The fresh 1,277-original native regression retains **1,248 PASS, 20 FAIL and
nine UNSUPPORTED**, with every previously successful output hash unchanged.
All 19 extended inputs retain their results (one NH pass, 18 CAA refusals).
Ancillary failures and unexecuted checks remain explicit; the full sample
correctness goal and vendor-viewer readiness limits stay open under
[Rust #406](https://github.com/rwv/caj2pdf-rust/issues/406) and
[#441](https://github.com/rwv/caj2pdf-rust/issues/441). The earlier 1,247-input
Node/Chromium run used reviewed #444 code; it is not relabeled as this new
implementation's full-corpus WASM run.

### Previous 1,277-document checkpoint

**1,277 distinct document candidates** are indexed, including 1,217 new
SHA-256 identities from the [2026-10-07 GitHub sweep](research/notes/github-sample-sweep-20261007.md).
After the [#402/#404 follow-up and full native rerun](research/notes/pdf-predictor-object-streams-20261007.md)
(caj2pdf-rust `73d62a6`), **1,228 convert, 39 fail and 10 are explicitly
unsupported**. One additional original now converts; every previously passing
attempt retains its PDF hash, with no conversion regressions. Of the outputs,
1,227 pass qpdf without warnings; one retains its source-content warning.
The [previous profile-fix checkpoint](research/notes/github-sweep-fixes-20261007.md)
records the preceding 99 new passes and refusal classifications. Seven synthetic
fixtures are excluded. Conversion/qpdf results do not establish full fidelity:
26 ancillary image-order failures remain visible, and full-corpus JavaScript
and rendered-page checks are NOT_RUN. The #402 original separately passes all
three runtimes and all 10 page renders against its unchanged decoded PDF.

The `external/github/` rows record pinned download URLs or archive members.
Acquire their bytes in an external cache; this repository contains metadata only.
See the [historical predictor per-input receipt](research/notes/pdf-predictor-object-streams-20261007.json)
for all attempts, the [preceding classifications](research/notes/github-sweep-fixes-20261007.json), and the unchanged
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

1. CAS: obtain authentic bytes and determine its layout; tracked in #28.
2. CAA: investigate historical viewer/target-resolution behavior. The 18
   observed descriptors are not complete documents; Linux 9 refuses them.
   Additional original-extension NH files may reveal layouts beyond the
   measured HN-A sample.
3. New CAJ/HN/C8/KDH failures: prefer a new structure or reproducible failure
   over another copy of an already represented document.

The original seven TEB files share one encrypted DRM container layout (see
[research notes](RESEARCH.md)); more TEB copies add no format evidence. The
historical CAA/CAS/NH search log is recorded there; the new discovery above
resolves the NH/CAA byte-sample gaps, while CAS remains unresolved.

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
