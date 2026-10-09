# Archive retries and NJU follow-up, 2026-10-09

[Issue #95](https://github.com/rwv/caj2pdf-samples/issues/95) continues the
[Archive 360-temp checkpoint](archive-360-temp-20261009.md).
The [machine-readable receipt](archive-nju-followup-20261009.json) pins sources,
failed attempts, artifacts and the exact verification scopes. External documents
remain outside the repository; public availability is not redistribution permission.

## Acquisition and results

Retrying the seven remaining failed Archive transfers through their metadata's
public storage servers obtains seven originals with matching size, SHA-1 and MD5.
An additional 300 NJU page requests find a public ZIP containing five new originals.
Its six entries, member sizes/CRC32/SHA-256 and GB18030 names are independently
checked; the initial replacement-decoded names remain in the acquisition receipt.
These are **12 new identities**, with no duplicates. The crawl now records 1,600
distinct attempted URLs and 91 remaining frontier URLs; it is not exhaustive.
Whole-web exact-title searches acquired no intact replacement for either zero-filled
original. Indexed forum filenames without accessible downloads are only leads.
Earlier Wayback CDX timeout/HTTP 429 results remain unresolved, not absence evidence.

| Original (SHA-256 prefix) | Format | Conversion | Accepted pages | Follow-up |
| --- | --- | --- | ---: | --- |
| `6edb8bfc8af0` | PDF | PASS | 2 | — |
| `16ccb2feb13d` | UNKNOWN | FAIL | — | [509](https://github.com/rwv/caj2pdf-rust/issues/509) |
| `c7af016853a0` | PDF | PASS | 17 | — |
| `ff8bd83668cc` | HN | PASS | 132 | — |
| `52db5d34e6ba` | HN | PASS | 124 | — |
| `0cebdd5cbaa5` | HN | PASS | 294 | — |
| `595e717a629e` | PDF | FAIL | — | [515](https://github.com/rwv/caj2pdf-rust/issues/515) |
| `bc1e8f8d49ce` | PDF | PASS | 5 | — |
| `9a50414e00a6` | C8 | FAIL | — | [513](https://github.com/rwv/caj2pdf-rust/issues/513) |
| `78bcceee7c66` | C8 | PASS | 6 | — |
| `a286d812d9d1` | C8 | UNSUPPORTED | — | [514](https://github.com/rwv/caj2pdf-rust/issues/514) |
| `4447375ea1b1` | C8 | FAIL | — | [513](https://github.com/rwv/caj2pdf-rust/issues/513) |

Totals extend the catalog to **1,403 identities: 1,353 conversion PASS,
22 FAIL and 28 UNSUPPORTED**. All 1,391 previous rows are unchanged.
The seven accepted inputs add **580 pages**, extending the reconciled historical
accepted-page total to **37,138**. This is not a fresh full-catalog conversion run.
`UNKNOWN` now records the missing-signature original honestly: the checker rejects
successful conversion or invented page/bookmark/variant metadata for that type.
Integrity PASS verifies the downloaded bytes against their acquisition identity;
it does not claim that the original is structurally intact.

## Product and independent checks

[Rust PR #512](https://github.com/rwv/caj2pdf-rust/pull/512), reviewed at
`56d7b7ba0b4da366b73ae842deccd33d207e507f` and merged as
`0fb8a78a8d8fffb4e855fe13a742085ff731fc10` with the same tree, admits the measured
package XML footer and exact marker plus complete block padding. No general XML,
non-ASCII GB2312 or arbitrary suffix stripping is enabled. It passes 1,397 Rust
checks (seven optional ignored), 182 JS checks and required CI. Optional skips
are not compatibility passes or release evidence. All 204 existing PDF/KDH
before/after outcomes and successful hashes agree; the initial missed SSE cache
path is retained separately from the corrected complete run.

All seven successful original outputs agree in native, Node and Chromium hash,
size and page count and pass qpdf. The three PDFs (24 pages) preserve selected
object values, raw streams and navigation, plus every page's geometry, word
positions and 72-dpi MuPDF pixels. The NJU package source has 76 selected objects
and 37 raw streams. Independent source bitmap identities/order and page geometry
pass for all 550 HN pages and six accepted C8 pages. All 118 HN-A outline titles,
destinations and depths agree. Full vendor-rendered glyph/vector appearance and
C8 outlines remain outside this proof; no viewer pass is added.

Three initial debug-build HN attempts hit the explicit 180-second limit. Their
optimized conversions succeed; neither those timeouts nor other failed attempts
are discarded. The raw copied JS harness also retained an old revision label and
incorrectly required zero writes for every refusal. Its imported worktree and
hard-checked WASM SHA-256 identify the actual artifact; the separate runtime audit
corrects the label without claiming another run. All five originals refuse with
the corresponding native/JS diagnostic. Three C8 failures emit 73 partial header
bytes before the JS error; these are **not zero-output or conversion passes**.
This is consistent with the API's caller-owned partial-output disposal contract.
The browser caller removes every OPFS file; native failures leave no output.
The two malformed footer controls refuse before JS output and clean up.

## Remaining originals

The missing-header source has a 225,280-byte zero prefix. Its public alternate
storage server independently returns the same complete zero prefix. The dance
PDF's valid padded marker is now recognized, exposing two zero body ranges totaling
9,293,824 bytes. A second public storage range agrees; one other range request
fails TLS and is retained. qpdf's recovered subset has missing-page-object warnings
and cannot establish faithful full conversion. No intact alternate was acquired.
[Issues #509](https://github.com/rwv/caj2pdf-rust/issues/509) and
[#515](https://github.com/rwv/caj2pdf-rust/issues/515) retain the recovery work;
[#511](https://github.com/rwv/caj2pdf-rust/issues/511)'s full-original criterion
remains unmet despite its implemented footer recognition.

Two native C8 originals hit an unverified glyph-size field, tracked in
[#513](https://github.com/rwv/caj2pdf-rust/issues/513). A third hits an unsupported
native record, tracked in [#514](https://github.com/rwv/caj2pdf-rust/issues/514).
Their measured page counts are retained without claiming converted pages.
No unknown records are skipped and no source fields are guessed. The broader
[#406](https://github.com/rwv/caj2pdf-rust/issues/406) remains open; this report
makes no new irrecoverability claim and publishes no release.
