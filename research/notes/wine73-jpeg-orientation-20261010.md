<!-- SPDX-License-Identifier: MIT -->

# Descriptor-specific JPEG orientation in Wine 7.3

[Rust #530](https://github.com/rwv/caj2pdf-rust/issues/530) is a production
placement defect: admitted HN-A/C8 type-1 JPEG rows must be drawn top-first,
whereas type-2 rows retain their bottom-first placement. Decoding or rewriting
the JPEG is unnecessary. Both the image-only composer and native C8 image
placement need this distinction. HN-B still admits type 2 only.

The [metadata receipt](wine73-jpeg-orientation-20261010.json) retains exact
source, PDF, executable, font, control, capture and log identities. It contains
no document, image, font program or vendor binary bodies. Raw evidence is
maintainer-local under `~/.cache/cajviewer73-fixes-20261010/`.

## Baselines and reference

The historical #459 implementation is `5f3cf7fb08297ddadfb1cff05e8dcdfe17c037dc`.
Fresh native/WASM builds of main `bfe4ff8fcbc33a082f23dee107d625893da26b1d`
were frozen separately. All 17 newly generated Node PDFs match the historical
hashes, with explicit Noto Serif CJK collection face 2 and FreeSerif for native
text. Completed #518 symbol-map support does not change this recipe.

The user-selected visual reference is the unchanged original in Windows
CAJViewer **7.3.151 Simple**, running under **Wine 8.0, 32-bit**. The image
is `sha256:6c9f5ec0610a7ff8bc45fe8e0a87dffd0ff17e42466c90b80237a1712847b95c`.
Each cold session clones the same manifest-pinned prefix: Windows Chinese and
Latin fonts, UI font substitutions, and native MSXML 3. The inherited MDAC
limitations remain; native Windows equivalence is unverified.

Sessions use Xvfb 1600 × 1200 at 96 DPI, Openbox, maximized CAJViewer,
single-page mode and 75%. After the splash, public Win32 numeric controls must
be at their canonical positions and confirm the requested page/total and zoom.
Capture twice, 0.6 seconds apart; repeat originals in a second cold session.
Page extraction includes the border and preserves native pixels. Connected
components exclude detached UI banners; there is no resizing, registration,
JPEG normalization or fitted pixel tolerance. All 20 orientation sessions
completed and were removed. Containers have no network, read-only root/input,
nonroot execution, dropped capabilities, 2 GiB memory/swap, two CPUs, 256 PIDs
and a 600-second lifetime. Other retained probes reproduce #533's separate
PDF-window failure and are not orientation passes.

## Original discriminator

Run `python3 research/cajviewer/jpeg_orientation_controls.py /external/new-dir`.
The generator reuses the project's original MIT `hna_image_fixture.py` and
`c8_image_fixture.py`; all four generated sources reproduce the measured
identities byte for byte. Convert with `--no-system-fonts`; the native C8
wrapper additionally requires explicit `--font-cjk` and `--font-latin`, both
pointing to the same DejaVuSans file. It draws no glyphs. The requirement comes
from the native-page route's preflight, not the image itself.

Each variant has an otherwise identical type-1/type-2 descriptor pair. The
original JPEG has a black top/left bar, blue lower-left patch and red
lower-right patch; placement is `(400,500)`, extent `(3500,2500)`, page
`(6400,4800)`. The predeclared discriminator changes only the descriptor.
Wine originals draw type 1 top-first and type 2 bottom-first in **both** HN-A
and C8. Main's PDFs incorrectly give both the type-2 orientation. The candidate
changes only type 1. Separate cold original captures repeat exactly.

| Pair | Main source/PDF differing pixels | Candidate differing pixels | Result |
| --- | ---: | ---: | --- |
| HN-A type 1 | 42,173 | 702 | Corrected orientation; raster differences remain |
| Native C8 type 1 | 42,173 | 702 | Corrected orientation; raster differences remain |
| HN-A type 2 | 937 | 937 | PDF unchanged |
| Native C8 type 2 | 937 | 937 | PDF unchanged |

Color-region centroids are an orientation diagnostic only; exact pixel counts
use no tolerance. An original core regression independently decodes grayscale
and RGB JPEGs with `djpeg` and renders the PDFs with MuPDF for HN-A/C8 types 1/2
and HN-B type 2. Existing decoder-rounding allowance is unchanged. A separate
native C8 regression checks nonzero placement and the unchanged image box.
The Node regression retains short reads and JPEG-byte preservation and checks
the distinct placement matrices instead of the former incorrect PDF equality.

## Actual 433-page original

Source SHA-256:
`16b1a3b1cb7177cc3d327f749f7f273d806b153ded5fe11d9261bac030ec66ac`
(8,527,548 bytes). The catalog calls it NH; its actual magic is `HN\0\0`.

Main/historical PDF:
`b12385a8a53a811ac245dd6f65b410a5c1b1be526292b42e94594a6b75c4add3`
(24,592,732 bytes).
Candidate PDF:
`ea43a23bb3e46b4589d78a81cedfd5e616384b3285af4eb0c00f12fefbfbbcdf`
(24,592,713 bytes).

The complete source inventory contains four type-1 JPEGs, three type-0 images
and 427 type-3 images. JPEGs occur on pages **1, 7, 9, 433**; page 9 also has
a bilevel image. Independent PyMuPDF inspection confirms all page boxes and
all raw image streams/dictionaries are unchanged. Only those four page
content streams change, and only their JPEG matrices. The other 429 content
streams are identical.

All four affected pages now have the original's vertical orientation in Wine.
Page 217 remains upright and its before/after PDF crop is byte-identical.
Each original page crop repeats exactly in its separate cold session.

| Page | Main source/PDF differing pixels | Candidate differing pixels |
| ---: | ---: | ---: |
| 1 | 360,380 | 237,471 |
| 7 | 326,953 | 157,722 |
| 9 | 104,693 | 67,859 |
| 217 | 21,042 | 21,042 |
| 433 | 346,673 | 163,216 |

These are orientation passes, **not exact raster passes**. #534 owns the
remaining sampling/page-boundary differences. Only these five actual pages
were viewed; the other 428 have inventory/stream preservation evidence.

## Runtime and regression boundaries

The candidate regenerates all 17 PDFs. Sixteen are byte-identical to main,
including the CAJ/KDH/PDF controls and every selected native-text document.
Node and real Chromium Worker output agree for all 17, with ranged/OPFS input,
sequential output and empty browser OPFS after cleanup. Native CLI agrees for
the changed 433-page original; qpdf reports no syntax/stream errors.

For all four original orientation controls, native, Node and Chromium also
agree when supplied the same font-source sharing recipe. The first browser
control attempt created two distinct font sources where native/Node used one;
its two C8 hash mismatches remain recorded. The repeated run shares one OPFS
font source across the roles, matching the declared native recipe. No converter
change or output normalization was used to hide that difference.

Rust formatting, Clippy with warnings denied, workspace tests, and all 186
Node/Chromium tests pass. Seven optional Rust corpus/vector tests were ignored
and are **NOT_RUN**, not compatibility passes. The first JS suite retained one
failure of the obsolete type-1/type-2 equality assertion; all 186 pass after
replacing it with the measured descriptor-specific geometry. Earlier native
test-parser and CLI executable-permission setup failures are retained too.

## Provenance and remaining work

Production changes only choose the existing image matrix's row orientation;
JPEG validation/copying, admission bounds, APIs, allocations, ranged input and
sequential output are unchanged. No document hash or page-number special case
is used. All new code and controls are independently authored MIT work.
Installed JPEG/PDF tools are independent validators. No vendor/private HN or
JBIG implementation or differently licensed converter code was inspected,
copied or transliterated; no font or document body is redistributed.

This corrects #224's unverified equal-orientation assumption without replacing
its historical payload/order evidence. Source fonts and spacing (#531), C8
ornaments (#532), the mode-specific PDF-window failure (#533), residual raster
and width differences (#534), general readiness (#441), and full #406 fidelity
remain separate obligations. No release or whole-corpus visual pass is claimed.
