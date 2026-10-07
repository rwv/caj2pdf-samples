<!-- SPDX-License-Identifier: MIT -->

# Additional native C8 profiles (#380 and #382)

The [expanded outline search](hnc8-outline-sample-search.md) found two new C8
conversion failures and one HN-B failure. This follow-up concerns the C8
profiles in [#380](https://github.com/rwv/caj2pdf-rust/issues/380) and
[#382](https://github.com/rwv/caj2pdf-rust/issues/382). Source identities and
pinned download locations are in the search manifest and catalog. All external
documents, extracted content, fonts, screenshots and PDFs remain outside Git.

## Independently observed rules

The original MIT [control generator](../cajviewer/c8_additional_profiles_fixture.py)
reproduces 75 small inputs byte for byte. It builds on this project's original
geometry and asymmetric-JPEG generators. No converter implementation, private
HN/JBIG module, vendor implementation or third-party glyph outline was copied.
The observations use the previously pinned offline Linux CAJViewer 9.0.0 image
`sha256:cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de`.
Original full-em marker fonts distinguish resource roles and placement from
Unicode identity. The real-document checks use the viewer's installed fonts.

- The last word of a length-delimited `80cc/01xx` string may be `e000`.
  Plain, terminated, NUL-only and embedded-NUL controls preserve the next
  glyph. Production admission remains limited to printable `e020..e07e`
  words with an optional **terminal** NUL; the embedded-NUL experiment is not
  a claim that every nonprintable value is understood. Framing still consumes
  the complete declared span, at most 28 bytes per read.
- An `810a/d300` reference whose byte length is divisible by four can end
  immediately after its name. The older NUL-padded form also works. Ten
  original image-plus-following-glyph controls, with lengths 0, 4, 8, 24 and
  260, have identical page crops with and without the extra four zero bytes.
  Nonaligned names retain zero padding to a four-byte boundary. The parser
  preserves the declared name span, recognizes only an all-zero optional
  four-byte pad, and never opens or decodes the name as a resource path.
  This extends the older [image-reference observation](c8-image-references.md),
  which did not establish the missing-NUL case.
- C8 paired explicit axes 22, 34, 38 and 40 establish a run even without a
  preceding `8002` style. Their nominal em is `axis * 75 / 301` PDF points;
  measured ordinary-Latin baseline adjustments are 11, 8, 7 and 7 empirical
  source units respectively. A following `8002` resets the axes.
- Style `094a` uses size field 10 (84 nominal units); original `094a` and
  `114a` controls have identical geometry. This does not remove the older
  separate variant/class restrictions on `114a`. Style `a4a5` matches the
  existing `10a5` geometry. The original controls also measured field 9, but
  that HN-B follow-up is not required for these two C8 fixes.
- `801c/2` and `801c/3` preserve rendering in the controlled profile.
  Ideographic full stop `a1a3` shares the established `a1a2` placement;
  `a1ab`, `a3a7` and `a3fc` share the controlled comma/symbol placement.
  Fullwidth ampersand `a3a6` selects the CJK resource and baseline.
- Explicit-axis parentheses and square brackets require independent offsets;
  they are not ordinary Latin letters. The measured source-unit offsets are:

  | Axis | Opening parenthesis x | Closing parenthesis x | Parenthesis down | Square x | Square down |
  | --- | --- | --- | --- | --- | --- |
  | 22 | 14 | 13 | 6 | 19 | 4 |
  | 34 | 21 | 20 | 0 | 29 | -3 |
  | 40 | 25 | 23 | -2 | 34 | -5 |

  Original shifted-origin controls bracket the quantization residual. At the
  displayed 1241% zoom, selected marker/PDF bounds differ by up to three pixels,
  including glyph raster extents. These empirical offsets are not a promise
  of exact pixels, authoritative physical units, or arbitrary unequal axes.
- `8010/2` and `8010/46` share the verified 12-byte horizontal-decoration
  framing and repeated-font-glyph geometry with `8010/1`. Repeated controls
  preserve subsequent text. Paired axes 34 and 40 select the decoration em;
  its endpoint clipping and source order are unchanged. Other dimensions and
  diagonal/reversed spans remain errors. The default PDF decoration alias
  remains a substitute; the viewer's flower-like mark is not reproduced by
  the default arrow alias.

The generator includes comparison and negative-scope inputs, so its 75 files
are **not** 75 production conversion passes. Earlier large GUI batches exhausted
the viewer and yielded black captures. Those captures, stale screenshots from
an unmaximized window, and the isolated HN-B unknown-code error dialog are
excluded from the C8 evidence. Fresh, nonempty captures establish the listed
comparisons. Selected default-font pages were inspected separately.

## Conversion checkpoint

The two unchanged originals now convert through the shared core:

| Input | Pages | Native glyphs retained | Image draws retained | PDF SHA-256 |
| --- | --- | --- | --- | --- |
| restructured C8 | 10 | 1,977 / 1,977 | 17 / 17 | `db0859192313afc1879f3b2bf941c9978251ef01ebeec28d446a16a4992bff23` |
| xue8 KVM C8 | 5 | 10,277 / 10,277 | 4 / 4 | `1ce3a67f4f6a43647dff2a8da88162d4a15f21ad2c06f7616e054f38989c280e` |

CLI output uses installed Noto Serif CJK SC (collection face 2) and FreeSerif.
Both outputs pass `qpdf --check`; `pdfinfo` confirms the complete page counts.
The unchanged originals also complete through Node and a real Chromium Worker
with identical per-document CLI/Node/browser SHA-256 values. Browser OPFS
cleanup leaves no files. Maximum observed output chunk sizes are 262,144 and
127,274 bytes respectively; these are chunk bounds, not peak-memory measurements.
Independent bounded record inventory and MuPDF content-stream inspection agree
on every page's glyph count, excluding explicitly nonsemantic decoration.
The page-10 portrait order and page-1/page-5 KVM heading, column and continuation
layout agree in selected viewer comparisons. All eight page-10 portraits are
present. This is scoped layout evidence, not whole-document pixel parity.
Substitute fonts still change weight, Latin spacing and decoration appearance;
some Latin text overlaps, as in the existing experimental profiles.

Original regressions cover terminal NULs across chunk boundaries, absent/present
image-name padding, malformed padding, truncated records, implicit axes, axis
resets, unequal-axis rejection, glyph continuation and decoration replay. Node
and real Chromium Worker controls exercise the shared WASM behavior, including
both aligned-name forms and embedded JPEG preservation. Optional external
corpus suites are reported separately, never inferred from these controls.

Raw evidence is retained under `~/.cache/caj2pdf-native-fixes-20261007/`, including
`control-manifest.json`, `reproduced/`, `viewer/`, `realviewer/`,
`c8-conversion-evidence.json`, and `marker-pdf-evidence.json`. The companion
[capture and output manifest](c8-additional-profiles-evidence.json) pins selected
receipts without redistributing their contents.

## Separate remaining work

[#381](https://github.com/rwv/caj2pdf-rust/issues/381)'s 12-page HN-B article still
requires field 9, further symbol/control semantics, and image-after-text
composition. The raw code `a661` on page 10 is private-use under ordinary
GB18030; the viewer displays a nonstandard accented glyph in an isolated control.
An ordinary viewer Copy action on the isolated glyph plus an ASCII `A`
returns UTF-8 `e2 97 8f 20 41 0d 0a` (a bullet, space, `A`, CRLF), despite
the displayed accented glyph. This exploratory copy observation is not an
authoritative Unicode mapping. Its semantic identity is not established by
guessing from neighboring text. The original page 10 does display in the default-font viewer. A failed
marker-font probe is not proof that the source document is corrupt.

[#303](https://github.com/rwv/caj2pdf-rust/issues/303) still lacks a positive
C8/HN-B stored-outline example. These fixes retain the bookmark-omission warning.
