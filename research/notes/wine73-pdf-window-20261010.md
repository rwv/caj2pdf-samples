<!-- SPDX-License-Identifier: MIT -->

# Wine 7.3 PDF mode and font-resource interaction

[Rust #533](https://github.com/rwv/caj2pdf-rust/issues/533) is an observed
CAJViewer/Wine limitation with a measured workaround. The unchanged four-page
PDF works in **continuous mode at 75%**. Its original single-page/75% procedure
still loses the window. A related PDF that shares the same embedded Latin and
ornament font now produces a visible **fatal-error dialog immediately after
the single-page click**, before the zoom action. The internal cause is not
isolated; no invalid-PDF or native-Windows diagnosis follows from this result.

The [metadata receipt](wine73-pdf-window-20261010.json) retains all original
failures and mode controls, fresh observations, public-window/process metadata,
hashes and the exact experiments. Raw captures, documents, fonts and PDFs remain
external under `~/.cache/cajviewer73-fixes-20261010/533-window/`.

## Fixed input and procedure

The C8 source is
`b9a64bf99e4bc496b976541a27128ee84109835d5f79f228a9c8ad159ec6829b`.
Its baseline PDF is
`185a14fd1155782ed691c450f4b63e15213c61914cd362f3a6ee380dbb8e4a42`
(305,034 bytes). Pinned current implementation `e6343aa785547f5e34bb499dfda56be2d5dc595d`
reproduces that historical #459 PDF exactly. Conversion uses the same external
Noto Serif CJK face 2 / FreeSerif recipe and frozen CLI/WASM identities as the
[orientation report](wine73-jpeg-orientation-20261010.md). Original source
single-page observations and their cold repeat still cover all four pages.

The Wine 8.0 32-bit / CAJViewer 7.3.151 Simple image, font/MSXML prefix, offline
read-only isolation and resource limits are unchanged. The desktop is
1600 × 1200, 96 DPI. The driver waits for canonical page/zoom controls,
maximizes, clicks single-page at `(558,54)` when requested, waits one second,
then sets 75% through the numeric zoom field. Each visited page has two captures
and before/after numeric gates. Independent connected components bound complete
pages without resizing, registration or tolerance. A successful numeric edit
or still-running container alone is not a page observation.

The new stepwise driver records a capture, public visible-window titles,
numeric fields and host `docker top` process metadata at startup, after the
single-page click, after zoom and twice for each page. It stops further input
when the fatal dialog is observed. This avoids intentionally dismissing a known
modal error. A dialog that appears between probes can still be dismissed by a
later Return; that race is not excluded by the failed baseline run.

## Observed factors and negative control

The three earlier independent controls remain unchanged: default continuous
162%, single-page only at 162%, and continuous zoom-only 75% all retained the
window at 1/5/15 seconds. The historical combined procedure remained desktop
at 1/5/15/30/60 seconds. These are retained as earlier observations, not replaced
by the new working recipe or relabeled complete four-page tests.

| Actual four-page PDF configuration | Fresh single-page/75% outcome |
| --- | --- |
| Baseline Latin font also draws the triangle | No confirmed page; window disappears |
| Explicit decoration role, same Latin font input and embedded object | Fatal-error dialog; no confirmed page |
| Separate font input containing identical FreeSerif bytes | All four pages observed, including a second stepwise session |
| Separate DejaVu Sans decoration input | All four pages observed |
| Correct external HGBZ ornament resource from #532 | All four pages observed in three independent sessions |

The explicit shared input changes logical decoration resource `/F1` to `/F3`,
but both refer to the same embedded font object. Merely renaming that resource
does not avoid this failure. A copied FreeSerif file produces an independent
decoration subset. The baseline, explicit shared and explicit separate PDFs
render **identically on all four pages in MuPDF at 72 DPI**, while their Wine
mode outcomes differ. All six checked actual/control PDFs pass `qpdf --check`;
that check explicitly cannot exclude every PDF error and is not a Wine pass.

The original
[`wine_pdf_font_sharing_control.py`](../cajviewer/wine_pdf_font_sharing_control.py)
authors one C8 page with eight Latin characters and a repeated ornament. Its
shared-font and separate-font PDFs both work in Wine single-page/75%, as does
the original input. Thus **font sharing is not a universal sufficient trigger**.
The real document's additional content/subset/cache interaction remains
unisolated. The control is a discriminator, not a claimed minimal reproducer.

For the explicit-shared actual PDF the stepwise capture contains the application's
`致命错误` (fatal error) window directly after the single-page click. The dialog
says CAJViewer encountered a fault and must close. Public window metadata and
process presence are retained; no stack-address interpretation or vendor code
inspection was performed. Wine logs also contain critical-section wait timeouts,
which are observations rather than an established causal chain. No recorded OOM
event explains the failure. This is stronger evidence than window disappearance
alone, but does not distinguish CAJViewer internals from its Wine interaction.

## Supported workaround and scope

For the unchanged baseline PDF, keep the default **continuous display**, change
only the zoom to 75%, and navigate by the page-number field. All four pages have
complete, stable, numerically confirmed observations in two cold sessions.
The page components exclude the partial neighboring pages in continuous mode.
Continuous-mode bounds are 507 × 748 pixels; the correctly configured single-page
PDF bounds are 506 × 748. These are separate display modes, not exact-raster
comparisons or a reason to normalize one column away.

Alternatively, the existing explicit decoration-font option can supply an
independent resource. The [#532 HGBZ recipe](wine73-ornament-resources-20261010.md)
also selects the intended ornament rather than the default triangle and has
matching native/Node/Chromium outputs. This is a measured alternative for this
document, not automatic fallback behavior. No production API, font sharing,
default PDF output, memory bounds or platform adapter was changed for #533.

The first experiment incorrectly expected an explicit shared role to preserve
the baseline PDF bytes; the failed assertion and distinct outputs were retained
before launching a viewer. The first authored control included two unadmitted
native codes and was correctly refused at byte 152; its original bytes and
diagnostic are retained before the admitted eight-character control. An initial
failure handler tried unavailable container `ps` and recorded that diagnostic
failure after saving the screenshot; later runs use host `docker top`. An initial
font inspector assumed TrueType for the CJK CFF resource and failed before any
conclusion; the corrected inspector distinguishes FontFile2/FontFile3.

The generator is original MIT code using the existing MIT C8 authoring helper.
Its bytes reproduce the observed input exactly; no document text, font program,
font outline or vendor binary is committed. No private HN/JBIG or other converter
implementation was read. One independent-parser control test verifies the 47
nonsemantic ornament draws and eight Latin characters with their paint order;
it passes without a viewer or corpus, with zero skips. The catalog is unchanged.
Required review/CI and Rust provenance/support links
complete this narrow issue; #406, #441, #531, #534 and full native-Windows
equivalence remain outside this result. No release is requested.
