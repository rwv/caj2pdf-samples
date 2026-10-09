# NJU native C8 profiles, 2026-10-09

Three unchanged originals acquired in the [Archive/NJU follow-up](archive-nju-followup-20261009.md)
now convert on reviewed Rust commit `b32672796dd2c4bd374d172df3271dc64930b7a4`
([PR #516](https://github.com/rwv/caj2pdf-rust/pull/516)). All 17 pages pass
independent source text/order, glyph geometry/color and vector/paint-order
checks. Native, Node and Chromium PDFs agree byte-for-byte. This resolves the
measured profiles in [Rust #513](https://github.com/rwv/caj2pdf-rust/issues/513)
and [#514](https://github.com/rwv/caj2pdf-rust/issues/514); it does not establish
full font/raster fidelity or C8/HN-B outline support.

The [machine-readable receipt](nju-native-profiles-20261009.json) pins the
originals, generated controls, selected observations, model/tool hashes, every
page check, runtime artifacts, neighboring-value refusals and scoped regression.
Raw documents, generated binaries, screenshots, full record inventories and API
traces remain external. Public availability does not grant redistribution.

| Original SHA-256 prefix | Pages | Glyphs | Vectors | PDF SHA-256 prefix |
| --- | ---: | ---: | ---: | --- |
| `9a50414e` | 5 | 8,926 | 6 | `4960547b` |
| `4447375e` | 5 | 9,071 | 6 | `05ae0f4a` |
| `a286d812` | 7 | 11,989 | 15 | `9354a6c5` |

## Source inventory and measured semantics

The two initial size refusals are style `8002/096b` at byte 432, then a glyph
at byte 456. The earlier `8001` word is the y coordinate, not the style. The
seven-page original first refuses `8021/2009` at byte 404; complete traversal
also exposes `8008/a380` at byte 118572 on page 6. The initial inventory stopped
there rather than guessing a record length. After independent controls
established two endpoint pairs, the full inventory frames every page with no
unaccounted tail bytes. The receipt publishes page bounds, record counts,
style/tag counts and text-region hashes without reproducing document content.

The [original MIT fixture generator](../cajviewer/c8_nju_profiles_fixture.py)
produces 148 named files, including repeated baseline identities. Reproduction
matches every recorded SHA-256. These are measurement controls and hypotheses;
generating or observing a file does not admit its profile into the converter.

| Profile | Observation and implemented scope |
| --- | --- |
| `096b` title | Exact page box/RGB equals explicit axes 95; adjacent 94/96/97 differ. The existing empirical `75/301` point model is retained. Only this style's CJK-class geometry is admitted, not other field-11 flags or Latin baselines. |
| `6084`, `0508`, `64c6` | Exact glyph aliases of `1084`, `1108`, `10c6`; public FreeType resource/transform observations agree. Neighbor flags remain refused. |
| `114a` | C8 CJK title matches known `094a` geometry (84 units). Ordinary Latin title behavior is not inferred. |
| Explicit `1/1` axes | Tiny CJK and source-symbol controls distinguish this measured geometry; ordinary Latin remains refused. |
| `8067/0,4,7,11` | Mixed glyph, line, decoration and image controls preserve the active state, equal to the existing font-6 control under ordinary/alternate font states. |
| `8021/2009` | Equal to absent/2000 controls, including reset to 2000, in all eight mode × font-state × skew contexts (32 files). No visible item is silently discarded on an unsupported value. |
| `8024/2815` | Public FreeType matrix observation agrees with the existing HN-B skew profile; the empirical 0.105 model is extended to C8. Integer viewer rounding remains a raster limitation. |
| `8006/a387,a38d`; `8008/a380` | Horizontal, vertical, diagonal and reversed controls match existing single segments. `8008` is twelve bytes, not a rectangle. New forms reject high coordinate flags. |
| `1084` brackets `a1b2/a1b3` | Both font states match a known opener at x−1/y+6, establishing offsets `(21,6)`. Adjacent x/y controls differ. |

The receipt includes 67 exact same-box/RGB equality pairs, plus discriminating
size and bracket neighbors. No image registration or crop adjustment is used
to turn a mismatch into a match. The small initial-tab `base.caj` observation
has a different box and is excluded from equality comparisons.

## Reference isolation and retained failures

The opaque viewer image is pinned to
`sha256:cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de`.
It runs as UID 1000, with no network, a read-only root and input, dropped
capabilities, no new privileges, bounded tmpfs, 2 GiB memory/swap, two CPUs,
256 PIDs and timeouts. Original geometric marker fonts identify resources;
no external font outlines are imported. Original interposers observe public
FreeType/Qt APIs, without inspecting proprietary or foreign converter code.

All unsuccessful attempts remain recorded:

- The first trace exhausts its event budget; a later viewer crash/black frame
  supplies no passing evidence. Filtered public API observations are repeated.
- An early darkness guard rejects valid tiny glyphs. A mistaken fit button
  clips a mixed page. Those cases are repeated with corrected automation.
- Pale antialiased hairlines fail the old contrast guard; the final drawing
  batches retain their actual pixels and two equal observations. Before/after
  baselines in those batches match exactly.
- Initial-tab baseline boxes can differ by one pixel; unequal boxes are not
  treated as matching controls.
- Original-page capture first fails on a manifest key; a second attempt uses
  an obsolete observer record format and all 17 pages are NOT_CONFIRMED. A
  local observer rebuild fails for missing Qt headers. The final attempt uses
  the existing original observer whose source hash exactly matches the current
  committed source; all 17 page routes have two equal cached observations.

The final original-page status is **STABLE**, meaning repeated observations
of the same complete cached page. It does not prove general viewer readiness,
original-font equivalence or source/PDF pixel parity. Catalog `viewer` stays
`NOT_RUN` for the broader comparison; [#441](https://github.com/rwv/caj2pdf-rust/issues/441)
and [#303](https://github.com/rwv/caj2pdf-rust/issues/303) remain open.

## Conversion, independent checks and rejection boundaries

The frozen final native/WASM artifact identities are in the JSON receipt.
All three original hashes remain unchanged; qpdf exits zero on all outputs.
The independent Python observers check all 29,986 glyph identities/order and
matrices, all 27 vectors, gray values and full paint-kind order. No image or
ornament occurs in these originals. The normal PDFs use installed NotoSerifCJKsc
(face 2) and FreeSerif; the geometry check does not validate their outline
appearance against the original fonts. It compares source measurements under
the documented rational empirical model, not an authoritative physical unit.

Three two-byte mutants retain the source/page structure but change `096b` to
`096c`, `2009` to `200a`, or page-6 `8008/a380` to `8008/a381`. All are refused
on native, Node and Chromium. CLI final/staging files are absent. JavaScript
sinks receive 73, 73 and 92,675 partial bytes respectively; the browser caller
removes output and source/font OPFS entries. These are expected refusals and
cleanup checks, not conversion passes or a zero-output claim.

Ten previously accepted C8/HN-B originals (60 pages) produce identical PDFs
before and after this change. This is a scoped regression, not a fresh run of
the complete catalog. Rust workspace tests pass 1,403 with seven optional
corpus tests ignored separately; JavaScript passes 182 with no skips. Relevant
research tests pass (4 new controls, 11 text-order and 16 geometry cases).
Initial harness/test-assumption failures are retained locally and corrected;
only the final passing runs are counted.

The catalog changes exactly three existing rows: **1,403 identities, 1,356
conversion PASS, 20 FAIL, 27 UNSUPPORTED**, and **37,155 accepted pages** across
separate historical checkpoints. The other 1,400 rows are unchanged. This
adds no new identity, release, broad format guarantee or irrecoverability
verdict. Remaining damaged-source cases from the same ZIP stay unresolved.

Reproduce the original fixtures outside the repository:

```sh
python3 research/cajviewer/c8_nju_profiles_fixture.py /tmp/nju-controls-new
python3 -m unittest discover -s research/conformance -p 'test_c8_nju_profiles.py' -v
python3 tools/check_catalog.py
```
