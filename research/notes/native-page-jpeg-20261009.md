# Retained native page-5 JPEG diagnostic

The two historical complete rasters for HN-B source `166d00147923…`, page 5,
are numerically connected by the already measured JPEG profile: encoding A
at quality 100 with 2×2 sampling and integer DCT, then decoding with integer
DCT and default upsampling, produces **B exactly**. The reverse direction
differs at 32,658 pixels. This explains the exact raster values without
establishing which APIs the historical native viewer sessions called.

The [metadata receipt](native-page-jpeg-20261009.json), SHA-256
`48694eaf6321c67c165880edd3404d0e1bfbcd81b62c1bf6c440625818537391`,
retains both directions, the frozen plan, commands, full-grid metrics and
source/tool/artifact identities. It extends the
[native composition observation](native-page-composition-20261008.md) under
[samples #51](https://github.com/rwv/caj2pdf-samples/issues/51) and
[Rust #441](https://github.com/rwv/caj2pdf-rust/issues/441).

## Measured scope

The unchanged source SHA-256 is
`166d0014792326570d9e8ca42fe13a4a44329e4ad095d3ac8dfd73c8ddb9f20e`.
Both retained images cover the complete 1003×1506 page buffer at confirmed
150% zoom and page field `5/12`. These are source-viewer rasters, not the
converted PDF. The historical reviewed PDF identity remains
`11cadd7d1857a26a929d5d74be4da53facef1215f5a2e43f9104706c26bb7b88`;
this diagnostic does not read, render or compare it.

| Retained observation | PNG SHA-256 | Raw RGB SHA-256 |
| --- | --- | --- |
| A, `native-composition-normal-1` | `c2b1b1716287350dd3087d0f2186a43124ebf4bc4e0483ab6770bb69b44099c1` | `a59bd3e1b6cb29414c443b46477b6dbab38e27f6076f354730716349db999b9f` |
| B, `native-composition-normal-2` | `2d09b4db29c5eff0356a4ad07af41d96d052bbb6a6c1126cfe869425cfa4467d` | `966f37a4e26ad6965754e877b3c61721344d84074f1e965c9d16819c894c6241` |

The original A/B disagreement remains **23,901 grayscale pixels**, maximum
absolute channel difference 2, bounds `[16,40,992,1480]` with exclusive maxima.
No pixel tolerance, alignment, crop fitting or resizing is used. The later
`normal-3` and `normal-v3-recheck` images remain identical to B. All 24 retained
metadata/pixmap files for these four sessions are rehashed against the original
receipt. Their two equal captures per session still do not establish readiness.

The two-direction plan was frozen before running either case, SHA-256
`6531f789c4630af51b1d4e7b11ff83d052791d3ca2f739794aaf97c5cbc02564`.
It reuses the fixed profile from the
[original JPEG controls](viewer-jpeg-roundtrip-20261009.md); there is no new
parameter search. External `cjpeg`/`djpeg` 2.1.5 both exit successfully in both
directions. Every one of the 1,510,518 pixels participates in each comparison.

| Direction | Result against the untouched target | Differing pixels |
| --- | --- | ---: |
| A → fixed JPEG encode/decode → B | Exact | 0 |
| B → fixed JPEG encode/decode → A | Different | 32,658 |

The forward JPEG SHA-256 is
`d90dca082ff7020bb1f8bae9f018b644714990a58e594027d5d32cbe5dfab5c7`.
Its decoded RGB hash equals B. The reverse decoded RGB hash is
`95556aebf58f05ffd3de37adef66810e7a185d76dbeaeb4acd1987909ffec9ea`.
The 23,901-pixel real-native disagreement is separate from the 29,877-pixel
original synthetic native control, the 2,499-pixel raw `7797…` discrepancy
and its 5,169-pixel displayed difference.

## Interpretation and remaining work

The numerical result is consistent with the JPEG representation change
observed through public APIs in other controls and the
[actual `7797…` case](viewer-original7797-jpeg-20261009.md). No new viewer
session is acquired here, and historical JPEG calls are not retroactively
claimed observed. The original discrepancy and all prior acquisition failures
remain in the composition receipt; a new follow-up field records this result.

JPEG quality 100 is still lossy. The earlier original one-pixel collision
control produces equal encoded/decoded outputs from distinct inputs. Thus
JPEG-normalized equality cannot accept a source/PDF pair, and this diagnostic
does not turn a historical raster mismatch into a conversion pass. Page
identity and the representation being compared must be established separately;
fixed routes, elapsed waits and repeated equal frames are insufficient as a
general readiness rule. That criterion remains open under #441.

The separately observed faint PDF table lines also do not establish a new
converter defect. Existing original
[segment-axis controls](c8-native-records.md#independent-horizontalvertical-segment-control)
measure the same zero-width PDF horizontal line at integrated widths about
2.0039 black pixels in CAJViewer and 0.2667 in MuPDF; source-viewer width is
about 1.0078. Earlier zoom controls support hairlines. These renderer-sensitive
values do not justify thicker strokes, fitted gray values or threshold-based
omission claims. This checkpoint makes no new line-width measurement or fix.

Native original-font appearance, ornament appearance and full source/PDF
fidelity remain open under samples #51 and Rust #406. Conversion totals stay
**1,252 PASS / 18 FAIL / 27 UNSUPPORTED** across 1,297 originals. There is no
new compatibility pass, converter run, runtime sweep or irrecoverable exception.

## Reproduction and provenance

Using the exact retained PNG identities, the original MIT driver writes P6
RGB rows sequentially and runs:

```sh
cjpeg -quality 100 -sample 2x2 -dct int -maxmemory 32768 -outfile out.jpg input.ppm
djpeg -dct int -rgb -pnm -maxmemory 32768 -outfile decoded.ppm out.jpg
```

Each codec child has a 256 MiB address-space limit, 16 MiB file-size limit,
10-second CPU limit and 15-second timeout. The existing checked-in PNG reader
admits at most 16 MiB and 4 Mi pixels per image. The driver holds bounded page
buffers; no whole-driver address-space cap or peak-memory measurement is claimed.
Commands, successful exits and both differing/equal outcomes remain recorded.

Only metadata is added to Git. Source documents, PNG/PPM/JPEG pixels, fonts,
derived PDFs and binaries remain external. The analysis uses original MIT
code and public black-box JPEG tools; no vendor implementation, vendor font
program/outline or differently licensed converter source is inspected or
copied. No production dependency, format, API, memory path or release changes.
