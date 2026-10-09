# Original viewer page-buffer observations (2026-10-09)

Both retained native raster variants already occur in RGB buffers wrapped by
public Qt image constructors. A separate original PDF reproduces a difference
at the same boundary. These observations narrow [#61](https://github.com/rwv/caj2pdf-samples/issues/61),
under [Rust #441](https://github.com/rwv/caj2pdf-rust/issues/441) and [#51](https://github.com/rwv/caj2pdf-samples/issues/51),
without identifying an internal renderer cause or changing converter output.
The [receipt](viewer-page-buffer-20261009.json) retains all twelve viewer sessions,
the two initial API positive controls, source/tool/trace hashes and cleanup.

## Observed boundary

The original Linux x86-64/Qt5 interposer forwards four public `QImage` buffer
constructors: mutable/const data, each with implicit/explicit row stride. It
then observes dimensions, format, stride, image identity, thread, pointer
alignment modulo 64, and endpoint floating state. For RGB888 images at least
200×100 and at most 4 Mi pixels, it hashes exactly width×3 bytes per row through
`constScanLine`. Padding is excluded; no raster bytes or font data are exported
by this hook. The existing `qpaint_observe.cpp` separately retains bounded
completed display pixmaps externally.

The buffer log is capped at 10,000 events plus an explicit `LIMIT` record,
with each record below 512 bytes. A missing forwarded symbol exits 125;
failed/truncated logging exits 126. The published tool adds an ABI guard and
a compile-time test log path, saturates the event counter, and skips hashing the `LIMIT` event. Its final
API controls are distinct from the twelve historical prototype sessions;
those sessions are not relabeled as final-tool reruns. Constructor completion
alone does not prove pixel readiness. Claims below require a matching hash in
the subsequently selected target-page pixmap.

## Native and PDF observations

Six new native sessions use the unchanged original 12-page/20-byte-index control
from [the navigation report](native-viewer-navigation-20261009.md). Metadata-only
direct/prior3 routes give A/B. With hashes enabled, direct and prior3 give A/A;
two predeclared fresh prior3 repeats give A/B. Every attempt is retained.
All four digest sessions match their selected page-5 display pixmap byte for
byte. A/B differ by 29,877 pixels, with channel deltas -2 through +2. Both
variants occur with the same worker TID, RGB888 format, 1003×1506 dimensions,
3012-byte stride, 32-byte pointer alignment remainder and observed floating
state (rounding 0, MXCSR `1fa3`, x87 control `37f`). These endpoint observations
do not establish earlier rendering state or all-thread floating behavior.

The PDF generator independently writes five- and six-page PDF 1.7 controls,
referencing Standard-14 Helvetica without embedding any font program. Each
page has an original marker count; pages outside 2–4 also have an authored
40×40 ASCII grid. The first five streams are identical across documents;
each file is below 160 KiB. Both pass qpdf syntax/stream checks.

| Unchanged document/protocol | Direct5 versus prior3→5 | Maximum channel delta |
| --- | --- | --- |
| Five-page PDF, complete displayed page crop | Identical | 0 |
| Six-page PDF, complete displayed page crop | 21,073 different pixels | 1 |
| Six-page PDF, selected 397×561 buffer/display pixmap | 8,254 different pixels | 1 |

Four fresh PDF sessions use no observer. A subsequent instrumented six-page
pair reproduces both screenshot hashes exactly. The current target-page
pixmaps have identical target/source rectangles and transforms, and each
matches a distinct public-buffer digest. The following-page pixmap is excluded.
Screenshot and buffer counts measure different stages: the displayed crop is
397×562 with a small Qt transform, not the underlying 397×561 pixmap. They must
not be mixed. Both captures within every session agree, despite across-session
differences. This supports neither a pixel tolerance nor a readiness rule.

The initial five-page analysis reused the old top-page crop, which actually
contained the preceding page because last-page navigation clamps scrolling.
Full-frame inspection corrected its target crop to `[626,607,1023,1169]`;
the six-page crop remains `[626,156,1023,718]`. The error and original frames
are retained. Different cross-document scroll origins also change fractional
placement, so a five-versus-six-page pixel comparison does not isolate page
count as a rendering cause. No alignment fit or tolerance is introduced.

## Reproduction, validation and provenance

```sh
python3 research/cajviewer/pdf_navigation_controls.py /external/new-pdf-controls
python3 -m unittest discover -s research/conformance -p 'test_pdf_navigation_controls.py' -v
python3 -m unittest discover -s research/conformance -p 'test_qimage_buffer_observe.py' -v
c++ -std=c++17 -shared -fPIC -O2 -Wall -Wextra -Werror -DQT_NO_VERSION_TAGGING \
  $(pkg-config --cflags Qt5Gui) research/cajviewer/qpaint_observe.cpp \
  research/cajviewer/qimage_buffer_observe.cpp -ldl -o /external/buffer-observe.so
```

The API tests require distro Qt5 development libraries and run without a
viewer/display/corpus. An independent Python RGB formula checks all four
constructor hashes despite different padding; C++ controls verify dimensions,
strides, unchanged caller buffer ownership, cleanup callbacks and null inputs.
Other controls exercise small/short/narrow/oversized non-hashed images, the
explicit event cap and fatal log failure. Independent pikepdf/qpdf controls
check generated framing, page inventories, original text-operator counts,
font references, exact measured document hashes and refusal to overwrite.

For native viewer observations, use the earlier report's contained
`native_page_capture.py` commands with the combined observer. For the PDF
experiment, the pinned desktop is maximized at 1600×1200/96 dpi; set 50%,
wait two seconds, then visit either 5 or 3→5. After each navigation wait three
seconds, capture, wait one second, capture again. Startup waits five seconds
plus two after maximization. The external driver hashes and all commands are
retained. This is a measured protocol, not a portable automated PDF capture
runner: validate page/zoom fields and full target-page position each time.
The native runner's large-page selection assumptions do not apply to these
compact PDF views. Keep every attempt, including variants.

All twelve sessions use the pinned image
`sha256:cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de`,
network none, read-only root/input, non-root uid, dropped capabilities,
no-new-privileges, 2 GiB memory/swap, 2 CPUs, 256 PIDs and a 90-second lifetime.
Source hashes, both page/zoom fields, no OOM, no capture/log limits and complete
container cleanup are verified. Buffer timestamps are taken after hashing;
UI action logs retain order/durations but no absolute timestamps. Therefore
the logs do not establish a timed prefetch mechanism. Instrumentation can
perturb timing; identical non-instrumented PDF screenshot variants are retained.

All committed source is original MIT work. PDF syntax and public Qt API
declarations are interfaces, not copied implementation. Qt5 signatures come
from Debian `qtbase5-dev` 5.15.15 headers; `qimage.h` SHA-256 is
`976caa9b43d15d0bcc99e9c62eb773cc1f117a16edb2dc7d7bb313ee33dec069`.
The ABI names were obtained by compiling our own four-call reference object.
The [current Qt documentation](https://doc.qt.io/qt-6/qimage.html) also describes
buffer ownership/row access, but Qt6 signatures are not the Qt5 ABI authority.
The Qt5 web archive was unavailable. No vendor implementation or font outline
was inspected; no foreign converter code or private module was migrated.
Generated PDFs, source/derived documents, pixels, fonts and binaries remain
external. The first local final-control link failed because an unpacked Qt
library directory was missing from the linker path; no test ran in that attempt.
The corrected environment uses the same source and explicit local library path.

The original `7797…` PDF cold discrepancy and a reliable comparison criterion
remain unresolved. This adds no corpus conversion pass, no full-corpus runtime
rerun and no API/support/output change. The ledger remains 1,252 PASS / 18 FAIL /
27 UNSUPPORTED. Broader #441/#406 and original-font/ornament fidelity work remain
open; no release is requested.
