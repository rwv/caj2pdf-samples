<!-- SPDX-License-Identifier: MIT -->

# GitHub sample collection and conversion sweep — 2026-10-07

## Result

The catalog expands from 60 to **1,277 distinct document candidates**: 1,217
new SHA-256 identities, with 2,740,801,965 bytes retained in the external cache.
This includes documents with misleading extensions: 47 are already PDF files.
Seven clearly synthetic converter fixtures and 37 non-document Git blobs are
excluded from these counts. This is a collection of inputs, not a declaration
that every input is well formed or that its publication grants redistribution.

The native CLI built from caj2pdf-rust
[`df6d0235cc60c82a36bc9eda9ae0529fda80a314`](https://github.com/rwv/caj2pdf-rust/commit/df6d0235cc60c82a36bc9eda9ae0529fda80a314)
was run on every catalogued input. The default conversion results are:

| Population | Converted | Failed | Explicitly unsupported | Total |
| --- | ---: | ---: | ---: | ---: |
| Previous catalog | 48 | 4 | 8 | 60 |
| New identities | 1,080 | 119 | 18 | 1,217 |
| All inputs | **1,128** | **123** | **26** | **1,277** |

Of the 1,128 outputs, **1,127 pass `qpdf --check` without warnings**. The
remaining warning is the previously catalogued `issue-20/文件名未知.caj`;
it is not a clean structural pass. None of the 149 rejected default conversions
publishes an output PDF. The status vocabulary comes from the existing
`current_formats.py` runner: `FAIL` includes typed malformed-input and ambiguous
repair refusals, not just implementation defects. Nine of the unsupported files
are TEB encrypted containers (seven previously catalogued, two new identities).

[Machine-readable evidence](github-sweep-20261007.json) contains each source,
revision or archive identity, byte size, SHA-256, inspection summary, exact
conversion diagnostic, qpdf result, and available page/outline checks.
The [catalog](../../catalog.json) contains canonical local paths and acquisition
locators. Document bytes, extracted text, PDFs and screenshots remain external.

## First failure groups

These are the first errors on unmodified inputs. A fix to one error can expose
another error later in the same document. A viewer opening a selected page does
not prove that every source object is valid or that every rejection should be
relaxed. The remaining strict PDF repair guards require their own evidence.

| First diagnostic | Documents |
| --- | ---: |
| PDF bytes after EOF are not a recognized footer, including `WebFastLoad` | 44 |
| C8 JBIG2 `SBRTEMPLATE without SBREFINE` | 25 |
| KDH wrapper field at `0x28` differs from the admitted profile | 15 |
| HN-A decoded record area is not a multiple of 16 | 12 |
| C8 unsupported compressed text header | 11 |
| TEB encrypted-container refusal | 9 |
| Other PDF structure/repair/profile errors, one CAJ span error, and two C8 profiles | 33 |

The complete 24-group breakdown and every member hash are in the JSON receipt.
Examples with independently inspected evidence include:

- `22ab67e5ce13…`: the 80-page HN-A thesis fails at page 19. Linux CAJViewer
  displays that exact page, including its figure and text.
- `761c1e690b1f…`: a KDH thesis has the existing 32-byte signature but
  `01 00 00 00` at `0x28`, rather than the admitted `00 00 02 00`. Its decoded
  payload starts with `%PDF-1.6`; CAJViewer opens it as 138 pages. This does not
  establish that changing the header guard alone completes conversion.
- `4772360d6518…`: a PDF disguised as `.caj` ends with `WebFastLoad` after
  `%%EOF`. Other examples also append file-property XML. CAJViewer displays the
  selected page; qpdf can open these PDFs with warnings.
- `220aa2f5c641…`: a 78-page C8 yearbook section fails on its first image's
  JBIG2 flags. CAJViewer displays page 1. A separate 38-page section,
  `6481714a8ac7…`, fails with `segment count` on page 2; that page appears blank
  in CAJViewer. Neither observation licenses dropping unknown image records.
- `22b6e4da1a6f…`: the C8 compressed-header refusal is a one-page color-chart
  document which CAJViewer displays.
- `b9a64bf99e4b…`: a four-page C8 article stops at native record byte 768;
  CAJViewer displays its first page.
- KDH inputs with forward `/Prev` links include a decoded PDF marked
  `/Linearized 1`; `4e3d3245bed4…` passes qpdf's structural check and has two
  pages. Preserve cycle/extent validation while investigating this profile.
- Both patent inputs rejected for outline actions open as 18-page documents
  and their decoded PDFs pass qpdf. Action semantics still need investigation.

These failures were also reproduced using nine selected original inputs in
Node and a real Chromium Worker. Error codes and messages agree with the CLI.
The #381 HN-B input is the positive control: both JavaScript targets convert its
12 pages with one reported private-use substitution. Browser OPFS cleanup leaves
no entries. This is a **ten-input runtime check**, not a full browser/Node corpus
run; those broader runs remain **NOT_RUN**.

## Follow-up issues

[Parent tracking issue #385](https://github.com/rwv/caj2pdf-rust/issues/385) records the whole failure set.
The following sub-issues isolate profiles with selected viewer or independent
PDF evidence. Other groups remain explicitly pending classification in the
parent; encrypted TEB refusals remain intentional.

| Issue | Investigation | Inputs with this first error |
| --- | --- | ---: |
| [#386](https://github.com/rwv/caj2pdf-rust/issues/386) | investigate WebFastLoad and file-property footers in GitHub documents | 44 |
| [#387](https://github.com/rwv/caj2pdf-rust/issues/387) | investigate the version-field 1 wrapper profile | 15 |
| [#388](https://github.com/rwv/caj2pdf-rust/issues/388) | investigate decoded text record areas with non-16-byte tails | 12 |
| [#389](https://github.com/rwv/caj2pdf-rust/issues/389) | investigate C8 text regions with SBRTEMPLATE and no SBREFINE | 25 |
| [#390](https://github.com/rwv/caj2pdf-rust/issues/390) | investigate unsupported compressed text prefix profiles | 11 |
| [#391](https://github.com/rwv/caj2pdf-rust/issues/391) | investigate the unsupported native record at byte 768 | 1 |
| [#392](https://github.com/rwv/caj2pdf-rust/issues/392) | investigate the segment-count refusal on a blank-looking page | 1 |
| [#393](https://github.com/rwv/caj2pdf-rust/issues/393) | investigate forward xref Prev links in KDH payloads | 4 |
| [#394](https://github.com/rwv/caj2pdf-rust/issues/394) | investigate outline action profiles in KDH patent inputs | 2 |

## Search coverage and boundaries

- Repository searches covered `.caj` references, conversion projects, theses,
  reference collections, course materials and related extensions. Recursive
  trees were inspected without reading foreign converter implementations.
- Date-partitioned repository searches retrieve all **6,976 matching forks**
  returned by the query, avoiding the API's 1,000-result cap per partition.
  This describes those query results, not every GitHub repository.
- There are **8,442 discovered repository candidates**. Of these, **7,437**
  have complete recursive-tree responses, **one** tree is truncated, and
  **four** repositories are empty. **1,000** remain unscanned or rate-limited:
  974 were not attempted and 26 hit GitHub's hourly REST API limit. Scanning
  stopped at that limit; the receipt records the outstanding repositories.
- The returned trees contain **4,022 candidate paths**. Git-blob deduplication
  reduces these to **1,315 header/download probes**. Full document deduplication
  uses SHA-256, including across Git LFS and archive members.
- Issue bodies and comments were examined in 11 relevant projects. **48**
  downloadable attachment/archive sources were processed, including the public
  Dropbox link in upstream issue 111. One additional GitHub tree-view link is
  a repository reference already covered by CAJSamples, not an attachment.
- The GitHub code-search API largely omits document binaries. The `.nh`
  extension also finds Newick data; extensions alone were never accepted as
  evidence of a CAJ-family format. CAA/CAS remain without an authentic sample.
- Only the selected default-branch snapshots and discovered attachment links
  were covered. Deleted history, private repositories, nonindexed repositories,
  inaccessible attachments and every possible branch are not exhaustively
  covered. The unchanged byte-identical fork copies are not new samples.

Each full Git download is checked against its blob identity; LFS pointers and
payload SHA-256 declarations are checked separately. Archive identity and member
path are recorded for attachment members. Downloads and hashing use bounded
chunks; no external source code was migrated or copied into the converter.

## Validation method and reproduction

The existing `research/scripts/current_formats.py` runner was reused from the
samples repository. Each document is inventoried before and after conversion;
the executable hash is stable. Every input gets the default conversion, and
C8/HN-B inputs also get `--no-bookmarks`, for **2,126 conversion attempts** in
total. Both modes are reported; repeated attempts do not increase the document
count. The complete 60-document previous catalog was actually run, not skipped.

Each child has a 180-second timeout, a 1 GiB address-space bound and a 512 MiB
output-file bound. Git/attachment downloads have a 1 GiB document cap. There
were no corpus omissions or timeout verdicts in this completed native run.
Native text uses the installed NotoSerifCJK-Regular.ttc face 2 and FreeSerif.ttf.
The receipt records CLI/tool identities, output hashes and diagnostics.

The runner's additional page/outline identity probes are retained as scoped
observations. Missing independent image oracles and unsupported oracle layouts
are not compatibility successes, and an oracle diagnostic is not automatically
a converter defect. `qpdf --check`, page counts and successful conversion do not
establish full text, image, geometry or font fidelity. No full-document visual
comparison is claimed.

To reproduce, download a chosen catalog row's pinned source (following LFS or
extracting its recorded archive member), verify its SHA-256, and place it at
`<external-corpus>/<catalog path>`. Use the established catalog runner after
preparing its documented checkout layout:

```sh
python3 tools/verify.py /path/to/external-corpus
# In a caj2pdf-rust checkout prepared as described in research/README.md:
python3 scripts/sample_catalog.py \
  --catalog /path/to/caj2pdf-samples/catalog.json --corpus-dir /path/to/external-corpus \
  --sample external/github/SHA256.caj \
  --candidate /path/to/caj2pdf --output-dir /path/to/new-external-result
```

Run the first command in the samples checkout; it is integrity-only. The second actually converts the selected
input and checks its PDF. The harness's `COMPLETE` means the attempts finished,
including refusals; it is not an all-pass verdict.

CAJViewer observations use Linux 9.0.0 in the previously pinned image
`sha256:cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de`,
with no network, read-only inputs, 2 GiB memory, two CPUs, Xvfb 1600×1200 at
96 DPI, and Noto Sans CJK UI fonts. The receipt hashes each selected capture.
The observed C8 contents panels remain empty, including the 78-page yearbook
and a separate 53-page document; this does not resolve rust#303.

External discovery responses, bounded-download receipts, the canonical corpus,
per-input run directories, native/WASM builds, runtime checks and selected viewer
captures are retained at `~/.cache/caj2pdf-github-sweep-20261007/`.
