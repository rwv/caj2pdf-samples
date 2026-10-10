<!-- SPDX-License-Identifier: MIT -->

# Broader web and historical-index follow-up, 2026-10-09

This bounded follow-up to the public-web collection acquired **zero new
CAJ-family documents**. The catalog remains at 1,408 identities, with 1,361
conversion PASS, 20 FAIL and 27 UNSUPPORTED. No conversion result is added,
repeated or relabeled by this search. Work is tracked in [samples #110](https://github.com/rwv/caj2pdf-samples/issues/110),
under #5 and [Rust #406](https://github.com/rwv/caj2pdf-rust/issues/406).

The [receipt](web-historical-followup-20261009.json) records query URLs,
response hashes, selected IDs, file-list candidates, transfer checksums and
every observed request failure. Document/container bytes and raw responses
remain external. This report does not establish that no additional samples
exist on the web or in archives.

## Searches and outcomes

| Scope | Attempted | Outcome |
| --- | ---: | --- |
| Archive.org advanced searches | 9 | Bounded results for Chinese thesis/CNKI terms and `.kdh`/`.teb`; these queries overlap |
| Additional selected Archive item metadata | 193 | 192 successful responses, one TLS failure; no direct original CAJ-family file |
| Wayback CDX prefix queries | 7 | Four empty results, two HTTP 503 failures and one timeout |
| Exact Wayback availability query | 1 | HTTP 429; snapshot availability remains unknown |
| Common Crawl historical prefix queries | 8 | HTTP 504 for the selected 2015, 2018, 2021 and 2024 indexes |
| Geodata public component lists | 400 | All succeed; no CAJ/NH/KDH/TEB/CAA/CAS document attachment |

The general web searches included direct-extension, academic-attachment,
Gitee, GitLab and Archive queries. Their returned leads were largely reader
software and documentation; none supplied a new acquired document.
Internet Archive item-file searches are separate from Wayback web snapshots.

Archive metadata selection excludes previously successful requests and
unrelated identifier families; the receipt lists the actual 193 selected
IDs. The nine queries are capped at 300 rows each. Their result counts must
not be summed as distinct files or searched items. The KDH/TEB terms also
match unrelated abbreviations, languages and software; those names are
leads, not evidence of CAJ-family file signatures.

Five potentially relevant compressed containers were considered. Two
download completely and match Archive size, SHA-1 and MD5. Their directory
listings contain 363 and nine members respectively, with no CAJ-family
filename. Two transfers reach the 90-second cap and have their partial files
removed. A 258,420,202-byte container exceeds the 64 MiB acquisition cap.
Unacquired containers, other metadata-listed archives and nested containers
remain unexamined. No executable or downloaded implementation was run/read.

The Geodata requests select pages 2, 50, 100 and 130, with 100 distinct IDs
per page. This unfiltered search reports 40,771 rows; only these 400 public
component lists were examined. The previous 100-row publisher-filtered
search is a separate scope. No account, dataset order or payment workflow
was used; this search concerns anonymous document-attachment metadata only.

## Continuing conversion work

No downloaded file is promoted to the catalog without bytes, a hash and
actual conversion. The existing native glyph/text distinction is being
implemented under [Rust #518](https://github.com/rwv/caj2pdf-rust/issues/518),
with its bounded PDF writer prerequisite in [#519](https://github.com/rwv/caj2pdf-rust/issues/519).
That independent implementation is not new-sample acquisition or a claim
that all source-font fidelity is complete. Refusal recovery, source content,
outlines and viewer-readiness issues remain open. No release is requested.
