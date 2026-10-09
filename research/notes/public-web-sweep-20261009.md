<!-- SPDX-License-Identifier: MIT -->

# Public-web and Internet Archive sample sweep — 2026-10-09

The expanded search acquired **87 unique originals**, all new to
the 1,297-identity catalog. The previously reviewed CLI converted
17 and refused 70. After the focused
fixes, **all 87 convert**, totaling **701 pages**.
**80 outputs pass qpdf without warnings; seven preserve source-content warnings.**
The catalog now contains **1,384 identities**. This is a bounded acquisition
and regression result, not an exhaustive search of the web or a claim of
complete C8 visual/outline fidelity.

The [per-input JSON receipt](public-web-sweep-20261009.json) records public
URLs, original names, source/container hashes, sizes, baseline diagnostics,
current output hashes/page counts and scoped preservation checks.
Collection: [samples #81](https://github.com/rwv/caj2pdf-samples/issues/81), under #5.

| New source type | Count |
| --- | ---: |
| C8 | 2 |
| HN | 2 |
| KDH | 1 |
| PDF | 82 |

## Acquisition and search limits

- [Nanjing University](https://eduwx.nju.edu.cn/46/be/c22766a345790/page.htm)
  exposes a public RAR containing one CAJ-named PDF. Its original member and
  container hashes are pinned. A bounded libarchive extraction succeeded;
  two earlier 7-Zip attempts failed with unsupported compression and their
  zero-byte artifacts were excluded. The site crawl examined 400 observed
  pages and stopped at its cap, leaving 205 discovered pages unvisited.
- Archive.org: 140 selected item metadata requests
  (6 failed) yielded 93 original CAJ-family file links.
  86 URLs downloaded with matching archive size, SHA-1 and MD5;
  local SHA-256 identities drive deduplication. Derivative JP2/Daisy archives,
  unrelated CAJ names and reader installers were excluded. 7 links remain
  unavailable after the retained initial attempt and bounded retry.
- [Shenzhen University NKOS](https://www.lib.szu.edu.cn/nkos2/directory/987):
  42 observed category pages yielded 108 CAJ/NH/KDH links, but
  all file requests were disconnected. These links are leads, not acquired
  samples or conversion failures. The initial seed TLS failures were retained;
  successful cached page bodies were explicitly reused for discovery.
- Wayback: two broad bounded CDX requests returned 503, and three exact-URL
  availability requests returned 429. No new Wayback document was acquired.
  This does **not** mean that no snapshots exist. Internet Archive's ordinary
  item-file downloads above are a separate successful acquisition path.
- Common Crawl: current collection metadata was retrieved. Four targeted
  NKOS-prefix queries in the August/September 2026 indexes returned
  400/502/504/404; a repeat of the first returned an explicit no-captures
  response for that prefix in the September index. No Common Crawl document
  was acquired, and no global historical absence is inferred.

Transfers used bounded streaming buffers and size/time caps; failed/partial
transfers were never catalogued. Public availability is not a redistribution
license: every new row remains metadata-only, with document, PDF, image,
font and proprietary viewer bytes external. No document URL embedded inside
opaque metadata was followed, and no foreign converter implementation was read.

## Fixes and verification

- [#494 / PR #497](https://github.com/rwv/caj2pdf-rust/pull/497): validate the
  length-framed zlib `WebFastLoad` suffix and exact `APPINFOSIGN` offset.
  The Nanjing original has 11 pages; ordered MuPDF renders at 72 dpi match
  source/output on every page, and qpdf reports no output warnings.
- [#495](https://github.com/rwv/caj2pdf-rust/issues/495) and
  [#496 / PR #498](https://github.com/rwv/caj2pdf-rust/pull/498): admit complete
  16-byte-aligned padding and only the measured unused object-zero sentinel
  `0000000000 65536 f ` + LF. Live/nonzero generation overflow, conflicting
  xref entries and arbitrary suffixes remain rejected.

Reviewed candidate commit: `7c13b4052dc7a20fa143c710cfba572d1543e2ab`.
CLI SHA-256: `dcd68b74d6f51b182cdde50db46cca5a367cdbbb72b55945a903e6fbb2d01106`.
WASM SHA-256: `245c16344b3c4285d33e6be262d5236af4c917eacd192f4b1e7789cb1b300336`.
Merged Rust commit: `d2bf82e8aec6fba5e8f3783e4953606c02ab1374`; its complete
Git tree matches the tested candidate. The final-head CI checks are recorded
in the linked PRs. Self-review and
simplification were performed; no independent human approval is claimed.

Native tests reuse the existing bounded `current_formats.Commands` runner:
180 seconds per child, 1 GiB address space, 512 MiB output cap. Every input
was independently hashed before publication; qpdf validates every successful
PDF, retaining warning exits separately from clean validation. PDF source-prefix
equality proves unchanged retained bytes where reported;
independent source/output page counts agree. The Nanjing exception has the
separate complete-page rendering check above. C8/KDH conversion success is
not presented as a proprietary viewer or unknown-outline oracle.

Node.js and a real Chromium DedicatedWorker also convert the complete new
cohort. Every output SHA-256, byte size and page count matches native;
source hashes remain unchanged and every final browser OPFS inventory is
empty. The existing accepted-corpus runner was reused with the frozen WASM
and explicit Noto Serif CJK face 2 / FreeSerif resources where configured.
An independent aggregation checks the exact source set/order and output
identities; complete per-runtime rows and runner/manifest hashes are in the
JSON receipt. Runtime byte parity is not a rendered-fidelity claim.
The two new HN-A originals additionally preserve all 71 and 24 bookmarks,
with matching independently decoded source/PDF outline hashes.

The affected old **119 PDF/KDH originals** were rerun before/after: every
outcome and successful PDF hash is unchanged. This includes preserved refusals;
it does not count protected inputs as conversion passes. Unchanged CAJ/HN/C8
old inputs were not rerun in this PDF-scoped regression.

## Seven unresolved source-content warnings

[Issue #499](https://github.com/rwv/caj2pdf-rust/issues/499) records seven
original PDFs (65 pages) whose content streams end inside hexadecimal strings.
Both source and output produce qpdf exit 3. Output is an unchanged source
prefix, and all 65 ordered MuPDF page hashes at 72 dpi match the originals;
this preserves their appearance but does not recover missing content. The
representative warning page has one Contents stream, so its token is not
continued in a later array member. No matching PDF alternative was found by
normalized title in the 134 successfully fetched Archive.org metadata lists.
The search is bounded and does not prove irrecoverability.

An early progress/PR draft incorrectly described all conversions as qpdf
passes. Runtime-manifest preparation caught this by requiring exit 0; it
stopped before any JavaScript conversion. The failed preparation and actual
warning exits were retained, the claims corrected, and runtime byte parity
was tested separately. These seven are conversion successes with unresolved
validation warnings, **not complete compatibility passes**. No guessed string
terminator, glyph text, text-showing operator or dropped content was used.

The previous full-catalog [runtime checkpoint](current-corpus-runtime-20261008.md)
retains **1,252 PASS / 18 FAIL / 27 UNSUPPORTED** for its 1,297 identities.
Adding this cohort gives **1,339 PASS / 18 FAIL / 27 UNSUPPORTED** across
1,384 catalogued identities, with separate revision-scoped evidence.
The old TTKN, TEB, CAA, truncated-source, missing-palette and unknown
outline/fidelity limits remain; the new samples do not resolve them.
