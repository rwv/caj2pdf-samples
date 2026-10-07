<!-- SPDX-License-Identifier: MIT -->

# C8/HN-B outline sample search — 2026-10-07

## Result and issue status

The expanded search found three C8/HN-B documents absent from the pinned
57-document catalog. All three open in Linux CAJViewer 9.0.0 with an empty
contents panel. None satisfies [#303](https://github.com/rwv/caj2pdf-rust/issues/303)'s
requirement for a viewer-confirmed, nonempty outline. Keep that issue open;
this search does not establish that C8/HN-B outlines cannot exist.

All three also fail actual conversion on `main` revision
`cb791bdef2b70a4e2cc1a1d63a5e223534d43e3b`. They are useful new parser-gap
candidates for [samples#5](https://github.com/rwv/caj2pdf-samples/issues/5),
target 6, rather than positive bookmark fixtures. Conversion failures are tracked separately in [#380](https://github.com/rwv/caj2pdf-rust/issues/380),
[#381](https://github.com/rwv/caj2pdf-rust/issues/381), and
[#382](https://github.com/rwv/caj2pdf-rust/issues/382). This note records the search
baseline; subsequent fixes are in [the native-profile follow-up](c8-additional-profiles.md).

The [metadata manifest](hnc8-outline-search-20261007.json) pins source URLs,
revisions, sizes, SHA-256 identities, viewer captures and actual errors.
It is a research record, not an executable compatibility baseline. Source
documents, screenshots and complete inspection reports remain outside Git.

## Search scope

The search extended beyond the upstream converter's recent issue attachments:

- Web searches covered `.caj`/`.nh` theses, university attachments, books,
  sample files, and C8/HN-B outline reports. Filename extensions and claims
  in converter descriptions were not treated as format evidence.
- GitHub code searches used `extension:caj`, `extension:nh`, and size-filtered
  variants. Repository searches included `".caj" in:readme`,
  `caj 参考文献 in:readme`, `caj 硕士 in:readme`, and `caj 资料 in:readme`.
- Recursive trees of 54 selected public repositories were inspected, including
  CAJSamples, thesis/reference collections, course materials, and converter
  test-data directories. All completed trees reported `truncated: false`.
  This is a selected search, not exhaustive coverage of GitHub.
- Outside CAJSamples, 107 distinct Git blobs with candidate extensions were
  screened, following Git LFS pointers where present. Header reads requested
  bytes 0–511 and consumed at most 512 response bytes even when a server
  ignored Range. The result was 36 CAJ, 31 HN-A, 22 KDH, 12 PDF, two C8,
  one HN-B, and three non-document files. Blob deduplication is not a claim
  of whole-document SHA-256 deduplication for the header-only candidates.
- A separately downloaded [Sichuan Normal University thesis](https://yjsc.sicnu.edu.cn/_wx/_wx_home_news_i.aspx?iid=635413920949557500&said=yjs)
  is HN-A, not HN-B: 45 pages, 2,908,165 bytes, and 42 bookmarks reported by
  the CLI. Its visible, populated viewer contents panel was the positive
  control for the three empty-panel observations.
- A [Central South University thesis attachment](https://hyh.csu.edu.cn/info/1041/1555.htm)
  required a CAPTCHA, and a [Beijing Language and Culture University attachment](https://faculty.blcu.edu.cn/sch1/zh_CN/lwcg/217047/content/70300.htm)
  returned an anti-hotlink page. Their file formats were not established.
  The [Nanning dialect bibliography](https://leimaau.github.io/book/REFERENCES.html)
  explicitly lists filenames without providing document downloads.

Three transient GitHub/raw-content failures were retried successfully. The
search scripts, selected repository lists, pinned trees and header results
are retained with the external evidence. No external converter implementation
was used to derive a parser or outline layout.

## New candidates

| Candidate / source | Format | Pages | Bytes | Viewer contents |
| --- | --- | --- | --- | --- |
| [restructured-c8](https://github.com/zombie110year/caj2pdf-restructured/blob/d34eaf586b40e21989ea9308e9afd2fd5e23e216/tests/c8_src.caj) | C8 | 10 | 8,786,313 | Empty |
| [restructured-hnb](https://github.com/zombie110year/caj2pdf-restructured/blob/d34eaf586b40e21989ea9308e9afd2fd5e23e216/tests/hn_src.caj) | HN-B | 12 | 163,779 | Empty |
| [xue8-kvm-c8](https://github.com/xue8/book/tree/2406baa03be1fc213d76f868b94821a513aa0c50) (KVM article; exact path in manifest) | C8 | 5 | 600,236 | Empty |

The first two are LFS-backed: downloading the raw Git blob alone yields a
pointer, not a CAJ-family document. Their complete downloads matched the
LFS SHA-256 declarations. The third download matched its Git blob identity.
All three SHA-256 values are absent from catalog revision
`a33905e19e8505ff922502b30a8e5c09477ff1b5`.

The C8 files use the observed page index at `0x50`; HN-B uses `0xd8`.
Their first page data immediately follows the page index (offsets 280, 456,
and 180 respectively). This supplies no evidence for an intervening HN-A-style
outline table, and does not exclude other, unobserved storage locations.

The KVM article has an application-info package starting at byte 596,838.
Its two header words are 40,765 decoded bytes and 3,372 compressed bytes.
Bounded inflation and XML inspection found 75 `Link` items, each containing
a `UrlLink` item, plus file properties. The CLI reports 75 notes; the 150
total XML `Item` elements are not 150 bookmarks. No outline structure was
observed in that package. Neither of the other two candidates has a final
`APPINFOSIGN` trailer.

Page count is not a reliable outline test. The existing `issue-33/test1.caj`
is already a seven-page C8 document; the old “all 1–6 pages” description is
too narrow. This search adds ten- and twelve-page journal articles, still
with empty viewer contents panels.

## Actual CLI and viewer checks

The latest fetched `main` was built separately with
`cargo build --locked -p caj2pdf-cli`. Each candidate was inspected with
`caj2pdf inspect INPUT --json --pages`, then converted with
`caj2pdf INPUT -o OUTPUT` using the installed CJK and Latin fonts.

| Candidate | First-page inspection error offset / field | Conversion error offset / field |
| --- | --- | --- |
| restructured-c8 | 358 / native encoded-string word | 358 / native encoded-string word |
| restructured-hnb | 8,248 / HN-B native record tag/value | 1,132 / unverified C8 glyph size field |
| xue8-kvm-c8 | 2,372 / native record tag/value | 2,144 / unverified C8 glyph resource or placement class |

Inspection exits 0 while retaining per-page text errors on all 27 pages.
`has_outline` and `bookmark_count` stay `null`; these are unknown, not zero.
All three conversions exit 1 and publish no PDF. These are **three actual
failures**, with no conversion or compatibility pass inferred from inspection.
Browser and Node conversion were not run.

Viewer checks reused the pinned Linux 9.0.0 image
`sha256:cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de`,
with Xvfb 1600 × 1200, 96 DPI and Noto Sans CJK. The container had no network,
a read-only root/input mount, and limits of 2 GiB, two CPUs and 256 tasks.
Each source opened with its expected page indicator, and the selected
**contents** tab displayed the empty-state message. The HN-A positive control
displayed nested entries in the same panel. Earlier captures without the CJK
UI font or with the annotations tab selected are not the evidence captures.
Only the first page and contents panel were observed; full-document rendering,
bookmark destinations and cross-viewer parity were not tested.

External evidence is retained under
`~/.cache/caj2pdf-issue303-search-20261007/`: `documents/`, `viewer/`,
`current-inspect/`, `current-convert/`, `tail-observations.json`, and the
discovery/header manifests. The companion metadata file hashes the selected
captures. Redistribution permission for the external documents is not declared;
none of their bytes, copied page text, screenshots or derived PDFs is added here.

## Next evidence needed

#303 remains blocked on a C8/HN-B file with a nonempty viewer contents panel.
Prioritize a directly downloadable thesis/book or a reporter's viewer-confirmed
example, record the first eight bytes before accepting its `.caj`/`.nh` label,
and retain the viewer version and document hash. A new file with visible
section headings or a printed contents page alone does not establish stored
bookmarks. The three new failures can be investigated independently of #303;
their native-text and glyph fields do not justify an outline implementation.
