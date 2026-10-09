# Original native viewer navigation controls (2026-10-09)

An original HN-B control reproduces two different complete page-5 rasters in
the same pinned viewer. No converter is involved. This provides a public
reproduction for [samples #59](https://github.com/rwv/caj2pdf-samples/issues/59),
under [samples #51](https://github.com/rwv/caj2pdf-samples/issues/51) and
[Rust #441](https://github.com/rwv/caj2pdf-rust/issues/441). It does not establish
an internal rendering mechanism, a readiness criterion, or corpus fidelity.
The [machine-readable receipt](native-viewer-navigation-20261009.json) retains
source/tool/raster hashes, routes, geometry, failed-attempt context and cleanup.

## Original controls and observations

The generator creates six original, image-free HN-B documents: 5, 6 or 12 pages,
each with 12-byte or 20-byte indexes. Page 5's native records are identical in
all six. It contains five marker glyphs and a 40×40 repeated neutral code grid;
there is no imported document text or font program. The first five page records
are identical across page-count variants; only the index and trailing pages
change. Dimensions are 5168×7760 source units, observed at 150% as a complete
1003×1506 pixmap.

| Total pages | Direct page 5 | Visit page 3, then page 5 | Changed pixels |
| --- | --- | --- | --- |
| 5 | A | A | 0 |
| 6 | A | B | 29,877 |
| 12 | A | B | 29,877 |

Both index layouts have these results in the first paired run. These labels refer to the original
control hashes, not the real-document A/B hashes in earlier issue comments:

- A: `cf503215234ccef451a29906a5aef1eb7ef592f0e04d6b842064703a81e4ef68`
- B: `c610a94a38c5cc9d3322222ddaf3ffbe3c3166a8a84aa7833d51623724580677`

Differences are grayscale, with channel deltas from -2 through +2 and exclusive
bounds `[32,40,880,1392]`. Both captures within every session agree, despite
different fresh sessions producing A or B. The 12-page/20-byte-index positive
pair is repeated in reverse order (prior-page route, then direct route), but
this time both produce A. Thus identical source bytes and an identical prior3
route also produce different rasters in fresh sessions. Navigation position
is not a sufficient condition. The initial report aggregator incorrectly
asserted repeat equality and failed; its script/failure hashes are retained,
and that assumption was removed without rerunning any viewer session. These
observations are evidence against using two equal cached captures as a readiness
test. They do not justify a ±2 acceptance tolerance.

Four discovery sessions first established the 12-page control. Fourteen fresh
sessions use the final generator/runner: six direct, six prior-page and the two
counterbalanced repeats. All inputs retain their hashes, no OOM occurs, and
all containers are removed. These are observations, not compatibility passes.
The previous 30-session investigation, including its observer startup failure,
remains linked in the receipt; it is not silently replaced or counted again.

## Real-document index-swap discriminator

An external diagnostic derivative of the magnesium original
`166d0014792326570d9e8ca42fe13a4a44329e4ad095d3ac8dfd73c8ddb9f20e`
swaps only the page-2/page-3 index entries. Exactly ten bytes change, within
source offsets `[236,276)`; every text/image body and the target page are
unchanged. The derivative SHA-256 is
`1fabc07fe3c9a08972ba435138f5899dce1c51b65990e3ac67d2429df643139c`.

Three fresh sessions preserve the original route classification: direct5 and
2→5 give the original A; 3→5 gives the original B. The first-page rasters also
swap exactly as expected, confirming that the viewer follows the changed index.
Thus this discriminator follows page position rather than the exchanged
preceding content. Together with the original controls, it motivates a forward
prefetch/cache hypothesis; it does not observe or prove an internal mechanism.
The diagnostic never substitutes for its unchanged original in the corpus.

## Reproduction and bounds

Use an already supplied opaque viewer image and the unchanged compiled
`qpaint_observe.cpp` observer from the [composition protocol](native-page-composition-20261008.md).
The measured image is
`sha256:cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de`;
observer SHA-256 is
`155e6a3e7a9604c6510c12986c0f867267d28a1b8fe72a2b0e2c382baa647e9b`.
No viewer, font or corpus download is performed by these commands:

```sh
python3 research/cajviewer/native_navigation_controls.py /external/new-controls
python3 research/cajviewer/native_page_capture.py /external/new-controls/manifest.json \
  /external/new-direct --observer /external/observe-v4.so --image "$VIEWER_IMAGE" \
  --lifetime-seconds 90 --route 5
python3 research/cajviewer/native_page_capture.py /external/new-controls/manifest.json \
  /external/new-prior3 --observer /external/observe-v4.so --image "$VIEWER_IMAGE" \
  --lifetime-seconds 90 --route 3 5
```

Each session uses network none, read-only root/input/observer, uid/gid1000,
dropped capabilities, no-new-privileges, 2 GiB memory/swap, 2 CPUs, 256 PIDs and
a 90-second lifetime. Page and zoom OCR, complete-page paint geometry, input
hashes and container cleanup are checked. Failures remain `NOT_CONFIRMED`.
The new route option accepts at most 12 distinct in-range pages, preflights
all cases before launching a container and records the route. Duplicate routes
are refused so captures cannot overwrite a prior visit. Omitting the route
preserves all-page capture; the existing default lifetime remains 600 seconds.

The generator admits only the six fixed profiles, writes a fresh directory
outside this checkout and produces at most 60 KiB per file. Independent source
framing/content controls cover every generated page, identical target records,
profile limits and refusal to overwrite. The capture controls reject invalid
routes before I/O or launch. Catalog CI uses these original controls without a
viewer or corpus; viewer observations are a separate explicitly recorded run.

## Provenance and remaining limits

All new code and tests are original MIT work. Header/index facts and native
record framing reuse this project's independently authored HN-B controls and
`hnc8_layout_source.py` / `native_text_order.py`; no external converter or vendor
implementation is consulted or translated. The repeated code grid is authored
for this experiment. No font outlines are read. Generated controls, original and
derived documents, pixels, fonts and binaries stay external. No new dependency,
private-source migration, production API, I/O path or output change is introduced.

The original `7797…` PDF cold-session disagreement is not explained by this HN
control, and an earlier real-document sequential session that yielded A remains
part of the evidence. Neither parent #441 nor #406 is complete. Corpus counts
remain 1,252 conversion PASS / 18 FAIL / 27 UNSUPPORTED; this work adds no
conversion pass and does not rerun or replace the full runtime ledger. Original
font/ornament appearance, other raster differences, unknown outlines and actual
TTKN/TEB recovery requirements remain open. No release is requested.
